"""portal_store.py — In-memory, client-scoped store for the UHUY B2B external portal.

Two actor kinds live here:
  * external client users (role ``client``), each bound to exactly one ``client_id``;
  * an internal approver (role ``admin``) that verifies client registrations.

Every client-data read/write is keyed by ``client_id`` and filtered server-side,
so a session for client A can never observe client B rows (RBAC role
"Klien Maklon/Ext", acceptance test AT-R08). The ``client_id`` is never taken
from the request body; it is resolved from the authenticated session.

Known ceiling: process-local, in-memory, resets on restart, single-process only.
Upgrade path: replace this module with the production PostgreSQL tables
(``actors``, ``client_memberships``, ``orders``, ``stock_lots``,
``portal_requests``) behind the same method API; RLS then enforces the same
``client_id`` predicate. No call site changes.
"""

from __future__ import annotations

import hashlib
import hmac
import re
import secrets
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

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


def normalize_phone(value: str) -> str:
    digits = re.sub(r"\D", "", value)
    if digits.startswith("0"):
        digits = "62" + digits[1:]
    elif digits.startswith("8"):
        digits = "62" + digits
    return digits


def hash_identifier(value: str) -> str:
    """Deterministic lookup hash for sensitive identifiers."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def mask_email(value: str) -> str:
    email = normalize_email(value)
    if "@" not in email:
        return "***"
    local, _, domain = email.partition("@")
    if len(local) <= 1:
        return f"*@{domain}"
    return f"{local[0]}{'*' * (len(local) - 1)}@{domain}"


# ── Domain errors ────────────────────────────────────────────────────────────


class PortalError(Exception):
    """Domain error carrying a stable ``code`` for the API layer."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


# ── Records ──────────────────────────────────────────────────────────────────


@dataclass
class ClientUser:
    user_id: str
    client_id: str
    company_name: str
    contact_name: str
    email: str
    phone: str
    password_hash: str
    role: str  # "client" | "admin"
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


@dataclass
class Order:
    order_id: str
    client_id: str
    article_name: str
    quantity: int
    scheme: str
    status: str  # confirmed | cutting | sewing | qc | completed
    progress: int  # 0..100
    current_phase: str
    target_date: str
    created_at: float
    timeline: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "order_id": self.order_id,
            "client_id": self.client_id,
            "article_name": self.article_name,
            "quantity": self.quantity,
            "scheme": self.scheme,
            "status": self.status,
            "progress": self.progress,
            "current_phase": self.current_phase,
            "target_date": self.target_date,
            "created_at": self.created_at,
            "timeline": self.timeline,
        }


@dataclass
class StockLot:
    lot_id: str
    client_id: str
    material_code: str
    material_name: str
    unit: str
    quantity_available: float
    received_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "lot_id": self.lot_id,
            "client_id": self.client_id,
            "material_code": self.material_code,
            "material_name": self.material_name,
            "unit": self.unit,
            "quantity_available": self.quantity_available,
            "received_at": self.received_at,
        }


@dataclass
class PortalRequest:
    request_id: str
    client_id: str
    kind: str  # "order" | "sample"
    article_name: str
    quantity: int
    scheme: str
    target_date: str
    notes: str
    status: str  # submitted | review | approved | rejected
    created_at: float
    updated_at: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "client_id": self.client_id,
            "kind": self.kind,
            "article_name": self.article_name,
            "quantity": self.quantity,
            "scheme": self.scheme,
            "target_date": self.target_date,
            "notes": self.notes,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


def _otp_hash(identifier_key: str, otp: str) -> str:
    return hashlib.sha256(f"{identifier_key}:{otp}".encode()).hexdigest()


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


# ── Store ────────────────────────────────────────────────────────────────────


class PortalStore:
    """Thread-safe, process-local, client-scoped store."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._users: dict[str, ClientUser] = {}
        self._index: dict[str, str] = {}  # "kind:value" -> user_id
        self._sessions: dict[str, Session] = {}  # token_hash -> session
        self._otps: dict[str, OtpChallenge] = {}  # identifier_key -> challenge
        self._orders: dict[str, Order] = {}
        self._stock: dict[str, StockLot] = {}
        self._requests: dict[str, PortalRequest] = {}

    # -- internals ----------------------------------------------------------

    @staticmethod
    def _candidate_keys(identifier: str) -> list[str]:
        raw = identifier.strip()
        keys: list[str] = []
        if "@" in raw:
            keys.append(f"email:{normalize_email(raw)}")
        if re.search(r"\d", raw):
            keys.append(f"phone:{normalize_phone(raw)}")
        return keys

    def _match(self, identifier: str) -> tuple[ClientUser | None, str | None]:
        for key in self._candidate_keys(identifier):
            user_id = self._index.get(key)
            if user_id and user_id in self._users:
                return self._users[user_id], key
        return None, None

    def _is_duplicate(self, email: str, phone: str) -> bool:
        return f"email:{email}" in self._index or f"phone:{phone}" in self._index

    def _revoke_user_sessions(self, user_id: str) -> None:
        stale = [h for h, s in self._sessions.items() if s.user_id == user_id]
        for token_hash in stale:
            del self._sessions[token_hash]

    def _add_user(
        self,
        *,
        client_id: str,
        company_name: str,
        contact_name: str,
        email: str,
        phone: str,
        password: str,
        role: str,
        status: str,
    ) -> ClientUser:
        now = time.time()
        user = ClientUser(
            user_id=str(uuid.uuid4()),
            client_id=client_id,
            company_name=company_name.strip(),
            contact_name=contact_name.strip(),
            email=normalize_email(email),
            phone=normalize_phone(phone),
            password_hash=hash_password(password),
            role=role,
            status=status,
            created_at=now,
            updated_at=now,
        )
        self._users[user.user_id] = user
        self._index[f"email:{user.email}"] = user.user_id
        if user.phone:
            self._index[f"phone:{user.phone}"] = user.user_id
        return user

    # -- seeding ------------------------------------------------------------

    def seed_admin(self, email: str, password: str, full_name: str = "Admin Ops") -> ClientUser:
        with self._lock:
            existing = self._index.get(f"email:{normalize_email(email)}")
            if existing:
                return self._users[existing]
            return self._add_user(
                client_id="",
                company_name="Lukla Manufacturing",
                contact_name=full_name,
                email=email,
                phone="",
                password=password,
                role="admin",
                status="active",
            )

    def seed_client(
        self,
        *,
        client_id: str,
        company_name: str,
        contact_name: str,
        email: str,
        phone: str,
        password: str,
    ) -> ClientUser:
        """Create an already-active client login (demo fixtures)."""
        with self._lock:
            return self._add_user(
                client_id=client_id,
                company_name=company_name,
                contact_name=contact_name,
                email=email,
                phone=phone,
                password=password,
                role="client",
                status="active",
            )

    def seed_order(
        self,
        *,
        client_id: str,
        order_id: str,
        article_name: str,
        quantity: int,
        scheme: str,
        status: str,
        progress: int,
        current_phase: str,
        target_date: str,
        timeline: list[dict[str, str]] | None = None,
    ) -> Order:
        with self._lock:
            order = Order(
                order_id=order_id,
                client_id=client_id,
                article_name=article_name,
                quantity=quantity,
                scheme=scheme,
                status=status,
                progress=progress,
                current_phase=current_phase,
                target_date=target_date,
                created_at=time.time(),
                timeline=timeline or [],
            )
            self._orders[order_id] = order
            return order

    def seed_stock(
        self,
        *,
        client_id: str,
        material_code: str,
        material_name: str,
        unit: str,
        quantity_available: float,
        received_at: str,
    ) -> StockLot:
        with self._lock:
            lot = StockLot(
                lot_id=str(uuid.uuid4()),
                client_id=client_id,
                material_code=material_code,
                material_name=material_name,
                unit=unit,
                quantity_available=quantity_available,
                received_at=received_at,
            )
            self._stock[lot.lot_id] = lot
            return lot

    # -- client lifecycle ---------------------------------------------------

    def register_client(
        self,
        *,
        company_name: str,
        contact_name: str,
        email: str,
        phone: str,
        password: str,
    ) -> ClientUser:
        with self._lock:
            normalized_email = normalize_email(email)
            normalized_phone = normalize_phone(phone)
            if self._is_duplicate(normalized_email, normalized_phone):
                raise PortalError(
                    "DUPLICATE_IDENTITY",
                    "Email atau nomor HP sudah terdaftar.",
                )
            client_id = f"CL-{uuid.uuid4().hex[:6].upper()}"
            return self._add_user(
                client_id=client_id,
                company_name=company_name,
                contact_name=contact_name,
                email=email,
                phone=phone,
                password=password,
                role="client",
                status="pending",
            )

    def authenticate(self, identifier: str, password: str) -> ClientUser:
        with self._lock:
            user, _ = self._match(identifier)
            if user is None or not verify_password(password, user.password_hash):
                raise PortalError("INVALID_CREDENTIALS", "Identitas atau password salah.")
            if user.status == "pending":
                raise PortalError(
                    "ACCOUNT_PENDING",
                    "Akun masih menunggu verifikasi tim internal Lukla.",
                )
            if user.status == "rejected":
                raise PortalError(
                    "ACCOUNT_REJECTED",
                    "Pengajuan akun ditolak. Hubungi tim internal Lukla.",
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

    def get_session_user(self, token: str) -> ClientUser | None:
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
                raise PortalError("AUTH_REQUIRED", "Sesi tidak valid.")
            if not verify_password(current, user.password_hash):
                raise PortalError("INVALID_CREDENTIALS", "Password saat ini salah.")
            if current == new:
                raise PortalError(
                    "SAME_PASSWORD", "Password baru harus berbeda dari password lama."
                )
            user.password_hash = hash_password(new)
            user.updated_at = time.time()
            self._revoke_user_sessions(user_id)

    # -- OTP (forgot/reset password) ---------------------------------------

    def create_otp(
        self, identifier: str, ttl_seconds: int, cooldown_seconds: int
    ) -> tuple[str, ClientUser] | None:
        with self._lock:
            user, key = self._match(identifier)
            if user is None or key is None:
                return None
            now = time.time()
            existing = self._otps.get(key)
            if existing and now - existing.last_sent_at < cooldown_seconds:
                raise PortalError("OTP_COOLDOWN", "Mohon tunggu sebelum meminta kode baru.")
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

    def list_pending_clients(self) -> list[ClientUser]:
        with self._lock:
            return sorted(
                (u for u in self._users.values() if u.role == "client" and u.status == "pending"),
                key=lambda u: u.created_at,
            )

    def set_client_status(self, user_id: str, status: str) -> ClientUser:
        with self._lock:
            user = self._users.get(user_id)
            if user is None:
                raise PortalError("NOT_FOUND", "Pengajuan tidak ditemukan.")
            user.status = status
            user.updated_at = time.time()
            if status != "active":
                self._revoke_user_sessions(user_id)
            return user

    # -- client-scoped data (the isolation boundary) ------------------------

    def list_orders(self, client_id: str) -> list[Order]:
        with self._lock:
            rows = [o for o in self._orders.values() if o.client_id == client_id]
            return sorted(rows, key=lambda o: o.created_at, reverse=True)

    def get_order(self, client_id: str, order_id: str) -> Order | None:
        with self._lock:
            order = self._orders.get(order_id)
            if order is None or order.client_id != client_id:
                return None
            return order

    def list_stock(self, client_id: str) -> list[StockLot]:
        with self._lock:
            rows = [s for s in self._stock.values() if s.client_id == client_id]
            return sorted(rows, key=lambda s: s.material_name)

    def list_requests(self, client_id: str) -> list[PortalRequest]:
        with self._lock:
            rows = [r for r in self._requests.values() if r.client_id == client_id]
            return sorted(rows, key=lambda r: r.created_at, reverse=True)

    def get_request(self, client_id: str, request_id: str) -> PortalRequest | None:
        with self._lock:
            req = self._requests.get(request_id)
            if req is None or req.client_id != client_id:
                return None
            return req

    def create_request(
        self,
        *,
        client_id: str,
        kind: str,
        article_name: str,
        quantity: int,
        scheme: str,
        target_date: str,
        notes: str,
    ) -> PortalRequest:
        with self._lock:
            now = time.time()
            req = PortalRequest(
                request_id=str(uuid.uuid4()),
                client_id=client_id,
                kind=kind,
                article_name=article_name.strip(),
                quantity=quantity,
                scheme=scheme,
                target_date=target_date.strip(),
                notes=notes.strip(),
                status="submitted",
                created_at=now,
                updated_at=now,
            )
            self._requests[req.request_id] = req
            return req

    def summary(self, client_id: str) -> dict[str, int]:
        with self._lock:
            orders = [o for o in self._orders.values() if o.client_id == client_id]
            requests = [r for r in self._requests.values() if r.client_id == client_id]
            stock = [s for s in self._stock.values() if s.client_id == client_id]
            return {
                "active_orders": sum(1 for o in orders if o.status != "completed"),
                "completed_orders": sum(1 for o in orders if o.status == "completed"),
                "pending_requests": sum(1 for r in requests if r.status in {"submitted", "review"}),
                "consigned_lots": len(stock),
                "total_orders": len(orders),
            }


# ── Process-wide singleton ───────────────────────────────────────────────────

_store = PortalStore()


def get_store() -> PortalStore:
    return _store
