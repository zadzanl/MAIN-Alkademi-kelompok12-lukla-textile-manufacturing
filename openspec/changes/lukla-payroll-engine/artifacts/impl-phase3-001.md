# Phase 3 implementation evidence — 2026-10-15

Branch: `feat/payroll-engine-implementation`. Scope: phase 3 only; **no phase review performed**. Five untracked SQL drafts from the timed-out worker were repaired, not discarded. The pre-existing M001/M008 migrations were not edited. Tasks 3.1–3.6 are marked authored/checked; **3.7 remains unchecked because pgTAP is not installed**. No phase 4+ work was done.

## Ownership and ordering

| Object | Sole owner | Reconciliation |
| --- | --- | --- |
| `set_request_context`, `idempotency_records`, identity RLS/grants | M001 | M012 no longer replaces the function or duplicates the table. M001's unique key is `(tenant_id, operation_id, key)`, equivalent to the task's `(tenant_id, key, operation_id)` for uniqueness, but ordered differently for index access. M001's setter does **not** validate actor membership; M012's payroll-only policy helper checks active tenant/actor and supported role, not membership. |
| `sewing_tallies` | M006 | No upstream production migration exists yet. M006 owns the temporary source table; it needs composite order/cut-batch/operator FKs when those owners ship. |
| `ledger_accounts`, `ledger_transactions`, `ledger_entries`, immutability, late-line and deferred balance triggers | M008 | No recreated ledger tables or M012 ledger trigger. Account/entry currency matching remains an unimplemented ledger-owner extension; M012 cannot silently attach it. |
| `job_runs` | M011 | Its period FK references M009. M001, not M011, owns `idempotency_records` despite the literal wording of 3.5. |
| payroll/QC tables and FORCE RLS | M006/M007/M009/M011 definitions, M012 payroll policies | Migration order M001 → M006 → M007 → M008 → M009 → M011 → M012. M012 adds the first-PASS eligibility trigger because M007 precedes M009. |

Each new migration assumes one transaction per file: a failed file rolls back and can be retried from its start. It is **not** safe to replay an already committed migration; there is no migration ledger/runner in scope. M012 drops/recreates only its own policy name if rerun; that is not a general replay guarantee. `btree_gist` is a prerequisite created in M006.

## Changes and boundaries

- M006: exclusion-backed nonoverlapping cards; immutable snapshots; `garment_units.piece_rate_snapshot_id NOT NULL` plus `(tenant_id, piece_rate_snapshot_id)` unique prevents two units from sharing a snapshot. The optional reverse `source_unit_id` is validated by a deferred trigger when present, rather than relying on nullable UNIQUE to establish the relationship.
- M007: QC transitions serialize on the assembly, refuse empty inspections/final assembly mutations, update allocated unit statuses, and reject component edits after QC. M012 records one unvalued first-PASS eligibility event; a pending rule cannot mint monetary facts.
- M009: integer nonnegative monetary columns, partial unique original wage credit per unit, unique bonus accrual per assembly, per-run version/credit references, approved-run payment FK. Cross-client `source_tenant_id` remains distinct; its authorization model is not invented here.
- M011: one `job_runs` row per tenant/kind/period, with M009 period FK; idempotency stays in M001.
- M012: approved rule check precedes wage inserts. Verified tally + QC-passed allocated unit + eligibility event + immutable snapshot drive original credit inserts; `ON CONFLICT` prevents repair double-credit. A scalar ordered aggregate hashes consumed credit IDs/amounts/currency; no invalid aggregate/non-grouped SELECT remains. No eligible credits returns `NULL` UUID with **no run or money**; the phase-4 service must map this to its existing `NO_OUTPUT` status. Pending rule raises `FINANCIAL_RULE_PENDING` before monetary inserts; exception rollback cannot also persist `PENDING_RULE` in that transaction, so phase 4 must record any blocked status separately. Overhead counts distinct first-PASS assemblies and returns `NULL` without allocation for zero units. No additional public API fields or business defaults were introduced. Approval commits run credits after status transition, prevents child edits on approved runs, and payment requires an approved run. Rule insertion cannot directly create an approved version; approval requires Owner context and evidence. Payroll tables have ENABLE/FORCE RLS and a context-validating policy. The app role is a trusted non-owner pool credential, not an end-user SQL credential.

## Environment and exact verification evidence

Windows PowerShell; Python 3.11; PostgreSQL 18.6 executable at `C:\Program Files\PostgreSQL\18\bin\psql.exe` (not on PATH); `pg_isready.exe -h localhost -p 5432` returned `accepting connections`. Configured `DATABASE_URL` (not printed) reached PostgreSQL 18.6 as `postgres` on database `lukla_phase3`; role has `CREATEDB`. `SELECT name, default_version FROM pg_available_extensions WHERE name IN ('pgtap','btree_gist')` returned **only** `('btree_gist','1.8')`. `Get-Command psql, pg_isready, sqlfluff -ErrorAction SilentlyContinue` returned no commands. No dependencies were installed or services started.

Commands run (outputs shown verbatim where concise):

```text
openspec status --change lukla-payroll-engine --json
openspec instructions apply --change lukla-payroll-engine --json
# ready; 8/40 complete before phase 3
& 'C:\Program Files\PostgreSQL\18\bin\psql.exe' --version
# psql (PostgreSQL) 18.6
& 'C:\Program Files\PostgreSQL\18\bin\pg_isready.exe' -h localhost -p 5432
# localhost:5432 - accepting connections
python -m pytest backend/payroll-costing/tests -q
# 120 passed in 0.30s (earlier pass: 120 passed in 1.30s)
python scripts/check_workspace_hygiene.py
# ✅ [OK] Workspace hygiene check passed. Root and sandbox isolation confirmed.
openspec validate lukla-payroll-engine
# Change 'lukla-payroll-engine' is valid
git diff --check
# no output; exit 0
git diff --no-index --check -- NUL backend/migrations/<each new SQL file>
# no whitespace errors for all five drafts; exit 0/1 (no-index differences return 1)
```

Ownership search command: `Select-String -Path backend/migrations/*.sql -Pattern '^CREATE (OR REPLACE )?FUNCTION set_request_context','^CREATE TABLE (IF NOT EXISTS )?idempotency_records','^CREATE TABLE (IF NOT EXISTS )?sewing_tallies','^CREATE TABLE (IF NOT EXISTS )?ledger_(accounts|transactions|entries)','^CREATE TRIGGER .*ledger_entries'`. Output: one `set_request_context` and `idempotency_records` definition (M001), one `sewing_tallies` (M006), one each ledger table and two ledger-entry triggers (M008); no M012 ledger entries/trigger definitions. No pgTAP test location or pgTAP extension exists; `backend/tests/test_ledger.py` is a legacy Python integration suite, not a pgTAP harness, so none was invented.

Disposable integration execution: inline `@' ... '@ | python -` using installed `psycopg`, `DATABASE_URL` translated from SQLAlchemy's `postgresql+psycopg://` to `postgresql://`, `CREATE DATABASE phase3_check_<random>` / `phase3_assert_<random>`, `with db.transaction(): db.execute(file.read_text())` over `sorted(Path('backend/migrations').glob('*.sql'))`, and `DROP DATABASE ... WITH (FORCE)` in `finally`. All seven migrations applied in filename order:

```text
APPLIED 001_identities.sql
APPLIED 006_payroll_rate_cards.sql
APPLIED 007_payroll_qc_inputs.sql
APPLIED 008_double_entry_ledger.sql
APPLIED 009_payroll_core.sql
APPLIED 011_job_idempotency.sql
APPLIED 012_payroll_routines_rls.sql
disposable removed phase3_check_44d12d009dec
```

The direct assertion script seeded two tenants, one actor, one snapshot/verified tally/unit/assembly/component, a QC inspection or first-PASS eligibility event, a pending then Owner-approved rule, a period, and a balanced two-line ledger transaction. Tests ran `SET LOCAL ROLE lukla_app` and `set_request_context` with actor/tenant/role, except the explicit missing-context case; expected SQL errors were caught inside nested transactions. Exact assertions: `calculate_weekly_payroll` with pending rule raises `FINANCIAL_RULE_PENDING` and both `SELECT count(*) FROM wage_credits` and `FROM payroll_runs` are zero; an approved rule mints a 6-minor-unit credit; second original credit and second `qc_bonus_accruals` row raise SQLSTATE `23505`; approval commits run credits and an approved run accepts one evidence-backed payment; editing paid run raises `APPROVED_RUN_IMMUTABLE`; an empty period returns SQL NULL and creates no run; no-context payroll read raises `TENANT_CONTEXT_MISSING` and other-tenant read returns zero; ledger header/entry UPDATE and DELETE raise `LEDGER_IMMUTABLE`. A later variant inserted `qc_inspections(PASS)` as `lukla_app`/QCInspector and asserted both the first eligibility event and unit `QC_PASS` status. Representative final outputs:

```text
PASS QC transition and first-pass eligibility via non-owner role
PASS pending-rule no monetary rows
PASS wage valuation and duplicate wage/bonus rejection
PASS missing context rejection and cross-tenant zero rows
PASS ledger UPDATE/DELETE rejection
disposable removed phase3_assert_ac0b103075c8
```

Another passing variant reported `PASS approved payment, immutable paid run and zero-output without monetary rows`, followed by the duplicate/RLS/ledger passes; its disposable database `phase3_assert_3ab84cc7217a` was removed. Two earlier assertion attempts failed due to **fixture errors**, not accepted invariants: one attached a component after setting its assembly to `QC_PASS` (`ASSEMBLY_FINAL`); one approved a rule without Owner context (`RULE_APPROVAL_FORBIDDEN`). A QC variant accidentally inserted PASS twice and correctly rejected the second as `QC_FINAL_OR_NOT_READY`. Each disposable database was removed after failure. Scripts were inline, not checked in; repeatable pgTAP coverage is still required for 3.7.

## Unverified and known ceilings

- **pgTAP: NOT RUN / UNVERIFIED.** Extension unavailable, so 3.7 is unchecked despite direct PostgreSQL assertions. No review was performed. Overhead `NO_OUTPUT` and cross-client approved-run authorization were not exercised by direct SQL assertions; SQL function creation did succeed.
- M001's context setter is an existing `SECURITY DEFINER` function using `public` in its search path and does not validate role membership/scope. M008 ledger policies also use its unvalidated tenant GUC. M012 does not weaken or silently replace either owner; hardening requires an explicitly owned follow-up migration and a connected identity/scope model. Custom GUCs are forgeable by anyone with direct access to the trusted app credential. The service must authenticate callers and explicitly require context **before** each read: an RLS predicate may not be evaluated on an empty table.
- App role has status-column UPDATE grants on assembly/units so the QC trigger can operate; because the pool credential is trusted, direct SQL holders can misuse these grants. Upgrade with dedicated QC routines/privileges and actor memberships when upstream modules arrive. Other business gates (meal, bonus split, remainder, cross-client payroll authorization) remain phase 4+/unresolved and are not implied by an approved borongan rule alone. The ledger account-currency guard belongs in a future additive M008-owner migration, not M012.
- SQL money uses integer minor units and CHECKs; the on-conflict uniqueness is enforced in PostgreSQL, but the inline direct tests do not replace retained regression tests. The existing payroll Python suite is the only retained runnable check in this change; pgTAP fixtures are the upgrade path when extension/test location is available.