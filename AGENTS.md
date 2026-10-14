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
