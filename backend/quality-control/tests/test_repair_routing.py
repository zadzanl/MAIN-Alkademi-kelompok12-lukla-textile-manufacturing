"""Repair routing reads the operator from the allocation, never from the caller."""

from uuid import NAMESPACE_OID, UUID, uuid5

import pytest

from src.models.money import Money
from src.models.problem import ErrorCode
from src.models.qc import Defect
from src.services.errors import DuplicateRepairCredit, ValidationFailed
from src.services.routing import (
    ComponentAllocation,
    index_allocations,
    resolve_defect_pieces,
    route_repair,
)

CURRENCY = "IDR"
S1 = UUID("11111111-1111-4111-8111-111111111111")
S2 = UUID("22222222-2222-4222-8222-222222222222")


def allocation(index: int, operator_id: UUID) -> ComponentAllocation:
    return ComponentAllocation(
        unit_id=uuid5(NAMESPACE_OID, f"piece-{index}"),
        component_code=f"COMP-{index}",
        operator_id=operator_id,
        piece_rate_snapshot_id=uuid5(NAMESPACE_OID, f"snapshot-{index}"),
        piece_rate=Money(amount_minor=2_000, currency=CURRENCY),
    )


def test_route_names_the_operator_who_sewed_the_piece() -> None:
    pieces = [allocation(0, S1), allocation(1, S2)]

    routes = route_repair([Defect(component_unit_id=pieces[1].unit_id, code="puckering")], pieces)

    assert len(routes) == 1
    assert routes[0].operator_id == S2
    assert routes[0].unit_id == pieces[1].unit_id
    assert routes[0].component_code == "COMP-1"
    assert routes[0].defect_code == "puckering"


def test_a_piece_allocated_twice_would_credit_twice() -> None:
    piece = allocation(0, S1)

    with pytest.raises(DuplicateRepairCredit) as exc:
        index_allocations([piece, piece])

    assert exc.value.code is ErrorCode.DUPLICATE_REPAIR_CREDIT


def test_a_defect_on_a_foreign_piece_is_refused() -> None:
    with pytest.raises(ValidationFailed) as exc:
        route_repair(
            [Defect(component_unit_id=allocation(9, S1).unit_id, code="puckering")],
            [allocation(0, S1)],
        )

    assert exc.value.code is ErrorCode.VALIDATION_ERROR


def test_resolving_keeps_the_order_the_defects_were_given() -> None:
    pieces = [allocation(0, S1), allocation(1, S2)]

    resolved = resolve_defect_pieces(
        [
            Defect(component_unit_id=pieces[1].unit_id, code="uneven seam"),
            Defect(component_unit_id=pieces[0].unit_id, code="broken stitch"),
        ],
        pieces,
    )

    assert [piece.unit_id for piece in resolved] == [pieces[1].unit_id, pieces[0].unit_id]
