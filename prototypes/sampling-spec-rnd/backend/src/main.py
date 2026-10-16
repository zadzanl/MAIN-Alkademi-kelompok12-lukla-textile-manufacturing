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
    from pathlib import Path
    _repo_root = str(Path(__file__).resolve().parents[4])
    _stashed_src = {k: sys.modules.pop(k) for k in list(sys.modules.keys()) if k == "src" or k.startswith("src.")}
    _old_path = list(sys.path)
    if _repo_root not in sys.path:
        sys.path.insert(0, _repo_root)
    try:
        from backend.app.api.v1.copilot import router as copilot_v1_router
        app.include_router(copilot_v1_router, prefix="/api/v1")
    finally:
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
