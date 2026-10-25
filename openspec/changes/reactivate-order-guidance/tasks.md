## 1. Persistence and authenticated domain foundation

- [ ] 1.1 Add `prototypes/sampling-spec-rnd/backend/src/services/ops_store.py` using stdlib `sqlite3`, WAL, foreign keys, busy timeout, schema initialization, and a documented single-server ceiling; stop if the runtime requires shared/multi-node storage.
- [ ] 1.2 Define durable records for sample versions, append-only team/consent approvals, orders, order confirmations, audit events, and idempotency records; preserve accepted revision data in an immutable order snapshot.
- [ ] 1.3 Add first-run import from the existing JSON seed state, make SQLite authoritative after import, and ensure the generated database/WAL/SHM files are ignored without changing unrelated ignore rules.
- [ ] 1.4 Add `prototypes/sampling-spec-rnd/backend/src/api/auth_deps.py` or equivalent session dependency that resolves bearer sessions, tenant, client mapping, and role; reject missing/expired sessions and never trust query scope values.
- [ ] 1.5 Extend prototype session/user context and seeded accounts with tenant/client mapping; map only verified client identities and deny records for unmapped clients.
- [ ] 1.6 Add focused backend tests for authentication, role denial, client isolation, unmapped clients, invalid scope parameters, and restart persistence. Stop if current auth/session shapes differ from the inspected prototype; return evidence instead of weakening the boundary.

## 2. Approval, consent, and handoff API

- [ ] 2.1 Refactor sample-version mutations so confirmed state is persisted transactionally and request failures do not create local success; preserve existing valid lifecycle transitions.
- [ ] 2.2 Implement authenticated team approval with the exact `pending_approval` precondition and append-only approval record; use the signed-in actor rather than the fixed `manager-001` identity.
- [ ] 2.3 Implement staff-recorded client consent with `EMAIL`, `DOCUMENT`, or `REFERENCE`, bounded non-empty reference, optional note, actor, timestamp, and one-record-per-revision behavior; do not add file upload.
- [ ] 2.4 Implement authenticated Owner-or-Mandor handoff that requires team approval plus consent, validates order number/quantity/line/date fields, snapshots the accepted revision, creates `READY_FOR_PRODUCTION` order and confirmation, links the revision, and writes audit data in one transaction.
- [ ] 2.5 Require idempotency keys on consent and handoff writes; return the original response for identical retries, reject payload conflicts, and reject duplicate order numbers without changing existing data.
- [ ] 2.6 Add authenticated order/sample read endpoints with server-side tenant/client filtering; return not-found/denied behavior without cross-client record disclosure.
- [ ] 2.7 Register the new router and request identifiers in `prototypes/sampling-spec-rnd/backend/src/main.py`; keep downstream production, warehouse, QC, delivery, payroll, and purchasing endpoints untouched.
- [ ] 2.8 Add backend regression tests for valid flow, missing prerequisites, unauthorized roles, malformed consent, duplicate/replayed writes, conflicting order numbers, rollback on failure, immutable snapshot, exact `READY_FOR_PRODUCTION` status, and no downstream side effects. If any test needs a new business rule, stop and report the mismatch.

## 3. Frontend guidance and truthful actions

- [ ] 3.1 Add `prototypes/sampling-spec-rnd/frontend/src/services/orderApi.ts` for authenticated order, consent, handoff, and guidance reads with idempotency keys and typed success/error responses.
- [ ] 3.2 Add a maintainable source guidance component near the sampling frontend pages, using the existing `.client-flow-guide` styling direction where useful but deriving state from backend records rather than `currentView` position.
- [ ] 3.3 Render a semantic heading/landmark and ordered steps with text states for current, waiting, blocked, unavailable, and ready; preserve the sidebar and do not use color as the only state cue.
- [ ] 3.4 Wire guidance into `App.tsx` and `SampleVersionView.tsx` for both client and staff views, showing client-owned records only and exposing approval/consent/handoff controls only to their server-authorized roles.
- [ ] 3.5 Add staff consent-reference and Owner/Mandor handoff forms using the existing order fields; validate required values before submit and state clearly that handoff does not start production.
- [ ] 3.6 Remove/narrow local fallback success behavior for approval and conversion; keep confirmed state unchanged after failures and provide retryable actionable error messaging.
- [ ] 3.7 Update auth session typing/storage for tenant and client context without retaining a fixed client identity or treating client-side role checks as authorization.

## 4. Verification and browser evidence

- [ ] 4.1 Run `cd prototypes/sampling-spec-rnd/backend; pytest -q` and confirm the new focused tests cover the complete approved slice.
- [ ] 4.2 Run `cd prototypes/sampling-spec-rnd/frontend; npm run type-check`, `npm test`, and `npm run lint`; fix only errors caused by this change.
- [ ] 4.3 Run the local frontend/backend stack and `cd prototypes/sampling-spec-rnd/frontend; npm run test:e2e`; add a focused browser test for client scope, state text, keyboard focus, narrow viewport layout, and no false completion if the existing harness supports it.
- [ ] 4.4 Use the interactive browser to verify staff approval/consent/handoff and client read-only guidance with demo accounts; capture whether evidence came from interactive browser, automated Playwright, both, or neither.
- [ ] 4.5 Inspect the unified diff and run repository workspace hygiene checks; verify generated SQLite files and unrelated pre-existing dirty files are not staged or modified.
- [ ] 4.6 If any target path, endpoint, role mapping, persistence runtime, or test harness differs from this task record, stop with `BLOCKED: <what differs> | <evidence> | <question>` and do not widen scope.
