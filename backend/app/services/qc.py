"""Quality inspection recording: the persistence behind `inspectUnit` and `listAssemblies`.

The rules this module must not re-invent are enforced by migration M007 and mapped here
to the contract's `Problem` codes:

- the disposition state machine (`MENUNGGU_QC | REWORK -> PASS | REPAIR | REJECT`),
  the terminal refusal, and the per-assembly sequence number
  (`trg_qc_inspections_prepare`),
- the disposition moving the assembly and its pieces
  (`trg_qc_inspections_apply_disposition`),
- the defect rules and the cross-assembly defect refusal
  (`trg_qc_defects_verify_piece`, `trg_qc_inspections_defect_rules`),
- the append-only log (the runtime role holds no `UPDATE`/`DELETE` privilege).

The one rule the database cannot answer is the tenant's defect taxonomy, because the frozen
schema has no taxonomy table: it is deployment configuration (design decision 4).

Known ceiling: the money a first `PASS` produces (one `eligibility_events` row, one
`wage_credits` row per allocated piece, one `qc_bonus_accruals` row) is written by
`classify_qc_unit`, task 3.2 of `openspec/changes/lukla-qc-mes-engine/tasks.md`. That routine
waits for migration `M009`, which owns those three tables and belongs to the payroll module,
so an inspection recorded before it lands carries the disposition and the piece statuses but
no money rows. See the module README for the operational consequence.
"""

import json
import uuid
from typing import Any, Dict, List, Optional, Sequence, Tuple

from sqlalchemy import insert, select
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from ..core.auth import AuthContext
from ..core.config import settings
from ..models.qc import AssemblyComponent, GarmentAssembly, QcDefect, QcInspection as QcInspectionRow
from ..schemas.problem import ProblemException
from ..schemas.qc import Assembly, AssemblyPage, Defect, QcInspection, QcRequest
from .idempotency import complete_idempotency, compute_canonical_hash, reserve_or_get_idempotency

INSPECT_UNIT_OPERATION_ID = "inspectUnit"

# Every rule M007 raises by name, and the response the contract gives it.
# Source: backend/quality-control/API_CONTRACTS.md, "Database error mapping".
_DATABASE_RULES: Tuple[Tuple[str, int, str, str], ...] = (
    (
        "QC_ASSEMBLY_NOT_FOUND",
        400,
        "VALIDATION_ERROR",
        "The assembly does not exist in this tenant",
    ),
    (
        "QC_ASSEMBLY_NOT_READY",
        409,
        "INVALID_STATE",
        "An assembly that is still assembling cannot be inspected",
    ),
    (
        "QC_DISPOSITION_TERMINAL",
        409,
        "INVALID_STATE",
        "A final pass or reject cannot be overridden in this release",
    ),
    (
        "QC_DEFECT_REQUIRED",
        400,
        "VALIDATION_ERROR",
        "A repair or reject disposition must select a defect category",
    ),
    (
        "QC_DEFECT_NOT_ALLOWED",
        400,
        "VALIDATION_ERROR",
        "A pass disposition must not carry a defect category",
    ),
    (
        "QC_DEFECT_FOREIGN_COMPONENT",
        400,
        "VALIDATION_ERROR",
        "The defect names a component piece that is not allocated to this assembly",
    ),
    (
        "QC_INSPECTION_NOT_FOUND",
        400,
        "VALIDATION_ERROR",
        "The inspection does not exist in this tenant",
    ),
    (
        "uq_qc_inspections_sequence",
        409,
        "IDEMPOTENCY_CONFLICT",
        "Another inspection of this assembly was recorded concurrently",
    ),
    (
        "uq_qc_defects_piece",
        400,
        "VALIDATION_ERROR",
        "A component piece appears twice in one inspection",
    ),
    (
        "uq_assembly_components_unit",
        400,
        "VALIDATION_ERROR",
        "A component piece already belongs to an assembly",
    ),
)


def load_defect_taxonomy() -> Dict[str, Any]:
    """Read the deployment-managed taxonomy file; an unreadable file means no known code."""
    try:
        with open(settings.QC_DEFECT_TAXONOMY_PATH, encoding="utf-8") as handle:
            loaded = json.load(handle)
    except (OSError, ValueError):
        return {}
    return loaded if isinstance(loaded, dict) else {}


def defect_taxonomy(tenant_id: uuid.UUID) -> Tuple[str, ...]:
    """
    The defect codes the tenant may record, exactly as configured.

    A tenant entry replaces the default list; an explicit empty list means the tenant
    has no recordable code, which is a refusal rather than a fallback.
    """
    configuration = load_defect_taxonomy()
    tenants = configuration.get("tenants")
    tenant_codes: Any = None
    if isinstance(tenants, dict) and str(tenant_id) in tenants:
        tenant_codes = tenants[str(tenant_id)]
    else:
        tenant_codes = configuration.get("default")
    if not isinstance(tenant_codes, list):
        return ()
    return tuple(str(code).strip() for code in tenant_codes)


def map_database_error(exc: DBAPIError, instance: str) -> Optional[ProblemException]:
    """Translate a named database refusal into the contract's `Problem`; None means re-raise."""
    origin = getattr(exc, "orig", None)
    diagnostics = getattr(origin, "diag", None)
    primary = getattr(diagnostics, "message_primary", None) or ""
    constraint = getattr(diagnostics, "constraint_name", None) or ""
    sqlstate = getattr(origin, "pgcode", None) or ""
    message = f"{primary} {constraint} {exc}"

    for marker, status, code, detail in _DATABASE_RULES:
        if marker in message:
            return ProblemException(status=status, code=code, detail=detail, instance=instance)

    if sqlstate == "42501":
        return ProblemException(
            status=400,
            code="TENANT_CONTEXT_MISSING",
            detail="The runtime role has no tenant context for this row",
            instance=instance,
        )
    if sqlstate == "23503":
        return ProblemException(
            status=400,
            code="VALIDATION_ERROR",
            detail="A referenced row does not exist in this tenant",
            instance=instance,
        )
    return None


def _preflight(
    db: Session, auth_context: AuthContext, assembly_id: uuid.UUID, instance: str
) -> None:
    """
    Refuse an inspection the contract refuses, before the insert.

    Two of these rules are the database's and are re-checked under the assembly row lock on
    insert, so this read only decides the response the caller sees first: an assembly that is
    assembling or terminal is `INVALID_STATE`, and an assembly with no allocated piece has
    nothing to credit, which no trigger checks.
    """
    assembly = db.execute(
        select(GarmentAssembly.status).where(
            GarmentAssembly.tenant_id == auth_context.tenant_id,
            GarmentAssembly.id == assembly_id,
        )
    ).scalar_one_or_none()

    if assembly is None:
        raise ProblemException(
            status=400,
            code="VALIDATION_ERROR",
            detail=f"Assembly '{assembly_id}' does not exist in this tenant",
            instance=instance,
        )
    if assembly == "ASSEMBLING":
        raise ProblemException(
            status=409,
            code="INVALID_STATE",
            detail=f"Assembly '{assembly_id}' is still assembling and cannot be inspected",
            instance=instance,
        )
    if assembly in ("QC_PASS", "REJECT_SCRAP"):
        raise ProblemException(
            status=409,
            code="INVALID_STATE",
            detail=(
                f"Assembly '{assembly_id}' reached its final disposition '{assembly}' "
                "and cannot be inspected again in this release"
            ),
            instance=instance,
        )

    allocated = db.execute(
        select(AssemblyComponent.id).where(
            AssemblyComponent.tenant_id == auth_context.tenant_id,
            AssemblyComponent.assembly_id == assembly_id,
        ).limit(1)
    ).first()
    if allocated is None:
        raise ProblemException(
            status=400,
            code="VALIDATION_ERROR",
            detail=f"Assembly '{assembly_id}' has no allocated component piece to inspect",
            instance=instance,
        )


def _verify_defect_codes(
    tenant_id: uuid.UUID, defects: Sequence[Defect], instance: str
) -> None:
    """Refuse a defect code the tenant has not configured, naming the code."""
    if not defects:
        return
    known = set(defect_taxonomy(tenant_id))
    for defect in defects:
        if defect.code not in known:
            raise ProblemException(
                status=400,
                code="VALIDATION_ERROR",
                detail=(
                    f"Unknown defect code '{defect.code}' for tenant {tenant_id}; "
                    f"the configured taxonomy has {len(known)} code(s)"
                ),
                instance=instance,
            )


def inspect_unit(
    db: Session,
    auth_context: AuthContext,
    request: QcRequest,
    idempotency_key: str,
    request_id: uuid.UUID,
    instance: str = "/api/v1/qc-inspections",
) -> QcInspection:
    """
    Record one assembly disposition.

    Order matters and is the contract's: a replayed request is answered from the stored
    decision before the terminal-state check runs, so the retry of the delivery that caused
    `QC_PASS` succeeds instead of failing as an override.
    """
    if auth_context.actor_id is None:
        raise ProblemException(
            status=401,
            code="AUTH_REQUIRED",
            detail="An inspection must name the inspector; the token carries no actor subject",
            instance=instance,
        )

    payload = request.model_dump(mode="json", by_alias=True)
    payload_hash = compute_canonical_hash(payload)

    is_new, cached = reserve_or_get_idempotency(
        db,
        tenant_id=auth_context.tenant_id,
        operation_id=INSPECT_UNIT_OPERATION_ID,
        key=idempotency_key,
        payload_hash=payload_hash,
        instance=instance,
    )
    if not is_new:
        assert cached is not None
        _status, body = cached
        return QcInspection.model_validate(body)

    _preflight(db, auth_context, request.assemblyId, instance)
    _verify_defect_codes(auth_context.tenant_id, request.defects, instance)

    inspection_id = uuid.uuid4()
    try:
        db.execute(
            insert(QcInspectionRow).values(
                id=inspection_id,
                tenant_id=auth_context.tenant_id,
                assembly_id=request.assemblyId,
                inspector_id=auth_context.actor_id,
                disposition=request.disposition,
                # The insert trigger assigns the next sequence number for this assembly.
                sequence_no=None,
                idempotency_key=idempotency_key,
            )
        )
        if request.defects:
            db.execute(
                insert(QcDefect).values(
                    [
                        {
                            "id": uuid.uuid4(),
                            "tenant_id": auth_context.tenant_id,
                            "inspection_id": inspection_id,
                            "garment_unit_id": defect.componentUnitId,
                            "defect_code": defect.code,
                            "notes": defect.notes,
                        }
                        for defect in request.defects
                    ]
                )
            )

        decision = QcInspection(
            id=inspection_id,
            assemblyId=request.assemblyId,
            disposition=request.disposition,
            defects=request.defects,
        )
        complete_idempotency(
            db=db,
            tenant_id=auth_context.tenant_id,
            operation_id=INSPECT_UNIT_OPERATION_ID,
            key=idempotency_key,
            response_status=201,
            response_body=decision.model_dump(mode="json", by_alias=True),
        )
        # The deferred defect rule fires here, at COMMIT.
        db.commit()
        return decision
    except DBAPIError as exc:
        db.rollback()
        mapped = map_database_error(exc, instance)
        if mapped is None:
            raise
        raise mapped from exc
    except Exception:
        db.rollback()
        raise


def list_assemblies(
    db: Session,
    auth_context: AuthContext,
    status_filter: Optional[str] = None,
    instance: str = "/api/v1/assemblies",
) -> AssemblyPage:
    """The QC queue: this tenant's assemblies, newest first, each with its allocated pieces."""
    statement = select(GarmentAssembly).where(
        GarmentAssembly.tenant_id == auth_context.tenant_id
    )
    if status_filter is not None:
        statement = statement.where(GarmentAssembly.status == status_filter)
    statement = statement.order_by(GarmentAssembly.created_at.desc(), GarmentAssembly.id)

    assemblies = db.execute(statement).scalars().all()
    allocated: Dict[uuid.UUID, List[uuid.UUID]] = {}
    if assemblies:
        allocation_rows = db.execute(
            select(AssemblyComponent.assembly_id, AssemblyComponent.garment_unit_id)
            .where(
                AssemblyComponent.tenant_id == auth_context.tenant_id,
                AssemblyComponent.assembly_id.in_([row.id for row in assemblies]),
            )
            .order_by(AssemblyComponent.allocated_at, AssemblyComponent.garment_unit_id)
        ).all()
        for assembly_id, garment_unit_id in allocation_rows:
            allocated.setdefault(assembly_id, []).append(garment_unit_id)

    return AssemblyPage(
        items=[
            Assembly(
                id=row.id,
                orderId=row.order_id,
                serialCode=row.serial_code,
                componentUnitIds=allocated.get(row.id, []),
                status=row.status,
            )
            for row in assemblies
        ]
    )
