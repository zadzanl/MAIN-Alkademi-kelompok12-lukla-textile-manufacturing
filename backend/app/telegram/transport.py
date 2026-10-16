"""
Minimal async Telegram Bot API client (`sendMessage` and `setWebhook`) with
bounded timeouts, plain-text fallback, and no unbounded retries.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import httpx

from ..core.config import settings
from .security import redact_chat_id

logger = logging.getLogger("lukla.telegram.transport")

TELEGRAM_API_BASE_URL = "https://api.telegram.org"
MAX_TELEGRAM_TEXT_LENGTH = 4000


def _sanitize_outbound_text(text: str) -> str:
    cleaned = (text or "").strip()
    if not cleaned:
        cleaned = "Tidak ada balasan dari sistem."
    if len(cleaned) > MAX_TELEGRAM_TEXT_LENGTH:
        cleaned = cleaned[: MAX_TELEGRAM_TEXT_LENGTH - 3] + "..."
    return cleaned


async def send_message(
    chat_id: str | int,
    text: str,
    bot_token: Optional[str] = None,
    timeout_seconds: float = 5.0,
) -> bool:
    """
    Send a plain-text reply via Telegram Bot API `sendMessage`.
    Never raises on Telegram network/429/5xx errors so upstream enrollment or Copilot
    processing is never rolled back (AC-7). Returns True on HTTP 200, False otherwise.
    """
    token = bot_token if bot_token is not None else getattr(settings, "TELEGRAM_BOT_TOKEN", "")
    if not token:
        logger.warning(
            "Telegram send_message skipped: TELEGRAM_BOT_TOKEN is not configured (chat=%s)",
            redact_chat_id(chat_id),
        )
        return False

    url = f"{TELEGRAM_API_BASE_URL}/bot{token}/sendMessage"
    payload: Dict[str, Any] = {
        "chat_id": int(chat_id) if str(chat_id).lstrip("-").isdigit() else str(chat_id),
        "text": _sanitize_outbound_text(text),
    }

    try:
        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            response = await client.post(url, json=payload)
            if response.status_code == 200:
                return True

            logger.warning(
                "Telegram sendMessage returned non-200 status=%s for chat=%s",
                response.status_code,
                redact_chat_id(chat_id),
            )
            return False
    except httpx.HTTPError as exc:
        logger.warning(
            "Telegram sendMessage transport failure (%s) for chat=%s",
            type(exc).__name__,
            redact_chat_id(chat_id),
        )
        return False


async def register_webhook(
    webhook_url: Optional[str] = None,
    secret_token: Optional[str] = None,
    bot_token: Optional[str] = None,
    timeout_seconds: float = 5.0,
) -> bool:
    """Register the HTTPS webhook URL and secret token with Telegram Bot API `setWebhook`."""
    token = bot_token or getattr(settings, "TELEGRAM_BOT_TOKEN", "")
    target_url = webhook_url or getattr(settings, "TELEGRAM_PUBLIC_WEBHOOK_URL", "")
    secret = secret_token or getattr(settings, "TELEGRAM_WEBHOOK_SECRET", "")

    if not token or not target_url or not secret:
        return False

    url = f"{TELEGRAM_API_BASE_URL}/bot{token}/setWebhook"
    payload = {
        "url": target_url,
        "secret_token": secret,
        "allowed_updates": ["message"],
    }
    try:
        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            resp = await client.post(url, json=payload)
            return resp.status_code == 200
    except httpx.HTTPError:
        return False
