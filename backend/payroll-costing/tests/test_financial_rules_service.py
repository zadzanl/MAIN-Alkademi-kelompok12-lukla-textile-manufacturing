"""Proposing never approves; only an Owner can open the gate."""

from uuid import UUID

import pytest

from src.models.financial_rule import FinancialRule, FinancialRuleRequest, RuleStatus
from src.models.problem import ErrorCode
from src.services.errors import FinancialRulePending, Forbidden
from src.services.financial_rules import (
    approve_rule,
    assert_may_approve,
    assert_may_propose,
    propose_rule,
)
from src.services.rule_gate import RuleReference, require_approved

RULE_ID = UUID("44444444-4444-4444-8444-444444444444")


def test_proposing_always_creates_a_pending_rule(rule_request: FinancialRuleRequest) -> None:
    rule = propose_rule(rule_request, RULE_ID)

    assert rule.status is RuleStatus.PENDING
    assert rule.id == RULE_ID


def test_proposing_keeps_every_contract_field(rule_request: FinancialRuleRequest) -> None:
    rule = propose_rule(rule_request, RULE_ID)

    assert rule.model_dump(exclude={"id", "status"}) == rule_request.model_dump()


def test_only_owner_and_finance_may_propose() -> None:
    assert_may_propose("Owner")
    assert_may_propose("FinancePayroll")

    with pytest.raises(Forbidden) as raised:
        assert_may_propose("ProductionHead")

    assert raised.value.code is ErrorCode.FORBIDDEN


def test_only_owner_may_approve() -> None:
    assert_may_approve("Owner")

    with pytest.raises(Forbidden):
        assert_may_approve("FinancePayroll")


def test_approval_opens_the_gate_and_leaves_the_proposal_untouched(
    rule_request: FinancialRuleRequest,
) -> None:
    pending = propose_rule(rule_request, RULE_ID)

    with pytest.raises(FinancialRulePending):
        require_approved([RuleReference(rule_id=pending.id, status=pending.status)])

    approved = approve_rule(pending, "Owner")

    assert approved.status is RuleStatus.APPROVED
    assert pending.status is RuleStatus.PENDING
    require_approved([RuleReference(rule_id=approved.id, status=approved.status)])


def test_a_forbidden_approval_leaves_the_rule_pending(rule_request: FinancialRuleRequest) -> None:
    pending = propose_rule(rule_request, RULE_ID)

    with pytest.raises(Forbidden):
        approve_rule(pending, "FinancePayroll")

    assert pending.status is RuleStatus.PENDING
    assert isinstance(pending, FinancialRule)
