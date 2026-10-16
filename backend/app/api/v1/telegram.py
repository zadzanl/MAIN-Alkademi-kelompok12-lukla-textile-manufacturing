"""
Telegram Copilot Bot Webhook and Admin Enrollment/Revocation Router.

Routes:
- POST /api/v1/telegram/webhook
- POST /api/v1/telegram/admin/enrollment-codes
- POST /api/v1/telegram/admin/bindings/{telegram_chat_id}/revoke
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Header, Path, Request, status

from ...copilot.schemas import ChatTurnRequest
from ...core.auth import AuthContext, create_access_token, get_current_admin_auth_context
from ...core.config import settings
from ...schemas.problem import ProblemException
from ...telegram.schemas import (
    EnrollmentCodeCreateRequest,
    EnrollmentCodeCreateResponse,
    TelegramBindingRevokeResponse,
    TelegramUpdate,
    TelegramWebhookResponse,
)
from ...telegram.security import redact_chat_id, verify_webhook_secret
from ...telegram.store import (
    consume_enrollment_code,
    resolve_active_telegram_binding,
    telegram_store,
)
from ...telegram.transport import send_message
from .copilot import _execute_copilot_turn

logger = logging.getLogger("lukla.security.audit")

router = APIRouter(prefix="/telegram", tags=["telegram-copilot"])

UNBOUND_ACCESS_DENIED_MESSAGE = (
    "Akses ditolak: akun Telegram ini belum terdaftar atau kode pendaftaran tidak valid. "
    "Silakan hubungi Administrator Lukla untuk mendapatkan kode pendaftaran sekali pakai (`/start <kode>`)."
)

ENROLLMENT_SUCCESS_TEMPLATE = (
    "Akun Telegram Anda berhasil didaftarkan ke Lukla Intelligence dengan peran: {role}. "
    "Anda sekarang dapat mengirimkan pertanyaan operasional (read-only)."
)


async def handle_telegram_update(request: Request, update: TelegramUpdate) -> TelegramWebhookResponse:
    """
    Core webhook handler enforcing:
    1. Private chat isolation (group/supergroup/channel rejected in first release).
    2. Transactional `update_id` idempotency so Telegram retries never trigger duplicate inference.
    3. `/start <code>` single-use enrollment binding.
    4. Active server-side binding lookup and server-minted JWT context for downstream read tools.
    """
    msg = update.message
    if msg is None or not msg.text:
        return TelegramWebhookResponse(ok=True, status="EMPTY_MESSAGE_IGNORED")

    chat_type = (msg.chat.type or "").lower()
    chat_id_str = str(msg.chat.id)

    # Reject non-private chats before claiming update or invoking Copilot
    if chat_type != "private":
        telegram_store.claim_update_id(update.update_id, chat_id_str)
        return TelegramWebhookResponse(ok=True, status="GROUP_CHAT_REJECTED")

    # Claim update_id for idempotency
    if not telegram_store.claim_update_id(update.update_id, chat_id_str):
        return TelegramWebhookResponse(ok=True, status="DUPLICATE_IGNORED")

    text = msg.text.strip()
    max_len = getattr(settings, "TELEGRAM_MAX_MESSAGE_LENGTH", 2000)
    if len(text) > max_len:
        text = text[:max_len]

    # Handle `/start <code>` single-use enrollment flow
    if text.startswith("/start"):
        parts = text.split(maxsplit=1)
        supplied_code = parts[1].strip() if len(parts) == 2 else ""
        binding = consume_enrollment_code(supplied_code, chat_id_str) if supplied_code else None
        if binding is None:
            await send_message(chat_id_str, UNBOUND_ACCESS_DENIED_MESSAGE)
            return TelegramWebhookResponse(ok=True, status="UNBOUND_REJECTED")

        role_display = ", ".join(binding.roles)
        await send_message(chat_id_str, ENROLLMENT_SUCCESS_TEMPLATE.format(role=role_display))
        logger.info(
            "Telegram chat enrolled: chat=%s actor_id=%s tenant_id=%s roles=%s",
            redact_chat_id(chat_id_str),
            binding.actor_id,
            binding.tenant_id,
            binding.roles,
        )
        return TelegramWebhookResponse(ok=True, status="ENROLLED")

    # Resolve server-side active binding; never trust Telegram username or caller headers/body
    binding = resolve_active_telegram_binding(chat_id_str)
    if binding is None or not binding.active:
        await send_message(chat_id_str, UNBOUND_ACCESS_DENIED_MESSAGE)
        return TelegramWebhookResponse(ok=True, status="UNBOUND_REJECTED")

    # Mint a short-lived internal Bearer JWT strictly from the server-verified binding
    # so downstream read tools (`/api/v1/stock`, `/api/v1/ledger/entries`, etc.) enforce
    # the bound actor's exact tenant_id, actor_id, and role.
    internal_jwt = create_access_token(
        {
            "sub": str(binding.actor_id),
            "actor_id": str(binding.actor_id),
            "tenant_id": str(binding.tenant_id),
            "roles": list(binding.roles),
        }
    )

    history = telegram_store.get_recent_history(chat_id_str)
    chat_req = ChatTurnRequest(
        message=text,
        history=history if history else None,
        roles=list(binding.roles),
        stream=False,
    )

    copilot_resp = await _execute_copilot_turn(
        request=request,
        body=chat_req,
        trusted_roles=list(binding.roles),
        trusted_authorization_header=f"Bearer {internal_jwt}",
    )

    reply_text = copilot_resp.reply
    if copilot_resp.shortcuts:
        shortcut_lines = [
            f"\n\n[Pintasan Web Read-Only] {sc.title}: {sc.url}"
            for sc in copilot_resp.shortcuts
        ]
        reply_text = f"{reply_text}{''.join(shortcut_lines)}"

    telegram_store.append_history_turn(chat_id_str, text, reply_text)
    await send_message(chat_id_str, reply_text)

    return TelegramWebhookResponse(
        ok=True,
        status="PROCESSED",
        tools_used=copilot_resp.tools_used,
    )


@router.post(
    "/webhook",
    response_model=TelegramWebhookResponse,
    status_code=status.HTTP_200_OK,
    summary="Inbound Telegram Bot API Webhook",
    operation_id="telegramCopilotWebhook",
)
async def telegram_webhook(
    request: Request,
    update: TelegramUpdate,
    x_telegram_bot_api_secret_token: Optional[str] = Header(
        default=None, alias="X-Telegram-Bot-Api-Secret-Token"
    ),
) -> TelegramWebhookResponse:
    if not getattr(settings, "TELEGRAM_BOT_ENABLED", False):
        raise ProblemException(
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
            code="SERVICE_SCOPE_REQUIRED",
            detail="Telegram Copilot Bot webhook is currently disabled",
            instance=request.url.path,
        )

    verify_webhook_secret(x_telegram_bot_api_secret_token, instance_path=request.url.path)
    return await handle_telegram_update(request=request, update=update)


@router.post(
    "/admin/enrollment-codes",
    response_model=EnrollmentCodeCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate Single-Use Telegram Enrollment Code (Admin Only)",
    operation_id="createTelegramEnrollmentCode",
)
async def create_enrollment_code_endpoint(
    body: EnrollmentCodeCreateRequest,
    auth: AuthContext = Depends(get_current_admin_auth_context),
) -> EnrollmentCodeCreateResponse:
    target_tenant_id = body.tenant_id or auth.tenant_id
    if target_tenant_id != auth.tenant_id:
        raise ProblemException(
            status=status.HTTP_403_FORBIDDEN,
            code="FORBIDDEN",
            detail="Cannot issue enrollment codes for a different tenant scope",
            instance="/api/v1/telegram/admin/enrollment-codes",
        )

    target_actor_id = body.actor_id or auth.actor_id
    if target_actor_id is None:
        raise ProblemException(
            status=status.HTTP_400_BAD_REQUEST,
            code="VALIDATION_ERROR",
            detail="actor_id is required to bind a Telegram chat to a verified actor",
            instance="/api/v1/telegram/admin/enrollment-codes",
        )

    raw_code, expires_at = telegram_store.create_enrollment_code(
        role=body.role,
        actor_id=target_actor_id,
        tenant_id=target_tenant_id,
        legal_owner_id=body.legal_owner_id,
        expires_in_seconds=body.expires_in_seconds,
    )

    logger.info(
        "Admin created Telegram enrollment code: admin_actor=%s target_actor=%s tenant=%s role=%s expires_at=%s",
        auth.actor_id,
        target_actor_id,
        target_tenant_id,
        body.role,
        expires_at.isoformat(),
    )

    return EnrollmentCodeCreateResponse(
        code=raw_code,
        role=body.role,
        actor_id=target_actor_id,
        tenant_id=target_tenant_id,
        expires_at=expires_at,
    )


@router.post(
    "/admin/bindings/{telegram_chat_id}/revoke",
    response_model=TelegramBindingRevokeResponse,
    status_code=status.HTTP_200_OK,
    summary="Revoke Active Telegram Chat Binding (Admin Only)",
    operation_id="revokeTelegramBinding",
)
async def revoke_telegram_binding_endpoint(
    telegram_chat_id: str = Path(..., min_length=1, max_length=64),
    auth: AuthContext = Depends(get_current_admin_auth_context),
) -> TelegramBindingRevokeResponse:
    revoked_at = telegram_store.revoke_binding(telegram_chat_id)
    logger.info(
        "Admin revoked Telegram binding: admin_actor=%s tenant=%s chat=%s",
        auth.actor_id,
        auth.tenant_id,
        redact_chat_id(telegram_chat_id),
    )
    return TelegramBindingRevokeResponse(
        telegram_chat_id=str(telegram_chat_id),
        status="REVOKED",
        revoked_at=revoked_at,
    )
