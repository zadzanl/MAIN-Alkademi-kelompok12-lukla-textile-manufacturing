# workspace-ci-governance Specification

## Purpose
TBD - created by archiving change repo-hygiene-ci-governance. Update Purpose after archive.
## Requirements
### Requirement: Workspace Root Isolation Verification
The repository SHALL provide a zero-dependency script `scripts/check_workspace_hygiene.py` that validates repository root structure and sandbox isolation according to `AGENTS.md`. The script MUST exit with code 0 if all root files comply with the allowed whitelist, and exit non-zero with descriptive remediation guidance if unauthorized files exist.

#### Scenario: Allowed Root Files Pass
- **WHEN** the hygiene script is run on a clean repository containing only allowed root files (`README.md`, `AGENTS.md`, `.gitignore`, configuration files)
- **THEN** the script prints a success confirmation and exits with code 0

#### Scenario: Unauthorized Root Markdown or Spike File Fails
- **WHEN** an unauthorized file (e.g. `NOTES.md` or `temp_script.py`) is added directly to the repository root
- **THEN** the script outputs an error naming the violating file, quotes the `AGENTS.md` isolation rule, and exits with code 1

---

### Requirement: Universal Agent Steering Contract
The repository SHALL maintain all agent negative constraints and a standardized Git workflow protocol universally inside `AGENTS.md`.

#### Scenario: AGENTS.md Mandates Git Branching and Self-Review
- **WHEN** an AI coding agent or developer consults `AGENTS.md`
- **THEN** it explicitly forbids direct commits to `main`, specifies the 4-step branch creation workflow, and forbids conversational narrative comments

---

### Requirement: Strict Multi-Ecosystem Linting
The repository SHALL configure strict static analysis for both backend and frontend codebases.

#### Scenario: Backend Strict Linting
- **WHEN** backend static analysis is executed via `ruff` and `mypy`
- **THEN** it enforces strict type definitions, flags dead commented-out code (`ERA001`), and rejects blanket `# type: ignore` directives (`PGH004`)

#### Scenario: Frontend Strict Linting
- **WHEN** frontend linting is executed via `npm run lint`
- **THEN** it enforces TypeScript strict mode, forbids `any` casts, and fails the build if any warnings occur (`--max-warnings=0`)

---

### Requirement: Pull Request Accountability Template
The repository SHALL provide a GitHub Pull Request template at `.github/pull_request_template.md` containing a mandatory diff self-review checklist.

#### Scenario: Opening a Pull Request
- **WHEN** a contributor or AI agent opens a pull request on GitHub
- **THEN** the pull request description is pre-populated with checkboxes verifying that the unified diff was self-reviewed and all conversational AI commentary was stripped

---

### Requirement: GitHub Actions Core CI Pipeline
The repository SHALL define a GitHub Actions workflow `.github/workflows/ci.yml` triggered on pull requests and pushes to `main` that runs core workspace hygiene and OpenSpec contract validation, with prototype quality checks isolated to an advisory workflow.

#### Scenario: Pull Request Triggers Automated Core Quality Gates
- **WHEN** a pull request targeting `main` is created or updated
- **THEN** GitHub Actions runs parallel jobs for workspace hygiene and OpenSpec blueprint contract validation (with dependencies installed), failing the build if any core job exits non-zero

---

### Requirement: Advisory Prototype Quality Pipeline
The repository SHALL define an advisory GitHub Actions workflow `.github/workflows/prototype-sampling.yml` triggered on paths matching `prototypes/sampling-spec-rnd/**` that runs backend and frontend static checks without blocking repository merges.

#### Scenario: Changes to Prototype Code
- **WHEN** a pull request modifies files within `prototypes/sampling-spec-rnd/`
- **THEN** GitHub Actions runs prototype static quality checks as an advisory build (`continue-on-error: true`), providing diagnostic feedback to developers without blocking universal PR workflows

