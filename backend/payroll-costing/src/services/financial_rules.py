"""Financial rule registry: proposing and approving versioned parameter sets.

Approval is the only way a rule becomes usable. It requires the ``Owner`` role
and recorded business evidence, because the contract's invariant states that a
proposal is not authorization. Everything else in the payroll engine depends on
that single transition.
"""

from typing import Final
from uuid import UUID

from src.models.financial_rule import (
    FinancialRule,
    FinancialRuleRequest,
    RuleStatus,
)
from src.services.errors import Forbidden

PROPOSER_ROLES: Final = frozenset({"Owner", "FinancePayroll"})
APPROVER_ROLES: Final = frozenset({"Owner"})


def assert_may_propose(role: str) -> None:
    """``proposeFinancialRule`` is open to Owner and FinancePayroll."""
    if role not in PROPOSER_ROLES:
        raise Forbidden(f"Role {role} may not propose a financial rule")


def assert_may_approve(role: str) -> None:
    """``approveFinancialRule`` is restricted to Owner."""
    if role not in APPROVER_ROLES:
        raise Forbidden(f"Role {role} may not approve a financial rule")


def propose_rule(request: FinancialRuleRequest, rule_id: UUID) -> FinancialRule:
    """Store a new rule version in ``PENDING``; it cannot be used yet."""
    return FinancialRule(id=rule_id, status=RuleStatus.PENDING, **request.model_dump())


def approve_rule(rule: FinancialRule, role: str) -> FinancialRule:
    """Authorize the transition to ``APPROVED`` and return the approved copy.

    Only the state transition and its authorization live here. The approval body
    (evidence file, reference, note) is validated at the API boundary, and
    persisting it is pending a schema decision: the frozen
    ``financial_rule_versions`` table has no evidence or approver column, and
    ``FinancialRule`` exposes neither, so the API never reports who approved.
    """
    assert_may_approve(role)
    return rule.model_copy(update={"status": RuleStatus.APPROVED})
