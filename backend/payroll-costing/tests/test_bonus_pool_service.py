"""The quality bonus pool: three equal shares, or a refusal."""

from uuid import NAMESPACE_OID, UUID, uuid5

import pytest

from src.models.bonus_pool import BonusPool, BonusPoolStatus
from src.models.financial_rule import RemainderPolicy, RuleStatus
from src.models.problem import ErrorCode
from src.services.bonus_pool import BonusAccrual, calculate_bonus_pool
from src.services.errors import FinancialRulePending, ValidationFailed
from src.services.rule_gate import RuleReference

CURRENCY = "IDR"
PERIOD_ID = UUID("77777777-7777-4777-8777-777777777777")
APPROVED_RULE = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
PENDING_RULE = UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")

# AT-06: Mandor 1, Mandor 2, Kepala Operasional. These are people, not RBAC roles.
MANDOR_1 = UUID("11111111-1111-4111-8111-111111111111")
MANDOR_2 = UUID("22222222-2222-4222-8222-222222222222")
KEPALA_OPS = UUID("33333333-3333-4333-8333-333333333333")
RECIPIENTS = [MANDOR_1, MANDOR_2, KEPALA_OPS]

BLOCK = RemainderPolicy.BLOCK_NON_DIVISIBLE


def accruals(count: int, amount_minor: int) -> list[BonusAccrual]:
    """``count`` distinct assemblies, each accruing ``amount_minor``."""
    return [
        BonusAccrual(
            assembly_id=uuid5(NAMESPACE_OID, f"assembly-{index}"),
            amount_minor=amount_minor,
            currency=CURRENCY,
        )
        for index in range(count)
    ]


def calculate(
    *,
    pool_accruals: list[BonusAccrual],
    recipients: list[UUID] = RECIPIENTS,
    remainder_policy: RemainderPolicy = BLOCK,
    required_rules: list[RuleReference] | None = None,
) -> BonusPool:
    return calculate_bonus_pool(
        period_id=PERIOD_ID,
        required_rules=required_rules
        or [RuleReference(rule_id=APPROVED_RULE, status=RuleStatus.APPROVED)],
        accruals=pool_accruals,
        recipient_ids=recipients,
        remainder_policy=remainder_policy,
        currency=CURRENCY,
    )


def test_at_06_three_thousand_passed_units_split_three_ways() -> None:
    pool = calculate(pool_accruals=accruals(3_000, 7))

    assert pool.pool.amount_minor == 21_000
    assert pool.status is BonusPoolStatus.CALCULATED
    assert [share.recipient_id for share in pool.recipients] == RECIPIENTS
    assert [share.amount.amount_minor for share in pool.recipients] == [7_000, 7_000, 7_000]


def test_at_06_the_shares_reconstruct_the_pool_exactly() -> None:
    pool = calculate(pool_accruals=accruals(3_000, 7))

    assert sum(share.amount.amount_minor for share in pool.recipients) == pool.pool.amount_minor


def test_at_07_only_passed_units_accrue_and_recalculation_does_not_accumulate() -> None:
    # Two units passed at Rp 600 each; the repaired and rejected units accrued nothing.
    passed = accruals(2, 600)

    first = calculate(pool_accruals=passed)
    second = calculate(pool_accruals=passed)

    assert first.pool.amount_minor == 1_200
    assert second == first


def test_at_08_a_non_divisible_pool_pays_nobody() -> None:
    with pytest.raises(FinancialRulePending) as raised:
        calculate(pool_accruals=accruals(1, 100_000))

    assert raised.value.code is ErrorCode.FINANCIAL_RULE_PENDING
    assert "not divisible" in str(raised.value)


def test_at_08_a_reserve_destination_is_refused_even_as_a_policy() -> None:
    with pytest.raises(FinancialRulePending) as raised:
        calculate(
            pool_accruals=accruals(1, 100_000),
            remainder_policy=RemainderPolicy.RESERVE_PROPOSED,
        )

    assert raised.value.code is ErrorCode.FINANCIAL_RULE_PENDING
    assert "13.2" in str(raised.value)


def test_a_divisible_pool_is_not_affected_by_the_policy() -> None:
    pool = calculate(
        pool_accruals=accruals(1, 30_000),
        remainder_policy=RemainderPolicy.RESERVE_PROPOSED,
    )

    assert pool.pool.amount_minor == 30_000
    assert [share.amount.amount_minor for share in pool.recipients] == [10_000, 10_000, 10_000]


def test_a_week_without_passed_units_reports_no_output() -> None:
    pool = calculate(pool_accruals=[])

    assert pool.status is BonusPoolStatus.NO_OUTPUT
    assert pool.pool.amount_minor == 0
    assert len(pool.recipients) == 3


def test_the_gate_runs_before_the_accruals_are_read() -> None:
    duplicated = [*accruals(1, 700), *accruals(1, 700)]

    with pytest.raises(FinancialRulePending):
        calculate(
            pool_accruals=duplicated,
            required_rules=[RuleReference(rule_id=PENDING_RULE, status=RuleStatus.PENDING)],
        )


def test_an_assembly_cannot_accrue_twice() -> None:
    with pytest.raises(ValidationFailed) as raised:
        calculate(pool_accruals=[*accruals(1, 700), *accruals(1, 700)])

    assert raised.value.code is ErrorCode.VALIDATION_ERROR


def test_accruals_must_match_the_pool_currency_and_stay_non_negative() -> None:
    wrong_currency = BonusAccrual(
        assembly_id=uuid5(NAMESPACE_OID, "assembly-usd"), amount_minor=700, currency="USD"
    )

    with pytest.raises(ValidationFailed):
        calculate(pool_accruals=[wrong_currency])

    negative = BonusAccrual(
        assembly_id=uuid5(NAMESPACE_OID, "assembly-negative"), amount_minor=-1, currency=CURRENCY
    )

    with pytest.raises(ValidationFailed):
        calculate(pool_accruals=[negative])


@pytest.mark.parametrize(
    "recipients",
    [
        [MANDOR_1, MANDOR_2],
        [MANDOR_1, MANDOR_2, KEPALA_OPS, MANDOR_1],
        [MANDOR_1, MANDOR_1, MANDOR_1],
    ],
)
def test_the_pool_is_shared_by_three_distinct_recipients(recipients: list[UUID]) -> None:
    with pytest.raises(ValidationFailed):
        calculate(pool_accruals=accruals(1, 30_000), recipients=recipients)
