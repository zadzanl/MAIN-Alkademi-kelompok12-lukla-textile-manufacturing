"""Payroll period lifecycle.

A period is the container a weekly run is calculated against. Its status moves
through a fixed set of transitions; anything else is refused with
``INVALID_STATE``. The frozen rules behind the table:

- a calculation yields ``CALCULATED``, or ``PENDING_RULE`` while a referenced
  rule version is not approved (``PayrollResult.status`` in the contract);
- "Payroll refuses approval when any required rule is PENDING or QC/payment
  inputs are not final" and "Approval freezes contributing credit IDs, rules and
  amounts", so approval leaves ``CALCULATED`` only, and an approved period is
  never recalculated;
- "Payment recording references the approved run", so payment needs ``APPROVED``;
- "late credits go to a later open period, never mutate a paid run", so a paid
  period is terminal except for its reversal, which is a compensating entry.

An edge that is not in the table is refused. Add one only with a source.
"""

from typing import Final
from uuid import UUID

from src.models.payroll_period import (
    PayrollPeriodStatus,
    Period,
    PeriodRequest,
)
from src.services.errors import InvalidState, ValidationFailed

CALCULATED: Final = PayrollPeriodStatus.CALCULATED
PENDING_RULE: Final = PayrollPeriodStatus.PENDING_RULE
APPROVED: Final = PayrollPeriodStatus.APPROVED
PAID: Final = PayrollPeriodStatus.PAID
REVERSED: Final = PayrollPeriodStatus.REVERSED

ALLOWED_TRANSITIONS: Final[dict[PayrollPeriodStatus, frozenset[PayrollPeriodStatus]]] = {
    PayrollPeriodStatus.OPEN: frozenset({CALCULATED, PENDING_RULE}),
    PENDING_RULE: frozenset({CALCULATED, PENDING_RULE}),
    CALCULATED: frozenset({CALCULATED, PENDING_RULE, APPROVED}),
    APPROVED: frozenset({PAID}),
    PAID: frozenset({REVERSED}),
    REVERSED: frozenset(),
}


def assert_valid_period_range(request: PeriodRequest) -> None:
    """A period must cover at least one day, or it can never carry output."""
    if request.ends_on <= request.starts_on:
        raise ValidationFailed("endsOn must be after startsOn")


def create_period(request: PeriodRequest, period_id: UUID) -> Period:
    """Open a new period, which starts in ``OPEN`` and cannot be calculated yet."""
    assert_valid_period_range(request)
    return Period(id=period_id, **request.model_dump())


def assert_transition_allowed(current: PayrollPeriodStatus, target: PayrollPeriodStatus) -> None:
    """Raise ``InvalidState`` unless the period may move from ``current`` to ``target``."""
    if target not in ALLOWED_TRANSITIONS[current]:
        raise InvalidState(f"Payroll period cannot move from {current} to {target}")
