# Warehouse authorization implementation report

## Task record

- Task record: `openspec/changes/lukla-payroll-engine/artifacts/orchestration-task-record.md`
- Revision: 2
- Scope: close `review-wave1-S-001` without changing payroll authorization behavior

## Actual edits

- `backend/app/core/auth.py`
  - Extracted the shared JWT, active-tenant, active-actor, and database-context validation into a private helper.
  - Kept `get_current_auth_context` restricted to exactly `Owner` and `FinancePayroll`.
  - Added `get_current_stock_auth_context`, restricted to `Owner` and `Warehouse`.
- `backend/app/api/v1/stock.py`
  - Added the stock dependency to GET `/api/v1/stock` and POST `/api/v1/material-issuances`.
  - Derived stock visibility from `auth.tenant_id` before applying filters.
  - A caller-supplied `tenantId` for another tenant returns no rows; it cannot expand scope.
  - Preserved beneficiary mismatch rejection and matched-issuance `INVALID_STATE` non-persistent behavior.
- `backend/tests/test_stock.py`
  - Added unauthenticated GET/POST checks.
  - Added tenant-scope and caller-tenant-expansion checks.
  - Added negative role checks for `MaklonClient`, `FinancePayroll`, and `Tailor`.
  - Added authorized mismatch-order rejection coverage.

## Role boundary decision

The RBAC matrix explicitly grants Warehouse stock views and material issuing, and grants MaklonClient only its own client-scoped stock. The current `AuthContext` has no server-derived client/beneficiary grant, so MaklonClient was not authorized for this route; granting it would expose tenant stock beyond the available scope proof. Owner remains allowed for the route-specific warehouse/owner boundary required by the acceptance criteria. This is a conservative route decision, not a resolution of the broader portal policy gap.

## Verification evidence

| Check | Result |
|---|---|
| Pre-change `PYTHONPATH=backend python -m pytest -q backend/tests/test_stock.py` | PASS — 4 passed |
| Focused post-change stock/auth tests | PASS — 10 passed; one existing Starlette/httpx deprecation warning |
| Existing payroll API tests | PASS — 2 passed |
| Existing ledger/payroll auth suite | NOT RUN to completion / BLOCKED — PostgreSQL connection to `127.0.0.1:5433` timed out; 2 passed and 47 errored in the combined invocation |
| Python compile/import | PASS — `py_compile` for edited Python modules; generated app import succeeded |
| Generated OpenAPI inspection | PASS — 20 paths; both stock routes present with 401 responses |
| Owned-file whitespace check | PASS — no trailing whitespace in the three owned files |
| `git diff --check` | PASS for the tracked auth diff; equivalent owned-file whitespace scan passed for untracked stock/test files |
| `python scripts/check_workspace_hygiene.py` | BLOCKED — pre-existing untracked root `package-lock.json` violates the repository root hygiene rule |
| Database-dependent checks | NOT RUN / BLOCKED — PostgreSQL unavailable |
| Production persistence/security claim | Not made; stock remains demo/non-persistent |

No subagents were dispatched, per the explicit user instruction. No payroll-costing files, migrations, frozen OpenAPI source, frontend, BRD/PRD, or unrelated dirty files were changed.
