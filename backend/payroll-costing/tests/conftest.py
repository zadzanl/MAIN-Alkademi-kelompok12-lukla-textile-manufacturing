"""Shared fixtures: a contract-valid financial rule payload."""

from typing import Any

import pytest

from src.models.financial_rule import FinancialRuleRequest
from src.models.payroll_period import PeriodRequest

RECIPIENT_A = "11111111-1111-4111-8111-111111111111"
RECIPIENT_B = "22222222-2222-4222-8222-222222222222"
RECIPIENT_C = "33333333-3333-4333-8333-333333333333"


@pytest.fixture
def rule_payload() -> dict[str, Any]:
    """A payload shaped exactly like the contract's ``FinancialRuleRequest``."""
    return {
        "effectiveFrom": "2026-10-17",
        "mealBasis": "VERIFIED_WAGES_PROPOSED",
        "mealBasisPoints": 1250,
        "mealDistribution": "PROPORTIONAL_PROPOSED",
        "bonusRate": {"amountMinor": 700, "currency": "IDR"},
        "bonusRecipientIds": [RECIPIENT_A, RECIPIENT_B, RECIPIENT_C],
        "remainderPolicy": "BLOCK_NON_DIVISIBLE",
        "cutoffLocal": "12:00:00",
        "overheadBasis": "FIRST_PASS_FINISHED_UNITS_PROPOSED",
    }


@pytest.fixture
def rule_request(rule_payload: dict[str, Any]) -> FinancialRuleRequest:
    return FinancialRuleRequest.model_validate(rule_payload)


@pytest.fixture
def period_payload() -> dict[str, Any]:
    """The week ending Saturday 2026-10-17, dates inclusive start, exclusive end."""
    return {
        "startsOn": "2026-10-11",
        "endsOn": "2026-10-18",
        "timezone": "Asia/Jakarta",
        "cutoffLocal": "12:00:00",
        "ruleVersion": "v1",
    }


@pytest.fixture
def period_request(period_payload: dict[str, Any]) -> PeriodRequest:
    return PeriodRequest.model_validate(period_payload)
