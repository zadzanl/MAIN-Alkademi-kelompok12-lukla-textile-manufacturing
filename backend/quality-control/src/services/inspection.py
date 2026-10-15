"""Assembly classification: the QC disposition state machine and its money boundary.

One call classifies one finished assembly. It records the disposition, moves the
assembly, and — on the first ``PASS`` only — produces the eligibility event, one
wage credit per allocated piece, and one bonus accrual, all in the shapes
``11-database-schema-spec.md`` §4 gives those tables. The caller persists the
result in one transaction; this module decides policy, not storage.

Two rules are structural rather than checked:

* ``PASS`` and ``REJECT`` are terminal, so at most one inspection can ever pass
  an assembly, so a repaired unit cannot be credited twice (AT-05).
* A pending rule version produces the eligibility event and no amount at all,
  because a value written under an unapproved rule is a wage that was never
  authorized.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from src.models.bonus_rule import BonusRule
from src.models.money import Money
from src.models.qc import (
    DEFECT_REQUIRED_DISPOSITIONS,
    DISPOSITION_STATUS,
    INSPECTABLE_STATUSES,
    TERMINAL_STATUSES,
    AssemblyStatus,
    Defect,
    Disposition,
    QcInspection,
    QcRequest,
)
from src.models.taxonomy import DefectTaxonomy
from src.services.errors import IdempotencyConflict, InvalidState, ValidationFailed
from src.services.routing import (
    ComponentAllocation,
    RepairRoute,
    resolve_defect_pieces,
    route_repair,
)


@dataclass(frozen=True, slots=True)
class InspectionRecord:
    """A stored, append-only ``qc_inspections`` row."""

    id: UUID
    sequence_no: int
    disposition: Disposition
    defects: tuple[Defect, ...]
    idempotency_key: str
    inspector_id: UUID


@dataclass(frozen=True, slots=True)
class AssemblySnapshot:
    """The assembly being inspected: its status, its pieces, and its history."""

    assembly_id: UUID
    status: AssemblyStatus
    allocations: tuple[ComponentAllocation, ...]
    inspections: tuple[InspectionRecord, ...]


@dataclass(frozen=True, slots=True)
class EligibilityEvent:
    """An ``eligibility_events`` row: the unvalued claim a first pass creates."""

    assembly_id: UUID
    passed_at: datetime
    rule_version_id: UUID | None


@dataclass(frozen=True, slots=True)
class WageCredit:
    """A ``wage_credits`` row for one allocated component piece."""

    unit_id: UUID
    operator_id: UUID
    amount_minor: int
    currency: str
    piece_rate_snapshot_id: UUID


@dataclass(frozen=True, slots=True)
class BonusAccrual:
    """A ``qc_bonus_accruals`` row: one per assembly, never one per piece."""

    assembly_id: UUID
    amount_minor: int
    currency: str
    rule_version: str


@dataclass(frozen=True, slots=True)
class ClassificationResult:
    """What the caller must persist for one classification, atomically.

    On a replay the side-effect fields are empty by design: the first delivery
    already produced them and a second delivery must not produce them again.
    """

    inspection: QcInspection
    sequence_no: int
    assembly_status: AssemblyStatus
    repair_routes: tuple[RepairRoute, ...]
    eligibility: EligibilityEvent | None
    wage_credits: tuple[WageCredit, ...]
    bonus_accrual: BonusAccrual | None
    replayed: bool


def _fingerprint(disposition: Disposition, defects: Sequence[Defect]) -> tuple[object, ...]:
    """A payload comparison that ignores defect ordering but nothing else."""
    return (
        disposition.value,
        tuple(
            sorted(
                (str(defect.component_unit_id), defect.code, defect.notes or "")
                for defect in defects
            )
        ),
    )


def _find_replay(
    assembly: AssemblySnapshot, request: QcRequest, idempotency_key: str
) -> InspectionRecord | None:
    """Return the stored inspection for this key, or refuse a reused key."""
    wanted = _fingerprint(request.disposition, request.defects)

    for record in assembly.inspections:
        if record.idempotency_key != idempotency_key:
            continue
        if _fingerprint(record.disposition, record.defects) != wanted:
            raise IdempotencyConflict(
                f"Idempotency key {idempotency_key} is already recorded for assembly "
                f"{assembly.assembly_id} with a different disposition or defect list"
            )
        return record

    return None


def _require_inspectable(assembly: AssemblySnapshot) -> None:
    if assembly.status in TERMINAL_STATUSES:
        raise InvalidState(
            f"Assembly {assembly.assembly_id} is {assembly.status.value}; a final pass or reject "
            "cannot be overridden in this release"
        )
    if assembly.status not in INSPECTABLE_STATUSES:
        raise InvalidState(
            f"Assembly {assembly.assembly_id} is {assembly.status.value}; only an assembly "
            "awaiting inspection or in rework can be inspected"
        )


def _require_defects(request: QcRequest, taxonomy: DefectTaxonomy) -> None:
    if request.disposition not in DEFECT_REQUIRED_DISPOSITIONS:
        if request.defects:
            raise ValidationFailed(
                f"A {request.disposition.value} disposition must not carry a defect; the BRD "
                "requires a defect category only for repair and reject"
            )
        return

    if not request.defects:
        raise ValidationFailed(
            f"A {request.disposition.value} disposition must select a defect category"
        )

    unknown = sorted(
        {defect.code for defect in request.defects if not taxonomy.contains(defect.code)}
    )
    if unknown:
        raise ValidationFailed(
            f"Unknown defect code(s) {unknown}; this tenant's taxonomy holds "
            f"{list(taxonomy.known_codes())}"
        )


def _first_pass_valuation(
    *,
    assembly: AssemblySnapshot,
    rule: BonusRule,
    now: datetime,
    disposition: Disposition,
) -> tuple[EligibilityEvent | None, tuple[WageCredit, ...], BonusAccrual | None]:
    """The money boundary: a first pass claims eligibility, and only an approved rule values it."""
    if disposition is not Disposition.PASS:
        return None, (), None

    # PASS is terminal, so no stored record can already carry it through the state
    # machine. The check stays because it is what makes "credited once" structural:
    # a snapshot that somehow already passed earns nothing a second time.
    if any(record.disposition is Disposition.PASS for record in assembly.inspections):
        return None, (), None

    eligibility = EligibilityEvent(
        assembly_id=assembly.assembly_id,
        passed_at=now,
        rule_version_id=rule.rule_version_id,
    )

    if not rule.is_approved or rule.bonus_rate is None:
        return eligibility, (), None

    rate: Money = rule.bonus_rate
    credits = tuple(
        WageCredit(
            unit_id=allocation.unit_id,
            operator_id=allocation.operator_id,
            amount_minor=allocation.piece_rate.amount_minor,
            currency=allocation.piece_rate.currency,
            piece_rate_snapshot_id=allocation.piece_rate_snapshot_id,
        )
        for allocation in assembly.allocations
    )
    accrual = BonusAccrual(
        assembly_id=assembly.assembly_id,
        amount_minor=rate.amount_minor,
        currency=rate.currency,
        rule_version=rule.rule_version,
    )
    return eligibility, credits, accrual


def classify_assembly(
    *,
    assembly: AssemblySnapshot,
    request: QcRequest,
    inspection_id: UUID,
    inspector_id: UUID,
    idempotency_key: str,
    taxonomy: DefectTaxonomy,
    rule: BonusRule,
    now: datetime,
) -> ClassificationResult:
    """Classify one assembly, idempotently, and return everything to persist."""
    if request.assembly_id != assembly.assembly_id:
        raise ValidationFailed(
            f"Inspection targets assembly {request.assembly_id} but assembly "
            f"{assembly.assembly_id} was loaded"
        )
    if not idempotency_key:
        raise ValidationFailed("An inspection must carry an idempotency key")

    # Idempotency is resolved before the state check, because the retried delivery of
    # the request that produced a final PASS or REJECT arrives at a terminal assembly.
    replay = _find_replay(assembly, request, idempotency_key)
    if replay is not None:
        return ClassificationResult(
            inspection=QcInspection(
                id=replay.id,
                assembly_id=assembly.assembly_id,
                disposition=replay.disposition,
                defects=list(replay.defects),
            ),
            sequence_no=replay.sequence_no,
            assembly_status=assembly.status,
            repair_routes=(),
            eligibility=None,
            wage_credits=(),
            bonus_accrual=None,
            replayed=True,
        )

    _require_inspectable(assembly)

    if not assembly.allocations:
        raise ValidationFailed("An assembly with no allocated component piece cannot be inspected")

    _require_defects(request, taxonomy)

    repair_routes: tuple[RepairRoute, ...] = ()
    if request.disposition is Disposition.REPAIR:
        repair_routes = route_repair(request.defects, assembly.allocations)
    elif request.disposition is Disposition.REJECT:
        # A reject is scrapped rather than routed back, so the pieces are validated
        # without producing a route: a defect on a foreign piece is still refused.
        resolve_defect_pieces(request.defects, assembly.allocations)

    eligibility, wage_credits, bonus_accrual = _first_pass_valuation(
        assembly=assembly, rule=rule, now=now, disposition=request.disposition
    )

    return ClassificationResult(
        inspection=QcInspection(
            id=inspection_id,
            assembly_id=assembly.assembly_id,
            disposition=request.disposition,
            defects=request.defects,
        ),
        sequence_no=max((record.sequence_no for record in assembly.inspections), default=0) + 1,
        assembly_status=DISPOSITION_STATUS[request.disposition],
        repair_routes=repair_routes,
        eligibility=eligibility,
        wage_credits=wage_credits,
        bonus_accrual=bonus_accrual,
        replayed=False,
    )
