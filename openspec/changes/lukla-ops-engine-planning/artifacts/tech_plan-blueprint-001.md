# Technical Plan: Lukla Operations Engine Blueprint Execution

## Goal
Produce the approved planning-only blueprint for an AWS-first but portable Lukla Operations Engine, with contract-first interfaces that let backend, frontend, data, operations, AI-search, and verification work proceed in parallel after a small sequential contract gate. The result must trace the BRD v2.3.0, PRD v2.0, source register, RBAC matrix, acceptance scenarios, and unresolved business decisions without rewriting those canonical requirements.

## Current Reality

- Approved design brief: `C:\Projects\hackathon-MAIN-alkademi\openspec\changes\lukla-ops-engine-planning\09-technical-blueprint-completion-plan.md`.
- Active task record: `C:\Projects\hackathon-MAIN-alkademi\openspec\changes\lukla-ops-engine-planning\task-record.md`, revision 12; it authorizes planning artifacts, contract work, and planning verification only. No application code, deployment, dependency installation, reset, stash, or commit is in scope.
- Canonical requirements to preserve: `C:\Projects\hackathon-MAIN-alkademi\openspec\changes\BRD - Lukla Operations Engine - v2.2.1 - FINAL.md`, `C:\Projects\hackathon-MAIN-alkademi\openspec\changes\PRD - Lukla Operations Engine - v2.0 - Wagile.md`, and the source register `C:\Projects\hackathon-MAIN-alkademi\openspec\changes\lukla-ops-engine-planning\00-deconstruction.md`.
- The PRD inventory is 26 IDs: 23 defined IDs plus `FR-1.4`, `FR-5`, and `FR-6`. The source register has 20 distinct source IDs. These are different coverage sets: do not force the 20-ID checker to represent the 26-ID PRD inventory, and do not invent definitions for unresolved `FR-1.4`, `FR-5`, or `FR-6`.
- The current checker is `C:\Projects\hackathon-MAIN-alkademi\openspec\changes\lukla-ops-engine-planning\artifacts\verify-traceability.ps1`; it checks legacy core documents, 20 IDs, roles, four scenarios, and unresolved echoes. It is not an OpenAPI validator or runtime test harness.
- The requested `research\blueprint-*` reports and several task-record-mentioned artifacts were not resolvable in the current filesystem inspection. Treat any recovered report as advisory only; reconcile it against the canonical BRD, PRD, register, and approved brief.
- Verified external constraints: PostgreSQL RLS can default-deny access and table owners/BYPASSRLS can bypass it, so tests must use a non-owner application role and explicitly force/test RLS. PostgreSQL `SET LOCAL` is transaction-scoped and is suitable for request tenant context when set inside the transaction. AWS documents EventBridge Scheduler invoking Lambda and API Gateway HTTP APIs invoking Lambda; the portable scheduled-job shape is **Scheduler -> Lambda -> authenticated application HTTP endpoint**, not “Scheduler -> HTTP” directly. Sources: `https://www.postgresql.org/docs/current/ddl-rowsecurity.html`, `https://www.postgresql.org/docs/current/sql-set.html`, `https://docs.aws.amazon.com/lambda/latest/dg/with-eventbridge-scheduler.html`, `https://docs.aws.amazon.com/lambda/latest/dg/services-apigateway.html`.
- `yaml` and `jsonschema` are installed. `openapi_spec_validator` is absent. Spectral and Schemathesis are not installed and must not be installed for this change. The plan must distinguish custom structural checks from those tools' future gates.

## Approach

1. Preserve canonical source documents and existing unrelated edits. Work only in the new blueprint deliverables, the explicitly requested narrow `.gitignore` allowlist, and tracking/spec files named below.
2. Execute A sequentially: define the database vocabulary and invariants, then define the OpenAPI contract against it. A is the parallelization gate.
3. Execute B in parallel after A review: authentication/authorization, UI, operations, test harness, semantic search, and business defaults. Each B document may refine provisional auth choices but must not change operation IDs, paths, schemas, or error codes without a contract change record.
4. Execute C sequentially: compose dependency-ordered workstreams, update OpenSpec tracking/spec deltas, extend the checker, and run planning-only verification.
5. Keep all financial values and unresolved rules configurable and marked `PROPOSED/PENDING-AUTHORIZATION`; production deployment is blocked until an authorized decision records the effective meal base, QC remainder treatment, recipient configuration, overhead basis, and payroll eligibility.
6. Model isolation as separate dimensions: `tenant_id` (commercial/workspace access), `legal_stock_owner_id` (custodial or Lukla legal owner), and `order_beneficiary_id` (the order/client entitled to the output). CMT, Semi-CMT, and Full Package must be representable without an implicit legal-title transfer.

## Exact Deliverables

### A — sequential contracts and persistence vocabulary

| Deliverable | Full path | Contract/interface required |
|---|---|---|
| Stack and portability decisions | `C:\Projects\hackathon-MAIN-alkademi\openspec\changes\lukla-ops-engine-planning\artifacts\10-technology-stack-and-decisions.md` | FastAPI + plain PostgreSQL baseline; portability rules; no provider-only APIs; Scheduler -> Lambda -> HTTP correction; no speculative version/pricing pins. |
| Database schema and invariant specification | `C:\Projects\hackathon-MAIN-alkademi\openspec\changes\lukla-ops-engine-planning\artifacts\11-database-schema-spec.md` | Tables, keys, indexes, migrations, tenant/owner/beneficiary columns, append-only ledger, RLS policy matrix, trigger/function signatures, transaction boundaries, and non-owner test role. |
| API contract explanation | `C:\Projects\hackathon-MAIN-alkademi\openspec\changes\lukla-ops-engine-planning\artifacts\12-api-contract-plan.md` | Endpoint catalog, role visibility, FR/view/scenario mapping, auth placeholder, state transitions, idempotency, pagination, and compatibility policy. |
| OpenAPI entry contract | `C:\Projects\hackathon-MAIN-alkademi\openspec\changes\lukla-ops-engine-planning\artifacts\contracts\openapi.yaml` | Machine-readable source of truth for all cross-workstream HTTP interfaces. Every operation has a unique `operationId`, tags, source IDs, role metadata, request/response schemas, examples, and known errors. |

A1 must not begin until the source-register/BRD/PRD path check and 26-versus-20 inventory reconciliation are recorded. A2 must not begin until A1 names the portability boundary and security assumptions. A3 must not begin until A2 names the database objects referenced by API schemas.

### B — parallel documents after the A3 review gate

| Deliverable | Full path | Contract/interface required |
|---|---|---|
| Authentication and authorization | `C:\Projects\hackathon-MAIN-alkademi\openspec\changes\lukla-ops-engine-planning\artifacts\13-authn-authz-design.md` | Provisional bearer/session decision, 8 roles, token claims-to-RLS context mapping, floor/tablet login, B2B provisioning, deny-by-default, owner/BYPASSRLS hazard, and no API break while auth is refined. |
| Frontend architecture | `C:\Projects\hackathon-MAIN-alkademi\openspec\changes\lukla-ops-engine-planning\artifacts\14-frontend-architecture.md` | Six views plus ledger surface; route-to-operationId table; loading/error/permission/offline states; idempotency for 30-minute tally submissions; browser accessibility and reduced-motion expectations. |
| Deployment and operations | `C:\Projects\hackathon-MAIN-alkademi\openspec\changes\lukla-ops-engine-planning\artifacts\15-deployment-and-operations.md` | AWS topology and portable pivots; authenticated scheduled endpoint flow; secrets, backups, observability, rollback, and environment gates. No NAT requirement is asserted for private RDS; network design must be decided from the selected topology, not from the discarded research claim. |
| Test harness and agent verification | `C:\Projects\hackathon-MAIN-alkademi\openspec\changes\lukla-ops-engine-planning\artifacts\16-test-harness-and-agent-verification.md` | API, database, system, and Playwright browser test plan; fixture identities; evidence bundle schema; deterministic AI review-orchestrator protocol; AT-01..AT-10, AT-R01..AT-R08, four closing scenarios, and all 26 PRD IDs mapped to test IDs. |
| Fenced semantic search | `C:\Projects\hackathon-MAIN-alkademi\openspec\changes\lukla-ops-engine-planning\artifacts\17-semantic-search-module.md` | Separate router/service boundary, `VectorStore` interface, tenant/legal-owner filtering, read-only access, feature flag, provider adapter, and deletion without ledger impact. |
| Business defaults register | `C:\Projects\hackathon-MAIN-alkademi\openspec\changes\lukla-ops-engine-planning\artifacts\19-business-defaults-register.md` | OQ-1..OQ-9 and all unresolved source items; proposed configurable defaults, owner, effective date, audit event, and explicit production-block status. No default becomes an approved BRD/PRD rule. |

### C — integration, tracking, and checker

| Deliverable | Full path | Contract/interface required |
|---|---|---|
| Parallel workstreams and handoff graph | `C:\Projects\hackathon-MAIN-alkademi\openspec\changes\lukla-ops-engine-planning\artifacts\18-parallelization-and-workstreams.md` | Dependency graph, workstream ownership, exact contract/database references, branch-safe boundaries, review handoffs, and stop conditions. |
| OpenSpec tracking/spec updates | `C:\Projects\hackathon-MAIN-alkademi\openspec\changes\lukla-ops-engine-planning\tasks.md`, `C:\Projects\hackathon-MAIN-alkademi\openspec\changes\lukla-ops-engine-planning\design.md`, and applicable `C:\Projects\hackathon-MAIN-alkademi\openspec\changes\lukla-ops-engine-planning\specs\*\spec.md` | Reflect only actually authored artifacts; add agent-verifiable-testing and semantic-search deltas if absent; correct portable-RLS wording; do not mark runtime implementation complete. |
| Extended planning checker | `C:\Projects\hackathon-MAIN-alkademi\openspec\changes\lukla-ops-engine-planning\artifacts\verify-traceability.ps1` | Preserve existing checks; add 26 PRD-ID presence in API mapping, 20 distinct source-ID preservation, 8 roles, 6 views, four scenarios, unresolved/default status, operationId uniqueness, and required evidence filenames. |
| Narrow persistence allowlist | `C:\Projects\hackathon-MAIN-alkademi\.gitignore` | Add only negated rules needed to retain the new deliverables under the existing broad `artifacts/` ignore; do not unignore existing artifacts globally and do not alter unrelated ignore behavior. |

## Contract Schema Conventions

- Use OpenAPI 3.1-compatible YAML for maximum installed-tool compatibility; do not pin a tool version. `openapi`, `info`, `paths`, and `components` are required; `$ref` targets must be local and resolvable. Use stable kebab-case paths, lowerCamelCase JSON properties, UUID identifiers, RFC 3339 timestamps, integer minor-unit money plus currency, explicit timezone, and string enums for business states.
- Use a reusable `Problem` error envelope: `type`, `title`, `status`, `code`, `detail`, `instance`, `requestId`, and optional `violations[]`. Stable `code` values include `AUTH_REQUIRED`, `FORBIDDEN`, `TENANT_CONTEXT_MISSING`, `LEGAL_OWNER_MISMATCH`, `ORDER_BENEFICIARY_MISMATCH`, `IDEMPOTENCY_CONFLICT`, `INVALID_STATE`, `LEDGER_IMMUTABLE`, `DUPLICATE_REPAIR_CREDIT`, `FINANCIAL_RULE_PENDING`, and `VALIDATION_ERROR`. Never expose SQL or provider details.
- Every write accepts `Idempotency-Key` where a retry could duplicate a tally, stock movement, QC decision, payroll run, or reversal. Replays return the original result; a different payload under the same key returns `409 IDEMPOTENCY_CONFLICT`.
- Every operation has a stable `operationId` such as `receiveMaterial`, `issueMaterial`, `recordCuttingResult`, `recordSewingTally`, `inspectUnit`, `runWeeklyPayroll`, `allocateMonthlyOverhead`, `getLedgerEntries`, and `searchOperationalDocuments`. Operation descriptions must include `x-source-ids` (all applicable PRD IDs), `x-roles`, `x-view`, and `x-invariant` annotations. Extensions are metadata only and must not replace validation.
- Common responses: `200/201` success, `202` only for explicitly asynchronous work, `400/422` malformed or schema-invalid input, `401` missing/invalid auth, `403` role or row-policy denial, `404` inaccessible/not found without cross-tenant leakage, `409` invariant/state/idempotency conflict, and `500` unexpected failure. Include errors in every operation rather than relying only on a generic default.
- Contract functions and database boundaries must be named, typed, and mapped: `set_request_context(tenant_id, actor_id, role, legal_owner_scope, beneficiary_scope)` transaction-local; `validate_material_dispatch(stock_lot_id, order_id)` rejects owner/beneficiary mismatch; `append_ledger_transaction(transaction_id, entries)` requires balanced debits/credits and never updates/deletes posted rows; `record_sewing_tally(..., idempotency_key)` creates a pending-QC unit; `classify_qc_unit(..., Pass|Repair|Reject)` ensures Repair cannot earn a second piece-rate credit; `calculate_weekly_payroll(period, rule_version)` refuses unresolved financial rules; `calculate_overhead_allocation(period, rule_version)` is configurable and auditable; `search_documents(query, tenant_scope, filters)` is read-only and fenced.
- Provisional auth must be explicit: document the selected bearer/session shape as a proposal, keep issuer/audience/key rotation and floor-device lifecycle as decision points, and pass only validated actor/role/scope context to PostgreSQL. The contract must not encode a provider-specific `auth.uid()` dependency.

## Test Mapping and Evidence Contract

The contract and harness must map:

- `FR-1.1`, `FR-2.1`, `FR-3.1` to tenant/RBAC/audit API and RLS/append-only tests.
- `FR-4.1..FR-4.3` to sample revision, time-study, lock, and transition tests.
- `FR-5.1`, `FR-5.2`, `FR-6.1..FR-6.3`, plus group IDs `FR-5` and `FR-6`, to inventory, custodial accounting, stocktake, dispatch rejection, and cutting-result tests; unresolved group definitions remain visibly unresolved.
- `FR-7.1..FR-7.4` to capacity, rate card, 30-minute tally, pending-QC, and conditional-pay tests.
- `FR-8.1`, `FR-8.2`, `FR-9.1`, `FR-9.2` to Pass/Repair/Reject, no double repair credit, bonus pool, and one shared divide-by-three rule test; `FR-9.2` and `FR-10.3` must not become two independent bonus rules.
- `FR-10.1..FR-10.4` to weekly payroll, configurable meal pool, shared QC bonus, and monthly overhead tests; financial defaults remain blocked pending authorization.
- Every test emits a stable test ID, source IDs, fixture identity, request correlation ID, expected result, actual result, and evidence paths. The minimum bundle is `results.json`, `results.xml`, `api-results.xml`, `db-results.xml`, `system-results.json`, and Playwright traces/screenshots on failure. The agent reads JSON/XML and exit status, never infers pass/fail from HTML.
- The harness must contain negative controls: cross-client material issue fails; missing tenant context fails; unauthorized role fails; ledger UPDATE/DELETE fails; duplicate Repair does not add pay; same idempotency key with altered payload fails; unresolved financial configuration blocks production approval; cross-tenant and cross-legal-owner reads do not leak.

## Phases

| Phase | Outcome | Likely files | Verification / expected output | Edge cases and stop conditions |
|---|---|---|---|---|
| 0. Baseline and inventory | Confirm inputs, preserve work, reconcile 26 PRD IDs against 20 source IDs, classify missing reports/artifacts. | Canonical BRD/PRD/register, task record, existing checker, git status. | `git status --short` records pre-existing state; PowerShell path checks print each required file as `PRESENT` or a named `MISSING`; a small Python/YAML inventory prints `PRD_IDS=26` and `SOURCE_IDS=20`. | Stop if canonical BRD, PRD, or register cannot be located, if the 26/20 counts cannot be reproduced, or if any proposed edit would rewrite a source document. |
| A1. Stack and persistence boundary | Publish portability decisions and database vocabulary/invariants. | `10-*`, `11-*`. | Markdown link/path check passes; schema inventory includes tenant, legal owner, beneficiary, ledger, RLS, trigger/function names; no NAT-required claim and no speculative pins/prices. | Stop on unresolved ownership semantics, missing ledger balance/immutability rule, or RLS design that relies on owner/BYPASSRLS access. |
| A2. OpenAPI contract | Publish the complete API proposal and machine-readable contract before parallel work. | `12-*`, `contracts/openapi.yaml`. | Python `yaml.safe_load` succeeds; custom structural validator reports `OPENAPI_STRUCTURE=PASS`, `OPERATION_IDS_UNIQUE=PASS`, `REFS_RESOLVABLE=PASS`, `PRD_IDS=26`, `SOURCE_IDS=20`; absent `openapi_spec_validator`, Spectral, and Schemathesis are reported as unavailable rather than simulated. | Stop on an unresolvable `$ref`, duplicate operationId, endpoint with no source mapping, missing error response, or any API change that silently transfers legal title. |
| A3. Contract review gate | Freeze a reviewed contract baseline and publish change policy. | Review record under `C:\Projects\hackathon-MAIN-alkademi\openspec\changes\lukla-ops-engine-planning\artifacts\review\blueprint-contract-review.md` (new). | `git diff --check` prints no output; contract review checklist names all blocking findings as closed or escalated. | Stop all B work if a critical schema, ownership, tenant isolation, or idempotency issue remains after the allowed two correction loops. |
| B1–B6. Parallel refinements | Produce auth, frontend, ops, harness, search, and business-default documents without breaking A. | `13-*` through `17-*`, `19-*`. | Cross-link checker reports every B document references operationIds and database object names; business register reports every unresolved item with `PROPOSED` and `PRODUCTION_BLOCKED`; harness reports all AT/scenario mappings. | Stop the affected workstream if it invents missing FR-1.4/FR-5/FR-6 behavior, changes API shape without a contract change, weakens scope filtering, or converts a proposed financial rule into an approval. |
| C1. Integration and workstreams | Make development split-ready with explicit dependencies and handoffs. | `18-*`, workstream table, tracking files. | Dependency graph has no unexplained cycles; every cross-workstream edge references an operationId or DB object; six UI views and all workstreams have owners, fixtures, and gates. | Stop if two workstreams own the same invariant, if a dependency is only prose, or if runtime implementation is marked complete during planning. |
| C2. Checker and persistence | Extend the existing checker and retain only new deliverables through a narrow ignore allowlist. | Existing `verify-traceability.ps1`, `.gitignore`. | Checker exit 0 prints named PASS sections for core docs, 26 PRD IDs, 20 source IDs, roles, views, scenarios, unresolved decisions, contract structure, and evidence names. A temporary negative copy with one ID removed exits 1 and names that ID. `git check-ignore -v` shows only intended new paths allowed; existing ignored artifacts remain ignored. | Stop if checker success depends on substring false positives, if the negative control does not fail, or if `.gitignore` broadens beyond the new deliverables. |
| C3. Final planning verification | Verify OpenSpec/tracking and document integrity only. | OpenSpec files, all new artifacts. | `openspec validate lukla-ops-engine-planning` exits 0; `openspec status --change lukla-ops-engine-planning` reports the expected artifact completion; `git diff --check` is empty; no application/runtime/browser/cloud test is claimed. | Stop and report exact failures if OpenSpec is unavailable, a source hash changes, or runtime evidence is requested; do not “fix” by modifying canonical BRD/PRD/register. |

## Verification Commands and Expected Output

Run from `C:\Projects\hackathon-MAIN-alkademi` after the corresponding phase:

```powershell
Get-Content '.\openspec\changes\lukla-ops-engine-planning\task-record.md' -TotalCount 12
# Expected: Revision 12 and planning-only scope are visible.

python -c "import yaml, jsonschema; print('yaml=installed jsonschema=installed')"
# Expected: yaml=installed jsonschema=installed

python .\openspec\changes\lukla-ops-engine-planning\artifacts\validate-blueprint.py
# Expected after C2: STRUCTURE=PASS; PRD_IDS=26; SOURCE_IDS=20; REFS=PASS; OPERATION_IDS=PASS; exit 0.
# This is a custom structural check, not Spectral, Schemathesis, or openapi_spec_validator.

pwsh -NoProfile -File .\openspec\changes\lukla-ops-engine-planning\artifacts\verify-traceability.ps1
# Expected after C2: all named checks PASS and exit code 0; warnings must be explicit and non-blocking.

openspec validate lukla-ops-engine-planning
# Expected: valid / zero errors.

openspec status --change lukla-ops-engine-planning
# Expected: status reflects only artifacts actually authored; no runtime implementation checkbox is marked complete.

git diff --check
# Expected: no output and exit code 0.
```

The plan author must not claim a successful Spectral lint, Schemathesis run, Playwright run, API runtime test, database integration test, browser test, cloud deployment, cost validation, or `openapi_spec_validator` result unless those tools are later installed/available and actually run. No dependency installation is part of this change.

## Acceptance Criteria

- A, B, and C deliverables exist at the exact paths above, with no canonical BRD, PRD, register, source image, or unrelated edit rewritten.
- The OpenAPI contract is parseable, locally referenced, operationId-unique, source-mapped, error-complete, and usable by parallel frontend/backend work without an unstated interface question.
- The 26-ID PRD inventory and 20-ID distinct source inventory are both preserved and separately checked; unresolved group IDs are not given invented behavior.
- Tenant access, legal stock ownership, and order beneficiary are distinct in schema, API, RLS, fixtures, and tests for CMT, Semi-CMT, and Full Package.
- Immutable double-entry behavior, material dispatch validation, repair no-double-pay, idempotency, and audit behavior have named functions and negative tests.
- The AI review-orchestrator can decide pass/fail from deterministic exit status and machine-readable evidence, including browser, API, system, and database evidence, without HTML interpretation.
- Auth remains a documented provisional decision that can be refined without breaking the contract.
- All configurable financial defaults are clearly proposed and production-blocked pending authorized decision.
- The final verification report states exactly which commands ran and which runtime checks did not run.

## Non-Goals

- No application code, migrations, frontend implementation, Terraform, cloud deployment, dependency installation, generated client, or runtime test execution in this planning task.
- No rewrite, translation, cleanup, or “correction” of BRD, PRD, source register, or existing user artifacts.
- No invented FR-1.4, FR-5, or FR-6 semantics; no unsupported NAT requirement; no speculative version or pricing pins.
- No statutory payroll, full accounting, MRP, logistics, mobile-native application, or unrequested AI autonomy.

## Risks

- **Missing files versus task-record claims:** reconcile by path checks and preserve a named missing-input report; do not recreate or overwrite silently.
- **RLS false confidence:** owner and BYPASSRLS roles can bypass policies; use a restricted application role and negative cross-scope tests.
- **Legal-title ambiguity:** keep legal stock owner and order beneficiary independent; block dispatch when the rule cannot prove compatibility.
- **Auth refinement drift:** make auth provisional in B and require contract compatibility review before any change.
- **Tooling ceiling:** custom YAML/JSON/schema/reference checks can prove structure only; they cannot substitute for Spectral style rules, Schemathesis generated runtime tests, or browser execution.
- **Financial harm:** configurable defaults are not approvals; production and release gates remain blocked until authorized decisions are recorded.

## Implementation Handoff

- Scope: execute Phase 0, then A1 → A2 → A3; only after the A3 review gate execute B in parallel, then C.
- Inspect first: the exact canonical paths in Current Reality, the task record revision 12, the approved design brief, the existing checker, `.gitignore`, and current `git status --short`.
- Tests: use the commands in “Verification Commands and Expected Output”; add the custom validator only as a planning verification artifact, without installing dependencies.
- Stop if: any canonical source is missing or would be rewritten, counts 26/20 cannot be reproduced, contract ownership/RLS semantics are unresolved, checker negative controls do not fail, proposed defaults are treated as approved, or a requested phase would require application/runtime/cloud implementation.
- Completion boundary: stop after C3 with a concise report of the exact output observed. Do not reset, stash, commit, archive, or claim runtime readiness.
