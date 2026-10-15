# Phase 3 blocking-findings remediation — 2026-10-15

Branch: `feat/payroll-engine-implementation`. Scope: M012 only; M001, M008, frozen contracts and phase 4+ untouched. **INCOMPLETE: IR-01 direct reads and IR-03 routine-only provenance remain blocking.** Task 3.7 stays unchecked; pgTAP was not available or run. No independent security review was dispatched.

## Implementation and decision

- IR-01: Both calculation routines now call `payroll_context_tenant()` before their first table read. An empty direct `SELECT` still does not execute a per-row RLS predicate. PostgreSQL 18 documentation states that RLS expressions evaluate per row: https://www.postgresql.org/docs/18/ddl-rowsecurity.html . Testing scalar and initplan variants confirmed none raises on an empty table. A database-wide guarantee requires an explicit read boundary (e.g. a checked data-access function/view layer with direct table reads revoked, with schema/API and grant implications). M001's setter is owned by M001 and was not replaced. Do not present the routine check as a fix for arbitrary direct SQL reads.
- IR-02: M012's `payroll_period_transition` trigger refuses reopening APPROVED/PAID periods and changes after REVERSAL. Moving a period into APPROVED or PAID requires a corresponding run in that state. The after-run transition advances the period along the proven approval/payment path. Direct terminal-state UPDATE privileges were retained but cannot bypass these checks.
- IR-03: Run insertion and approval verify an approved applicable rule, an existing nonempty original wage-credit set, canonical input hash, matching period snapshot, and an exact set of linked credits at approval. Approval commits linked credits; payment still requires an approved run and payment evidence. New wage credits cannot enter an APPROVED/PAID/REVERSED period. A fabricated zero-credit `CALCULATED` run is rejected on INSERT. **Limit:** because the app role retains INSERT on `payroll_runs` and `payroll_run_credits`, an actor with that credential and actual eligible credits can derive the canonical hash, insert a matching run and links, then approve it without invoking `calculate_weekly_payroll`. Contents are validated; invocation provenance is not. Closing that last gap requires a restricted write capability/routine and coordinated RLS grants rather than another forgeable custom GUC. Do not call IR-03 fully closed.

## Disposable PostgreSQL verification

Environment: Windows PowerShell; `C:\Program Files\PostgreSQL\18\bin\psql.exe --version` returned `psql (PostgreSQL) 18.6`; `SHOW server_version` returned `18.6`. `DATABASE_URL` was read from the environment and never printed. All test scripts used installed Python `psycopg` and `CREATE DATABASE payroll_remedy_<random>` / `DROP DATABASE ... WITH (FORCE)` in `finally`. For each script, the migration command was `for p in sorted(Path('backend/migrations').glob('*.sql')): ... c.execute(p.read_text(encoding='utf-8'))` inside a transaction per file. All seven files applied in lexical order (`001`, `006`, `007`, `008`, `009`, `011`, `012`); disposable databases were removed. Non-owner probes used `SET LOCAL ROLE lukla_app` and valid probes used `SELECT set_request_context(tenant_uuid,actor_uuid,'Owner')` inside the same transaction.

Exact SQL probes executed via inline PowerShell `@' ... '@ | python -` (with Python `psycopg` `c.execute(sql, parameters)` and nested transactions to catch expected errors):

| Probe SQL / command | Observed result |
| --- | --- |
| `SELECT count(*) FROM payroll_periods` on empty DB with no context | `[(0,)]` — **FAIL IR-01**, not TENANT_CONTEXT_MISSING |
| `SELECT * FROM payroll_periods` on empty DB with no context (review baseline, unchanged per-row policy) | `[]`; **not rerun after edit** |
| `SELECT calculate_weekly_payroll(gen_random_uuid(),'r')` without context | SQLSTATE `42501`, `TENANT_CONTEXT_MISSING` |
| `UPDATE payroll_periods SET status='OPEN' WHERE id=%s` for PAID then APPROVED fixtures | Both SQLSTATE `55000`, `APPROVED_RUN_IMMUTABLE` |
| `UPDATE payroll_periods SET status='PAID' WHERE id=%s` on APPROVED fixture with no paid run | SQLSTATE `23514`, `RUN_INPUT_INVALID` |
| `INSERT INTO payroll_runs(tenant_id,period_id,period_start,period_end,timezone,cutoff_local,rule_version_id,status,input_hash,version) VALUES (%s,%s,'2026-01-01','2026-01-08','Asia/Jakarta','17:00',%s,'CALCULATED',decode('00','hex'),1)` with approved rule and empty credit table | SQLSTATE `23514`, `RUN_INPUT_INVALID`; no zero-credit approval was possible |
| `SELECT calculate_weekly_payroll(%s,'r')` with pending rule | SQLSTATE `23514`, `FINANCIAL_RULE_PENDING`; assertions confirmed zero `payroll_runs` and zero `wage_credits` |
| `SELECT calculate_weekly_payroll(%s,'r')` with approved rule and verified tally, QC-pass unit, eligible assembly and immutable snapshot | Returned UUID; one run-credit link |
| `UPDATE payroll_runs SET status='APPROVED' WHERE id=%s` on real run | Succeeded; period `APPROVED`, one committed credit |
| `INSERT INTO payroll_payments(tenant_id,run_id,external_reference,evidence_file_id,recorded_by) VALUES (%s,%s,'bank',%s,%s)` then `UPDATE payroll_runs SET status='PAID' WHERE id=%s` | Succeeded; period `PAID`; changing paid run back to `CALCULATED` raised `55000 APPROVED_RUN_IMMUTABLE` |
| `SELECT count(*) FROM payroll_periods` after changing to second tenant context | Zero rows (cross-tenant negative control) |
| duplicate wage INSERT after payment | Rejected `55000 APPROVED_RUN_IMMUTABLE` before unique-index check; separate pre-approval duplicate and bonus/ledger checks **not rerun** |

The first lifecycle fixture failed before its assertions due to a duplicate period-window unique key; it was corrected to use three distinct windows. A later fixture tried `calculate_weekly_payroll(period,'missing')` against a period whose rule name is `r` and got `PERIOD_NOT_CALCULABLE`; this was a wrong-rule fixture, not pending-rule coverage. The corrected pending-rule fixture above raised `FINANCIAL_RULE_PENDING`.

Required shell checks (run from repository root):

```text
python -m pytest backend/payroll-costing/tests -q
# 120 passed in 0.40s; final rerun: 120 passed in 0.28s
python scripts/check_workspace_hygiene.py
# [OK] Workspace hygiene check passed. Root and sandbox isolation confirmed.
git diff --check
# no output, exit 0; untracked M012 is not included in this command
git diff --no-index --check -- NUL backend/migrations/012_payroll_routines_rls.sql
# no whitespace errors; no-index returns exit 1 because the untracked file differs from NUL
```

Post-final-edit lifecycle and negative SQL probes were rerun on disposable PostgreSQL 18.6 and passed as stated above. No pgTAP, bonus duplication, ledger immutability or pre-approval duplicate-wage assertion was run in this remediation. Prior `impl-phase3-001.md` contains older positive probes but is not fresh evidence for this edit. The missing direct-read error and unsealed run-creation permission preclude a complete remediation verdict. The smallest next design choice is a dedicated checked read boundary and a restricted calculator-only run writer, with integration and grant changes explicitly authorized before implementation.
