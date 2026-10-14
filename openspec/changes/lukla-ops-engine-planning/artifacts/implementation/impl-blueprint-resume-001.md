# Implementation Report: Phase A contract repair and validation

**Status:** COMPLETE for the bounded repair; Phase A review gate remains OPEN.

**Objective:** Repair confirmed OpenAPI example/schema defects, synchronize the human API catalog, and add a repeatable planning-only validator without beginning Phase B or runtime implementation.

## Changes Made

- `artifacts/contracts/openapi.yaml`
  - Repaired `recordSewingTally` example to use `cutBatchId`, `lineId`, and integer `pieces` required by `TallyRequest`.
  - Repaired `inspectUnit` example to use assembly-level `assemblyId` and `defects: []`.
  - Clarified component wage and finished-assembly bonus invariants.
  - Preserved the three-recipient bonus baseline and pending business-rule gate.
  - Replaced the impossible closed `FinancialRuleRequest` response composition with shared `FinancialRuleFields` plus strict request/response wrappers.
  - Added `Idempotency-Key` to `createClient` and separated financial-rule approval evidence from payroll `PaymentEvidence`.
- `artifacts/12-api-contract-plan.md`
  - Enumerated all 69 current operation IDs and corrected `listLedgerEntries` to `getLedgerEntries`.
  - Documented the assembly/component/material quantity boundaries and stated that operation count is not requirement coverage.
  - Kept financial-policy alternatives explicitly pending authorization.
- `artifacts/validate-blueprint.py`
  - Added a small local checker for YAML loading, local references, operation IDs, referenced path parameters, Draft 2020-12 component schema checks, and inline/named examples with `FormatChecker`.
  - Added negative controls for stale examples, broken references, duplicate IDs, missing path parameters, and closed-schema response composition.
- `task-record.md`
  - Advanced to revision 14 with evidence, scope, limitations, and provider-recovery status.

## Verification

- `python openspec/changes/lukla-ops-engine-planning/artifacts/validate-blueprint.py --self-test`: **PASS**; printed 69 operations, 630 refs, 111 schemas, 5 examples; all six negative controls passed; financial-rule fixtures passed; semantic approval remained explicitly not granted by the checker.
- `openspec validate lukla-ops-engine-planning`: **PASS**; `Change 'lukla-ops-engine-planning' is valid`.
- `git diff --check`: **PASS**; no output.
- `get_errors` on the four changed/added files: **PASS**; no errors found.
- Catalog parity script: **PASS**; `CATALOG_MISSING []`.
- Direct A3 review follow-up: **PASS**; all 69 operations have source, role, view and invariant metadata; `createClient` carries idempotency; financial-rule approval references `FinancialRuleApproval`.

## Acceptance Criteria

- [x] Confirmed request examples validate against their current schemas.
- [x] Confirmed local references and referenced path parameters resolve.
- [x] Confirmed the financial-rule request/response shapes are independently usable.
- [x] Added runnable negative controls for the repaired defects.
- [x] Kept Phase B/C and runtime implementation out of scope.
- [x] Phase A review approval — direct recovery review recorded in `artifacts/review/blueprint-contract-review.md` after delegated Review Orchestrator failed to produce a record.

## Decisions Made

- Kept the fixed three-way bonus baseline; a clarification question about possible future recipient changes is not authorization to weaken the current source rule.
- Kept client invoice and financial-governance surfaces as proposed extensions; operation count and source metadata do not by themselves prove BRD/PRD coverage.
- Used the installed `jsonschema`/`referencing` libraries without installing dependencies. The checker is explicitly not a full OpenAPI validator, Spectral lint, Schemathesis run, or runtime test.

## Failures and Recovery

- The delegated implementation and Review Orchestrator attempts failed with provider `server_error` / no output. Existing partial contract edits were inspected and verified before direct recovery continued; the user explicitly authorized direct review.
- A prior quick path-parameter script falsely warned on referenced parameters; the new checker resolves parameter references before comparison.

## Risks / Notes

- `openapi_spec_validator`, Spectral, Schemathesis, Playwright, PostgreSQL, and application runtime are unavailable or intentionally not run in this planning-only change.
- Phase A is not approved until an independent review examines source coverage, authorization metadata, error completeness, tenant/ownership invariants, idempotency, and the new checker’s limits.

## Files Modified

- `openspec/changes/lukla-ops-engine-planning/task-record.md`
- `openspec/changes/lukla-ops-engine-planning/artifacts/contracts/openapi.yaml`
- `openspec/changes/lukla-ops-engine-planning/artifacts/12-api-contract-plan.md`
- `openspec/changes/lukla-ops-engine-planning/artifacts/validate-blueprint.py`
- `openspec/changes/lukla-ops-engine-planning/artifacts/impl-blueprint-resume-001.md`