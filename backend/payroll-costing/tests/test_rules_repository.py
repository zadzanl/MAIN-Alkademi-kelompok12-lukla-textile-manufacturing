"""URL-free checked-reader tests; SQL privileges need restricted-role integration."""

from datetime import date
from unittest.mock import Mock
from uuid import UUID

import pytest
from sqlalchemy.orm import Session

from src.models.financial_rule import FinancialRuleApproval, RuleStatus
from src.repositories.rules import (
    _rule_from_row,
    approve_financial_rule,
    get_required_versions,
    list_financial_rules,
)
from src.services.errors import FinancialRulePending, Forbidden

TENANT = UUID("11111111-1111-4111-8111-111111111111")
ACTOR = UUID("22222222-2222-4222-8222-222222222222")
EVIDENCE = UUID("33333333-3333-4333-8333-333333333333")


def _row(
    payload: dict[str, object], rule_id: UUID, *, status: str = "PENDING"
) -> dict[str, object]:
    return {
        "id": str(rule_id),
        "rule_name": str(rule_id),
        "effective_from": payload["effectiveFrom"],
        "effective_through": None,
        "parameters": payload,
        "status": status,
    }


class _Result:
    def __init__(self, rows: list[object]) -> None:
        self.rows = rows

    def scalar_one(self) -> object:
        return self.rows[0]

    def scalar_one_or_none(self) -> object | None:
        return self.rows[0] if self.rows else None

    def scalars(self) -> "_Result":
        return self

    def all(self) -> list[object]:
        return self.rows

    def one(self) -> object:
        return self.rows[0]


def _session(
    pages: list[list[object]], *, tenant: UUID = TENANT, role: str = "Owner"
) -> tuple[Session, list[tuple[str, dict[str, object]]]]:
    calls: list[tuple[str, dict[str, object]]] = []
    remaining = list(pages)

    def execute(statement: object, params: dict[str, object] | None = None) -> _Result:
        sql = str(statement)
        calls.append((sql, params or {}))
        if "payroll_context_tenant" in sql:
            return _Result([tenant])
        if "current_setting('app.role'" in sql:
            return _Result([(role, str(ACTOR))])
        if "payroll_read_rows" in sql:
            return _Result(remaining.pop(0))
        return _Result([None])

    db = Mock(spec=Session)
    db.execute.side_effect = execute
    return db, calls


def test_contract_mapping_rejects_bad_rows(rule_payload: dict[str, object]) -> None:
    rule = _rule_from_row(_row(rule_payload, ACTOR))
    assert rule.effective_from == date(2026, 10, 17)
    with pytest.raises(ValueError):
        _rule_from_row({**_row(rule_payload, ACTOR), "effective_from": "2026-10-18"})
    with pytest.raises(ValueError):
        _rule_from_row({**_row(rule_payload, ACTOR), "parameters": {"effectiveFrom": "2026-10-17"}})


def test_list_empty_and_1001_rows(rule_payload: dict[str, object]) -> None:
    db, calls = _session([[]])
    assert list_financial_rules(db, TENANT) == []
    assert calls[1][1] == {"rule_id": None, "after_id": None, "page_size": 1000}
    rows = [_row(rule_payload, UUID(int=i + 1)) for i in range(1001)]
    db, calls = _session([rows[:1000], rows[1000:]])
    assert len(list_financial_rules(db, TENANT)) == 1001
    assert calls[2][1]["after_id"] == UUID(int=1000)
    assert calls[2][1]["page_size"] == 1000
    db.commit.assert_not_called()
    db.rollback.assert_not_called()


def test_required_versions_filter_and_fail_closed(rule_payload: dict[str, object]) -> None:
    approved = _row(rule_payload, UUID(int=1), status="APPROVED")
    pending_id = UUID(int=2)
    expired_id = UUID(int=3)
    pending = _row(rule_payload, pending_id)
    expired = {**_row(rule_payload, expired_id), "effective_through": "2026-10-18"}
    db, _ = _session([[approved], [pending]])
    refs = get_required_versions(db, TENANT, [UUID(int=1), pending_id], date(2026, 10, 18))
    assert [(ref.rule_id, ref.status) for ref in refs] == [
        (UUID(int=1), RuleStatus.APPROVED),
        (UUID(int=2), RuleStatus.PENDING),
    ]
    for rule_id, pages in ((UUID(int=99), [[]]), (expired_id, [[expired]])):
        db, _ = _session(pages)
        with pytest.raises(FinancialRulePending):
            get_required_versions(db, TENANT, [rule_id], date(2026, 10, 18))


def test_required_versions_prefer_effective_approved_and_detect_ambiguity(
    rule_payload: dict[str, object],
) -> None:
    approved = _row(rule_payload, UUID(int=1), status="APPROVED")
    db, _ = _session([[approved]])
    assert get_required_versions(db, TENANT, [UUID(int=1)], date(2026, 10, 17))[0].rule_id == UUID(
        int=1
    )


def test_approval_checks_context_and_uses_routine_then_reader(
    rule_payload: dict[str, object],
) -> None:
    approval = FinancialRuleApproval(evidence_file_id=EVIDENCE)
    db, calls = _session([[_row(rule_payload, UUID(int=1), status="APPROVED")]])
    request_id = UUID("55555555-5555-4555-8555-555555555555")
    rule = approve_financial_rule(db, TENANT, ACTOR, "Owner", UUID(int=1), approval, request_id)
    assert rule.status is RuleStatus.APPROVED
    assert "payroll_approve_rule" in calls[2][0]
    assert calls[2][1] == {
        "rule_id": UUID(int=1),
        "evidence_file_id": EVIDENCE,
        "approval_reference": None,
        "note": None,
        "request_id": request_id,
    }
    assert "payroll_read_rows" in calls[3][0]
    db.commit.assert_not_called()
    db.rollback.assert_not_called()
    db, calls = _session([], role="FinancePayroll")
    with pytest.raises(Forbidden):
        approve_financial_rule(
            db, TENANT, ACTOR, "FinancePayroll", UUID(int=1), approval, request_id
        )
    assert not calls
    db, calls = _session([], tenant=UUID(int=9))
    with pytest.raises(ValueError, match="tenant_id"):
        approve_financial_rule(db, TENANT, ACTOR, "Owner", UUID(int=1), approval, request_id)
    assert len(calls) == 1
    db, calls = _session([], role="FinancePayroll")
    with pytest.raises(ValueError, match="role"):
        approve_financial_rule(db, TENANT, ACTOR, "Owner", UUID(int=1), approval, request_id)
    assert len(calls) == 2


def test_reader_refuses_mismatched_tenant_and_missing_approval_row(
    rule_payload: dict[str, object],
) -> None:
    request_id = UUID("55555555-5555-4555-8555-555555555555")
    db, calls = _session([], tenant=UUID(int=9))
    with pytest.raises(ValueError, match="tenant_id"):
        list_financial_rules(db, TENANT)
    assert len(calls) == 1
    db, _ = _session([[]])
    with pytest.raises(LookupError):
        approve_financial_rule(
            db,
            TENANT,
            ACTOR,
            "Owner",
            UUID(int=1),
            FinancialRuleApproval(evidence_file_id=EVIDENCE),
            request_id,
        )
