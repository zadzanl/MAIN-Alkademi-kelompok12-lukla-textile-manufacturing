"""Pure phase-4 orchestration over an explicit QC/MES adapter."""

from uuid import UUID

from src.adapters.qc_mes import QcMesAdapter
from src.models.bonus_pool import BonusPool
from src.models.financial_rule import RemainderPolicy
from src.models.payroll_calculation import PayrollResult
from src.services.bonus_pool import calculate_bonus_pool
from src.services.wage_calculation import calculate_weekly_payroll
from src.services.rule_gate import RuleReference


def calculate_weekly_from_facts(
    *,
    adapter: QcMesAdapter,
    tenant_id: UUID,
    period_id: UUID,
    required_rules: list[RuleReference],
    currency: str,
    recipient_ids: list[UUID],
    remainder_policy: RemainderPolicy,
) -> tuple[PayrollResult, BonusPool]:
    """Calculate wages and bonuses from one explicit, tenant-scoped fact load.

    No monetary persistence occurs here. Callers must persist the result in the
    same transaction as any accounting record once those repositories exist.
    """
    facts = adapter.load_facts(tenant_id, period_id)
    wages = calculate_weekly_payroll(
        period_id=period_id,
        required_rules=required_rules,
        units=facts.units,
        currency=currency,
    )
    bonuses = calculate_bonus_pool(
        period_id=period_id,
        required_rules=required_rules,
        accruals=facts.bonus_accruals,
        recipient_ids=recipient_ids,
        remainder_policy=remainder_policy,
        currency=currency,
    )
    return wages, bonuses
