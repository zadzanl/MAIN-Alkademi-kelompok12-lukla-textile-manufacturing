from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Literal
import uuid

class LedgerEntry(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    accountCode: str = Field(..., alias="accountCode")
    direction: Literal["DEBIT", "CREDIT"]
    amountMinor: int = Field(..., ge=1, alias="amountMinor")

class LedgerRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    transactionType: str = Field(..., alias="transactionType")
    currency: str = Field(..., pattern="^[A-Z]{3}$")
    entries: List[LedgerEntry] = Field(..., min_length=2)

class LedgerTransaction(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id: uuid.UUID
    tenantId: uuid.UUID = Field(..., alias="tenantId")
    entries: List[LedgerEntry]
    reversalOf: Optional[uuid.UUID] = Field(default=None, alias="reversalOf")

class ReversalRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    reason: str

class LedgerPage(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    items: List[LedgerTransaction]
    nextCursor: Optional[str] = Field(default=None, alias="nextCursor")
