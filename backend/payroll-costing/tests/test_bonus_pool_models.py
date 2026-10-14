"""The bonus pool response must always carry exactly three shares."""

from typing import Any

import pytest
from pydantic import ValidationError

from src.models.bonus_pool import BonusPool, BonusPoolStatus

RECIPIENTS = [
    {
        "recipientId": "11111111-1111-4111-8111-111111111111",
        "amount": {"amountMinor": 7000, "currency": "IDR"},
    },
    {
        "recipientId": "22222222-2222-4222-8222-222222222222",
        "amount": {"amountMinor": 7000, "currency": "IDR"},
    },
    {
        "recipientId": "33333333-3333-4333-8333-333333333333",
        "amount": {"amountMinor": 7000, "currency": "IDR"},
    },
]


def pool_payload() -> dict[str, Any]:
    return {
        "periodId": "77777777-7777-4777-8777-777777777777",
        "pool": {"amountMinor": 21000, "currency": "IDR"},
        "recipients": RECIPIENTS,
        "status": "CALCULATED",
    }


def test_bonus_pool_round_trips() -> None:
    pool = BonusPool.model_validate(pool_payload())

    assert pool.status is BonusPoolStatus.CALCULATED
    assert [share.amount.amount_minor for share in pool.recipients] == [7000, 7000, 7000]
    assert pool.model_dump(mode="json", by_alias=True) == pool_payload()


@pytest.mark.parametrize("count", [0, 2, 4])
def test_the_recipient_count_is_fixed_at_three(count: int) -> None:
    recipients = (RECIPIENTS * 2)[:count]

    with pytest.raises(ValidationError):
        BonusPool.model_validate(dict(pool_payload(), recipients=recipients))


def test_unknown_properties_and_statuses_are_rejected() -> None:
    with pytest.raises(ValidationError):
        BonusPool.model_validate(dict(pool_payload(), disbursed=True))

    with pytest.raises(ValidationError):
        BonusPool.model_validate(dict(pool_payload(), status="PAID"))
