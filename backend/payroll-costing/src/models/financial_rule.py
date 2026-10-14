"""Financial rule schemas: the versioned parameter set that gates every calculation."""

from datetime import date
from enum import StrEnum
from uuid import UUID

from pydantic import Field, field_validator

from src.models.base import ContractModel
from src.models.money import Money


class RuleStatus(StrEnum):
    """A rule version is unusable for calculation until it is ``APPROVED``."""

    PENDING = "PENDING"
    APPROVED = "APPROVED"


class MealBasis(StrEnum):
    VERIFIED_WAGES_PROPOSED = "VERIFIED_WAGES_PROPOSED"


class MealDistribution(StrEnum):
    PROPORTIONAL_PROPOSED = "PROPORTIONAL_PROPOSED"
    EQUAL_ACTIVE_PROPOSED = "EQUAL_ACTIVE_PROPOSED"


class RemainderPolicy(StrEnum):
    """``RESERVE_PROPOSED`` stays blocked: BRD section 13.2 forbids a named reserve account."""

    BLOCK_NON_DIVISIBLE = "BLOCK_NON_DIVISIBLE"
    RESERVE_PROPOSED = "RESERVE_PROPOSED"


class OverheadBasis(StrEnum):
    FIRST_PASS_FINISHED_UNITS_PROPOSED = "FIRST_PASS_FINISHED_UNITS_PROPOSED"


class FinancialRuleFields(ContractModel):
    """The nine parameters the contract requires, with the frozen ranges and enums."""

    effective_from: date
    meal_basis: MealBasis
    meal_basis_points: int = Field(
        ge=1000, le=1500, description="10 to 15 percent, in basis points"
    )
    meal_distribution: MealDistribution
    bonus_rate: Money
    bonus_recipient_ids: list[UUID] = Field(min_length=3, max_length=3)
    remainder_policy: RemainderPolicy
    cutoff_local: str
    overhead_basis: OverheadBasis

    @field_validator("bonus_recipient_ids")
    @classmethod
    def _recipients_unique(cls, value: list[UUID]) -> list[UUID]:
        if len(set(value)) != len(value):
            raise ValueError("bonusRecipientIds must be unique")
        return value


class FinancialRuleRequest(FinancialRuleFields):
    """Body of ``proposeFinancialRule``."""


class FinancialRule(FinancialRuleFields):
    """A stored rule version, as returned by the contract."""

    id: UUID
    status: RuleStatus


class FinancialRuleApproval(ContractModel):
    """Body of ``approveFinancialRule``; evidence is mandatory, not a formality."""

    evidence_file_id: UUID
    approval_reference: str | None = Field(default=None, min_length=1, max_length=200)
    note: str | None = Field(default=None, max_length=500)


class FinancialRulePage(ContractModel):
    """Body of ``listFinancialRules``."""

    items: list[FinancialRule]
