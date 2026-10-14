"""Equal splits must expose a remainder instead of hiding or allocating it."""

import pytest

from src.utils.money_math import split_equal


def test_at_06_bonus_pool_divides_exactly() -> None:
    # 3,000 passed units at Rp 7 per piece, split across three recipients.
    assert split_equal(21_000, 3) == (7_000, 0)


def test_at_08_non_divisible_pool_reports_the_remainder() -> None:
    # Rp 100,000 across three recipients: Rp 33,333 each with Rp 1 left over.
    # The remainder is returned, never allocated; OQ-4 is unresolved.
    assert split_equal(100_000, 3) == (33_333, 1)


@pytest.mark.parametrize(
    ("amount_minor", "shares"),
    [(0, 1), (1, 1), (999, 7), (60_000, 1), (123_457, 13)],
)
def test_share_and_remainder_reconstruct_the_amount(amount_minor: int, shares: int) -> None:
    share, remainder = split_equal(amount_minor, shares)

    assert share * shares + remainder == amount_minor
    assert 0 <= remainder < shares


@pytest.mark.parametrize(("amount_minor", "shares"), [(100, 0), (100, -1), (-1, 3)])
def test_impossible_splits_are_rejected(amount_minor: int, shares: int) -> None:
    with pytest.raises(ValueError):
        split_equal(amount_minor, shares)
