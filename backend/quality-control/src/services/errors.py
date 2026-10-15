"""Domain errors that the API layer maps to contract ``Problem`` documents."""

from src.models.problem import ErrorCode


class DomainError(Exception):
    """An error carrying the contract error code the API layer must return."""

    code: ErrorCode

    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail


class ValidationFailed(DomainError):
    """The request is well-formed but violates a domain invariant."""

    code = ErrorCode.VALIDATION_ERROR


class InvalidState(DomainError):
    """The requested transition is not reachable from the current assembly state."""

    code = ErrorCode.INVALID_STATE


class IdempotencyConflict(DomainError):
    """An idempotency key was reused for a different payload."""

    code = ErrorCode.IDEMPOTENCY_CONFLICT


class DuplicateRepairCredit(DomainError):
    """One component piece would earn more than one piece-rate credit."""

    code = ErrorCode.DUPLICATE_REPAIR_CREDIT
