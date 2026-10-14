# Phase B4 — Test Harness and Agent Verification

**Change:** `lukla-ops-engine-planning`  
**Task record:** revision 15  
**Status:** planning artifact only. The tools and commands below are future gates; none were installed or run for this artifact.

## 1. Purpose and evidence boundary

The harness verifies the reviewed contract without changing it. It covers API behavior, PostgreSQL invariants/RLS, system workflows, browser views, the acceptance cases in `06-acceptance-tests.md`, the four closing scenarios, and all 26 PRD IDs.

The harness must preserve these boundaries:

- `tenant_id` is access scope.
- `legal_stock_owner_id` is title/custody.
- `order_beneficiary_id` is output entitlement.
- Ledger history is immutable; correction is a compensating event.
- Idempotency is `(authenticated tenant, operationId, key)`.
- Financial rules remain proposed/pending and block production approval until authorized.
- `FR-1.4`, `FR-5`, and `FR-6` remain status-only or unresolved where the source says so; tests cannot invent semantics.

No test result in this document is a runtime result. Acceptance cases in the source remain `NOT RUN` or `BLOCKED — decision needed` until an application and disposable test environment exist.

## 2. Future toolchain and one-command entry point

The future implementation may expose one bounded command such as `make verify` or `pnpm verify`, with equivalent CI steps. Tool selection is intentionally unpinned here; installation is outside this planning task.

| Layer | Future tool | Purpose | Required evidence |
|---|---|---|---|
| API contract | Schemathesis against `contracts/openapi.yaml` | Generated request/response and negative contract checks against a running API | `api-results.xml`, deterministic exit status, contract hash. |
| API/unit/integration | pytest | FastAPI service, authorization, idempotency, workflow calculations and fixtures | `api-results.xml` or separate pytest JUnit XML, plus JSON summary. |
| Database | pytest-testcontainers | Disposable PostgreSQL integration environment and restricted application role | `db-results.xml`, SQL setup hash, container/image identity. |
| Database invariants | pgTAP | RLS, FORCE RLS, trigger, function, ledger and transaction-boundary assertions | `db-results.xml` with stable test IDs. |
| Browser/system | Playwright | Six views, portal isolation, floor/tally/QC workflows, accessibility and failure states | `system-results.json`, `results.xml`, traces/screenshots/video on failure. |
| Evidence review | deterministic Python/PowerShell collector | Normalize records, validate schema, calculate bundle status | `results.json`, `results.xml`, manifest and exit status. |

Recommended future commands, not run:

```text
pytest -q --junitxml=artifacts/evidence/api-results.xml
pytest -q tests/db --junitxml=artifacts/evidence/db-results.xml
schemathesis run contracts/openapi.yaml --base-url "$API_BASE_URL" --report-junit-path artifacts/evidence/schemathesis-report.xml
playwright test --reporter=json,junit
python tools/collect_evidence.py --out artifacts/evidence
```

The exact command syntax remains an implementation choice. The harness must not report a tool as passing when it is unavailable or skipped.

## 3. Deterministic fixture model

Fixtures use generated UUIDs from a fixed seed, explicit timestamps, explicit timezone, and named data versions. No live customer data is allowed. Every fixture record includes `fixtureSetId`, `tenantId`, `legalStockOwnerId`, `orderBeneficiaryId`, and a cleanup/rollback strategy.

Required identities include at least:

- Owner, SampleTeam, Warehouse, ProductionHead, Tailor, QCInspector, FinancePayroll, and MaklonClient/portal identities from the RBAC matrix.
- A restricted non-owner PostgreSQL application role for RLS tests.
- A separate migration role and a service principal for scheduled jobs.
- Client A and Client B, with distinct material owners and order beneficiaries.
- S1–S8 sewer/tailor fixtures, mandor verification, QC inspector, Finance, Sample, and named QC bonus recipients. Bonus recipients are people, not inferred RBAC roles.

Fixtures must express CMT, Semi-CMT, and Full Package ownership cases without silently transferring legal title. The test database is disposable; each case starts from a known snapshot or uses a unique fixture namespace.

## 4. Evidence bundle contract

Each run writes a deterministic manifest under an implementation-selected evidence directory. At minimum:

```json
{
  "schemaVersion": "1",
  "runId": "stable-run-identifier",
  "contractSha256": "sha256-of-openapi.yaml",
  "fixtureSetId": "fixed-fixture-set",
  "startedAt": "normalized-utc-time",
  "finishedAt": "normalized-utc-time",
  "exitCode": 0,
  "tests": [
    {
      "testId": "API-AT-01",
      "sourceIds": ["FR-6.2", "FR-1.1"],
      "fixtureId": "fixture-a-b-dispatch",
      "requestId": "fixed-or-recorded-correlation-id",
      "expected": "cross-client issue is rejected without stock mutation",
      "actual": "recorded result or unavailable",
      "status": "PASS|FAIL|BLOCKED|NOT_RUN|SKIPPED",
      "evidence": ["api-results.xml", "db-results.xml"]
    }
  ]
}
```

Required files when their layer runs:

- `results.json` — normalized complete manifest.
- `results.xml` — normalized aggregate JUnit-compatible result.
- `api-results.xml` — pytest/Schemathesis API evidence.
- `db-results.xml` — pytest-testcontainers/pgTAP evidence.
- `system-results.json` — normalized system/browser summary.
- Playwright `trace.zip`, screenshot, and video for failures when configured.
- `manifest.json` — file hashes, tool availability, command metadata, contract hash, fixture ID.

JSON and XML must be deterministic in ordering and status vocabulary. Timestamps may be normalized or explicitly marked volatile; secrets, tokens, raw credentials, and unrestricted business payloads must not appear. HTML reports are optional human aids and are never the source for an AI pass/fail decision.

A missing required layer is `NOT_RUN` or `BLOCKED`, not `PASS`. A skipped optional extension must state why. The collector exits non-zero for any `FAIL`, malformed evidence, hash mismatch, missing required evidence, or contradictory status.

## 5. Stable test-ID map

### 5.1 Acceptance cases AT-01..AT-10

| Source case | Stable harness ID | Future assertion |
|---|---|---|
| AT-01 | `API-AT-01`, `DB-AT-01` | Cross-client material issuance rejects and leaves quantity/history unchanged. |
| AT-02 | `API-AT-02` | Matched-owner control can issue through the same workflow; unresolved FR-5 detail is not asserted. |
| AT-03 | `API-AT-03`, `DB-AT-03` | +5 midweek headcount, verified component output, and per-sewer Saturday piece-rate totals. |
| AT-04 | `API-AT-04`, `DB-AT-04` | Unverified tally and pending-QC unit do not earn premature wages; later gates allow one credit. |
| AT-05 | `API-AT-05`, `DB-AT-05` | Repair returns to original operator and cannot create a second piece-rate credit. |
| AT-06 | `API-AT-06`, `DB-AT-06` | One shared QC pool across FR-9.2/FR-10.3; 3,000 passes and three named recipients. |
| AT-07 | `API-AT-07`, `DB-AT-07` | Only Pass contributes; repeated calculation does not duplicate the same pass units. |
| AT-08 | `API-AT-08` | Mathematical quotient is observable; integer payout/remainder remains `BLOCKED` until authorized. |
| AT-09 | `API-AT-09`, `UI-AT-09` | Sample v1/v2 history remains traceable into a Semi-CMT order; no automatic rate inheritance asserted. |
| AT-10 | `API-AT-10`, `UI-AT-10` | Sample role cannot approve mass order without separately decided confirmation mechanics. |

### 5.2 RBAC negative cases AT-R01..AT-R08

| Source case | Stable harness ID | Future assertion |
|---|---|---|
| AT-R01 | `DB-ATR01`, `API-ATR01` | Owner cannot modify locked transaction history; reversal permission remains separately governed. |
| AT-R02 | `API-ATR02`, `UI-ATR02` | Sample account cannot approve mass order on sample approval alone. |
| AT-R03 | `API-ATR03`, `DB-ATR03` | Warehouse mismatch rejection leaves protected material state unchanged. |
| AT-R04 | `API-ATR04`, `DB-ATR04` | Mandor cannot change payroll formula or final QC result; rate-card permission is not removed. |
| AT-R05 | `API-ATR05`, `DB-ATR05` | Tailor cannot edit mandor-verified output. |
| AT-R06 | `API-ATR06`, `DB-ATR06` | QC cannot change borongan rate or client order data. |
| AT-R07 | `API-ATR07`, `DB-ATR07` | Finance cannot change physical warehouse stock. |
| AT-R08 | `API-ATR08`, `UI-ATR08`, `DB-ATR08` | Client A cannot read Client B portal data, including by explicit identifier. |

### 5.3 Four closing scenarios

| Scenario | Stable scenario IDs | Covered cases |
|---|---|---|
| Closing-01 cross-client material issuance | `SCN-01-API`, `SCN-01-DB` | AT-01, AT-02, AT-R03; `issueMaterial`, `getStock`. |
| Closing-02 headcount and Saturday payroll | `SCN-02-API`, `SCN-02-DB`, `SCN-02-UI` | AT-03, AT-04, AT-05; `recordSewingTally`, `verifySewingTally`, `inspectUnit`, `calculateWeeklyPayroll`, `getPayrollStatement`. |
| Closing-03 3,000 Pass units and shared bonus | `SCN-03-API`, `SCN-03-DB` | AT-06, AT-07, AT-08; `inspectUnit`, `getBonusPool`, `calculateWeeklyPayroll`. |
| Closing-04 sample v2 to Semi-CMT order | `SCN-04-API`, `SCN-04-UI`, `SCN-04-DB` | AT-09, AT-10, AT-R02; `createSampleRevision`, `approveSample`, `convertSampleToOrder`, `getOrder`. |

## 6. PRD coverage map: all 26 IDs

The map distinguishes source-backed behavior from unresolved/group status. No missing behavior is filled in by the test ID.

| PRD ID | Stable test IDs | Coverage boundary |
|---|---|---|
| FR-1.1 | `API-FR-1.1-tenant-scope`, `DB-FR-1.1-RLS`, `UI-FR-1.1-portal-isolation` | Tenant scope and isolation. |
| FR-1.4 | `TRACE-FR-1.4-status` | Status/contract trace only; exact meaning remains pending. |
| FR-2.1 | `API-FR-2.1-auth`, `DB-FR-2.1-membership`, `UI-FR-2.1-role-routing` | Auth and role restriction boundary. |
| FR-3.1 | `API-FR-3.1-audit-ledger`, `DB-FR-3.1-append-only` | Audit and history behavior. |
| FR-4.1 | `API-FR-4.1-samples`, `DB-FR-4.1-revisions` | Sample lifecycle and revision history. |
| FR-4.2 | `API-FR-4.2-time-study`, `DB-FR-4.2-time-study` | Time-study records. |
| FR-4.3 | `API-FR-4.3-lock`, `DB-FR-4.3-lock` | Lock/immutability behavior. |
| FR-5 | `TRACE-FR-5-status`, `NEG-FR-5-ownership` | Group status plus only source-backed stock boundary; detailed FR-5 semantics remain unresolved. |
| FR-5.1 | `API-FR-5.1-receive`, `DB-FR-5.1-stock` | Receipt/stock contract as defined by the reviewed proposal. |
| FR-5.2 | `API-FR-5.2-stocktake`, `DB-FR-5.2-stocktake` | Stocktake/observation boundary. |
| FR-6 | `TRACE-FR-6-status`, `NEG-FR-6-ownership` | Group status; no invented cutting-module ownership. |
| FR-6.1 | `API-FR-6.1-cutting`, `DB-FR-6.1-conservation` | Cutting result and unit-safe conservation. |
| FR-6.2 | `API-FR-6.2-dispatch`, `DB-FR-6.2-owner-beneficiary` | Mismatch rejection; owning module remains unresolved. |
| FR-6.3 | `API-FR-6.3-adjustment`, `DB-FR-6.3-adjustment` | Stock adjustment authorization boundary. |
| FR-7.1 | `API-FR-7.1-capacity`, `DB-FR-7.1-capacity` | Dynamic capacity/allocation; ±70 is not a cap. |
| FR-7.2 | `API-FR-7.2-rate-card`, `DB-FR-7.2-rate-card` | Rate-card scope and immutability. |
| FR-7.3 | `API-FR-7.3-tally`, `DB-FR-7.3-tally` | 30-minute output and idempotent tally record. |
| FR-7.4 | `API-FR-7.4-assembly`, `DB-FR-7.4-assembly-qc` | Assembly linkage and pending-QC state. |
| FR-8.1 | `API-FR-8.1-qc`, `DB-FR-8.1-qc-transition` | Pass/Repair/Reject state and first-pass gate. |
| FR-8.2 | `API-FR-8.2-repair-credit`, `DB-FR-8.2-no-double-pay` | Repair attribution and no second credit. |
| FR-9.1 | `API-FR-9.1-bonus-eligibility`, `DB-FR-9.1-pass-pool` | Pass-based bonus eligibility. |
| FR-9.2 | `API-FR-9.2-bonus-pool`, `DB-FR-9.2-shared-rule` | Shared pool, not a second independent rule. |
| FR-10.1 | `API-FR-10.1-weekly-payroll`, `DB-FR-10.1-payroll-gates` | Verified output and payroll calculation. |
| FR-10.2 | `API-FR-10.2-meal-rule`, `DB-FR-10.2-pending` | Configurable meal rule; basis remains pending. |
| FR-10.3 | `API-FR-10.3-shared-bonus`, `DB-FR-10.3-remainder-pending` | Shared bonus and unresolved integer remainder. |
| FR-10.4 | `API-FR-10.4-overhead`, `DB-FR-10.4-overhead-gate` | Monthly overhead with unresolved denominator/policy gate. |

## 7. Contract-operation references used by the harness

The following names are copied from `contracts/openapi.yaml`; the implementation must resolve them before running the harness:

- Authentication/context: `login`, `refreshSession`, `logout`, `getMyContext`.
- Scope and orders: `provisionAccount`, `listClients`, `createClient`, `createOrder`, `listOrders`, `getOrder`.
- Ledger/audit: `appendLedgerTransaction`, `reverseLedgerTransaction`, `getLedgerEntries`, `listAuditEvents`.
- Samples/rates: `createSample`, `listSampleRevisions`, `createSampleRevision`, `lockSample`, `recordTimeStudy`, `upsertRateCard`, `listSamples`, `approveSample`, `convertSampleToOrder`, `listRateCards`.
- Warehouse/cutting: `receiveMaterial`, `issueMaterial`, `getStock`, `createStocktake`, `createStockAdjustment`, `recordCuttingResult`.
- Sewing/assembly: `listLines`, `createLine`, `listOperators`, `createOperator`, `listAssignments`, `assignOperator`, `recordSewingTally`, `listAssemblies`, `createAssembly`, `listProductionProgress`, `verifySewingTally`.
- QC/payroll/overhead: `inspectUnit`, `getBonusPool`, `createPayrollPeriod`, `listPayrollPeriods`, `calculateWeeklyPayroll`, `getPayrollStatement`, `approvePayroll`, `recordPayrollPayment`, `recordOverhead`, `calculateOverhead`.
- Governance/procurement/billing: `listFinancialRules`, `proposeFinancialRule`, `approveFinancialRule`, `createPurchaseOrder`, `approvePurchaseOrder`, `recordSupplierInvoice`, `listClientInvoices`, `createClientInvoice`, `issueClientInvoice`.
- Files/dashboard/portal/jobs/search: `createFileUpload`, `completeFileUpload`, `getFileDownload`, `getDashboard`, `getPortalOrderStatus`, `runSaturdayPayrollJob`, `runMonthlyOverheadJob`, `getJob`, `searchOperationalDocuments`.

The harness implementation must fail fast if a referenced operation ID is absent, duplicated, or mapped to a different path/verb than the reviewed contract. It must not silently substitute a similarly named operation.

## 8. AI review-orchestrator protocol

The future review agent is an evidence parser, not an exploratory tester and not a business-rule approver.

1. **Input validation:** require the manifest, contract hash, fixture set ID, tool-availability record, exit code, and all required JSON/XML files. Reject malformed or contradictory evidence.
2. **Contract identity:** compare the recorded contract hash to the reviewed `openapi.yaml` hash. A mismatch is `BLOCKED_CONTRACT_DRIFT`, not a pass.
3. **Status policy:** `FAIL`, missing required evidence, malformed XML/JSON, non-zero collector exit, or unresolved required operation reference yields `FAIL`/`BLOCKED` according to the manifest’s declared reason. `NOT_RUN` never becomes `PASS`. `BLOCKED` financial assertions remain blocked.
4. **Traceability:** verify every required AT, AT-R, closing scenario, and PRD ID has at least one stable test record. `TRACE-*` records satisfy inventory only, not behavior coverage.
5. **Financial guard:** reject any evidence that treats a demo/default meal basis, QC remainder destination, recipient mapping, payroll eligibility, overhead denominator, or approval evidence as authorized when the source marks it pending.
6. **Isolation guard:** require negative evidence for cross-tenant, legal-owner, beneficiary, pooled-context, forged-service, and owner/BYPASSRLS cases.
7. **Verdict:** emit deterministic JSON/XML with `PASS`, `FAIL`, `BLOCKED`, or `NOT_RUN`, ordered by stable test ID. Include finding code, source/test IDs, evidence paths, and remediation. Do not infer from screenshots or HTML.
8. **Human escalation:** route contract drift, missing source decisions, security ambiguity, data-loss risk, or any financial-rule change to a human owner. The agent cannot approve those changes.

Suggested verdict codes: `EVIDENCE_MISSING`, `EVIDENCE_MALFORMED`, `CONTRACT_DRIFT`, `TEST_FAILURE`, `NOT_EXECUTED`, `FINANCIAL_RULE_PENDING`, `TRACEABILITY_GAP`, `ISOLATION_GAP`, `TOOL_UNAVAILABLE`.

## 9. Negative controls and known ceilings

Required negative controls include: cross-client dispatch; missing tenant context; unauthorized role; cross-tenant and cross-beneficiary reads; cross-legal-owner file access; ledger update/delete; unbalanced or late ledger line insertion; duplicate Repair credit; same idempotency key with altered payload; leaked pooled GUC; forged service principal; unresolved financial configuration blocking payroll approval; duplicate job delivery; and mixed material units.

Known ceiling: this artifact defines stable future checks and evidence, but does not prove that the application, tools, database, browser, cloud, or financial policy exists. Tool installation, runtime execution, and external-provider validation are deliberately excluded. The first implementation should add the smallest runnable smoke check for evidence-schema validation before expanding to full generated tests.

### 9.1 Phase C catalog preservation

The harness preserves the 26 PRD/FR catalog IDs (FR-1.1 through FR-10.4, including child IDs) and separately preserves the 20 source IDs required by the Phase C verifier. These are inventory identifiers, not runtime evidence.

