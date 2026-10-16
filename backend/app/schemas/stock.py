import uuid
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict


class MaterialQuantity(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    value: str = Field(..., pattern=r"^(0|[1-9][0-9]*)(\.[0-9]+)?$")
    unit: Literal["PIECE", "METER", "KILOGRAM", "ROLL"]

class MaterialLot(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id: uuid.UUID
    tenantId: uuid.UUID = Field(..., alias="tenantId")
    legalStockOwnerId: uuid.UUID = Field(..., alias="legalStockOwnerId")
    orderBeneficiaryId: uuid.UUID = Field(..., alias="orderBeneficiaryId")
    orderId: uuid.UUID = Field(..., alias="orderId")
    scheme: Literal["CMT", "SEMI_CMT", "FULL_PACKAGE"]
    sku: str
    quantity: float
    lotTag: Optional[str] = Field(default=None, alias="lotTag")
    storageLocation: Optional[str] = Field(default=None, alias="storageLocation")
    status: Literal["AVAILABLE", "RESERVED", "ALLOCATED", "DEPLETED"] = "AVAILABLE"

class StockPage(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    items: List[MaterialLot]
    nextCursor: Optional[str] = Field(default=None, alias="nextCursor")


class MaterialIssueRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    materialLotId: uuid.UUID = Field(..., alias="materialLotId")
    orderId: uuid.UUID = Field(..., alias="orderId")
    quantity: MaterialQuantity


class StockMovement(MaterialIssueRequest):
    id: uuid.UUID
