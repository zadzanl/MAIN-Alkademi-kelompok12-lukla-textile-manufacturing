# Tasks: Portal Internal Authentication

## 1. Backend
- [x] 1.1 `services/auth_store.py` — users, sessions, OTPs; scrypt hashing; identifier index.
- [x] 1.2 `services/emailer.py` — stdlib SMTP with `dev-log` fallback.
- [x] 1.3 `api/auth_routes.py` — register/login/logout/me/change/forgot/reset + admin approve/reject.
- [x] 1.4 Wire the router in `src/main.py`; seed the Admin IT account from env.
- [x] 1.5 `tests/test_auth.py` — lifecycle + error paths.
- [x] 1.6 Extend `.env.example` (SMTP, seed admin, TTLs).

## 2. Frontend
- [x] 2.1 `services/authRules.ts` — pure validation/format helpers.
- [x] 2.2 `services/authApi.ts` — typed client over `http.ts`.
- [x] 2.3 `services/authSession.ts` — session store (memory + sessionStorage).
- [x] 2.4 `services/http.ts` / `config.ts` — `base`/`token` options + `AUTH_BASE`.
- [x] 2.5 `pages/PortalAuthView.tsx` — login / registration / forgot-password.
- [x] 2.6 `pages/PortalAdminView.tsx` — approval queue (admin only).
- [x] 2.7 `components/ChangePasswordCard.tsx` + wire into Settings.
- [x] 2.8 `App.tsx` auth gate + admin nav + logout; `identity.ts` reads session actor.
- [x] 2.9 `tests/auth.test.ts`; extend `.env.example`.

## 3. Verification
- [x] 3.1 Backend: `pytest -q` (12 auth tests + existing contract tests), `ruff check`, `mypy src`.
- [x] 3.2 Frontend: `tsc --noEmit`, `eslint --max-warnings=0`, `node --test` (63 tests).
- [x] 3.3 Live smoke test: server boot + `/api/auth/health` + register→approve→login flow.

## 4. Docs
- [x] 4.1 Backend README + BACKEND_STATUS portal-auth section.
- [x] 4.2 Frontend INTEGRATION_GUIDE portal-auth section.
- [x] 4.3 OpenSpec change artifacts (this folder).
