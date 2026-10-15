"""Repair routing: the defect-linked pieces return to their existing operator.

The operator is read from the assembly's immutable allocation, never from the
caller. ``research/blueprint-boundaries-001.md`` FR-8.2 proposed a caller-supplied
``original_operator_id``; ``11-database-schema-spec.md`` §2 and §6 supersede it
with "repair operator derived from immutable component source, not supplied by
caller", and the frozen ``Defect`` schema has no such field to carry it.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from uuid import UUID

from src.models.money import Money
from src.models.qc import Defect
from src.services.errors import DuplicateRepairCredit, ValidationFailed


@dataclass(frozen=True, slots=True)
class ComponentAllocation:
    """One component piece inside an assembly, as ``assembly_components`` records it."""

    unit_id: UUID
    component_code: str
    operator_id: UUID
    piece_rate_snapshot_id: UUID
    piece_rate: Money


@dataclass(frozen=True, slots=True)
class RepairRoute:
    """A defect-linked piece and the operator who already sewed it."""

    unit_id: UUID
    component_code: str
    operator_id: UUID
    defect_code: str


def index_allocations(
    allocations: Sequence[ComponentAllocation],
) -> dict[UUID, ComponentAllocation]:
    """Index an assembly's pieces by unit, refusing a piece allocated twice."""
    index: dict[UUID, ComponentAllocation] = {}
    for allocation in allocations:
        if allocation.unit_id in index:
            raise DuplicateRepairCredit(
                f"Component piece {allocation.unit_id} is allocated to the assembly more than "
                "once; a unit earns at most one piece-rate credit"
            )
        index[allocation.unit_id] = allocation
    return index


def resolve_defect_pieces(
    defects: Sequence[Defect], allocations: Sequence[ComponentAllocation]
) -> tuple[ComponentAllocation, ...]:
    """Resolve each defect to its allocated piece, in the order the defects were given.

    Refuses a defect on a piece that is not part of the inspected assembly and a
    piece that carries more than one defect in the same inspection.
    """
    index = index_allocations(allocations)
    resolved: list[ComponentAllocation] = []
    seen: set[UUID] = set()

    for defect in defects:
        allocation = index.get(defect.component_unit_id)
        if allocation is None:
            raise ValidationFailed(
                f"Defect component {defect.component_unit_id} is not allocated to this assembly"
            )
        if defect.component_unit_id in seen:
            raise ValidationFailed(
                f"Component piece {defect.component_unit_id} carries more than one defect in "
                "the same inspection"
            )
        seen.add(defect.component_unit_id)
        resolved.append(allocation)

    return tuple(resolved)


def route_repair(
    defects: Sequence[Defect], allocations: Sequence[ComponentAllocation]
) -> tuple[RepairRoute, ...]:
    """Route every defect of a repair back to the piece's original operator."""
    pieces = resolve_defect_pieces(defects, allocations)
    return tuple(
        RepairRoute(
            unit_id=piece.unit_id,
            component_code=piece.component_code,
            operator_id=piece.operator_id,
            defect_code=defect.code,
        )
        for piece, defect in zip(pieces, defects, strict=True)
    )
