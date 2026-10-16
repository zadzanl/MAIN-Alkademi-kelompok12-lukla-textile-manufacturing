"""Financial rule persistence in the caller's tenant-scoped transaction.

Ceiling: the checked SQL reader filters only by UUID. Name/date resolution scans
every tenant rule; add a narrowly checked database resolver before large registries.
"""

import json
from collections.abc import Sequence
from datetime import date
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.models.financial_rule import (
    FinancialRule,
    FinancialRuleApproval,
    FinancialRuleRequest,
)
from src.services.errors import FinancialRulePending
from src.services.financial_rules import assert_may_approve, assert_may_propose, propose_rule
from src.services.rule_gate import RuleReference

_PAGE_SIZE = 1000
_READ = text("SELECT payroll_read_rows('financial_rule_versions', :rule_id, :after_id, :page_size)")


def _require_tenant(db: Session, tenant_id: UUID) -> None:
    actual = db.execute(text("SELECT payroll_context_tenant()")).scalar_one()
    if actual != tenant_id:
        raise ValueError("tenant_id differs from installed payroll context")


def _rule_from_row(row: object) -> FinancialRule:
    if not isinstance(row, dict) or not isinstance(row.get("parameters"), dict):
        raise ValueError("payroll_read_rows returned invalid rule parameters")
    rule = FinancialRule.model_validate(
        {**row["parameters"], "id": row["id"], "status": row["status"]}
    )
    if rule.effective_from != date.fromisoformat(str(row["effective_from"])):
        raise ValueError("financial rule effective date differs from stored parameters")
    return rule


def _rows(db: Session) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    after: UUID | None = None
    while True:
        page = (
            db.execute(_READ, {"rule_id": None, "after_id": after, "page_size": _PAGE_SIZE})
            .scalars()
            .all()
        )
        for row in page:
            if not isinstance(row, dict):
                raise ValueError("payroll_read_rows returned a non-object rule")
            rows.append(row)
        if len(page) < _PAGE_SIZE:
            return rows
        after = UUID(str(rows[-1]["id"]))


def _get_rule(db: Session, rule_id: UUID) -> FinancialRule:
    row = db.execute(
        _READ, {"rule_id": rule_id, "after_id": None, "page_size": 1}
    ).scalar_one_or_none()
    if row is None:
        raise LookupError("Financial rule not found in tenant context")
    return _rule_from_row(row)


def list_financial_rules(db: Session, tenant_id: UUID) -> list[FinancialRule]:
    """Return all tenant rules in UUID order through the allowlisted reader."""
    _require_tenant(db, tenant_id)
    return [_rule_from_row(row) for row in _rows(db)]


def get_required_versions(
    db: Session, tenant_id: UUID, rule_ids: Sequence[UUID], on_date: date
) -> list[RuleReference]:
    """Resolve exact immutable versions; never replace a pending ID with another rule."""
    _require_tenant(db, tenant_id)
    resolved: list[RuleReference] = []
    for rule_id in rule_ids:
        row = db.execute(
            _READ, {"rule_id": rule_id, "after_id": None, "page_size": 1}
        ).scalar_one_or_none()
        if row is None:
            raise FinancialRulePending(f"Financial rule version {rule_id} is missing")
        rule = _rule_from_row(row)
        through = row["effective_through"]
        if rule.effective_from > on_date or (
            through is not None and on_date >= date.fromisoformat(str(through))
        ):
            raise FinancialRulePending(f"Financial rule version {rule_id} is outside its window")
        resolved.append(RuleReference(rule.id, rule.status))
    return resolved


def _require_actor(db: Session, actor_id: UUID, role: str) -> None:
    actual_role, actual_actor = db.execute(
        text("SELECT current_setting('app.role', true), current_setting('app.actor_id', true)")
    ).one()
    if actual_role != role or actual_actor != str(actor_id):
        raise ValueError("actor or role differs from installed payroll context")


def propose_financial_rule(
    db: Session, tenant_id: UUID, actor_id: UUID, role: str, request: FinancialRuleRequest
) -> FinancialRule:
    """Insert a pending version; the legacy internal rule_name is its immutable UUID."""
    assert_may_propose(role)
    _require_tenant(db, tenant_id)
    _require_actor(db, actor_id, role)
    rule = propose_rule(request, uuid4())
    db.execute(
        text(
            "INSERT INTO financial_rule_versions "
            "(id, tenant_id, rule_name, effective_from, parameters) "
            "VALUES (:id, :tenant_id, :name, :effective_from, CAST(:parameters AS jsonb))"
        ),
        {
            "id": rule.id,
            "tenant_id": tenant_id,
            "name": str(rule.id),
            "effective_from": rule.effective_from,
            "parameters": json.dumps(request.model_dump(mode="json", by_alias=True)),
        },
    )
    return _get_rule(db, rule.id)


def approve_financial_rule(
    db: Session,
    tenant_id: UUID,
    actor_id: UUID,
    role: str,
    rule_id: UUID,
    approval: FinancialRuleApproval,
    request_id: UUID | None = None,
) -> FinancialRule:
    """Use the existing Owner-only SQL transition, then checked-read in the same session."""
    assert_may_approve(role)
    _require_tenant(db, tenant_id)
    _require_actor(db, actor_id, role)
    db.execute(
        text(
            "SELECT payroll_approve_rule(:rule_id, :evidence_file_id, "
            ":approval_reference, :note, :request_id)"
        ),
        {
            "rule_id": rule_id,
            "evidence_file_id": approval.evidence_file_id,
            "approval_reference": approval.approval_reference,
            "note": approval.note,
            "request_id": request_id or uuid4(),
        },
    )
    return _get_rule(db, rule_id)
