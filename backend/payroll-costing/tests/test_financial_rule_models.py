"""The rule schemas must accept exactly what the frozen contract accepts."""

from typing import Any
from uuid import UUID

import pytest
from pydantic import ValidationError

from src.models.financial_rule import (
    FinancialRule,
    FinancialRuleApproval,
    FinancialRulePage,
    FinancialRuleRequest,
    RuleStatus,
)


def test_camel_case_payload_round_trips(rule_payload: dict[str, Any]) -> None:
    request = FinancialRuleRequest.model_validate(rule_payload)

    assert request.meal_basis_points == 1250
    assert request.model_dump(mode="json", by_alias=True) == rule_payload


def test_unknown_property_is_rejected(rule_payload: dict[str, Any]) -> None:
    payload = dict(rule_payload, undocumentedKnob="yes")

    with pytest.raises(ValidationError):
        FinancialRuleRequest.model_validate(payload)


@pytest.mark.parametrize("points", [1000, 1500])
def test_meal_basis_points_accepts_the_frozen_range(
    rule_payload: dict[str, Any], points: int
) -> None:
    payload = dict(rule_payload, mealBasisPoints=points)

    assert FinancialRuleRequest.model_validate(payload).meal_basis_points == points


@pytest.mark.parametrize("points", [999, 1501])
def test_meal_basis_points_rejects_outside_ten_to_fifteen_percent(
    rule_payload: dict[str, Any], points: int
) -> None:
    payload = dict(rule_payload, mealBasisPoints=points)

    with pytest.raises(ValidationError):
        FinancialRuleRequest.model_validate(payload)


def test_exactly_three_unique_bonus_recipients_are_required(rule_payload: dict[str, Any]) -> None:
    recipients = rule_payload["bonusRecipientIds"]

    for invalid in (recipients[:2], [*recipients, recipients[0]], [recipients[0]] * 3):
        with pytest.raises(ValidationError):
            FinancialRuleRequest.model_validate(dict(rule_payload, bonusRecipientIds=invalid))


def test_bonus_rate_is_integer_minor_units(rule_payload: dict[str, Any]) -> None:
    request = FinancialRuleRequest.model_validate(rule_payload)

    assert request.bonus_rate.amount_minor == 700
    assert request.bonus_rate.currency == "IDR"

    for invalid_rate in (
        {"amountMinor": -1, "currency": "IDR"},
        {"amountMinor": 1, "currency": "idr"},
    ):
        with pytest.raises(ValidationError):
            FinancialRuleRequest.model_validate(dict(rule_payload, bonusRate=invalid_rate))


def test_rule_status_is_limited_to_pending_and_approved(rule_payload: dict[str, Any]) -> None:
    rule = FinancialRule.model_validate(
        dict(rule_payload, id="44444444-4444-4444-8444-444444444444", status="PENDING")
    )

    assert rule.status is RuleStatus.PENDING

    with pytest.raises(ValidationError):
        FinancialRule.model_validate(
            dict(rule_payload, id="44444444-4444-4444-8444-444444444444", status="DRAFT")
        )


def test_approval_requires_evidence_and_bounded_optional_text() -> None:
    approval = FinancialRuleApproval.model_validate(
        {
            "evidenceFileId": "55555555-5555-4555-8555-555555555555",
            "approvalReference": "BO-2026-041",
        }
    )

    assert isinstance(approval.evidence_file_id, UUID)
    assert approval.note is None

    invalid_bodies = [
        {},
        {"evidenceFileId": "55555555-5555-4555-8555-555555555555", "approvalReference": ""},
        {"evidenceFileId": "55555555-5555-4555-8555-555555555555", "note": "x" * 501},
        {"evidenceFileId": "55555555-5555-4555-8555-555555555555", "approver": "someone"},
    ]
    for body in invalid_bodies:
        with pytest.raises(ValidationError):
            FinancialRuleApproval.model_validate(body)


def test_rule_page_wraps_rules(rule_payload: dict[str, Any]) -> None:
    rule = dict(rule_payload, id="44444444-4444-4444-8444-444444444444", status="APPROVED")

    page = FinancialRulePage.model_validate({"items": [rule]})

    assert [item.status for item in page.items] == [RuleStatus.APPROVED]
