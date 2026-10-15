# UHUY B2B — Portal Klien Eksternal (External Client Portal)

A **separate** client-facing application from the internal Sampling & Spec R&D dashboard.
Maklon clients ("Klien Maklon/Ext", RBAC role #8) register, log in, submit order/sample
requests, track their own order progress, and see their own consigned (titipan) material.

> This is the **external** portal. It is visually and configurationally marked
> (`PORTAL EKSTERNAL`, indigo accent, `VITE_PORTAL_SCOPE=external`) and runs on its own
> backend/port, so it can never be confused with the internal app.

## Ports & isolation

| App | Backend | Frontend |
|---|---|---|
| Internal Sampling & Spec R&D | 8009 | 3009 |
| **External UHUY B2B portal** | **8010** | **3010** |

All client data is filtered server-side by the session's `client_id`; the `client_id` is
never read from the request. A client asking for another client's record gets `404`.

## Structure

```text
prototypes/uhuy-b2b-portal/
├── backend/     # FastAPI "portal eksternal" API (port 8010)
│   ├── src/api/portal_auth_routes.py   # client register/login/change/forgot + admin approval
│   ├── src/api/portal_routes.py        # client-scoped summary/orders/stock/requests
│   ├── src/services/portal_store.py    # in-memory, client-scoped store
│   ├── src/services/seed.py            # demo admin + clients A/B with data
│   └── tests/                          # auth lifecycle + client_id isolation
└── frontend/    # React + Vite + Tailwind (port 3010), Apple-inspired tokens
    ├── src/pages/                      # login, dashboard, orders, requests, stock, settings
    ├── src/components/PortalBadge.tsx  # the EXTERNAL marker
    └── tests/                          # pure validation/search rules
```

## Run it (fresh machine, top-to-bottom)

### 1. Backend (port 8010)

```powershell
cd prototypes/uhuy-b2b-portal/backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements-dev.txt
uvicorn src.main:app --reload --port 8010
```

**Did it work?** Open <http://localhost:8010/api/portal/health> → `{"status":"healthy","module":"uhuy-b2b-portal","scope":"external"}`.
API docs at <http://localhost:8010/docs>.

### 2. Frontend (port 3010)

```powershell
cd prototypes/uhuy-b2b-portal/frontend
npm install
npm run dev
```

**Did it work?** Open <http://localhost:3010> → the login page shows the **PORTAL EKSTERNAL** badge.

### 3. Demo logins

| Role | Email | Password |
|---|---|---|
| Client A — Nusantara Apparel | `klien.a@uhuy.local` | `Klien#12345` |
| Client B — Bumi Tekstil | `klien.b@uhuy.local` | `Klien#12345` |
| Internal approver (admin) | `admin@uhuy.local` | `Admin#12345` |

Log in as **Client A** → Dashboard shows only A's orders; try A's own data vs Client B to see
the isolation. Register a new client, then approve it via `POST /api/portal/auth/admin/clients/{id}/approve`
using the admin token.

## Verify

```powershell
# Backend (from backend/, venv active)
pytest -q; ruff check .; mypy src

# Frontend (from frontend/)
npm run type-check; npm run lint; npm test; npm run build

# Workspace hygiene (from repo root)
python scripts/check_workspace_hygiene.py
```

## Known ceiling

Prototype only: in-memory store (resets on restart), `sessionStorage` token, no persistence.
See `openspec/changes/uhuy-b2b-portal/design.md` for the upgrade path.
