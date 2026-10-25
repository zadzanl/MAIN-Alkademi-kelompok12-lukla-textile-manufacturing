## Why

The remembered client guide is only partially present: its committed CSS remains, while its React implementation survives only in an ignored build bundle. More importantly, that guide treated page visits as completed order steps, while the current sampling service has no durable order entity, server-side role enforcement, client ownership binding, or reliable mutation persistence. This change restores the usability goal without presenting unverified progress as real order completion.

The first delivery will cover the trustworthy boundary from approved sample revision to saved order ready for production. It will serve both staff and client accounts inside the sampling Ops Engine on port 3009, and will stop explicitly before materials, production, QC, delivery, or UHUY portal integration.

## What Changes

- Add a data-driven order journey for a specific sample revision/order, replacing positional page completion with confirmed business states.
- Record team sample approval and staff-recorded external client consent as separate, auditable events.
- Allow only Owner or Mandor to authorize creation of a saved order in `READY_FOR_PRODUCTION` state.
- Persist the accepted sample snapshot, order handoff, approvals, audit events, and idempotency records across application restarts on the approved single-server deployment boundary.
- Enforce authentication, role checks, tenant scope, and server-side client scope for sampling and order reads/writes.
- Restore maintainable source for the guide presentation, with keyboard-accessible step navigation, explicit current/waiting/blocked states, and no color-only meaning.
- Preserve existing production, warehouse, QC, finance, and UHUY behavior; do not claim those stages are connected by this release.

## Capabilities

### New Capabilities

- `order-guidance`: State-aware guidance and saved handoff from sample approval to an order ready for production.

### Modified Capabilities

- None. No existing OpenSpec capability currently defines the sampling prototype's guided order journey requirements.

## Impact

- Sampling prototype backend under `prototypes/sampling-spec-rnd/backend/src`, including auth dependencies, sampling routes, persistence, order handoff service, and tests.
- Sampling prototype frontend under `prototypes/sampling-spec-rnd/frontend/src`, including `App.tsx`, `SampleVersionView.tsx`, a maintainable guidance component, styles, auth session data, and API clients.
- Prototype data directory gains a local transactional database file; generated database files must remain untracked.
- No new runtime dependency or external database service is required for the approved single-server scope.
- Existing uncommitted files outside this change must remain untouched.
