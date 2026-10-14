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
pip install -r requirements-dev.txt
ruff check .
ruff format --check .
mypy src/ --strict
pytest -q
```

All four must exit 0. The same four commands run as the blocking `payroll-engine-quality` job in `.github/workflows/ci.yml`.

## Status

The financial rule registry and the payroll period lifecycle are implemented and tested: the contract schemas for rules and periods, the rule gate, the proposal and approval service, the period transition guard, and the integer money arithmetic. The HTTP layer and the PostgreSQL persistence are not implemented yet; the router lands with the real repository so that no endpoint ships against a fake store. Work proceeds through the phases in `openspec/changes/lukla-payroll-engine/tasks.md`.

