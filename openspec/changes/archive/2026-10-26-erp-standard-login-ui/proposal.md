# Proposal: ERP-Standard Login UI (Ports 3009 & 3010)

## Why
Both prototype entry pages — the internal portal (`PortalAuthView`, port 3009) and the
external client portal (`PortalLoginView`, port 3010) — currently use a marketing-hero
vertical stack (large headline, two oversized action cards, form pushed below the fold).
That layout is unbalanced on desktop and buries the login form on phones/tablets. The
planning suite already defines the target enterprise behaviour
(`13-authn-authz-design.md`, `14-frontend-architecture.md`, `contracts/openapi.yaml`),
but the runnable screens do not yet reflect ERP conventions: environment/build
visibility, org identity, security posture, contract error codes, and legal/support
access. This change brings both entry pages to an ERP-standard login experience without
altering authentication or session behaviour.

## What Changes
- **Split login layout** (brand/context panel + auth form panel) at `lg+`; a compact
  brand band over the form on tablet/mobile. Replaces the hero + oversized action cards.
- **Organization identity + system name** on the brand panel.
- **Environment + build/version badge** (`dev`/`test`/`prod` + version) read from
  `VITE_APP_ENV`/`VITE_APP_VERSION` with safe defaults.
- **Security/trust panel** (TLS, auto session expiry, never-share credentials, audited
  login) — static copy only; no fabricated last-login/IP.
- **Legal/support footer** (privacy, terms, help, accessibility) as prototype
  placeholders that raise an informational toast.
- **Contract error-code messaging + requestId**: map `Problem.code` to stable Indonesian
  copy and surface the server `requestId` for support.
- **SSO / corporate login placeholder** button (disabled; OIDC is proposed, not built).
- **Additive error plumbing** so the login views can read `code`/`status`/`requestId`
  from `ApiError` (no change to login/session flow).

## Capabilities

### New Capabilities
- `erp-login-ui`: enterprise-standard login entry for the internal and external
  prototypes — split brand/form layout, environment/build visibility, security and
  legal surfaces, and contract-aligned error messaging.

### Modified Capabilities
*(None — the frozen `contracts/openapi.yaml` and the auth/session flow are unchanged.)*

## Non-Goals
- No change to authentication, session, refresh, or `getMyContext` behaviour.
- No real SSO/OIDC integration; the SSO control is an explicit placeholder.
- No backend changes; no new dependencies.
- No change to the 3009 Playwright smoke assertion (the form panel keeps an accessible
  `Akses portal` heading).

## Impact
- **Frontend UI only** plus additive error-metadata plumbing:
  - `prototypes/sampling-spec-rnd/frontend/src/pages/PortalAuthView.tsx`
  - `prototypes/uhuy-b2b-portal/frontend/src/pages/PortalLoginView.tsx`
  - `src/services/{config,http,problem,authApi|portalApi}.ts`, new `authErrorCopy.ts`,
    `.env.example` in both apps.
- **Security**: no new token handling; `sessionStorage` prototype ceiling unchanged.
- **Isolation**: external portal keeps its indigo accent + external marker; internal
  stays blue.
