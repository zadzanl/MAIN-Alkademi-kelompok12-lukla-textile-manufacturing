"""
Security primitives for Telegram Copilot Bot:
- Constant-time webhook secret verification (`hmac.compare_digest`)
- High-entropy single-use enrollment code generation (`secrets.token_urlsafe`)
- Salted SHA-256 code hashing so plaintext codes are never persisted or logged
- Redacted audit logging helpers
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
from typing import Optional

from ..core.config import settings
from ..schemas.problem import ProblemException


def verify_webhook_secret(provided_secret: Optional[str], instance_path: str = "/api/v1/telegram/webhook") -> None:
    """
    Validate `X-Telegram-Bot-Api-Secret-Token` in constant time.
    Raises RFC 7807 401/403 ProblemException before any update processing or Copilot call.
    """
    expected_secret = getattr(settings, "TELEGRAM_WEBHOOK_SECRET", "") or ""
    if not expected_secret:
        raise ProblemException(
            status=503,
            code="SERVICE_SCOPE_REQUIRED",
            detail="Telegram webhook secret is not configured on this server",
            instance=instance_path,
        )

    if not provided_secret:
        raise ProblemException(
            status=401,
            code="AUTH_REQUIRED",
            detail="Missing X-Telegram-Bot-Api-Secret-Token header",
            instance=instance_path,
        )

    if not hmac.compare_digest(provided_secret.encode("utf-8"), expected_secret.encode("utf-8")):
        raise ProblemException(
            status=403,
            code="FORBIDDEN",
            detail="Invalid X-Telegram-Bot-Api-Secret-Token header",
            instance=instance_path,
        )


def generate_enrollment_code() -> str:
    """Generate a high-entropy URL-safe single-use code suitable for `/start <code>`."""
    return secrets.token_urlsafe(18)


def hash_enrollment_code(raw_code: str) -> str:
    """
    Compute a keyed HMAC-SHA256 digest of the enrollment code using the server's SECRET_KEY.
    Raw enrollment codes are never stored at rest or written to logs.
    """
    normalized = raw_code.strip()
    key = (settings.SECRET_KEY or "lukla-telegram-code-pepper").encode("utf-8")
    return hmac.new(key, normalized.encode("utf-8"), hashlib.sha256).hexdigest()


def redact_chat_id(chat_id: str | int) -> str:
    """Return a partially redacted chat ID safe for operational audit logs."""
    raw = str(chat_id)
    if len(raw) <= 4:
        return "***"
    return f"***{raw[-4:]}"
