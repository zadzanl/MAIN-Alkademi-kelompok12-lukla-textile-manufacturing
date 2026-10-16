"""Tenant-scoped persistence for phase-4 statements and phase-5 jobs.

All reads use the checked payroll JSON reader. Mutations stay in the caller's
transaction; callers decide commit or rollback.
"""

from datetime import datetime, date, timezone
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.models.money import Money
from src.models.payroll_operations import (
    BonusPool,
    BonusRecipient,
    JobAccepted,
    JobRequest,
    OverheadAllocation,
    OverheadEvent,
    OverheadRequest,
    PayrollApproval,
    PayrollItem,
    PayrollStatement,
    PaymentEvidence,
)
from src.repositories.payroll import calculate_weekly_payroll
from src.repositories.rules import get_required_versions
from src.services.errors import FinancialRulePending

_READ = text("SELECT payroll_read_rows(:table_name, :row_id, NULL, 1000)")


def _rows(db: Session, table_name: str) -> list[dict[str, object]]:
    rows = db.execute(_READ, {"table_name": table_name, "row_id": None}).scalars().all()
    return [row for row in rows if isinstance(row, dict)]


def _row(db: Session, table_name: str, row_id: UUID) -> dict[str, object]:
    value = db.execute(_READ, {"table_name": table_name, "row_id": row_id}).scalar_one_or_none()
    if not isinstance(value, dict):
        raise LookupError(f"{table_name} row not found")
    return value


def _money(amount: object, currency: object) -> Money:
    return Money(amount_minor=int(amount or 0), currency=str(currency))


def get_statement(db: Session, period_id: UUID) -> PayrollStatement:
    runs = [r for r in _rows(db, "payroll_runs") if str(r.get("period_id")) == str(period_id)]
    if not runs:
        raise LookupError("Payroll statement not found")
    run = max(runs, key=lambda row: int(row["version"]))
    run_id = UUID(str(run["id"]))
    items = [r for r in _rows(db, "payroll_items") if str(r.get("run_id")) == str(run_id)]
    return PayrollStatement(
        period_id=period_id,
        version=int(run["version"]),
        input_hash=bytes(run["input_hash"]).hex() if run.get("input_hash") is not None else "",
        status=str(run["status"]),
        items=[
            PayrollItem(
                recipient_id=UUID(str(row["recipient_id"])),
                base=_money(row["base_minor"], row["currency"]),
                meal=_money(row["meal_minor"], row["currency"]),
                bonus=_money(row["bonus_minor"], row["currency"]),
            )
            for row in items
        ],
        reserve=Money(amount_minor=0, currency=str(items[0]["currency"]) if items else "IDR"),
    )


def get_bonus_pool(db: Session, period_id: UUID) -> BonusPool:
    period = _row(db, "payroll_periods", period_id)
    rule = _row(db, "financial_rule_versions", UUID(str(period["rule_version"])))
    parameters = rule.get("parameters")
    if not isinstance(parameters, dict):
        raise ValueError("Financial rule parameters are invalid")
    bonus_rate = parameters.get("bonusRate")
    if not isinstance(bonus_rate, dict):
        raise ValueError("Financial rule bonusRate is invalid")
    currency = str(bonus_rate.get("currency"))
    recipients = parameters.get("bonusRecipientIds")
    if not isinstance(recipients, list) or len(recipients) != 3:
        raise ValueError("Financial rule must contain exactly three bonus recipients")
    accruals = [
        row for row in _rows(db, "qc_bonus_accruals")
        if str(row.get("created_at", "")) >= str(period["period_start"])
        and str(row.get("created_at", "")) < str(period["period_end"])
    ]
    total = sum(int(row["amount_minor"]) for row in accruals)
    if total % 3:
        raise ValueError("Bonus pool remainder policy is unresolved")
    share = total // 3
    return BonusPool(
        period_id=period_id,
        pool=Money(amount_minor=total, currency=currency),
        recipients=[BonusRecipient(recipient_id=UUID(str(value)), amount=Money(amount_minor=share, currency=currency)) for value in recipients],
        status="CALCULATED" if total else "NO_OUTPUT",
    )


def record_overhead(db: Session, tenant_id: UUID, actor_id: UUID, request: OverheadRequest) -> OverheadEvent:
    event_id = uuid4()
    db.execute(
        text("""INSERT INTO overhead_events
        (id, tenant_id, starts_on, ends_on, rule_version, kind, amount_minor, currency, source_ref, authorized_by)
        SELECT :id, :tenant_id, p.period_start, p.period_end, p.rule_version, :kind,
               :amount_minor, :currency, :source_ref, :actor_id
        FROM payroll_periods p WHERE p.tenant_id = :tenant_id AND p.id = :period_id"""),
        {"id": event_id, "tenant_id": tenant_id, "period_id": request.period_id,
         "kind": request.kind, "amount_minor": request.amount.amount_minor,
         "currency": request.amount.currency, "source_ref": f"payroll-period:{request.period_id}",
         "actor_id": actor_id},
    )
    return OverheadEvent(id=event_id, **request.model_dump())


def calculate_overhead(db: Session, period_id: UUID, rule_version: UUID) -> OverheadAllocation:
    allocation_id = db.execute(
        text("SELECT calculate_overhead_allocation(:period_id, :rule_version)"),
        {"period_id": period_id, "rule_version": rule_version},
    ).scalar_one()
    if allocation_id is None:
        return OverheadAllocation(period_id=period_id, status="NO_OUTPUT")
    row = _row(db, "overhead_periods", UUID(str(allocation_id)))
    produced = int(row["produced_units"])
    amount = int(row["total_minor"]) // produced if produced else 0
    return OverheadAllocation(
        period_id=period_id,
        status=str(row["status"]),
        amount_per_unit=_money(amount, row["currency"]),
    )


def approve_run(db: Session, period_id: UUID, approval: PayrollApproval) -> PayrollStatement:
    statement = get_statement(db, period_id)
    if statement.version != approval.version or statement.input_hash != approval.input_hash:
        raise ValueError("Payroll approval does not match the calculated run")
    run = max((r for r in _rows(db, "payroll_runs") if str(r.get("period_id")) == str(period_id)), key=lambda r: int(r["version"]))
    db.execute(text("SELECT payroll_advance_run(:run_id, 'APPROVED')"), {"run_id": run["id"]})
    return get_statement(db, period_id)


def record_payment(db: Session, tenant_id: UUID, actor_id: UUID, period_id: UUID, payment: PaymentEvidence) -> PayrollStatement:
    statement = get_statement(db, period_id)
    if statement.status != "APPROVED":
        raise ValueError("Payroll run is not approved")
    run = max((r for r in _rows(db, "payroll_runs") if str(r.get("period_id")) == str(period_id)), key=lambda r: int(r["version"]))
    linked = db.execute(text("SELECT 1 FROM ledger_transactions WHERE tenant_id=:tenant_id AND source_type='PAYROLL' AND source_id=:run_id"), {"tenant_id": tenant_id, "run_id": run["id"]}).scalar_one_or_none()
    if linked is None:
        raise ValueError("Payment requires an existing PAYROLL ledger transaction")
    db.execute(text("INSERT INTO payroll_payments (tenant_id, run_id, external_reference, evidence_file_id, recorded_by) VALUES (:tenant_id, :run_id, :external_reference, :evidence_file_id, :actor_id)"), {"tenant_id": tenant_id, "run_id": run["id"], "external_reference": payment.external_reference, "evidence_file_id": payment.evidence_file_id, "actor_id": actor_id})
    db.execute(text("SELECT payroll_advance_run(:run_id, 'PAID')"), {"run_id": run["id"]})
    return get_statement(db, period_id)


def start_job(db: Session, tenant_id: UUID, kind: str, request: JobRequest) -> JobAccepted:
    job_id = uuid4()
    db.execute(text("INSERT INTO job_runs (id, tenant_id, kind, period_id, scheduled_for, status) VALUES (:id, :tenant_id, :kind, :period_id, :scheduled_for, 'RUNNING') ON CONFLICT (tenant_id, kind, period_id) DO NOTHING"), {"id": job_id, "tenant_id": tenant_id, "kind": kind, "period_id": request.period_id, "scheduled_for": datetime.now(timezone.utc)})
    row = db.execute(text("SELECT id, status FROM job_runs WHERE tenant_id=:tenant_id AND kind=:kind AND period_id=:period_id"), {"tenant_id": tenant_id, "kind": kind, "period_id": request.period_id}).one()
    return JobAccepted(job_id=row[0], status=row[1])


def execute_job(db: Session, tenant_id: UUID, kind: str, request: JobRequest) -> JobAccepted:
    accepted = start_job(db, tenant_id, kind, request)
    if accepted.status != "RUNNING":
        return accepted
    try:
        period = _row(db, "payroll_periods", request.period_id)
        rule_id = UUID(str(period["rule_version"]))
        get_required_versions(db, tenant_id, [rule_id], date.fromisoformat(str(period["period_start"])))
        if kind == "SATURDAY_PAYROLL":
            calculate_weekly_payroll(db, tenant_id, request.period_id, rule_id)
        else:
            calculate_overhead(db, request.period_id, rule_id)
        db.execute(text("UPDATE job_runs SET status='SUCCEEDED', updated_at=now(), error_code=NULL WHERE tenant_id=:tenant_id AND id=:job_id"), {"tenant_id": tenant_id, "job_id": accepted.job_id})
        return JobAccepted(job_id=accepted.job_id, status="SUCCEEDED")
    except FinancialRulePending:
        db.execute(text("UPDATE job_runs SET status='BLOCKED', error_code='FINANCIAL_RULE_PENDING', updated_at=now() WHERE tenant_id=:tenant_id AND id=:job_id"), {"tenant_id": tenant_id, "job_id": accepted.job_id})
        return JobAccepted(job_id=accepted.job_id, status="BLOCKED")


def get_job(db: Session, tenant_id: UUID, job_id: UUID) -> JobAccepted:
    row = db.execute(text("SELECT id, status FROM job_runs WHERE tenant_id=:tenant_id AND id=:job_id"), {"tenant_id": tenant_id, "job_id": job_id}).one_or_none()
    if row is None:
        raise LookupError("Job not found")
    return JobAccepted(job_id=row[0], status=row[1])