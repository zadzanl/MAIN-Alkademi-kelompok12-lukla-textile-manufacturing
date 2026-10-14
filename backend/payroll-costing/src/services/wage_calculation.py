"""Weekly piece-rate (borongan) wage calculation.

Only quality-passed units carrying an immutable piece-rate snapshot earn
anything. Unverified tallies never reach this function: verification is what
creates a garment unit, and a unit awaiting inspection stays out of the wage
total until it passes (FR-7.4, FR-8.1).

The financial rule gate runs first. While any referenced rule version is not
``APPROVED`` the calculation raises ``FINANCIAL_RULE_PENDING`` and produces
nothing, which is what the capability spec requires: the operation "SHALL NOT
use a development-only default".

Contract ambiguity, recorded on purpose: ``PayrollResult.status`` enumerates
``PENDING_RULE`` while the same operation also documents a ``409
FinancialRulePending``. The capability spec says an operation referencing an
unapproved rule returns ``FINANCIAL_RULE_PENDING``, so this engine fails closed
with the error and never returns a 200 carrying ``PENDING_RULE``. Escalated for
a contract decision rather than guessed at.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from uuid import UUID

from src.models.garment_unit import GarmentUnitStatus
from src.models.money import Money
from src.models.payroll_calculation import PayrollResult, PayrollResultStatus
from src.services.errors import DuplicateRepairCredit, ValidationFailed
from src.services.rule_gate import RuleReference, require_approved


@dataclass(frozen=True, slots=True)
class EligibleUnit:
    """A garment unit joined to its piece-rate snapshot, as the repository supplies it."""

    unit_id: UUID
    operator_id: UUID
    component_code: str
    rate_minor: int
    currency: str
    status: GarmentUnitStatus


@dataclass(frozen=True, slots=True)
class WageTotal:
    """The borongan aggregate for one period."""

    eligible_units: int
    total_minor: int
    currency: str
    by_operator: Mapping[UUID, int]


def calculate_borongan(units: Sequence[EligibleUnit], *, currency: str) -> WageTotal:
    """Sum the piece-rate snapshots of the quality-passed units.

    Raises ``DuplicateRepairCredit`` if one unit appears twice, because a unit
    carries at most one credit, and ``ValidationFailed`` if a unit is
    denominated in another currency or carries a negative rate.
    """
    seen: set[UUID] = set()
    by_operator: dict[UUID, int] = {}

    for unit in units:
        if unit.status is not GarmentUnitStatus.QC_PASS:
            continue
        if unit.unit_id in seen:
            raise DuplicateRepairCredit(
                f"Garment unit {unit.unit_id} is present more than once in the wage pool"
            )
        seen.add(unit.unit_id)
        if unit.currency != currency:
            raise ValidationFailed(
                f"Garment unit {unit.unit_id} is denominated in {unit.currency}, not {currency}"
            )
        if unit.rate_minor < 0:
            raise ValidationFailed(f"Garment unit {unit.unit_id} carries a negative rate")
        by_operator[unit.operator_id] = by_operator.get(unit.operator_id, 0) + unit.rate_minor

    return WageTotal(
        eligible_units=len(seen),
        total_minor=sum(by_operator.values()),
        currency=currency,
        by_operator=by_operator,
    )


def calculate_weekly_payroll(
    *,
    period_id: UUID,
    required_rules: Sequence[RuleReference],
    units: Sequence[EligibleUnit],
    currency: str,
) -> PayrollResult:
    """Gate first, then aggregate. Persisting the run is the repository's job.

    ``currency`` is the period's currency; it is required even for an empty
    period so that a zero preview is still denominated correctly instead of
    falling back to a hard-coded default.
    """
    require_approved(required_rules)

    totals = calculate_borongan(units, currency=currency)
    status = (
        PayrollResultStatus.CALCULATED if totals.eligible_units else PayrollResultStatus.NO_OUTPUT
    )
    return PayrollResult(
        period_id=period_id,
        status=status,
        eligible_units=totals.eligible_units,
        total_wages=Money(amount_minor=totals.total_minor, currency=currency),
    )
