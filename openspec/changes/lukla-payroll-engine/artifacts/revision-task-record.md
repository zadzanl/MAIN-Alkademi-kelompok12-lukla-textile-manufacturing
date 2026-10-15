# Phases 1–3 review and revision

## Revision 1 — baseline restored

- User: "Alright, please go ahead and perform a 3-max-loop review-revision workflow. Please inform me when phase 1, 2, and 3 passes."
- Scope: technical-plan-001 phases 1 (gates/adapters), 2 (database invariants), 3 (persistent rules/periods). No phase 4/5 implementation.
- Branch: feat/payroll-engine-implementation, starting HEAD 7afa880.
- Original stash a2a991d996de08a684a936de986aa3320f0c7000 was applied, not popped; preserve it throughout.
- Original budget: maximum three revision/review cycles; superseded for future work by the instruction below. No pass without usable independent security review and focused executable verification.
- Prior findings: missing repositories; SQL proposal guard excludes FinancePayroll; period database validation differs from contract; SQL concurrency/RLS evidence missing. Payment/accounting integration belongs to later scope, not a completed-feature claim.
- Evidence: clean worktree before apply; apply succeeded; OpenSpec ready, 14/40 tasks marked complete. Task sections are not technical-plan phase numbers.
- Required retrieval: read proposal, design, specs/payroll-engine-runtime/spec.md, tasks.md and technical-plan-001.md before implementation.
- Verification: local Ruff, format, strict mypy, payroll tests, hygiene, isolated PostgreSQL restricted-role and concurrent regression tests. Do not install dependencies without approval or change existing databases destructively.
- Baseline status at record creation: investigation; no revision code written, no cycle approved.

## Updated review budget — 2026-10-15

- User: "For further iteration, please restrict the amount of review-revisions to only be one review-revise loop iteration. it is likely that we wont meet deadline if its 3 review-revision"
- Effective for subsequent implementation phases: one review followed by at most one targeted revision and verification. Do not automatically start another review/revision loop.
- Unresolved blockers or unavailable mandatory review coverage must be reported, not converted into a pass. Preserve required security coverage and focused regression tests.
- Current evidence: package A alone was approved in revision-review-sql-002.md. Later period and rule repository slices have implementation reports (impl-periods-revision2.md and impl-rules-revision2.md); these do not establish whole-phase approval.
- Phases 1–3 remain incomplete; the reduced iteration budget does not change their acceptance criteria or authorize unresolved financial-policy defaults.

## Execution milestones and decisions — 2026-10-15

- User requests completion through phase 5, with reviews only after phase 3 and phase 5; at most one review/revise cycle at each milestone. Group implementation into foundation (remaining phases 1–3) and runtime/API (4–5). No intermediate package reviews.
- User approved immutable FinancialRule.id UUID strings as ruleVersion, replacing name/date lookup. Update SQL, contract documentation, and examples consistently; no silent compatibility claim for old named versions.
- User asked for least inter-worker friction and approved bounded setup changes: declare existing SQLAlchemy/psycopg dependencies, install already-declared mypy in an isolated environment, and replace unavailable pgTAP acceptance execution with equivalent pytest/psycopg assertions. Never claim pgTAP ran.
- Prefer a repository-local environment and documented commands over machine-specific cached executables. Preserve unrelated frontend/tools/probe changes and the original stash.