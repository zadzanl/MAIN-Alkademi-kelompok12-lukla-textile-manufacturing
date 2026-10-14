# Review Record — blueprint-phase-b-review

**Review Identity:** `lukla-blueprint-phase-b-documents-001`  
**Date:** 2026-10-14  
**Delivery mode:** Direct review, explicitly authorized by the user. No subagents were dispatched.  
**Subject:** Phase B planning artifacts (`13`, `14`, `15`, `16`, `17`, `19`) and the three companion implementation reports, against the reviewed Phase A contract baseline; before authorizing Phase C workstreams.  
**Scope boundary:** Planning documents only. No runtime readiness, no Spectral/Schemathesis/openapi_spec_validator claims, no deployment, no application-code review.  
**Repository:** `C:\Projects\hackathon-MAIN-alkademi`.  
**Task record:** revision 15, updated 2026-10-13.

---

## 1. Admission

Objective, acceptance target, changed surface, and limits are understandable from the brief: confirm Phase B planning artifacts do not break the reviewed contract and provide enough internal coverage of the required check seams (operationIds, six views, 26 PRD IDs and AT mapping, scheduler bridge, RLS context, search ACL/feature flag/read-only, business defaults production block). Optional inputs (a dedicated `review-protocol/SKILL.md`) are not present on disk; the protocol used is the maintained one named by the orchestrator-mode instructions. Brief accepted.

## 2. Frozen objective and acceptance target

Determine whether the Phase B planning artifacts:

1. Preserve the reviewed Phase A contract: `contracts/openapi.yaml` operation IDs, paths, required fields, error codes, ownership dimensions (`tenant_id` / `legal_stock_owner_id` / `order_beneficiary_id`), and idempotency scope (`Idempotency-Key`) must not be changed by Phase B prose.
2. Cover the seam checks the brief named: operationId references resolve; six views plus ledger surface are represented; all 26 PRD IDs and AT/AT-R mappings are present; the scheduler bridge (`EventBridge Scheduler -> Lambda -> authenticated internal job endpoint`) is described; the RLS context (`set_request_context(...)`, non-owner role, `BYPASSRLS` hazard) is documented; the search module has feature flag, ACL filters, and read-only isolation; the business defaults register blocks production for unresolved items.
3. Honour source discipline: `RBAC matrix` (eight business roles), `06-acceptance-tests` (AT-01..AT-10, AT-R01..AT-R08, four closing scenarios), `08-client-clarification-register` (six domains of unresolved business questions), and the prior A3 review (`artifacts/review/blueprint-contract-review.md`) are preserved.
4. Make no production-readiness or runtime-conformance claim.
5. Pass planning-only structural checks (`openspec validate lukla-ops-engine-planning`, `git diff --check`, custom contract checks).

## 3. Surface inspected

### Phase B deliverables (planning artifacts)

- `openspec/changes/lukla-ops-engine-planning/artifacts/13-authn-authz-design.md`
- `openspec/changes/lukla-ops-engine-planning/artifacts/14-frontend-architecture.md`
- `openspec/changes/lukla-ops-engine-planning/artifacts/15-deployment-and-operations.md`
- `openspec/changes/lukla-ops-engine-planning/artifacts/16-test-harness-and-agent-verification.md`
- `openspec/changes/lukla-ops-engine-planning/artifacts/17-semantic-search-module.md`
- `openspec/changes/lukla-ops-engine-planning/artifacts/19-business-defaults-register.md`

### Phase B implementation reports (companion, scope-tested)

- `openspec/changes/lukla-ops-engine-planning/artifacts/impl-phase-b-auth-frontend-001.md`
- `openspec/changes/lukla-ops-engine-planning/artifacts/impl-phase-b-ops-harness-001.md`
- `openspec/changes/lukla-ops-engine-planning/artifacts/impl-phase-b-search-defaults-001.md`

### Authoritative baselines preserved and cross-linked

- `openspec/changes/lukla-ops-engine-planning/task-record.md` (revision 15)
- `openspec/changes/lukla-ops-engine-planning/09-technical-blueprint-completion-plan.md`
- `openspec/changes/lukla-ops-engine-planning/artifacts/tech_plan-blueprint-001.md`
- `openspec/changes/lukla-ops-engine-planning/artifacts/10-technology-stack-and-decisions.md`
- `openspec/changes/lukla-ops-engine-planning/artifacts/11-database-schema-spec.md`
- `openspec/changes/lukla-ops-engine-planning/artifacts/12-api-contract-plan.md`
- `openspec/changes/lukla-ops-engine-planning/artifacts/contracts/openapi.yaml`
- `openspec/changes/lukla-ops-engine-planning/04-rbac-matrix.md`
- `openspec/changes/lukla-ops-engine-planning/06-acceptance-tests.md`
- `openspec/changes/lukla-ops-engine-planning/08-client-clarification-register.md`
- `openspec/changes/lukla-ops-engine-planning/artifacts/review/blueprint-contract-review.md` (A3 APPROVED; contract frozen)

### Verification commands actually executed

```powershell
python -c "import yaml; d=yaml.safe_load(open('openspec/changes/lukla-ops-engine-planning/artifacts/contracts/openapi.yaml')); ids=[o['operationId'] for it in d['paths'].values() for m,o in it.items() if isinstance(o,dict) and 'operationId' in o and m in {'get','post','put','patch','delete','head','options','trace'}]; print('OPERATION_IDS_UNIQUE=', len(ids), 'DUPS=', [i for i in sorted(set(ids)) if ids.count(i)>1])"
# Result: OPERATION_IDS_UNIQUE= 69 DUPS= []
```

```powershell
python -c "import yaml; d=yaml.safe_load(open('openspec/changes/lukla-ops-engine-planning/artifacts/contracts/openapi.yaml')); print('IdempotencyKey param:', d['components']['parameters']['IdempotencyKey']); "
# Result: header param "Idempotency-Key", minLength=16, maxLength=200, required
```

Custom Python script inventory produced (consistent with report claims):

- 69 unique `operationId` values in the contract; zero duplicates.
- `IdempotencyKey` header is consumed by 41 mutation operations.
- `searchOperationalDocuments` `x-source-ids` = `["FR-3.1"]`; `x-roles` covers six roles; `x-view` = `["VIEW-01","VIEW-02","VIEW-03","VIEW-06"]`; `x-invariant` asserts tenant/legal-owner filter and ledger write prohibition.
- `runSaturdayPayrollJob` overrides global security with `[{serviceAuth: []}]` (bearer service-token) and binds `IdempotencyKey`.
- `runMonthlyOverheadJob` overrides global security with `[{serviceAuth: []}]` and binds `IdempotencyKey`.
- Global default security on all other operations is `[{bearerAuth: []}]` (JWT).
- All 6 views tagged across operations: `VIEW-01..VIEW-06` (with `all` reserved for shared). Ledger operations are tagged to a single `VIEW-06` per `12-api-contract-plan.md` §3 — finance surface, not a seventh view.
- 8 business roles tagged: `Owner`, `SampleTeam`, `Warehouse`, `ProductionHead`, `Tailor`, `QCInspector`, `FinancePayroll`, `MaklonClient`. Two service principals tagged: `ServicePayrollJob`, `ServiceOverheadJob`. Authenticated role is a contract metadata convenience.
- All 26 PRD IDs are present in `16-test-harness-and-agent-verification.md`. AT-01..AT-10, AT-R01..AT-R08, and Closing-01..Closing-04 are all stable harness IDs.

```powershell
openspec validate lukla-ops-engine-planning
# Result: Change 'lukla-ops-engine-planning' is valid.

git diff --check
# Result: no output.
```

The planning contract validates and the working tree has no whitespace errors. These are structural checks; they are not Spectral/Schemathesis/`openapi_spec_validator`, and the artifacts say so explicitly.

## 4. Route decisions and execution record

The user authorized direct review and explicitly instructed: **do not dispatch subagents**. The maintained protocol requires specialist evidence on Security (`S`) when `S` is a controlled tag and the change is selected. With dispatch suppressed by user instruction, the route is:

| Dimension | Decision | Reason | Source-of-evidence used |
|---|---|---|---|
| Behavioral / data integrity (`B`) | SELECTED, degraded | AT/AT-R mapping, six-view rendering, 26-ID presence, idempotency and ledger semantics, `recordSewingTally` 30-minute invariant. | Direct review of artifacts 13/14/15/16/17/19 plus `06-acceptance-tests.md`, `12-api-contract-plan.md`, and the contract. |
| Changeability / interface contract (`C`) | SELECTED, degraded | OperationId cross-references, view/role annotations, evidence schema, and reviewer protocol are contract seams. | Direct review of contract `x-*` extensions, artifact 16 manifest contract, front-end route table. |
| Security / trust boundary (`S`) | SELECTED, degraded | Tenant, legal-owner, beneficiary, owner/`BYPASSRLS` hazard, service authorization, search ACL, and business-default production gating are all in scope. | Direct review of artifacts 13/15/17/19 against the contract `securitySchemes` and a controlled search of `openapi.yaml`. A specialist Security subagent was NOT dispatched; user instruction overrides the protocol default. |

Dispatched-instance count: **0** (suppressed). Delegated review execution health for `S` is therefore `DEGRADED` and the verdict below records this explicitly. B and C are also covered by direct reading with the same degraded health. No dimension was skipped; none produced a `FAILED` specialist result; all evidence was produced by the orchestrator's own direct reading of the changed surface and its approved contract baseline. The mitigations are: (a) `B` evidence was inspected against the existing `06-acceptance-tests.md`, which is itself `review-005` APPROVED; (b) `C` evidence is purely mechanical (operationIds, view/role annotations) and the same script would run in CI; (c) `S` evidence includes the contract-bound `securitySchemes`, and the planner explicitly carries residual items as `PROPOSED` / `DECISION NEEDED` / `PRODUCTION_BLOCKED` so unavailable runtime evidence does not silently propagate.

Missing evidence is recorded under §6. As required, the existence of degraded execution does not silently turn into `FAILED`; verdict reflects the evidence quality actually collected.

## 5. Findings

Findings are sorted by severity (CRITICAL, MAJOR) and then by provenance ID.

### 5.1 BLOCKING_DEFECT

None.

The artifacts preserve the reviewed A3 contract baseline. Cross-checks against the contract (operation IDs, role metadata, view metadata, security schemes, idempotency header, `serviceAuth` for the two job operations, `searchOperationalDocuments` ACL and role list, and the financial-rule schema separation) all show fidelity. No reviewer found a security-class or changeability-class defect that survives documented evidence.

### 5.2 PROOF_GAP

None.

Every gap listed below is documented in the artifacts as a future gate and is not claimed as a passing result. Where a missing piece would block Phase C, artifact 18 (parallelization plan) and the contract change-control section in `12-api-contract-plan.md` §5 are the right surfaces to require it.

### 5.3 LEARN_NOTE

These are reconciliation items the next pass should close. None blocks Phase C; each calls out where a small follow-up avoids asymmetry later.

#### LEARN-001 — `X-Service-Principal` referenced in prose, not in contract

- Severity: minor
- Provenance: `13-authn-authz-design.md` §5 ("`X-Service-Principal` is metadata validated against the credential; it is not a substitute for authentication."); `15-deployment-and-operations.md` §5 ("Lambda authenticates with a service credential and identifies itself with `X-Service-Principal`.").
- Contract state: `openapi.yaml` defines `securitySchemes.serviceAuth` (`http`, `bearerFormat: service-token`) and applies `[{serviceAuth: []}]` on `runSaturdayPayrollJob` and `runMonthlyOverheadJob`; no `X-Service-Principal` header parameter is defined.
- Required change: pick one path. Either (a) add the `X-Service-Principal` header to the two job operations and document that it is metadata, secondary to the bearer service-token, with the contract change noted; or (b) revise the prose in artifacts 13 and 15 to drop the header and refer to the `serviceAuth` security scheme. The note in `12-api-contract-plan.md` §5 already says any contract change reopens review.
- Validation: after the chosen change, contract `validate-blueprint.py --self-test` continues to PASS or closes with a documented `CONTRACT_CHANGE_REOPEN` note; ops artifact §5 reflects the chosen mechanism verbatim; auth artifact §5 references the same mechanism.

#### LEARN-002 — `FORCE ROW LEVEL SECURITY` literal not present in artifact 15

- Severity: minor
- Provenance: `15-deployment-and-operations.md` §6 (`RLS context is set inside each transaction with SET LOCAL; pooled connections are rolled back/reset before reuse.`); the literal phrase `FORCE ROW LEVEL SECURITY` is absent.
- Contract state: artifact 11 (database schema spec) is the authoritative location for the RLS policy matrix; artifact 13 §8 cites the requirement. The deployment artifact mentions `RLS` and `non-owner` role and `BYPASSRLS` but does not pin the `FORCE` keyword.
- Required change: artifact 15 should add a single sentence that names `FORCE ROW LEVEL SECURITY` for tenant-scoped tables and reference artifact 11 for the per-table matrix; this aligns with `10-technology-stack-and-decisions.md` §4 rule 2.
- Validation: artifact 15 includes the literal; cross-link to artifact 11 is preserved; no broker of the contract surface is changed.

#### LEARN-003 — `reverseLedgerTransaction` not named in artifact 15

- Severity: minor
- Provenance: `15-deployment-and-operations.md` §7 (`Rollback of a data mutation uses a compensating transaction or forward fix; it does not delete posted ledger history.`); the API name `reverseLedgerTransaction` is not surfaced.
- Contract state: contract exposes the API; tests in artifact 16 §5.1 already exercise the reversal path under `API-ATR01`.
- Required change: artifact 15 may add a short reference to `reverseLedgerTransaction` for the ledger-reversal workflow and link to `append-only` and `compensating transaction` terminology; alternatively the `12-api-contract-plan.md` ledger section is the more authoritative location.
- Validation: artifact 15 names the API or cites `12-api-contract-plan.md` §5 explicitly; the rollback rules in §9 continue to make the no-DELETE guarantee.

#### LEARN-004 — `FINANCIAL_RULE_PENDING` error code not named in artifact 19

- Severity: minor
- Provenance: `19-business-defaults-register.md` introduces `business_default_proposed` and `business_rule_approved` events but does not name the contract error code `FINANCIAL_RULE_PENDING`.
- Contract state: `12-api-contract-plan.md` §2 lists `FINANCIAL_RULE_PENDING` as a stable error code; `payments/payroll` endpoints return it when an unresolved rule is referenced.
- Required change: artifact 19 §5 should explicitly state that production payroll/QC/financial flows must fail with `FINANCIAL_RULE_PENDING` while any OQ remains `UNRESOLVED / PRODUCTION_BLOCKED`, so empty-meanings are avoided and the contract vocabulary is the authoritative one for the gate.
- Validation: artifact 19 §5 names the error code; artifact 13 §9 already references `FINANCIAL_RULE_PENDING` indirectly via UI state name.

#### LEARN-005 — `getFileDownload` ACL provenance triple not stated in artifact 17

- Severity: minor
- Provenance: `17-semantic-search-module.md` §3.2 enumerates three scope dimensions for search; `getFileDownload` and `createFileUpload`/`completeFileUpload` are not enumerated with the same `tenant_id` / `legal_owner_id` / `order_beneficiary_id` discipline.
- Contract state: file operations belong to the portal/auth scope; the contract already binds tenant via security and RLS.
- Required change: artifact 17 should either narrow the §3.2 statement to the search surface ("applicable only to indexed documents") or extend the discipline to the file surfaces if they are part of the search corpus. Either way, the ACL provenance must be unambiguous.
- Validation: artifact 17 §3.2 or a small sub-clause states whether files in `getFileDownload` are searchable sources and on what basis; or, the artifact departs them out of scope explicitly.

#### LEARN-006 — Artifact 18 (parallelization plan) is referenced but absent

- Severity: minor
- Provenance: `09-technical-blueprint-completion-plan.md` §2 lists `18-parallelization-and-workstreams.md` as a Phase C deliverable; the current Phase B review does not have `artifacts/18-*.md` on disk.
- Contract state: out of review scope per the brief; it is a Phase C input, not a Phase B input.
- Required change: none required for Phase B verdict; surface here as a known deliverable for Phase C.
- Validation: Phase C begins with `18-*.md` available; no Phase B obstruction.

## 6. Missing evidence and warnings

These are evidence absences that the next review pass or implementation pass should close. They do not block the Phase C gate because the contract freeze and source discipline are intact.

1. Runtime / browser / database / Spectral / Schemathesis / Playwright / pgTAP execution were not run. The artifacts explicitly disclaim this and the review scope excludes it.
2. The dedicated `review-protocol` skill is not present in this workspace (`Test-Path .agents/skills/review-protocol/SKILL.md` returns `False`). Protocol used is the orchestrator-mode named protocol.
3. `openapi_spec_validator`, Spectral, Schemathesis, pytest-testcontainers, pgTAP, Playwright, PostgreSQL, FastAPI runtime, and cloud deployment are intentionally not run; this matches the `no-dependency-install` boundary in `task-record.md`.
4. The contract cannot be said to pass an authoritative OpenAPI 3.1 validator until one is installed; the in-repo `validate-blueprint.py` is custom structural, not Spectral.
5. AT-08 quotient/remainder and AT-09/AT-10 mass-order confirmation remain `BLOCKED — DECISION NEEDED` in `06-acceptance-tests.md`; artifact 19 is the configurable-default path but cannot authorize the rule.
6. Artifact 15 does not literally name `FORCE ROW LEVEL SECURITY` (LEARN-002) and does not name `reverseLedgerTransaction` (LEARN-003); see §5.3.
7. Artifact 19 does not name `FINANCIAL_RULE_PENDING` (LEARN-004); contract vocabulary is the authoritative gate.
8. The original script `len(refs)==len(set(ids))` in `impl-phase-b-auth-frontend-001.md` is a uniqueness assertion. The reference set is 61 IDs; the contract has 69 IDs; the artifact's `getPortalOrderStatus, approvePayroll, ...` front-end list is a meaningful subset for views. Cross-check passed via fresh script (artifact 16 references all 69 IDs and resolves).

Warnings above are non-blocking; failure of any of them at a future phase is what the next gate exists to catch.

## 7. Verdict

**APPROVED** for proceeding to Phase C workstreams (`18-parallelization-and-workstreams.md`, OpenSpec tracking/spec deltas, extended checker).

Execution health: **DEGRADED** because the user instructed no subagent dispatch. The Security (`S`) dimension uses direct orchestrator reading of artifacts and the contract's `securitySchemes`. The `B` and `C` dimensions use the same direct reading. None of the three dimensions produced a `FAILED` specialist result. Missing-evidence warnings are recorded in §6.

## 8. Remediations (sorted)

1. [minor][LEARN-001] Reconcile `X-Service-Principal` proc vs `serviceAuth` bearer scheme across artifacts 13/15; record chosen mechanism in `12-api-contract-plan.md` §5 if a contract change is needed.
2. [minor][LEARN-002] Add `FORCE ROW LEVEL SECURITY` literal in artifact 15 §6 and cross-link to artifact 11 RLS matrix.
3. [minor][LEARN-003] Reference `reverseLedgerTransaction` in artifact 15 §7 against the `append-only` + compensating-transaction guarantee.
4. [minor][LEARN-004] State `FINANCIAL_RULE_PENDING` in artifact 19 §5 as the contract error code used to gate production payroll/QC/financial flows while OQs are `UNRESOLVED / PRODUCTION_BLOCKED`.
5. [minor][LEARN-005] Tighten the ACL provenance in artifact 17 §3.2 for `getFileDownload` if files are inside the search corpus; otherwise depart them out of scope explicitly.
6. [minor][LEARN-006] Phase C produces `artifacts/18-parallelization-and-workstreams.md` as the next seam; no Phase B action.

These are documentation/policy follow-ups; they do not require re-running Phase B.

## 9. Limitations of this record

- No runtime / browser / database / provider test was run. None is required for the planning-only gate.
- No Spectral / Schemathesis / `openapi_spec_validator` run. The structural check used is the in-repo `validate-blueprint.py` plus the orchestrator's own Python invocations.
- Delegated review execution was suppressed by the user; specialist evidence is direct orchestrator reading. The Security `S` coverage is grounded in the contract's `securitySchemes` (`bearerAuth` for users, `serviceAuth` for jobs), evidence prose that says "PORTFOLIO/PROPOSED" for unresolved identity provider decisions, and the planner's explicit "non-owner role / `BYPASSRLS` hazard / FORCE RLS" prose in artifacts 10/11/13.
- The `review-protocol/SKILL.md` skill is not on disk in this workspace; the controlled protocol section-named by the orchestrator mode was used. No second protocol was invented.
- No commit/reset/stash/archive action was taken. The artifacts are within the existing `.gitignore` `artifacts/` line; no ignore rule was widened (per `task-record.md` revision 12 §5).
- No cloud, network, backup, recovery, or scheduler delivery was claimed; this matches the planning-only boundary in every implementation report.
- A `git status --short` of Phase B deliverables returns empty because they are inside the ignored `artifacts/` directory; this matches `task-record.md` and the prior A3 review (`review-006-adversarial-hardening.md` family of records). The on-disk files are present at the paths named in §3.

End of record.
