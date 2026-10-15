# Design: Portal Internal Authentication

## Context
The portal homepage must authenticate internal factory users without adding dependencies. The
prototype backend runs in-memory on port 8009; the frontend is a React + Vite + Tailwind app on
port 3009 that already proxies `/api` to the backend. The production auth design
(`openspec/.../13-authn-authz-design.md`) is provider-gated and not implementable yet, so this
change delivers a self-contained prototype behind a stable API shape that can later be swapped for
PostgreSQL-backed endpoints.

## Decisions

### Credentials and identifiers
- A user may log in with **employee ID, NIK/KTP, email, or phone**. The store normalises each form
  and resolves the first matching index key, so the login field is a single free-text input.
- **Password + OTP for reset** (chosen over pure passwordless): login uses a password; "lupa akses"
  sends a 6-digit OTP to the registered email.

### Registration as a request
- Registration creates a `pending` account. It cannot log in until an `admin` actor approves it.
  This matches the supplied design copy ("Siapkan permintaan akses untuk tim Admin IT").

### Storage (in-memory, prototype)
- `PortalUser` holds display fields plus `password_hash` (scrypt) and `ktp_hash` (SHA-256). The
  plaintext NIK/KTP is never retained; only a masked last-4 is kept for display.
- Sessions and OTPs are stored as SHA-256 hashes with expiry; OTPs are single-use with an attempt
  cap and a per-identifier cooldown.

### Email
- `smtplib` sends the OTP when `SMTP_HOST` is configured. Otherwise the OTP is written to the
  backend log (`dev-log` mode) so the flow is testable without credentials. `forgot-password`
  always returns the same generic message to avoid account enumeration.

### Frontend integration
- `PortalAuthView` is rendered by `App` as a gate when there is no session; it reuses the app's CSS
  variables and `.field` / `.btn-primary` / `.tab` classes so light/dark mode, focus rings, 48px
  touch targets, and reduced-motion keep working.
- The opaque access token + actor context live in `authSession` (memory + `sessionStorage`).
- Admins get an extra "Persetujuan Akses" nav chapter; logout is a Header control; change password
  lives in Settings.

## Alternatives considered
- **Passwordless OTP login**: rejected — the requirement explicitly includes change-password, and a
  password gives a stable credential for internal accounts.
- **New dependency (`passlib`/`bcrypt`/`PyJWT`)**: rejected — stdlib `hashlib.scrypt` and opaque
  tokens cover the prototype; `AGENTS.md` forbids unrequested dependencies.
- **Implement in production `backend/app`**: deferred — that path is gated by unresolved provider
  decisions and would need PostgreSQL + RLS wiring.

## Known ceiling & upgrade path
Single-process, in-memory, resets on restart; `sessionStorage` is script-readable. Upgrade by
swapping `auth_store` for the production `actors`/`sessions`/`credentials` tables and moving the
token to memory + HttpOnly refresh cookie, without changing the HTTP contract or UI.
