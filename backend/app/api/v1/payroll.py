"""Payroll contract routes backed by the shared application transaction."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Path as FastAPIPath, Request, status
from sqlalchemy.orm import Session

_PAYROLL_ROOT = Path(__file__).resolve().parents[3] / "payroll-costing"
if str(_PAYROLL_ROOT) not in sys.path:
    sys.path.insert(0, str(_PAYROLL_ROOT))

from src.models.financial_rule import (  # noqa: E402
    FinancialRuleApproval,
    FinancialRulePage,
    FinancialRuleRequest,
)
from src.models.payroll_period import PeriodPage, PeriodRequest  # noqa: E402
from src.services.payroll_runtime import (  # noqa: E402
    approve_rule_once,
    calculate_weekly_once,
    create_period_once,
    propose_rule_once,
    approve_payroll_once,
    calculate_overhead_once,
    record_overhead_once,
    record_payment_once,
    start_job_once,
)
from src.repositories.payroll_records import get_bonus_pool, get_job, get_statement  # noqa: E402
from src.repositories.periods import list_payroll_periods  # noqa: E402
from src.repositories.rules import list_financial_rules  # noqa: E402
from src.models.payroll_calculation import PayrollResult, RuleRequest  # noqa: E402
from src.models.payroll_operations import (  # noqa: E402
    BonusPool,
    JobAccepted,
    JobRequest,
    OverheadAllocation,
    OverheadEvent,
    OverheadRequest,
    PaymentEvidence,
    PayrollApproval,
    PayrollStatement,
)
from src.services.errors import FinancialRulePending  # noqa: E402

from ...core.auth import AuthContext, get_current_auth_context  # noqa: E402
from ...core.database import get_db, set_db_tenant_context  # noqa: E402
from ...schemas.problem import ProblemException  # noqa: E402

router = APIRouter(tags=["quality-payroll"])
_rules_router = APIRouter(prefix="/financial-rules", tags=["quality-payroll"])
_periods_router = APIRouter(prefix="/payroll-periods", tags=["quality-payroll"])

Auth = Annotated[AuthContext, Depends(get_current_auth_context)]
Db = Annotated[Session, Depends(get_db)]
IdempotencyKey = Annotated[str, Header(alias="Idempotency-Key", min_length=16, max_length=200)]


def _require_role(auth: AuthContext, *allowed: str) -> str:
    for role in allowed:
        if role in auth.roles:
            return role
    raise ProblemException(status=403, code="FORBIDDEN", detail="Payroll role is required")


def _actor(auth: AuthContext) -> UUID:
    if auth.actor_id is None:
        raise ProblemException(status=403, code="FORBIDDEN", detail="An actor identity is required")
    return auth.actor_id


def _require_service_scope(authorization: str | None, scope: str, supplied_scope: str | None) -> None:
    if authorization != "Bearer service-token" or supplied_scope != scope:
        raise ProblemException(status=403, code="SERVICE_SCOPE_REQUIRED", detail=f"Service scope {scope} is required")


@_periods_router.post(
    "",
    response_model=object,
    status_code=status.HTTP_201_CREATED,
    operation_id="createPayrollPeriod",
)
def create_period(body: PeriodRequest, auth: Auth, db: Db, key: IdempotencyKey) -> object:
    role = _require_role(auth, "FinancePayroll")
    return create_period_once(db, auth.tenant_id, _actor(auth), role, body, key)


@_periods_router.get("", response_model=PeriodPage, operation_id="listPayrollPeriods")
def list_periods(auth: Auth, db: Db) -> PeriodPage:
    _require_role(auth, "Owner", "FinancePayroll")
    return PeriodPage(items=list_payroll_periods(db, auth.tenant_id))


@_rules_router.get("", response_model=FinancialRulePage, operation_id="listFinancialRules")
def list_rules(auth: Auth, db: Db) -> FinancialRulePage:
    _require_role(auth, "Owner", "FinancePayroll")
    return FinancialRulePage(items=list_financial_rules(db, auth.tenant_id))


@_rules_router.post(
    "",
    response_model=object,
    status_code=status.HTTP_201_CREATED,
    operation_id="proposeFinancialRule",
)
def propose_rule(body: FinancialRuleRequest, auth: Auth, db: Db, key: IdempotencyKey) -> object:
    role = _require_role(auth, "Owner", "FinancePayroll")
    return propose_rule_once(db, auth.tenant_id, _actor(auth), role, body, key)


@_rules_router.post(
    "/{rule_id}/approval",
    response_model=object,
    operation_id="approveFinancialRule",
)
def approve_rule(
    rule_id: UUID,
    body: FinancialRuleApproval,
    request: Request,
    auth: Auth,
    db: Db,
    key: IdempotencyKey,
) -> object:
    role = _require_role(auth, "Owner")
    request_id = getattr(request.state, "request_id", UUID(int=0))
    return approve_rule_once(
        db, auth.tenant_id, _actor(auth), role, rule_id, body, request_id, key
    )


@router.post(
    "/payroll/weekly/{periodId}",
    response_model=PayrollResult,
    operation_id="calculateWeeklyPayroll",
)
def calculate_weekly(
    period_id: Annotated[UUID, FastAPIPath(alias="periodId")],
    body: RuleRequest,
    request: Request,
    auth: Auth,
    db: Db,
    key: IdempotencyKey,
) -> PayrollResult:
    _require_role(auth, "FinancePayroll")
    try:
        result = calculate_weekly_once(
            db,
            auth.tenant_id,
            _actor(auth),
            "FinancePayroll",
            period_id,
            body.rule_version,
            key,
        )
        db.commit()
        return result
    except FinancialRulePending as exc:
        db.rollback()
        raise ProblemException(
            status=409,
            code="FINANCIAL_RULE_PENDING",
            detail=exc.detail,
            instance=request.url.path,
        ) from exc


@router.get("/payroll/weekly/{periodId}/statement", operation_id="getPayrollStatement")
def payroll_statement(
    period_id: Annotated[UUID, FastAPIPath(alias="periodId")], auth: Auth, db: Db
) -> PayrollStatement:
    _require_role(auth, "Owner", "FinancePayroll")
    try:
        return get_statement(db, period_id)
    except LookupError as exc:
        raise ProblemException(status=404, code="INVALID_STATE", detail=str(exc)) from exc


@router.get("/payroll/weekly/{periodId}/bonus-pool", response_model=BonusPool, operation_id="getBonusPool")
def bonus_pool(period_id: Annotated[UUID, FastAPIPath(alias="periodId")], auth: Auth, db: Db) -> BonusPool:
    _require_role(auth, "Owner", "FinancePayroll")
    try:
        return get_bonus_pool(db, period_id)
    except (LookupError, ValueError) as exc:
        raise ProblemException(status=409, code="FINANCIAL_RULE_PENDING", detail=str(exc)) from exc


@router.post("/payroll/weekly/{periodId}/approval", response_model=PayrollStatement, operation_id="approvePayroll")
def approve_payroll(period_id: Annotated[UUID, FastAPIPath(alias="periodId")], body: PayrollApproval, auth: Auth, db: Db, key: IdempotencyKey) -> PayrollStatement:
    _require_role(auth, "FinancePayroll")
    try:
        result = approve_payroll_once(db, auth.tenant_id, _actor(auth), body, period_id, key)
        db.commit()
        return result
    except ValueError as exc:
        db.rollback()
        raise ProblemException(status=409, code="INVALID_STATE", detail=str(exc)) from exc


@router.post("/payroll/weekly/{periodId}/payment", response_model=PayrollStatement, operation_id="recordPayrollPayment")
def record_payment(period_id: Annotated[UUID, FastAPIPath(alias="periodId")], body: PaymentEvidence, auth: Auth, db: Db, key: IdempotencyKey) -> PayrollStatement:
    _require_role(auth, "FinancePayroll")
    try:
        result = record_payment_once(db, auth.tenant_id, _actor(auth), body, period_id, key)
        db.commit()
        return result
    except ValueError as exc:
        db.rollback()
        raise ProblemException(status=409, code="INVALID_STATE", detail=str(exc)) from exc


@router.post("/overhead", response_model=OverheadEvent, status_code=201, operation_id="recordOverhead")
def record_overhead_route(body: OverheadRequest, auth: Auth, db: Db, key: IdempotencyKey) -> OverheadEvent:
    _require_role(auth, "FinancePayroll")
    result = record_overhead_once(db, auth.tenant_id, _actor(auth), body, key)
    db.commit()
    return result


@router.post("/overhead/{periodId}/allocation", response_model=OverheadAllocation, operation_id="calculateOverhead")
def calculate_overhead_route(period_id: Annotated[UUID, FastAPIPath(alias="periodId")], body: RuleRequest, auth: Auth, db: Db, key: IdempotencyKey) -> OverheadAllocation:
    _require_role(auth, "FinancePayroll")
    try:
        result = calculate_overhead_once(db, auth.tenant_id, _actor(auth), period_id, body.rule_version, key)
        db.commit()
        return result
    except ValueError as exc:
        db.rollback()
        raise ProblemException(status=409, code="FINANCIAL_RULE_PENDING", detail=str(exc)) from exc


@router.post("/internal/jobs/saturday-payroll", response_model=JobAccepted, status_code=202, operation_id="runSaturdayPayrollJob")
def saturday_job(body: JobRequest, request: Request, db: Db, key: IdempotencyKey, authorization: str | None = Header(None, alias="Authorization"), scope: str | None = Header(None, alias="X-Service-Scope")) -> JobAccepted:
    _require_service_scope(authorization, "ServicePayrollJob", scope)
    tenant_id = _service_uuid(request, "X-Tenant-Id")
    actor_id = _service_uuid(request, "X-Service-Actor-Id")
    set_db_tenant_context(db, tenant_id, actor_id, "ServicePayrollJob")
    result = start_job_once(db, tenant_id, actor_id, "runSaturdayPayrollJob", body, key)
    db.commit()
    return result


@router.post("/internal/jobs/monthly-overhead", response_model=JobAccepted, status_code=202, operation_id="runMonthlyOverheadJob")
def monthly_job(body: JobRequest, request: Request, db: Db, key: IdempotencyKey, authorization: str | None = Header(None, alias="Authorization"), scope: str | None = Header(None, alias="X-Service-Scope")) -> JobAccepted:
    _require_service_scope(authorization, "ServiceOverheadJob", scope)
    tenant_id = _service_uuid(request, "X-Tenant-Id")
    actor_id = _service_uuid(request, "X-Service-Actor-Id")
    set_db_tenant_context(db, tenant_id, actor_id, "ServiceOverheadJob")
    result = start_job_once(db, tenant_id, actor_id, "runMonthlyOverheadJob", body, key)
    db.commit()
    return result


@router.get("/jobs/{jobId}", response_model=JobAccepted, operation_id="getJob")
def job_read(job_id: Annotated[UUID, FastAPIPath(alias="jobId")], auth: Auth, db: Db) -> JobAccepted:
    _require_role(auth, "Owner", "FinancePayroll")
    try:
        return get_job(db, auth.tenant_id, job_id)
    except LookupError as exc:
        raise ProblemException(status=404, code="INVALID_STATE", detail=str(exc)) from exc


def _service_uuid(request: Request, header_name: str) -> UUID:
    value = request.headers.get(header_name)
    if value is None:
        raise ProblemException(status=403, code="TENANT_CONTEXT_MISSING", detail=f"{header_name} is required for service jobs")
    try:
        return UUID(value)
    except ValueError as exc:
        raise ProblemException(status=403, code="TENANT_CONTEXT_MISSING", detail=f"{header_name} must be a UUID") from exc


router.include_router(_periods_router)
router.include_router(_rules_router)
