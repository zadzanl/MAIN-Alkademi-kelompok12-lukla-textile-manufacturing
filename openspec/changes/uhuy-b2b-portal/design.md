# Design: UHUY B2B External Client Portal

## Context
The internal prototype (`prototypes/sampling-spec-rnd/`) is a single-tenant-ish internal
dashboard on ports 8009/3009. The external portal must be a distinct application for
maklon clients: different audience, different trust boundary, and a clear visual marker.
It reuses the internal app's *frontend* conventions (React + Vite + Tailwind, Apple-inspired
design tokens, component set) but ships its **own backend** ("portal eksternal", port 8010)
so the internal API surface is untouched.

## Decisions

### Separate backend and port
- **Choice:** a dedicated FastAPI app under `prototypes/uhuy-b2b-portal/backend` on port
  8010, with its own client store. Frontend on port 3010, proxying `/api` → 8010.
- **Rationale:** the external portal has a different audience and authorization model;
  sharing the internal process would blur the trust boundary and risk cross-audience
  leakage. Separate ports also let both run side by side during a demo.
- **Alternatives considered:** adding a portal view inside the internal app (rejected —
  mixes audiences, no clean marker); reusing the internal store (rejected — the internal
  store is tenant/actor oriented, not client-scoped).

### Client-scoped authorization boundary
- **Choice:** every data method takes `client_id`; the route layer resolves it **only**
  from the authenticated session. Reads for another client's id return `404` (never `403`)
  to avoid confirming existence.
- **Rationale:** this is the core invariant of RBAC role #8 and acceptance test AT-R08.
- **Alternatives considered:** trusting a `client_id` query/body field (rejected —
  client-controlled input must never be an authorization source, per `13-authn-authz-design.md` §3.1).

### Request submission allowed; no internal mutation
- **Choice:** clients may *submit* order/sample requests (`status=submitted`). They cannot
  confirm, price, or advance an order — that stays internal.
- **Rationale:** the RBAC marks portal mutation as an open decision; allowing submission
  with an explicit internal review status satisfies "client can order" without granting
  workflow authority.

### External marker
- **Choice:** an indigo accent (overriding `--c-brand`/`--blue`), a persistent top ribbon,
  a `PortalBadge` component in the sidebar/header/login, and `VITE_PORTAL_SCOPE=external`.
- **Rationale:** make the external build unmistakable next to the internal dashboard.

### Storage & auth primitives
- **Choice:** reuse the internal prototype's proven primitives — stdlib `scrypt` password
  hashing, opaque `secrets` session tokens (stored hashed, expiring), stdlib `smtplib`
  with a `dev-log` fallback for OTP.
- **Rationale:** no new dependencies; consistent with `portal-auth`.

## Known ceiling & upgrade path
Single-process, in-memory, resets on restart; `sessionStorage` is script-readable; requests
are not persisted. Upgrade by replacing `portal_store` with the production PostgreSQL tables
(`actors`, `client_memberships`, `orders`, `stock_lots`, `portal_requests`) behind the same
method API and enforcing the `client_id` predicate via RLS, without changing the HTTP
contract or UI.
