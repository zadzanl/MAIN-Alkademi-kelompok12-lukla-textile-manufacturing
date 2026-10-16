"""auth_store.py — In-memory identity store for the PT Lukla portal (prototype).

Holds users, sessions, and one-time-password (OTP) challenges. Passwords are
hashed with stdlib ``hashlib.scrypt``; session tokens and OTPs are stored
hashed, never in plaintext. All state is process-local and resets on restart.

Known ceiling: single-process, in-memory only, no persistence. Upgrade path:
replace this module with the production backend's PostgreSQL ``actors`` /
``sessions`` / ``credentials`` tables (see ``backend/app`` and
``openspec/.../13-authn-authz-design.md``) behind the same method API.
"""

from __future__ import annotations

import hashlib
import hmac
import re
import secrets
import threading
import time
import uuid
from dataclasses import dataclass

# ── Password hashing (stdlib scrypt) ─────────────────────────────────────────

_SCRYPT_N = 2**14
_SCRYPT_R = 8
_SCRYPT_P = 1
_SALT_BYTES = 16
_KEY_LEN = 32


def hash_password(password: str) -> str:
    """Return a self-describing ``scrypt$n$r$p$salt$hash`` string."""
    salt = secrets.token_bytes(_SALT_BYTES)
    digest = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=_SCRYPT_N,
        r=_SCRYPT_R,
        p=_SCRYPT_P,
        dklen=_KEY_LEN,
    )
    return f"scrypt${_SCRYPT_N}${_SCRYPT_R}${_SCRYPT_P}${salt.hex()}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    """Constant-time verification of a password against a stored hash."""
    try:
        scheme, n, r, p, salt_hex, digest_hex = encoded.split("$")
        if scheme != "scrypt":
            return False
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(digest_hex)
        digest = hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt,
            n=int(n),
            r=int(r),
            p=int(p),
            dklen=len(expected),
        )
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(digest, expected)


# ── Identifier normalisation ─────────────────────────────────────────────────


def normalize_email(value: str) -> str:
    return value.strip().lower()


def normalize_employee_id(value: str) -> str:
    return re.sub(r"\s+", "", value).upper()


def normalize_ktp(value: str) -> str:
    return re.sub(r"\D", "", value)


def normalize_phone(value: str) -> str:
    digits = re.sub(r"\D", "", value)
    if digits.startswith("0"):
        digits = "62" + digits[1:]
    elif digits.startswith("8"):
        digits = "62" + digits
    return digits


def hash_identifier(value: str) -> str:
    """Deterministic lookup hash for sensitive identifiers (KTP)."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def mask_ktp(value: str) -> str:
    digits = normalize_ktp(value)
    if len(digits) <= 4:
        return "*" * len(digits)
    return "*" * (len(digits) - 4) + digits[-4:]


def mask_email(value: str) -> str:
    email = normalize_email(value)
    if "@" not in email:
        return "***"
    local, _, domain = email.partition("@")
    if len(local) <= 1:
        return f"*@{domain}"
    return f"{local[0]}{'*' * (len(local) - 1)}@{domain}"


# ── Domain errors ────────────────────────────────────────────────────────────


class AuthError(Exception):
    """Domain error carrying a stable ``code`` for the API layer."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


# ── Records ──────────────────────────────────────────────────────────────────


@dataclass
class PortalUser:
    user_id: str
    full_name: str
    email: str
    employee_id: str
    ktp_hash: str
    ktp_last4: str
    phone: str
    department: str
    password_hash: str
    role: str
    status: str  # pending | active | rejected
    created_at: float
    updated_at: float


@dataclass
class Session:
    token_hash: str
    user_id: str
    created_at: float
    expires_at: float


@dataclass
class OtpChallenge:
    identifier_key: str
    otp_hash: str
    expires_at: float
    last_sent_at: float
    attempts: int = 0
    consumed: bool = False


def _otp_hash(identifier_key: str, otp: str) -> str:
    return hashlib.sha256(f"{identifier_key}:{otp}".encode()).hexdigest()


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


# ── Store ────────────────────────────────────────────────────────────────────


class AuthStore:
    """Thread-safe, process-local identity store."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._users: dict[str, PortalUser] = {}
        self._index: dict[str, str] = {}  # "kind:value" -> user_id
        self._sessions: dict[str, Session] = {}  # token_hash -> session
        self._otps: dict[str, OtpChallenge] = {}  # identifier_key -> challenge

    # -- internals ----------------------------------------------------------

    @staticmethod
    def _candidate_keys(identifier: str) -> list[str]:
        raw = identifier.strip()
        keys: list[str] = []
        if "@" in raw:
            keys.append(f"email:{normalize_email(raw)}")
        emp = normalize_employee_id(raw)
        if emp:
            keys.append(f"emp:{emp}")
        if re.search(r"\d", raw):
            keys.append(f"phone:{normalize_phone(raw)}")
            keys.append(f"ktp:{hash_identifier(normalize_ktp(raw))}")
        return keys

    def _match(self, identifier: str) -> tuple[PortalUser | None, str | None]:
        for key in self._candidate_keys(identifier):
            user_id = self._index.get(key)
            if user_id and user_id in self._users:
                return self._users[user_id], key
        return None, None

    def _is_duplicate(self, email: str, employee_id: str, ktp_hash: str, phone: str) -> bool:
        return any(
            key in self._index
            for key in (
                f"email:{email}",
                f"emp:{employee_id}",
                f"ktp:{ktp_hash}",
                f"phone:{phone}",
            )
        )

    def _revoke_user_sessions(self, user_id: str) -> None:
        stale = [h for h, s in self._sessions.items() if s.user_id == user_id]
        for token_hash in stale:
            del self._sessions[token_hash]

    # -- user lifecycle -----------------------------------------------------

    def seed_admin(self, email: str, password: str, full_name: str = "Admin IT") -> PortalUser:
        """Create (or return) the active administrator account."""
        with self._lock:
            normalized = normalize_email(email)
            existing = self._index.get(f"email:{normalized}")
            if existing:
                return self._users[existing]
            now = time.time()
            user = PortalUser(
                user_id=str(uuid.uuid4()),
                full_name=full_name,
                email=normalized,
                employee_id="ADMIN-IT",
                ktp_hash=hash_identifier("ADMIN-IT"),
                ktp_last4="0000",
                phone="",
                department="IT",
                password_hash=hash_password(password),
                role="admin",
                status="active",
                created_at=now,
                updated_at=now,
            )
            self._users[user.user_id] = user
            self._index[f"email:{normalized}"] = user.user_id
            self._index[f"emp:{user.employee_id}"] = user.user_id
            return user

    def register(
        self,
        *,
        full_name: str,
        email: str,
        employee_id: str,
        ktp_id: str,
        phone: str,
        department: str,
        password: str,
    ) -> PortalUser:
        with self._lock:
            normalized_email = normalize_email(email)
            normalized_emp = normalize_employee_id(employee_id)
            normalized_ktp = normalize_ktp(ktp_id)
            normalized_phone = normalize_phone(phone)
            ktp_hash = hash_identifier(normalized_ktp)
            if self._is_duplicate(normalized_email, normalized_emp, ktp_hash, normalized_phone):
                raise AuthError(
                    "DUPLICATE_IDENTITY",
                    "Email, nomor karyawan, NIK/KTP, atau nomor HP sudah terdaftar.",
                )
            now = time.time()
            user = PortalUser(
                user_id=str(uuid.uuid4()),
                full_name=full_name.strip(),
                email=normalized_email,
                employee_id=normalized_emp,
                ktp_hash=ktp_hash,
                ktp_last4=mask_ktp(normalized_ktp)[-4:],
                phone=normalized_phone,
                department=department.strip(),
                password_hash=hash_password(password),
                role="employee",
                status="pending",
                created_at=now,
                updated_at=now,
            )
            self._users[user.user_id] = user
            self._index[f"email:{normalized_email}"] = user.user_id
            self._index[f"emp:{normalized_emp}"] = user.user_id
            self._index[f"ktp:{ktp_hash}"] = user.user_id
            self._index[f"phone:{normalized_phone}"] = user.user_id
            return user

    def find_by_identifier(self, identifier: str) -> PortalUser | None:
        with self._lock:
            user, _ = self._match(identifier)
            return user

    def get_user(self, user_id: str) -> PortalUser | None:
        with self._lock:
            return self._users.get(user_id)

    # -- authentication -----------------------------------------------------

    def authenticate(self, identifier: str, password: str) -> PortalUser:
        with self._lock:
            user, _ = self._match(identifier)
            if user is None or not verify_password(password, user.password_hash):
                raise AuthError("INVALID_CREDENTIALS", "Identitas atau password salah.")
            if user.status == "pending":
                raise AuthError(
                    "ACCOUNT_PENDING",
                    "Akun masih menunggu verifikasi Admin IT.",
                )
            if user.status == "rejected":
                raise AuthError(
                    "ACCOUNT_REJECTED",
                    "Pengajuan akun ditolak. Hubungi Admin IT.",
                )
            return user

    def create_session(self, user_id: str, ttl_seconds: int) -> tuple[str, int]:
        with self._lock:
            token = secrets.token_urlsafe(32)
            now = time.time()
            self._sessions[_token_hash(token)] = Session(
                token_hash=_token_hash(token),
                user_id=user_id,
                created_at=now,
                expires_at=now + ttl_seconds,
            )
            return token, ttl_seconds

    def get_session_user(self, token: str) -> PortalUser | None:
        with self._lock:
            session = self._sessions.get(_token_hash(token))
            if session is None:
                return None
            if session.expires_at <= time.time():
                del self._sessions[session.token_hash]
                return None
            user = self._users.get(session.user_id)
            if user is None or user.status != "active":
                return None
            return user

    def revoke_session(self, token: str) -> None:
        with self._lock:
            self._sessions.pop(_token_hash(token), None)

    # -- password management ------------------------------------------------

    def change_password(self, user_id: str, current: str, new: str) -> None:
        with self._lock:
            user = self._users.get(user_id)
            if user is None:
                raise AuthError("AUTH_REQUIRED", "Sesi tidak valid.")
            if not verify_password(current, user.password_hash):
                raise AuthError("INVALID_CREDENTIALS", "Password saat ini salah.")
            if current == new:
                raise AuthError("SAME_PASSWORD", "Password baru harus berbeda dari password lama.")
            user.password_hash = hash_password(new)
            user.updated_at = time.time()
            self._revoke_user_sessions(user_id)

    # -- OTP (forgot/reset password) ---------------------------------------

    def create_otp(
        self, identifier: str, ttl_seconds: int, cooldown_seconds: int
    ) -> tuple[str, PortalUser] | None:
        """Create an OTP for an existing user. Returns None when unknown (the
        caller must still answer generically to avoid account enumeration)."""
        with self._lock:
            user, key = self._match(identifier)
            if user is None or key is None:
                return None
            now = time.time()
            existing = self._otps.get(key)
            if existing and now - existing.last_sent_at < cooldown_seconds:
                raise AuthError(
                    "OTP_COOLDOWN",
                    "Mohon tunggu sebelum meminta kode baru.",
                )
            otp = f"{secrets.randbelow(1_000_000):06d}"
            self._otps[key] = OtpChallenge(
                identifier_key=key,
                otp_hash=_otp_hash(key, otp),
                expires_at=now + ttl_seconds,
                last_sent_at=now,
            )
            return otp, user

    def verify_otp(self, identifier: str, otp: str, max_attempts: int) -> bool:
        with self._lock:
            now = time.time()
            for key in self._candidate_keys(identifier):
                challenge = self._otps.get(key)
                if challenge is None or challenge.consumed:
                    continue
                if challenge.expires_at <= now:
                    del self._otps[key]
                    continue
                if challenge.attempts >= max_attempts:
                    return False
                challenge.attempts += 1
                if hmac.compare_digest(challenge.otp_hash, _otp_hash(key, otp)):
                    challenge.consumed = True
                    return True
                return False
            return False

    def reset_password(self, identifier: str, otp: str, new: str, max_attempts: int) -> bool:
        with self._lock:
            user, key = self._match(identifier)
            if user is None or key is None:
                return False
            if not self.verify_otp(identifier, otp, max_attempts):
                return False
            user.password_hash = hash_password(new)
            user.updated_at = time.time()
            self._revoke_user_sessions(user.user_id)
            self._otps.pop(key, None)
            return True

    # -- admin approval -----------------------------------------------------

    def list_pending(self) -> list[PortalUser]:
        with self._lock:
            return sorted(
                (u for u in self._users.values() if u.status == "pending"),
                key=lambda u: u.created_at,
            )

    def set_status(self, user_id: str, status: str) -> PortalUser:
        with self._lock:
            user = self._users.get(user_id)
            if user is None:
                raise AuthError("NOT_FOUND", "Pengajuan tidak ditemukan.")
            user.status = status
            user.updated_at = time.time()
            if status != "active":
                self._revoke_user_sessions(user_id)
            return user


# ── Process-wide singleton ───────────────────────────────────────────────────

_store = AuthStore()


def get_store() -> AuthStore:
    return _store
