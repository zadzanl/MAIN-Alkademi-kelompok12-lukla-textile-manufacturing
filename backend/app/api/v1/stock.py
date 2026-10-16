import uuid
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, Response, status
from ...core.auth import AuthContext, get_current_stock_auth_context
from ...schemas.problem import ProblemException
from ...schemas.stock import (
    MaterialIssueRequest,
    MaterialLot,
    StockMovement,
    StockPage,
)

router = APIRouter(tags=["warehouse-cutting"])

# Deterministic demo lot seeds matching View-03 and warehouse domain fixtures
DEFAULT_MATERIAL_LOTS: List[MaterialLot] = [
    MaterialLot(
        id=uuid.UUID("a0000000-0000-4000-8000-000000000101"),
        tenantId=uuid.UUID("b0000000-0000-4000-8000-000000000001"),
        legalStockOwnerId=uuid.UUID("c0000000-0000-4000-8000-000000000001"),
        orderBeneficiaryId=uuid.UUID("d0000000-0000-4000-8000-000000000001"),
        orderId=uuid.UUID("e0000000-0000-4000-8000-000000000104"),
        scheme="CMT",
        sku="Kain Cotton Fleece 280gsm",
        quantity=1250.0,
        lotTag="LOT-2026-105",
        storageLocation="Rak A-08",
        status="AVAILABLE"
    ),
    MaterialLot(
        id=uuid.UUID("a0000000-0000-4000-8000-000000000102"),
        tenantId=uuid.UUID("b0000000-0000-4000-8000-000000000001"),
        legalStockOwnerId=uuid.UUID("c0000000-0000-4000-8000-000000000001"),
        orderBeneficiaryId=uuid.UUID("d0000000-0000-4000-8000-000000000001"),
        orderId=uuid.UUID("e0000000-0000-4000-8000-000000000401"),
        scheme="CMT",
        sku="Poly-Oxford 600D",
        quantity=420.0,
        lotTag="LOT-2026-99",
        storageLocation="Rak A-04",
        status="ALLOCATED"
    ),
    MaterialLot(
        id=uuid.UUID("a0000000-0000-4000-8000-000000000103"),
        tenantId=uuid.UUID("b0000000-0000-4000-8000-000000000001"),
        legalStockOwnerId=uuid.UUID("c0000000-0000-4000-8000-000000000002"),
        orderBeneficiaryId=uuid.UUID("d0000000-0000-4000-8000-000000000002"),
        orderId=uuid.UUID("e0000000-0000-4000-8000-000000000402"),
        scheme="SEMI_CMT",
        sku="Thermolite Insulation 120gsm",
        quantity=184.0,
        lotTag="LOT-2026-102",
        storageLocation="Rak B-12",
        status="ALLOCATED"
    ),
    MaterialLot(
        id=uuid.UUID("a0000000-0000-4000-8000-000000000104"),
        tenantId=uuid.UUID("b0000000-0000-4000-8000-000000000001"),
        legalStockOwnerId=uuid.UUID("c0000000-0000-4000-8000-000000000002"),
        orderBeneficiaryId=uuid.UUID("d0000000-0000-4000-8000-000000000002"),
        orderId=uuid.UUID("e0000000-0000-4000-8000-000000000402"),
        scheme="SEMI_CMT",
        sku="Taslan Microfiber",
        quantity=215.0,
        lotTag="LOT-2026-108",
        storageLocation="Rak C-01",
        status="AVAILABLE"
    ),
]

# These fixture links are only enough to exercise the ownership boundary. They
# are not an order repository and must not be treated as durable stock state.
DEFAULT_ORDER_BENEFICIARIES = {
    uuid.UUID("e0000000-0000-4000-8000-000000000104"): uuid.UUID(
        "d0000000-0000-4000-8000-000000000001"
    ),
    uuid.UUID("e0000000-0000-4000-8000-000000000401"): uuid.UUID(
        "d0000000-0000-4000-8000-000000000001"
    ),
    uuid.UUID("e0000000-0000-4000-8000-000000000402"): uuid.UUID(
        "d0000000-0000-4000-8000-000000000002"
    ),
}


def validate_material_dispatch(material_lot: MaterialLot, order_id: uuid.UUID) -> None:
    """Reject an ownership mismatch before any future repository mutation."""
    beneficiary_id = DEFAULT_ORDER_BENEFICIARIES.get(order_id)
    if beneficiary_id is None:
        raise ProblemException(
            status=404,
            code="VALIDATION_ERROR",
            detail=f"Order '{order_id}' is not available in the warehouse fixture.",
            instance="/api/v1/material-issuances",
        )

    if material_lot.orderBeneficiaryId != beneficiary_id:
        raise ProblemException(
            status=409,
            code="ORDER_BENEFICIARY_MISMATCH",
            detail=(
                "Material dispatch rejected: lot beneficiary does not match "
                "the target order beneficiary. No stock movement was created."
            ),
            instance="/api/v1/material-issuances",
        )

@router.get(
    "/stock",
    response_model=StockPage,
    status_code=status.HTTP_200_OK,
    summary="Read scoped stock",
    operation_id="getStock"
)
async def get_stock(
    response: Response,
    auth: AuthContext = Depends(get_current_stock_auth_context),
    status: Optional[str] = Query(default=None, description="Filter by stock availability status"),
    legalOwnerId: Optional[uuid.UUID] = Query(default=None, description="Filter by legal owner UUID"),
    orderBeneficiaryId: Optional[uuid.UUID] = Query(default=None, description="Filter by order beneficiary UUID"),
    tenantId: Optional[uuid.UUID] = Query(default=None, description="Filter by tenant UUID"),
    sku: Optional[str] = Query(default=None, description="Search by material SKU name")
) -> StockPage:
    """
    Returns fixture inventory matching independent scope filters.

    The response is deliberately labelled non-persistent until a repository
    exists; this route must not be mistaken for production stock accounting.
    """
    response.headers["X-Stock-Data-Source"] = "demo-non-persistent"
    lots = [lot for lot in DEFAULT_MATERIAL_LOTS if lot.tenantId == auth.tenant_id]
    if tenantId is not None and tenantId != auth.tenant_id:
        lots = []
    if status:
        lots = [l for l in lots if l.status.upper() == status.upper()]
    if legalOwnerId:
        lots = [l for l in lots if l.legalStockOwnerId == legalOwnerId]
    if orderBeneficiaryId:
        lots = [l for l in lots if l.orderBeneficiaryId == orderBeneficiaryId]
    if sku:
        sku_lower = sku.lower()
        lots = [l for l in lots if sku_lower in l.sku.lower()]

    return StockPage(items=lots, nextCursor=None)


@router.post(
    "/material-issuances",
    response_model=StockMovement,
    status_code=status.HTTP_201_CREATED,
    summary="Issue material to cutting/order",
    operation_id="issueMaterial",
)
async def issue_material(
    request: MaterialIssueRequest,
    _auth: AuthContext = Depends(get_current_stock_auth_context),
) -> StockMovement:
    """Validate beneficiary ownership without pretending fixture writes persist."""
    material_lot = next(
        (lot for lot in DEFAULT_MATERIAL_LOTS if lot.id == request.materialLotId),
        None,
    )
    if material_lot is None:
        raise ProblemException(
            status=404,
            code="VALIDATION_ERROR",
            detail=f"Material lot '{request.materialLotId}' is not available in the warehouse fixture.",
            instance="/api/v1/material-issuances",
        )

    validate_material_dispatch(material_lot, request.orderId)
    raise ProblemException(
        status=409,
        code="INVALID_STATE",
        detail=(
            "Material issuance is blocked: stock persistence is unavailable. "
            "The demo fixture was not mutated."
        ),
        instance="/api/v1/material-issuances",
    )
