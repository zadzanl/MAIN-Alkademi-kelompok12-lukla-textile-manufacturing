"""Quality Control & MES routers, bound one-to-one to contract operationIds.

Implemented here: `inspectUnit` (the disposition recording) and `listAssemblies` (the QC queue).
`createAssembly` and `listProductionProgress` wait for `orders` (M004) and `garment_units`/tallies
(M006), and the `qc` section of `getDashboard` waits for those same tables before the dashboard
schema can be filled; see `openspec/changes/lukla-qc-mes-engine/tasks.md` phase 4.
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Header, Query, Request, status
from sqlalchemy.orm import Session

from ...core.auth import AuthContext, require_roles
from ...core.database import get_db
from ...schemas.qc import AssemblyPage, QcInspection, QcRequest
from ...services.qc import inspect_unit, list_assemblies

router = APIRouter(tags=["quality-mes"])


@router.post(
    "/qc-inspections",
    response_model=QcInspection,
    status_code=status.HTTP_201_CREATED,
    operation_id="inspectUnit",
    summary="Classify assembly Pass Repair Reject",
)
def inspect_unit_route(
    request: Request,
    body: QcRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=16, max_length=200),
    auth_context: AuthContext = Depends(
        require_roles("QCInspector", capability="quality inspection")
    ),
    db: Session = Depends(get_db),
) -> QcInspection:
    request_id = getattr(request.state, "request_id", uuid.uuid4())
    return inspect_unit(
        db=db,
        auth_context=auth_context,
        request=body,
        idempotency_key=idempotency_key,
        request_id=request_id,
        instance=request.url.path,
    )


@router.get(
    "/assemblies",
    response_model=AssemblyPage,
    status_code=status.HTTP_200_OK,
    operation_id="listAssemblies",
    summary="List assemblies including the QC queue",
)
def list_assemblies_route(
    request: Request,
    status_filter: Optional[str] = Query(
        None,
        alias="status",
        pattern="^(MENUNGGU_QC|REWORK|QC_PASS|REJECT_SCRAP)$",
    ),
    auth_context: AuthContext = Depends(
        require_roles("ProductionHead", "QCInspector", capability="assembly listing")
    ),
    db: Session = Depends(get_db),
) -> AssemblyPage:
    return list_assemblies(
        db=db,
        auth_context=auth_context,
        status_filter=status_filter,
        instance=request.url.path,
    )
