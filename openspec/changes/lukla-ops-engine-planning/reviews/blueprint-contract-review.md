# Review Record: Phase A contract baseline

**Review identity:** `lukla-blueprint-phase-a-contract-repair-001`  
**Date:** 2026-10-13  
**Delivery mode:** Direct recovery review, explicitly authorized by the user after the Review Orchestrator produced no output twice.  
**Subject:** Planning-only stack/database/API contract baseline; no runtime implementation.

## Objective and acceptance target

Determine whether the repaired Phase A contract is coherent enough to freeze before Phase B documents are authored. The review target is not production readiness. It is a machine-readable, source-mapped, scope-safe proposal with explicit limits and no silently approved business rules.

## Route decisions and execution health

| Dimension | Route | Reason | Result |
|---|---|---|---|
| Behavioral / data integrity | SELECTED | Examples, assembly/QC, ledger, payroll and idempotency semantics changed. | COMPLETE |
| Changeability / interface contract | SELECTED | OpenAPI operation IDs and the human catalog are parallel-team seams. | COMPLETE |
| Security / trust boundary | SELECTED | Tenant, legal-owner, beneficiary, bearer/service auth and RLS are in scope. | COMPLETE |

Delegated review execution: **DEGRADED**. Two dispatches returned no usable output and created no record. Direct review was authorized before this record was written. No route was skipped.

## Evidence checked

- `task-record.md`, revision 14 before review.
- `artifacts/impl-blueprint-resume-001.md`.
- `artifacts/contracts/openapi.yaml`.
- `artifacts/validate-blueprint.py`.
- `artifacts/10-technology-stack-and-decisions.md`, `11-database-schema-spec.md`, `12-api-contract-plan.md`.
- `09-technical-blueprint-completion-plan.md`, `artifacts/tech_plan-blueprint-001.md`.
- `04-rbac-matrix.md`, `06-acceptance-tests.md`, `08-client-clarification-register.md`.
- Python checks using PyYAML 6.0.2, jsonschema 4.23.0, referencing 0.36.2 and explicit `FormatChecker`.
- `openspec validate lukla-ops-engine-planning`, `git diff --check`, and editor diagnostics.

## Findings and remediation

### R-001 — BLOCKING_DEFECT — stale request examples

The sewing example originally omitted required `cutBatchId`, `lineId`, and `pieces`; the QC example originally used `garmentUnitId` and `originalOperatorId` instead of required `assemblyId` and `defects`. Both were repaired. The validator's `NEGATIVE_CONTROL=qc:PASS` and `NEGATIVE_CONTROL=tally:PASS` prove the old shapes are rejected by the regression harness.

**Status:** CLOSED.  
**Validation:** five media examples checked; validator exit 0.

### R-002 — BLOCKING_DEFECT — impossible financial-rule response composition

The original response composed a request schema that rejected additional properties while requiring response-only `id` and `status`. It was replaced with shared `FinancialRuleFields`, a strict request wrapper, and a strict response wrapper. The validator accepts request/response fixtures and rejects the closed-base mutation.

**Status:** CLOSED.  
**Validation:** `FINANCIAL_RULE_FIXTURES=PASS; CLOSED_BASE_NEGATIVE_CONTROL=PASS`.

### R-003 — BLOCKING_DEFECT — retryable client mutation lacked idempotency

`createClient` was a mutating operation without the common idempotency header. It now references `IdempotencyKey`, matching the database idempotency boundary.

**Status:** CLOSED.  
**Validation:** direct metadata check printed `CREATE_CLIENT_IDEMPOTENCY True`; all 69 operations retain metadata.

### R-004 — BLOCKING_DEFECT — governance approval used payment evidence schema

`approveFinancialRule` originally accepted `PaymentEvidence`, which requires a payment external reference and conflates payroll payment with business-rule authorization. It now uses `FinancialRuleApproval` with required authorization evidence and optional approval reference/note. This does not approve any business rule; it only expresses the evidence contract.

**Status:** CLOSED.  
**Validation:** direct check printed the `FinancialRuleApproval` reference; component schema meta-check passed.

### R-005 — LEARN_NOTE — operation count is not coverage

The contract has 69 operations and the catalog now enumerates all 69. The count is an inventory, not proof that all 26 PRD IDs, 20 source IDs, six views, acceptance scenarios, or runtime behaviors are covered. The plan and catalog state this limitation explicitly.

**Status:** CLOSED as a documentation risk; future traceability checker remains required.

### R-006 — PROOF_GAP — unavailable full-tool/runtime evidence

`openapi_spec_validator`, Spectral, Schemathesis, PostgreSQL, Playwright, application runtime, cloud deployment, and database integration tests were not run. The custom checker cannot substitute for them. This is expected for the planning-only phase and remains a required future gate, not a Phase A contract defect.

**Status:** ESCALATED to Phase B/C/runtime gates; does not block the planning baseline.

## Security and data-integrity assessment

- Tenant access, legal stock ownership, and order beneficiary remain separate in the database and API vocabulary.
- Service jobs use a separate security scheme and service roles; employee roles are not substituted for job authority.
- RLS design requires `FORCE ROW LEVEL SECURITY`, transaction-local context, a restricted non-owner application role, and explicit negative tests. No runtime evidence is claimed.
- Material conservation distinguishes material quantities from produced piece counts.
- Component wage attribution and one-per-assembly bonus accrual remain distinct.
- Idempotency is scoped by tenant, operation and key in the prose and database spec; `createClient` now participates in the API contract.
- Financial defaults remain proposed/pending and production-blocked; no client clarification was silently converted into an approved rule.

## Verification results

- `python ...\artifacts\validate-blueprint.py --self-test`: **PASS**; 69 operations, 630 references, 111 schemas, 5 examples; six negative controls pass.
- `openspec validate lukla-ops-engine-planning`: **PASS**.
- `git diff --check`: **PASS**.
- `get_errors` for changed contract/checker files: **PASS**; no errors found.
- Operation metadata and catalog parity: **PASS**; 69 unique IDs, no missing catalog IDs, no missing required metadata.

## Verdict

**APPROVED for the Phase A planning-contract baseline, with explicit proof gaps.**

This approval permits Phase B document authoring against the reviewed proposal. It does **not** claim application implementation, runtime conformance, database migration success, browser test success, cloud deployment, security certification, or production readiness. Any Phase B artifact that changes operation IDs, required fields, ownership dimensions, error codes, or idempotency scope must reopen contract review.

## Review limits

This direct recovery review is not independent in the same way as a separate provider-backed reviewer. That execution limitation is recorded, not hidden. The user authorized this route after two delegated review failures. Future implementation phases still require their own review and runtime evidence.