"""Domain errors that the API layer maps to contract ``Problem`` documents."""

from src.models.problem import ErrorCode


class DomainError(Exception):
    """An error carrying the contract error code the API layer must return."""

    code: ErrorCode

    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail


class FinancialRulePending(DomainError):
    """A referenced rule version is not approved, so no monetary amount may be produced."""

    code = ErrorCode.FINANCIAL_RULE_PENDING


class Forbidden(DomainError):
    """The authenticated role does not hold the capability the operation requires."""

    code = ErrorCode.FORBIDDEN


class InvalidState(DomainError):
    """The requested transition is not reachable from the current state."""

    code = ErrorCode.INVALID_STATE


class ValidationFailed(DomainError):
    """The request is well-formed but violates a domain invariant."""

    code = ErrorCode.VALIDATION_ERROR
