# Technical Plan: Lukla Payroll and Costing Backend

## Goal

Implement the approved payroll/costing runtime behind the frozen OpenAPI contract and existing FastAPI/database/auth/ledger conventions. The MVP path must calculate verified borongan wages, enforce approved financial rules, preserve integer-Rupiah arithmetic, prevent duplicate credits and payments, support immutable ledger evidence, and expose honest blocked states for unresolved policy decisions.

This plan covers the full backend scope in small, reviewable workstreams. It does not authorize changing frozen specifications, adding financial defaults, or pretending unfinished QC/MES systems are production inputs.

## Current Reality

- `backend/payroll-costing/` contains tested contract models and pure services, including the rule gate, period lifecycle, borongan aggregation, bonus pooling, and integer money arithmetic. Its HTTP layer and PostgreSQL persistence are not implemented (`backend/payroll-costing/README.md:58-61`).
- The pure wage entry point is `calculate_weekly_payroll(*, period_id, required_rules, units, currency) -> PayrollResult`; it gates before aggregation and delegates persistence to the repository (`backend/payroll-costing/src/services/wage_calculation.py:95-112`).
- The bonus entry point is `calculate_bonus_pool(*, period_id, required_rules, accruals, recipient_ids, remainder_policy, currency) -> BonusPool`; it rejects non-divisible pools rather than rounding or assigning a remainder (`backend/payroll-costing/src/services/bonus_pool.py:54-112`).
- `backend/payroll-costing/src/api/__init__.py` is currently empty. The shared API router includes only ledger routes (`backend/app/api/v1/__init__.py:1-5`).
- The existing ledger route establishes the integration shape: `get_db`, `AuthContext`, `get_current_auth_context`, request ID propagation, `Idempotency-Key`, and service invocation (`backend/app/api/v1/ledger.py:1-84`).
- Migration `008_double_entry_ledger.sql` establishes tenant-scoped ledger tables, append-only triggers, late-line protection, deferred balance validation, and RLS (`backend/migrations/008_double_entry_ledger.sql:1-174`). Payroll must call this ledger boundary rather than duplicate accounting writes.
- The authoritative operation index is `backend/payroll-costing/API_CONTRACTS.md:9-35`; the older routes in `docs/MODULES_ARCHITECTURE.md:99-122` are superseded.
- The approved design chooses `payroll_periods` as the period container and versioned `payroll_runs` as calculated results, and chooses `overhead_events` as the cost log plus `overhead_periods` as the allocation snapshot (`openspec/changes/lukla-payroll-engine/design.md:32-32`, with rationale in the surrounding Decisions section).
- Nine financial policy items remain unresolved and must produce `409 FINANCIAL_RULE_PENDING`; no fallback, demo constant, environment setting, or proposed rule may authorize money (`backend/payroll-costing/README.md:9-15`; `openspec/changes/lukla-payroll-engine/design.md:14-28`).
- The current checkout is `master` and the requested planning artifact is the only permitted file change. No implementation or test command was run for this planning task.

## Approach

1. Preserve the pure services and their unit tests as the financial calculation seam.
2. Add database migrations and repository/service adapters that load immutable, tenant-scoped facts and persist only after the rule gate succeeds.
3. Add thin FastAPI routes matching the frozen operation IDs and schemas, reusing shared auth, DB sessions, problem responses, request IDs, and idempotency conventions.
4. Register the payroll router in the shared app only after its repository boundary is real; never ship routes backed by an in-memory fake.
5. Use explicit fixture/adapters for unfinished QC/MES inputs. Fixtures must carry tenant, legal owner, beneficiary, stable IDs, and `fixtureSetId`; they must be visibly test-only and never report a production success.
6. Verify at unit, PostgreSQL/pgTAP, API, integration, and evidence-bundle layers. A skipped or unavailable layer is `NOT_RUN`/`BLOCKED`, not `PASS`.

## Dependency and Delegation Map

| Workstream | Can run in parallel with | Blocks | Owner-sized outcome |
|---|---|---|---|
| A. Shared scaffold/hygiene and contract inventory | B, C, D after interfaces are agreed | All app integration; CI acceptance | Backend module remains allowed and quality checks are reproducible |
| B. Financial-rule repository/gate adapter | C, D, E against the interface only | Wage/bonus calculation persistence and all gated mutations | Approved/pending rule resolution with no-write semantics |
| C. Database migrations, RLS, invariants | B, with A's migration numbering decision | Repository tests, API mutations, jobs | M006-M012 schema and database-enforced protections |
| D. Upstream fixture/adapters | B, C | End-to-end wage/bonus fixtures only | Explicit QC/MES read adapter; no fake production path |
| E. Payroll period/wage/bonus repositories | B, C, D interfaces | HTTP employee-facing operations | Idempotent run snapshots preserving pure service behavior |
| F. HTTP routes and shared app registration | A, B, E interface contracts | API/system verification | 15 frozen operation IDs wired to real dependencies |
| G. Jobs | C, E, F auth/readback contracts | Job verification and evidence bundle | Service-authenticated, single-run-per-period jobs |
| H. Evidence harness and acceptance fixtures | A, C, D, E, F incrementally | MVP verification sign-off | Machine-readable honest results and negative controls |
| I. Contract/policy escalations | Parallel with implementation, but not silently resolved | Per-recipient meal/bonus remainder/approval claims | Maintainer decisions or explicit blocked outcomes |

Recommended delegation: A, B, C, and D are independent subagent-sized starts. E depends on B/C/D schemas. F depends on E and the shared app patterns. G depends on F plus job schema. H can build the collector early but cannot assert passing runtime IDs until the relevant layers execute. I may proceed in parallel because it records blockers rather than changing behavior.

## Phases

### Phase 0 — Branch, scope, and interface freeze

**Outcome:** Establish implementation branches from an up-to-date non-`master` base and freeze the internal repository interfaces before DDL or route code.

**Target files:**
- `backend/payroll-costing/README.md`
- `backend/payroll-costing/API_CONTRACTS.md`
- `openspec/changes/lukla-payroll-engine/design.md` and `tasks.md` are read-only inputs for this task; do not edit them as part of implementation unless an approved artifact update is separately authorized.

**Interfaces/signatures to agree:**
- `RuleRepository.get_required_versions(tenant_id, rule_ids) -> Sequence[RuleReference]`
- `PayrollRepository.create_period(...) -> PayrollPeriodRecord`
- `PayrollRepository.calculate_run(...) -> PayrollRunRecord`
- `LedgerAdapter.post_transaction(...) -> LedgerTransactionRecord`
- `IdempotencyStore.begin_or_replay(tenant_id, operation_id, key, request_hash) -> Replay | NewRequest`

**Edge cases:** wrong base branch; accidental implementation on `master`; schema/contract operation ID drift; conflicting ownership of `payroll_items` and `wage_credits`.

**Stop condition:** Stop before migrations if the maintainer has not confirmed Decision 2 (`payroll_periods` plus `payroll_runs`), Decision 3 (`overhead_events` plus `overhead_periods`), or the workstream owner for wage credits.

**Verification:**
```powershell
git status --short --branch
git branch --show-current
openspec status --change "lukla-payroll-engine" --json
```
No source changes are complete until the branch is not `master` and the interfaces are recorded in the implementation branch's module documentation.

### Phase 1 — Hygiene, module quality gate, and shared adapters

**Outcome:** Make `backend/` an intentional production root and make the payroll package pass the repository's quality gate without adding dependencies.

**Target files:**
- `scripts/check_workspace_hygiene.py`
- `.github/workflows/ci.yml`
- `backend/payroll-costing/pyproject.toml`
- `backend/payroll-costing/src/api/__init__.py`
- new repository/adapter modules under `backend/payroll-costing/src/{repositories,adapters,services}` only if the existing layout requires them
- tests under `backend/payroll-costing/tests/`

**Signatures/schema changes:**
- Add no public operation yet.
- Define typed protocols for rule, payroll fact, ledger, idempotency, and auth-context adapters.
- Keep Python 3.11, Ruff, strict mypy, and pytest settings already declared in `pyproject.toml:1-35`.

**Edge cases:** import path collisions between package-local `src` and shared `backend/app`; no `Any` escape hatch; no new dependency; quality job must cover tests once tests exist.

**Stop condition:** Stop if the hygiene script rejects the intended module location, if CI needs a new package, or if the adapter interface requires changing the frozen OpenAPI contract.

**Verification:**
```powershell
python scripts/check_workspace_hygiene.py
Push-Location backend/payroll-costing; ruff check .; ruff format --check .; mypy src/ --strict; pytest -q; Pop-Location
```
For CI wiring, deliberately introduce and revert a lint-only failure in a disposable branch; do not leave it in the worktree.

### Phase 2 — Database migrations, tenant context, and financial invariants

**Outcome:** Add the PostgreSQL source of truth and database-enforced safety rules before route persistence.

**Target files:**
- `backend/migrations/006_payroll_rate_cards.sql`
- `backend/migrations/007_payroll_qc_inputs.sql`
- `backend/migrations/008_double_entry_ledger.sql` (read existing ownership; do not duplicate or rewrite it)
- `backend/migrations/009_payroll_core.sql`
- `backend/migrations/011_job_idempotency.sql`
- `backend/migrations/012_payroll_routines_rls.sql`
- PostgreSQL/pgTAP tests in the repository's existing database test location

**Schema changes:**
- M006: `rate_cards`, exclusion/range protection, `piece_rate_snapshots`, and one snapshot per `garment_unit_id`.
- M007: `garment_assemblies`, `assembly_components`, `qc_inspections`, and `qc_defects`; distinguish QC pass, repair, reject, and uninspected states.
- M009: `financial_rule_versions`, `eligibility_events`, `payroll_periods`, `payroll_runs`, `payroll_run_credits`, `payroll_items`, `payroll_payments`, `wage_credits`, `payroll_adjustments`, `qc_bonus_accruals`, `overhead_events`, and `overhead_periods`.
- M011: `job_runs` and `idempotency_records` with unique `(tenant_id, key, operation_id)` and request/payload hashes.
- M012: `set_request_context`, `calculate_weekly_payroll(p_period_id, p_rule_version)`, `calculate_overhead_allocation(p_period_id, p_rule_version)`, grants, and `ENABLE/FORCE ROW LEVEL SECURITY` for every tenant-scoped payroll table.

**Database signatures/invariants:**
- Stored routines must refuse unapproved rules before monetary inserts.
- One `wage_credits` row per `garment_unit_id`; one `qc_bonus_accruals` row per `assembly_id`.
- A run snapshots contributing credit IDs, rule version, amounts, version, and `input_hash`; approved runs cannot be recalculated in place.
- Payment rows reference an approved run and external evidence; payment recording does not initiate a bank transfer.
- Ledger data remains append-only and balanced through the existing ledger routine/triggers.
- Tenant context must be installed inside the transaction before reads/writes.

**Edge cases:** concurrent calculation of one period; late credits after approval/payment; empty production month; same idempotency key with changed payload; RLS query without tenant context; retry after commit but before response; repair/reinspection of one unit; non-divisible bonus pool; integer overflow/negative amounts/currency mismatch.

**Stop condition:** Stop all API persistence if any pgTAP invariant fails, if RLS can read another tenant, if a pending rule inserts a monetary row, or if the chosen migration duplicates existing ledger ownership.

**Verification:**
```powershell
# Use the repository's configured PostgreSQL migration command; record the exact command and database image/version used.
# Then run the existing database test command plus the payroll pgTAP suite.
pytest -q backend/tests -k "ledger or payroll"
```
Required database assertions: `LEDGER_IMMUTABLE` on ledger update/delete; duplicate unit credit rejected; duplicate assembly bonus rejected; non-owner tenant read returns zero rows without context; concurrent idempotency creates one record; pending-rule transaction leaves no monetary rows.

### Phase 3 — Rule registry and period lifecycle persistence

**Outcome:** Persist financial rule versions and period state transitions while preserving the existing pure services.

**Target files:**
- `backend/payroll-costing/src/repositories/rules.py`
- `backend/payroll-costing/src/repositories/periods.py`
- `backend/payroll-costing/src/services/rule_registry.py` (adapter only if needed; preserve existing pure implementation)
- `backend/payroll-costing/src/services/payroll_periods.py`
- contract-shaped models under `backend/payroll-costing/src/models/`
- focused tests under `backend/payroll-costing/tests/`

**Signatures/schema changes:**
- `list_financial_rules(tenant_id, filters) -> Sequence[FinancialRule]`
- `propose_financial_rule(tenant_id, actor_id, fields, idempotency) -> FinancialRule`
- `approve_financial_rule(tenant_id, rule_id, owner_id, evidence_file_id, idempotency) -> FinancialRule`
- `create_payroll_period(tenant_id, request, actor) -> PayrollPeriod`
- `transition_period(period_id, expected_status, target_status, actor) -> PayrollPeriod`

**Rules:** proposals are `PENDING`; only `Owner` may approve; evidence is required; `APPROVED` is immutable; `Asia/Jakarta`, inclusive start, exclusive end, and exact `HH:MM:00` cutoff validation follow the contract.

**Edge cases:** approval of a nonexistent/tenant-mismatched rule; repeated approval; period overlap; invalid timezone/cutoff; transition from `PAID` or `REVERSED`; rule version not applicable to period.

**Stop condition:** Stop if a proposed rule can pass the calculation gate, if approval lacks evidence, or if period transitions allow an approved/paid run to mutate.

**Verification:**
```powershell
Push-Location backend/payroll-costing; pytest -q tests/test_financial_rules.py tests/test_payroll_periods.py; Pop-Location
pytest -q backend/tests -k "payroll_period or financial_rule"
```

### Phase 4 — Upstream QC/MES adapters and wage/bonus repositories

**Outcome:** Connect verified production facts to the existing pure calculations without claiming QC/MES implementation.

**Target files:**
- `backend/payroll-costing/src/adapters/qc_mes.py`
- `backend/payroll-costing/src/repositories/production_facts.py`
- `backend/payroll-costing/src/repositories/payroll_runs.py`
- `backend/payroll-costing/src/repositories/payments.py`
- `backend/payroll-costing/src/services/payroll_runtime.py`
- `backend/payroll-costing/src/services/overhead.py`
- explicit fixture/adapters under `backend/payroll-costing/tests/fixtures/`

**Signatures:**
- `load_eligible_units(tenant_id, period_id) -> Sequence[EligibleUnit]`
- `load_bonus_accruals(tenant_id, period_id) -> Sequence[BonusAccrual]`
- `calculate_and_persist_weekly_payroll(tenant_id, period_id, rule_version, actor) -> PayrollResult`
- `get_statement(tenant_id, period_id, version=None) -> PayrollStatement`
- `approve_payroll(tenant_id, period_id, version, input_hash, actor) -> PayrollApproval`
- `record_payroll_payment(tenant_id, period_id, evidence, actor, idempotency) -> PaymentEvidence`
- `record_overhead(...) -> OverheadEvent`; `calculate_overhead(...) -> OverheadResult`

**Behavior:** call `require_approved` before reading/writing monetary facts where the contract requires gate-first behavior; include only `QC_PASS` units with immutable rate snapshots; leave uninspected/repair units unpaid; never create a second credit after repair/reinspection; calculate meal allowance only according to the approved proportional verified-borongan rule; hold `reserve` at zero while OQ-4 is unresolved; refuse non-divisible three-way bonus pools.

**Fixture boundary:** fixture data must be marked with `fixtureSetId`, tenant, legal owner, beneficiary, and source metadata. It may stand in for `sewing_tallies`, `garment_units`, `qc_inspections`, and `qc_bonus_accruals` in tests only. No production adapter may silently fall back to fixtures.

**Edge cases:** zero eligible units returns `NO_OUTPUT`; QC pending/repair/reject contributes zero; mixed currencies or negative rates fail; duplicate unit/accrual inputs fail; seven operators and proportional allowance use integer minor units; a pool of 21,000 split three ways yields 7,000 each; a pool with remainder blocks all payout.

**Stop condition:** Stop if an upstream adapter invents a successful QC result, if an unapproved rule permits a monetary insert, or if a pure-service unit test changes behavior without an approved domain decision.

**Verification:**
```powershell
Push-Location backend/payroll-costing; pytest -q tests/test_wage_calculation.py tests/test_bonus_pool.py tests/test_payroll_runtime.py; Pop-Location
```
Required regression IDs: `API-AT-03`, `DB-AT-03`, `API-AT-06`, `DB-AT-06`, `API-AT-07`, `DB-AT-07`, `DB-AT-04`, `DB-AT-05`.

### Phase 5 — Thin HTTP layer and shared FastAPI registration

**Outcome:** Expose the frozen operation IDs through the existing app with real DB/auth/ledger/idempotency dependencies.

**Target files:**
- `backend/payroll-costing/src/api/routers.py` or operation-specific modules under `src/api/`
- `backend/payroll-costing/src/api/dependencies.py`
- `backend/app/api/v1/payroll.py`
- `backend/app/api/v1/__init__.py`
- `backend/app/main.py` only if registration requires an existing app change
- shared schemas only where the frozen contract maps to existing `backend/app/schemas/problem.py`

**Operations/signatures:** implement exactly the `operationId`, path, roles, request/response models, and error responses in `API_CONTRACTS.md:9-35`: periods, weekly calculation/statement/bonus/approval/payment, overhead record/allocation, financial rules, Saturday/monthly jobs, and job readback.

Route handlers should be thin: parse Pydantic input, obtain `Request`, `AuthContext`, and `Session`, enforce role/service scope, begin idempotency, install tenant context, call a repository/service, commit atomically, and serialize the contract model. Reuse the shared request-ID/problem exception path; do not create a second auth or error framework.

**Idempotency/concurrency:** hash the canonical request body plus relevant path parameters; same tenant/operation/key and same hash replays the original response; changed hash returns `409 IDEMPOTENCY_CONFLICT`; acquire the period/run lock before calculation/approval/payment; commit ledger and payroll records in one transaction where the operation requires both.

**Edge cases:** missing/short/long idempotency key; duplicate concurrent requests; employee JWT on service endpoint; missing tenant context; wrong role; statement for nonexistent or other-tenant period; approval with stale `version`/`inputHash`; payment before approval or repeated external reference.

**Stop condition:** Stop registration if any route uses a fake/in-memory store, if OpenAPI operation IDs or schemas drift, if a pending-rule request writes a monetary row, or if a ledger post can commit separately from its payroll payment record.

**Verification:**
```powershell
pytest -q backend/tests -k "ledger or auth or idempotency"
# Run the repository's API test command against the shared FastAPI app.
python -m pytest -q backend/tests
# Run Schemathesis against the frozen contract, scoped to payroll/finance paths.
schemathesis run openspec/changes/lukla-ops-engine-planning/contracts/openapi.yaml --base-url http://127.0.0.1:<test-port> --include-path /payroll --include-path /payroll-periods --include-path /overhead --include-path /financial-rules --include-path /internal/jobs --include-path /jobs
```
Also assert a gated `409 FINANCIAL_RULE_PENDING`, an unchanged-payload replay, and changed-payload `409 IDEMPOTENCY_CONFLICT`.

### Phase 6 — Service-authenticated jobs and accounting evidence

**Outcome:** Make weekly payroll and monthly overhead schedulable by an external scheduler without in-process cron or duplicate execution.

**Target files:**
- `backend/payroll-costing/src/services/jobs.py`
- `backend/payroll-costing/src/repositories/jobs.py`
- `backend/payroll-costing/src/api/jobs.py`
- job-focused migrations/tests if Phase 2 exposes a gap

**Signatures:**
- `run_saturday_payroll_job(tenant_id, period_id, service_principal, idempotency_key) -> JobRun`
- `run_monthly_overhead_job(tenant_id, period_id, service_principal, idempotency_key) -> JobRun`
- `get_job(tenant_id, job_id, actor) -> JobRun`

**Behavior:** only `serviceAuth` with `ServicePayrollJob`/`ServiceOverheadJob` may invoke jobs; one row per `(kind, period)`; `RUNNING`, `SUCCEEDED`, `BLOCKED`, `FAILED`; pending rules produce `BLOCKED`; retries replay or resume safely; job payment writes link to an approved payroll run and external accounting evidence.

**Edge cases:** duplicate delivery, concurrent delivery, service token presented as employee JWT, job failure after ledger post, pending rule, zero-output month, late credits after a paid run.

**Stop condition:** Stop if a retry can produce a second ledger/payment record, if a job reports `SUCCEEDED` on a pending rule, or if the endpoint introduces an in-process scheduler.

**Verification:**
```powershell
pytest -q backend/tests -k "job or payroll_payment or idempotency"
```
Use one idempotency key twice and concurrent requests; assert one run/payment and correct terminal status.

### Phase 7 — Evidence harness, negative controls, and MVP boundary

**Outcome:** Produce a machine-readable evidence bundle that distinguishes pass, not-run, blocked, and failed outcomes.

**Target files:**
- repository-approved harness command/configuration location
- `backend/payroll-costing/tests/evidence/`
- collector output directory outside source roots, as configured by the harness
- no source/spec/task changes unless a separate approval explicitly authorizes them

**Evidence:** emit `results.json`, `results.xml`, `api-results.xml`, `db-results.xml`, `system-results.json`, and `manifest.json`. Map `API-AT-03`, `DB-AT-03`, `API-AT-06`, `DB-AT-06`, `API-AT-07`, `DB-AT-07`, `DB-AT-04`, `DB-AT-05`, `DB-ATR04`..`DB-ATR07`, `API-FR-10.1-weekly-payroll`, `DB-FR-10.2-pending`, `DB-FR-10.3-remainder-pending`, and `DB-FR-10.4-overhead-gate`.

**Required blocked assertions:** `API-AT-08` remains `BLOCKED` while remainder policy is unresolved; no floor payout, reserve account, fourth recipient, hidden-loss rule, or unapproved meal/recipient policy is produced.

**Edge cases:** missing required output; missing requirement ID; unavailable DB/API layer; test process crash; stale fixture version; evidence generated from the wrong commit.

**Stop condition:** Stop MVP sign-off if the collector exits zero while a required layer is missing, if a negative control passes, or if any result claims `PASS` without an executed test record.

**Verification:**
```powershell
# Run the repository-approved collector command once its implementation is available.
# Then run its required negative controls:
# 1. remove one required requirement ID -> exit 1
# 2. remove one required output -> exit non-zero
# 3. include FAIL -> exit non-zero
```
Record actual commands, commit SHA, database version, fixture set, and outcomes in the evidence manifest. Do not report unexecuted commands as passing.

## Acceptance Criteria

- The shared FastAPI app exposes the frozen payroll/finance operation IDs with the exact paths and role/service-scope behavior; no superseded sketch route is added.
- Quality-passed units with immutable piece-rate snapshots are the only wage inputs. Uninspected, repair, rejected, or merely tallied output earns no wage until the authoritative upstream state qualifies it.
- The existing pure services retain their tested integer arithmetic and refusal semantics: no floating-point money, no negative amount, no duplicate repair credit, and no rounded/non-divisible three-way bonus payout.
- Every mutation is tenant-scoped, idempotent, transactionally safe under retry/concurrency, and protected by the database constraints/RLS described in Phase 2.
- Pending financial rules fail closed with `409 FINANCIAL_RULE_PENDING` and no monetary rows written; proposals never pass the gate.
- Payroll approval pins run `version` and `inputHash`; payment records reference only an approved run and existing accounting evidence; retries cannot double-pay.
- Ledger entries are appended through the existing immutable double-entry boundary and cannot be updated, deleted, late-appended, or left unbalanced.
- Explicit QC/MES fixtures/adapters are isolated to tests and clearly marked; no fixture can be selected by a production request as a silent fallback.
- Zero-output payroll/overhead is a valid `NO_OUTPUT` result, not a divide-by-zero failure; unresolved policy outcomes are `BLOCKED`, not fabricated values.
- The evidence collector distinguishes `PASS`, `FAIL`, `NOT_RUN`, and `BLOCKED`, and its negative controls fail as designed.
- All phase-specific commands have actually run before their phase is called complete. This plan records no test pass for the planning-only task.

## Non-Goals

- No edits to frozen OpenAPI, product requirements, database schema specifications, design, or task records as part of implementation unless a separately approved contract/spec change is opened.
- No new dependency without maintainer approval.
- No QC/MES, touch-floor, warehouse, or ledger reimplementation inside payroll.
- No hard-coded wage rate, 12% default, meal bearer, bonus remainder destination, recipient policy, payment method, or final approver beyond the approved contract.
- No bank transfer initiation; payroll records accounting/payment evidence only.
- No in-process scheduler.
- No claim that the project is MVP-ready until the acceptance criteria and evidence bundle are executed.

## Known Traps and Required Controls

1. **Money integer arithmetic:** use `amount_minor`/`bigint`, explicit currency checks, and integer allocation. Never use floating point or implicit rounding.
2. **Idempotency and concurrency:** uniqueness is `(tenant_id, operation_id, key)` plus request hash; lock the period/run before calculation/approval/payment; handle commit-then-retry replays.
3. **Immutable ledger:** use existing `append_ledger_transaction`/ledger service; never update/delete ledger rows or append lines after the originating transaction commits.
4. **Tenant/RLS:** set request context inside every transaction; test missing context and cross-tenant reads/writes under a non-owner role.
5. **Pending-rule no-write path:** resolve and validate all required rules before monetary inserts; roll back the entire request if any rule is not `APPROVED`.
6. **Explicit mock boundaries:** fixtures must be named, tenant-scoped, source-labelled, and test-only; a missing upstream record must be `NO_OUTPUT`, validation failure, or blocked—not synthesized production success.
7. **Versioned approval:** freeze contributing credit IDs, rule IDs, amounts, `version`, and `inputHash`; late credits go to a later open period and never mutate a paid run.
8. **Policy gaps:** OQ-1..OQ-9, especially meal allocation, bonus remainder, recipient configuration, QC treatment, approver, and payment method, remain escalation items. Do not infer policy from examples such as 12%.
9. **Schema ownership:** payroll owns its tables; MOD-01 owns ledger tables; MOD-04 owns production/QC facts. Do not duplicate tables to avoid an integration dependency.
10. **Framework integration:** reuse the existing FastAPI exception, auth, database, request-ID, and idempotency patterns rather than introducing a second application stack.

## Risks

| Risk | Impact | Mitigation / stop rule |
|---|---|---|
| Frozen contract cannot express unresolved policy | Incorrect payouts or contract drift | Gate behavior; record `BLOCKED`; reopen contract review before adding fields/enums. |
| Existing migration numbering/ownership conflicts | Destructive or duplicate DDL | Inventory all migrations and table owners before M006-M012; stop on collision. |
| PostgreSQL/RLS differs between local and CI | Tenant or balance invariant failure | Run migration and pgTAP tests against the same supported PostgreSQL version used by CI; record version in manifest. |
| Ledger and payroll commits split | Accounting mismatch or double payment | One DB transaction and existing ledger service; test failure/retry boundaries. |
| Upstream modules remain unfinished | False confidence in end-to-end result | Explicit fixtures/adapters with no production fallback; mark unavailable layers `BLOCKED`/`NOT_RUN`. |
| Parallel branches touch shared schema | Merge-order conflicts and duplicate ownership | Use the dependency table and branch chain; one owner for `payroll_items`/`wage_credits`; merge migrations sequentially. |
| Hidden policy defaults enter configuration | Irreversible financial error | Code review checklist rejects constants/env defaults; pending gate test must inspect row counts after refusal. |

## Worklog

| Date | Activity | Evidence | Result |
|---|---|---|---|
| 2026-10-15 | Read governing instructions and approved runtime artifacts | `c:\Users\lenovo\.copilot\instructions\copilot-instructions.md`; `openspec/changes/lukla-payroll-engine/design.md`; `tasks.md` | Planning-only constraints and approved decisions captured. |
| 2026-10-15 | Searched payroll implementation and integration patterns | Semantic search results; `backend/payroll-costing/README.md:58-61`; `API_CONTRACTS.md:9-35`; `src/services/wage_calculation.py:95-112`; `src/services/bonus_pool.py:54-112` | Confirmed pure services exist; HTTP/PostgreSQL do not. |
| 2026-10-15 | Inspected shared FastAPI/auth/ledger conventions | `backend/app/api/v1/ledger.py:1-84`; `backend/app/api/v1/__init__.py:1-5`; `backend/app/main.py`; `backend/migrations/008_double_entry_ledger.sql:1-174` | Confirmed reusable DB/auth/problem/request-ID/ledger patterns and current router registration boundary. |
| 2026-10-15 | Checked workspace state | `git status --short --branch; git worktree list` | Checkout is `master`; no implementation was performed. |
| 2026-10-15 | Wrote this plan | `openspec/changes/lukla-payroll-engine/artifacts/technical-plan-001.md` | Only permitted planning artifact was created. Tests were not run. |

## Implementation Handoff

- **Scope:** Start with Phase 0, then Phase 1. Do not implement source code from this artifact in the current planning task.
- **Inspect first:** `openspec/changes/lukla-payroll-engine/design.md`, `tasks.md`, `backend/payroll-costing/README.md`, `API_CONTRACTS.md`, `backend/app/api/v1/ledger.py`, `backend/app/core/auth.py`, `backend/app/core/database.py`, `backend/app/services/idempotency.py`, `backend/app/services/ledger.py`, and all existing migrations.
- **Tests:** Run the exact phase commands after each phase; preserve the existing payroll unit suite before and after adapter changes. Use interactive/local browser verification only if the frontend View 06 work is later included; browser verification is out of scope for this backend plan.
- **Stop if:** on `master`; a maintainer has not confirmed unresolved policy handling; contract/schema drift is required; a migration duplicates an owned table; pending-rule path writes money; tenant isolation fails; retry can double-pay; or a proposed fixture can be used as production data.
- **Handoff status:** This is a technical plan only. No source code, frozen spec, or task record was edited, and no tests were run for this artifact.
