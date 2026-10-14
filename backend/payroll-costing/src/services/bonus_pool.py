"""Quality bonus pool: accrual sum and the three-way split.

The pool is the sum of the per-assembly accruals the quality routine records on
the first pass of each assembly (``qc_bonus_accruals`` is unique per assembly),
so this module never re-derives the rate; it consolidates what was already
accrued under an approved rule version.

The split is where the engine must refuse rather than round. The remainder
destination is unresolved (OQ-4) and every alternative is forbidden: a floored
payout, a reserve account, a fourth recipient, and a hidden loss rule are all
explicitly disallowed, and BRD section 13.2 forbids directing the remainder to a
named account. So a pool that is not divisible by three raises
``FINANCIAL_RULE_PENDING`` and pays nobody. AT-08 is therefore a blocked test by
design, not a failing one.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from uuid import UUID

from src.models.bonus_pool import BonusPool, BonusPoolStatus, BonusRecipient
from src.models.financial_rule import RemainderPolicy
from src.models.money import Money
from src.services.errors import FinancialRulePending, ValidationFailed
from src.services.rule_gate import RuleReference, require_approved
from src.utils.money_math import split_equal

SHARES = 3


@dataclass(frozen=True, slots=True)
class BonusAccrual:
    """One assembly's accrued bonus, as the quality routine recorded it."""

    assembly_id: UUID
    amount_minor: int
    currency: str


def _consolidate(accruals: Sequence[BonusAccrual], *, currency: str) -> int:
    """Sum the accruals of distinct assemblies, refusing anything unusable."""
    seen: set[UUID] = set()
    total = 0

    for accrual in accruals:
        if accrual.assembly_id in seen:
            raise ValidationFailed(f"Assembly {accrual.assembly_id} accrued a bonus more than once")
        seen.add(accrual.assembly_id)
        if accrual.currency != currency:
            raise ValidationFailed(
                f"Assembly {accrual.assembly_id} accrued in {accrual.currency}, not {currency}"
            )
        if accrual.amount_minor < 0:
            raise ValidationFailed(f"Assembly {accrual.assembly_id} accrued a negative bonus")
        total += accrual.amount_minor

    return total


def _assert_recipients(recipient_ids: Sequence[UUID]) -> None:
    if len(recipient_ids) != SHARES:
        raise ValidationFailed(f"The bonus pool is shared by exactly {SHARES} recipients")
    if len(set(recipient_ids)) != SHARES:
        raise ValidationFailed("Bonus recipients must be distinct")


def calculate_bonus_pool(
    *,
    period_id: UUID,
    required_rules: Sequence[RuleReference],
    accruals: Sequence[BonusAccrual],
    recipient_ids: Sequence[UUID],
    remainder_policy: RemainderPolicy,
    currency: str,
) -> BonusPool:
    """Gate, consolidate, then split three ways or refuse.

    The rule gate runs first, so an unapproved rule blocks the pool before any
    accrual is read. ``recipient_ids`` come from the approved rule version, which
    is where the recipient identity decision (OQ-3) belongs.
    """
    require_approved(required_rules)
    _assert_recipients(recipient_ids)

    pool_minor = _consolidate(accruals, currency=currency)
    share, remainder = split_equal(pool_minor, SHARES)

    if remainder:
        if remainder_policy is RemainderPolicy.RESERVE_PROPOSED:
            raise FinancialRulePending(
                "Remainder destination is unresolved: BRD section 13.2 forbids directing the "
                "quality bonus remainder to a named account"
            )
        raise FinancialRulePending(
            f"The quality bonus pool of {pool_minor} {currency} is not divisible by {SHARES}; "
            "the remainder destination is unresolved (OQ-4) and floored payouts, a reserve "
            "account, a fourth recipient, and a hidden loss rule are all forbidden"
        )

    status = BonusPoolStatus.CALCULATED if pool_minor else BonusPoolStatus.NO_OUTPUT
    return BonusPool(
        period_id=period_id,
        pool=Money(amount_minor=pool_minor, currency=currency),
        recipients=[
            BonusRecipient(
                recipient_id=recipient_id, amount=Money(amount_minor=share, currency=currency)
            )
            for recipient_id in recipient_ids
        ],
        status=status,
    )
