## Context

The remembered guide is split across artifacts. `prototypes/sampling-spec-rnd/frontend/src/index.css#L185-L211` contains committed `.client-flow-guide` styles, while the recovered `ClientFlowGuide` implementation exists only in an ignored compiled bundle and is not part of the current Vite source. Its three-step completion was positional, not business-state based.

The active sampling backend stores sample versions in an in-process dictionary and writes a JSON seed snapshot only during initialization. The current mutation handlers at `prototypes/sampling-spec-rnd/backend/src/api/routes.py#L526-L598` do not authenticate callers, persist mutations, create an order entity, or connect the free-text conversion reference to production records. The frontend also contains failure fallbacks that can display local success after an unsuccessful request.

The approved first slice is deliberately smaller: sample-team approval plus staff-recorded external client consent, followed by Owner-or-Mandor authorization of a saved order in `READY_FOR_PRODUCTION`. It runs inside the sampling Ops Engine on one application server. The UHUY portal and downstream warehouse, production, QC, delivery, and purchasing flows are excluded.

## Goals / Non-Goals

**Goals:**

- Provide a durable, per-revision state model for approval, consent, and order handoff.
- Enforce role and tenant/client scope on the server, not only in React.
- Make handoff atomic and retry-safe, with an immutable accepted sample snapshot and audit trail.
- Restore a maintainable accessible guidance component that reports confirmed state and explicit boundaries.
- Reuse existing order form fields while treating production-line text as descriptive only.

**Non-Goals:**

- Do not implement actual file upload or document storage; consent stores a method/reference/note.
- Do not connect or claim live material allocation, production execution, QC, delivery, payroll, purchasing, or shipment.
- Do not integrate the separate UHUY portal or root PostgreSQL service in this release.
- Do not grant clients approval, conversion, or handoff actions.
- Do not edit generated `dist` assets as source.

## Decisions

### 1. Keep the implementation in the sampling prototype

Use the existing `prototypes/sampling-spec-rnd/backend` and `frontend` because the approved behavior is for the running `:3009` Ops Engine. Do not reuse the root backend: its planned order schema is not implemented, its default PostgreSQL service is not available in this workspace, and its frontend is a separate mock harness.

### 2. Use standard-library SQLite for the single-server durable slice

Add a small SQLite store using Python `sqlite3`, WAL mode, foreign keys, busy timeout, and `BEGIN IMMEDIATE` transactions. This requires no new dependency or service and survives backend restart. Keep schema names close to the planned order/sample concepts so a later PostgreSQL migration can map them.

Alternatives rejected:
- Continue using the JSON snapshot: whole-file rewrites are not safe for concurrent actors and current mutations are lost on restart.
- Add root PostgreSQL now: requires infrastructure, migrations, a second auth trust model, and a much larger scope than the approved first delivery.

The known ceiling is one application server. If the deployment requires multiple workers across machines or horizontal scaling, stop and migrate this slice to shared PostgreSQL rather than silently relying on a local file.

### 3. Store explicit records and immutable handoff snapshot

Use tables/records for sample versions, approval records, orders, order confirmations, audit events, and idempotency records. The handoff transaction SHALL validate the revision, required approvals, role, order uniqueness, and input constraints; snapshot the accepted revision; create the order and authorization; update the revision link; record audit/idempotency; then commit or roll back as one unit.

The order status is exactly `READY_FOR_PRODUCTION`. Creating it does not call production, warehouse, QC, or purchasing APIs.

### 4. Record consent references, not files

The consent record stores `EMAIL`, `DOCUMENT`, or `REFERENCE`, a non-empty bounded reference string, optional note, actor, and timestamp. There is no upload route or configured object storage in the current prototype. Adding file bytes would be a separate security/storage decision and is explicitly excluded.

### 5. Derive scope from authenticated sessions

Extend the prototype session context with tenant and client identity. Sampling endpoints use the bearer session dependency and enforce role guards. Client reads are filtered by mapped `client_id`; unmapped clients receive no records. Query `tenant_id` and `client_id` values are not authorization inputs.

The selected business permissions are:
- Sample-team role: team approval and staff-recorded client consent.
- Owner or Mandor: final order handoff.
- Client: read own state and guidance only.
- Other roles: no approval, consent, or handoff writes.

### 6. Separate journey state from navigation

Create a source TypeScript guidance component and retain the existing CSS direction where useful, but derive state from API records. Use a semantic heading/landmark and ordered list; include textual labels such as Current, Waiting for Sample team, Consent recorded, Ready for production, Blocked, and Unavailable. Keep the sidebar as the primary navigation. Do not render a step complete because a page was visited.

### 7. Make API failures truthful

Remove or narrow frontend success fallbacks for approval, consent, and handoff. A failed request keeps the prior confirmed state, shows an actionable error, and allows retry. The UI may show optimistic busy state, but it must not manufacture a business success record.

## Risks / Trade-offs

- **[Risk] Local SQLite is unsuitable for multi-node deployment.** → Add a module header documenting the ceiling and fail deployment review if more than one application server is required.
- **[Risk] Existing seed JSON and new SQLite records can diverge.** → Add a first-run import/migration path, make SQLite authoritative after initialization, and test restart behavior; do not continue writing both stores.
- **[Risk] Existing demo accounts have incomplete client mapping.** → Map only known accounts; deny unassigned client reads and report the missing mapping rather than broadening access.
- **[Risk] Existing routes and tests expect unauthenticated calls.** → Update focused tests and preserve a clear compatibility boundary; if a caller cannot provide authenticated session context, stop rather than weakening server-side authorization.
- **[Risk] Business users may interpret READY_FOR_PRODUCTION as production started.** → Use exact copy and guidance boundary text; no downstream status is shown as complete.
- **[Risk] Duplicate submissions can create duplicate orders.** → Require idempotency keys for writes, hash payloads, return cached identical results, and reject conflicting reuse.
- **[Risk] Consent references may be insufficient for audit policy.** → The first release records method/reference/note as explicitly approved; file upload remains a separately scoped follow-up.

## Migration Plan

1. Initialize the local database and import the existing sample seed snapshot once.
2. Run focused backend tests for authorization, client scope, consent validation, handoff atomicity, idempotency, conflict handling, and restart persistence.
3. Run frontend type-check/unit tests and the local browser harness for keyboard, responsive, and state messaging evidence.
4. If migration or runtime behavior differs from this design, stop and return a blocked report; do not fall back to in-memory or unauthenticated behavior.
5. Rollback is application-level: stop using the new routes/component and restore the previous source revision; never delete the database file as a rollback shortcut. Preserve it for inspection and migration recovery.

## Open Questions

None. Business decisions for this first slice were confirmed: consent is recorded by reference, deployment is single-server, handoff creates a saved `READY_FOR_PRODUCTION` order, and Owner or Mandor authorizes it.
