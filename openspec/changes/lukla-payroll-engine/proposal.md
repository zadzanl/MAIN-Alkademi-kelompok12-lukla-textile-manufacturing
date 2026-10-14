# Proposal: Payroll Engine Runtime Implementation

## Why
The `lukla-ops-engine-planning` change froze the product requirements, the OpenAPI 3.1 contract, and the database schema for the Dynamic Payroll Engine (piece-rate borongan, floating meal allowance, 3-way QC bonus pool, monthly overhead allocation), but it authorizes no application code. The repository currently has no runnable backend at all: root holds only configuration, `docs/`, `openspec/`, `prototypes/`, and `scripts/`.

Implementation cannot start from the frozen documents alone, because they leave four things undecided that a coder would otherwise invent: which of the two competing payroll schemas is authoritative (`payroll_periods`/`wage_credits` in schema §4 versus `payroll_runs`/`payroll_run_credits`/`payroll_items`/`payroll_payments` in §8), how `overhead_periods` relates to `overhead_events`, where the module physically lives given the workspace-hygiene allow-list, and how the financial rule gate is enforced at runtime rather than in prose. This change resolves those four by written decision, and scopes the runtime work so that the nine business items still marked `UNRESOLVED / PRODUCTION_BLOCKED` (`19-business-defaults-register.md`, OQ-1..OQ-9) block computation instead of being silently defaulted.

## What Changes
- Add the payroll runtime module (FastAPI + plain PostgreSQL) implementing the frozen contract operations `createPayrollPeriod`, `listPayrollPeriods`, `calculateWeeklyPayroll`, `getPayrollStatement`, `getBonusPool`, `approvePayroll`, `recordPayrollPayment`, `recordOverhead`, `calculateOverhead`, `listFinancialRules`, `proposeFinancialRule`, and `approveFinancialRule`, plus the service-authenticated jobs `runSaturdayPayrollJob`, `runMonthlyOverheadJob` and their readback `getJob`.
- Add the payroll/QC database migrations (M006–M009, M011–M012 subset): rate snapshots and garment units, assemblies and QC inspections, the append-only ledger, financial rule versions, eligibility events, versioned payroll runs, overhead periods, and job/idempotency records, with `ENABLE`/`FORCE ROW LEVEL SECURITY` and the `calculate_weekly_payroll` / `calculate_overhead_allocation` routines.
- Enforce the financial rule gate at runtime: an operation that resolves a rule version whose status is not `APPROVED` returns `409 FINANCIAL_RULE_PENDING` and persists no monetary amounts.
- Record the schema reconciliation decisions (period versus run, overhead cost events versus allocation snapshot) and the module location decision, including the workspace-hygiene allow-list amendment that `backend/` requires.
- Emit machine-readable verification evidence keyed to the stable test IDs already defined for AT-03, AT-06, AT-07, AT-08, and AT-R04..AT-R07.

Out of scope: resolving OQ-1..OQ-9, amending `contracts/openapi.yaml` (that requires the Phase A review reopen rule), editing frozen source documents, cloud deployment, and the QC/touch-floor modules that produce this engine's inputs.

## Capabilities

### New Capabilities
- `payroll-engine-runtime`: Versioned payroll run lifecycle, calculation-time financial rule enforcement, verified-output-only wage eligibility, idempotent service-authenticated job invocation, tenant-isolated payroll data access, and machine-readable payroll verification evidence.

### Modified Capabilities
*(None; this change adds a runtime capability and does not alter the product requirements held by `payroll-and-costing-engine` in `lukla-ops-engine-planning`.)*

## Impact
- **Backend:** Adds `backend/payroll-costing/` (module structure `src/{models,services,utils,api}` plus `README.md` and `API_CONTRACTS.md` per `docs/MODULES_ARCHITECTURE.md`).
- **CI:** Adds a payroll lint/test job and extends `scripts/check_workspace_hygiene.py` `ALLOWED_ROOT_DIRS` with `backend`, because the current allow-list rejects the documented module location and would fail the blocking `workspace-hygiene` job.
- **Database:** Adds migrations for fifteen payroll/QC tables plus the ledger tables they depend on, and the `FORCE ROW LEVEL SECURITY` policies and routines listed above.
- **Contract:** Consumes `contracts/openapi.yaml` as authored; no operation ID, path, schema, or enum is changed. Fields that cannot express OQ-1/OQ-2/OQ-3/OQ-5/OQ-6 outcomes are recorded as a contract gap for a separate amendment.
- **Dependencies:** `MOD-01` (ledger + RBAC) and `MOD-04` (MES + QC) per `BRD §12.1`; until those exist, this engine reads seeded fixtures that satisfy the frozen schema rather than inventing substitute tables.
