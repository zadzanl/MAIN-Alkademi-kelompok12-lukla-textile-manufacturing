"""Integer minor-unit arithmetic for money.

No floating point and no rounding policy live here. Where a split is not exact
the remainder is returned to the caller, never allocated: the bonus remainder
rule (OQ-4) is unresolved and BRD section 13.2 forbids directing it to a named
account. The caller must block, not guess.
"""


def split_equal(amount_minor: int, shares: int) -> tuple[int, int]:
    """Return ``(share, remainder)`` for an equal split of ``amount_minor``.

    ``amount_minor = shares * share + remainder`` always holds, so a caller can
    detect a non-divisible pool and refuse it rather than losing or hiding money.
    """
    if shares < 1:
        raise ValueError("shares must be at least 1")
    if amount_minor < 0:
        raise ValueError("amount_minor must not be negative")
    share, remainder = divmod(amount_minor, shares)
    return share, remainder
