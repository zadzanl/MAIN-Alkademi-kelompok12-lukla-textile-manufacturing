# Tasks: UHUY B2B External Client Portal

## 1. Backend (`prototypes/uhuy-b2b-portal/backend`)
- [x] 1.1 `services/portal_store.py` — client-scoped in-memory store; scrypt hashing; identifier index; orders/stock/requests.
- [x] 1.2 `services/emailer.py` — stdlib SMTP with `dev-log` fallback (reused).
- [x] 1.3 `services/seed.py` — admin + two demo clients (A/B) with orders and consigned stock.
- [x] 1.4 `api/portal_auth_routes.py` — register/login/logout/me/change/forgot/reset + admin approve/reject.
- [x] 1.5 `api/portal_routes.py` — summary/orders/stock/requests + order/sample request submission (client-scoped).
- [x] 1.6 `src/main.py` — app wiring, CORS (3010), seed; port 8010.
- [x] 1.7 Config: `pyproject.toml`, `requirements*.txt`, `.env.example`, `run_backend.bat`.
- [x] 1.8 Tests: `tests/test_portal_auth.py`, `tests/test_portal_scope.py`.

## 2. Frontend (`prototypes/uhuy-b2b-portal/frontend`)
- [x] 2.1 Config/services: `config.ts` (PORTAL_BASE + marker), `http.ts`, `query.ts`, `problem.ts`, `toast.ts`, `authSession.ts`, `authRules.ts`, `portalApi.ts`, `types/portal.ts`.
- [x] 2.2 Components: reuse Sidebar/Header/DataTable/StatusBadge/MetricCard/Modal/Toaster/ErrorBoundary; add `PortalBadge`; extend `StatusBadge`.
- [x] 2.3 External marker: indigo accent + ribbon + badge in `index.css`, `App.tsx`, login, sidebar.
- [x] 2.4 Pages: `PortalLoginView`, `PortalDashboardView`, `OrderTrackView`, `NewOrderRequestView`, `NewSampleRequestView`, `RequestsView`, `ConsignedStockView`, `PortalSettingsView`, shared `RequestForm`.
- [x] 2.5 Config: `package.json`, `vite.config.ts` (3010), `.env.example`, `index.html`, `favicon.svg`.
- [x] 2.6 Tests: `tests/portal-rules.test.ts` (+ reused `problem.test.ts`).

## 3. Verification
- [x] 3.1 Backend: `pytest -q` (23 passed), `ruff check`, `mypy src` — all clean.
- [x] 3.2 Frontend: `tsc --noEmit`, `eslint --max-warnings=0`, `node --test` (15 passed), `vite build` — all clean.
- [x] 3.3 Live smoke: server boot + `/health` + login (client A) + scoped summary/orders/stock + cross-client 404 + order request creation.

## 4. Docs
- [x] 4.1 `prototypes/uhuy-b2b-portal/README.md`.
- [x] 4.2 `backend/BACKEND_STATUS.md`, `frontend/TEST_FRONTEND.md`.
- [x] 4.3 OpenSpec change artifacts (this folder).
