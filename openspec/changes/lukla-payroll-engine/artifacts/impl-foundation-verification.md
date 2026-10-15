# Payroll foundation dependency and verification handoff

Scope: bounded setup approved by maintainer; no reviewer/subagent dispatched. No changes to worker-owned repositories, models, migrations, runtime, package tests, specs, or root/prototype files. No stash, reset, commit, or role change.

## Setup delivered

- `backend/payroll-costing/requirements.txt` declares SQLAlchemy 2, Psycopg 3, FastAPI, and PyJWT already required by payroll runtime/shared `backend.app` imports; `requirements-dev.txt` still supplies pytest, ruff, mypy.
- `backend/payroll-costing/pyproject.toml` gives pytest both repository and module import roots via its supported `pythonpath` setting and importlib mode; mypy also resolves the repository root. No test `sys.path` hacks.
- `backend/payroll-costing/README.md` documents Python 3.11 module-local `.venv`, installation, `pip check`, quality commands, and the one-command local disposable PostgreSQL regression.
- `backend/tools/run_payroll_db_tests.py` requires explicit loopback `postgresql+psycopg` admin/app URLs on one instance, verifies that the actual app login is the existing non-privileged `lukla_app` role, applies the exact 001/006/007/008/009/011/012 sequence to a fresh UUID-named database in separate transactions, runs `backend/tests/test_payroll_invariants.py` with generated URLs, and drops only the database it created in `finally`. No ambient database fallback, global role changes, passwords printed by the runner, or trigger disabling. M001 is allowed only with a preexisting restricted role so its `CREATE ROLE IF NOT EXISTS` branch is inert.
- `backend/tests/test_payroll_invariants.py` was aligned to UUID rule versions and the five-argument Owner approval routine; restricted-role missing/cross-tenant read and pending-rule no-monetary-write checks were added.

## Observed results

- Python 3.11 `.venv` install from `requirements-dev.txt`: success; `.venv/Scripts/python -m pip check`: `No broken requirements found.` Fresh-venv import of `src.services.payroll_runtime` and `backend.app.services.idempotency`: `imports OK` after declaring FastAPI/PyJWT.
- Local PG18 at `127.0.0.1:55432`: runner applied all seven migrations, pytest **5 passed in 3.35s**, and printed `Dropped owned disposable payroll test database`; exit 0. Role/remote-host negative controls returned exit 2 before database creation. Four preexisting `payroll_revision_*` databases were observed; none were deleted by this worker.
- Owned runner + invariant tests: `ruff check --config backend/payroll-costing/pyproject.toml` passed; `ruff format --check --config ...` passed; Python compilation passed.
- `python scripts/check_workspace_hygiene.py`: passed.
- Fresh-venv package `pytest -q --tb=line`: **129 passed, 2 failed**. `test_periods_repository::test_create_uses_caller_session_and_reads_its_insert` expects its first mocked reader page to be a rule but supplies a period row (`payroll_read_rows returned invalid rule parameters`). `test_rules_repository::test_approval_checks_context_and_uses_routine_then_reader` expects only two bound parameters, but the current routine receives `approval_reference`, `note`, and `request_id` too. These tests belong to the parallel worker; neither was changed here.
- Package `ruff check .`: exit 1, four worker-owned findings: unused `RuleStatus` in `src/repositories/rules.py`; import order and line length in `src/services/payroll_runtime.py`; line length in `tests/test_rules_repository.py`. `ruff format --check .`: exit 1, worker-owned `src/repositories/rules.py`, `src/services/payroll_runtime.py`, `tests/test_payroll_calculation_models.py`, `tests/test_rules_repository.py` unformatted.
- Package `mypy src/ --strict`: exit 1, three preexisting shared-backend errors now correctly reachable: `backend/app/core/database.py:17` missing function annotation; `backend/app/services/ledger.py:353,515` incompatible `str` vs `Literal['DEBIT','CREDIT']`. No ignore flags/suppressions added. CI payroll quality job remains red until these and the package failures are repaired by their owners.

## Coverage still open

This pass checks restricted-rule approval, period constraints, isolation without context/across tenants, and pending-rule rollback/no wage/run/item/payment rows. It does **not** prove duplicate wage or bonus rejection with valid QC/garment inputs, approved-run immutability, ledger end-to-end behavior, or concurrent idempotency. Those require valid upstream fixtures and the parallel worker's completed runtime. The runner does not execute `backend/tests/test_ledger.py`, which needs its own credentials and existing backend dependencies. No entire phase is marked passed.

Risk: dependency lower bounds are not a lockfile. A clean install is reproducible as a declared isolated setup, but exact upstream versions can change; pin through an approved lock/constraints process if byte-for-byte resolution is required. The current `.venv` resolved SQLAlchemy 2.1.4, Psycopg 3.3.6, FastAPI 0.143.1, PyJWT 2.15.1, pytest 9.1.1, mypy 2.4.0, and ruff 0.17.0. PostgreSQL itself and provisioned restricted role are external prerequisites.

References consulted before implementation: [SQLAlchemy engine URLs](https://docs.sqlalchemy.org/en/20/core/engines.html), [Psycopg 3 connection usage](https://www.psycopg.org/psycopg3/docs/basic/usage.html), [pytest import mode/venv guidance](https://docs.pytest.org/en/stable/explanation/goodpractices.html).
