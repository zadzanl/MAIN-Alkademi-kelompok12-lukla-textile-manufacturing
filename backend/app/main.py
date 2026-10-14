import logging
import uuid
from typing import List
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from fastapi.openapi.utils import get_openapi
from .api.v1 import api_router
from .schemas.problem import Problem, Violation, ProblemException, ProblemCode

logger = logging.getLogger("lukla.security.audit")
logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Lukla Operations Engine API",
    version="1.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json"
)

@app.middleware("http")
async def request_id_and_security_audit_middleware(request: Request, call_next):
    # Derive or assign request ID
    incoming_req_id = request.headers.get("X-Request-Id")
    try:
        req_id = uuid.UUID(incoming_req_id) if incoming_req_id else uuid.uuid4()
    except (ValueError, TypeError):
        req_id = uuid.uuid4()

    request.state.request_id = req_id

    response = await call_next(request)
    response.headers["X-Request-Id"] = str(req_id)
    return response

@app.exception_handler(ProblemException)
async def problem_exception_handler(request: Request, exc: ProblemException):
    req_id = getattr(request.state, "request_id", exc.request_id)
    problem = Problem(
        type=exc.type_,
        title=exc.title,
        status=exc.status,
        code=exc.code,
        detail=exc.detail,
        instance=exc.instance or request.url.path,
        requestId=req_id,
        violations=exc.violations
    )

    # Emit sanitized security audit log outside the aborted transaction
    logger.warning(
        f"Security/Business Invariant Rejected: request_id={req_id} path={request.url.path} "
        f"status={exc.status} code={exc.code} detail='{exc.detail}'"
    )

    return JSONResponse(
        status_code=exc.status,
        content=problem.model_dump(mode="json", by_alias=True, exclude_none=True),
        media_type="application/problem+json"
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    req_id = getattr(request.state, "request_id", uuid.uuid4())
    violations: List[Violation] = []
    for err in exc.errors():
        loc = " -> ".join(str(l) for l in err.get("loc", []))
        msg = err.get("msg", "Invalid value")
        violations.append(Violation(field=loc, message=msg))

    detail_str = "; ".join(f"{v.field}: {v.message}" for v in violations) or "Validation failed"

    # Map validation errors to 400 for ledger operations per OpenAPI spec line 145
    status_code = status.HTTP_400_BAD_REQUEST

    problem = Problem(
        type="about:blank",
        title="Validation Error",
        status=status_code,
        code="VALIDATION_ERROR",
        detail=detail_str,
        instance=request.url.path,
        requestId=req_id,
        violations=violations
    )

    logger.warning(f"Request validation failure: request_id={req_id} detail='{detail_str}'")

    return JSONResponse(
        status_code=status_code,
        content=problem.model_dump(mode="json", by_alias=True, exclude_none=True),
        media_type="application/problem+json"
    )

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    req_id = getattr(request.state, "request_id", uuid.uuid4())
    code_map: dict[int, ProblemCode] = {
        400: "VALIDATION_ERROR",
        401: "AUTH_REQUIRED",
        403: "FORBIDDEN",
        404: "VALIDATION_ERROR",
        405: "VALIDATION_ERROR",
        409: "INVALID_STATE",
        422: "VALIDATION_ERROR"
    }
    code: ProblemCode = code_map.get(exc.status_code, "VALIDATION_ERROR")

    problem = Problem(
        type="about:blank",
        title=exc.detail if isinstance(exc.detail, str) else "HTTP Exception",
        status=exc.status_code,
        code=code,
        detail=str(exc.detail),
        instance=request.url.path,
        requestId=req_id
    )

    logger.warning(f"HTTP Exception: request_id={req_id} status={exc.status_code} detail='{exc.detail}'")

    return JSONResponse(
        status_code=exc.status_code,
        content=problem.model_dump(mode="json", by_alias=True, exclude_none=True),
        media_type="application/problem+json"
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    req_id = getattr(request.state, "request_id", uuid.uuid4())
    # Log full traceback internally, but never expose DB details to client
    logger.error(f"Unhandled server error: request_id={req_id} exception={str(exc)}", exc_info=True)

    problem = Problem(
        type="about:blank",
        title="Internal Server Error",
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        code="VALIDATION_ERROR",
        detail="An internal server error occurred while processing the request",
        instance=request.url.path,
        requestId=req_id
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=problem.model_dump(mode="json", by_alias=True, exclude_none=True),
        media_type="application/problem+json"
    )

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Lukla Operations Engine API",
        version="1.0.0",
        description="Immutable Double-Entry Core API",
        routes=app.routes,
    )

    # Security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }
    openapi_schema["security"] = [{"bearerAuth": []}]

    # Ensure Problem and Violation schemas exist
    openapi_schema["components"]["schemas"]["Problem"] = Problem.model_json_schema()
    openapi_schema["components"]["schemas"]["Violation"] = Violation.model_json_schema()

    # Clean endpoints and parameters
    for path, methods in openapi_schema.get("paths", {}).items():
        for method, op in methods.items():
            if not isinstance(op, dict):
                continue
            if "parameters" in op:
                op["parameters"] = [
                    p for p in op["parameters"]
                    if p.get("name", "").lower() != "authorization"
                ]
            responses = op.get("responses", {})
            responses.pop("422", None)
            responses["401"] = {
                "description": "Authentication required",
                "content": {
                    "application/problem+json": {
                        "schema": {"$ref": "#/components/schemas/Problem"}
                    }
                }
            }
            responses["403"] = {
                "description": "Forbidden",
                "content": {
                    "application/problem+json": {
                        "schema": {"$ref": "#/components/schemas/Problem"}
                    }
                }
            }
            if method.lower() == "post":
                responses["400"] = {
                    "description": "Validation error",
                    "content": {
                        "application/problem+json": {
                            "schema": {"$ref": "#/components/schemas/Problem"}
                        }
                    }
                }
                responses["409"] = {
                    "description": "Conflict or invalid state",
                    "content": {
                        "application/problem+json": {
                            "schema": {"$ref": "#/components/schemas/Problem"}
                        }
                    }
                }
                if "{transactionId}" in path:
                    responses["404"] = {
                        "description": "Not found",
                        "content": {
                            "application/problem+json": {
                                "schema": {"$ref": "#/components/schemas/Problem"}
                            }
                        }
                    }

    openapi_schema["components"]["schemas"].pop("HTTPValidationError", None)

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
app.include_router(api_router)
