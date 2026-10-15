# Proposal: Portal Internal Authentication (PT Luka)

## Why
The PT Luka portal homepage (login / registration) is currently a static design with no backend.
Internal factory users must be able to register for access, wait for Admin IT verification, log in
with an employee ID / NIK (KTP) / email / phone, change their password, and recover it via a
one-time code. Until this exists, every dashboard screen is reachable without identity and the
design mock cannot be used for real work.

## What Changes
- **Prototype backend** (`prototypes/sampling-spec-rnd/backend`): add `/api/auth/*` endpoints
  (register, login, logout, me, change-password, forgot-password, reset-password, admin
  approve/reject) backed by an in-memory identity store. No new dependencies: passwords use
  `hashlib.scrypt`, OTP/session tokens use `secrets`, email uses stdlib `smtplib`.
- **Registration is a request**: new accounts start `pending` and cannot log in until an Admin IT
  actor approves them. Rejected accounts stay blocked.
- **Frontend** (`prototypes/sampling-spec-rnd/frontend`): add `PortalAuthView` as an auth gate in
  front of the existing dashboard, plus `PortalAdminView` (approval queue) and a change-password
  card in Settings. Reuses existing design tokens (no new UI dependencies).

## Capabilities

### New Capabilities
- `portal-auth`: internal-user registration, Admin IT verification, password login, password
  change, and OTP-based password recovery for the PT Luka portal.

### Modified Capabilities
*(None)*

## Impact
- **Backend**: adds `src/services/auth_store.py`, `src/services/emailer.py`,
  `src/api/auth_routes.py`; wires the router in `src/main.py`; adds `tests/test_auth.py`;
  extends `.env.example` (SMTP + seed admin + TTLs).
- **Frontend**: adds `services/authApi.ts`, `services/authSession.ts`, `services/authRules.ts`,
  `pages/PortalAuthView.tsx`, `pages/PortalAdminView.tsx`, `components/ChangePasswordCard.tsx`;
  edits `App.tsx`, `components/Header.tsx`, `pages/SettingsView.tsx`, `services/http.ts`,
  `services/config.ts`, `services/identity.ts`; adds `tests/auth.test.ts`; extends `.env.example`.
- **Security/PII**: NIK/KTP is stored only as a SHA-256 lookup hash; passwords use salted scrypt;
  OTPs and session tokens are stored hashed and expire. `sessionStorage` holds the opaque access
  token (prototype ceiling, documented).
- **Not changed**: the frozen ops-engine OpenAPI contract; the production `backend/app` (auth
  there remains gated by `13-authn-authz-design.md`).
