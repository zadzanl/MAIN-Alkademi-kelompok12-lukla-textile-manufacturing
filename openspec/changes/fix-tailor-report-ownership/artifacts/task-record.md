# Task record: fix tailor report ownership

## Intent

Prevent a signed-in `Tailor`/`penjahit` from reading or mutating another tailor's mock sewing report. Keep `Mandor` production verification and administration working. Fail closed when a tailor session has no explicit operator identity. This is a prototype/mock-mode authorization fix; frontend checks must not be presented as live-mode security.

## Exact bounded plan

1. `prototypes/sampling-spec-rnd/backend/src/api/auth_routes.py`: add an explicit prototype-only `operatorId` to the seeded `penjahit1` actor context, using the stable mock operator ID assigned to Dewi Lestari's `OPR-010` record. Do not infer identity from display name or select the first operator.
2. `prototypes/sampling-spec-rnd/frontend/src/services/authApi.ts`: type the optional server-issued `operatorId` actor field.
3. `prototypes/sampling-spec-rnd/frontend/src/services/opsApi.ts`: read the current actor session; in mock mode scope tailor operator/assignment reads to the explicit operator ID, reject missing/unlinked tailor identity, reject tailor admin writes and tally verification, and authorize tally ownership before idempotency replay. Leave non-tailor/mandor behavior unchanged. Do not claim live mode is secured by these frontend guards.
4. `prototypes/sampling-spec-rnd/frontend/src/pages/ProductionView.tsx`: derive role from the current session, hide the admin switcher and prevent admin-mode rendering for tailor users, while retaining terminal access for tailor and existing admin/mandor behavior.
5. `prototypes/sampling-spec-rnd/frontend/src/pages/FloorTerminalView.tsx`: reset draft counts/results when the authenticated actor changes so a session switch cannot reuse another user’s unsent state.
6. Add focused runnable regression tests under `prototypes/sampling-spec-rnd/frontend/tests` for service authorization, including missing identity, cross-operator mutation, idempotency ordering, and mandor verification compatibility. Preserve all unrelated dirty edits.

## Edge cases and verification

- A tailor with no `operatorId` gets no operators/assignments and cannot write.
- A tailor cannot replay another actor's idempotency key before ownership validation.
- A tailor cannot use `createOperator`, `assignOperator`, or `verifySewingTally` through the mock service.
- A `Mandor` remains able to read the full mock production data and verify tallies.
- Live transport remains server-authorized; this change does not claim to secure it.
- Commands: `npm run build`; focused frontend tests via `npm test -- --test-name-pattern ...` or the narrowest existing runnable test command; inspect `git diff` and ensure tracked generated `dist` is unchanged.