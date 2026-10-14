"""Payroll period schemas and the frozen period status enumeration."""

from datetime import date
from enum import StrEnum
from typing import Final, Literal
from uuid import UUID

from pydantic import Field

from src.models.base import ContractModel

CUTOFF_LOCAL_PATTERN: Final = r"^([01][0-9]|2[0-3]):[0-5][0-9]:00$"


class PayrollPeriodStatus(StrEnum):
    """The six statuses the frozen schema allows for ``payroll_periods.status``."""

    OPEN = "OPEN"
    CALCULATED = "CALCULATED"
    PENDING_RULE = "PENDING_RULE"
    APPROVED = "APPROVED"
    PAID = "PAID"
    REVERSED = "REVERSED"


class PeriodRequest(ContractModel):
    """Body of ``createPayrollPeriod``.

    The contract fixes the timezone to a single value and constrains the cutoff
    to a whole minute, so both are validated here rather than at the router.
    """

    starts_on: date
    ends_on: date
    timezone: Literal["Asia/Jakarta"]
    cutoff_local: str = Field(pattern=CUTOFF_LOCAL_PATTERN)
    rule_version: str


class Period(PeriodRequest):
    """A stored period. The contract exposes no status on this response."""

    id: UUID


class PeriodPage(ContractModel):
    """Body of ``listPayrollPeriods``."""

    items: list[Period]
