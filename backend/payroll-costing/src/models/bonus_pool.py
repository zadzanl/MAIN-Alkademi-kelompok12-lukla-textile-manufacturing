"""Quality bonus pool schemas."""

try:
    from enum import StrEnum
except ImportError:
    from enum import Enum
    class StrEnum(str, Enum):
        pass
from uuid import UUID

from pydantic import Field

from src.models.base import ContractModel
from src.models.money import Money


class BonusPoolStatus(StrEnum):
    """The contract leaves ``BonusPool.status`` untyped, so this mirrors the
    payroll result vocabulary rather than inventing a new one."""

    CALCULATED = "CALCULATED"
    NO_OUTPUT = "NO_OUTPUT"


class BonusRecipient(ContractModel):
    """One share of the pool."""

    recipient_id: UUID
    amount: Money


class BonusPool(ContractModel):
    """Body of ``getBonusPool``; the contract fixes the recipient count at three."""

    period_id: UUID
    pool: Money
    recipients: list[BonusRecipient] = Field(min_length=3, max_length=3)
    status: BonusPoolStatus
