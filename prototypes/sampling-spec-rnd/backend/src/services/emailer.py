"""emailer.py — Minimal SMTP sender with a development fallback.

Reads SMTP_* settings from the environment. When ``SMTP_HOST`` is unset (the
default for local development) it does not connect anywhere: it logs the message
so the OTP is still retrievable during testing.

Known ceiling: synchronous send, no retry/queue. Upgrade path: hand off to the
production outbox/notification service when one exists.
"""

from __future__ import annotations

import logging
import os
import smtplib
from email.message import EmailMessage

logger = logging.getLogger("lukla.portal.auth.email")


def smtp_configured() -> bool:
    return bool(os.getenv("SMTP_HOST", "").strip())


def send_email(to: str, subject: str, body: str) -> str:
    """Send a plain-text email. Returns ``sent``, ``dev-log`` or ``error``.

    Transport failures are logged, never raised: the caller must not leak
    delivery status to the client (anti-enumeration).
    """
    sender = os.getenv("SMTP_FROM", "no-reply@lukla.local")

    if not smtp_configured():
        logger.warning("[DEV EMAIL] to=%s subject=%s\n%s", to, subject, body)
        return "dev-log"

    message = EmailMessage()
    message["From"] = sender
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)

    host = os.environ["SMTP_HOST"]
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER", "")
    password = os.getenv("SMTP_PASSWORD", "")
    use_ssl = os.getenv("SMTP_SSL", "false").strip().lower() == "true"
    use_tls = os.getenv("SMTP_TLS", "true").strip().lower() == "true"

    try:
        if use_ssl:
            with smtplib.SMTP_SSL(host, port, timeout=10) as server:
                if user:
                    server.login(user, password)
                server.send_message(message)
        else:
            with smtplib.SMTP(host, port, timeout=10) as server:
                if use_tls:
                    server.starttls()
                if user:
                    server.login(user, password)
                server.send_message(message)
        return "sent"
    except (OSError, smtplib.SMTPException) as exc:
        logger.error("SMTP send failed: %s", exc)
        return "error"
