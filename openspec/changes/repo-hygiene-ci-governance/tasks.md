# Tasks: Repository Hygiene & CI Governance Pipeline

## 1. Workspace Isolation Gate Script

- [x] 1.1 Create `scripts/check_workspace_hygiene.py` with zero dependencies, validating allowed root files and designated directories (`docs/`, `prototypes/`, `openspec/`).
- [x] 1.2 Run and verify `python scripts/check_workspace_hygiene.py` against the clean repository.

## 2. Universal Agent Contract in AGENTS.md

- [x] 2.1 Update `AGENTS.md` with explicit negative constraints (no narrative comments, no conversational Markdown filler, no type evasion) and the mandatory 4-step Git & PR Protocol.
- [x] 2.2 Consolidate all rules exclusively into `AGENTS.md` (remove standalone `.cursorrules` and `.github/copilot-instructions.md`).

## 3. Strict Linting & CI Automation

- [x] 3.1 Create `.github/pull_request_template.md` with unified diff self-review checklist.
- [x] 3.2 Configure backend strict linting via `pyproject.toml` (Ruff and Mypy strict mode) and `requirements-dev.txt`.
- [x] 3.3 Configure frontend strict linting via `.eslintrc.cjs` (`@typescript-eslint/no-explicit-any: error`, `--max-warnings=0`).
- [x] 3.4 Create `.github/workflows/ci.yml` (Core CI for workspace hygiene and blueprint validation with dependencies) and `.github/workflows/prototype-sampling.yml` (advisory prototype static quality checks).

## 4. End-to-End Verification

- [x] 4.1 Execute `python scripts/check_workspace_hygiene.py` and confirm exit code 0.
- [x] 4.2 Validate OpenSpec change integrity with `openspec validate repo-hygiene-ci-governance`.
