"""Schemas for the weekly payroll calculation."""

try:
    from enum import StrEnum
except ImportError:
    from enum import Enum
    class StrEnum(str, Enum):
        pass
from uuid import UUID

from src.models.base import ContractModel
from src.models.money import Money


class PayrollResultStatus(StrEnum):
    """The contract's ``PayrollResult.status`` values.

    ``PENDING_RULE`` is accepted on the wire for contract fidelity, but this
    engine never returns it: the capability spec requires an operation that
    references an unapproved rule to return ``FINANCIAL_RULE_PENDING``, so the
    gate raises that error instead. See the wage calculation module docstring.
    """

    CALCULATED = "CALCULATED"
    NO_OUTPUT = "NO_OUTPUT"
    PENDING_RULE = "PENDING_RULE"


class RuleRequest(ContractModel):
    """Body of ``calculateWeeklyPayroll`` and ``calculateOverhead``."""

    rule_version: UUID


class PayrollResult(ContractModel):
    """Response of ``calculateWeeklyPayroll``; a preview, never a disbursement."""

    period_id: UUID
    status: PayrollResultStatus
    eligible_units: int
    total_wages: Money


class PayrollItem(ContractModel):
    """One recipient line in a persisted payroll statement."""

    recipient_id: UUID
    base: Money
    meal: Money
    bonus: Money


class PayrollStatement(ContractModel):
    """A versioned statement read from a calculated payroll run."""

    period_id: UUID
    version: int
    input_hash: str
    status: str
    items: list[PayrollItem]
    reserve: Money
