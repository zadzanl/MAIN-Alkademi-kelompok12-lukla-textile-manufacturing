# Unverified Runtime Evidence Report

**Task record:** `openspec/changes/lukla-ops-engine-planning/task-record.md` revision 17  
**Inspection date:** 2026-10-15  
**Scope:** Lukla planning suite, implementation reports, current backend/frontend/tests, verification scripts, and generated evidence.  
**Mode:** Research only. No source files, tests, migrations, deployments, or dependencies were modified or executed for this report. Veteran-engineer consultation was not dispatched.

## Executive finding

The Lukla planning suite is structurally verified as documentation and contract planning, not as a running product. The strongest runtime evidence inspected is a Playwright Chromium run against a local standalone mock HTML file: two UI tests passed. The same evidence manifest explicitly records the corresponding API and database scenario as `NOT_RUN`. No inspected evidence proves the complete FastAPI application, PostgreSQL schema/RLS/ledger behavior, OpenAPI conformance against a running API, full browser workflows, performance, backup/restore, deployment, security, or production financial calculations.

## Evidence classification

- **Structurally verified:** file existence, planning-document consistency claims, OpenAPI inventory/reference checks as recorded by the planning reports, traceability-script result as recorded in the task context, and review/approval records for the planning baseline.
- **Runtime evidence actually inspected:** two Playwright tests against `prototypes/design-mocks/lukla-ui-mock.html`; both are UI-only and pass in `frontend/artifacts/evidence/results.xml`.
- **Not proven:** anything requiring the production application, API, PostgreSQL, tenant/RLS enforcement, ledger persistence, cloud resources, external services, load, restore, or authorized financial-policy decisions.
- **Important rule:** presence of test source, installed tooling, a README claim, or a planning acceptance case is not execution evidence.

## Files and commands inspected

### Planning and implementation records

Inspected:

- `openspec/changes/lukla-ops-engine-planning/06-acceptance-tests.md` — declares “Specification only,” no application exists for execution, and all executable assertions are `NOT RUN`; AT-08 and dependent business assertions are `BLOCKED — decision needed`.
- `openspec/changes/lukla-ops-engine-planning/09-technical-blueprint-completion-plan.md` — planning phase marked complete/review-approved, while application implementation, runtime tests, and cloud deployment remain out of scope. Its verification section is structural/planning verification.
- `openspec/changes/lukla-ops-engine-planning/15-deployment-and-operations.md` — explicitly says no application, dependency, infrastructure, cloud, runtime, or price validation was performed; backup/restore and deployment claims are future gates.
- `openspec/changes/lukla-ops-engine-planning/16-test-harness-and-agent-verification.md` — explicitly says the harness is a future toolchain, commands are not run, and no runtime result is claimed.
- `openspec/changes/lukla-ops-engine-planning/artifacts/implementation/impl-phase-b-ops-harness-001.md` — records planning-only scope and says Playwright, Schemathesis, pytest-testcontainers, pgTAP, PostgreSQL, FastAPI runtime, cloud deployment, backup/restore, and scheduled-job delivery were not installed or run for that planning task.
- `openspec/changes/lukla-ops-engine-planning/artifacts/implementation/impl-007-tests.md` — records acceptance-test documentation and arithmetic checking, not application execution; it states all acceptance cases remain `NOT RUN`.
- `openspec/changes/lukla-ops-engine-planning/validate-blueprint.py` — located at the change root, not under `artifacts/`; the task record and planning reports describe its structural contract checks.
- `openspec/changes/lukla-ops-engine-planning/verify-traceability.ps1` — present at the change root. The supplied task context records the latest invocation as exit code 0; this verifies traceability assertions, not runtime behavior.
- `openspec/changes/lukla-ops-engine-planning/reviews/blueprint-contract-review.md` — records the proof gap: OpenAPI validator, Spectral, Schemathesis, PostgreSQL, Playwright, application runtime, cloud deployment, and database integration tests were not run.
- `openspec/changes/lukla-ops-engine-planning/19-business-defaults-register.md` — states no application, database, payroll, tax, legal, runtime, or deployment verification was performed and financial defaults remain production-blocked.

Read-only inventory command used:

```powershell
Get-ChildItem -Path . -Directory -Recurse -Force
Get-ChildItem -Path backend,frontend,openspec\changes\lukla-ops-engine-planning -File -Recurse -Force
```

The inventory found real `backend/`, `backend/tests/`, `backend/payroll-costing/tests/`, `frontend/tests/`, and `frontend/artifacts/evidence/` paths. It did not by itself prove execution.

## Category-by-category findings

### 1. Application behavior

**Partially evidenced only for a mock UI.** `frontend/tests/closing-01-mismatch.spec.ts` and `frontend/tests/view-04-stepper.spec.ts` run against `file://.../prototypes/design-mocks/lukla-ui-mock.html`, not the FastAPI service or a deployed frontend. The tests check a rendered ownership-mismatch modal/dismissal and a local tally stepper interaction.

**Not proven:** production routing, persistence, API integration, real workflow transitions, error handling, authorization, data mutation, or the AT-01..AT-10 and AT-R01..AT-R08 application assertions in `06-acceptance-tests.md`.

### 2. Database, RLS, and ledger

**Test source exists, execution is not proven.** `backend/tests/test_ledger.py` contains tests for API rollback, deferred balance constraints, positive amounts, and ledger immutability using admin and `lukla_app` SQLAlchemy engines. `backend/tests/test_payroll_invariants.py` contains restricted-role payroll/RLS-oriented tests and has a skip guard unless explicit disposable `DATABASE_URL` and `LUKLA_APP_DATABASE_URL` are supplied.

`backend/payroll-costing/README.md` documents a disposable PostgreSQL runner at `backend/tools/run_payroll_db_tests.py`, but no run output, JUnit file, database identity, or restoreable evidence was inspected. The planning documents explicitly say PostgreSQL integration tests were not run.

**Not proven:** RLS policy behavior under all tenant/legal-owner/beneficiary cases; FORCE RLS; pooled transaction context isolation; ledger balance/late-line protections; append-only/reversal behavior in a live database; duplicate-delivery/idempotency behavior; cross-tenant or BYPASSRLS negative controls; migration success on a disposable database.

### 3. API and OpenAPI

**Structurally evidenced; runtime conformance unproven.** Planning reports record unique operation IDs, local-reference resolution, schema/example checks, and traceability checks. `contracts/openapi.yaml` is a planning contract.

The inspected harness document recommends, but does not report running:

```text
pytest -q --junitxml=artifacts/evidence/api-results.xml
schemathesis run contracts/openapi.yaml --base-url "$API_BASE_URL" --report-junit-path artifacts/evidence/schemathesis-report.xml
```

**Not proven:** a running FastAPI service implements the contract, response/error conformance, authentication/service-auth behavior, idempotency, all 69 operation paths, Schemathesis results, or API-level AT/SCN outcomes. The payroll README specifically says the HTTP layer and PostgreSQL persistence are not implemented yet.

### 4. Browser and system workflows

**Two narrow mock-browser checks are evidenced.** `frontend/artifacts/evidence/manifest.json` has run ID `run-e2e-20261015083931`, Chromium tooling, and `exitCode: 0`. `frontend/artifacts/evidence/results.json` marks these as `PASS`:

- `UI-PROTO-VIEW03-MISMATCH-MODAL`
- `UI-PROTO-VIEW04-TALLY-STEPPER`

`frontend/artifacts/evidence/results.xml` contains two passing Playwright test cases. `frontend/playwright.config.ts` confirms the base URL is the standalone local mock HTML, with `trace: off`, `video: off`, and no backend URL.

The same `results.json` explicitly marks both `SCN-01-API` and `SCN-01-DB` as `NOT_RUN`, with `requestId: not-executed` and no evidence files.

**Not proven:** real frontend/backend integration, all six operational views, portal isolation, accessibility, offline/PWA behavior, API/database-backed browser workflows, failure traces, or the complete closing scenarios.

### 5. Performance and resilience

**No performance evidence inspected.** Planning documents define future checks and a 30-minute offline tally requirement, but no load, latency, concurrency, queue, retry, browser performance, database contention, or recovery test result was found.

**Not proven:** throughput/latency targets, ±70 scale behavior, concurrent tally writes, duplicate job delivery under load, lock contention, connection saturation, or offline queue recovery.

### 6. Backup and restore

**Not proven.** `15-deployment-and-operations.md` explicitly says backup retention, PITR, snapshots, S3 versioning/retention, restore policy, and restore success are not claimed. Required future evidence includes isolated restore, row counts/checksums, ledger continuity, smoke checks, RTO, and RPO observations. No backup policy output, snapshot ID, restore log, checksum report, or post-restore test evidence was inspected.

### 7. Deployment and operations

**Design only.** The AWS topology, ECS/RDS/S3/EventBridge/Lambda shape, secrets guidance, observability, rollback, and portable fallbacks are documented in `15-deployment-and-operations.md`. That file explicitly disclaims Docker build success, Terraform execution, AWS access, network validation, cloud deployment, scheduled-job delivery, and production readiness.

**Not proven:** image build/publish, infrastructure plan/apply, AWS account/resource existence, health/readiness endpoints, TLS/ingress/networking, scheduler-to-Lambda-to-API delivery, job idempotency in deployment, secrets injection/rotation, monitoring/alerts, rollback, or cost/pricing validation.

### 8. Security

**Design and test intent exist; enforcement is not proven.** The planning suite specifies JWT/session concepts, transaction-local tenant context, restricted database roles, RLS, secret redaction, service-principal checks, and negative controls. `16-test-harness-and-agent-verification.md` lists future checks for cross-tenant reads, cross-beneficiary access, cross-legal-owner files, leaked pooled context, forged service principals, owner/BYPASSRLS access, and altered idempotency payloads.

**Not proven:** actual authentication/token validation, role authorization, RLS enforcement, object ACL enforcement, secret non-disclosure in logs/errors/evidence, replay protection, service-principal authentication, dependency/container scanning, TLS/security headers, or penetration/red-team outcomes.

### 9. Financial calculations

**Arithmetic examples and module-level source exist; policy/runtime proof does not.** `06-acceptance-tests.md` gives illustrative arithmetic: seven-sewer wages total Rp 60,000; 3,000 Pass units × Rp 7 gives Rp 21,000 and Rp 7,000 each for three recipients. `impl-007-tests.md` records a PowerShell arithmetic check for those figures and the nondivisible Rp 100,000 ÷ 3 boundary.

`backend/payroll-costing/` contains model/service code and unit-test source for money math, rule gates, periods, wages, and bonus pools. Its README says those parts are implemented/tested, but no corresponding test output was inspected; the same README says HTTP and PostgreSQL persistence are not implemented.

**Not proven:** live calculation against production-shaped records, QC/mandor eligibility gates, no-double-pay repair behavior, payroll period/cutoff lifecycle, approved financial-rule enforcement in the API/database, meal-base policy, overhead denominator, bonus recipient policy, integer remainder destination, payment recording, ledger posting, or approval/audit evidence. The business-defaults register marks unresolved financial rules `PRODUCTION_BLOCKED`.

## Structural verification that should not be overstated

The following are useful planning checks, but they do not convert the system into runtime evidence:

- `openspec validate lukla-ops-engine-planning` recorded as passing.
- `validate-blueprint.py` structural OpenAPI/schema/reference checks recorded as passing.
- `verify-traceability.ps1` latest recorded invocation exited 0, with the task record noting its preserved FR-10.4 coverage warning.
- Review records marked the planning artifacts approved.
- Installed `node_modules`, Playwright, Python caches, and test directories exist.

None proves a running service, database, deployed environment, security boundary, financial authorization, or production readiness.

## Evidence status table

| Area | Evidence inspected | Status | What remains unproven |
|---|---|---|---|
| App behavior | Two mock Playwright tests | **Partial / mock-only** | Real app workflows and persistence |
| DB/RLS/ledger | Test source, migrations, planning schema | **Structural/source-only** | Live restricted-role DB results and invariants |
| API | OpenAPI and structural reports | **Structural** | Running API and Schemathesis/conformance |
| Browser | `results.json`/JUnit, 2 Chromium tests | **Partial** | Backend-connected/system-wide browser evidence |
| Performance | Planning requirements only | **Unverified** | Load, latency, concurrency, resilience |
| Backup/restore | Runbook requirements only | **Unverified** | Actual backup, isolated restore, RTO/RPO |
| Deployment | AWS topology/runbook only | **Unverified** | Build, provision, deploy, health, jobs, rollback |
| Security | Design and negative-control catalog | **Unverified** | Enforcement and adversarial results |
| Financial calculations | Source arithmetic and module test source | **Partial arithmetic only** | Authorized policy and live end-to-end calculations |

## Commands/evidence not run during this inspection

No test runner, database runner, Docker/Terraform command, cloud command, dependency install, or source edit was performed for this report. In particular, this report does **not** claim fresh execution of:

```text
pytest
playwright test
schemathesis
backend/tools/run_payroll_db_tests.py
Docker/Terraform/AWS deployment commands
```

The only runtime execution evidence relied upon is the already-present frontend evidence bundle (`manifest.json`, `results.json`, `results.xml`), whose own manifest identifies the run and its mock-only scope. The supplied task context also records the latest `verify-traceability.ps1` command as exit code 0; that is a traceability check, not runtime proof.

## Bottom line

The planning suite is substantially traceable and structurally checked. Runtime evidence currently supports only two local mock-browser interactions and illustrative/module-level source inspection. The critical unverified boundary remains the complete application and its trust boundaries: API, PostgreSQL/RLS/ledger, real browser workflows, performance, restore, deployment, security enforcement, and authorized financial calculation behavior.
