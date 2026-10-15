# Raw implementation report — revision 1, work package A

## Objective and boundary

Read `revision-task-record.md` **Revision 1 — baseline restored**, `revision-plan-001.md`, both revision research reports, proposal, design, runtime spec, tasks and technical plan. Branch `feat/payroll-engine-implementation`, HEAD `7afa880`; original stash `a2a991d996de08a684a936de986aa3320f0c7000` remains applied and retained. No stash/reset/commit, branch switch, subagent dispatch, dependency installation, shared-role mutation, or edit to an existing database. This implements **A only**: R1 FinancePayroll PENDING proposals without approval power; R2 fixed period timezone; R3 whole-minute cutoff below 24:00. No phase 1, 2 or 3 approval claimed; review cycle approval remains with the orchestrator and independent reviewers.

## Changed files

- `backend/migrations/012_payroll_routines_rls.sql`: INSERT approval guard accepts PENDING for Owner or FinancePayroll; null/unknown role, non-PENDING insert, DELETE, and existing Owner-only evidence/actor/immutable UPDATE logic remain restricted.
- `backend/migrations/009_payroll_core.sql`: named CHECKs require `timezone = 'Asia/Jakarta'` and `EXTRACT(SECOND FROM cutoff_local) = 0 AND cutoff_local < TIME '24:00:00'`. Existing date ordering and exact-range uniqueness unchanged. Typed SQL cannot police input-text spelling; the request model remains responsible for exact `HH:MM:00` syntax.
- New `backend/tests/test_payroll_invariants.py`: real `lukla_app` R1–R3 tests with admin identity seed, transaction-local context, checked readback, SQLSTATE assertions, URL/name guard for two connections to the same `payroll_revision_*` database. Fixture-only rule names; no production naming policy. File header documents the R1–R3 coverage ceiling and upgrade path.
- This report only under `openspec/changes/lukla-payroll-engine/artifacts/`.

## Environment and isolation

Read-only preflight with `psql -X -w -h 127.0.0.1 -p 55432 -U postgres -d postgres -Atqc`: PG 18.6, loopback listener, `lukla_app` LOGIN/NOSUPERUSER/NOBYPASSRLS/NOCREATEROLE/NOCREATEDB and no memberships; existing DBs `postgres`, `lukla_test`; `btree_gist`, `pgcrypto` available and `pgtap` unavailable. `psql` app login to `postgres` executed only `SELECT current_user,current_database()` and returned `lukla_app|postgres`. M001 creates the role only if absent; it was already present. Source branch and retained stash verified before and after work. Python: `C:/Users/lenovo/AppData/Local/Programs/Python/Python311/python.exe`; Ruff: `C:/Users/lenovo/AppData/Local/uv/cache/archive-v0/UkdC2l72lX-BSz4-b3WBA/Scripts/ruff.exe`.

All disposable runs used `createdb -w -h 127.0.0.1 -p 55432 -U postgres <generated-name>` (exit 0), then applied each of `001_identities`, `006_payroll_rate_cards`, `007_payroll_qc_inputs`, `008_double_entry_ledger`, `009_payroll_core`, `011_job_idempotency`, `012_payroll_routines_rls` in that order using `psql -X -w -q -h 127.0.0.1 -p 55432 -U postgres -d <generated-name> -v ON_ERROR_STOP=1 -1 -f backend/migrations/<name>.sql`. Each migration exited 0 in each run; first-time DROP POLICY/TRIGGER notices were nonfatal. Before test imports, set both `DATABASE_URL=postgresql+psycopg://postgres@127.0.0.1:55432/<generated-name>` and `LUKLA_APP_DATABASE_URL=postgresql+psycopg://lukla_app@127.0.0.1:55432/<generated-name>`; restore prior values in `finally`, then `dropdb -w -h 127.0.0.1 -p 55432 -U postgres <generated-name>` against only the DB just created. All three drop commands exited 0. No migration or test targeted `lukla_test` or `postgres`.

## Baseline versus revised evidence

| Run | Command and observed output | Exit |
| --- | --- | --- |
| Original DDL in `payroll_revision_old_6697a7b3fbad41948746b718ea47b4c5` | `& $py -m pytest -q backend/tests/test_payroll_invariants.py -p no:cacheprovider`: `FFF`, **3 failed in 3.27s**. R1 FinancePayroll PENDING INSERT raised `RULE_APPROVAL_FORBIDDEN`, `psycopg.errors.InsufficientPrivilege` (`42501`). R2 expected rejection of `UTC` but **DID NOT RAISE**. R3 expected rejection of `12:00:01` but **DID NOT RAISE**. These are target defects, not fixture/permission setup failures. | 1 (expected baseline failure) |
| First revised DDL in `payroll_revision_new_655c93cdcfbf45fab7df9fa2c8eeb5ce` | Focused tests `3 passed in 0.83s`; `& $py -m pytest -q backend/tests -p no:cacheprovider --tb=short`: `50 passed, 1 warning in 5.11s`. | 0, 0 |
| Final revised DDL and finalized tests in `payroll_revision_final_544aa6954c564f20910c429562276749` | `& $py -m pytest -q backend/tests/test_payroll_invariants.py -p no:cacheprovider --tb=short`: `3 passed in 1.17s`; `& $py -m pytest -q backend/tests -p no:cacheprovider --tb=short`: `50 passed, 1 warning in 6.33s`. | 0, 0 |

The baseline run used the first revision of the new test file. After baseline, the tests were strengthened with explicit SQLSTATE/readback, more denied roles and times, and a disposable-URL guard; **the strengthened file itself was not rerun on original DDL**. The same three baseline defect assertions remain, but do not misstate old-versus-new as execution of a byte-identical test file. The final run verifies FinancePayroll/Owner proposals, Finance approval denial `42501`, Owner approval evidence and committed readback, rejected absent/unknown roles and direct APPROVED/REJECTED inserts; UTC/empty/other timezone and second/fractional-second/24:00 cutoffs reject with `23514`, and Jakarta and 00:00/12:00/23:59 whole-minute values insert successfully. The backend warning is Starlette TestClient's existing httpx deprecation notice; no dependency changed.

Original M009 SHA256 `26483AB215D632CE3E7DC2247D9A930B09BD843DAA044839CC9302D87E3C78CB`; final M009 `72C4962C4853FE0E77B9576999FB114C9D492A8583523F0A89A4C411F47725BC`. Original M012 SHA256 `C19B6D5C626AB0FC90E81074255128F6B75E73511B3882EB368FA29F7680AF1A`; final M012 `5BD46EE55A35949BA8CB1E3AFC834131D970854B810FCC9EE581F8B6847E0067`. Final test SHA256 `251AAB6C878B29433F031099F860ECD40CB313F81BC2DA9EAE30F6893A4D864D`. Other migration SHA256s, unchanged between runs: M001 `E37A73B041AC5A5B474D2AA5FE89F82CEC75963686086D5190B697684C6C811B`; M006 `133C11A29CBDDCC97AD5BD8FBD549B5D7F42E1717988622B0460927D0A192C9D`; M007 `B3DD854E29F037D091BF082F889BDC9AEFA6C31BA1AE1AE078E3996E71530C9F`; M008 `FB948DF84C0ED59E007B9FA4A46A545477D62713C4466B4E92BE6E4363F22016`; M011 `6938FC0874EB989E49C29906C4F2A418958661AAACCA9F32DC23262DCE78EE6C`.

## Other executed checks and exceptions

| Command | Observed output / exit |
| --- | --- |
| `& $py -m pytest -q -p no:cacheprovider` in `backend/payroll-costing` | Final `120 passed in 0.55s`, exit 0; an earlier run also passed 120 in 0.58s. |
| `& $ruff check --config backend/payroll-costing/pyproject.toml backend/tests/test_payroll_invariants.py` | Final `All checks passed!`, exit 0. Earlier runs reported unsorted imports, missing EOF newline, then one extra blank line; all repaired with `apply_patch`. |
| `& $ruff format --check --config backend/payroll-costing/pyproject.toml backend/tests/test_payroll_invariants.py` | Final `1 file already formatted`, exit 0. Earlier format check exited 1 for missing EOF newline; repaired. |
| `& $py scripts/check_workspace_hygiene.py` | Final `[OK] Workspace hygiene check passed. Root and sandbox isolation confirmed.`, exit 0. |
| `git diff --check` | Final exit 0. Untracked SQL/test files are not covered by ordinary git diff; whole target files and checks were inspected separately. |
| VS Code `get_errors` for two SQL files and the new test file | No errors reported at the time queried (before final test-only formatting patch). |
| Read-only preflight first attempt | PowerShell parser error (`Get-FileHash backend/migrations/{...}` invalid syntax), so no preflight SQL ran on that attempt. Corrected command returned the PG/role/database facts above and exited 0. |

## Acceptance and risks

R1–R3 baseline failures were captured on original DDL and revised tests passed under the restricted runtime login; Owner-only approval and direct SQL refusal remained. Existing backend/ledger and pure payroll suites passed. No cutoff attribution/period overlap ban, rule naming scheme, repository, HTTP, job, payment runtime, dependency, or frozen contract change was added. Finance/Owner checks are database-context assertions, not an end-user JWT authorization proof: the pool credential and custom GUCs must remain trusted-server-only. `pgtap`, strict mypy, concurrency/RLS R4–R11, CI negative control, independent Security review and browser verification were **NOT_RUN** in this package; browser does not apply to backend-only SQL. No whole technical phase passes from these results. Deployed immutable migration histories require additive migration planning rather than replacing these restored unmerged SQL files.