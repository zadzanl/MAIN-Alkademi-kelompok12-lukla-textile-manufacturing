"""The gate is the only thing standing between an unapproved rule and a paid wage."""

from uuid import UUID

import pytest

from src.models.financial_rule import RuleStatus
from src.models.problem import ErrorCode
from src.services.errors import FinancialRulePending
from src.services.rule_gate import GateDecision, RuleReference, evaluate_gate, require_approved

APPROVED_RULE = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
PENDING_RULE = UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")
SECOND_PENDING_RULE = UUID("cccccccc-cccc-4ccc-8ccc-cccccccccccc")


def reference(rule_id: UUID, status: RuleStatus) -> RuleReference:
    return RuleReference(rule_id=rule_id, status=status)


def test_all_approved_rules_open_the_gate() -> None:
    decision = evaluate_gate(
        [
            reference(APPROVED_RULE, RuleStatus.APPROVED),
            reference(SECOND_PENDING_RULE, RuleStatus.APPROVED),
        ]
    )

    assert decision == GateDecision(allowed=True, pending_rule_ids=())


def test_no_referenced_rules_means_nothing_blocks() -> None:
    assert evaluate_gate([]).allowed is True


def test_a_pending_rule_blocks_and_is_named() -> None:
    decision = evaluate_gate(
        [reference(APPROVED_RULE, RuleStatus.APPROVED), reference(PENDING_RULE, RuleStatus.PENDING)]
    )

    assert decision.allowed is False
    assert decision.pending_rule_ids == (PENDING_RULE,)


def test_every_pending_rule_is_reported() -> None:
    decision = evaluate_gate(
        [
            reference(PENDING_RULE, RuleStatus.PENDING),
            reference(SECOND_PENDING_RULE, RuleStatus.PENDING),
        ]
    )

    assert set(decision.pending_rule_ids) == {PENDING_RULE, SECOND_PENDING_RULE}


def test_require_approved_raises_the_contract_error_code() -> None:
    with pytest.raises(FinancialRulePending) as raised:
        require_approved([reference(PENDING_RULE, RuleStatus.PENDING)])

    assert raised.value.code is ErrorCode.FINANCIAL_RULE_PENDING
    assert str(PENDING_RULE) in str(raised.value)


def test_require_approved_is_silent_when_the_rule_is_approved() -> None:
    require_approved([reference(APPROVED_RULE, RuleStatus.APPROVED)])
