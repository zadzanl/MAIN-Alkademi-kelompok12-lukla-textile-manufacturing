# Phase 3 read/write boundary — 2026-10-15

Branch: `feat/payroll-engine-implementation`. Changed source: `backend/migrations/012_payroll_routines_rls.sql` only. M001/M008 and phase 4+ remain untouched. Task 3.7 is unchecked; no pgTAP or independent security review was run.

## Decision and limits

- M012 revokes direct `SELECT` on its 21 payroll/QC/job tables from `lukla_app`. Phase-4 SQL must call `payroll_read_rows(table_name, id, after_id, limit)` instead. The routine validates `payroll_context_tenant()` **before** querying, allowlists table names, binds the tenant and UUID filters, orders by UUID, and limits a page to 1–1000 JSON rows. A UUID cursor is not a chronological list; phase 4 may add typed, filtered readers. A missing context on an empty direct table fails with permission denied, not a silent empty result.
- M012 revokes direct `INSERT` into `payroll_runs` and `payroll_run_credits`. The only exposed insert path for these tables is `calculate_weekly_payroll` as a restricted `SECURITY DEFINER` function. `payroll_advance_run` performs only APPROVED/PAID updates through existing validation triggers; `payroll_approve_rule` preserves Owner rule approval after removing direct SELECT. Payment inserts remain guarded by their existing trigger. Existing QC and approval triggers that read protected tables execute as the migration owner with a fixed search path. Policy `TO PUBLIC` applies the tenant predicate also to a non-bypassing owner; all 21 tables retain ENABLE/FORCE RLS. The checked reader also filters on tenant explicitly, including if the migration owner is a superuser.
- `public` is in inherited function search paths. M012 revokes `CREATE ON SCHEMA public` from `PUBLIC` and `lukla_app` and puts `pg_temp` last for the new owner-executed functions/triggers. The deployment must not grant `CREATE` on `public` to untrusted inherited roles. M001's setter still accepts forgeable request GUCs and does not establish actor membership; a trusted app credential and phase-4 authentication are required. M001 identity/idempotency and M008 ledger tables still have their **separate** direct SELECT grants and policies; this change does not claim to fix missing-context reads there or silently change their owners. Context-less direct UPDATE of an empty table may still affect zero rows; the checked read guarantee is a SELECT boundary, not universal statement-level enforcement.

Reference checked before adapting existing conventions: PostgreSQL 18 [RLS](https://www.postgresql.org/docs/18/ddl-rowsecurity.html) (per-row predicate, FORCE and superuser exceptions), [CREATE FUNCTION](https://www.postgresql.org/docs/18/sql-createfunction.html) (definer privileges, secure `search_path`, revoke PUBLIC EXECUTE), [function security](https://www.postgresql.org/docs/18/perm-functions.html).

## Disposable PostgreSQL evidence

Windows PowerShell, Python `psycopg`, `DATABASE_URL` from the environment (never printed). `DATABASE_URL.replace('postgresql+psycopg://','postgresql://')` converts the configured SQLAlchemy scheme for libpq. The first attempted `psycopg.connect(os.environ['DATABASE_URL'])` failed with `ProgrammingError: missing "=" after "postgresql+psycopg://..."` before creating a DB; retried with the conversion. Every successful probe used `CREATE DATABASE payroll_<random>` and `DROP DATABASE payroll_<random> WITH (FORCE)` in `finally`. Migration application command inside each Python fixture:

```python
for file in sorted(Path('backend/migrations').glob('*.sql')):
    with db.transaction():
        db.execute(file.read_text(encoding='utf-8'))
```

Output: `VERSION 18.6`; `APPLIED 001_identities.sql`, `006_payroll_rate_cards.sql`, `007_payroll_qc_inputs.sql`, `008_double_entry_ledger.sql`, `009_payroll_core.sql`, `011_job_idempotency.sql`, `012_payroll_routines_rls.sql`; `DISPOSABLE REMOVED`. The following SQL was executed from inline PowerShell `@' ... '@ | python -`, using `db.execute(sql, parameters)`; negative probes used a nested `with db.transaction()` savepoint to catch expected errors. All app probes used `SET LOCAL ROLE lukla_app`; valid-context probes also called `SELECT set_request_context(tenant_uuid, actor_uuid, 'Owner')`, except QC PASS used `QCInspector`.

| Exact SQL / fixture operation | Observed output |
| --- | --- |
| Empty database, no context: `SELECT count(*) FROM payroll_periods` | `42501 permission denied for table payroll_periods` |
| Empty database, no context: `SELECT * FROM payroll_read_rows('payroll_periods')` | `42501 TENANT_CONTEXT_MISSING` |
| No context: `INSERT INTO payroll_runs (...) VALUES (...)` and `INSERT INTO payroll_run_credits(tenant_id,run_id,source_tenant_id,wage_credit_id) VALUES(gen_random_uuid(),gen_random_uuid(),gen_random_uuid(),gen_random_uuid())` | Each `42501 permission denied for table ...` |
| Valid context: `INSERT INTO payroll_runs DEFAULT VALUES`; `INSERT INTO payroll_run_credits DEFAULT VALUES` | Each `42501 permission denied for table ...` before column validation |
| Valid context: `has_table_privilege(current_user, format('public.%I', name), 'SELECT')` for each of the 21 M012 allowlisted tables | `DIRECT_READ_PRIVILEGES 0` |
| Fixture: two tenants, actor, rate card/snapshot, verified tally, unit, assembly/component, PENDING rule, October period; as app QCInspector `INSERT INTO qc_inspections(... disposition, sequence_no, idempotency_key) VALUES(..., 'PASS', 1, 'qc-1')` | `QC PASS`; eligibility event and unit status allowed the subsequent calculation |
| As app Owner: `SELECT calculate_weekly_payroll(period_uuid,'r')` against PENDING rule | `23514 FINANCIAL_RULE_PENDING`; owner counts `SELECT (SELECT count(*) FROM payroll_runs),(SELECT count(*) FROM wage_credits)` returned `(0, 0)` |
| As app Owner: `SELECT payroll_approve_rule(rule_uuid,evidence_uuid)`; then `SELECT calculate_weekly_payroll(period_uuid,'r')` | UUID run returned; `SELECT * FROM payroll_read_rows('payroll_run_credits')` returned one link |
| As app Owner: direct `INSERT INTO payroll_runs(tenant_id,period_id,period_start,period_end,timezone,cutoff_local,rule_version_id,status,input_hash,version) VALUES(tenant_uuid,period_uuid,'2026-10-01','2026-11-01','Asia/Jakarta','17:00',rule_uuid,'CALCULATED',real_hash,2)`; `real_hash = hashlib.md5((credit_uuid + ':6:IDR').encode()).digest()` from actual checked credit link | `42501 permission denied for table payroll_runs` even with genuine credit and canonical hash |
| Switch checked read to second tenant: `SELECT * FROM payroll_read_rows('payroll_periods')` | `OTHER READ []`; no first-tenant period disclosed |
| Under first tenant context: `SELECT * FROM payroll_read_rows('payroll_periods')` | `OWN PERIODS 1 True` (one row, its `tenant_id` equals the first tenant); same fixture returned `OTHER READ []` after switching tenant |
| As app Owner: `SELECT payroll_advance_run(run_uuid,'APPROVED')`; `INSERT INTO payroll_payments(tenant_id,run_id,external_reference,evidence_file_id,recorded_by) VALUES(tenant_uuid,run_uuid,'bank',evidence_uuid,actor_uuid)`; `SELECT payroll_advance_run(run_uuid,'PAID')` | `APPROVED`, `PAID`; owner final `SELECT status FROM payroll_runs WHERE id=run_uuid` returned `PAID` and committed credit count returned `1` |
| As app Owner: `UPDATE payroll_periods SET status='OPEN' WHERE id=period_uuid` after APPROVED and PAID; `SELECT payroll_advance_run(run_uuid,'CALCULATED')` after PAID | Reopen twice `42501 permission denied for table payroll_periods`; invalid run transition `55000 APPROVED_RUN_IMMUTABLE` |

Two earlier fixture iterations failed and were removed: missing Owner/actor GUC on rule approval (`RULE_APPROVAL_FORBIDDEN`) and January period dates before the October QC event (`RUN None`, zero links). The final run corrected both, and the exact-hash fabrication and lifecycle assertions above passed. No data from disposable DBs was retained.

## Shell checks and remaining verification

```text
& 'C:\Program Files\PostgreSQL\18\bin\psql.exe' --version
# psql (PostgreSQL) 18.6
python scripts/check_workspace_hygiene.py
# ✅ [OK] Workspace hygiene check passed. Root and sandbox isolation confirmed.
python -m pytest backend/payroll-costing/tests -q
# 120 passed in 0.42s
git diff --check
# no output; tracked_diff_check_exit=0
git diff --no-index --check -- NUL backend/migrations/012_payroll_routines_rls.sql
# no whitespace diagnostics; untracked_no_index_exit=1 means NUL differs from the file
git diff --no-index --check -- NUL openspec/changes/lukla-payroll-engine/artifacts/impl-phase3-boundary-001.md
# no whitespace diagnostics; artifact_no_index_exit=1 means NUL differs from the file
SELECT count(*) FROM pg_available_extensions WHERE name='pgtap';
# pgtap_available: 0 (via psycopg on configured server); pgTAP NOT RUN
```

`git diff --check` does not inspect the untracked M012 file; the no-index check did. No retained pgTAP regression exists; task 3.7 must remain unchecked. No browser work belongs to phase 3: browser verification not applicable/unverified. This is not an independent security approval or proof of end-user authorization, deployment safety, M001/M008 read behavior, or phase-4 API behavior.