# Phase B2 — Frontend Architecture

**Status:** Planning proposal only. No frontend application, dependency, browser test, service worker, or deployment is implemented by this document.

**Contract boundary:** This design consumes the reviewed `artifacts/contracts/openapi.yaml`. It does not change operation IDs, paths, required fields, error codes, ownership dimensions, or `(tenant, operationId, Idempotency-Key)` idempotency scope.

## 1. Sources and design limits

- `[task]` `task-record.md`, revision 15; Phase B is authorized after A3 approval.
- `[plan]` `09-technical-blueprint-completion-plan.md`, especially the six-view inventory, portability commitments, and NFR-05 tally requirement.
- `[tech]` `artifacts/tech_plan-blueprint-001.md`, Contract Schema Conventions, Test Mapping, and offline tally boundary.
- `[stack]` `artifacts/10-technology-stack-and-decisions.md`, §2 Web portability (`Next.js`, `output: standalone`, no Vercel-only API).
- `[schema]` `artifacts/11-database-schema-spec.md`, sewing tally, assembly/QC, idempotency, outbox, and scope dimensions.
- `[api]` `artifacts/12-api-contract-plan.md`, endpoint catalog and error/paging/idempotency rules.
- `[contract]` `artifacts/contracts/openapi.yaml`, the machine-readable operation and schema source.
- `[rbac]` `04-rbac-matrix.md`, eight roles and explicit restrictions.
- `[tests]` `06-acceptance-tests.md`, AT-01–AT-10 and AT-R01–AT-R08; no runtime assertions are claimed here.
- `[review]` `artifacts/review/blueprint-contract-review.md`, approved frozen contract and proof gaps.

**PROPOSAL:** use a responsive Next.js web application with a framework-neutral data-access layer and `output: 'standalone'`. The same frontend build must be hostable by Vercel, AWS Amplify/CloudFront, or a standard container/static delivery path. No Vercel-only server action, Edge runtime, ISR write, or image-optimization dependency is required.

## 2. Information architecture and six views plus ledger

The six product views are represented by the contract metadata as `VIEW-01` through `VIEW-06`. The ledger is an explicit finance surface within `VIEW-06`, not a new contract view.

| View | Route proposal | Primary users | Primary operation IDs |
|---|---|---|---|
| `VIEW-01` Operations dashboard | `/app/overview` | Owner, ProductionHead, FinancePayroll, scoped internal users | `getDashboard`, `listOrders`, `getOrder`, `listProductionProgress`, `listAuditEvents`, `getPortalOrderStatus`, `searchOperationalDocuments` |
| `VIEW-02` Sample and specification tracker | `/app/samples` | SampleTeam, Owner, scoped production users | `listSamples`, `createSample`, `listSampleRevisions`, `createSampleRevision`, `approveSample`, `lockSample`, `recordTimeStudy`, `convertSampleToOrder`, `listRateCards`, `upsertRateCard`, `createFileUpload`, `completeFileUpload` |
| `VIEW-03` Warehouse and cutting controls | `/app/materials` | Warehouse, Owner, scoped production users; client read projection where permitted | `getStock`, `receiveMaterial`, `issueMaterial`, `createStocktake`, `createStockAdjustment`, `recordCuttingResult`, `createOrder`, `listOrders`, `getPortalOrderStatus`, `createFileUpload`, `completeFileUpload` |
| `VIEW-04` Production line and 30-minute tally terminal | `/app/production` and `/terminal/tally` | ProductionHead/Mandor, Tailor, scoped operators | `listLines`, `createLine`, `listOperators`, `createOperator`, `listAssignments`, `assignOperator`, `recordSewingTally`, `verifySewingTally`, `listAssemblies`, `createAssembly`, `listProductionProgress`, `listRateCards` |
| `VIEW-05` QC and defect routing | `/app/quality` | QCInspector, ProductionHead, scoped finance/read users | `listAssemblies`, `inspectUnit`, `getOrder`, `listProductionProgress` |
| `VIEW-06` Finance, payroll, procurement and ledger | `/app/finance` | FinancePayroll, Owner, authorized internal reviewers | `getLedgerEntries`, `appendLedgerTransaction`, `reverseLedgerTransaction`, `listAuditEvents`, `createPayrollPeriod`, `listPayrollPeriods`, `calculateWeeklyPayroll`, `getPayrollStatement`, `getBonusPool`, `approvePayroll`, `recordPayrollPayment`, `recordOverhead`, `calculateOverhead`, `listFinancialRules`, `proposeFinancialRule`, `approveFinancialRule`, `listClientInvoices`, `createClientInvoice`, `issueClientInvoice`, `createPurchaseOrder`, `approvePurchaseOrder`, `recordSupplierInvoice`, `getJob`, `runSaturdayPayrollJob`, `runMonthlyOverheadJob`, `getFileDownload`, `searchOperationalDocuments` |

`VIEW-01` may render a client-portal projection through `getPortalOrderStatus`, but the client experience must use a separate navigation shell and server-derived scope. It must not expose internal dashboard fields merely because both surfaces use the same route component.

## 3. Route-to-operation binding rules

The UI data layer should expose typed operation functions generated or hand-written from the OpenAPI contract, but the route components must depend on domain hooks rather than raw `fetch` calls. Each request carries `X-Request-Id`; each retryable mutation carries a stable client-created `Idempotency-Key`.

| UI action | Operation ID | Mutation policy |
|---|---|---|
| Load dashboard cards | `getDashboard` | read; abort stale requests; scope comes from server |
| Open order detail | `getOrder` | read; inaccessible order is rendered as not-found, not cross-tenant detail |
| Submit sample revision | `createSampleRevision` | idempotent; preserve draft until server acknowledgment |
| Approve or lock sample | `approveSample`, `lockSample` | confirm state and permission; no optimistic lock success |
| Receive/issue material | `receiveMaterial`, `issueMaterial` | no optimistic stock decrement; surface legal-owner/beneficiary conflict |
| Record cutting result | `recordCuttingResult` | idempotent; material-unit validation stays server-side |
| Submit tally | `recordSewingTally` | queueable offline under §5; stable interval key and replay-safe payload |
| Verify tally | `verifySewingTally` | online only unless a later contract explicitly supports otherwise |
| Create assembly / inspect | `createAssembly`, `inspectUnit` | online, stateful, no speculative QC success |
| Calculate/approve payroll | `calculateWeeklyPayroll`, `approvePayroll` | online; pending financial rule is a blocking state |
| Post/reverse ledger | `appendLedgerTransaction`, `reverseLedgerTransaction` | online; no client-side balance authority; no destructive edit UI |

Operation IDs in this table are copied from `[contract]`; a removed or renamed ID is a contract change, not a frontend refactor.

## 4. Shared state and request lifecycle

**PROPOSAL:** separate four state classes:

1. **Session state:** access token in memory, refresh lifecycle, current actor/context from `getMyContext`, and an explicit `AUTH_REQUIRED` transition.
2. **Server state:** cache keys include operation, normalized parameters, and effective server context. Invalidate related reads after a successful mutation. Never use cached data as authorization proof.
3. **Draft state:** local form values and validation messages; drafts may survive navigation but are not presented as committed records.
4. **Offline mutation state:** a bounded, inspectable tally queue only. Every queued item shows status, attempt count, last error, and server result.

All errors map from `Problem.code`, not message text. The minimum UI mapping is:

| Code/state | UI behavior |
|---|---|
| `AUTH_REQUIRED` | pause mutation, restore/session prompt, preserve safe draft; never retry indefinitely |
| `FORBIDDEN` | permission explanation and read-only fallback; no hidden mutation retry |
| `TENANT_CONTEXT_MISSING` | stop requests and require context reload; log request ID |
| `LEGAL_OWNER_MISMATCH` / `ORDER_BENEFICIARY_MISMATCH` | show the ownership conflict and leave stock/order form unchanged |
| `IDEMPOTENCY_CONFLICT` | show “same key, different data”; require explicit new submission after reviewing draft |
| `INVALID_STATE` / `LEDGER_IMMUTABLE` | explain that the record cannot be edited; offer approved next workflow if one exists |
| `FINANCIAL_RULE_PENDING` | mark calculation/approval blocked, not zero or successful |
| `VALIDATION_ERROR` | map `violations[]` to fields and retain entered values |
| network/offline | queue only eligible tally writes; all other mutations remain unsent and visibly pending |

## 5. Thirty-minute tally terminal: retry, offline, and idempotency

`recordSewingTally` is the only mutation proposed for bounded offline capture. The database contract requires an operator, line, component, cut batch, aligned 30-minute interval, quantity, and idempotency key. The client must not invent a different interval or use a floating material quantity.

### 5.1 Stable submission identity

For each user-created tally, generate one UUID `clientSubmissionId` and derive a stable `Idempotency-Key` from it (or use it directly if the contract permits). Store the canonical request payload alongside it in IndexedDB. The key is reused for every retry of that logical submission; it is never regenerated after a timeout.

The canonical payload must include the ownership-relevant identifiers supplied by the contract. A user editing any identifying field creates a new submission/key rather than mutating a queued record. The server remains authoritative and returns the stored result on an identical replay; altered payload under the same key must display `IDEMPOTENCY_CONFLICT`.

### 5.2 Queue state machine

`DRAFT -> QUEUED -> SENDING -> ACCEPTED | RETRYABLE_FAILURE | PERMANENT_FAILURE`.

- `QUEUED`: created locally with visible timestamp and actor/device context.
- `SENDING`: one active attempt per key; use an abortable request and bounded backoff with jitter.
- `ACCEPTED`: retain server tally ID and response for audit; remove only after a retention/inspection policy is met.
- `RETRYABLE_FAILURE`: network, timeout, or explicitly retryable server failure; retry on reconnect and manual retry.
- `PERMANENT_FAILURE`: validation, permission, ownership, state, or idempotency conflict; stop automatic retry and require correction/new key.

The queue has a finite capacity and an explicit “storage full / export or discard” path. Discarding a queued item requires confirmation and is recorded locally; it does not claim server deletion. Offline mode shows stale-data age and never promises that payroll/progress has incorporated unsent tallies.

### 5.3 Reconnect safety

On reconnect, refresh session/context first, then replay oldest queued entries serially or with a small bounded concurrency that cannot reorder dependent operations. Before sending, revalidate that the local actor/device session is still usable. The server rechecks assignment, tenant, legal-owner/beneficiary scope, cut-batch capacity, interval uniqueness, and current state. A successful response is authoritative even if the original network response was lost.

Offline tally support is a **proposal** pending the final tablet lifecycle and retention decisions in `13-authn-authz-design.md`. It is not permission to queue QC, payroll approval, ledger posting, stock adjustment, or invoice issuance.

## 6. Loading, error, permission, and offline states

Every route and mutation has explicit states; blank screens and disabled controls without explanation are not acceptable.

| State | Required behavior |
|---|---|
| Initial loading | route-level skeleton preserves layout; announce loading status to assistive technology where meaningful |
| Refreshing | retain last known safe data with a non-blocking “updating” indicator; do not show old data as confirmed after a failed mutation |
| Empty | explain what is empty and the permitted next action; distinguish no data from no permission |
| Error | show stable human wording, request ID, retry action when safe, and support path; do not expose SQL/provider details |
| Permission denied | render read-only/blocked state based on server response; do not infer access from hidden navigation alone |
| Not found | use an indistinguishable inaccessible/not-found detail response where required by API contract |
| Offline | show connection status, data age, queued tally count, and actions disabled because they are online-only |
| Session expired | preserve safe local draft, pause queue, reauthenticate, then revalidate before replay |
| Pending financial rule | visibly block approval/payment and link to the unresolved decision; never substitute a demo default |

The dashboard and portal must not use a client-supplied tenant selector as a scope switch. If an authorized internal user has multiple scopes, the server-derived context picker may request a bounded context, and all affected caches must be invalidated after the change.

## 7. Accessibility and reduced motion

**PROPOSAL:** target WCAG 2.2 AA-equivalent behavior for keyboard and assistive-technology flows, subject to a future accessibility review.

- Every interactive control has a visible focus indicator, keyboard path, accessible name, and logical focus order.
- Tables expose headers and relationships; status badges include text, not color alone. Pass/Repair/Reject and `Menunggu QC` are written labels.
- Form errors are associated with fields and summarized at submit; queued tally status is announced without interrupting unrelated work.
- Touch targets on the floor terminal are large enough for gloved/tablet use, while still supporting keyboard/switch input where practical.
- Modal confirmations trap and restore focus; destructive/reversal actions require clear confirmation and explain immutable-history consequences.
- Color contrast, zoom/reflow, orientation, and screen-reader semantics are tested in the future browser harness; no visual-only pass claim is made now.
- Honor `prefers-reduced-motion: reduce`: remove decorative transitions, spring effects, parallax, and nonessential auto-animation. Loading must remain understandable through text/status semantics. Do not make essential feedback depend on motion.
- Provide a static equivalent for progress/tally freshness and connection state; do not rely on animation to signal an upload or sync.

## 8. Hosting portability and build boundary

The frontend build must:

- use standard browser APIs and HTTPS API calls;
- emit a standalone build suitable for a container or standard host;
- read API origin and public feature flags from deployment configuration, not hard-coded Vercel globals;
- keep authentication cookie/domain/CORS policy explicit per environment;
- avoid Vercel-only server actions, Edge-only APIs, ISR writes, and required platform storage;
- permit AWS CloudFront/Amplify or an ordinary container/static host as the primary alternative;
- keep offline data in browser storage behind a small adapter so IndexedDB can be replaced or disabled for unsupported devices;
- make service-worker/cache policy explicit and never cache private API responses as public assets.

The API origin, issuer, audience, and environment are deployment concerns. The UI must not infer legal ownership or beneficiary from the hosting provider or URL path.

## 9. Verification plan and known ceiling

Required future checks:

1. Parse `openapi.yaml` and verify every referenced operation ID in this document resolves.
2. Run the eventual Playwright suite for login/session expiry, each view's loading/error/permission states, client A/B isolation, tally offline/reconnect/idempotent replay, and reduced-motion mode.
3. Verify keyboard navigation, focus restoration, accessible names, status text, contrast, zoom/reflow, and no-motion behavior with an accessibility tool and manual review.
4. Verify the tally queue never retries a permanent failure and never changes an idempotency key after timeout.
5. Verify both a Vercel-compatible build and an AWS/container-compatible standalone build, without assuming either deployment is available during planning.

From `C:\Projects\hackathon-MAIN-alkademi`:

```powershell
python -c "import yaml; d=yaml.safe_load(open('openspec/changes/lukla-ops-engine-planning/artifacts/contracts/openapi.yaml')); ids={o['operationId'] for item in d['paths'].values() for o in item.values() if isinstance(o,dict) and 'operationId' in o}; refs={'getDashboard','listOrders','getOrder','listProductionProgress','listAuditEvents','getPortalOrderStatus','searchOperationalDocuments','listSamples','createSample','listSampleRevisions','createSampleRevision','approveSample','lockSample','recordTimeStudy','convertSampleToOrder','listRateCards','upsertRateCard','getStock','receiveMaterial','issueMaterial','createStocktake','createStockAdjustment','recordCuttingResult','listLines','createLine','listOperators','createOperator','listAssignments','assignOperator','recordSewingTally','verifySewingTally','listAssemblies','createAssembly','inspectUnit','getLedgerEntries','appendLedgerTransaction','reverseLedgerTransaction','createPayrollPeriod','listPayrollPeriods','calculateWeeklyPayroll','getPayrollStatement','getBonusPool','approvePayroll','recordPayrollPayment','recordOverhead','calculateOverhead','listFinancialRules','proposeFinancialRule','approveFinancialRule','listClientInvoices','createClientInvoice','issueClientInvoice','createPurchaseOrder','approvePurchaseOrder','recordSupplierInvoice','getJob','runSaturdayPayrollJob','runMonthlyOverheadJob','createFileUpload','completeFileUpload','getFileDownload'}; missing=sorted(refs-ids); assert not missing, missing; print('frontend operationIds=PASS',len(refs))"
openspec validate lukla-ops-engine-planning
git diff --check
```

These checks validate document structure and contract references only. They do not execute a browser, prove accessibility, prove offline durability, or prove API authorization.

## 10. Unresolved product decisions

The following remain explicit decisions needed rather than hidden implementation assumptions: final route names and navigation labels; client portal mutation scope; tablet offline grace/queue retention; device storage policy; exact dashboard aggregation and freshness target; payroll/ledger display permissions; financial-rule approval UX; browser support matrix; service-worker update/rollback policy; and the final identity-provider/session storage choices. None may be resolved by changing the frozen contract in an unreviewed frontend change.
