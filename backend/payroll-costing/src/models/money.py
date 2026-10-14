"""Money in integer minor units, matching the contract ``Money`` schema."""

from typing import Final

from pydantic import Field

from src.models.base import ContractModel

CURRENCY_PATTERN: Final = r"^[A-Z]{3}$"


class Money(ContractModel):
    """A currency amount. Floating point is never used for money."""

    amount_minor: int = Field(ge=0, description="Amount in minor units (rupiah, no decimals)")
    currency: str = Field(pattern=CURRENCY_PATTERN, description="ISO 4217 alphabetic code")
