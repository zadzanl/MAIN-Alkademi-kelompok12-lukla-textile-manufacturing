"""Checked repository operations for the approved aggregate payroll path."""

from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.models.money import Money
from src.models.payroll_calculation import PayrollResult, PayrollResultStatus
from src.repositories.periods import get_payroll_period
from src.repositories.rules import get_required_versions

_READ_RUN = text("SELECT payroll_read_rows('payroll_runs', :run_id, :after_id, :page_size)")
_READ_WAGES = text("SELECT payroll_read_rows('wage_credits', :credit_id, :after_id, :page_size)")


def _read_one(db: Session, row_id: UUID) -> dict[str, object] | None:
    row = db.execute(
        _READ_RUN,
        {"run_id": row_id, "after_id": None, "page_size": 1},
    ).scalar_one_or_none()
    return row if isinstance(row, dict) else None


def _read_period_wages(db: Session, period_id: UUID) -> list[dict[str, object]]:
    rows = (
        db.execute(
            _READ_WAGES,
            {"credit_id": None, "after_id": None, "page_size": 1000},
        )
        .scalars()
        .all()
    )
    return [
        row for row in rows if isinstance(row, dict) and str(row.get("period_id")) == str(period_id)
    ]


def calculate_weekly_payroll(
    db: Session, tenant_id: UUID, period_id: UUID, rule_version: UUID
) -> PayrollResult:
    """Run the existing atomic SQL calculation and serialize its aggregate result.

    The rule lookup happens before the SQL routine. A pending or missing rule
    therefore raises before any monetary insert is attempted.
    """
    period = get_payroll_period(db, tenant_id, period_id)
    get_required_versions(db, tenant_id, [rule_version], period.starts_on)
    rule_row = db.execute(
        text("SELECT payroll_read_rows('financial_rule_versions', :rule_id)"),
        {"rule_id": rule_version},
    ).scalar_one_or_none()
    if not isinstance(rule_row, dict) or not isinstance(rule_row.get("parameters"), dict):
        raise ValueError("Financial rule reader returned invalid parameters")
    parameters = rule_row["parameters"]
    bonus_rate = parameters.get("bonusRate")
    currency = bonus_rate.get("currency") if isinstance(bonus_rate, dict) else None
    if not isinstance(currency, str) or not currency:
        raise ValueError("Approved financial rule has no currency")

    # The SQL routine is the invariant boundary: it creates no rows for a
    # blocked rule and returns NULL for a valid zero-output period.
    run_id = db.execute(
        text("SELECT calculate_weekly_payroll(:period_id, :rule_version)"),
        {"period_id": period_id, "rule_version": rule_version},
    ).scalar_one()
    if run_id is None:
        return PayrollResult(
            period_id=period_id,
            status=PayrollResultStatus.NO_OUTPUT,
            eligible_units=0,
            total_wages=Money(amount_minor=0, currency=currency),
        )
    if _read_one(db, run_id) is None:
        raise ValueError("Payroll calculation returned an unreadable run")
    wages = _read_period_wages(db, period_id)
    total = sum(int(row["amount_minor"]) for row in wages)
    return PayrollResult(
        period_id=period_id,
        status=PayrollResultStatus.CALCULATED if wages else PayrollResultStatus.NO_OUTPUT,
        eligible_units=len(wages),
        total_wages=Money(amount_minor=total, currency=currency),
    )
