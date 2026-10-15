"""auth_routes.py — Portal authentication API for PT Luka (prototype).

Endpoints (prefix ``/api/auth``):
  POST /register            ajukan akun (status pending, verifikasi Admin IT)
  POST /login               identitas (ID karyawan/NIK/email/HP) + password
  POST /logout              cabut sesi
  GET  /me                  konteks aktor dari sesi
  POST /change-password     ganti password (butuh sesi)
  POST /forgot-password     kirim OTP ke email terdaftar (respons generik)
  POST /reset-password      setel ulang password dengan OTP
  GET  /admin/registrations daftar pengajuan pending (admin)
  POST /admin/registrations/{id}/approve|reject   (admin)
  GET  /health              status modul + mode email

All responses are JSON; errors use FastAPI's ``{"detail": ...}`` shape which the
frontend ``services/problem.ts`` already normalises.
"""

from __future__ import annotations

import os
import re

from dotenv import load_dotenv
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from ..services.auth_store import (
    AuthError,
    PortalUser,
    get_store,
    mask_email,
)
from ..services.emailer import send_email, smtp_configured

load_dotenv()

# ── Settings ─────────────────────────────────────────────────────────────────


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    try:
        return int(raw) if raw else default
    except ValueError:
        return default


def _token_ttl() -> int:
    return _int_env("AUTH_TOKEN_TTL_MINUTES", 120) * 60


def _remember_ttl() -> int:
    return _int_env("AUTH_REMEMBER_TTL_MINUTES", 720) * 60


def _otp_ttl() -> int:
    return _int_env("OTP_TTL_MINUTES", 10) * 60


def _otp_max_attempts() -> int:
    return _int_env("OTP_MAX_ATTEMPTS", 5)


def _otp_cooldown() -> int:
    return _int_env("OTP_COOLDOWN_SECONDS", 60)


# ── Request models ───────────────────────────────────────────────────────────


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=3, max_length=120)
    employee_id: str = Field(min_length=1, max_length=40)
    ktp_id: str = Field(min_length=1, max_length=32)
    phone: str = Field(min_length=1, max_length=32)
    department: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=8, max_length=128)
    consent: bool


class LoginRequest(BaseModel):
    identifier: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=1, max_length=128)
    remember: bool = False


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class ForgotPasswordRequest(BaseModel):
    identifier: str = Field(min_length=1, max_length=120)


class ResetPasswordRequest(BaseModel):
    identifier: str = Field(min_length=1, max_length=120)
    otp: str = Field(min_length=6, max_length=6)
    new_password: str = Field(min_length=8, max_length=128)


# ── Validation helpers ───────────────────────────────────────────────────────

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _validate_email(value: str) -> None:
    if not _EMAIL_RE.match(value.strip()):
        raise HTTPException(status_code=400, detail="Format email tidak valid.")


def _validate_ktp(value: str) -> None:
    digits = re.sub(r"\D", "", value)
    if len(digits) != 16:
        raise HTTPException(status_code=400, detail="NIK/KTP harus 16 digit angka.")


def _validate_phone(value: str) -> None:
    digits = re.sub(r"\D", "", value)
    if not 9 <= len(digits) <= 15:
        raise HTTPException(status_code=400, detail="Nomor HP tidak valid.")


def _validate_password(value: str) -> None:
    if len(value) < 8:
        raise HTTPException(status_code=400, detail="Password minimal 8 karakter.")
    if not re.search(r"[A-Za-z]", value) or not re.search(r"\d", value):
        raise HTTPException(status_code=400, detail="Password harus memuat huruf dan angka.")


# ── Auth dependencies ────────────────────────────────────────────────────────


def _bearer_token(authorization: str | None) -> str:
    if not authorization:
        raise HTTPException(status_code=401, detail="Header Authorization wajib diisi.")
    parts = authorization.split(maxsplit=1)
    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1].strip():
        raise HTTPException(status_code=401, detail="Format token Bearer tidak valid.")
    return parts[1].strip()


def _current_user(authorization: str | None) -> PortalUser:
    token = _bearer_token(authorization)
    user = get_store().get_session_user(token)
    if user is None:
        raise HTTPException(status_code=401, detail="Sesi tidak valid atau telah berakhir.")
    return user


def _actor_context(user: PortalUser) -> dict[str, object]:
    return {
        "actorId": user.user_id,
        "displayName": user.full_name,
        "email": mask_email(user.email),
        "role": user.role,
        "status": user.status,
    }


def _registration_view(user: PortalUser) -> dict[str, object]:
    return {
        "registration_id": user.user_id,
        "full_name": user.full_name,
        "email": user.email,
        "employee_id": user.employee_id,
        "phone": user.phone,
        "department": user.department,
        "status": user.status,
        "created_at": user.created_at,
    }


# ── Router factory ───────────────────────────────────────────────────────────


def create_auth_router() -> APIRouter:
    router = APIRouter(prefix="/api/auth", tags=["auth"])

    # Seed the admin account once, after .env is loaded.
    admin_email = os.getenv("SEED_ADMIN_EMAIL", "admin@luka.local")
    admin_password = os.getenv("SEED_ADMIN_PASSWORD", "Admin#12345")
    get_store().seed_admin(admin_email, admin_password)

    @router.get("/health")
    def auth_health() -> dict[str, object]:
        return {
            "status": "healthy",
            "module": "portal-auth",
            "email_mode": "smtp" if smtp_configured() else "dev-log",
        }

    @router.post("/register", status_code=201)
    def register(payload: RegisterRequest) -> dict[str, object]:
        if not payload.consent:
            raise HTTPException(
                status_code=400, detail="Persetujuan akses internal wajib dicentang."
            )
        _validate_email(payload.email)
        _validate_ktp(payload.ktp_id)
        _validate_phone(payload.phone)
        _validate_password(payload.password)
        try:
            user = get_store().register(
                full_name=payload.full_name,
                email=payload.email,
                employee_id=payload.employee_id,
                ktp_id=payload.ktp_id,
                phone=payload.phone,
                department=payload.department,
                password=payload.password,
            )
        except AuthError as exc:
            raise HTTPException(status_code=409, detail=exc.message) from exc
        return {
            "success": True,
            "status": user.status,
            "registration_id": user.user_id,
            "message": "Pengajuan diterima. Menunggu verifikasi Admin IT.",
        }

    @router.post("/login")
    def login(payload: LoginRequest) -> dict[str, object]:
        try:
            user = get_store().authenticate(payload.identifier, payload.password)
        except AuthError as exc:
            status = 403 if exc.code in {"ACCOUNT_PENDING", "ACCOUNT_REJECTED"} else 401
            raise HTTPException(status_code=status, detail=exc.message) from exc
        ttl = _remember_ttl() if payload.remember else _token_ttl()
        token, expires_in = get_store().create_session(user.user_id, ttl)
        return {
            "success": True,
            "accessToken": token,
            "expiresIn": expires_in,
            "actor": _actor_context(user),
        }

    @router.post("/logout")
    def logout(
        authorization: str | None = Header(None, alias="Authorization"),
    ) -> dict[str, object]:
        token = _bearer_token(authorization)
        get_store().revoke_session(token)
        return {"success": True}

    @router.get("/me")
    def me(authorization: str | None = Header(None, alias="Authorization")) -> dict[str, object]:
        user = _current_user(authorization)
        return {"success": True, "actor": _actor_context(user)}

    @router.post("/change-password")
    def change_password(
        payload: ChangePasswordRequest,
        authorization: str | None = Header(None, alias="Authorization"),
    ) -> dict[str, object]:
        user = _current_user(authorization)
        _validate_password(payload.new_password)
        try:
            get_store().change_password(
                user.user_id, payload.current_password, payload.new_password
            )
        except AuthError as exc:
            status = 401 if exc.code == "INVALID_CREDENTIALS" else 400
            raise HTTPException(status_code=status, detail=exc.message) from exc
        return {"success": True, "message": "Password berhasil diubah. Silakan masuk kembali."}

    @router.post("/forgot-password")
    def forgot_password(payload: ForgotPasswordRequest) -> dict[str, object]:
        generic = {
            "success": True,
            "message": "Jika identitas terdaftar, kode verifikasi telah dikirim ke email Anda.",
        }
        try:
            result = get_store().create_otp(payload.identifier, _otp_ttl(), _otp_cooldown())
        except AuthError as exc:
            raise HTTPException(status_code=429, detail=exc.message) from exc
        if result is None:
            return generic
        otp, user = result
        send_email(
            to=user.email,
            subject="Kode Verifikasi Reset Password — Portal PT Luka",
            body=(
                f"Halo {user.full_name},\n\n"
                f"Kode verifikasi Anda: {otp}\n"
                f"Kode berlaku {_otp_ttl() // 60} menit. "
                "Jangan bagikan kode ini kepada siapa pun.\n\n"
                "Jika Anda tidak meminta reset password, abaikan email ini."
            ),
        )
        return generic

    @router.post("/reset-password")
    def reset_password(payload: ResetPasswordRequest) -> dict[str, object]:
        _validate_password(payload.new_password)
        ok = get_store().reset_password(
            payload.identifier, payload.otp, payload.new_password, _otp_max_attempts()
        )
        if not ok:
            raise HTTPException(status_code=400, detail="Kode verifikasi salah atau kedaluwarsa.")
        return {"success": True, "message": "Password berhasil disetel ulang. Silakan masuk."}

    @router.get("/admin/registrations")
    def list_registrations(
        authorization: str | None = Header(None, alias="Authorization"),
    ) -> dict[str, object]:
        user = _current_user(authorization)
        if user.role != "admin":
            raise HTTPException(status_code=403, detail="Akses hanya untuk Admin IT.")
        pending = get_store().list_pending()
        return {
            "success": True,
            "data": [_registration_view(u) for u in pending],
            "count": len(pending),
        }

    @router.post("/admin/registrations/{registration_id}/approve")
    def approve_registration(
        registration_id: str,
        authorization: str | None = Header(None, alias="Authorization"),
    ) -> dict[str, object]:
        return _decide(registration_id, "active", authorization)

    @router.post("/admin/registrations/{registration_id}/reject")
    def reject_registration(
        registration_id: str,
        authorization: str | None = Header(None, alias="Authorization"),
    ) -> dict[str, object]:
        return _decide(registration_id, "rejected", authorization)

    def _decide(
        registration_id: str, status: str, authorization: str | None
    ) -> dict[str, object]:
        user = _current_user(authorization)
        if user.role != "admin":
            raise HTTPException(status_code=403, detail="Akses hanya untuk Admin IT.")
        try:
            updated = get_store().set_status(registration_id, status)
        except AuthError as exc:
            raise HTTPException(status_code=404, detail=exc.message) from exc
        return {"success": True, "registration_id": updated.user_id, "status": updated.status}

    return router
