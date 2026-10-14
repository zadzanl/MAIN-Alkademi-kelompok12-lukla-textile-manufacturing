# Blueprint Phase A — Recovery Inspection

**Change:** `lukla-ops-engine-planning`
**Task record revision:** 12 (2026-10-13)
**Inspection mode:** read-only; no subagents dispatched; no source files modified.
**Approved scope reference files:** `09-technical-blueprint-completion-plan.md` (root09) and `artifacts/tech_plan-blueprint-001.md`. User instruction verbatim: "Plan looks good. Please proceed with implementation." — restricted to planning documents, OpenAPI contract, and planning verification.
**Recovery context:** prior Phase A sequential dispatch reported a `provider server_error` (server-side overloaded), but artifacts `10`/`11`/`12` and `contracts/openapi.yaml` exist on disk. The Phase A close-out record `artifacts/implementation/blueprint-phase-a.md` is missing.

## 1. Environment and actual worklog

Working directory: `C:\Projects\hackathon-MAIN-alkademi`
Shell: PowerShell (pwsh), Python 3 with `yaml`/`jsonschema` installed (verified by an earlier `tech_plan-blueprint-001.md` baseline note)
Filesystem snapshot (relevant subset):

```
openspec\changes\lukla-ops-engine-planning\proposal.md
openspec\changes\lukla-ops-engine-planning\design.md
openspec\changes\lukla-ops-engine-planning\task-record.md       (rev 12)
openspec\changes\lukla-ops-engine-planning\09-technical-blueprint-completion-plan.md
openspec\changes\lukla-ops-engine-planning\.openspec.yaml
openspec\changes\lukla-ops-engine-planning\artifacts\10-technology-stack-and-decisions.md   (5648 bytes)
openspec\changes\lukla-ops-engine-planning\artifacts\11-database-schema-spec.md            (17209 bytes)
openspec\changes\lukla-ops-engine-planning\artifacts\12-api-contract-plan.md                (6266 bytes)
openspec\changes\lukla-ops-engine-planning\artifacts\contracts\openapi.yaml                 (53312 bytes)
openspec\changes\lukla-ops-engine-planning\artifacts\tech_plan-blueprint-001.md            (25349 bytes)
openspec\changes\lukla-ops-engine-planning\artifacts\implementation\blueprint-phase-a.md   (MISSING)
openspec\changes\lukla-ops-engine-planning\artifacts\review\blueprint-contract-review.md   (NOT YET)
```

Actual commands executed by this recovery session (verbatim):

1. `Get-ChildItem <change>/artifacts -File` (sorted, sizes) — verified three named artifacts at the byte sizes reported.
2. `Get-ChildItem <change> -Recurse -File` with relative paths — mapped the change layout; located `contracts/openapi.yaml` and confirmed absence of `implementation/blueprint-phase-a.md`.
3. `read_file` on task-record.md (lines 1..300) — confirmed revision 12 and the Phase A sequential scope (`A1.stack → A2.schema → A3.api+openapi`).
4. `read_file` on `proposal.md` — captured the 6 capability names.
5. `read_file` on `09-technical-blueprint-completion-plan.md` — captured the Phase A→B→C plan and the §3 non-negotiables.
6. `read_file` on `\.openspec.yaml` — confirmed `schema: spec-driven`.
7. `read_file` on `artifacts/10-technology-stack-and-decisions.md` (full, 300 lines).
8. `read_file` on `artifacts/12-api-contract-plan.md` (full, 500 lines).
9. `read_file` on `artifacts/11-database-schema-spec.md` (full, 600 lines).
10. `read_file` on `artifacts/contracts\openapi.yaml` (lines 1..800, full scope of paths + components).
11. `read_file` on `artifacts/tech_plan-blueprint-001.md` (lines 1..200) — verified Phase A2 acceptance: structured validator expected output, A3 contract review gate.
12. Wrote a Python script at `C:\Users\lenovo\AppData\Local\Temp\recovery-parse\parse_openapi.py` (not a project file) mirroring the prior orchestrator's isolated-temp practice for the negative harness in rev 11. Ran it twice (one fix for a `TypeError` on `dict.keys()` iteration).
13. Wrote a second Python script `parse_openapi_2.py` for schema-level cross-checks. Ran once. Both deleted workspace side effects are confined to `%TEMP%`; no project files were modified.

No edits were applied to any file under `openspec/`. The only persistent file written by this session is this recovery document, at the path explicitly requested by the user.

## 2. Phase A artifact-by-artifact findings

### 2.1 `artifacts/10-technology-stack-and-decisions.md` (5648 B)

- **Size check vs content**: 5.6 KB is consistent with five decision sections plus a coherent §5 exit criteria. No truncation; no obvious TODO placeholders.
- **Boundary declared (§1)**: "It does not rewrite any of those documents." Reads as canonical of `BRD v2.3.0`/`PRD v2.0`/`00-deconstruction.md rev 4` without touching them.
- **26 IDs vs 20 IDs reconciliation**: handled explicitly in §1, including the group/status IDs `FR-1.4`, `FR-5`, `FR-6` being `status-only`. Matches what `verify-traceability.ps1` checks and what `tech_plan-blueprint-001.md` requires.
- **Decisions table (§2)**: covers API / store / tenant context / files / vectors / models / web / jobs / test. None pins a version, price, or CVE. The job decision correctly bounds the schedule shape as `EventBridge Scheduler → Lambda → HTTPS POST`, not Scheduler-direct-to-HTTP (matches tech_plan §Current Reality correction).
- **Three-scope rule (§4.1)**: "tenant_id is access scope; legal_stock_owner_id is legal title/custody; order_beneficiary_id is the party entitled to order output. They are never silently copied into one field." This rule is later visible and consistent in artifact 11 and the openapi `ActorContext` schema (verified in §3 of this report).
- **Financial gate (§4.5)**: "Financial rules are configurable but unresolved rules carry `FINANCIAL_RULE_PENDING` and block production payroll approval. Demo defaults are not approvals." Aligned with `tech_plan-blueprint-001.md` §Current Reality and root09 §7.
- **A1 exit criteria**: present in §5. Maps cleanly into A2/A3 outputs (verified below).

Verdict: A1 is **complete and consistent** with the planning-only scope.

### 2.2 `artifacts/11-database-schema-spec.md` (17209 B)

- **Size check vs content**: 17 KB matches six tables of column lists plus four prose sections; no truncation.
- **Identity / access / commercial model (§2)**: tables `tenants`, `actors`, `actor_memberships`, `scope_grants`, `clients`, `orders`, `order_components`. The `scope_grants` table holds all three scopes (`tenant_id`, `legal_stock_owner_id`, `order_beneficiary_id`) explicitly — the canonical three-scope rule from artifact 10 §4.1 is realized at schema level.
- **Sample / production / stock (§3)**: tables `samples`, `sample_revisions`, `time_studies`, `rate_cards`, `material_lots`, `stock_movements`, `cut_batches`, `sewing_lines`, `operator_assignments`, `sewing_tallies`, `garment_units`, `garment_assemblies`, `assembly_components`, `qc_inspections`. **Whole garment linkage**: `garment_units` is per-component, `garment_assemblies` carries the whole-garment serial, and `assembly_components` allocates one or more `garment_unit_id` rows into each assembly with the rule "QC applies to the assembly serial only after required component quantities are allocated." The `qc_inspections.garment_unit_id` identifies the assembly serial's accountable source unit at the QC boundary — the half-garment → whole-garment QC transition. The `allocate_component` function locks assembly + source unit and enforces that allocated quantity cannot exceed remaining tally-backed quantity.
- **Ledger / payroll / procurement / files (§4)**: tables `ledger_accounts`, `ledger_transactions`, `ledger_entries`, `piece_rate_snapshots`, `payroll_periods`, `wage_credits`, `qc_bonus_accruals`, `payroll_adjustments`, `financial_rule_versions`, `overhead_events`, `purchase_orders`, `purchase_order_lines`, `supplier_invoices`, `file_objects`, `audit_events`, `idempotency_records`, `outbox_events`. Ledger immutability stated in §4 ("no UPDATE/DELETE"). `idempotency_records` unique constraint is `(tenant_id, key, operation_id)` — same shape as artifact 12 §2.
- **Functions & triggers (§5)**: `set_request_context`, `validate_material_dispatch`, `append_ledger_transaction`, `record_sewing_tally`, `classify_qc_unit`, `calculate_weekly_payroll`, `calculate_overhead_allocation`, `allocate_component`. Names exactly match artifact 12 §4 invariants. Payroll refusal rule on `PENDING` rule versions and `NO_OUTPUT` is stated in prose.
- **RLS (§6)**: `ENABLE ROW LEVEL SECURITY` + `FORCE ROW LEVEL SECURITY` policy required; tested as a non-owner role with explicit negative control. Transaction-pooling GUC leakage addressed (§6).
- **Migration ordering (§1, §7)**: §1 mentions migrations must run in dependency order and be reversible except for the immutable-ledger protection which is forward-only; §7 names what must commit together. **No explicit numbered migration list (M1, M2, …)** is provided — this is a gap relative to root09 AC-2 ("migration ordering"). Acceptable for Phase A close-out; can be authored in C1 (parallel workstreams) or as a small extension of artifact 11. Not a stop-condition per `tech_plan-blueprint-001.md` Phase A2.

Verdict: A2 is **complete with one acceptable deferral** (explicit migration sequence). No truncation; no fabricated columns.

### 2.3 `artifacts/12-api-contract-plan.md` (6266 B)

- **Size check vs content**: 6.3 KB matches five tight sections plus an endpoint catalog table. Compact but complete.
- **§1 protocol baseline**: HTTPS JSON, OAuth2/OIDC-compatible bearer at `Authorization: Bearer`, opaque refresh at `/auth/refresh`. Identity-provider choice deferred to Phase B (artifact 13) — matches artifact 10 §2 "API" row ("ASGI deployment and standard HTTP only").
- **§2 stable error/paging contract**: lists the 13 codes. All 13 are also present in the `openapi.yaml` `Problem.code` enum (verified in §3 of this report). Idempotency scoping text `(authenticated tenant, operationId, key)` matches the schema's `idempotency_records` unique key.
- **§3 endpoint catalog**: 42 operation IDs declared in 10 areas. The catalog table indicates one operation ID `listLedgerEntries` for the ledger entries list — but the actual `contracts/openapi.yaml` operationId is `getLedgerEntries`. This is the **single textual discrepancy** found in Phase A; only §3 of artifact 12 needs correction. Path is `/ledger/entries` and matches artifact 12's intent.
- **§4 state machines**: order flow `DRAFT → CONFIRMED → IN_PRODUCTION → QC → COMPLETED|CANCELLED`; tally → `MENUNGGU_QC` → `QC_PASS`/`REWORK`/`REJECT_SCRAP`. Procurement PO `DRAFT|APPROVED|RECEIVED|CANCELLED`. Sample `DRAFT|SUBMITTED|APPROVED|LOCKED`. All four are mirrored in the openapi schemas (verified §3 of this report).
- **§5 compatibility**: rename/removal of an operation, required-fields change, enum/state change, idempotency-scope change, or merging the three-scope fields all require a versioned contract change record.

Verdict: A3 is **complete aside from one naming inconsistency** in the §3 catalog table.

### 2.4 `artifacts/contracts/openapi.yaml` (53312 B)

- **YAML parse**: `yaml.safe_load` succeeded. `openapi: 3.1.0`, title `Lukla Operations Engine API`. No exceptions.
- **Path and operation count**: 40 path entries; **42 operations** (multiple paths have both GET and POST or PUT).
- **Operation ID uniqueness**: zero duplicates (verified by `set([x for x in ids if ids.count(x) > 1])`).
- **`$ref` resolution**: every `$ref` of kind `schemas|parameters|responses|securitySchemes` resolves locally. No missing references.
- **Source-ID coverage**: 26 unique `x-source-ids` (`FR-1.1`, `FR-1.4`, `FR-2.1`, `FR-3.1`, `FR-4.1..4.3`, `FR-5`, `FR-5.1`, `FR-5.2`, `FR-6`, `FR-6.1..6.3`, `FR-7.1..7.4`, `FR-8.1`, `FR-8.2`, `FR-9.1`, `FR-9.2`, `FR-10.1..10.4`). The full 26-ID PRD inventory is present; the full 20-ID traceability set is present. Every mutating operation has at least one `x-source-ids` entry.
- **Idempotency**: `Idempotency-Key` header is bound (minLength 16, maxLength 200, required). 26 mutating operations reference `/components/parameters/IdempotencyKey`. The 4 without are `login`, `refreshSession`, `logout`, `createClient` — session-establishing or non-duplicate-risk endpoints (`createClient` returns 409 Conflict when the unique `tenantCode` exists, so retry without Idempotency-Key is safe and idempotency-of-effect is preserved by the constraint, not by replay storage).
- **Roles**: `x-roles` enumerates `Owner`, `SampleTeam`, `Warehouse`, `ProductionHead`, `Tailor`, `QCInspector`, `FinancePayroll`, `MaklonClient` (= the 8 canonical roles from `04-rbac-matrix.md`). It also enumerates 3 non-canonical scopes: `Authenticated`, `ServicePayrollJob`, `ServiceOverheadJob`. The latter two are the dedicated scopes for `/internal/jobs/*` and are correctly paired with the `serviceAuth` security scheme (separate from the employee `bearerAuth`). `Authenticated` is the catch-all on `refreshSession`, `logout`, `getMyContext`. No canonical role is missing.
- **Views**: `x-view` enumerates `VIEW-01..VIEW-06` plus `all`. The 6 PRD views are referenced; nothing missing.
- **Three-scope model in schemas**:
  - `OrderRequest.required` includes `orderNumber`, `beneficiaryTenantId`, `scheme`, `timezone`, `cutoffLocal` ✓
  - `MaterialReceiptRequest.required` includes `legalStockOwnerId` AND `orderBeneficiaryId` ✓ (parallel fields enforced)
  - `ActorContext.required` includes `tenantScopes`, `legalOwnerScopes`, `beneficiaryScopes` (three separate arrays) ✓
  - `ActorContext.properties` exposes all three scopes; no field collapses them.
- **Auth**:
  - Two security schemes: `bearerAuth` (JWT) and `serviceAuth` (service-token).
  - `/auth/login` and `/auth/refresh` declare `security: []` (anonymous access allowed).
  - `/internal/jobs/saturday-payroll` and `/internal/jobs/monthly-overhead` declare `security: [{serviceAuth: []}]`, not `bearerAuth`. Service scope correctly isolated from employee roles.
  - All other operations inherit the document-level `security: [{bearerAuth: []}]`.
- **Idempotency**:
  - `Idempotency-Key` parameter defined in `components.parameters` (minLength 16, maxLength 200, required).
  - List/get operations properly omit Idempotency-Key.
  - Stable error code `IDEMPOTENCY_CONFLICT` declared in `Problem.code` enum.
- **Financial gates**:
  - `FINANCIAL_RULE_PENDING` declared in `Problem.code` enum.
  - `PayrollResult.status` enum: `CALCULATED | NO_OUTPUT | PENDING_RULE` — all three states from artifact 11 are exposed.
  - `calculateWeeklyPayroll`, `getBonusPool`, `calculateOverhead` all reference the `FinancialRulePending` response.
- **QC and whole-garment state mapping**:
  - `QcRequest.disposition` enum: `PASS | REPAIR | REJECT` ✓
  - `ProgressItem.status` enum: `MENUNGGU_QC | QC_PASS | REWORK | REJECT_SCRAP` — maps cleanly to artifact 11 `garment_units.status` (matches the schema definition that "PATCH without reuse" applies to repair and "REJECT_SCRAP" to reject) and exposes the whole-garment-level status to the production board.
- **Stable `x-invariant` per operation**: 42/42 operations carry an `x-invariant` annotation. The A2 acceptance criterion "Each operation has source IDs, roles, view, and invariant metadata" is met.
- **Error response coverage**: every operation references at least one `Problem`-form response. The 13 codes are all declared; the 8 response components (`AuthRequired`, `Forbidden`, `ServiceScopeRequired`, `ValidationError`, `Conflict`, `InvalidState`, `FinancialRulePending`, `NotFound`) are all referenced by ≥1 operation. No missing response references.

Verdict: `openapi.yaml` is **structurally complete**. Parses cleanly, all `$ref`s resolve, all 26 PRD IDs covered, all 8 roles covered, all 6 views covered, three-scope model is enforced at `OrderRequest` + `MaterialReceiptRequest` + `ActorContext` simultaneously, idempotency header is bound and applied broadly, financial gates exposed via `PayrollResult.status` + `FinancialRulePending` response code, ledger immutability exposed via `LEDGER_IMMUTABLE` error code, dual auth schemes (employee bearer + service) properly partitioned.

## 3. Cross-deliverable alignment (the user's five foci)

### 3.1 Tenant / owner / beneficiary

- Schema (`artifact 11 §2`, §3):
  - `tenants.tenant_id` (access)
  - `clients.tenant_id`, `orders.tenant_id`, `material_lots.tenant_id` (commercial record access)
  - `orders.beneficiary_tenant_id` (output entitlement)
  - `material_lots.legal_stock_owner_id` (custody / title)
  - `scope_grants` carries an explicit tuple `(actor_id, tenant_id, legal_stock_owner_id, order_beneficiary_id, capability)` — granting never silently merges dimensions.
- API (`openapi`):
  - `OrderRequest` requires `beneficiaryTenantId` separate from `tenantId` ✓
  - `MaterialReceiptRequest` requires `legalStockOwnerId` AND `orderBeneficiaryId` as parallel required fields ✓
  - `ActorContext` returns three arrays: `tenantScopes`, `legalOwnerScopes`, `beneficiaryScopes` ✓
- Plan (`artifact 10 §4.1`): rule stated in prose.
- All three documents converge. No merge, no shorthand. **PASS.**

### 3.2 Whole garment linkage

- Schema (`artifact 11 §3`): `garment_units` (per component) → `garment_assemblies` (whole-garment `serial_code`) → `assembly_components` (one or more `garment_unit_id` per assembly) → `qc_inspections.garment_unit_id` (whole-garment QC keyed to the assembly's accountable source unit).
- Function (`allocate_component`): locks assembly + source unit; checks identical order/tenant/component; refuses exceed-tally quantity; uniqueness prevents duplicate allocation.
- Rule (artifact 11 §5): "QC applies to the assembly serial only after required component quantities are allocated. `qc_inspections.garment_unit_id` identifies that finished serial's accountable source unit; the implementation must reject a serial without the assembly/component chain."
- API (`openapi`): `QcRequest.garmentUnitId`, `ProgressItem.status` exposes `MENUNGGU_QC | QC_PASS | REWORK | REJECT_SCRAP` at the assembly granularity.
- The half-component → whole-assembly → QC flow is consistent. **PASS.**

### 3.3 Auth

- API: dual security schemes (`bearerAuth` JWT for employees, `serviceAuth` service-token for internal jobs). `login` and `refreshSession` permit anonymous access; everything else requires `bearerAuth`; the two `/internal/jobs/*` endpoints require `serviceAuth` exclusively.
- Plan: artifact 10 §2 "API" row and artifact 12 §1 explicitly defer issuer/audience/key-rotation/floor-device enrollment to Phase B (artifact 13).
- Schema: `actor_memberships` + `scope_grants` + `set_request_context` are the basis for fed-and-validated scopes.
- The app-side hook for §3.1/§3.2 depends on this. Provider choices are deliberately left open. **PASS** (out of scope for Phase A by design).

### 3.4 Idempotency

- Schema: `idempotency_records` table with unique `(tenant_id, key, operation_id)`, `canonical_payload_hash bytea`, `response_status`, `response_body`. Same hash returns stored response; different hash returns `IDEMPOTENCY_CONFLICT`. Lease/explicit retry state described in §5.
- API: `Idempotency-Key` header is required for 26 mutating operations (parameter minLength 16, maxLength 200, `required: true`).
- Plan (artifact 12 §2): "(authenticated tenant, operationId, key), never by key alone"; canonical JSON encoding after stripping transport-only headers and normalizing property order; owner/beneficiary included in the hash so a replay cannot change legal meaning.
- Schema: §5 says "Canonical idempotency payload bytes are a sorted-key JSON encoding with normalized decimal strings, UTC timestamps, and explicit owner/beneficiary IDs; hash with SHA-256."
- Header, table key, hash policy, and error code are all consistent. **PASS.**

### 3.5 Financial gates

- Schema: `financial_rule_versions.status` 'PENDING'; payroll refuses approval when any required rule is PENDING; `PayrollPeriods.status` includes `PENDING_RULE`; `payroll_adjustments` require authorized adjustment with reason (no automatic QC-reject deductions).
- API: `Problem.code` enum includes `FINANCIAL_RULE_PENDING`. `PayrollResult.status` enum `CALCULATED | NO_OUTPUT | PENDING_RULE`. `calculateWeeklyPayroll`, `getBonusPool`, `calculateOverhead` all reference `FinancialRulePending` response component.
- `BonusPool.recipients` is `minItems: 3, maxItems: 3` — implements the "FR-9.2 and FR-10.3 are one divide-by-three rule, not two bonuses" invariant from artifact 12 §4 (the mechanism keeping a single pool rather than parallel arithmetic).
- `OverheadAllocation.amountPerUnit` plus zero-output handling — `PayrollResult.status` includes `NO_OUTPUT` to defend against divide-by-zero without bumping an error.
- Plan: artifact 10 §4.5 names the gate. artifact 12 §4 names it. artifact 11 §5 names it in prose. openapi embeds it.
- All four documents converge. **PASS.**

## 4. Mismatch / truncation inventory

| # | Where | What | Severity | Fix path |
|---|---|---|---|---|
| 1 | `artifacts/12-api-contract-plan.md` §3 catalog row "Ledger/audit" | Operation ID written as `listLedgerEntries`; actual `openapi.yaml` ID is `getLedgerEntries` (path `/ledger/entries`) | Low (textual inconsistency only; path, role metadata, FR mapping, and `x-invariant` are correct in the contract) | One-line edit in artifact 12 §3 to read `getLedgerEntries`. Operationally inconsequential — both names point at the same operation. |
| 2 | `artifacts/11-database-schema-spec.md` §1 / §7 | Migration "dependency order" is stated but no explicit `M001 .. Mnn` ordering is enumerated | Low (gap, not error) | Author migration-sequence table either in artifact 11 (small addition) or in C1 (`18-parallelization-and-workstreams.md`). Not a Phase A stop blocker per `tech_plan-blueprint-001.md` Phase A2 acceptance (which only lists "Tables, keys, indexes, **migrations**, tenant/owner/beneficiary columns…" but stops on missing schema content, not ordering numbers). |
| 3 | `artifacts/implementation/blueprint-phase-a.md` | **MISSING** | Phase A close-out record is not on disk | Author a small close-out summary that names the verified checks above. This is treated as tracking, not a content deliverable; one file. |
| 4 | `artifacts/review/blueprint-contract-review.md` | Not authored | Phase A3 review record per `tech_plan-blueprint-001.md` §A3 ("Contract review gate"). Not required for Phase A close-out; required **before** B1 starts. | Author after the close-out record, before B. |

No truncation in `contracts/openapi.yaml` (cleaned parse, all `$ref`s resolve, all expected paths/operations present). No truncation in artifact 10 or 12 (TOCs intact, exit criteria sections present). Artifact 11 has the migration-ordering gap above but is not truncated.

## 5. Completeness against acceptance criteria (root09 §5 + tech_plan §A2)

| AC | Source | Verified status |
|---|---|---|
| AC-1 | `contracts/openapi.yaml` covers every endpoint implied by the 26 FRs and 6 UI views; parseable; locally referenced; operationId-unique; usable by parallel devs | PASS — 42 ops, all $refs resolve, all 26 FRs covered, all 6 views covered, all opIds unique. Spectral / Schemathesis / openapi_spec_validator are explicitly out of plan per `tech_plan-blueprint-001.md` "Cannot be claimed when tools are not installed" |
| AC-2 | Artifact 11 defines every table, RLS policy, and trigger needed by the 6 capability specs, including `validate_material_dispatch()` and the append-only ledger | PASS on content; minor gap on explicit migration ordering (acceptable for Phase A) |
| AC-3 | Out of scope for Phase A (deployment is Phase B/C) | N/A here |
| AC-4 | Out of scope for Phase A (test harness is Phase B §16) | N/A here |
| AC-5 | Out of scope (parallel workstreams is Phase C §18) | N/A here |
| AC-6 | Out of scope (business defaults is Phase B §19) | N/A here |
| AC-7 | `openspec validate` and `openspec status` 4/4 | Already validated per task-record rev 11 ("verified exit code 0"). Phase A artifacts do not change the OpenSpec status (proposal/design/specs/tasks), which remains 4/4. PASS preserved. |
| AC-8 | CI grep portability rules (e.g. `auth.uid()`, `process.env.VERCEL`) | Out of scope for Phase A (Phase C2 with extended `verify-traceability.ps1` / new `validate-blueprint.py`) |

**Conclusion**: Phase A acceptance gates are met, with two textual/structural follow-ups (listLedgerEntries rename in artifact 12, migration-order table addition) and one tracking artifact missing (`implementation/blueprint-phase-a.md`). No content blocker.

## 6. Remaining narrow work (enumerated, no implementation)

The work that has not been touched in this recovery is **narrow and well-bounded**:

1. Author `artifacts/implementation/blueprint-phase-a.md` — a close-out record for Phase A. Content suggestion: title, status (Phase A complete; close-out record only), per-artifact verification results (taken from §§2-4 of this inspection), source ID coverage result, mismatch list (single item: listLedgerEntries vs getLedgerEntries), restart-point pointer to Phase A3 review gate.
2. Apply the one-line fix to `artifacts/12-api-contract-plan.md` §3: change `listLedgerEntries` → `getLedgerEntries` for the ledger list row.
3. Optional: add a numbered migration-sequence table (M001 .. Mnn) to `artifacts/11-database-schema-spec.md` §1 or §7. AC-2 is met without it; this is hardening only.
4. Author `artifacts/review/blueprint-contract-review.md` per `tech_plan-blueprint-001.md` §A3 (the A3 review gate). The record should verify: openapi structure = PASS, refs resolvable = PASS, opIds unique = PASS, three-scope separation, idempotency-key header, role coverage, error-code coverage, no silent semantic change vs artifact 11. This gates B1..B6.
5. After A3 review passes: Phase B (artifacts 13, 14, 15, 16, 17, 19) can begin in parallel. Phase C (18, tasks/design/spec deltas, extended checker, narrow `.gitignore` allowlist) follows B. None of those is in scope for this recovery.

Verification commands to run before Phase B starts (already documented in `tech_plan-blueprint-001.md`):
- `python -c "import yaml; yaml.safe_load(open(r'..\artifacts\contracts\openapi.yaml','r',encoding='utf-8'))"  # safe_load PASS`
- Custom structural script (to be authored in C2): `OPERATION_IDS_UNIQUE=PASS REFS_RESOLVABLE=PASS PRD_IDS=26 SOURCE_IDS=20 error_responses_complete=PASS three_scope_present=PASS idempotency_header_bound=PASS`.
- `pwsh -NoProfile -File .\openspec\changes\lukla-ops-engine-planning\artifacts\verify-traceability.ps1` (already passing per rev 11; should still pass).
- `openspec validate lukla-ops-engine-planning` (already passing per rev 11).
- `git diff --check` (clean per task-record rev 11).

## 7. Safe restart recommendation

**Restart point**: after this recovery inspection, the orchestrator should:

1. Apply the one-line fix (`listLedgerEntries` → `getLedgerEntries`) in `artifacts/12-api-contract-plan.md` §3. One character difference, no semantic impact, no contract change required because no operation ID is being renamed in `openapi.yaml`.
2. Author `artifacts/implementation/blueprint-phase-a.md` as the Phase A close-out. Reference the findings in §2–§4 of this document. Keep the file small (≤2 KB) per AGENTS.md "smallest correct, readable change" and per `tech_plan-blueprint-001.md` "stop after C3 with a concise report of the exact output observed."
3. Author `artifacts/review/blueprint-contract-review.md` per `tech_plan-blueprint-001.md` Phase A3. This is the published review-gate artifact and is the precondition for any B work to begin. The review should record: structural check results (42/42 ops unique IDs, 0 missing `$ref`s, 26/26 PRD IDs, 20/20 source IDs, 8/8 canonical roles), three-scope-model verification, idempotency-header verification, financial-gate verification, ledger-immutability verification, no silent semantic change. Use this recovery document as evidence.
4. Do **not** touch tasks.md / design.md / specs/deltas until Phase C lands (per `tech_plan-blueprint-001.md` — those are intentionally not Phase A).
5. Do **not** modify `artifacts/verify-traceability.ps1` until C2 (Phase C).
6. Do **not** author any of artifacts 13–19 until the A3 review record exists and points PASS or PASS-WITH-NITS.

This sequence respects the user's two-review-loop policy and preserves every existing edit. No previously committed file is rewritten.

The orchestrator may proceed under its standard pattern in task-record rev 11 ("subagent dispatch failed 3x → orchestrator-direct execution + review per rev-5 precedent") if subagent dispatch continues to surface provider errors. The orchestrator-direct execution pattern has been used successfully at:
- task-record rev 5 (re-transcription of the 13-slide deconstruction);
- task-record rev 7 (Phase 0-R);
The pattern is acceptable for Phase A close-out because the close-out content is bounded by this inspection's evidence.

## 8. Files NOT modified by this recovery

- No edits to `openspec/changes/lukla-ops-engine-planning/**` source documents.
- No edits to any BRD/PRD/register files.
- No git operations (no reset, no stash, no commit, no checkout).
- No dependency installation.
- No application code, no cloud resource, no schema migration.
- No subagents dispatched.

## 9. Open questions (FIND or ASK)

- **ASK (orchestrator should ask the user, not another research pass)**: Does the user want the listLedgerEntries→getLedgerEntries textual fix applied now, or deferred to a later Phase A cleanup pass? Either path is safe; the answer is purely about timing.
- **FIND (could be answered by inspecting `tasks.md` + `.openspec.yaml`)**: Is `tasks.md` currently updated to reflect that Phase A is structurally complete? Per `tech_plan-blueprint-001.md` §C2, tasks.md is updated only in Phase C. The user may pre-approve an early update outside of Phase C; default is to wait.
- **FIND (inspects existing `verify-traceability.ps1`)**: Does the existing `verify-traceability.ps1` need the Phase A–specific structural checks (opId uniqueness, `$ref` resolution, 26-ID coverage, three-scope schema presence) added before Phase A3 review signoff? `tech_plan-blueprint-001.md` §C2 says these belong in C2, not Phase A. The recovery view is: the close-out record + review record can attest to those checks without modifying `verify-traceability.ps1`. Acceptable per the plan; the user may prefer to author them earlier.

No question is a blocker for Phase A close-out.
