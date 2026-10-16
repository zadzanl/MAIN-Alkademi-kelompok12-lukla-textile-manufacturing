# Implementation Report: Payroll API 001

Date: 2026-10-16
Change: `lukla-payroll-engine`
Task record: `orchestration-task-record.md` Revision 1 was loaded before work.

## Implemented

- Replaced the weekly calculation `_unsupported` route with the existing SQL-backed aggregate path.
- Reused the checked tenant period/rule readers and `calculate_weekly_payroll` database routine.
- Enforced the rule gate before calculation; `FinancialRulePending` maps to `409 FINANCIAL_RULE_PENDING` and rolls back the session.
- Serialized `CALCULATED` and valid zero-output `NO_OUTPUT` results using the existing `PayrollResult` and `Money` models.
- Reused the existing idempotency reservation/completion helper for `calculateWeeklyPayroll`, including replay/conflict behavior and the frozen 200 response status.
- Added contract models for payroll item/statement shapes for subsequent persistence work.
- Corrected payroll path parameter spelling to frozen OpenAPI `periodId` while retaining Python snake_case locals.
- Added focused route tests for approved aggregate serialization/commit and pending-rule rollback/problem mapping.

## Deliberately not implemented

- `getPayrollStatement` remains a 501 boundary. Existing persistence does not provide statement item allocation, meal policy, bonus allocation, or remainder policy needed to produce the frozen per-recipient contract honestly.
- Bonus pool, approval, payment, overhead, and financial-rule HTTP operations remain unchanged where their required repositories/services or unresolved policy inputs are absent.
- No mock success, zero-value fallback, meal allocation, reserve allocation, payment initiation, or approval-authority inference was added.

## Verification

- `backend/payroll-costing`: `python -m pytest -q` — **134 passed**.
- Focused API test: `python -m pytest -q tests/test_payroll_api.py` from `backend` with `PYTHONPATH=.` — **2 passed**.
- Payroll module Ruff checks on touched files — **passed**.
- FastAPI import and concrete route inspection — **passed**; routes include:
  - `/payroll/weekly/{periodId}` / `calculateWeeklyPayroll` / `PayrollResult`
  - `/payroll/weekly/{periodId}/statement` / `getPayrollStatement`
- `python scripts/check_workspace_hygiene.py` — **passed**.
- `python openspec/changes/lukla-ops-engine-planning/validate-blueprint.py` — contract checks passed; semantic approval remains `NOT_GRANTED`.
- Exact required command `python -m pytest -q backend/tests` — **blocked at collection** because root execution does not put `backend` on `PYTHONPATH` (`ModuleNotFoundError: app`).
- Corrected backend run with `PYTHONPATH=backend` — **21 passed, 8 skipped, 47 errors**; errors are PostgreSQL connection timeouts to `127.0.0.1:5433` (`lukla_test`). No database-backed runtime success was claimed.

## Scope safety

Only payroll-owned implementation/tests and the required implementation artifact were added or changed by this work. Existing unrelated dirty files were preserved; pre-existing modifications under `backend/payroll-costing/src/repositories/rules.py`, `tests/test_periods_repository.py`, and other areas were not overwritten.
