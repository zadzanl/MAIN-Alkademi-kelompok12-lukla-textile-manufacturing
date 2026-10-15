"""The taxonomy is configuration, and a rule version is unusable until approved."""

from uuid import UUID

import pytest

from src.models.bonus_rule import BonusRule, RuleStatus
from src.models.money import Money
from src.models.taxonomy import DefectTaxonomy

RULE_VERSION_ID = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")


def test_a_taxonomy_needs_at_least_one_code() -> None:
    with pytest.raises(ValueError, match="at least one code"):
        DefectTaxonomy.from_codes([])


@pytest.mark.parametrize("code", ["", "  ", " puckering"])
def test_blank_and_untrimmed_codes_are_refused(code: str) -> None:
    with pytest.raises(ValueError, match="non-blank"):
        DefectTaxonomy.from_codes([code])


def test_membership_is_exact() -> None:
    taxonomy = DefectTaxonomy.from_codes(["puckering", "broken stitch"])

    assert taxonomy.contains("puckering") is True
    assert taxonomy.contains("Puckering") is False
    assert taxonomy.known_codes() == ("broken stitch", "puckering")


def test_an_approved_rule_carries_its_rate() -> None:
    rule = BonusRule.approved(
        rule_version="2026-W41-v1",
        rule_version_id=RULE_VERSION_ID,
        bonus_rate=Money(amount_minor=7, currency="IDR"),
    )

    assert rule.is_approved is True
    assert rule.bonus_rate is not None
    assert rule.bonus_rate.amount_minor == 7


def test_a_pending_rule_carries_no_rate() -> None:
    rule = BonusRule.pending(rule_version="2026-W42-draft")

    assert rule.status is RuleStatus.PENDING
    assert rule.is_approved is False
    assert rule.bonus_rate is None


def test_an_approved_rule_without_a_rate_is_refused() -> None:
    with pytest.raises(ValueError, match="must carry its per-pass bonus rate"):
        BonusRule(
            rule_version="2026-W41-v1",
            rule_version_id=RULE_VERSION_ID,
            status=RuleStatus.APPROVED,
            bonus_rate=None,
        )


def test_a_pending_rule_with_a_rate_is_refused() -> None:
    with pytest.raises(ValueError, match="must not carry a rate"):
        BonusRule(
            rule_version="2026-W42-draft",
            rule_version_id=None,
            status=RuleStatus.PENDING,
            bonus_rate=Money(amount_minor=7, currency="IDR"),
        )
