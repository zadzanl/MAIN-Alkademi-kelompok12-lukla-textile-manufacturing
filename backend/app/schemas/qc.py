"""Contract-shaped schemas for the QC & MES operations.

Field names match the frozen contract's JSON exactly (`contracts/openapi.yaml`):
`QcRequest`, `QcInspection`, `Assembly`, `AssemblyPage`, `Defect`, `QcSummary`.
"""

import uuid
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

Disposition = Literal["PASS", "REPAIR", "REJECT"]
AssemblyStatus = Literal["ASSEMBLING", "MENUNGGU_QC", "QC_PASS", "REWORK", "REJECT_SCRAP"]


class Defect(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    componentUnitId: uuid.UUID
    code: str = Field(..., min_length=1)
    # The contract declares `notes` as a string, not a nullable string, so a null is not emitted.
    notes: Optional[str] = None


class QcRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    assemblyId: uuid.UUID
    disposition: Disposition
    defects: List[Defect]


class QcInspection(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id: uuid.UUID
    assemblyId: uuid.UUID
    disposition: Disposition
    defects: List[Defect]


class Assembly(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id: uuid.UUID
    orderId: uuid.UUID
    serialCode: str
    componentUnitIds: List[uuid.UUID]
    status: AssemblyStatus


class AssemblyPage(BaseModel):
    """`AssemblyPage` in the contract carries `items` only: it has no cursor."""

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    items: List[Assembly]
