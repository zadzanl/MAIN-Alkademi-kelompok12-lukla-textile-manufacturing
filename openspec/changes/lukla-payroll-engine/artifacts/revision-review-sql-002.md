# Review Record — revision 2 package A

## Review identity

- **Review:** `lukla-payroll-engine` revision loop 2, package A only
- **Record:** `revision-review-sql-002`
- **Date:** 2026-10-15
- **Branch / HEAD:** `feat/payroll-engine-implementation` / `7afa880`
- **Retained stash:** `a2a991d996de08a684a936de986aa3320f0c7000`; not popped or modified
- **Objective:** determine whether the current M009/M012 SQL delta and `test_payroll_invariants.py` satisfy the frozen package-A acceptance target after revision 1.
- **Implementation files edited by reviewer:** none

This record does not approve technical-plan phases 1–3, package B or C, phase 4 or 5, or any whole-system claim.

## Frozen review brief

### Objective and user impact

Validate the narrow SQL corrections needed for payroll rule proposal authorization and payroll-period input invariants. The user requested a maximum-three-loop review/revision workflow and explicitly limited this review to package A.

### Acceptance criteria

- **R1:** `FinancePayroll` and `Owner` may propose `PENDING` financial rules; `FinancePayroll` cannot approve; `Owner` approval requires actor/evidence; missing or unknown roles fail closed; direct `APPROVED` and other non-`PENDING` inserts remain denied.
- **R2:** payroll periods accept only `Asia/Jakarta` and reject UTC, empty, and other time zones.
- **R3:** payroll periods reject seconds, fractional seconds, and `24:00:00`, while accepting `00:00:00`, `12:00:00`, and `23:59:00`.

The target includes preservation of existing approval restrictions and use of a restricted `lukla_app` connection against a disposable `payroll_revision_*` database. It does not require broader R4–R11 evidence for this package-A verdict.

### Changed surface

- `backend/migrations/009_payroll_core.sql`
- `backend/migrations/012_payroll_routines_rls.sql`
- `backend/tests/test_payroll_invariants.py`

### Evidence and limits

- `artifacts/revision-task-record.md`, revision 1 baseline restored.
- `artifacts/revision-plan-001.md`.
- `artifacts/impl-revision1-sql.md`.
- `artifacts/revision-review-sql-001.md`.
- `artifacts/review-behavioral-revision2.md`.
- `artifacts/review-security-revision2.md`.
- Prior C-001 result preserved in `revision-review-sql-001.md`.
- Current package-A files are untracked restored work; ordinary `git diff` does not show their contents. Whole-file reads and SHA256 values were used.
- No browser verification is applicable to this backend-only SQL package. R4–R11, phase 1–3 completion, package B/C, phase 4/5, strict mypy, pgTAP, CI negative control, JWT mapping, pooled context reset, and end-user authorization are not claimed.

## Route decisions and dispatch accounting

| Dimension | Decision | Controlled tags / reason | Actual instances | Usable result | Execution state |
|---|---|---|---:|---:|---|
| Behavioral | YES | `observable-behavior`, `defect-regression`, `data-integrity`, `behavioral-validation`; SQL authorization and invariant behavior changed | 2 | 1 (`B-002`) | `COMPLETE` usable coverage; `B-001` had no usable structured result |
| Changeability | YES | `teammate-safety`, `module-responsibility`, `interface-contract`, `dependency-shape`; prior package-A handoff risks remain relevant | 1 | 1 (`C-001`) | `COMPLETE` prior result reused; no redundant dispatch |
| Security | YES | `trust-boundary`, `identity-or-authorization`, `untrusted-input`, `data-integrity`; M012 changes authorization semantics | 2 | 1 (`S-002`) | `COMPLETE` usable mandatory Security coverage; `S-001` had no usable structured result |

Security was selected and usable Security Assurance coverage is present. The failed first Behavioral and Security dispatches are preserved in execution health; they are not silently counted as completed evidence. No additional instance was necessary after B-002 and S-002 returned complete, role-bounded results.

## Preserved specialist results

### B-002 — Behavioral Assurance

- **Status:** `COMPLETE`.
- **Source:** `artifacts/review-behavioral-revision2.md`.
- **Evidence preserved:** source/hash match for all three package-A files; static verification of M009 named checks and M012 proposal/approval guard; historical baseline `FFF` and revised focused/full-suite results reported; fresh isolated PG18.6 run with `3 passed` focused and `50 passed, 1 warning` backend tests; disposable database cleanup succeeded.
- **Source findings preserved:** B2-01 test ownership/isolation is not guaranteed; B2-02 several role/error-layer and approval edge cases are not dynamically distinguished; B2-03 final strengthened tests were not run byte-identically against original DDL.
- **Limits preserved:** no R4–R11, end-user authentication, JWT mapping, concurrency, browser, pgTAP, strict mypy, or whole-phase claim.

### S-002 — Security Assurance

- **Status:** `COMPLETE`.
- **Source:** `artifacts/review-security-revision2.md`.
- **Evidence preserved:** restricted-role PG18.6 run; RLS/FORCE RLS and privilege catalog checks; SECURITY DEFINER search paths and grants; M012 role/status/evidence/tenant checks; focused revised test passed; disposable database cleanup succeeded.
- **Source findings preserved:** S-01 trusted connection-context/GUC dependency; S-02 PUBLIC EXECUTE on the trigger function as existing hardening debt; S-03 broader approval negative cases are not dynamically exercised.
- **Limits preserved:** no JWT or caller-to-context proof, pooled reset proof, SQL injection/concurrency proof, R4–R11, browser, pgTAP, or full-suite rerun in this assignment. S-02 did not establish an exploit.

### C-001 — Changeability Assurance

- **Status:** `COMPLETE`.
- **Source:** `artifacts/revision-review-sql-001.md`, preserved under the prior review's C-001 section.
- **Evidence and source findings preserved:** C-01 untracked package-A files are fragile to ordinary diff review; C-02 focused tests can silently skip without two environment variables and are not in CI; C-03 checked-reader coupling is obscure; C-04 process-global environment variables can redirect other backend tests; C-05 psycopg-specific SQLSTATE access is conditional on driver pinning.
- **Prior classification and limit preserved:** these were treated as non-blocking package-A handoff observations, not SQL defects; no whole-phase claim was made.

### Failed first instances

- **B-001:** no usable protocol-shaped result; raw probe material was not promoted to specialist coverage.
- **S-001:** no usable protocol-shaped result; transport failure. This did not remove the Security route; S-002 supplied the required usable Security result.

## Acceptance evidence assessment

| Criterion | Assessment | Evidence boundary |
|---|---|---|
| R1 | **Supported for package A.** | M012 INSERT guard allows only `PENDING` with `Owner` or `FinancePayroll`; UPDATE remains Owner-only with actor/evidence/immutability checks; direct deletion/non-PENDING paths remain denied. Focused revised test exercised committed PENDING readback, Finance approval refusal, Owner approval with evidence, Owner proposal, invalid roles, and direct non-PENDING inserts under `lukla_app`. |
| R2 | **Supported for package A.** | M009 named check fixes `timezone = 'Asia/Jakarta'`; revised test rejects UTC/empty/other zones with SQLSTATE `23514` and accepts Jakarta on an isolated database. |
| R3 | **Supported for package A.** | M009 named check requires whole minutes and value below `24:00:00`; revised test rejects seconds, fractional seconds, and `24:00:00` with `23514`, and accepts the three specified whole-minute values. |
| Preservation / restricted execution | **Supported with stated limits.** | Specialist reports record `lukla_app` as restricted (`LOGIN`, non-superuser, no bypass RLS, no memberships), migrations applied in order to generated disposable databases, focused test success, and cleanup. This is not end-user authentication proof. |

Reported current hashes match the revision-1 implementation report: M009 `72C4962C4853FE0E77B9576999FB114C9D492A8583523F0A89A4C411F47725BC`; M012 `5BD46EE55A35949BA8CB1E3AFC834131D970854B810FCC9EE581F8B6847E0067`; test `251AAB6C878B29433F031099F860ECD40CB313F81BC2DA9EAE30F6893A4D864D`.

## Classified findings

No `BLOCKING_DEFECT` or package-A acceptance-tied `PROOF_GAP` remains.

| Source ID / provenance | Severity | Orchestrator classification | Finding and consequence | Required closure / validation |
|---|---|---|---|---|
| B2-01 / B-002 | MINOR | `LEARN_NOTE` | Test fixture ownership is not fully proven: a prior `payroll_revision_*` database or wrong principal could be selected, and missing URLs can skip. The reviewed run used a newly created database and restricted login, so this does not invalidate that evidence. | Before treating this as an unattended regression gate, require disposable-database ownership and runtime-principal checks; validate unsafe/missing configuration fails clearly without writing to an existing database. |
| B2-02 / B-002 | MINOR | `LEARN_NOTE` | Some negative role assertions prove refusal but do not distinguish context/RLS rejection from the intended guard; null-evidence and approved-row immutability are source-inspected rather than fully exercised. R1 as frozen does not require the broader R5/R6 matrix. | If broader R5/R6 assurance is later claimed, add committed readback and intended-error assertions on a new disposable database. |
| B2-03 / B-002 | MINOR | `LEARN_NOTE` | The final strengthened test was not run byte-identically against the original DDL, so the before/after comparison is historical targeted evidence rather than an exact same-test replication. | If exact same-test before/after proof is required, reconstruct old DDL in a separate disposable database and run the unchanged final test; otherwise retain this limitation. |
| S-01 / S-002 | MAJOR | `LEARN_NOTE` for package A (trust-boundary note) | `app.*` context settings are trusted-server context, not authentication. A party holding the SQL credential could request an Owner context; the review did not establish that an untrusted end user can obtain that credential. | Keep the credential and arbitrary SQL behind the application boundary; verify authenticated caller-to-context mapping and pooled reset before making end-user authorization claims. |
| S-02 / S-002 | MINOR | `LEARN_NOTE` (hardening note) | PUBLIC EXECUTE on `payroll_rule_approval_guard()` is existing hardening debt. It is a trigger function and no escalation was established. | Review/revoke unnecessary PUBLIC EXECUTE in a separate privilege-hardening pass and recheck catalog ACLs and trigger behavior. |
| S-03 / S-002 | MINOR | `PROOF_GAP` for broader R5/R6; `LEARN_NOTE` for frozen package A | Missing dynamic NULL-evidence, wrong-tenant, second-approval and approved-row mutation cases would matter to broader R5/R6 assurance, not to frozen R1–R3 acceptance. | Run the broader negative matrix before claiming R5/R6 or phase-level assurance. No package-A remediation is required from this finding. |
| C-01..C-05 / C-001 | MAJOR/MINOR | `LEARN_NOTE` | Untracked files, environment-dependent test execution, obscured checked-reader coupling, process-global environment effects, and driver-specific SQLSTATE access are handoff/changeability risks. The frozen package-A target does not require commit history, CI wiring, or a tracked harness. | Address before unattended repository regression use or normal handoff; validate with an isolated tracked diff, explicit disposable-DB recipe/gate, separated suite configuration, and pinned/declared driver behavior. |

The classifications intentionally keep S-01 as a trust-boundary note and S-02 as a hardening note. S-03 is a `PROOF_GAP` only for broader R5/R6 assurance and remains a non-blocking `LEARN_NOTE` against the frozen package-A target. Broader R5/R6 or phase-1–3 evidence requirements are not promoted into package-A blockers. No specialist established an unsafe package-A SQL behavior.

## Missing evidence and warnings

- Exact byte-identical execution of the final strengthened test against original DDL is absent.
- Test harness ownership, CI execution, and safe missing-URL behavior remain unverified.
- Broader approval edge cases and trust-boundary integration remain unverified.
- The package-A files remain untracked in the restored worktree; ordinary `git diff` cannot represent them.
- No phase 1, 2, or 3 pass is claimed. Packages B/C and phases 4/5 remain outside this record.
- Browser verification is not applicable; pgTAP, strict mypy, concurrency, JWT mapping, and pooled context reset were not run.

These are explicit limits and handoff notes, not blockers under frozen R1–R3.

## Verdict

**APPROVED — package A only.**

R1–R3 are supported by the current source inspection, preserved baseline/revised evidence, fresh restricted-role disposable-database verification, and usable independent Behavioral and Security Assurance results. No package-A `BLOCKING_DEFECT` or acceptance-tied `PROOF_GAP` remains. This approval does not pass any whole phase or authorize claims outside the frozen brief.

## Execution health

**DEGRADED.** The usable Behavioral (`B-002`), Changeability (`C-001`), and mandatory Security (`S-002`) results are complete, but the earlier B-001 and S-001 instances failed to produce usable results. A valid package-A verdict is nevertheless possible because replacement usable B/S coverage exists and all required Security coverage is present.

## Remediation validation

No blocking remediation is required for this package-A verdict. The exact remaining gaps are the harness/ownership and broader-assurance items listed above. Any future review that claims R5/R6, phase 1–3 completion, end-user authorization, or package B/C must use a new frozen brief and obtain the corresponding evidence; it must not reuse this package-A approval as proof.
