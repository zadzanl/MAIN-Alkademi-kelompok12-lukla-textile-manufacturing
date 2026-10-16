"""
Main FastAPI Application
Sampling & Spec R&D Module
"""

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.auth_routes import create_auth_router
from .api.routes import create_api_router

# Load environment variables from .env file
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="Sampling & Spec R&D API",
    description="Time Study Recording and Specification Version Tracking",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3009",
        "http://127.0.0.1:3009",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
router = create_api_router()
app.include_router(router)

# Portal authentication router (register/login/change/forgot password)
app.include_router(create_auth_router())

# Mount Lukla Intelligence Copilot router so port 8009 can also serve /api/v1/copilot/chat directly
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


# Health check endpoint (at root level for backward compatibility).
# The /api/sampling-spec-rnd/health route is provided by the API router.
@app.get("/health")
def health_check() -> dict[str, str]:
    """Health check endpoint"""
    return {"status": "healthy", "service": "sampling-spec-rnd-api"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8009, reload=True)
