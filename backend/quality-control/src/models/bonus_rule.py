"""The bonus rule version in force when an assembly is inspected.

This is the QC module's read-only view of MOD-05's ``financial_rule_versions``:
the version label recorded on ``qc_bonus_accruals.rule_version``, the identifier
recorded on ``eligibility_events.rule_version_id``, the approval status, and the
per-pass bonus rate. Only an approved version carries a rate, so the impossible
combination is refused at construction instead of at the point of payment.
"""

from dataclasses import dataclass
try:
    from enum import StrEnum
except ImportError:
    from enum import Enum
    class StrEnum(str, Enum):
        pass

try:
    from typing import Self
except ImportError:
    from typing_extensions import Self

from uuid import UUID

from src.models.money import Money


class RuleStatus(StrEnum):
    """A rule version produces no monetary amount until it is ``APPROVED``."""

    PENDING = "PENDING"
    APPROVED = "APPROVED"


@dataclass(frozen=True, slots=True)
class BonusRule:
    """A bonus rule version. Construct it through ``approved`` or ``pending``."""

    rule_version: str
    rule_version_id: UUID | None
    status: RuleStatus
    bonus_rate: Money | None

    def __post_init__(self) -> None:
        if not self.rule_version:
            raise ValueError("A bonus rule must carry its version label")
        if self.status is RuleStatus.APPROVED and self.bonus_rate is None:
            raise ValueError("An approved bonus rule must carry its per-pass bonus rate")
        if self.status is RuleStatus.PENDING and self.bonus_rate is not None:
            raise ValueError(
                "A pending bonus rule must not carry a rate; the rate is resolved when the "
                "rule version is approved, not before"
            )

    @classmethod
    def approved(cls, *, rule_version: str, rule_version_id: UUID, bonus_rate: Money) -> Self:
        return cls(
            rule_version=rule_version,
            rule_version_id=rule_version_id,
            status=RuleStatus.APPROVED,
            bonus_rate=bonus_rate,
        )

    @classmethod
    def pending(cls, *, rule_version: str, rule_version_id: UUID | None = None) -> Self:
        """A version that is proposed but not authorized: no rate exists yet."""
        return cls(
            rule_version=rule_version,
            rule_version_id=rule_version_id,
            status=RuleStatus.PENDING,
            bonus_rate=None,
        )

    @property
    def is_approved(self) -> bool:
        return self.status is RuleStatus.APPROVED
