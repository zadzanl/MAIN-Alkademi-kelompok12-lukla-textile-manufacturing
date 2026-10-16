from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from app.api.v1 import payroll
from app.core.auth import AuthContext
from app.schemas.problem import ProblemException

from src.models.money import Money
from src.models.payroll_calculation import PayrollResult, PayrollResultStatus
from src.services.errors import FinancialRulePending


class _Db:
    def __init__(self) -> None:
        self.committed = False
        self.rolled_back = False

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True


def _auth() -> AuthContext:
    return AuthContext(actor_id=uuid4(), tenant_id=uuid4(), roles=["FinancePayroll"])


def test_weekly_route_returns_approved_aggregate(monkeypatch: pytest.MonkeyPatch) -> None:
    period_id = uuid4()
    rule_id = uuid4()
    db = _Db()
    expected = PayrollResult(
        period_id=period_id,
        status=PayrollResultStatus.CALCULATED,
        eligible_units=3,
        total_wages=Money(amount_minor=2100, currency="IDR"),
    )
    received: dict[str, object] = {}

    def fake_calculate(*args: object, **kwargs: object) -> PayrollResult:
        received["args"] = args
        received["kwargs"] = kwargs
        return expected

    monkeypatch.setattr(payroll, "calculate_weekly_once", fake_calculate)
    result = payroll.calculate_weekly(
        period_id,
        payroll.RuleRequest(rule_version=rule_id),
        _Request("/api/v1/payroll/weekly/" + str(period_id)),
        _auth(),
        db,
        "0123456789abcdef",
    )

    assert result == expected
    assert db.committed
    assert not db.rolled_back
    assert received["args"]


def test_weekly_route_maps_pending_rule_and_rolls_back(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db = _Db()

    def blocked(*args: object, **kwargs: object) -> PayrollResult:
        raise FinancialRulePending("rule is not approved")

    monkeypatch.setattr(payroll, "calculate_weekly_once", blocked)
    with pytest.raises(ProblemException) as error:
        payroll.calculate_weekly(
            uuid4(),
            payroll.RuleRequest(rule_version=uuid4()),
            _Request("/api/v1/payroll/weekly"),
            _auth(),
            db,
            "0123456789abcdef",
        )

    assert error.value.status == 409
    assert error.value.code == "FINANCIAL_RULE_PENDING"
    assert db.rolled_back
    assert not db.committed


class _Request:
    def __init__(self, path: str) -> None:
        self.url = type("_Url", (), {"path": path})()