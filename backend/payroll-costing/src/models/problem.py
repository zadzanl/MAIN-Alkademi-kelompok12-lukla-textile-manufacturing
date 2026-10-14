"""Contract ``Problem`` response model and its error code enumeration."""

from enum import StrEnum
from uuid import UUID

from pydantic import Field

from src.models.base import ContractModel


class ErrorCode(StrEnum):
    """The complete ``Problem.code`` enumeration from the frozen contract."""

    AUTH_REQUIRED = "AUTH_REQUIRED"
    FORBIDDEN = "FORBIDDEN"
    TENANT_CONTEXT_MISSING = "TENANT_CONTEXT_MISSING"
    LEGAL_OWNER_MISMATCH = "LEGAL_OWNER_MISMATCH"
    ORDER_BENEFICIARY_MISMATCH = "ORDER_BENEFICIARY_MISMATCH"
    IDEMPOTENCY_CONFLICT = "IDEMPOTENCY_CONFLICT"
    INVALID_STATE = "INVALID_STATE"
    LEDGER_IMMUTABLE = "LEDGER_IMMUTABLE"
    DUPLICATE_REPAIR_CREDIT = "DUPLICATE_REPAIR_CREDIT"
    FINANCIAL_RULE_PENDING = "FINANCIAL_RULE_PENDING"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INSUFFICIENT_STOCK = "INSUFFICIENT_STOCK"
    OVER_CONSUMPTION = "OVER_CONSUMPTION"
    SERVICE_SCOPE_REQUIRED = "SERVICE_SCOPE_REQUIRED"


class Violation(ContractModel):
    """A single field-level validation failure."""

    field: str
    message: str


class Problem(ContractModel):
    """The RFC 9457-style problem document every error response uses."""

    type: str
    title: str
    status: int = Field(ge=400, le=599)
    code: ErrorCode
    detail: str
    instance: str
    request_id: UUID
    violations: list[Violation] | None = None
