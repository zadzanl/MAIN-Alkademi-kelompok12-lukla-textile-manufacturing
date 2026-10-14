"""Weekly borongan wages, traced to the frozen acceptance tests."""

from uuid import NAMESPACE_OID, UUID, uuid5

import pytest

from src.models.financial_rule import RuleStatus
from src.models.garment_unit import GarmentUnitStatus
from src.models.payroll_calculation import PayrollResultStatus
from src.models.problem import ErrorCode
from src.services.errors import DuplicateRepairCredit, FinancialRulePending, ValidationFailed
from src.services.rule_gate import RuleReference
from src.services.wage_calculation import (
    EligibleUnit,
    WageTotal,
    calculate_borongan,
    calculate_weekly_payroll,
)

RATE_MINOR = 2000
CURRENCY = "IDR"
PERIOD_ID = UUID("77777777-7777-4777-8777-777777777777")
APPROVED_RULE = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
PENDING_RULE = UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")

QC_PASS = GarmentUnitStatus.QC_PASS

# AT-03: two sewers from Monday, five added on Thursday, one article and one rate.
OPERATOR_UNIT_COUNTS = {"S1": 4, "S2": 6, "S3": 2, "S4": 3, "S5": 4, "S6": 5, "S7": 6}
EXPECTED_PER_OPERATOR_MINOR = {
    "S1": 8_000,
    "S2": 12_000,
    "S3": 4_000,
    "S4": 6_000,
    "S5": 8_000,
    "S6": 10_000,
    "S7": 12_000,
}


def operator_id(label: str) -> UUID:
    return uuid5(NAMESPACE_OID, f"operator-{label}")


def unit(
    operator: str,
    index: int,
    *,
    status: GarmentUnitStatus = QC_PASS,
    currency: str = CURRENCY,
    rate_minor: int = RATE_MINOR,
) -> EligibleUnit:
    return EligibleUnit(
        unit_id=uuid5(NAMESPACE_OID, f"{operator}-unit-{index}"),
        operator_id=operator_id(operator),
        component_code="SLEEVE",
        rate_minor=rate_minor,
        currency=currency,
        status=status,
    )


def weekly_pool() -> list[EligibleUnit]:
    return [
        unit(label, index)
        for label, count in OPERATOR_UNIT_COUNTS.items()
        for index in range(count)
    ]


def test_at_03_seven_sewers_earn_their_verified_piece_rates() -> None:
    totals = calculate_borongan(weekly_pool(), currency=CURRENCY)

    assert totals.eligible_units == 30
    assert totals.total_minor == 60_000
    assert dict(totals.by_operator) == {
        operator_id(label): amount for label, amount in EXPECTED_PER_OPERATOR_MINOR.items()
    }


def test_at_03_the_headcount_is_not_capped_or_restarted() -> None:
    totals = calculate_borongan(weekly_pool(), currency=CURRENCY)

    assert len(totals.by_operator) == 7


@pytest.mark.parametrize(
    "status",
    [
        GarmentUnitStatus.MENUNGGU_QC,
        GarmentUnitStatus.REWORK,
        GarmentUnitStatus.REJECT_SCRAP,
        GarmentUnitStatus.ASSEMBLED,
    ],
)
def test_at_04_units_that_have_not_passed_quality_earn_nothing(
    status: GarmentUnitStatus,
) -> None:
    totals = calculate_borongan([unit("S8", 0, status=status)], currency=CURRENCY)

    assert totals == WageTotal(eligible_units=0, total_minor=0, currency=CURRENCY, by_operator={})


def test_at_04_ineligible_units_do_not_disturb_the_eligible_pool() -> None:
    totals = calculate_borongan(
        [unit("S1", 0), unit("S2", 0, status=GarmentUnitStatus.MENUNGGU_QC, currency="USD")],
        currency=CURRENCY,
    )

    assert totals.total_minor == RATE_MINOR


def test_at_05_one_credit_per_repaired_unit() -> None:
    totals = calculate_borongan([unit("S1", 0)], currency=CURRENCY)

    assert totals.total_minor == RATE_MINOR


def test_at_05_a_unit_cannot_be_credited_twice() -> None:
    repaired = unit("S1", 0)

    with pytest.raises(DuplicateRepairCredit) as raised:
        calculate_borongan([repaired, repaired], currency=CURRENCY)

    assert raised.value.code is ErrorCode.DUPLICATE_REPAIR_CREDIT


def test_a_unit_in_another_currency_is_refused() -> None:
    with pytest.raises(ValidationFailed) as raised:
        calculate_borongan([unit("S1", 0, currency="USD")], currency=CURRENCY)

    assert raised.value.code is ErrorCode.VALIDATION_ERROR


def test_a_negative_rate_is_refused() -> None:
    with pytest.raises(ValidationFailed):
        calculate_borongan([unit("S1", 0, rate_minor=-1)], currency=CURRENCY)


def test_a_cleared_calculation_returns_a_denominated_preview() -> None:
    result = calculate_weekly_payroll(
        period_id=PERIOD_ID,
        required_rules=[RuleReference(rule_id=APPROVED_RULE, status=RuleStatus.APPROVED)],
        units=[unit("S1", 0), unit("S1", 1)],
        currency=CURRENCY,
    )

    assert result.period_id == PERIOD_ID
    assert result.status is PayrollResultStatus.CALCULATED
    assert result.eligible_units == 2
    assert result.total_wages.amount_minor == 4_000
    assert result.total_wages.currency == CURRENCY


def test_zero_output_is_a_valid_zero_preview() -> None:
    result = calculate_weekly_payroll(
        period_id=PERIOD_ID,
        required_rules=[RuleReference(rule_id=APPROVED_RULE, status=RuleStatus.APPROVED)],
        units=[],
        currency=CURRENCY,
    )

    assert result.status is PayrollResultStatus.NO_OUTPUT
    assert result.eligible_units == 0
    assert result.total_wages.amount_minor == 0
    assert result.total_wages.currency == CURRENCY


def test_a_pending_rule_blocks_the_calculation() -> None:
    with pytest.raises(FinancialRulePending) as raised:
        calculate_weekly_payroll(
            period_id=PERIOD_ID,
            required_rules=[RuleReference(rule_id=PENDING_RULE, status=RuleStatus.PENDING)],
            units=weekly_pool(),
            currency=CURRENCY,
        )

    assert raised.value.code is ErrorCode.FINANCIAL_RULE_PENDING


def test_the_gate_runs_before_the_pool_is_even_inspected() -> None:
    # The pool below would raise DuplicateRepairCredit on its own; the gate must win.
    with pytest.raises(FinancialRulePending):
        calculate_weekly_payroll(
            period_id=PERIOD_ID,
            required_rules=[RuleReference(rule_id=PENDING_RULE, status=RuleStatus.PENDING)],
            units=[unit("S1", 0), unit("S1", 0)],
            currency=CURRENCY,
        )
