# Design: ERP-Standard Login UI

## Context
Two independent React + Vite + Tailwind prototypes share one visual language but not
code. The internal app (`prototypes/sampling-spec-rnd/frontend`, port 3009) and the
external portal (`prototypes/uhuy-b2b-portal/frontend`, port 3010) each own their own
`index.css` tokens and services. Both entry pages are near-duplicates.

Sources of truth for this design:
- `13-authn-authz-design.md` — bearer session, 8 roles, deny-by-default, `AUTH_REQUIRED`.
- `14-frontend-architecture.md` — `/auth/login`, session state, `Problem.code` error
  mapping, WCAG 2.2 AA, reduced motion.
- `contracts/openapi.yaml` — `LoginRequest`, `Session`, `Problem` (`code` enum + `requestId`
  + `violations[]`).
- `15-deployment-and-operations.md` §52 — `dev`/`test`/`prod` environments.
- `04-rbac-matrix.md` — internal roles vs. external Klien Maklon.

## Decisions

### 1. Split layout, single column below `lg`
`lg` is the existing desktop breakpoint used by both app shells. The brand/context panel
is full-height beside the form at `lg+` and collapses to a compact brand band on top of
the form on tablet/mobile. This keeps the form above the fold on phones.

### 2. Environment/build are deployment config, not host globals
`VITE_APP_ENV` (default `dev`) and `VITE_APP_VERSION` (default `1.0.0`) are read through
the existing `config.ts` env guard. Badge colour: `dev`=brand, `test`/`uat`=warning,
`prod`=danger, unknown=neutral. No URL/host inference (per `14-frontend-architecture.md` §8).

### 3. Error messaging is UI-only
The transport already extracts `code` into `ApiError`; `ApiResult` is extended
additively with optional `code`/`status`/`requestId`. A pure `authErrorCopy.ts` maps
`Problem.code` to Indonesian copy and decides the feedback tone. No retry/session logic
is added.

### 4. Security panel is static and honest
Trust copy is fixed (TLS, auto expiry, never-share, audited). No last-login/IP is shown
because the prototype backend does not return it — inventing it would violate the
source-fidelity rule in this repo.

### 5. Legal/support links are explicit placeholders
They are buttons (not dead `href="#"` links) that raise an info toast, so the affordance
is accessible and the limitation is visible rather than hidden.

### 6. Preserve the smoke contract
The form panel keeps an `<h2>` whose accessible name is exactly `Akses portal`, so
`prototypes/sampling-spec-rnd/frontend/tests/smoke.spec.ts` passes unchanged.

## Accessibility
- Brand panel is `<aside aria-label>`; form panel is a labelled `<section>`.
- Errors use `role="status"`/`aria-live`; field errors link via `aria-describedby`.
- Disabled SSO control carries a visible explanation, not just `disabled`.
- Focus order is brand → form; reduced-motion is already global.
- Status badges carry text, never colour alone.

## Known ceiling / upgrade path
- The SSO control is a placeholder; wire to an OIDC provider when the issuer decision in
  `13-authn-authz-design.md` §9 is made.
- Environment/version are build-time only; a future `/me/context` or build manifest can
  supply them dynamically without changing this layout.
