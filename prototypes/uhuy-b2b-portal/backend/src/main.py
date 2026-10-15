"""Main FastAPI application — UHUY B2B External Client Portal.

This is the EXTERNAL portal backend, separate from the internal
Sampling & Spec R&D backend. It serves client-scoped data only (see
``portal_routes.py``) plus external client authentication (``portal_auth_routes.py``).
"""

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.portal_auth_routes import create_portal_auth_router
from .api.portal_routes import create_portal_router
from .services.seed import seed_demo

load_dotenv()

app = FastAPI(
    title="UHUY B2B — Portal Eksternal API",
    description="External client portal: client-scoped orders, consigned stock, and requests.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3010",
        "http://127.0.0.1:3010",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(create_portal_router())
app.include_router(create_portal_auth_router())

# Deterministic demo fixtures (admin + two active clients with orders and stock).
seed_demo()


@app.get("/health")
def health_check() -> dict[str, str]:
    """Root health check (external portal)."""
    return {"status": "healthy", "service": "uhuy-b2b-portal-api"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8010, reload=True)
