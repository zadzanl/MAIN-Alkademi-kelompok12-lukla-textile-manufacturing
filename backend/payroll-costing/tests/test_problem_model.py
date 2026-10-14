"""Every error response the engine returns must fit the contract Problem shape."""

from uuid import UUID

import pytest
from pydantic import ValidationError

from src.models.problem import ErrorCode, Problem, Violation

REQUEST_ID = "99999999-9999-4999-8999-999999999999"


def problem_payload() -> dict[str, object]:
    return {
        "type": "about:blank",
        "title": "Financial rule pending",
        "status": 409,
        "code": "FINANCIAL_RULE_PENDING",
        "detail": "Rule version bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb is not approved",
        "instance": "/api/v1/payroll/weekly/period-1",
        "requestId": REQUEST_ID,
    }


def test_problem_round_trips_by_alias() -> None:
    problem = Problem.model_validate(problem_payload())

    assert problem.code is ErrorCode.FINANCIAL_RULE_PENDING
    assert isinstance(problem.request_id, UUID)
    assert problem.violations is None
    assert problem.model_dump(mode="json", by_alias=True, exclude_none=True) == problem_payload()


@pytest.mark.parametrize("status", [200, 399, 600])
def test_problem_status_must_be_an_error_status(status: int) -> None:
    with pytest.raises(ValidationError):
        Problem.model_validate(dict(problem_payload(), status=status))


def test_problem_rejects_an_unknown_error_code() -> None:
    with pytest.raises(ValidationError):
        Problem.model_validate(dict(problem_payload(), code="SOMETHING_ELSE"))


def test_violations_carry_field_and_message() -> None:
    problem = Problem.model_validate(
        dict(
            problem_payload(),
            violations=[{"field": "mealBasisPoints", "message": "must be 1000-1500"}],
        )
    )

    assert problem.violations == [Violation(field="mealBasisPoints", message="must be 1000-1500")]

    with pytest.raises(ValidationError):
        Problem.model_validate(dict(problem_payload(), violations=[{"field": "mealBasisPoints"}]))
