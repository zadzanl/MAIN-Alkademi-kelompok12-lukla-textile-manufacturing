"""The calculation schemas must accept exactly what the frozen contract accepts."""

from typing import Any
from uuid import UUID

import pytest
from pydantic import ValidationError

from src.models.payroll_calculation import PayrollResult, PayrollResultStatus, RuleRequest


def result_payload() -> dict[str, Any]:
    return {
        "periodId": "77777777-7777-4777-8777-777777777777",
        "status": "CALCULATED",
        "eligibleUnits": 30,
        "totalWages": {"amountMinor": 60000, "currency": "IDR"},
    }


def test_rule_request_round_trips() -> None:
    request = RuleRequest.model_validate({"ruleVersion": "44444444-4444-4444-8444-444444444444"})

    assert request.model_dump(mode="json", by_alias=True) == {
        "ruleVersion": "44444444-4444-4444-8444-444444444444"
    }


def test_payroll_result_round_trips() -> None:
    result = PayrollResult.model_validate(result_payload())

    assert result.period_id == UUID("77777777-7777-4777-8777-777777777777")
    assert result.status is PayrollResultStatus.CALCULATED
    assert result.total_wages.amount_minor == 60000
    assert result.model_dump(mode="json", by_alias=True) == result_payload()


@pytest.mark.parametrize("status", ["CALCULATED", "NO_OUTPUT", "PENDING_RULE"])
def test_every_contract_status_is_accepted_on_the_wire(status: str) -> None:
    result = PayrollResult.model_validate(dict(result_payload(), status=status))

    assert result.status == status


def test_unknown_status_and_properties_are_rejected() -> None:
    with pytest.raises(ValidationError):
        PayrollResult.model_validate(dict(result_payload(), status="DRAFT"))

    with pytest.raises(ValidationError):
        PayrollResult.model_validate(dict(result_payload(), disbursed=True))
