# Implementation report — persistent payroll-period repository, revision 2

## Context

- Confirmed `revision-task-record.md` **Revision 1 — baseline restored**.
- Package A SQL was narrowly approved in `revision-review-sql-002.md`.
- No reviewer was dispatched for this implementation slice, per the user instruction.
- Branch/history/worktree preservation rules were followed: no stash, reset, clean, commit, branch switch, or dependency installation.
- Scope was limited to the persistent payroll-period repository and its required SQL seam. Rule repository, HTTP, payroll runtime, payment, jobs, and phase 4/5 were not implemented.

## Changed paths

- `backend/migrations/012_payroll_routines_rls.sql`
  - Tightened `payroll_period_transition()` to permit only the pure service transition table and to reject all period fields except `status` and `updated_at` from changing through the trigger.
  - Added `payroll_transition_period(uuid,text,text)` as a tenant-context-checked, row-locking, expected-status compare-and-set `SECURITY DEFINER` routine.
  - Revoked PUBLIC execute and granted execute only to `lukla_app`.
  - Revoked direct `UPDATE` on `payroll_periods` from `lukla_app`; did not broaden grants.
- `backend/payroll-costing/src/repositories/__init__.py`
- `backend/payroll-costing/src/repositories/periods.py`
  - Uses the caller-supplied SQLAlchemy `Session` only.
  - Does not open a session, commit, rollback, or create a second connection.
  - Uses the allowlisted `payroll_read_rows` checked reader with bound parameters and page size 1000.
  - Generates a UUID before insert, validates through `create_period`, inserts, then checked-reads.
  - Lists all pages and validates JSON rows into the existing `Period` contract model.
  - Validates pure transition rules, calls the narrow SQL routine, then checked-reads.
- `backend/payroll-costing/tests/test_periods_repository.py`
  - URL-free unit tests for checked-row mapping, invalid model data, insert/read call order, no transaction ownership, 1001-row pagination, and transition validation/call order.
- `openspec/changes/lukla-payroll-engine/artifacts/impl-periods-revision2.md`

Existing restored and user-modified files were not rewritten. `prototypes/s001-probe/probe_fixture.sql` was preserved byte-for-byte.

## Exact verification commands and observed output

All commands ran from `C:\Projects\hackathon-MAIN-alkademi` unless stated otherwise.

1. Focused repository and lifecycle tests:

```powershell
$py='C:/Users/lenovo/AppData/Local/Programs/Python/Python311/python.exe'
Push-Location backend/payroll-costing
try { & $py -m pytest -q tests/test_periods_repository.py tests/test_payroll_periods_service.py }
finally { Pop-Location }
```

Observed: `34 passed in 2.92s`, exit 0.

2. Full payroll-costing suite after formatting:

```powershell
Push-Location backend/payroll-costing
try { & $py -m pytest -q }
finally { Pop-Location }
```

Observed: `125 passed in 3.42s`, exit 0.

3. Cached Ruff on changed Python files:

```powershell
$ruff='C:/Users/lenovo/AppData/Local/uv/cache/archive-v0/UkdC2l72lX-BSz4-b3WBA/Scripts/ruff.exe'
Push-Location backend/payroll-costing
try {
  & $ruff check src/repositories tests/test_periods_repository.py
  & $ruff format --check src/repositories tests/test_periods_repository.py
}
finally { Pop-Location }
```

Observed: `All checks passed!`; `3 files already formatted`; exit 0 for both checks.

4. Python311 compilation and diagnostics:

```powershell
$env:PYTHONPATH='backend;backend/payroll-costing'
& $py -m compileall -q backend/payroll-costing/src/repositories backend/payroll-costing/tests/test_periods_repository.py
```

Observed: `compile_exit=0`. Editor diagnostics reported `No errors found` for all three changed Python paths.

5. Fresh disposable PostgreSQL migration check:

```powershell
$files=@('001_identities.sql','006_payroll_rate_cards.sql','007_payroll_qc_inputs.sql',
  '008_double_entry_ledger.sql','009_payroll_core.sql','011_job_idempotency.sql',
  '012_payroll_routines_rls.sql')
# Each file was applied with psql -X -w -q -v ON_ERROR_STOP=1 -1
# to a newly generated payroll_revision_<guid> database.
```

Observed: all seven migrations applied; PostgreSQL `18.6`. Catalog query output:

```text
payroll_revision_0db7f403955f473f90eb023de0d6f790|18.6

t|f|f
migration_exit=0
 drop_exit=0
```

The booleans mean: `lukla_app` execute on the new routine = true; `lukla_app` direct UPDATE on `payroll_periods` = false; PUBLIC execute on the new routine = false. The generated database was dropped successfully. The first attempt used an invalid `createdb -X` option and created no database; it was corrected and rerun.

6. Workspace and diff checks:

```powershell
& $py scripts/check_workspace_hygiene.py
git diff --check
```

Observed: `Workspace hygiene check passed`; `hygiene_exit=0 diff_check_exit=0`.

7. Probe fixture preservation:

```powershell
Get-FileHash prototypes/s001-probe/probe_fixture.sql -Algorithm SHA256
```

Observed before and after: `1B108B45868AA1A5F6B31F2518A91A876D80B5664D099059CDFCCC3577902B8D`.

## Acceptance assessment

- **Repository transaction neutrality:** unit-tested by asserting no `commit()` or `rollback()` call and by using one supplied Session mock. No second Session is constructed.
- **Checked reads:** implemented through the existing allowlisted reader with bound ID/cursor/limit values; rows are Pydantic-validated as `Period`.
- **Pagination:** unit-tested with 1001 rows and a 1000-row first page.
- **Create:** UUID generation, pure range validation, insert, and checked read are implemented.
- **Transition:** pure `ALLOWED_TRANSITIONS` is checked before the routine; SQL locks the tenant-scoped row, compares expected state, updates status only, and the repository checked-reads afterward.
- **SQL safety:** migration applies cleanly in a fresh database; routine privileges are narrow; direct period UPDATE remains unavailable to `lukla_app`.
- **Not claimed:** live restricted-role repository CRUD, concurrent transition proof, broader RLS/auth mapping, strict mypy, pgTAP, HTTP/runtime/payment/jobs, phase 4/5, or whole phase 3 completion.

## Risks and remaining evidence

- The repository unit tests do not prove the full restricted PostgreSQL read-after-write path. A disposable DB integration test remains appropriate before unattended CI use.
- The migration catalog check does not prove concurrent stale-state outcomes; that needs two restricted sessions with lock/timeout assertions.
- `app.*` context remains trusted-server context, not end-user authentication. Caller-to-context mapping and pooled reset remain outside this slice.
- Existing trigger-function PUBLIC execute hardening outside the new routine was not broadened or changed here.
- No package, task checkbox, frozen contract, or phase-level status was changed.
