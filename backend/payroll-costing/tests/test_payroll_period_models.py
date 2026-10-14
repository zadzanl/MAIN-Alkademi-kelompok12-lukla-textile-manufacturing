"""Period requests must accept exactly the window the frozen contract describes."""

from typing import Any
from uuid import UUID

import pytest
from pydantic import ValidationError

from src.models.payroll_period import Period, PeriodPage, PeriodRequest


def test_camel_case_payload_round_trips(period_payload: dict[str, Any]) -> None:
    request = PeriodRequest.model_validate(period_payload)

    assert request.cutoff_local == "12:00:00"
    assert request.model_dump(mode="json", by_alias=True) == period_payload


def test_unknown_property_is_rejected(period_payload: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        PeriodRequest.model_validate(dict(period_payload, status="APPROVED"))


def test_timezone_is_fixed_to_the_factory_timezone(period_payload: dict[str, Any]) -> None:
    assert PeriodRequest.model_validate(period_payload).timezone == "Asia/Jakarta"

    with pytest.raises(ValidationError):
        PeriodRequest.model_validate(dict(period_payload, timezone="UTC"))


@pytest.mark.parametrize("cutoff", ["00:00:00", "12:00:00", "23:59:00"])
def test_cutoff_accepts_whole_minutes(period_payload: dict[str, Any], cutoff: str) -> None:
    assert (
        PeriodRequest.model_validate(dict(period_payload, cutoffLocal=cutoff)).cutoff_local
        == cutoff
    )


@pytest.mark.parametrize("cutoff", ["24:00:00", "9:00:00", "12:00", "12:00:01", "12:60:00", ""])
def test_cutoff_rejects_anything_else(period_payload: dict[str, Any], cutoff: str) -> None:
    with pytest.raises(ValidationError):
        PeriodRequest.model_validate(dict(period_payload, cutoffLocal=cutoff))


def test_period_requires_an_id_and_the_page_wraps_periods(period_payload: dict[str, Any]) -> None:
    period = Period.model_validate(dict(period_payload, id="77777777-7777-4777-8777-777777777777"))

    assert isinstance(period.id, UUID)
    assert [item.id for item in PeriodPage(items=[period]).items] == [period.id]
