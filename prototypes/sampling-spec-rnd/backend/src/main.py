"""
Main FastAPI Application
Sampling & Spec R&D Module
"""

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api.auth_routes import create_auth_router
from .api.routes import create_api_router
from .services.ops_store import OpsStore
from .services.ops_store import SnapshotError
from .services.seed import _get_storage_path
from pathlib import Path
import os

# Load environment variables from .env file
load_dotenv()

_data_dir = Path(__file__).resolve().parents[1] / "data"


def create_app(db_path: str | None = None) -> FastAPI:
    app = FastAPI(title="Sampling & Spec R&D API",
                  description="Time Study Recording and Specification Version Tracking",
                  version="1.0.0")
    app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3009", "http://127.0.0.1:3009"],
                       allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
    @app.exception_handler(SnapshotError)
    async def _snapshot_error_handler(request, exc: SnapshotError):
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=422, content={"detail": str(exc)})
    selected_db = db_path or os.getenv("OPS_DB_PATH", str(_data_dir / "ops.db"))
    store = OpsStore(selected_db)
    # Import legacy sample JSON only when SQLite is empty; SQLite is authoritative afterward.
    store.import_seed_once(_get_storage_path())
    app.include_router(create_api_router(store=store))
    app.include_router(create_auth_router())
    return app


app = create_app()

# Mount Lukla Intelligence Copilot router so port 8009 can also serve /api/v1/copilot/chat directly
_copilot_identity = None
try:
    import sys
    import types
    from pathlib import Path
    from fastapi import Request
    from fastapi.responses import JSONResponse
    _repo_root = str(Path(__file__).resolve().parents[4])
    _stashed_src = {k: sys.modules.pop(k) for k in list(sys.modules.keys()) if k == "src" or k.startswith("src.")}
    _old_path = list(sys.path)
    if _repo_root not in sys.path:
        sys.path.insert(0, _repo_root)
    _created_api_stub = "backend.app.api" not in sys.modules
    _created_v1_stub = "backend.app.api.v1" not in sys.modules
    try:
        # Pre-seed lightweight package namespace stubs for backend.app.api and backend.app.api.v1
        # so importing backend.app.api.v1.copilot does not execute backend/app/api/v1/__init__.py
        # (which otherwise pulls in ledger/payroll/sqlalchemy/postgres at import time).
        _api_dir = Path(_repo_root) / "backend" / "app" / "api"
        _v1_dir = _api_dir / "v1"
        if _created_api_stub:
            _api_pkg = types.ModuleType("backend.app.api")
            _api_pkg.__path__ = [str(_api_dir)]
            sys.modules["backend.app.api"] = _api_pkg
        if _created_v1_stub:
            _v1_pkg = types.ModuleType("backend.app.api.v1")
            _v1_pkg.__path__ = [str(_v1_dir)]
            sys.modules["backend.app.api.v1"] = _v1_pkg

        from backend.app.api.v1.copilot import router as copilot_v1_router
        from backend.app.copilot.identity import copilot_identity as _copilot_identity
        from backend.app.schemas.problem import Problem, ProblemException

        @app.exception_handler(ProblemException)
        async def _copilot_problem_handler(request: Request, exc: ProblemException):
            problem = Problem(
                type=exc.type_,
                title=exc.title,
                status=exc.status,
                code=exc.code,
                detail=exc.detail,
                instance=exc.instance or request.url.path,
                requestId=exc.request_id,
                violations=exc.violations,
            )
            return JSONResponse(
                status_code=exc.status,
                content=problem.model_dump(mode="json", by_alias=True, exclude_none=True),
                media_type="application/problem+json",
            )

        app.include_router(copilot_v1_router, prefix="/api/v1")
    finally:
        if _created_v1_stub:
            sys.modules.pop("backend.app.api.v1", None)
        if _created_api_stub:
            sys.modules.pop("backend.app.api", None)
        sys.path[:] = _old_path
        if _repo_root not in sys.path:
            sys.path.append(_repo_root)
        sys.modules.update(_stashed_src)
except Exception as _exc:
    print(f"[WARN] Could not mount copilot router on sampling backend: {_exc}")


@app.middleware("http")
async def _copilot_identity_middleware(request: Request, call_next):
    """Resolve the Copilot caller role from the authenticated session.

    Only the two chat POST routes are gated. The HTML GET pages, the root
    ``backend/app`` mount, and the Telegram adapter keep their current behaviour.
    """
    if request.method == "POST" and request.url.path in (
        "/api/v1/copilot/chat",
        "/api/v1/copilot/demo/chat",
    ):
        if _copilot_identity is None:
            return JSONResponse(
                status_code=503,
                content={"detail": "Copilot authorization is unavailable."},
            )
        try:
            _copilot_identity(request, request.headers.get("Authorization"))
        except HTTPException as exc:
            return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    return await call_next(request)


# Health check endpoint (at root level for backward compatibility).
# The /api/sampling-spec-rnd/health route is provided by the API router.
@app.get("/health")
def health_check() -> dict[str, str]:
    """Health check endpoint"""
    return {"status": "healthy", "service": "sampling-spec-rnd-api"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8009, reload=True)
