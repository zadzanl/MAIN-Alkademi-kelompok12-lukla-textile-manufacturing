"""Foundation mutation boundary; HTTP orchestration and monetary work belong to phases 4–5.

Caller installs trusted tenant/actor context and owns commit/rollback. The shared
idempotency reservation, mutation and completion must use this one transaction.
"""

from collections.abc import Callable
from typing import TypeVar
from uuid import UUID

from backend.app.services.idempotency import (
    complete_idempotency,
    compute_canonical_hash,
    reserve_or_get_idempotency,
)
from sqlalchemy.orm import Session

from src.models.base import ContractModel
from src.models.financial_rule import FinancialRule, FinancialRuleApproval, FinancialRuleRequest
from src.models.payroll_period import Period, PeriodRequest
from src.repositories.periods import create_payroll_period
from src.repositories.rules import approve_financial_rule, propose_financial_rule

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
        200 if operation_id == "approveFinancialRule" else 201,
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
