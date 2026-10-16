import logging
import uuid
from typing import List
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from .api.v1 import api_router
from .schemas.problem import Problem, Violation, ProblemException, ProblemCode
from .copilot.html import get_copilot_html

logger = logging.getLogger("lukla.security.audit")
logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Lukla Operations Engine API",
    version="1.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json"
)

# Enable CORS for local development & cross-origin mock UI testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

@app.get(
    "/copilot",
    response_class=HTMLResponse,
    include_in_schema=False
)
@app.get(
    "/copilot/",
    response_class=HTMLResponse,
    include_in_schema=False
)
async def get_copilot_page():
    return HTMLResponse(content=get_copilot_html(), status_code=status.HTTP_200_OK)

@app.get(
    "/copilot/demo",
    response_class=HTMLResponse,
    include_in_schema=False
)
@app.get(
    "/copilot/demo/",
    response_class=HTMLResponse,
    include_in_schema=False
)
async def get_copilot_demo_page():
    return HTMLResponse(
        content=get_copilot_html(
            endpoint_url="/api/v1/copilot/demo/chat",
            subtitle="Spare / Redundant Demo Endpoint"
        ),
        status_code=status.HTTP_200_OK
    )

@app.api_route(
    "/health",
    methods=["GET", "HEAD"],
    include_in_schema=False
)
async def health_check():
    return {"status": "OK", "service": "lukla-operations-engine"}

@app.get(
    "/ui",
    response_class=HTMLResponse,
    include_in_schema=False
)
async def get_dashboard_ui():
    import os
    mock_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "prototypes", "design-mocks", "lukla-ui-mock.html"
    )
    if os.path.exists(mock_path):
        with open(mock_path, "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content, status_code=status.HTTP_200_OK)
    return HTMLResponse(content="Dashboard mock not found", status_code=status.HTTP_404_NOT_FOUND)

def get_portal_html() -> str:
    return """<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Lukla Operations Engine & Intelligence</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-neutral-950 text-neutral-100 min-h-screen flex flex-col justify-between p-6 antialiased font-sans">
  <div class="max-w-4xl mx-auto w-full py-10">
    <div class="flex items-center justify-between border-b border-neutral-800 pb-6 mb-8">
      <div>
        <h1 class="text-2xl font-bold tracking-tight text-white flex items-center gap-3">
          Lukla Operations Engine
          <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-950 text-emerald-400 border border-emerald-800">
            🟢 Online · Port 80 (HTTP)
          </span>
        </h1>
        <p class="text-sm text-neutral-400 mt-1">Enterprise Garment Manufacturing ERP & Intelligence Platform</p>
      </div>
      <div class="text-right hidden sm:block">
        <span class="text-xs text-neutral-500 block">Deploy Target</span>
        <span class="text-xs font-mono text-neutral-300">AWS EC2 · us-east-1 Bedrock</span>
      </div>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
      <!-- AI Copilot Card -->
      <a href="/copilot" class="group block p-6 bg-neutral-900 border border-neutral-800 rounded-xl hover:border-indigo-500 transition-all hover:shadow-lg hover:shadow-indigo-500/10">
        <div class="flex items-center justify-between mb-3">
          <div class="w-10 h-10 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 text-lg">🤖</div>
          <span class="text-xs font-medium px-2 py-1 bg-indigo-950 text-indigo-300 rounded border border-indigo-800">Bedrock / Nova</span>
        </div>
        <h2 class="text-lg font-semibold text-white group-hover:text-indigo-400 transition-colors">Lukla Intelligence (AI Copilot)</h2>
        <p class="text-xs text-neutral-400 mt-2 leading-relaxed">
          Asisten AI interaktif dengan model Bedrock Nova/Claude. Terhubung ke data inventaris kain, status order, dan mutasi ledger.
        </p>
        <div class="mt-4 flex items-center text-xs font-medium text-indigo-400 group-hover:translate-x-1 transition-transform">
          Buka AI Copilot &rarr;
        </div>
      </a>

      <!-- Sampling & Spec R&D Frontend Card -->
      <a href="/sampling/" class="group block p-6 bg-neutral-900 border border-neutral-800 rounded-xl hover:border-cyan-500 transition-all hover:shadow-lg hover:shadow-cyan-500/10">
        <div class="flex items-center justify-between mb-3">
          <div class="w-10 h-10 rounded-lg bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400 text-lg">⏱️</div>
          <span class="text-xs font-medium px-2 py-1 bg-cyan-950 text-cyan-300 rounded border border-cyan-800">React 18 + Vite</span>
        </div>
        <h2 class="text-lg font-semibold text-white group-hover:text-cyan-400 transition-colors">Sampling & Spec R&D Portal</h2>
        <p class="text-xs text-neutral-400 mt-2 leading-relaxed">
          Modul frontend operasional untuk pencatatan Time Study siklus jahit, sampling statistik n&ge;30, dan versioning spesifikasi.
        </p>
        <div class="mt-4 flex items-center text-xs font-medium text-cyan-400 group-hover:translate-x-1 transition-transform">
          Buka Sampling Portal &rarr;
        </div>
      </a>

      <!-- UI Dashboard Mock -->
      <a href="/ui" class="group block p-6 bg-neutral-900 border border-neutral-800 rounded-xl hover:border-amber-500 transition-all hover:shadow-lg hover:shadow-amber-500/10">
        <div class="flex items-center justify-between mb-3">
          <div class="w-10 h-10 rounded-lg bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400 text-lg">📊</div>
          <span class="text-xs font-medium px-2 py-1 bg-amber-950 text-amber-300 rounded border border-amber-800">ERP Dashboard</span>
        </div>
        <h2 class="text-lg font-semibold text-white group-hover:text-amber-400 transition-colors">Lukla Operations Dashboard</h2>
        <p class="text-xs text-neutral-400 mt-2 leading-relaxed">
          Pratinjau antarmuka ERP manufaktur terintegrasi: modul Gudang, Cutting, Line Sewing, QC Inspection, dan Payroll.
        </p>
        <div class="mt-4 flex items-center text-xs font-medium text-amber-400 group-hover:translate-x-1 transition-transform">
          Buka Dashboard UI &rarr;
        </div>
      </a>

      <!-- API Documentation -->
      <a href="/docs" class="group block p-6 bg-neutral-900 border border-neutral-800 rounded-xl hover:border-emerald-500 transition-all hover:shadow-lg hover:shadow-emerald-500/10">
        <div class="flex items-center justify-between mb-3">
          <div class="w-10 h-10 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 text-lg">📑</div>
          <span class="text-xs font-medium px-2 py-1 bg-emerald-950 text-emerald-300 rounded border border-emerald-800">OpenAPI 3.1</span>
        </div>
        <h2 class="text-lg font-semibold text-white group-hover:text-emerald-400 transition-colors">Interactive API Docs</h2>
        <p class="text-xs text-neutral-400 mt-2 leading-relaxed">
          Swagger UI interaktif lengkap: 69+ endpoint operasi double-entry ledger, batching, QC inspection, dan sampling specs.
        </p>
        <div class="mt-4 flex items-center text-xs font-medium text-emerald-400 group-hover:translate-x-1 transition-transform">
          Buka Swagger Docs &rarr;
        </div>
      </a>
    </div>
  </div>

  <footer class="max-w-4xl mx-auto w-full pt-6 border-t border-neutral-850 text-center text-xs text-neutral-500">
    PT Lukla Textile Manufacturing &middot; Alkademi Hackathon Deployment
  </footer>
</body>
</html>"""

@app.api_route(
    "/",
    methods=["GET", "HEAD"],
    response_class=HTMLResponse,
    include_in_schema=False
)
async def get_root_portal():
    return HTMLResponse(content=get_portal_html(), status_code=status.HTTP_200_OK)

# ── Mount Sampling & Spec R&D Backend Routes ─────────────────────────────────
try:
    import sys
    from pathlib import Path
    _sampling_backend_dir = str(Path(__file__).resolve().parents[2] / "prototypes" / "sampling-spec-rnd" / "backend")
    # Stash any conflicting 'src.*' modules (e.g. from payroll-costing) during import
    _stashed_src = {k: sys.modules.pop(k) for k in list(sys.modules.keys()) if k == "src" or k.startswith("src.")}
    _old_path = list(sys.path)
    sys.path.insert(0, _sampling_backend_dir)
    try:
        from src.api.routes import create_api_router as create_sampling_router
        from src.api.auth_routes import create_auth_router
        app.include_router(create_sampling_router())
        app.include_router(create_auth_router())
    finally:
        sys.path[:] = _old_path
        sys.modules.update(_stashed_src)
except Exception as exc:
    logger.warning(f"Could not load sampling prototype routes: {exc}", exc_info=True)

# ── Mount Sampling & Spec R&D Static Frontend ────────────────────────────────
try:
    import os
    from fastapi.staticfiles import StaticFiles
    _dist_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "prototypes", "sampling-spec-rnd", "frontend", "dist"
    )
    if os.path.exists(_dist_path):
        app.mount("/sampling", StaticFiles(directory=_dist_path, html=True), name="sampling")
except Exception as exc:
    logger.warning(f"Could not mount static frontend at /sampling: {exc}")



