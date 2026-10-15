# Payroll & Costing Module (MOD-05)

Dynamic Payroll Engine for the Lukla Operations Engine: weekly piece-rate wages (borongan), floating meal allowance (10–15%), 3-way QC bonus pool, and monthly factory overhead allocation.

## The frozen contract is the source of truth

This module implements the OpenAPI 3.1 contract authored during planning. The sketch routes in `docs/MODULES_ARCHITECTURE.md` (`/api/v1/payroll-rates`, `/api/v1/worker-calculations`) are superseded and must not be implemented.

- Contract: `openspec/changes/lukla-ops-engine-planning/contracts/openapi.yaml`
- Database schema: `openspec/changes/lukla-ops-engine-planning/11-database-schema-spec.md`
- Runtime requirements: `openspec/changes/lukla-payroll-engine/specs/payroll-engine-runtime/spec.md`
- Plan, decisions, and checklist: `openspec/changes/lukla-payroll-engine/`

## Gate first

Nine business rules are `UNRESOLVED / PRODUCTION_BLOCKED` (`19-business-defaults-register.md`, OQ-1..OQ-9). When a calculation references a rule version that is not `APPROVED`, this module MUST return `409 FINANCIAL_RULE_PENDING` and persist no monetary amount. Never add a fallback constant, environment variable, or demo value in its place, and never treat a proposal as an approval.

## Decisions before database migrations

- **Periods and runs (Decision 2):** `payroll_periods` holds the window, timezone, cut-off, referenced rule version, and lifecycle status. `payroll_runs` holds each versioned calculation with its `version`, `input_hash`, and rule version; `payroll_run_credits` records which `wage_credits` that run consumed. `payroll_items` and `payroll_payments` belong to the run. Schema §4 defines the period and wage credits; §8 defines the run and related tables. This preserves the contract's `PayrollApproval{version, inputHash}` pin. Rejected: using only a mutable period as the run (cannot pin approval to a calculation) or dropping periods in favour of runs (period-scoped operations need a stable container).
- **Overhead events and periods (Decision 3):** `recordOverhead` appends authorized cost to `overhead_events` (schema §4); `calculateOverhead` writes a monthly allocation snapshot to `overhead_periods` (schema §8) with `total_minor`, `produced_units`, and status. Rejected: calculating only on read and dropping the snapshot, because the frozen schema requires it and the denominator must not drift after close.
- **Location and hygiene (Decision 4):** This production module lives in `backend/payroll-costing/`, not `prototypes/`; `scripts/check_workspace_hygiene.py` permits `backend` explicitly, without admitting arbitrary root directories. The blocking payroll CI job checks this module only. Maintainer approval for this placement and shared-gate amendment is recorded in the approved OpenSpec design and implementation request. Rejected: putting production code in `prototypes/` or removing the root allow-list.

These decisions authorize the schema shape, not unresolved payout policies. OQ-1..OQ-9 remain gated; do not author a migration or monetary default on the strength of this README alone.

## Boundaries

Read-only inputs, owned by other modules:

- `sewing_tallies` with status `VERIFIED`, and `garment_units` with status `QC_PASS` carrying a `piece_rate_snapshots` reference
- `qc_bonus_accruals` (written by the QC routine), `rate_cards`, and the ledger tables owned by MOD-01

Written by this module:

- `financial_rule_versions`, `payroll_periods`, `payroll_runs`, `payroll_run_credits`, `payroll_items`, `payroll_payments`, `wage_credits`, `payroll_adjustments`, `overhead_events`, `overhead_periods`, `job_runs`, `idempotency_records`

## Layout

```
backend/payroll-costing/
├── src/
│   ├── api/        # HTTP routers bound 1:1 to contract operationIds (not implemented yet)
│   ├── models/     # contract-shaped pydantic schemas (Money, Problem, financial rules)
│   ├── services/   # the financial rule gate, the rule registry, domain errors
│   └── utils/      # integer minor-unit arithmetic
├── tests/          # pytest suite
├── API_CONTRACTS.md
├── pyproject.toml
├── requirements.txt
└── requirements-dev.txt
```

## Local checks

```bash
cd backend/payroll-costing
py -3.11 -m venv .venv
.venv\Scripts\python -m pip install -r requirements-dev.txt
.venv\Scripts\python -m pip check
.venv\Scripts\ruff check .
.venv\Scripts\ruff format --check .
.venv\Scripts\mypy src/ --strict
.venv\Scripts\python -m pytest -q
```

Use the repository-local Python 3.11 environment, not globally installed tools. `pip check` prints `No broken requirements found.` on a valid installation. The same quality checks run in `.github/workflows/ci.yml`.

### Disposable PostgreSQL regression

Use a reachable loopback PostgreSQL instance and an existing `lukla_app` login
without SUPERUSER, BYPASSRLS, CREATEDB, or CREATEROLE. Provision that role using
approved cluster administration before running tests; this command never changes
cluster roles. Supply explicit admin and application URLs (passwords must be URL
encoded). The runner rejects remote hosts and privileged application credentials,
creates one unique `payroll_revision_*` database, applies exactly migrations
001/006/007/008/009/011/012, runs restricted-role tests, and drops only the
database it created, including when tests fail. It never falls back to an ambient
`DATABASE_URL`.

```powershell
cd backend/payroll-costing
.venv\Scripts\python ..\tools\run_payroll_db_tests.py `
	--admin-url "postgresql+psycopg://postgres@127.0.0.1:55432/postgres" `
	--app-url "postgresql+psycopg://lukla_app:YOUR_LOCAL_PASSWORD@127.0.0.1:55432/postgres"
```

Neither URL is printed by the runner. The application login must be able to
connect to the maintenance database specified in its URL.

## Status

The financial rule registry, the payroll period lifecycle, the weekly borongan calculation, and the quality bonus pool are implemented and tested: the contract schemas for rules, periods, calculation results, and bonus pools; the rule gate; the proposal and approval service; the period transition guard; the quality-passed-only wage aggregation; the three-way bonus split that refuses a non-divisible pool; and the integer money arithmetic. The HTTP layer and the PostgreSQL persistence are not implemented yet; the router lands with the real repository so that no endpoint ships against a fake store. Work proceeds through the phases in `openspec/changes/lukla-payroll-engine/tasks.md`.

