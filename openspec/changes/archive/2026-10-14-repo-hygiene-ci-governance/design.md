# Technical Design: Repository Hygiene & CI Governance Pipeline

## Context
The repository houses the Lukla Operations Engine (Garment Manufacturing ERP platform) with multiple developers ranging from senior to junior, and backgrounds spanning web, systems, embedded, and data engineering. As codified in `AGENTS.md`, maintainers require simple, explainable tooling over clever abstractions. When junior developers prompt coding agents (such as Cursor, Copilot, or Claude Code) without negative constraints, agents generate narrative comment slop, type evasions (`as any`), and untracked root files. This design introduces deterministic, zero-dependency validation gates, strict linter configurations, and a universal agent instruction contract in `AGENTS.md`.

## Goals / Non-Goals

**Goals:**
- Enforce `AGENTS.md` Root & Sandbox Isolation via a deterministic, zero-dependency Python script runnable locally and in CI.
- Codify upstream negative prompt constraints and a mandatory 4-step Git & PR Protocol universally into `AGENTS.md` (no redundant IDE-specific config files).
- Configure strict linting across backend (`ruff` with `ERA001`/`PGH004` and `mypy --strict`) and frontend (`eslint` with `--max-warnings=0` and TypeScript strict mode).
- Establish a fast (< 15s) Core GitHub Actions CI workflow on `pull_request` executing workspace hygiene and OpenAPI blueprint contract validation.
- Decouple prototype-specific static analysis into an advisory workflow (`.github/workflows/prototype-sampling.yml`) scoped to prototype paths.
- Provide a standardized pull request template (`.github/pull_request_template.md`) with a mandatory unified diff self-review checklist.

**Non-Goals:**
- Integrating brittle third-party regex "slop-detector" CLIs (`aislop`, `unslop`, `avoid-ai-writing`).
- Managing multiple redundant IDE-specific instruction files (`.cursorrules`, `.github/copilot-instructions.md`).
- Running slow or blocking git pre-commit hooks that impede local developer velocity on Windows.
- Calling external LLM APIs inside CI.

## Decisions

### 1. Zero-Dependency Python Script for Workspace Isolation
- **Choice:** Implement `scripts/check_workspace_hygiene.py` using Python's standard library (`pathlib`, `sys`).
- **Rationale:** Python 3 is already a prerequisite for the backend. A zero-dependency script executes in under 50ms across Windows and Linux, ignores legitimate local dev artifacts (`.env*`, `.idea/`, caches), handles symlinks safely, and produces plain-English error messages referencing `AGENTS.md`.
- **Alternatives Considered:** Bash script (fails on Windows without git bash); custom npm package (adds Node dependency to backend-only contributors).

### 2. Universal Rulebook in `AGENTS.md`
- **Choice:** Maintain all agent behavioral directives, coding rules, and git protocols exclusively in root `AGENTS.md`. Remove separate `.cursorrules` and `.github/copilot-instructions.md`.
- **Rationale:** Aligns with project principle of "One prerequisite, not two" and avoids configuration drift across multiple vendor files.
- **Alternatives Considered:** Maintaining vendor-specific rule copies (rejected due to maintenance overhead).

### 3. Server-Side Enforcement: Core CI vs Advisory Prototype Gates (Option B)
- **Choice:** Run blocking universal repository gates (workspace hygiene, OpenAPI blueprint validation with explicit dependency installation) in `.github/workflows/ci.yml` triggered on `main`. Isolate prototype-specific checks into `.github/workflows/prototype-sampling.yml` with path filtering and advisory status (`continue-on-error: true`).
- **Rationale:** Prevents experimental prototype development from breaking repository-wide CI while ensuring core architecture and root hygiene remain strictly enforced.
- **Alternatives Considered:** Monolithic blocking CI for all prototypes (rejected due to blocking unrelated PRs and high false-alarm friction).

### 4. Strict Linting Configuration
- **Choice:** Configure strict rules:
  - Python: `pyproject.toml` targeting Python 3.11 with `ruff` (selecting `E`, `W`, `F`, `I`, `B`, `C4`, `UP`, `ERA001`, `PGH004`) and `mypy` running with `strict = true`.
  - TypeScript: `.eslintrc.cjs` with `@typescript-eslint/no-explicit-any: error`, `@typescript-eslint/ban-ts-comment: error`, and `npm run lint` running with `--max-warnings=0`.
- **Rationale:** Eliminates type evasion and commented-out dead code mechanically without relying on AI detectors.
- **Alternatives Considered:** Permissive linting with warnings (juniors ignore warnings).

## Risks / Trade-offs

- **[Risk] Junior developer accidentally pushes to `main`.**  
  *Mitigation:* Enable GitHub Branch Protection on `main` to reject direct pushes, forcing the agent to create a feature branch.
- **[Risk] Strict linting causes false-alarm build failures.**  
  *Mitigation:* Rules target unambiguous defects (dead code, loose `any` casts, missing types) with zero heuristic word-banning.
- **[Risk] False positives on intentional root files.**  
  *Mitigation:* The hygiene script maintains an explicit whitelist of allowed root files (`README.md`, `AGENTS.md`, `.gitignore`, configuration files).
