"""Foundation mutation boundary; HTTP orchestration and monetary work belong to phases 4–5.

Caller installs trusted tenant/actor context and owns commit/rollback. The shared
idempotency reservation, mutation and completion must use this one transaction.
"""

from collections.abc import Callable
from typing import TypeVar
from uuid import UUID

from sqlalchemy.orm import Session

from src.models.base import ContractModel
from src.models.financial_rule import FinancialRule, FinancialRuleApproval, FinancialRuleRequest
from src.models.payroll_calculation import PayrollResult
from src.models.payroll_operations import (
    JobAccepted,
    JobRequest,
    OverheadAllocation,
    OverheadEvent,
    OverheadRequest,
    PayrollApproval,
    PayrollStatement,
    PaymentEvidence,
)
from src.models.payroll_period import Period, PeriodRequest
from src.repositories.payroll import calculate_weekly_payroll
from src.repositories.payroll_records import (
    approve_run,
    calculate_overhead,
    record_overhead,
    record_payment,
    execute_job,
)
from src.repositories.periods import create_payroll_period
from src.repositories.rules import approve_financial_rule, propose_financial_rule

try:
    from backend.app.services import idempotency as _idempotency
except ModuleNotFoundError as exc:
    if exc.name != "backend":
        raise
    from app.services import idempotency as _idempotency

complete_idempotency = _idempotency.complete_idempotency
compute_canonical_hash = _idempotency.compute_canonical_hash
reserve_or_get_idempotency = _idempotency.reserve_or_get_idempotency

_Result = TypeVar("_Result", bound=ContractModel)


def _mutate(
    db: Session,
    tenant_id: UUID,
    actor_id: UUID,
    operation_id: str,
    key: str,
    payload: dict[str, object],
    model: type[_Result],
    action: Callable[[], _Result],
) -> _Result:
    # Actor and path identity are part of the digest: a different principal cannot replay
    # an earlier principal's response for the same tenant/key/operation.
    digest = compute_canonical_hash({"actorId": str(actor_id), **payload})
    is_new, cached = reserve_or_get_idempotency(db, tenant_id, operation_id, key, digest)
    if not is_new:
        if cached is None:
            raise ValueError("Completed idempotency reservation has no response")
        return model.model_validate(cached[1])
    result = action()
    complete_idempotency(
        db,
        tenant_id,
        operation_id,
        key,
        200 if operation_id in {"approveFinancialRule", "calculateWeeklyPayroll"} else 201,
        result.model_dump(mode="json", by_alias=True),
    )
    return result


def propose_rule_once(
    db: Session,
    tenant_id: UUID,
    actor_id: UUID,
    role: str,
    request: FinancialRuleRequest,
    key: str,
) -> FinancialRule:
    return _mutate(
        db,
        tenant_id,
        actor_id,
        "proposeFinancialRule",
        key,
        {"role": role, "body": request.model_dump(mode="json", by_alias=True)},
        FinancialRule,
        lambda: propose_financial_rule(db, tenant_id, actor_id, role, request),
    )


def approve_rule_once(
    db: Session,
    tenant_id: UUID,
    actor_id: UUID,
    role: str,
    rule_id: UUID,
    approval: FinancialRuleApproval,
    request_id: UUID,
    key: str,
) -> FinancialRule:
    return _mutate(
        db,
        tenant_id,
        actor_id,
        "approveFinancialRule",
        key,
        {
            "role": role,
            "ruleId": str(rule_id),
            "body": approval.model_dump(mode="json", by_alias=True),
        },
        FinancialRule,
        lambda: approve_financial_rule(
            db, tenant_id, actor_id, role, rule_id, approval, request_id
        ),
    )


def create_period_once(
    db: Session,
    tenant_id: UUID,
    actor_id: UUID,
    role: str,
    request: PeriodRequest,
    key: str,
) -> Period:
    return _mutate(
        db,
        tenant_id,
        actor_id,
        "createPayrollPeriod",
        key,
        {"role": role, "body": request.model_dump(mode="json", by_alias=True)},
        Period,
        lambda: create_payroll_period(db, tenant_id, request),
    )


def calculate_weekly_once(
    db: Session,
    tenant_id: UUID,
    actor_id: UUID,
    role: str,
    period_id: UUID,
    rule_version: UUID,
    key: str,
) -> PayrollResult:
    """Calculate and cache one aggregate result under the shared idempotency key."""
    return _mutate(
        db,
        tenant_id,
        actor_id,
        "calculateWeeklyPayroll",
        key,
        {
            "role": role,
            "periodId": str(period_id),
            "body": {"ruleVersion": str(rule_version)},
        },
        PayrollResult,
        lambda: calculate_weekly_payroll(db, tenant_id, period_id, rule_version),
    )


def approve_payroll_once(db: Session, tenant_id: UUID, actor_id: UUID, approval: PayrollApproval, period_id: UUID, key: str) -> PayrollStatement:
    return _mutate(db, tenant_id, actor_id, "approvePayroll", key, {"periodId": str(period_id), "body": approval.model_dump(mode="json", by_alias=True)}, PayrollStatement, lambda: approve_run(db, period_id, approval))


def record_payment_once(db: Session, tenant_id: UUID, actor_id: UUID, payment: PaymentEvidence, period_id: UUID, key: str) -> PayrollStatement:
    return _mutate(db, tenant_id, actor_id, "recordPayrollPayment", key, {"periodId": str(period_id), "body": payment.model_dump(mode="json", by_alias=True)}, PayrollStatement, lambda: record_payment(db, tenant_id, actor_id, period_id, payment))


def record_overhead_once(db: Session, tenant_id: UUID, actor_id: UUID, request: OverheadRequest, key: str) -> OverheadEvent:
    return _mutate(db, tenant_id, actor_id, "recordOverhead", key, {"body": request.model_dump(mode="json", by_alias=True)}, OverheadEvent, lambda: record_overhead(db, tenant_id, actor_id, request))


def calculate_overhead_once(db: Session, tenant_id: UUID, actor_id: UUID, period_id: UUID, rule_version: UUID, key: str) -> OverheadAllocation:
    return _mutate(db, tenant_id, actor_id, "calculateOverhead", key, {"periodId": str(period_id), "ruleVersion": str(rule_version)}, OverheadAllocation, lambda: calculate_overhead(db, period_id, rule_version))


def start_job_once(db: Session, tenant_id: UUID, actor_id: UUID, kind: str, request: JobRequest, key: str) -> JobAccepted:
    return _mutate(db, tenant_id, actor_id, kind, key, {"body": request.model_dump(mode="json", by_alias=True)}, JobAccepted, lambda: execute_job(db, tenant_id, "SATURDAY_PAYROLL" if kind == "runSaturdayPayrollJob" else "MONTHLY_OVERHEAD", request))
