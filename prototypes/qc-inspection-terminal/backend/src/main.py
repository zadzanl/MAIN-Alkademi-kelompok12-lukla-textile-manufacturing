"""QC Inspection Terminal backend (prototype).

In-memory FastAPI app. Port 8010 (different from sampling-spec-rnd's 8009).
"""

from __future__ import annotations

from typing import Dict

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import create_api_router

load_dotenv()

app = FastAPI(
    title="QC Inspection Terminal API",
    description=(
        "In-memory prototype. Mirrors contract operations inspectUnit, "
        "listAssemblies, getDashboard from "
        "openspec/changes/lukla-ops-engine-planning/contracts/openapi.yaml. "
        "NO production data — see src/utils/seed_fixtures.py."
    ),
    version="0.1.0-prototype",
)

# CORS allowlist mirrors sampling-spec-rnd shape but binds to QC ports.
# Sampling-spec-rnd prototype uses 3009/8009; QC prototype uses 3010/8010.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3010",
        "http://127.0.0.1:3010",
        "http://localhost:3009",   # sibling prototype allowed for parity
        "http://127.0.0.1:3009",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Same health endpoint at both paths as the sampling-spec-rnd reference.
@app.get("/health")
def health_root() -> Dict[str, str]:
    return {"status": "healthy", "module": "qc-inspection-terminal", "prototype": "true"}


# Module router mounted under /api/qc-inspection-terminal
app.include_router(create_api_router())


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8010, reload=True)
