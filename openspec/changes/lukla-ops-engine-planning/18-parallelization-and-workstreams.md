# 18 — Phase C Parallelization and Workstreams

**Change:** `lukla-ops-engine-planning`  
**Baseline:** task-record revision 16; Phase B review `blueprint-phase-b-review.md` APPROVED  
**Scope:** planning integration only. No application code, dependency installation, runtime, database, cloud, or test execution is authorized by this artifact.

## 1. Phase C entry contract

Phase C starts only after these inputs are present and internally consistent:

- `proposal.md`, `design.md`, `tasks.md`, and all six `specs/**/spec.md` capability files.
- Phase A contract sources: `artifacts/contracts/openapi.yaml`, `artifacts/10-technology-stack-and-decisions.md`, `artifacts/11-database-schema-spec.md`, and `artifacts/12-api-contract-plan.md`.
- Phase B surfaces: `artifacts/13-authn-authz-design.md`, `artifacts/14-frontend-architecture.md`, `artifacts/15-deployment-and-operations.md`, `artifacts/16-test-harness-and-agent-verification.md`, `artifacts/17-semantic-search-module.md`, and `artifacts/19-business-defaults-register.md`.
- Approved review: `artifacts/review/blueprint-phase-b-review.md`.
- The six learn-note resolutions in §2 are reflected before a workstream is marked ready.

The contract remains planning evidence. It is not runtime evidence, and no workstream may convert a proposed business default or unresolved source item into production behavior.

## 2. Phase B learn-note resolutions

1. **Service authentication terminology:** use `serviceAuth` / bearer `service-token` as the contract term. The prose in artifacts 13 and 15 identifies `X-Service-Principal` only as optional, non-authoritative metadata; the bearer service credential remains the authentication mechanism.
2. **RLS enforcement:** artifact 15 names `ENABLE` and `FORCE ROW LEVEL SECURITY` for tenant-scoped tables and points to artifact 11 §6 and §9 for the matrix and non-owner negative control.
3. **Ledger reversal:** artifact 15 names `reverseLedgerTransaction`; reversal is a compensating transaction and never a delete of posted history.
4. **Pending financial rule:** artifact 19 names `FINANCIAL_RULE_PENDING`; payroll/QC/financial flows remain blocked while a referenced rule is `UNRESOLVED / PRODUCTION_BLOCKED`.
5. **File ACL provenance:** artifact 17 states that `getFileDownload` and upload completion are not semantic-search sources unless an explicit classification is approved; indexed files carry tenant, legal-owner, beneficiary, source ACL, and provenance fields, and otherwise remain excluded.
6. **Dependencies:** the graph and briefs below make Phase C dependencies explicit. A downstream brief cannot claim readiness from a prose reference alone; its named artifact and operation checks must pass.

## 3. Dependency graph and branch boundaries

```text
Frozen sources (00, BRD/PRD, 04, 06, 08)
        |
        v
A: contract + database seams (10, 11, 12, OpenAPI)
        |
        +--> B: identity/RLS/service boundary (13, 15)
        +--> C: frontend routes/views (14, 16)
        +--> D: verification/search/default gates (16, 17, 19)
        |
        +---- B + C + D ----> integration: design/tasks/spec deltas + verifier
                                      |
                                      v
                                review handoff / Phase D gate
```

Branch-safe boundaries:

- Dev 1 edits only `artifacts/14-frontend-architecture.md` and assigned planning notes; it does not edit OpenAPI schemas or database policy.
- Dev 2 edits only touch-floor portions of `artifacts/14-frontend-architecture.md` and matching harness references in `artifacts/16-test-harness-and-agent-verification.md`; it does not alter payroll rules.
- Dev 3 edits only auth, operations, and database/RLS planning surfaces: artifacts 10, 11, 12, 13, and 15. Contract changes require the Phase A review reopen rule.
- Dev 4 edits only artifacts 16, 17, and 19 plus verifier/report files. It does not change frozen requirements or public operation semantics.
- The integration owner edits `design.md`, `tasks.md`, `specs/**/spec.md`, and this artifact. These files are merge-conflict hotspots and are integrated after workstream review, not concurrently.

No branch may edit frozen canonical source files, rewrite ignored-artifact policy broadly, or add dependencies.

## 4. Four developer briefs

### Dev 1 — Admin, warehouse, and portal planning

**Inputs:** artifacts 04, 10, 11, 12, 14; operations `listClients`, `createClient`, `createOrder`, `getOrder`, `listOrders`, `receiveMaterial`, `issueMaterial`, `getStock`, `getPortalOrderStatus`, `getFileDownload`.

**Deliverable:** reconcile admin/warehouse/portal route ownership, view IDs, role tags, tenant/legal-owner/beneficiary filters, and file-download provenance in planning artifacts only.

**Database references:** `clients`, `orders`, `order_components`, `material_lots`, `material_movements`, `file_uploads`, `file_objects`, `search_documents`; RLS matrix in artifact 11 §9.

**Stop conditions:** stop and hand off if FR-1.4, FR-5/FR-6 semantics, client ownership, or an operation's required schema is unresolved. Do not invent behavior or amend OpenAPI unilaterally.

### Dev 2 — Touch-floor production and QC planning

**Inputs:** artifacts 04, 06, 12, 14, 16; operations `listLines`, `assignOperator`, `recordSewingTally`, `verifySewingTally`, `createAssembly`, `listAssemblies`, `inspectUnit`, `getBonusPool`.

**Deliverable:** reconcile 30-minute tally capture, dynamic headcount, component attribution, assembly-to-QC staging, repair routing, and agent-verifiable touch-terminal scenarios.

**Database references:** `lines`, `assignments`, `operators`, `tallies`, `component_units`, `assemblies`, `inspections`, `defects`, `eligibility_events`, `bonus_accruals`.

**Stop conditions:** stop on any double-credit path, missing source contributor, ambiguous QC disposition, or mismatch with AT-04/AT-05/AT-08/AT-09. Do not resolve the bonus remainder or other business defaults.

### Dev 3 — Backend, PostgreSQL, and RLS planning

**Inputs:** artifacts 10, 11, 12, 13, 15; OpenAPI `securitySchemes`, all mutation operation IDs, and migration/RLS sections.

**Deliverable:** produce the implementation-ready boundary list for request context, `serviceAuth`, `FORCE ROW LEVEL SECURITY`, transaction/outbox order, idempotency, append-only ledger, and migration gates.

**Database references:** `set_request_context`, `ENABLE/FORCE ROW LEVEL SECURITY`, `ledger_transactions`, `ledger_lines`, `audit_events`, `outbox_events`, `idempotency_records`, `job_runs`, and migrations M001–M013.

**Stop conditions:** stop on any owner/BYPASSRLS assumption, missing tenant/legal-owner/beneficiary predicate, operationId change, or unreviewed schema change. Route public-contract changes through the Phase A review reopen rule.

### Dev 4 — Payroll, search, verification, and DevOps planning

**Inputs:** artifacts 15, 16, 17, 19; OpenAPI operations `calculateWeeklyPayroll`, `approvePayroll`, `recordPayrollPayment`, `runSaturdayPayrollJob`, `runMonthlyOverheadJob`, `searchOperationalDocuments`.

**Deliverable:** reconcile production-blocked defaults, `FINANCIAL_RULE_PENDING`, search ACL/provenance exclusion, evidence filenames, harness counts, and verifier assertions.

**Database references:** `financial_rule_versions`, `payroll_runs`, `payroll_run_credits`, `payroll_items`, `payroll_payments`, `overhead_periods`, `search_documents`, `search_chunks`, and `job_runs`.

**Stop conditions:** stop if an unresolved OQ is treated as approved, a search result bypasses source ACL/RLS, evidence is missing, or an operationId is duplicated. No runtime/provider/cloud test is claimed.

## 5. Review handoffs and integration order

1. Each developer returns a file list, source/operation/database references checked, unresolved items, and a verification transcript.
2. The integration owner compares changes against this graph, the Phase B review, and frozen-source hashes before editing root OpenSpec artifacts.
3. The verifier runs on the integrated tree, then a negative copy removes one PRD ID and must exit 1 without modifying the working tree.
4. Review receives the implementation report, verifier output, OpenSpec validation output, YAML/catalog output, and `git diff --check` output. Review must distinguish planning structure from runtime evidence.

## 6. Phase C stop conditions

Stop Phase C and escalate rather than guessing when: a frozen source changes; an operationId, role, view, schema, or ownership dimension changes; any OQ becomes approved without business evidence; `FINANCIAL_RULE_PENDING` or `PRODUCTION_BLOCKED` is removed; verifier negative control passes unexpectedly; or OpenSpec validation fails.

## 7. Traceability

- Product requirements: `00-deconstruction.md`, `Lukla Operations Engine - BRD v2.2.1 - FINAL.md`, `lukla_PRD_V.1.0.md`, `04-rbac-matrix.md`, `06-acceptance-tests.md`, `08-client-clarification-register.md`.
- Contract: `artifacts/contracts/openapi.yaml`, `artifacts/12-api-contract-plan.md`.
- Persistence/security: `artifacts/10-technology-stack-and-decisions.md`, `artifacts/11-database-schema-spec.md`, `artifacts/13-authn-authz-design.md`, `artifacts/15-deployment-and-operations.md`.
- Verification/search/defaults: `artifacts/16-test-harness-and-agent-verification.md`, `artifacts/17-semantic-search-module.md`, `artifacts/19-business-defaults-register.md`.