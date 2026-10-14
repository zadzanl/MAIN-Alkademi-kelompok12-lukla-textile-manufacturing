# Proposal: Repository Hygiene & CI Governance Pipeline

## Why
Junior developers and non-web contributors driving AI coding agents risk polluting the repository with conversational prose, unorganized root files, dead commented code, and unverified type evasions. This change establishes an automated, deterministic quality gate in CI and codifies an upstream agent steering contract to safeguard repository health without introducing brittle, third-party AI-detection tools.

## What Changes
- **Workspace Hygiene Gate**: Add `scripts/check_workspace_hygiene.py` to deterministically enforce `AGENTS.md` Root & Sandbox Isolation, preventing accidental file pollution in the root.
- **Universal Agent Contract**: Consolidate all agent negative constraints and Git workflow rules exclusively in `AGENTS.md` (no redundant IDE-specific rule files).
- **Strict Linting Configuration**: Configure strict linting across backend (`ruff` with `ERA001`/`PGH004` and `mypy --strict` via `pyproject.toml`) and frontend (`eslint` with `--max-warnings=0` and TypeScript strict mode).
- **Pull Request Accountability Gate**: Add `.github/pull_request_template.md` with a mandatory diff self-review checklist.
- **Deterministic Core CI Pipeline**: Add `.github/workflows/ci.yml` running workspace root hygiene and OpenAPI contract validation with explicit dependencies on pull requests, while decoupling prototype checks into `.github/workflows/prototype-sampling.yml`.

## Capabilities

### New Capabilities
- `workspace-ci-governance`: Automated root hygiene verification, standardized agent git workflow, PR review checklist, and deterministic GitHub Actions quality gates.

### Modified Capabilities
*(None)*

## Impact
- **Root Directory**: Adds `scripts/check_workspace_hygiene.py`. Updates `AGENTS.md`. Removes separate IDE config stubs.
- **GitHub Configuration**: Adds `.github/workflows/ci.yml`, `.github/workflows/prototype-sampling.yml`, and `.github/pull_request_template.md`.
- **Backend**: Adds `pyproject.toml` (strict Ruff and Mypy) and `requirements-dev.txt`.
- **Frontend**: Adds `.eslintrc.cjs` (strict TypeScript rules) and updates `package.json` lint script.
