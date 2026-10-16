"""Contract models for persisted payroll, overhead, and job operations."""

from enum import StrEnum
from uuid import UUID

from pydantic import Field

from src.models.base import ContractModel
from src.models.money import Money


class PayrollApproval(ContractModel):
    version: int = Field(ge=1)
    input_hash: str = Field(min_length=1)


class PaymentEvidence(ContractModel):
    external_reference: str = Field(min_length=1)
    evidence_file_id: UUID


class BonusRecipient(ContractModel):
    recipient_id: UUID
    amount: Money


class BonusPool(ContractModel):
    period_id: UUID
    pool: Money
    recipients: list[BonusRecipient] = Field(min_length=3, max_length=3)
    status: str


class OverheadRequest(ContractModel):
    period_id: UUID
    kind: str = Field(min_length=1)
    amount: Money


class OverheadEvent(OverheadRequest):
    id: UUID


class OverheadAllocation(ContractModel):
    period_id: UUID
    status: str
    amount_per_unit: Money | None = None


class JobRequest(ContractModel):
    period_id: UUID


class JobAccepted(ContractModel):
    job_id: UUID
    status: str


class JobStatus(StrEnum):
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"


class PayrollStatement(ContractModel):
    period_id: UUID
    version: int = Field(ge=1)
    input_hash: str
    status: str
    items: list["PayrollItem"]
    reserve: Money


class PayrollItem(ContractModel):
    recipient_id: UUID
    base: Money
    meal: Money
    bonus: Money