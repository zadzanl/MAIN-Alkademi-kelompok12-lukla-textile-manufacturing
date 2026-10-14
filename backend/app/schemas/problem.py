from pydantic import BaseModel, Field
from typing import List, Optional, Literal
import uuid

ProblemCode = Literal[
    "AUTH_REQUIRED",
    "FORBIDDEN",
    "TENANT_CONTEXT_MISSING",
    "LEGAL_OWNER_MISMATCH",
    "ORDER_BENEFICIARY_MISMATCH",
    "IDEMPOTENCY_CONFLICT",
    "INVALID_STATE",
    "LEDGER_IMMUTABLE",
    "DUPLICATE_REPAIR_CREDIT",
    "FINANCIAL_RULE_PENDING",
    "VALIDATION_ERROR",
    "INSUFFICIENT_STOCK",
    "OVER_CONSUMPTION",
    "SERVICE_SCOPE_REQUIRED",
]

class Violation(BaseModel):
    field: str
    message: str

class Problem(BaseModel):
    type: str = "about:blank"
    title: str
    status: int
    code: ProblemCode
    detail: str
    instance: str
    requestId: uuid.UUID = Field(default_factory=uuid.uuid4)
    violations: Optional[List[Violation]] = None

class ProblemException(Exception):
    def __init__(
        self,
        status: int,
        code: str,
        detail: str,
        title: Optional[str] = None,
        type_: str = "about:blank",
        violations: Optional[List[Violation]] = None,
        instance: Optional[str] = None,
        request_id: Optional[uuid.UUID] = None,
    ):
        super().__init__(detail)
        self.status = status
        self.code = code
        self.detail = detail
        self.title = title or self._default_title(status)
        self.type_ = type_
        self.violations = violations
        self.instance = instance or ""
        self.request_id = request_id or uuid.uuid4()

    @staticmethod
    def _default_title(status: int) -> str:
        titles = {
            400: "Bad Request",
            401: "Unauthorized",
            403: "Forbidden",
            404: "Not Found",
            409: "Conflict",
            422: "Unprocessable Entity",
            500: "Internal Server Error"
        }
        return titles.get(status, "Error")
