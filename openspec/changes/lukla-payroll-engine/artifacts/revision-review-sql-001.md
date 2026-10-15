# Review Record — revision 1 package A

## Review identity

- **Review:** `lukla-payroll-engine` revision 1, package A only
- **Record:** `revision-review-sql-001`
- **Branch / HEAD:** `feat/payroll-engine-implementation` / `7afa880`
- **Objective:** review the M009/M012 SQL delta and R1–R3 regression test. This is not approval of technical-plan phases 1–3, package B/C, or phase 4/5.
- **Changed surface:** `backend/migrations/009_payroll_core.sql`, `backend/migrations/012_payroll_routines_rls.sql`, `backend/tests/test_payroll_invariants.py`
- **Implementation files edited by reviewer:** none

## Frozen acceptance target

1. Owner and FinancePayroll may insert `PENDING` financial-rule proposals; FinancePayroll cannot approve; Owner approval requires actor/evidence; missing or unknown roles fail closed; direct `APPROVED` and non-`PENDING` inserts are denied.
2. Payroll periods accept only `Asia/Jakarta` and reject UTC/empty/other zones.
3. Payroll periods reject seconds, fractional seconds, and `24:00:00`, while accepting `00:00:00`, `12:00:00`, and `23:59:00`.
4. Existing approval restrictions and database safeguards are not weakened, and the tests use the restricted `lukla_app` role against a disposable `payroll_revision_*` database.

## Route decisions and dispatch

| Dimension | Decision | Controlled tags / reason | Planned | Actual | State |
|---|---|---|---:|---:|---|
| Behavioral | YES | `observable-behavior`, `defect-regression`, `data-integrity`, `error-recovery`, `behavioral-validation` | 1 | 2 | `FAILED` — B-001 produced no usable structured result; B-002 transport failed |
| Changeability | YES | `teammate-safety`, `module-responsibility`, `interface-contract`, `dependency-shape` | 1 | 1 | `COMPLETE` — C-001 |
| Security | YES | `trust-boundary`, `identity-or-authorization`, `untrusted-input`, `data-integrity`, `security-recovery` | 1 | 2 | `FAILED` — S-001 produced no usable structured result; S-002 transport failed |

Security was mandatory because M012 changes authorization semantics. It was not skipped. No fallback security specialist result was available after the explicit escalation attempts failed with `net::ERR_CONNECTION_RESET`.

## Preserved source results

### C-001 — Changeability Specialist

**Status:** `COMPLETE`.

The specialist inspected the full changed files, isolated the package-A delta against the retained baseline, confirmed the reported hashes, and ran the focused test with disposable URLs (`3 passed in 2.68s`). It reported these findings without classifying them:

- **C-01:** all package-A files are untracked and ordinary `git diff` cannot review/recover them. Required closure: commit the isolated files/report before normal handoff; validate with `git show --stat` and an isolated diff.
- **C-02:** the R1–R3 test is not in CI and silently skips without two undocumented environment variables. Required closure: tracked run instructions and an explicit CI/test gate; validate from a fresh clone.
- **C-03:** `_rule_status` hides its dependency on the checked `payroll_read_rows` interface. Required closure: make the coupling visible by naming/comment; validate that reader failures are diagnosable.
- **C-04:** the new test’s process-global environment can redirect the pre-existing ledger suite to the disposable database. Required closure: document the interaction or isolate configuration; validate target databases before both suites.
- **C-05:** SQLSTATE assertions use psycopg-specific `.orig.sqlstate`. The specialist marked this as conditional on driver pinning and not a current blocker.

The specialist also stated that the strengthened test was not byte-identically rerun against the old DDL and that no whole-phase claim was made.

### B-001 and S-001 — first dispatches

No usable protocol-shaped result was returned. Review-generated raw probe files exist under `prototypes/b001-probe/` and `prototypes/s001-probe/`, including SQL probes and pytest output, but these are not specialist results with the required role/status/evidence/findings/limits headings. They are preserved as workspace evidence, not promoted to independent review coverage.

### B-002 and S-002 — escalations

Both dispatches failed before producing a result: the agent service returned `net::ERR_CONNECTION_RESET`. No findings were obtained from these instances.

## Available implementation and execution evidence

- `impl-revision1-sql.md` reports baseline original-DDL failures: R1 FinancePayroll `PENDING` insert denied with SQLSTATE `42501`; R2 invalid UTC was accepted; R3 `12:00:01` was accepted.
- The same report records final disposable-DB revised runs: focused R1–R3 `3 passed`; backend suite `50 passed, 1 warning`; migrations applied in the prescribed order; `lukla_app` was `LOGIN`, `NOSUPERUSER`, `NOBYPASSRLS`, `NOCREATEDB`, `NOCREATEROLE`, with no memberships; each generated database was dropped.
- The report explicitly says the strengthened test file was not byte-identically rerun on original DDL. That limitation remains.
- Static inspection confirms M009 named checks:
  - `timezone = 'Asia/Jakarta'`
  - `EXTRACT(SECOND FROM cutoff_local) = 0 AND cutoff_local < TIME '24:00:00'`
- Static inspection confirms M012 INSERT guard requires `PENDING` and current role in `Owner`/`FinancePayroll`; the existing UPDATE branch remains Owner-only with actor/evidence/immutability checks.
- Current local focused invocation without explicit disposable URLs did not execute the tests. Current broad backend invocation timed out against unrelated `lukla_test` on port `5433`; it is not evidence against this package.
- Current editor diagnostics reported no errors for the two SQL files and the new test.
- Strict mypy, pgTAP, CI negative-control, R4–R11, and browser checks were not run. Browser verification is not applicable to this backend-only SQL package.

## Classified findings

No implementation `BLOCKING_DEFECT` was established by the available source evidence. C-01 through C-04 are preserved as changeability observations; they are classified as `LEARN_NOTE` for this narrow review because the frozen acceptance target does not require a commit, CI wiring, or tracked runbook, and the historical disposable execution evidence remains assessable.

| Classification | Provenance | Severity | Finding / consequence | Required validation |
|---|---|---|---|---|
| `LEARN_NOTE` | C-001 / C-01 | MAJOR | Untracked package-A files are fragile and ordinary diff review misses them. | Before handoff, isolate/record the files in normal git history and verify the exact three-file delta. |
| `LEARN_NOTE` | C-001 / C-02 | MAJOR | R1–R3 can silently skip outside the specially prepared environment and are not in CI. | Add a tracked disposable-DB recipe or explicit gate before relying on these tests as a repository regression check. |
| `LEARN_NOTE` | C-001 / C-03 | MINOR | Checked-reader coupling is obscured by `_rule_status`. | Rename/comment the helper if the test is retained for ongoing maintenance. |
| `LEARN_NOTE` | C-001 / C-04 | MAJOR | Shared process environment can redirect unrelated backend tests. | Document target selection and run suites separately, or isolate settings resolution. |

## Missing evidence and warnings

- **Required Security coverage is missing.** This alone prevents approval under the review protocol, regardless of the historical SQL test pass.
- Behavioral coverage is also missing as a usable independent specialist result. Raw probe output is not a substitute.
- The current environment did not rerun the disposable database because explicit URLs were absent; no existing database was touched by the review commands.
- The retained worktree contains unrelated restored untracked migrations and modified baseline files, plus review-generated probe directories. Nothing was reset, cleaned, stashed, committed, or deleted.
- The trusted `app.*` GUC design is documented as trusted-server context only; it is not proof of end-user JWT authorization.

## Verdict

**FAILED** — required independent Security coverage is absent, and the selected Behavioral dimension has no usable review result. This is an execution/coverage failure, not a finding that R1–R3 are demonstrably wrong. Do not claim package-A approval or any whole-phase pass.

## Execution health

**DEGRADED** — C-001 completed, but B-001/S-001 returned no usable structured results and both escalation dispatches failed at the agent transport layer. A valid positive verdict cannot be issued from this run.

## Remediation validation

Rerun the unchanged frozen brief after independent Behavioral and Security specialists return protocol-shaped results. Preserve the current implementation and historical evidence. Before a positive verdict, obtain usable Security Assurance coverage, confirm the restricted-role R1–R3 evidence, and separately decide whether C-01/C-02/C-04 should be addressed as repository handoff work. Do not widen the review to packages B/C or whole phases without a new review identity and brief.