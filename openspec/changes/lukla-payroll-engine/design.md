# Technical Design: Payroll Engine Runtime Implementation

## Context
`lukla-ops-engine-planning` (Phases A–C, review-approved 2026-10-14) froze the product requirements (`specs/payroll-and-costing-engine/spec.md`), the OpenAPI 3.1 contract (69 operation IDs, `contracts/openapi.yaml`), and the database schema (`11-database-schema-spec.md`) for the Dynamic Payroll Engine, and explicitly authorizes no application code. The stack decision is FastAPI (Python) with plain PostgreSQL, business logic in Python and invariants in the database (D-1), jobs exposed as authenticated HTTP endpoints invoked by an external scheduler (no in-process cron), and one verification command producing a machine-readable evidence bundle.

Two facts constrain this design more than anything else. First, nine business items are `UNRESOLVED / PRODUCTION_BLOCKED` with `approved_by` and `effective_at` null (`19-business-defaults-register.md`), and the frozen contract answers this with `409 FINANCIAL_RULE_PENDING` rather than a development default. Second, no application source exists anywhere in the repository, so the module has no scaffold to extend and the workspace-hygiene gate does not yet permit the documented module location.

## Goals / Non-Goals

**Goals:**
- Implement the payroll and finance contract operations against the frozen `openapi.yaml` without changing any operation ID, path, schema, or enum.
- Make the financial rule gate a first-class runtime behaviour: unapproved rule versions block computation and persist nothing.
- Reconcile the two competing payroll schemas and the two overhead tables into one written decision each.
- Keep every monetary invariant in the database (append-only ledger, one wage credit per garment unit, one bonus accrual per assembly, one run per credit).
- Produce evidence keyed to the stable test IDs already defined for the payroll/QC acceptance tests, in the bundle format the harness contract requires.

**Non-Goals:**
- Resolving OQ-1..OQ-9 or authoring any business default. The engine ships a gate, not a policy.
- Amending `contracts/openapi.yaml`. The fields needed to express OQ-2/OQ-3/OQ-5/OQ-6 do not exist in `FinancialRuleFields`; that gap is escalated, not patched here.
- Editing frozen sources (`00-deconstruction.md`, BRD, PRD, `04-rbac-matrix.md`, `06-acceptance-tests.md`, `08-client-clarification-register.md`) or the root OpenSpec artifacts of `lukla-ops-engine-planning`.
- Implementing the touch-floor, QC, warehouse, or ledger modules this engine consumes.
- Cloud deployment, Terraform, and any claim of runtime evidence that has not actually been executed.

## Decisions

### 1. Gate-first: the engine ships refusal, not policy
- **Choice:** Every calculation resolves the rule versions it depends on and returns `409 FINANCIAL_RULE_PENDING` when any is not `APPROVED`; no monetary row is written in that path. No fallback constant, environment variable, or seeded demo value may substitute.
- **Rationale:** `specs/payroll-and-costing-engine/spec.md` states the operation "SHALL NOT use a development-only default", and `19-business-defaults-register.md` records that a draft proposal is not authorization evidence. A defaulted wage is unrecoverable once paid.
- **Alternatives Considered:** Ship proposed values behind a feature flag (rejected: the register forbids the value becoming a payroll instruction, and a flag is indistinguishable from a default at 3 a.m. on payroll Saturday); hard-code nothing and compute only the approved borongan aggregate (accepted as the intermediate step, see Decision 6).

### 2. `payroll_periods` is the container; `payroll_runs` is the versioned result
- **Choice:** `payroll_periods` holds the period window, timezone, cut-off, rule version reference, and lifecycle status. Each `calculateWeeklyPayroll` call creates or supersedes a `payroll_runs` row carrying `version`, `input_hash`, and `rule_version_id`, with `payroll_run_credits`, `payroll_items`, and `payroll_payments` hanging off the run. `wage_credits` remains the per-unit monetary fact assigned to a period, and `payroll_run_credits` links a run to the credits it consumed.
- **Rationale:** The contract already requires `approvePayroll` to carry `PayrollApproval{version, inputHash}` and `PayrollStatement` to expose `version` and `inputHash`; a mutable single-run model cannot honour that, and `payroll_run_credits` exists precisely to make the consumed credit set immutable per run.
- **Alternatives Considered:** Use `payroll_periods` alone as the run (rejected: no version or input hash, so approval cannot be pinned to what was approved); use `payroll_runs` alone and drop periods (rejected: `getBonusPool`, `calculateOverhead`, and `createPayrollPeriod` are period-scoped in the contract).

### 3. `overhead_events` records cost; `overhead_periods` records the allocation snapshot
- **Choice:** `recordOverhead` appends to `overhead_events` (append-only, with `authorized_by`). `calculateOverhead` writes the `overhead_periods` row holding `total_minor`, `produced_units`, and status for the month.
- **Rationale:** The schema defines both and never states their relationship; one is an event log and one is a derived aggregate, and `calculateOverhead` needs a single row to be idempotent against. The proposed basis enum `FIRST_PASS_FINISHED_UNITS_PROPOSED` fixes the denominator as a snapshot, which only an aggregate row can hold.
- **Alternatives Considered:** Derive the total on read from `overhead_events` and drop `overhead_periods` (rejected: the frozen schema names the table, and the produced-unit snapshot must not drift after month close).

### 4. Module location `backend/payroll-costing/` with an explicit allow-list amendment
- **Choice:** Place the module at `backend/payroll-costing/` as `docs/MODULES_ARCHITECTURE.md` targets, and extend `scripts/check_workspace_hygiene.py` `ALLOWED_ROOT_DIRS` with `backend` in a separate, reviewable change.
- **Rationale:** The hygiene script is a blocking CI job and its allow-list currently covers only `.git`, `.github`, `.agents`, `.vscode`, `docs`, `openspec`, `prototypes`, `scripts`, `tools`; creating the module without the amendment turns CI red on every PR. Keeping the amendment in its own commit keeps the gate change reviewable on its own merits.
- **Alternatives Considered:** Put the module in `prototypes/payroll-costing/` (allowed today, but this is production code, not a spike, and `AGENTS.md` scopes `prototypes/` to experimental work); relax the hygiene rule to "any directory" (rejected: it removes the isolation guarantee the gate exists for).

### 5. Invariants live in the database, the API stays thin
- **Choice:** `calculate_weekly_payroll(p_period_id, p_rule_version)` and `calculate_overhead_allocation(p_period_id, p_rule_version)` are PL/pgSQL routines invoked inside the request transaction; the FastAPI layer performs authorization, context installation, idempotency, and serialization only.
- **Rationale:** Matches D-1 ("business logic in Python; invariants in the database") and the ledger rules that a trigger enforces; it also makes the anti-double-credit guarantees testable with pgTAP independently of the HTTP layer.
- **Alternatives Considered:** Compute wages in Python and write results (rejected: two code paths would have to agree on the one-credit-per-unit rule, and the repair-no-double-credit rule is enforced by a partial unique index).

### 6. Approved aggregate first, per-recipient split gated
- **Choice:** `calculateWeeklyPayroll` may return `PayrollResult{status: CALCULATED, eligibleUnits, totalWages}` because the borongan aggregation is approved (FR-10.1, FR-9.1/FR-9.2 accrual basis). Any statement containing per-recipient `meal`, `bonus`, or a non-zero `reserve`, and both `approvePayroll` and `recordPayrollPayment`, remain gated until the referenced rule versions are `APPROVED`.
- **Rationale:** The meal *pool* level (percentage 10–15% of verified sewing wages, entered manually per period) is source-backed, but the per-sewer allocation basis (OQ-1) and the remainder destination (OQ-4) are not; AT-03 asserts pure borongan only and instructs that no meal amount be added to its totals. `PayrollStatement.reserve` exists in the contract while the BRD forbids allocating the remainder to a named account, so the field must stay zero, not become a destination.
- **Alternatives Considered:** Gate the whole calculation including the aggregate (rejected: it would make AT-03 unassertable although its arithmetic is fully approved); compute per-recipient meal with the pool percentage spread evenly (rejected: inventing the distribution rule OQ-1 is asking about).

### 7. Contract gaps are escalated, not patched
- **Choice:** Record, and do not silently work around, that `FinancialRuleFields` cannot express the OQ-2 bearer, the OQ-3 recipient policy, the OQ-5 uninspected-output handling, or the OQ-6 approver/payment method; that `bonusRecipientIds` is pinned to exactly three items while OQ-3 asks whether recipients are configurable; that `remainderPolicy` offers `RESERVE_PROPOSED` although the BRD forbids a reserve destination; and that `approvePayroll` is `FinancePayroll` while OQ-6 proposes an `Owner` final approver.
- **Rationale:** `18-parallelization-and-workstreams.md` §3 and §6 make a public-contract change a reopen of the Phase A review; a private field or a widened enum would be contract drift that the harness explicitly treats as `BLOCKED_CONTRACT_DRIFT`.
- **Alternatives Considered:** Add the missing fields in this change (rejected: it silently changes the frozen contract that frontend and harness work against).

### 8. Evidence-first verification
- **Choice:** Tests report the pre-defined stable IDs (`API-AT-03`, `DB-AT-03`, `API-AT-06`, `DB-AT-06`, `API-AT-07`, `DB-AT-07`, `API-AT-08`, `DB-AT-04`/`DB-AT-05`, `DB-ATR04`..`DB-ATR07`, `API-FR-10.1-weekly-payroll`, `DB-FR-10.2-pending`, `DB-FR-10.3-remainder-pending`, `DB-FR-10.4-overhead-gate`) and emit `results.json`, `results.xml`, `api-results.xml`, `db-results.xml`, `system-results.json`, and `manifest.json`. A layer that did not run is reported `NOT_RUN` or `BLOCKED`, never `PASS`.
- **Rationale:** The harness contract makes a missing layer a non-pass by construction, and AT-08 cannot pass at all while the remainder policy is unresolved; the honest report is `BLOCKED`, not a green tick.
- **Alternatives Considered:** Claim conformance from Schemathesis alone (rejected: it proves contract shape, not wage arithmetic or ledger invariants).

## Risks / Trade-offs

- **[Risk] The engine cannot be finished until business decisions land.** → *Mitigation:* the gate is the deliverable; `DB-FR-10.2-pending`, `DB-FR-10.3-remainder-pending`, and `API-AT-08` are specified as `BLOCKED` outcomes, so an unresolved rule produces a correct, reviewable result rather than a stalled branch.
- **[Risk] The contract cannot express OQ-2/OQ-3/OQ-5/OQ-6 outcomes.** → *Mitigation:* Decision 7 escalates through the Phase A reopen rule before any field is added; the engine implements only what the current enums allow and gates the rest.
- **[Risk] Upstream modules (MOD-01 ledger, MOD-04 MES/QC) do not exist.** → *Mitigation:* seed fixtures that satisfy the frozen schema (explicit UUIDs, `fixtureSetId`, tenant, legal owner, beneficiary) instead of substitute tables, so the same tests keep passing once the real producers arrive.
- **[Risk] Choosing the wrong payroll schema wastes the migration.** → *Mitigation:* Decision 2 is recorded before any DDL is written and is the first reviewable item in `tasks.md`.
- **[Risk] The `12%` example in the payroll spec is mistaken for a default.** → *Mitigation:* `06-acceptance-tests.md` records it as an illustrative fixture; the runtime reads the percentage only from an approved `financial_rule_versions` row and never from code.
- **[Risk] The hygiene allow-list amendment is treated as unrelated.** → *Mitigation:* it is the first task, in its own commit, with the module creation as its verification step.
- **[Trade-off] Gate-first means a demo shows refusals.** → Accepted: a visible `FINANCIAL_RULE_PENDING` is the accurate state of the business rules, and it is what the harness expects to assert.
