# Phase 1–2 implementation evidence

## Scope and revision

- Branch: `feat/payroll-engine-implementation`; starting HEAD: `7afa880` (`docs(openspec): archive playwright spec`). Read `tasks.md` from this branch before editing: 40 unchecked tasks, OpenSpec `spec-driven`, ready.
- Existing tracked files already supplied `backend/payroll-costing/` with README, API_CONTRACTS, `src/{models,services,utils,api}`, tests, an explicit `backend` root allow-list entry, and the `payroll-engine-quality` job in `.github/workflows/ci.yml`. No scaffold, application behavior, or CI job was duplicated.
- The implementation request confirms the approved design and shared gate amendment; the earlier task-record branch chain and post-merge checkboxes predate this branch. Per the current request, tasks 1.1–1.4 and 2.1–2.4 were checked after local verification on this branch, before merge. No phase review was performed; review is deferred until phase 3 by request.

## Changes

- `scripts/check_workspace_hygiene.py`: explained the existing narrow `backend` root-directory allow-list entry inline; did not broaden the allow-list.
- `backend/payroll-costing/README.md`: recorded Decision 2 (period container and versioned run), Decision 3 (append-only overhead events and monthly allocation snapshot), Decision 4 (production location and shared gate), rejected alternatives, and unresolved business-rule gate. Checked the table definitions against `openspec/changes/lukla-ops-engine-planning/11-database-schema-spec.md` §§4, 8 before authoring. No migration was authored.
- `openspec/changes/lukla-payroll-engine/tasks.md`: checked only 1.1–1.4 and 2.1–2.4.
- This report: `openspec/changes/lukla-payroll-engine/artifacts/impl-phase12-001.md`. Pre-existing untracked `artifacts/technical-plan-001.md` was left untouched.

## Verification (Windows, Python 3.11.4)

- Existing active Python: `python -m pytest --version` -> 8.3.5; global `ruff` and `mypy` unavailable, global `pytest.exe` launcher pointed to a missing Python 3.14 executable. Installed the module's *existing declared* `requirements-dev.txt` into `%TEMP%/lukla-payroll-phase12-check` only; no project dependency files changed. Isolated tool versions: Ruff 0.17.0, mypy 2.4.0, pytest 9.1.1, Python 3.11.4.
- `python scripts/check_workspace_hygiene.py` -> exit 0, `[OK] Workspace hygiene check passed`. Temporary directory control using `check_workspace_hygiene`: directory with `backend/` -> 0; after adding `unapproved-root/` -> 1, `Unauthorized root directory`. No test directory created in the repository.
- CI job: inspected `.github/workflows/ci.yml`: job `payroll-engine-quality`, `working-directory: backend/payroll-costing`, `ruff check .`, `ruff format --check .`, `mypy src/ --strict`, `pytest -q`. No `continue-on-error` or job skip condition; existing hygiene and contract jobs preserved. Local in-memory lint tripwire from module root: `import os` piped to `ruff check --stdin-filename src/api/ci_tripwire.py -` -> exit 1 (`F401`); corrected input `value = 1` -> exit 0 (`All checks passed!`). No test file persisted.
- From `backend/payroll-costing` with isolated tools on PATH: `ruff check .` -> exit 0 (`All checks passed!`); `ruff format --check .` -> exit 0 (`34 files already formatted`); `mypy src/ --strict` -> exit 0 (`Success: no issues found in 20 source files`); `pytest -q` -> exit 0 (`120 passed in 0.73s`). Also `python -m pytest -q` using the existing Python -> exit 0 (`120 passed in 0.41s`).
- `rg --files backend/payroll-costing` filtered for migration directories and `.sql` files -> no matches, exit 1 (expected). Phase 3 migrations were not edited. `git diff --check` -> exit 0. `git status --short` inspected; only the scoped edits and pre-existing untracked artifacts directory appeared before report creation.

## Unverified

- GitHub-hosted CI execution, branch-protection configuration, and merge status were not verified; local command results and workflow inspection are not a hosted CI run. No runtime/API or database migration checks were performed in this phase.
