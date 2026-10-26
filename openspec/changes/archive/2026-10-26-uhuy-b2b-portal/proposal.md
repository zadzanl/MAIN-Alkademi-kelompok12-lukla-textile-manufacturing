# Proposal: UHUY B2B External Client Portal (Portal Eksternal)

## Why
Lukla's internal dashboard (Sampling & Spec R&D) serves factory staff. The business
also needs a **separate, client-facing** application: maklon clients ("Klien Maklon/Ext",
RBAC role #8) must be able to register for access, log in, submit production-order and
design/sample requests, track their own order progress, and see their own consigned
(titipan) material balance. Today the client portal exists only as a planning lifecycle
(`13-authn-authz-design.md` §7) with no runnable app, and the source RBAC marks portal
mutations ("may a client submit/edit an order") as an open decision — this change takes
the pragmatic decision to allow **request submission** while keeping all reads
client-scoped.

## What Changes
- **New prototype** `prototypes/uhuy-b2b-portal/` — a standalone external portal, separate
  from `prototypes/sampling-spec-rnd/` (internal).
  - **Backend** (`backend/`, port 8010, FastAPI): a dedicated external-portal API with
    client-scoped in-memory data. No new dependencies (stdlib `hashlib.scrypt`,
    `secrets`, `smtplib`).
  - **Frontend** (`frontend/`, port 3010, React + Vite + Tailwind): reuses the existing
    component/design-token layer, with an **indigo accent + "PORTAL EKSTERNAL" marker**
    so it is never confused with the internal app.
- **External client authentication**: registration creates a `pending` account that an
  internal approver activates; login by email or phone; change/forgot/reset password.
- **Client-scoped data**: orders, consigned stock, and request history are filtered
  server-side by the session's `client_id`; `client_id` is never taken from the request.
- **Request submission**: clients can submit production-order and design/sample requests
  (status `submitted`).

## Capabilities

### New Capabilities
- `uhuy-b2b-portal`: external client authentication, client-scoped order/stock visibility,
  and order/sample request submission for the UHUY B2B portal.

### Modified Capabilities
*(None — this is an independent external application; it does not change the frozen
ops-engine OpenAPI contract or the internal prototype.)*

## Impact
- **New code only**: `prototypes/uhuy-b2b-portal/{backend,frontend}` and this OpenSpec
  change folder. No existing prototype, contract, or production `backend/app` is modified.
- **Security/PII**: passwords use salted scrypt; session tokens and OTPs are stored hashed
  and expire. `sessionStorage` holds the opaque access token (prototype ceiling).
- **Isolation**: the external portal is a separate backend/port; client A cannot read or
  mutate client B rows (acceptance-test AT-R08 analog).
