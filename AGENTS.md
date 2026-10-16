# AGENTS.md — Manufacturing ERP/SAP -like Dashboard Thingy

## Efficient Engineering Mode (Required)

Be an efficient senior engineer, but never careless. After understanding the request and tracing the affected flow, stop at the first option that works:

1. Does this actually need to be built? If no, do not build it (YAGNI: You Ain't Gonna Need It).
2. Is the user solving the right problem, or patching a symptom while the real bug laughs from two files over?
3. Is there already something in this codebase that does this? Because you'd be amazed how often there is. Check whether an existing repository pattern or helper exists. Use the standard library, platform, or an installed dependency. Do not install new dependencies without asking.
4. Do the user's ideas, strategies, or code account for blind spots, weak assumptions, and structural flaws?
5. Is this overengineered for what's actually needed? Write the smallest correct, readable change.
6. Is this request safe, boring, and exactly what a committee of middle managers would approve and if so, is there a sharper version hiding underneath?

Prefer deletion, boring solutions, no new dependencies, no unrequested abstractions, and the fewest line changes possible. Fix bugs at their shared root cause after checking all callers.

This never permits skipping retrieval, trust-boundary validation, data-loss prevention, security, accessibility, requested work, or the orchestration and verification workflow below.

Leave one smallest runnable regression check for non-trivial logic; document a deliberate known ceiling with a file header comment and its upgrade path.

### Browser Verification Default

Playwright GitHub Actions is intentionally disabled to control CI costs. Keep `.github/workflows/prototype-e2e.yml` for future use, but do not re-enable or dispatch it without explicit maintainer approval. Use local browser tools or the local Playwright harness for verification instead.

For pre-commit checks involving user-visible web behavior, prefer an available **interactive browser tool**: a tool that can open a page, interact with rendered controls, and inspect the result. Tool names are environment-specific; in GitHub Copilot for VS Code, `open_browser_page` is one example.

If no interactive browser tool is available, run the repository's automated Playwright smoke command when the harness exists. Report whether evidence came from an interactive tool, automated Playwright, both, or neither. If neither is available, mark browser verification **unverified**; an API request or static inspection is not equivalent browser evidence.

#### Non-Root Playwright Harness Locations

Due to root isolation rules (`scripts/check_workspace_hygiene.py`), Playwright is **never** installed or configured at the repository root (`/tests/` or root `playwright.config.ts`). Automated E2E harnesses exist in two dedicated locations:

1. **Operations Engine Frontend Harness (`frontend/`):**
   - **Configuration:** [`frontend/playwright.config.ts`](frontend/playwright.config.ts)
   - **Tests:** [`frontend/tests/`](frontend/tests/) (e.g., `closing-01-mismatch.spec.ts`, `view-04-stepper.spec.ts`)
   - **Run Command:**
     ```bash
     cd frontend
     node ../node_modules/@playwright/test/cli.js test
     ```
   - **Evidence Normalization:**
     ```bash
     python tools/collect_evidence.py
     ```
     Generates deterministic `frontend/artifacts/evidence/results.json` and JUnit `results.xml` conforming to `16-test-harness-and-agent-verification.md` §4.

2. **Prototype Sampling & Spec R&D Smoke Harness (`prototypes/sampling-spec-rnd/frontend/`):**
   - **Configuration:** [`prototypes/sampling-spec-rnd/frontend/playwright.config.ts`](prototypes/sampling-spec-rnd/frontend/playwright.config.ts)
   - **Tests:** [`prototypes/sampling-spec-rnd/frontend/tests/smoke.spec.ts`](prototypes/sampling-spec-rnd/frontend/tests/smoke.spec.ts)
   - **Run Command:**
     ```bash
     cd prototypes/sampling-spec-rnd/frontend
     npm run test:e2e
     ```

### Working With a Multiple Developer Seniority and Discipline

This repository are maintained by multiple maintainers. Some of them are senior, but most of them are junior. Some of them comes from system , embedded, or data engineering. Always adjust the communication, planning, and report to be understandable by any developer, regardless of seniority or backgrounds. 

The engineering bar is unchanged: correct, tested, no new dependencies without asking — but *how* work is planned and handed over changes. **Prefer the option a thorough junior developer can run, debug, and explain, over the option a senior would find elegant**. Generalizable rules are valid beyond the persistence change:

- **Delete machinery instead of engineering around it.** Fewer moving parts beats clever parts; the simplest correct, readable change is the target. Before building an abstraction, ask whether a step can simply be removed.
- **Reach for the framework's documented pattern before inventing one.** Copy the official tutorial shape (e.g., FastAPI's SQL-databases pattern) so a stuck developer can google an answer that maps 1:1 onto this repo.
- **One prerequisite, not two.** Don't make a developer install and learn two tools when one already-installed tool does the job.
- **Every setup step needs one visible "did it work?" check.** A README must be runnable top-to-bottom on a fresh machine; each step should end in an obvious verification (`pip check` prints `No broken requirements found.`, `/health` returns `{"status":"OK"}`).
- **Fail with an actionable message, not an opaque stack trace.** A two-line guard (`if not DATABASE_URL: raise RuntimeError("create a .env with ...")`) beats a config framework and beats a raw `ArgumentError`.
- **Record the reasoning and who agreed.** For all non-trivial decisions, keep the tradeoff and the perspectives considered in the change artifacts so the next person doesn't redo the analysis.

## Standard Working Method

1. Clarify the requested outcome and inspect the affected files before editing.
2. **For any work, you must ALWAYS retrieve context first: use web search (web) for external references, semantic search (local) for fuzzy local search and grep/rip-grep/select-string to search through this giant repo.** Select-string or grep or rip-grep are not as effective in this repo due to the sheer amount of files, use `#tool:semantic-search/search`. If necessary follow-up with `#tool:semantic-search/find-related` tools.   
3. Keep exploration, planning, implementation, and review as specified, limited, constrained(bounded), non-overlapping steps. Confirm material changes to behaviour, scope, architecture, data, cost, or risk before implementing.
4. Use OpenSpec to propose, implement, and archive material changes. Keep implementation small, reversible, and directly traceable to approved requirements.
5. Verify each change with focused checks, then broader relevant checks when practical. Report exactly what was and was not verified. Never use unverified positive claims.

### Workspace Hygiene & Pre-Archive Gate

**CRITICAL: You MUST maintain workspace clarity across sprints and avoid adding cognitive clutter for both developers and collaborating agents**

- **Root & Sandbox Isolation:** Keep the repository root clean (only root configuration files, `README.md`, and `AGENTS.md`). Place all experimental spikes in `prototypes/<name>/` and documentation in `docs/`. OpenSpec change folders must contain only specification diffs, designs, tasks, and review records—never runnable application source trees or duplicate backups.
- **Anchored Git Rules:** Always anchor folder ignore patterns in `.gitignore` with a leading slash (e.g., `/artifacts/`, `/build/`) so nested application folders in subdirectories are not silently untracked.
- **Pre-Archive Gate (Adversarial Check):** Before archiving an OpenSpec change or promoting a prototype:
    1. **Asset Reconciliation:** Audit uncommitted and unported files to ensure working algorithms, UI components, active PRDs, and test scripts are not abandoned or accidentally deleted.
    2. **Configuration Drift:** Confirm target ports, environment variables, and proxy URLs match the single source of truth across backend, frontend, scripts, and documentation without drift.

## Upstream Agent Steering & Negative Constraints

AI coding agents (and developers prompting them) must strictly observe the following output boundaries:
- **No Conversational Filler:** Never generate narrative filler, chatty transitional phrases ("Let's dive in", "In summary", "It is important to note"), or bloated prose in Markdown docs or code comments.
- **No Code-Restating Comments:** Never write comments that merely repeat the next line of code (e.g. `// increment count: count++`). Only document non-obvious business logic, domain invariants, or hardware tolerances.
- **No Unrequested Markdown Sprawl:** Do NOT create new markdown files, summaries, or scratch notes in the repository root. All design specs belong in `openspec/` and permanent documentation belongs in `docs/`.
- **Zero Type Evasion:** Never bypass type safety using `as any`, loose `Any` casts, or blanket `# type: ignore` without explicit architectural justification approved by a maintainer.

## Mandatory Git & PR Protocol for Agents & Developers

1. **Check Your Branch First:**
   NEVER write code directly on `main` or `master`. Always branch off from an up-to-date base branch (`main` or `master`) before modifying files:
   ```bash
   git checkout main || git checkout master
   git pull origin HEAD
   git checkout -b <type>/<short-description>
   # Examples: feat/sampling-tolerance, fix/cors-port, chore/ci-hygiene
   ```

2. **Verify Workspace Hygiene Before Committing:**
   ```bash
   python scripts/check_workspace_hygiene.py
   ```

3. **Self-Review Unified Diff:**
   Inspect `git diff` top-to-bottom. Strip all leftover debug statements (`console.log`, `print()`, `debugger`) and conversational AI commentary before staging files.

4. **Push and Create Pull Request:**
   ```bash
   git push -u origin HEAD
   gh pr create --fill
   ```
   *(If GitHub CLI `gh` is not installed, open the PR using the link generated by git).*

## EC2 Deployment and Recovery Guardrails

### Deployment Context and Known Limits

- Deployment target: Amazon Linux 2023, as specified by `scripts/deploy_ec2.sh`.
- Application runtime: Python 3.11. The EC2 session reported Python **3.11.16** after installation. The original virtual environment used Python **3.9**, which failed to import the application.
- Database: the deployment script targets PostgreSQL **15**. Verify the running server version separately; an installed client version is not server-version evidence.
- Shell: the SSM session displayed `sh-5.2`. The deployment script uses Bash; execute it with its shebang or `bash`, not `sh scripts/deploy_ec2.sh`.
- Application owner: `ec2-user`. The observed SSM session used `ssm-user`; these users have different home directories.
- Observed repository path:
  `/home/ec2-user/MAIN-Alkademi-kelompok12-lukla-textile-manufacturing`
- Mainline branch: `master`, not `main`.
- Intended application port: **80** in the updated deployment script. The older script launched on **3000**. Verify the checked-out script, listening port, and security-group rules rather than assuming they agree.
- Instance type, EBS volume size, available disk space, AMI ID, and CI runner version were not established during this incident. Retrieve them when relevant; never substitute typical values. These commands ran interactively on EC2, not on a demonstrated CI runner.

### 1. Match the Existing Virtual Environment to Python 3.11

Check `.venv/bin/python --version`, not merely `python3 --version` or whether `.venv` exists.

**Incident:** Python 3.9 failed first on `enum.StrEnum`, introduced in Python 3.11, and then on evaluation of `str | None`, supported from Python 3.10.

- Create this application's environment explicitly with `python3.11 -m venv .venv`.
- Installing Python 3.11 does not upgrade an existing Python 3.9 virtual environment.
- Validate the replacement interpreter before rebuilding; preserve recovery options.
- Use the environment's interpreter explicitly for installation and verification:
  `.venv/bin/python -m pip ...`.
- Do not replace Amazon Linux's system Python to change the application runtime.
- Do not patch newer Python features individually to support Python 3.9 unless backward compatibility is an explicitly approved requirement.

### 3. Preserve Configuration and Verify Database Changes

**Incident:** PostgreSQL authentication initially used `ident` for loopback connections. Deployment instructions changed those entries to `scram-sha-256`. Later, seeding failed on row-level security for `ledger_accounts`, but the migration runner still reported successful completion.

- Confirm the active PostgreSQL configuration before editing an assumed path.
- Back up authentication configuration before changing it; keep changes narrowly scoped.
- Do not overwrite an existing `.env` without inspecting and preserving its intended settings.
- Track applied migrations. “Relation already exists” does not prove an entire migration completed.
- Required migration and seed failures must return a nonzero exit status.
- Resolve seed failures using the intended tenant and role context; do not disable row-level security to force success.
- Distinguish warnings from fatal errors using command results. The `postgres` user's inability to enter `/home/ec2-user/...` did not prevent the SQL commands shown in this incident from executing.

Obtain AWS resource details from the EC2 console or authorized AWS tooling. Use local checks such as `uname -m`, `lsblk`, and `df -h` for architecture and storage evidence. Do not guess instance specifications from an IP address, shell prompt, or deployment template.
