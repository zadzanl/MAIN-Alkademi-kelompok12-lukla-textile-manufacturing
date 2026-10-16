"""Explicit QC/MES input boundary for payroll calculations.

The production adapter is intentionally not implemented until the upstream QC/MES
contracts are available. Fixture data must be selected explicitly by callers and
carries a fixture-set identifier so it cannot be mistaken for production data.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from src.services.bonus_pool import BonusAccrual
from src.services.wage_calculation import EligibleUnit


@dataclass(frozen=True, slots=True)
class ProductionFacts:
    tenant_id: UUID
    period_id: UUID
    fixture_set_id: str | None
    units: Sequence[EligibleUnit]
    bonus_accruals: Sequence[BonusAccrual]


class QcMesAdapter(Protocol):
    def load_facts(self, tenant_id: UUID, period_id: UUID) -> ProductionFacts:
        """Load verified production facts for one tenant and payroll period."""


class FixtureQcMesAdapter:
    """Test-only adapter requiring an explicit, non-empty fixture set ID."""

    def __init__(self, facts: ProductionFacts) -> None:
        if not facts.fixture_set_id or not facts.fixture_set_id.strip():
            raise ValueError("fixture_set_id is required for fixture payroll facts")
        self._facts = facts

    def load_facts(self, tenant_id: UUID, period_id: UUID) -> ProductionFacts:
        if self._facts.tenant_id != tenant_id or self._facts.period_id != period_id:
            raise LookupError("fixture facts are outside the requested tenant or period")
        return self._facts


class ProductionQcMesAdapter:
    """Reserved production boundary; never silently falls back to fixtures."""

    def load_facts(self, tenant_id: UUID, period_id: UUID) -> ProductionFacts:
        raise RuntimeError(
            "QC/MES production adapter is unavailable; provide a verified upstream adapter"
        )
