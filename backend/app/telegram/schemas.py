"""
Strict Pydantic schemas for Telegram Bot API updates, enrollment requests,
persistent bindings, and administrative responses.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


CANONICAL_COPILOT_ROLES = {
    "Owner",
    "SampleTeam",
    "Warehouse",
    "ProductionHead",
    "Tailor",
    "QCInspector",
    "FinancePayroll",
    "MaklonClient",
}


class TelegramChat(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int | str
    type: str = Field(..., description="Chat type: private, group, supergroup, or channel")
    username: Optional[str] = None
    first_name: Optional[str] = None


class TelegramUser(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int | str
    is_bot: bool = False
    first_name: Optional[str] = None
    username: Optional[str] = None


class TelegramMessage(BaseModel):
    model_config = ConfigDict(extra="ignore")

    message_id: int
    date: Optional[int] = None
    chat: TelegramChat
    from_user: Optional[TelegramUser] = Field(default=None, alias="from")
    text: Optional[str] = Field(default=None, max_length=4096)


class TelegramUpdate(BaseModel):
    """
    Inbound Telegram Bot API Update payload.
    Ignores untrusted extra fields (e.g., spoofed `roles`) so they can never be consumed.
    """
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    update_id: int = Field(..., ge=1)
    message: Optional[TelegramMessage] = None


class EnrollmentCodeCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: str = Field(..., description="Canonical Lukla role to grant upon enrollment")
    actor_id: Optional[uuid.UUID] = Field(default=None, description="Verified actor UUID")
    tenant_id: Optional[uuid.UUID] = Field(default=None, description="Verified tenant UUID")
    legal_owner_id: Optional[uuid.UUID] = Field(default=None, description="Optional client legal owner scope UUID")
    expires_in_seconds: int = Field(default=900, ge=60, le=86400)

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str) -> str:
        cleaned = value.strip()
        if cleaned not in CANONICAL_COPILOT_ROLES:
            raise ValueError(f"Role '{cleaned}' is not a valid Lukla Assistant role")
        return cleaned


class EnrollmentCodeCreateResponse(BaseModel):
    code: str = Field(..., description="One-time enrollment code (returned only once; never stored in plaintext)")
    role: str
    actor_id: uuid.UUID
    tenant_id: uuid.UUID
    expires_at: datetime


class TelegramBinding(BaseModel):
    telegram_chat_id: str
    actor_id: uuid.UUID
    tenant_id: uuid.UUID
    roles: List[str]
    legal_owner_id: Optional[uuid.UUID] = None
    active: bool = True
    created_at: datetime
    revoked_at: Optional[datetime] = None


class TelegramBindingRevokeResponse(BaseModel):
    telegram_chat_id: str
    status: Literal["REVOKED"] = "REVOKED"
    revoked_at: datetime


class TelegramWebhookResponse(BaseModel):
    ok: bool = True
    status: Literal[
        "PROCESSED",
        "ENROLLED",
        "DUPLICATE_IGNORED",
        "UNBOUND_REJECTED",
        "GROUP_CHAT_REJECTED",
        "EMPTY_MESSAGE_IGNORED",
    ]
    tools_used: List[str] = Field(default_factory=list)
