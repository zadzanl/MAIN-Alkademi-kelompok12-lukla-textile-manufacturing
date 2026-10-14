"""The financial rule gate.

Every payroll, bonus, and overhead calculation resolves the rule versions it
depends on. While any of them is not ``APPROVED`` the operation must fail with
``FINANCIAL_RULE_PENDING`` and persist nothing. There is deliberately no
fallback value, environment variable, or demo default anywhere in this path.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from uuid import UUID

from src.models.financial_rule import RuleStatus
from src.services.errors import FinancialRulePending


@dataclass(frozen=True, slots=True)
class RuleReference:
    """A rule version that a calculation depends on."""

    rule_id: UUID
    status: RuleStatus


@dataclass(frozen=True, slots=True)
class GateDecision:
    """Whether a calculation may proceed, and which rule versions block it."""

    allowed: bool
    pending_rule_ids: tuple[UUID, ...]


def evaluate_gate(required: Sequence[RuleReference]) -> GateDecision:
    """Return the gate decision for the rule versions a calculation depends on."""
    pending = tuple(ref.rule_id for ref in required if ref.status is not RuleStatus.APPROVED)
    return GateDecision(allowed=not pending, pending_rule_ids=pending)


def require_approved(required: Sequence[RuleReference]) -> None:
    """Raise ``FinancialRulePending`` unless every referenced rule version is approved."""
    decision = evaluate_gate(required)
    if not decision.allowed:
        blocked = ", ".join(sorted(str(rule_id) for rule_id in decision.pending_rule_ids))
        raise FinancialRulePending(
            f"Financial rule authorization is pending for rule version(s): {blocked}"
        )
