"""URL-free repository tests; SQL permissions and locking need a disposable DB check."""

from datetime import date
from unittest.mock import Mock
from uuid import UUID

import pytest
from sqlalchemy.orm import Session

from src.models.payroll_period import PayrollPeriodStatus, PeriodRequest
from src.repositories.periods import (
    _period_from_row,
    create_payroll_period,
    list_payroll_periods,
    transition_period,
)
from src.services.errors import InvalidState, ValidationFailed

TENANT = UUID("11111111-1111-4111-8111-111111111111")
PERIOD = UUID("22222222-2222-4222-8222-222222222222")
RULE = UUID("44444444-4444-4444-8444-444444444444")


def _row(period_id: UUID) -> dict[str, str]:
    return {
        "id": str(period_id),
        "period_start": "2026-10-11",
        "period_end": "2026-10-18",
        "timezone": "Asia/Jakarta",
        "cutoff_local": "12:00:00",
        "rule_version": str(RULE),
    }


def _rule_row(rule_payload: dict[str, object]) -> dict[str, object]:
    return {
        "id": str(RULE),
        "effective_from": rule_payload["effectiveFrom"],
        "effective_through": None,
        "parameters": rule_payload,
        "status": "PENDING",
    }


class _Result:
    def __init__(self, rows: list[object]) -> None:
        self.rows = rows

    def scalar_one(self) -> object:
        assert len(self.rows) == 1
        return self.rows[0]

    def scalar_one_or_none(self) -> object | None:
        assert len(self.rows) <= 1
        return self.rows[0] if self.rows else None

    def scalars(self) -> "_Result":
        return self

    def all(self) -> list[object]:
        return self.rows


def _session(
    pages: list[list[object]] | None = None,
) -> tuple[Session, list[tuple[str, dict[str, object]]]]:
    calls: list[tuple[str, dict[str, object]]] = []
    remaining = list(pages or [])

    def execute(statement: object, params: dict[str, object] | None = None) -> _Result:
        sql = str(statement)
        values = params or {}
        calls.append((sql, values))
        if "payroll_context_tenant" in sql:
            return _Result([TENANT])
        if "payroll_read_rows" in sql:
            return _Result(remaining.pop(0))
        return _Result([None])

    db = Mock(spec=Session)
    db.execute.side_effect = execute
    return db, calls


def test_row_mapping_is_contract_shaped_and_rejects_invalid_data() -> None:
    period = _period_from_row(_row(PERIOD))
    assert period.id == PERIOD
    assert period.starts_on == date(2026, 10, 11)
    with pytest.raises(ValueError):
        _period_from_row("not JSON object")
    with pytest.raises(ValueError):
        _period_from_row({**_row(PERIOD), "timezone": "UTC"})


def test_create_uses_caller_session_and_reads_its_insert(
    period_request: PeriodRequest, rule_payload: dict[str, object]
) -> None:
    db, calls = _session([[_rule_row({**rule_payload, "effectiveFrom": "2026-10-11"})], [_row(PERIOD)]])
    period = create_payroll_period(db, TENANT, period_request)
    assert period.id == PERIOD
    assert "payroll_context_tenant" in calls[0][0]
    assert any("payroll_read_rows" in c[0] and c[1].get("rule_id") == RULE for c in calls)
    assert any("INSERT INTO payroll_periods" in c[0] and c[1].get("tenant_id") == TENANT for c in calls)
    assert any("payroll_read_rows" in c[0] and c[1].get("period_id") is not None for c in calls)
    db.commit.assert_not_called()
    db.rollback.assert_not_called()


def test_range_is_validated_before_insert(period_payload: dict[str, object]) -> None:
    request = PeriodRequest.model_validate({**period_payload, "endsOn": "2026-10-11"})
    db, calls = _session()
    with pytest.raises(ValidationFailed):
        create_payroll_period(db, TENANT, request)
    assert not calls


def test_list_pages_all_1001_rows() -> None:
    rows = [_row(UUID(int=index + 1)) for index in range(1001)]
    db, calls = _session([rows[:1000], rows[1000:]])
    periods = list_payroll_periods(db, TENANT)
    assert len(periods) == 1001
    assert calls[1][1] == {"period_id": None, "after_id": None, "page_size": 1000}
    assert calls[2][1]["after_id"] == UUID(int=1000)
    assert calls[2][1]["page_size"] == 1000


def test_transition_checks_edge_and_uses_checked_read() -> None:
    db, calls = _session([[_row(PERIOD)]])
    with pytest.raises(InvalidState):
        transition_period(
            db, TENANT, PERIOD, PayrollPeriodStatus.APPROVED, PayrollPeriodStatus.REVERSED
        )
    assert not calls
    result = transition_period(
        db, TENANT, PERIOD, PayrollPeriodStatus.OPEN, PayrollPeriodStatus.PENDING_RULE
    )
    assert result.id == PERIOD
    assert "payroll_transition_period" in calls[1][0]
    assert calls[1][1]["expected"] == "OPEN"
    assert "payroll_read_rows" in calls[2][0]
