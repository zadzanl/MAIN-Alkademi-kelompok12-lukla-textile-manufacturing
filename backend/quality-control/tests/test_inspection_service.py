"""Assembly classification: the state machine, the defect rules, and the money boundary."""

from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import NAMESPACE_OID, UUID, uuid5

import pytest

from src.models.bonus_rule import BonusRule
from src.models.money import Money
from src.models.problem import ErrorCode
from src.models.qc import AssemblyStatus, Defect, Disposition, QcRequest
from src.models.taxonomy import DefectTaxonomy
from src.services.errors import IdempotencyConflict, InvalidState, ValidationFailed
from src.services.inspection import (
    AssemblySnapshot,
    ClassificationResult,
    InspectionRecord,
    classify_assembly,
)
from src.services.routing import ComponentAllocation

CURRENCY = "IDR"
ASSEMBLY_ID = UUID("55555555-5555-4555-8555-555555555555")
OTHER_ASSEMBLY_ID = UUID("66666666-6666-4666-8666-666666666666")
INSPECTOR_ID = UUID("77777777-7777-4777-8777-777777777777")
RULE_VERSION_ID = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
NOW = datetime(2026, 10, 15, 9, 30, tzinfo=UTC)

# The BRD's three named defects are examples for a fixture taxonomy, not a code
# list this module ships: the taxonomy arrives as configuration.
TAXONOMY = DefectTaxonomy.from_codes(["broken stitch", "puckering", "uneven seam"])
PIECE_RATE_MINOR = 2_000  # AT-05's illustrative component rate
BONUS_RATE_MINOR = 7  # AT-06's illustrative per-pass bonus rate

APPROVED_RULE = BonusRule.approved(
    rule_version="2026-W41-v1",
    rule_version_id=RULE_VERSION_ID,
    bonus_rate=Money(amount_minor=BONUS_RATE_MINOR, currency=CURRENCY),
)
PENDING_RULE = BonusRule.pending(rule_version="2026-W42-draft")


def piece(index: int) -> ComponentAllocation:
    return ComponentAllocation(
        unit_id=uuid5(NAMESPACE_OID, f"piece-{index}"),
        component_code=f"COMP-{index}",
        operator_id=uuid5(NAMESPACE_OID, f"operator-{index}"),
        piece_rate_snapshot_id=uuid5(NAMESPACE_OID, f"snapshot-{index}"),
        piece_rate=Money(amount_minor=PIECE_RATE_MINOR, currency=CURRENCY),
    )


def snapshot(
    *,
    status: AssemblyStatus = AssemblyStatus.MENUNGGU_QC,
    pieces: Sequence[ComponentAllocation] | None = None,
    inspections: Sequence[InspectionRecord] = (),
) -> AssemblySnapshot:
    return AssemblySnapshot(
        assembly_id=ASSEMBLY_ID,
        status=status,
        allocations=tuple(pieces) if pieces is not None else (piece(0),),
        inspections=tuple(inspections),
    )


def request(
    disposition: Disposition, defects: Sequence[Defect] = (), assembly_id: UUID = ASSEMBLY_ID
) -> QcRequest:
    return QcRequest(assembly_id=assembly_id, disposition=disposition, defects=list(defects))


def defect(component: ComponentAllocation, code: str = "broken stitch") -> Defect:
    return Defect(component_unit_id=component.unit_id, code=code)


def classify(
    *,
    assembly: AssemblySnapshot,
    body: QcRequest,
    rule: BonusRule = APPROVED_RULE,
    key: str = "key-1",
    taxonomy: DefectTaxonomy = TAXONOMY,
) -> ClassificationResult:
    return classify_assembly(
        assembly=assembly,
        request=body,
        inspection_id=uuid5(NAMESPACE_OID, f"inspection-{key}"),
        inspector_id=INSPECTOR_ID,
        idempotency_key=key,
        taxonomy=taxonomy,
        rule=rule,
        now=NOW,
    )


def stored(result: ClassificationResult, *, key: str = "key-1") -> InspectionRecord:
    return InspectionRecord(
        id=result.inspection.id,
        sequence_no=result.sequence_no,
        disposition=result.inspection.disposition,
        defects=tuple(result.inspection.defects),
        idempotency_key=key,
        inspector_id=INSPECTOR_ID,
    )


def test_pass_moves_the_assembly_to_a_terminal_state() -> None:
    result = classify(assembly=snapshot(), body=request(Disposition.PASS))

    assert result.inspection.disposition is Disposition.PASS
    assert result.assembly_status is AssemblyStatus.QC_PASS
    assert result.sequence_no == 1
    assert result.replayed is False
    assert result.repair_routes == ()


def test_first_pass_credits_each_piece_once_and_accrues_one_bonus() -> None:
    pieces = [piece(0), piece(1), piece(2)]
    result = classify(
        assembly=snapshot(pieces=pieces),
        body=request(Disposition.PASS),
    )

    assert [credit.unit_id for credit in result.wage_credits] == [p.unit_id for p in pieces]
    assert [credit.operator_id for credit in result.wage_credits] == [p.operator_id for p in pieces]
    assert all(credit.amount_minor == PIECE_RATE_MINOR for credit in result.wage_credits)
    assert all(credit.currency == CURRENCY for credit in result.wage_credits)

    assert result.bonus_accrual is not None
    assert result.bonus_accrual.assembly_id == ASSEMBLY_ID
    assert result.bonus_accrual.amount_minor == BONUS_RATE_MINOR
    assert result.bonus_accrual.rule_version == "2026-W41-v1"

    assert result.eligibility is not None
    assert result.eligibility.assembly_id == ASSEMBLY_ID
    assert result.eligibility.passed_at == NOW
    assert result.eligibility.rule_version_id == RULE_VERSION_ID


def test_pending_rule_records_the_disposition_unvalued() -> None:
    result = classify(
        assembly=snapshot(),
        body=request(Disposition.PASS),
        rule=PENDING_RULE,
    )

    assert result.assembly_status is AssemblyStatus.QC_PASS
    assert result.eligibility is not None
    assert result.eligibility.rule_version_id is None
    assert result.wage_credits == ()
    assert result.bonus_accrual is None


def test_repair_routes_to_the_original_operator_and_credits_nothing() -> None:
    pieces = [piece(0), piece(1)]
    result = classify(
        assembly=snapshot(pieces=pieces),
        body=request(Disposition.REPAIR, [defect(pieces[1], "puckering")]),
    )

    assert result.assembly_status is AssemblyStatus.REWORK
    assert len(result.repair_routes) == 1
    assert result.repair_routes[0].operator_id == pieces[1].operator_id
    assert result.repair_routes[0].component_code == pieces[1].component_code
    assert result.repair_routes[0].defect_code == "puckering"
    assert result.wage_credits == ()
    assert result.bonus_accrual is None
    assert result.eligibility is None


def test_reject_records_no_money_and_no_deduction() -> None:
    pieces = [piece(0), piece(1)]
    result = classify(
        assembly=snapshot(pieces=pieces),
        body=request(Disposition.REJECT, [defect(pieces[0])]),
    )

    assert result.assembly_status is AssemblyStatus.REJECT_SCRAP
    assert result.repair_routes == ()
    assert result.wage_credits == ()
    assert result.bonus_accrual is None
    assert result.eligibility is None


def test_rework_is_credited_once_in_total() -> None:
    """AT-05: a unit that comes back from repair does not earn a second credit."""
    pieces = [piece(0)]
    repaired = classify(
        assembly=snapshot(pieces=pieces),
        body=request(Disposition.REPAIR, [defect(pieces[0])]),
        key="repair-1",
    )

    passed = classify(
        assembly=snapshot(
            status=AssemblyStatus.REWORK,
            pieces=pieces,
            inspections=[stored(repaired, key="repair-1")],
        ),
        body=request(Disposition.PASS),
        key="pass-1",
    )

    assert passed.assembly_status is AssemblyStatus.QC_PASS
    assert passed.sequence_no == 2
    assert len(passed.wage_credits) == 1
    assert passed.wage_credits[0].amount_minor == PIECE_RATE_MINOR
    assert sum(credit.amount_minor for credit in passed.wage_credits) == PIECE_RATE_MINOR


def test_replay_is_served_before_the_terminal_check() -> None:
    pieces = [piece(0)]
    first = classify(assembly=snapshot(pieces=pieces), body=request(Disposition.PASS), key="k")
    terminal = snapshot(
        status=AssemblyStatus.QC_PASS, pieces=pieces, inspections=[stored(first, key="k")]
    )

    replayed = classify(assembly=terminal, body=request(Disposition.PASS), key="k")

    assert replayed.replayed is True
    assert replayed.inspection.id == first.inspection.id
    assert replayed.assembly_status is AssemblyStatus.QC_PASS
    assert replayed.wage_credits == ()
    assert replayed.bonus_accrual is None
    assert replayed.eligibility is None


def test_replay_ignores_defect_ordering() -> None:
    pieces = [piece(0), piece(1)]
    body = request(Disposition.REPAIR, [defect(pieces[0]), defect(pieces[1], "puckering")])
    first = classify(assembly=snapshot(pieces=pieces), body=body, key="k")

    reordered = request(Disposition.REPAIR, [defect(pieces[1], "puckering"), defect(pieces[0])])
    replayed = classify(
        assembly=snapshot(
            status=AssemblyStatus.REWORK, pieces=pieces, inspections=[stored(first, key="k")]
        ),
        body=reordered,
        key="k",
    )

    assert replayed.replayed is True
    assert replayed.inspection.id == first.inspection.id


def test_reused_key_with_a_different_payload_conflicts() -> None:
    pieces = [piece(0)]
    first = classify(
        assembly=snapshot(pieces=pieces),
        body=request(Disposition.REPAIR, [defect(pieces[0])]),
        key="k",
    )
    assembly = snapshot(
        status=AssemblyStatus.REWORK, pieces=pieces, inspections=[stored(first, key="k")]
    )

    with pytest.raises(IdempotencyConflict) as exc:
        classify(assembly=assembly, body=request(Disposition.PASS), key="k")

    assert exc.value.code is ErrorCode.IDEMPOTENCY_CONFLICT


@pytest.mark.parametrize("status", [AssemblyStatus.QC_PASS, AssemblyStatus.REJECT_SCRAP])
def test_a_terminal_disposition_cannot_be_overridden(status: AssemblyStatus) -> None:
    assembly = snapshot(status=status, inspections=[])

    with pytest.raises(InvalidState) as exc:
        classify(assembly=assembly, body=request(Disposition.PASS))

    assert exc.value.code is ErrorCode.INVALID_STATE


def test_an_assembly_still_assembling_cannot_be_inspected() -> None:
    with pytest.raises(InvalidState) as exc:
        classify(
            assembly=snapshot(status=AssemblyStatus.ASSEMBLING), body=request(Disposition.PASS)
        )

    assert exc.value.code is ErrorCode.INVALID_STATE


def test_an_assembly_without_pieces_cannot_be_inspected() -> None:
    with pytest.raises(ValidationFailed) as exc:
        classify(assembly=snapshot(pieces=[]), body=request(Disposition.PASS))

    assert exc.value.code is ErrorCode.VALIDATION_ERROR


def test_a_pass_must_not_carry_a_defect() -> None:
    pieces = [piece(0)]

    with pytest.raises(ValidationFailed) as exc:
        classify(
            assembly=snapshot(pieces=pieces), body=request(Disposition.PASS, [defect(pieces[0])])
        )

    assert exc.value.code is ErrorCode.VALIDATION_ERROR


@pytest.mark.parametrize("disposition", [Disposition.REPAIR, Disposition.REJECT])
def test_repair_and_reject_require_a_defect_category(disposition: Disposition) -> None:
    with pytest.raises(ValidationFailed) as exc:
        classify(assembly=snapshot(), body=request(disposition))

    assert exc.value.code is ErrorCode.VALIDATION_ERROR
    assert "defect category" in exc.value.detail


def test_an_unknown_defect_code_is_refused() -> None:
    pieces = [piece(0)]

    with pytest.raises(ValidationFailed) as exc:
        classify(
            assembly=snapshot(pieces=pieces),
            body=request(Disposition.REPAIR, [defect(pieces[0], "needle hole")]),
        )

    assert exc.value.code is ErrorCode.VALIDATION_ERROR
    assert "needle hole" in exc.value.detail


def test_a_defect_on_a_piece_outside_the_assembly_is_refused() -> None:
    with pytest.raises(ValidationFailed) as exc:
        classify(
            assembly=snapshot(pieces=[piece(0)]),
            body=request(Disposition.REPAIR, [defect(piece(9))]),
        )

    assert exc.value.code is ErrorCode.VALIDATION_ERROR


def test_a_piece_cannot_carry_two_defects_in_one_inspection() -> None:
    pieces = [piece(0)]

    with pytest.raises(ValidationFailed) as exc:
        classify(
            assembly=snapshot(pieces=pieces),
            body=request(Disposition.REPAIR, [defect(pieces[0]), defect(pieces[0], "puckering")]),
        )

    assert exc.value.code is ErrorCode.VALIDATION_ERROR


def test_a_request_for_another_assembly_is_refused() -> None:
    with pytest.raises(ValidationFailed) as exc:
        classify(assembly=snapshot(), body=request(Disposition.PASS, assembly_id=OTHER_ASSEMBLY_ID))

    assert exc.value.code is ErrorCode.VALIDATION_ERROR


def test_a_blank_idempotency_key_is_refused() -> None:
    with pytest.raises(ValidationFailed) as exc:
        classify(assembly=snapshot(), body=request(Disposition.PASS), key="")

    assert exc.value.code is ErrorCode.VALIDATION_ERROR
