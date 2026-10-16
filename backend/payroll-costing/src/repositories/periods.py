"""Payroll period persistence; callers install context and own the transaction.

Ceiling: the checked reader pages by UUID, not calendar date. Add a purpose-built
checked database reader if the period list needs date ordering or filtering.
"""

from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.models.payroll_period import PayrollPeriodStatus, Period, PeriodRequest
from src.services.payroll_periods import assert_transition_allowed, create_period

_PAGE_SIZE = 1000
_READ = text("SELECT payroll_read_rows('payroll_periods', :period_id, :after_id, :page_size)")


def _period_from_row(row: object) -> Period:
    if not isinstance(row, dict):
        raise ValueError("payroll_read_rows returned a non-object period")
    return Period.model_validate(
        {
            "id": row["id"],
            "startsOn": row["period_start"],
            "endsOn": row["period_end"],
            "timezone": row["timezone"],
            "cutoffLocal": row["cutoff_local"],
            "ruleVersion": row["rule_version"],
        }
    )


def _require_tenant(db: Session, tenant_id: UUID) -> None:
    actual = db.execute(text("SELECT payroll_context_tenant()")).scalar_one()
    if actual != tenant_id:
        raise ValueError("tenant_id differs from installed payroll context")


def _get_period(db: Session, period_id: UUID) -> Period:
    row = db.execute(
        _READ, {"period_id": period_id, "after_id": None, "page_size": 1}
    ).scalar_one_or_none()
    if row is None:
        raise LookupError("Payroll period not found in tenant context")
    return _period_from_row(row)


def get_payroll_period(db: Session, tenant_id: UUID, period_id: UUID) -> Period:
    """Read one period through the tenant-checked reader."""
    _require_tenant(db, tenant_id)
    return _get_period(db, period_id)


def create_payroll_period(db: Session, tenant_id: UUID, request: PeriodRequest) -> Period:
    """Insert an OPEN period and checked-read it without committing."""
    period = create_period(request, uuid4())
    _require_tenant(db, tenant_id)
    # A pending version is a valid period reference; a nonexistent/expired one is not.
    from src.repositories.rules import get_required_versions

    get_required_versions(db, tenant_id, [request.rule_version], request.starts_on)
    db.execute(
        text(
            "INSERT INTO payroll_periods "
            "(id, tenant_id, period_start, period_end, timezone, cutoff_local, rule_version) "
            "VALUES (:id, :tenant_id, :starts_on, :ends_on, :timezone, "
            "CAST(:cutoff_local AS time), :rule_version)"
        ),
        {**period.model_dump(), "tenant_id": tenant_id},
    )
    return _get_period(db, period.id)


def list_payroll_periods(db: Session, tenant_id: UUID) -> list[Period]:
    """Read every period in UUID order from the tenant-scoped checked reader."""
    _require_tenant(db, tenant_id)
    periods: list[Period] = []
    after: UUID | None = None
    while True:
        rows = (
            db.execute(_READ, {"period_id": None, "after_id": after, "page_size": _PAGE_SIZE})
            .scalars()
            .all()
        )
        periods.extend(_period_from_row(row) for row in rows)
        if len(rows) < _PAGE_SIZE:
            return periods
        after = periods[-1].id


def transition_period(
    db: Session,
    tenant_id: UUID,
    period_id: UUID,
    expected: PayrollPeriodStatus,
    target: PayrollPeriodStatus,
) -> Period:
    """Compare-and-set via the checked SQL routine; re-read inside the same transaction."""
    assert_transition_allowed(expected, target)
    _require_tenant(db, tenant_id)
    db.execute(
        text("SELECT payroll_transition_period(:period_id, :expected, :target)"),
        {"period_id": period_id, "expected": expected.value, "target": target.value},
    )
    return _get_period(db, period_id)
