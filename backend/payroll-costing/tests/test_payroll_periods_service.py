"""The period lifecycle: only sourced transitions are reachable."""

from typing import Any
from uuid import UUID

import pytest

from src.models.payroll_period import PayrollPeriodStatus, PeriodRequest
from src.models.problem import ErrorCode
from src.services.errors import InvalidState, ValidationFailed
from src.services.payroll_periods import (
    assert_transition_allowed,
    assert_valid_period_range,
    create_period,
)

PERIOD_ID = UUID("77777777-7777-4777-8777-777777777777")

OPEN = PayrollPeriodStatus.OPEN
CALCULATED = PayrollPeriodStatus.CALCULATED
PENDING_RULE = PayrollPeriodStatus.PENDING_RULE
APPROVED = PayrollPeriodStatus.APPROVED
PAID = PayrollPeriodStatus.PAID
REVERSED = PayrollPeriodStatus.REVERSED

# The complete reachable set, written out so that editing the table without a
# source breaks this test rather than passing silently.
REACHABLE = {
    (OPEN, CALCULATED),
    (OPEN, PENDING_RULE),
    (PENDING_RULE, CALCULATED),
    (PENDING_RULE, PENDING_RULE),
    (CALCULATED, CALCULATED),
    (CALCULATED, PENDING_RULE),
    (CALCULATED, APPROVED),
    (APPROVED, PAID),
    (PAID, REVERSED),
}


def test_create_period_opens_the_window_it_was_given(period_request: PeriodRequest) -> None:
    period = create_period(period_request, PERIOD_ID)

    assert period.id == PERIOD_ID
    assert period.model_dump(exclude={"id"}) == period_request.model_dump()


@pytest.mark.parametrize("ends_on", ["2026-10-11", "2026-10-04"])
def test_a_period_must_cover_at_least_one_day(period_payload: dict[str, Any], ends_on: str) -> None:
    empty_or_reversed = PeriodRequest.model_validate(dict(period_payload, endsOn=ends_on))

    with pytest.raises(ValidationFailed) as raised:
        assert_valid_period_range(empty_or_reversed)

    assert raised.value.code is ErrorCode.VALIDATION_ERROR


@pytest.mark.parametrize(("current", "target"), sorted(REACHABLE, key=lambda pair: pair[0].value))
def test_every_reachable_transition_is_allowed(
    current: PayrollPeriodStatus, target: PayrollPeriodStatus
) -> None:
    assert_transition_allowed(current, target)


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (OPEN, APPROVED),
        (OPEN, PAID),
        (OPEN, REVERSED),
        (PENDING_RULE, APPROVED),
        (PENDING_RULE, PAID),
        (CALCULATED, OPEN),
        (CALCULATED, PAID),
        (APPROVED, OPEN),
        (APPROVED, CALCULATED),
        (APPROVED, APPROVED),
        (PAID, OPEN),
        (PAID, CALCULATED),
        (PAID, APPROVED),
        (REVERSED, OPEN),
        (REVERSED, PAID),
        (REVERSED, REVERSED),
    ],
)
def test_unsourced_transitions_are_refused(
    current: PayrollPeriodStatus, target: PayrollPeriodStatus
) -> None:
    with pytest.raises(InvalidState) as raised:
        assert_transition_allowed(current, target)

    assert raised.value.code is ErrorCode.INVALID_STATE


def test_the_reachable_set_is_exactly_what_the_table_allows() -> None:
    refused = {
        (current, target)
        for current in PayrollPeriodStatus
        for target in PayrollPeriodStatus
        if (current, target) not in REACHABLE
    }

    assert len(REACHABLE) + len(refused) == len(PayrollPeriodStatus) ** 2
    for current, target in refused:
        with pytest.raises(InvalidState):
            assert_transition_allowed(current, target)
