# Technical Plan: Payroll phases 1–3, first revision

## Goal

Repair the reviewed phase-1/2/3 gaps without redesigning payroll or implementing technical-plan phase 4/5. Start with contract-backed SQL fixes that do not depend on a rule-naming decision; then complete only the approved persistence seams. This is a planning handoff, not an approval.

## Task identity and boundary

- Confirmed **revision-task-record.md Revision 1 — baseline restored**. HEAD is `7afa880`, branch `feat/payroll-engine-implementation`.
- Original stash remains `a2a991d996de08a684a936de986aa3320f0c7000`, applied and retained. Do not pop, reset, clean, switch branches, or overwrite the restored work.
- Read both `revision-research-database-001.md` and `revision-research-persistence-001.md`, plus proposal, design, runtime spec, tasks, and `technical-plan-001.md` in this change.
- Phase numbers below refer to the technical plan, not sections of `tasks.md`. Maximum three review/revision cycles; this planning/baseline run consumes no implementation cycle. No subagents dispatched; no source files edited; no phase pass claimed.
- Required independent Security coverage remains an approval gate. With no subagents dispatched in this assignment, that evidence has not been produced. The orchestrator must obtain usable independent review later, or report approval blocked rather than approve its own work.

## Current Reality

### FIND dispositions

| Question | Retrieved result | Consequence |
|---|---|---|
| Is `ruleVersion` a UUID string? | No authoritative UUID representation found. Frozen `contracts/openapi.yaml:1193,1227` specifies a plain string; `test_payroll_calculation_models.py` and `tests/conftest.py` use `v1`. M012 `calculate_weekly_payroll(uuid,text)` compares it to `payroll_periods.rule_version` and selects `financial_rule_versions.rule_name` plus effective date. UUID IDs separately identify stored rows and run references. | Do not parse every public version as UUID, replace it with `str(rule.id)`, or silently change lookup semantics. The existing SQL behavior is name/date resolution, not proof that the naming policy was approved. |
| How does a proposal acquire `rule_name`? | M009 requires it; `FinancialRuleRequest` contains no name/version field. Schema spec §8 requires `parameters` to conform to that request. No producer, registry, or authoritative derivation found in semantic search and targeted backend/contract/schema searches. | A real integration decision remains: approve the internal name/namespace derivation and how clients obtain/use it. Do not add a public field, arbitrary JSON key, generated constant, or caller-supplied internal name to work around the gap. Tests may use explicitly labelled fixture names. |
| Must periods never overlap? | Schema spec table `payroll_periods` specifies unique `(tenant_id,period_start,period_end)`, not exclusion. OpenAPI supplies no overlap rule. The technical plan lists overlap as an edge case, not an approved ban. Rate cards and financial rules have separate explicit exclusion rules. | Preserve exact-window uniqueness and end-after-start. Adjacent windows remain valid. Do not add period exclusion without a policy decision. Database research finding 3/N3 overstates the contract when it treats overlap rejection as mandatory; persistence research correctly qualifies it. |
| What does cutoff mean? | Fixed period timezone and whole-minute format are specified. `19-business-defaults-register.md` OQ-5 still marks Saturday noon and handling of uninspected output as proposed/unresolved. | Enforce storage format now; do not choose noon, shift attribution by cutoff, or infer close/defer rules. Cutoff attribution/overlap decisions do not block the first SQL patch. |
| Which Python can run tests? | Explicit Python 3.11.4 has pytest 8.3.5, SQLAlchemy 2.0.52, psycopg 3.3.4, Pydantic 2.10.6. Launcher default Python 3.14.2 has pytest but lacks SQLAlchemy/psycopg. Bare pytest resolves to another Python314 Scripts path. | Use explicit Python311 `-m pytest`, not bare pytest or default `py`. CI targets 3.11. |
| Are Ruff/mypy installed executables? | Ruff is absent from PATH but cached executable below runs as 0.17.0. No runnable mypy found in PATH, inspected Python roots, workspace, `.local`, or uv cache; Python311/3.14 module probes found none. Cache metadata and a macOS mypy wheel lock are not an installed Windows tool. | Ruff checks can run now, no installation. Strict mypy is NOT_RUN; do not use `uvx` or install to conceal this gap. Availability is not globally disproven outside searched locations. |
| Is shared SQLAlchemy packaging ready? | `backend/payroll-costing/requirements.txt` declares only Pydantic; dev requirements add Ruff/mypy/pytest. No shared backend requirements/pyproject exists in inspected backend inventory. CI installs only payroll dev requirements. SQLAlchemy/shared imports work from repo root with current Python311; `find_spec('backend')` from package directory returns None. | Local availability is not reproducible packaging. Before repository imports land, approve/declare the already-used SQLAlchemy dependency and explicit launch path; do not install anything in this task or add ad-hoc `sys.path` code. |
| Can the live PG18 cluster host a fresh test DB without role changes? | Yes for the current inspected state, and executed successfully below. Existing `lukla_app` is LOGIN, NOSUPERUSER, NOBYPASSRLS, NOCREATEDB, NOCREATEROLE, with no memberships returned. M001 only creates it if absent; remaining grants are database-local. | Reuse that role only while these preconditions hold. No ALTER ROLE/password reset/global membership changes. If absent, privileged, or incompatible, use an independently initialized temporary cluster, not another DB in the shared cluster. |

### Actual verification on 2026-10-15

| Executed action | Observed result / limit |
|---|---|
| `python -m pytest -q` from `backend/payroll-costing` using Python311 | **120 passed in 0.73s**. Existing pure tests only; no new repository tests exist. |
| Cached Ruff `check .`; `format --check .` from payroll directory | **All checks passed; 34 files already formatted**. Ruff 0.17.0; no CI/negative-control execution. |
| `python scripts/check_workspace_hygiene.py` | Successful hygiene check. |
| Read-only PG catalog at `127.0.0.1:55432` | PostgreSQL **18.6**, listens on `127.0.0.1`; databases initially `postgres`, `lukla_test`. `btree_gist` and `pgcrypto` available; no `pgtap` row. App login to `postgres` executed only `SELECT current_user,current_database()`. |
| New disposable database `payroll_revision_8184db2f66254268862359cd5641dcf6` | Created successfully; M001, M006, M007, M008, M009, M011, M012 each applied with `psql -X -w -q -v ON_ERROR_STOP=1 -1 -f`. Existing role reused; no role creation branch taken. |
| `python -m pytest -q backend/tests` against that database | **47 passed, 1 warning in 9.89s**, exit 0. Warning: Starlette TestClient's httpx usage deprecated. No dependency change warranted here. This is existing backend evidence, not payroll concurrency/RLS regression coverage. |
| Disposable cleanup | `dropdb` of exactly the created database exited 0; prior DATABASE_URL/LUKLA_APP_DATABASE_URL restored. No migration/fixture writes to existing databases. |
| Not executed | New payroll tripwires, strict mypy, pgTAP, CI negative control, independent review, browser verification. Browser is not applicable to this backend-only scope. |

## Approach

Use three small work packages, preserving the approved architecture. Begin with the phase-2 SQL patch after capturing old-code failures. Phase-1 gates and phase-3 persistence must not be called complete simply because that patch is correct.

| Work package / technical phase | Outcome | Exact likely files | Verification |
|---|---|---|---|
| A / phase 2, first edit | Finance can propose PENDING rules; periods obey fixed timezone and whole-minute range | `backend/migrations/009_payroll_core.sql`, `backend/migrations/012_payroll_routines_rls.sql`; new `backend/tests/test_payroll_invariants.py` | Old/new restricted-role tripwires R1–R3 below, unchanged unit/backend suites |
| B / phase 1 | Reproducible typed session seam and gates, without framework duplication | `backend/payroll-costing/requirements.txt`, `backend/payroll-costing/pyproject.toml`, `.github/workflows/ci.yml`, `backend/payroll-costing/README.md` only where demonstrated necessary | Ruff, strict mypy when available, import-path check, unit tests, hygiene, isolated lint negative control |
| C / phase 3, conditional | Persist rules/periods using checked reads and caller-owned transactions; enforce lifecycle in SQL | new `backend/payroll-costing/src/repositories/__init__.py`, `rules.py`, `periods.py`; new `backend/payroll-costing/tests/test_rules_repository.py`, `test_periods_repository.py`; M012 for checked transition and invariant fix | Restricted-role read/write/CAS/idempotency tests; naming decision before proposal producer; independent review |

### A. Safe first edit scope

1. Add failing tests to `backend/tests/test_payroll_invariants.py` first. Use admin fixture setup but actual `lukla_app` connections for operations. Existing ledger fixtures are local to `test_ledger.py`, not reusable global fixtures; do not import that test module merely to inherit its fixtures. Keep minimal payroll fixtures local, with an explicit disposable-URL guard before any commit. No migrations against an implicit default URL.
2. In **M012 `payroll_rule_approval_guard() RETURNS trigger`**, change only the INSERT role condition to allow `Owner` and `FinancePayroll`, **only when status is PENDING**. Use a null-safe membership condition: a missing role must still refuse. Preserve DELETE refusal and all UPDATE-to-APPROVED checks: Owner, actor match, non-null evidence, unchanged fields, immutable APPROVED row. Do not broaden approval grants or grant raw SELECT. Preserve its existing SECURITY DEFINER/search_path setup.
3. In **M009 `CREATE TABLE payroll_periods`**, add named checks for `timezone = 'Asia/Jakarta'` and `EXTRACT(SECOND FROM cutoff_local) = 0 AND cutoff_local < TIME '24:00:00'`. Keep NOT NULL, date ordering and exact-range uniqueness. Do not change `time` to `time(0)` (rounding could hide invalid fractions), default the cutoff, or add overlap exclusion. SQL stores a typed value, so it cannot enforce the original text spelling; the existing request model remains responsible for exact `HH:MM:00` syntax.
4. No repository naming decision is needed to test these fixes: use fixture-only `rule_name` values and explicit request context. Do not implement production proposal naming as part of A.
5. Do not edit M001/M008, shared ledger behavior, calculation algorithms, HTTP routes, jobs, or payment adapters. New SQL invariants must be tested using a fresh schema both before and after the patch. Existing restored migrations are untracked: ordinary `git diff` will not show their contents; inspect whole files and preserve baseline hashes/copies outside the repo before editing.

### B. Packaging and adapter boundary

- Reuse `sqlalchemy.orm.Session`, `backend/app/core/database.py:set_db_tenant_context` and `backend/app/services/idempotency.py:{reserve_or_get_idempotency,complete_idempotency}`. Do not add a base repository, new ORM, second auth system, unused protocols, or ledger adapter.
- Recommended minimum packaging resolution: explicitly declare SQLAlchemy 2.x where the payroll repository imports it, using the existing shared application's SQLAlchemy approach. This changes the package manifest and CI installation set even though the dependency is already used locally: obtain maintainer agreement before that edit. Do not assume a nonexistent shared manifest will supply it. Psycopg is needed in the shared integration-test environment, not by pure payroll tests.
- Run shared integration from repository root; run pure tests from the payroll directory as today. For tests that need both `backend.app` and local `src`, explicitly set PYTHONPATH to repository root and payroll directory for that test process, restoring it afterward. A pyproject pythonpath amendment is acceptable only after its effect on CI and imports is tested. No runtime `sys.path` mutation or package rename.
- Caller owns context installation, idempotency reservation, repository call, completion and commit in **one Session transaction**. Repositories never commit/rollback, open a second connection, or call a ledger service that commits. SQLAlchemy autobegin means an auth lookup may already have started the transaction; do not blindly nest `Session.begin()`.
- Keep current pure service behavior. Correct the stale evidence-column docstring in `src/services/financial_rules.py` only if that file is otherwise touched; M009 already has evidence and approver columns.
- Do not mark strict typing verified by suppressing imported errors, adding Any escapes, or running Python314 with incompatible dependencies. If mypy remains unavailable, report the gate as NOT_RUN and request tool availability/installation approval separately.

### C. Concrete persistence handoff (after prerequisites)

These are proposed internal signatures, not functions that already exist. Use UUID, date, Sequence, Session and existing contract models; no public API addition.

`backend/payroll-costing/src/repositories/rules.py`:

- `list_financial_rules(db: Session, tenant_id: UUID) -> list[FinancialRule]`
- `get_required_versions(db: Session, tenant_id: UUID, rule_names: Sequence[str], on_date: date) -> list[RuleReference]`
- `propose_financial_rule(db: Session, tenant_id: UUID, actor_id: UUID, role: str, request: FinancialRuleRequest) -> FinancialRule` — **blocked until proposal-to-name derivation is agreed**; do not sneak in a new request field.
- `approve_financial_rule(db: Session, tenant_id: UUID, actor_id: UUID, role: str, rule_id: UUID, approval: FinancialRuleApproval) -> FinancialRule`

`backend/payroll-costing/src/repositories/periods.py`:

- `create_payroll_period(db: Session, tenant_id: UUID, request: PeriodRequest) -> Period`
- `list_payroll_periods(db: Session, tenant_id: UUID) -> list[Period]`
- `transition_period(db: Session, tenant_id: UUID, period_id: UUID, expected: PayrollPeriodStatus, target: PayrollPeriodStatus) -> None`

Rules for implementation:

1. Tenant/actor/role arguments must agree with transaction context installed from trusted shared auth; they are not a way for request data to select a different principal. Do not treat caller-controlled custom settings as independent authentication. Existing raw DB credentials are trusted-server credentials, never client credentials.
2. Read using existing **`payroll_read_rows(text,uuid,uuid,integer) RETURNS SETOF jsonb`**, with bound table/ID/cursor/limit arguments. Raw ORM SELECT is intentionally denied. Page through all results via `p_after` (maximum 1000 each); test 1001 rows, empty pages and filter correctness. Validate JSON into typed models; do not bypass strict typing with casts.
3. Store validated proposal fields as contract-shaped parameters (including effectiveFrom), with separate metadata columns. Generate a UUID before INSERT; do not use `RETURNING *` when app SELECT privilege is absent. Read back with the checked reader. Approval calls existing **`payroll_approve_rule(uuid,uuid) RETURNS void`**, followed by checked read. Evidence existence beyond UUID presence is not proven: upstream file table is absent. A zero UUID ban is not specified by the current model/contract and must not be invented.
4. Missing, wrong-tenant, pending or out-of-effective-window required rules must fail closed. Do not drop unresolved names from the result and then let `require_approved([])` authorize calculation. Preserve named effective-date resolution until an approved replacement exists; immutable UUID pinning belongs to stored run references.
5. Use pure `create_period`/`assert_valid_period_range` and `assert_transition_allowed` as existing validation helpers. Do not add a blanket APPROVED-rule prerequisite to period creation: PENDING_RULE is a supported lifecycle state. Keep unresolved rule applicability from authorizing monetary operations.
6. Test direct restricted UPDATE first; current no-SELECT grants are expected to block WHERE/RETURNING paths. Add **`payroll_transition_period(p_period_id uuid, p_expected_status text, p_target_status text) RETURNS void`** in M012 only as a narrow checked definer: validate context and allowed roles, find tenant-scoped row with `FOR UPDATE`, reject missing/stale state, then update status only. Revoke PUBLIC execute, grant only app role, fix search_path to `pg_catalog, public, pg_temp`, and keep triggers active. Do not restore blanket SELECT.
7. Before exposing that routine, tighten existing **`payroll_period_transition() RETURNS trigger`** to match the pure transition table and prevent edits to period identity/window/timezone/cutoff/rule reference, especially same-status edits after approval. Test the discrepancy: current SQL permits edges such as APPROVED→REVERSED that the pure table forbids. Do not let a convenience transition bypass existing approved-run/payment prerequisites. Revoke broad direct period UPDATE when the checked transition supplies all required application paths.
8. Idempotent mutation wrappers use shared reserve/complete in the caller transaction; repository functions remain transaction-neutral. Test commit-before-response replay with same body/key and changed-hash refusal. Approval replay must return the prior result rather than attempt a second approval; a second approval with a different key remains refused.
9. Prove OPEN→PENDING_RULE persistence independently. The calculation exception rolls back its transaction; no phase-3 claim should imply that calculation-to-409 orchestration now exists. That wiring stays outside this revision. Do not swallow the exception and continue a failed transaction.
10. Optional approvalReference/note storage is not represented by dedicated current columns. Reuse an appropriate existing audit boundary if its schema supports these fields; if it does not, record that gap rather than silently claiming the metadata was persisted or adding private keys to financial parameters.

## Required regression matrix

All items below are **NOT RUN in this planning task**. Before modifying SQL, run new tests against baseline DDL in a fresh disposable database and record the exact failing assertion/SQLSTATE. Run the same tests after the patch in another fresh database. A test failing due to bad fixture permissions or collection failure is not an old-code defect demonstration.

| ID | Required check | Baseline expectation and scope |
|---|---|---|
| R1 | Owner and FinancePayroll can INSERT PENDING proposals; Finance approval denied; Owner approval with evidence accepted; absent/unknown roles denied; direct APPROVED insert denied | Finance proposal expected to fail with `42501 RULE_APPROVAL_FORBIDDEN` before fix. Preserve other refusal cases. |
| R2 | Direct SQL rejects UTC, empty/other timezone; accepts exactly Asia/Jakarta | Old M009 expected to accept invalid zone; correct assertion must fail before fix. Use different valid period ranges to avoid uniqueness masking failure. |
| R3 | Reject `12:00:01`, `12:00:00.000001`, `24:00:00`; accept `00:00:00`, `12:00:00`, `23:59:00` | Old M009 expected to accept invalid values. Assert CHECK SQLSTATE 23514 after patch, not merely any exception. |
| R4 | Reject equal/reversed dates and duplicate same-tenant range; accept adjacent ranges and same range in tenant B | Existing guards should already pass. Nonidentical overlap is a characterization test, not a newly forbidden case. |
| R5 | Missing context on empty checked read raises TENANT_CONTEXT_MISSING; A cannot read/write B; raw SELECT remains denied; rollback/reuse does not leak context | Verify using real app connections, role attributes and function/schema privileges. Report direct SQL credential trust separately from JWT auth. |
| R6 | Missing evidence, Finance approval, wrong tenant/ID and second approval refused; APPROVED fields immutable; proposals remain gated | Check committed readback and zero new monetary rows on pending paths. Do not assert upstream file existence. |
| R7 | Restricted INSERT/read-after-write without SELECT; 0/1/1000/1001-row pagination; request/response alias mapping | New persistence behavior. Mock tests alone are insufficient. No fake repository or route. |
| R8 | Invalid lifecycle edge and same-status protected-field mutation rejected; stale expected state fails; authorized pending transition commits | Old trigger expected to permit some invalid edges/field edits. Compare with pure ALLOWED_TRANSITIONS, preserving run prerequisites. |
| R9 | Two app sessions race transition/proposal approval and shared idempotency reservation; same key/hash replays once; changed hash conflicts | Use barriers with deadlines, lock_timeout and statement_timeout; collect both outcomes and final counts. Serial calls are not concurrency proof. |
| R10 | Existing phase-2 SQL safeguards: pending calculation writes no wage/run/item/bonus/overhead rows; duplicate wage/assembly bonus rejected; ledger immutable/unbalanced/late-line controls hold | Test existing routines, do not add phase-4 orchestration. Existing 47 backend tests do not substitute for payroll coverage. |
| R11 | Timestamp `2026-09-30 17:30+00` attributed consistently under UTC/Jakarta sessions; start inclusive/end exclusive | Current `passed_at::date` is session-sensitive. Capture old failure; repair each affected M012 predicate consistently using explicit factory timezone in a separately bounded phase-2 fix. Do not combine this with a newly invented cutoff-shift policy. Monetary routine changes are not part of first edit A. |

Preserve database research N1–N9 as remaining phase-2 evidence requirements, including simultaneous calculation/late-credit behavior and unchanged old run snapshots. These are tests of existing SQL, not authorization to implement phase-4 repositories. If the unresolved cutoff policy prevents an expected result, label that specific assertion BLOCKED, not the whole executable suite.

## Verification commands and isolation procedure

Run from `C:\Projects\hackathon-MAIN-alkademi`. Commands for future verification are not additional execution claims.

```powershell
$py = 'C:/Users/lenovo/AppData/Local/Programs/Python/Python311/python.exe'
$ruff = 'C:/Users/lenovo/AppData/Local/uv/cache/archive-v0/UkdC2l72lX-BSz4-b3WBA/Scripts/ruff.exe'
$pg = 'C:/Program Files/PostgreSQL/18/bin'
git status --short --branch
git rev-parse 'stash@{0}'
& $py scripts/check_workspace_hygiene.py
Push-Location backend/payroll-costing
try {
    & $ruff check .
    & $ruff format --check .
    & $py -m pytest -q
    # Only after a runnable, approved mypy environment exists:
    # & $py -m mypy src/ --strict
} finally { Pop-Location }
```

For every command, capture and check its own exit code; a later successful command must not hide an earlier failure. The cached Ruff path is ephemeral: if missing later, report missing tooling, not an installation permission.

**Database preflight:** use `psql -X -w -h 127.0.0.1 -p 55432 -U postgres -d postgres -Atqc` with `SELECT` queries for server version/listen address, existing `lukla_app` attributes/memberships, and database names. Never print password catalogs. Check M001 still has only conditional role creation and migrations contain no new global-role mutations. Test the app login read-only. If role preconditions changed, do not repair the shared cluster.

**Disposable run:** generate `$db = 'payroll_revision_' + [guid]::NewGuid().ToString('N')`; create with `createdb -w -h 127.0.0.1 -p 55432 -U postgres $db`, recording ownership only after exit 0. Use a try/finally, save prior environment variables, and apply this exact order:

```text
backend/migrations/001_identities.sql
backend/migrations/006_payroll_rate_cards.sql
backend/migrations/007_payroll_qc_inputs.sql
backend/migrations/008_double_entry_ledger.sql
backend/migrations/009_payroll_core.sql
backend/migrations/011_job_idempotency.sql
backend/migrations/012_payroll_routines_rls.sql
```

For each: `& "$pg/psql.exe" -X -w -q -h 127.0.0.1 -p 55432 -U postgres -d $db -v ON_ERROR_STOP=1 -1 -f $file`; stop immediately on nonzero exit. Record SHA256 per migration, test revision and server version. Set **both** URLs before Python imports settings:

```powershell
$env:DATABASE_URL = "postgresql+psycopg://postgres@127.0.0.1:55432/$db"
$env:LUKLA_APP_DATABASE_URL = "postgresql+psycopg://lukla_app@127.0.0.1:55432/$db"
& $py -m pytest -q backend/tests
# After the proposed test file exists:
& $py -m pytest -q backend/tests/test_payroll_invariants.py
```

For repository tests after they exist and packaging is resolved, set process PYTHONPATH to repo root plus `backend/payroll-costing` and run:

```powershell
Push-Location backend/payroll-costing
try {
    & $py -m pytest -q tests/test_financial_rules_service.py tests/test_payroll_periods_service.py tests/test_rules_repository.py tests/test_periods_repository.py
} finally { Pop-Location }
```

In outer finally restore all saved environment variables, dispose test connections, then drop **only** `$db` if this invocation successfully created it: `& "$pg/dropdb.exe" -w -h 127.0.0.1 -p 55432 -U postgres $db`. Never fall back to dropping `lukla_test`, `postgres`, schemas in an existing DB, or cluster roles; no force-drop of unrelated sessions. Record cleanup errors instead of widening cleanup.

**Fallback if role collision/absence is discovered:** initialize a unique TEMP directory with installed `initdb.exe -D $data -U postgres --auth-local=trust --auth-host=trust`, then start that independently owned test cluster with `pg_ctl.exe -D $data -l $log -o "-p <verified-unused-port> -c listen_addresses=127.0.0.1" -w start`. Trust authentication is for this short-lived, loopback-only local test cluster, never a production configuration. Use generated DB names there and allow M001 to create its role only there. Stop only this cluster via its exact `$data` path in finally. Do not touch the existing `$env:TEMP/payroll_review_pg`. No fallback cluster was initialized in this task; port availability/startup must be checked at execution time, without elevation or new installations.

**pgTAP:** unavailable on inspected PG18 installation. Installed pytest/psycopg can execute assertions without installing extensions, but this is not pgTAP evidence. Leave tasks §3.7 unchecked unless pgTAP actually runs or an explicit acceptance-method change is approved.

## Acceptance Criteria

- R1–R3 fail on baseline for the intended defect and pass on revised DDL; restrictive approval semantics and direct SQL denial remain intact.
- No regression in existing pure/ledger behavior; new DB tests use restricted runtime credentials, not only migration-owner privileges.
- Phase 1 includes reproducible dependency/import setup and strict typing evidence, not merely local imports. CI lint negative control is performed in disposable input/worktree and leaves no deliberate break behind.
- Phase 3 has committed readback, correct tenant isolation, lifecycle CAS, idempotent replay and typed models without hidden commits or naming defaults.
- Separate failures, NOT_RUN tooling, policy BLOCKED assertions and independent review gaps remain visible. Do not infer whole-phase success from individual green checks.
- Orchestrator informs the user when each phase actually passes, only after focused execution and required independent review. Stop after at most three revision/review cycles; escalate remaining anchored blockers rather than start a fourth.

## Non-Goals

No phase-4/5 production adapters, wage/payment orchestration, HTTP registration, jobs, UI, payout-policy decisions, default rates, schema redesign, frozen-contract changes, new dependency installation, ledger rewrites, commits/pushes, or archive. Do not change task checkboxes based on this report.

## Risks and stop conditions

- **Naming:** stop production proposal mapping until derivation is approved. Continue A and fixture-backed SQL tests. Public UUID-only mapping or new public fields require contract review, not an internal shortcut.
- **Policy:** overlap prohibition and cutoff attribution need owner decisions if requested; preserving current uniqueness/format does not. Do not turn an edge-case mention into business authority.
- **Packaging:** stop repository integration into CI if dependency declaration/import resolution is absent. Local installed libraries do not satisfy clean-checkout reproducibility.
- **Isolation:** if app role is missing/privileged, role creation would be global, credentials fail, or migration ownership is unclear, use the independent-cluster fallback or report a concrete execution blocker. No request for exclusive ownership of the existing cluster is needed for the verified separate-DB path with unchanged roles.
- **Migrations:** editing restored, unmerged DDL is appropriate only if these changes have not been deployed as an immutable migration history. If deployed elsewhere, stop and agree an additive migration rather than rewriting history.
- **Lifecycle/security:** stop if a pending rule writes money, tenant isolation fails, approval mutates frozen inputs, or a transition lacks its run prerequisites. No broader grants to make a failing test green.
- **Trust boundary:** current GUC checks trust the application connection. Independent review must assess auth-to-context installation; forged settings through a trusted SQL credential do not by themselves prove an end-user exploit, but are not authentication protection either.
- **Verification:** unavailable mypy/pgTAP/security review prevents the corresponding approval claim, not safe execution of available tests. Do not ask the user to answer facts obtainable from these commands.

## Implementation Handoff

- **Exact next scope:** work package A only: new regression tests, M012 PENDING proposal role condition, M009 period timezone/cutoff checks. Capture old failures before edits. Do not wait for the naming decision to start these tests.
- **Inspect first:** restored M009/M012 in full; `backend/tests/test_ledger.py`; `backend/app/core/config.py`; period/rule contract schemas; revision-1 record and both research reports. Read applicable code-writing guidance before implementing test logic.
- **Tests:** explicit Python311, isolated PG18 run above, R1–R3 then all existing suites; cached Ruff and hygiene; record mypy as unavailable unless resolved.
- **Stop if:** any isolation precondition fails, new behavior exceeds the frozen contract, baseline tripwire fails for fixture/setup rather than the target defect, or a security invariant regresses.
- **Remaining user decisions, not discoverable facts:** proposal naming/namespace; any requested overlap/cutoff policy change; approval to declare missing package dependencies or supply unavailable verification tools. None blocks the safe first SQL patch.

## Retrieval and evidence worklog

- Used local semantic search for rule/period persistence, then exact searches of `rule_name`, `rule_version`, `ruleVersion`, overlap, cutoff, role DDL, manifests and CI. Read required reports/artifacts and affected service/model/SQL/test code. Some oversized terminal output omitted leading text; reread the research reports directly and the omitted design/proposal sections.
- Consulted official PostgreSQL 18 role/function/date-time docs and SQLAlchemy 2.0 transaction docs. Sources: https://www.postgresql.org/docs/18/database-roles.html ; https://www.postgresql.org/docs/18/sql-createfunction.html ; https://www.postgresql.org/docs/18/datatype-datetime.html ; https://docs.sqlalchemy.org/en/20/orm/session_transaction.html . Roles are cluster-global; safe definer paths put pg_temp last; time accepts 24:00 and fractions; Session.commit affects the outer transaction.
- An initial recursive executable search was slow and moved to background; bounded searches located runnable Ruff. Searches for nonexistent root/backend pyproject files and one Windows wildcard rg path produced errors; subsequent manifest inventory resolved those paths. No dependency installation attempted.
- Actual baseline commands/results are enumerated above. Tests were run on unchanged source. New old-code-failure tripwires remain planned, not falsely reported as reproduced. Only this requested report was created in the repository by this planning task.