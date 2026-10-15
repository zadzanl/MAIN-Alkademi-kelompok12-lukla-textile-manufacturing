# Phase 3 timeout exploration

Date: 2026-10-15  
Repository: `C:\Projects\hackathon-MAIN-alkademi`  
Scope: read-only repository inspection after the timed-out phase-3 attempt. No source files or migrations were edited by this exploration. No database execution was performed.

## Task-record revision

`openspec/changes/lukla-payroll-engine/tasks.md` currently records phase 3 as incomplete:

- `tasks.md:37-45`: 3.1 through 3.7 are all `[ ]`.
- The same file records 1.1–1.4 and 2.1–2.4 as `[x]`.
- Phase 3 still requires M006, M007, M008, M009, M011, M012, and pgTAP verification.

This matches the requested workflow: implement the payroll backend, then perform one review after phase 3. The task record does not support treating individual migration phases as reviewed or complete.

## Commands and output evidence

Read-only commands used:

```text
git status --short
 M backend/payroll-costing/README.md
 M openspec/changes/lukla-payroll-engine/tasks.md
 M scripts/check_workspace_hygiene.py
?? backend/migrations/006_payroll_rate_cards.sql
?? backend/migrations/007_payroll_qc_inputs.sql
?? backend/migrations/009_payroll_core.sql
?? backend/migrations/011_job_idempotency.sql
?? backend/migrations/012_payroll_routines_rls.sql
?? openspec/changes/lukla-payroll-engine/artifacts/
```

```text
Get-ChildItem backend/migrations -Filter *.sql
001_identities.sql
006_payroll_rate_cards.sql
007_payroll_qc_inputs.sql
008_double_entry_ledger.sql
009_payroll_core.sql
011_job_idempotency.sql
012_payroll_routines_rls.sql
```

Untracked migration sizes:

```text
006_payroll_rate_cards.sql       92 lines   4589 bytes
007_payroll_qc_inputs.sql       108 lines   5212 bytes
009_payroll_core.sql            218 lines  10711 bytes
011_job_idempotency.sql          16 lines    802 bytes
012_payroll_routines_rls.sql    367 lines  20649 bytes
```

`psql`, `pg_isready`, and `sqlfluff` were not available from `Get-Command`. No SQL parser, migration runner, PostgreSQL server, or pgTAP suite was run. The findings below are static inspection findings, not database-execution results.

## Untracked migration assessment

The five files are substantial drafts, not empty placeholders, but they are not phase-complete deliverables. Their apparent state is **partial and unverified**:

- M006 defines `rate_cards`, `piece_rate_snapshots`, `sewing_tallies`, and `garment_units`, including the rate-card exclusion constraint and a snapshot/unit relationship. It also creates a circular relationship by adding the snapshot-to-unit FK after `garment_units`.
- M007 defines assemblies, components, QC inspections, and defects with several triggers.
- M009 defines the requested payroll/rule/overhead tables and several uniqueness/FK constraints.
- M011 defines only `job_runs`; its own first comment says M001 owns `idempotency_records`.
- M012 defines context/routine/guard functions, payroll RLS/grants, and an additional ledger-entry trigger.

They are therefore more than a partial stub, but cannot be called complete: phase-3 task checkboxes remain unchecked and 3.7 has no recorded pgTAP evidence.

## Ownership conflicts

### M001 (`001_identities.sql`)

- M001 already creates `idempotency_records` and the unique constraint `(tenant_id, operation_id, key)` at `001_identities.sql:38-51`.
- M011 does not create that table and explicitly says M001 owns it at `011_job_idempotency.sql:1`. This avoids a literal duplicate table, but leaves task 3.5 unresolved: the requested M011 deliverable and the actual ownership split do not match. A replacement must record one authoritative owner rather than copy the table.
- M001 creates `set_request_context` at `001_identities.sql:71-96` and grants it at `:125`. M012 uses `CREATE OR REPLACE FUNCTION` for the same signature at `012_payroll_routines_rls.sql:4-32`, then changes its validation behavior and grants at `:33-34`. This is duplicate ownership of a shared function and creates migration-order/review risk. Consolidate the function under one owner or make the later hardening an explicit forward migration with a recorded contract.
- M001 owns RLS/policy/grants for `idempotency_records` and `audit_events` at `001_identities.sql:99-125`. M012's dynamic payroll-table RLS list excludes those tables. That is acceptable only if the ownership boundary is explicit; it does not satisfy a reading of phase 3.6 that expects M012 to own every listed tenant-scoped payroll/security object.

### M008 (`008_double_entry_ledger.sql`)

- M008 owns `ledger_accounts`, `ledger_transactions`, `ledger_entries`, their immutability/late-line/balance triggers, RLS, and grants at `008_double_entry_ledger.sql:4-309`.
- M012 adds `ledger_entry_currency_guard` and attaches it to the M008-owned `ledger_entries` table at `012_payroll_routines_rls.sql:356-366`. This is an ownership overlap, not a duplicate table. Move the guard into M008, or document a deliberate extension migration and its ordering/rollback contract.
- M008 already creates `set_request_context`-dependent RLS policies using `app.tenant_id`; M012 replaces the context function while also adding stricter payroll-context behavior. The combined behavior needs one owner and an integration test; it was not tested here.

Additional boundary concern: M006 says upstream order/tally data is not yet migrated, but creates `sewing_tallies` at `006_payroll_rate_cards.sql:42-59`. The replacement must either establish M006 as the owner or remove this duplicate/upstream-owned table and reference the actual owner.

## Static SQL gaps by migration

### 006

- `piece_rate_snapshots.source_unit_id` is nullable at `006_payroll_rate_cards.sql:34`, so `UNIQUE (tenant_id, source_unit_id)` does not enforce one snapshot per unit for rows with NULL. The requested one-snapshot-per-unit invariant is therefore incomplete.
- M006 creates `sewing_tallies` although its header says source tallies are upstream-owned. Ownership must be resolved before implementation continues.
- `rate_cards`, `piece_rate_snapshots`, `sewing_tallies`, and `garment_units` use `CREATE TABLE` without `IF NOT EXISTS`; retrying a partially applied migration is not safely idempotent.
- The snapshot/unit mutual FK is ordered through an `ALTER TABLE` at `:83-84`, which is structurally plausible, but it must be validated on the supported PostgreSQL version and paired with a clear insert/update lifecycle.

### 007

- The QC trigger at `007_payroll_qc_inputs.sql:66-87` locks the assembly and advances its status, which is a useful ordering guard, but there is no explicit trigger preventing component mutation after an assembly reaches a terminal QC state. The intended immutability boundary is not complete from static inspection.
- `qc_defects` validates an inspection/component composite FK, but there is no explicit check that the defect's component belongs to the same inspection's assembly beyond the composite FK shape; this should be covered by a negative test.
- The trigger/function names and tables are created without `IF NOT EXISTS`/conditional replacement. A timeout after partial application will not be safely retryable.
- M007 depends on M006's `payroll_snapshot_immutable()` at `:88` and on actors/garment units. The migration chain and owner boundaries must be explicit.

### 009

- The requested unique invariants are present statically: one original `wage_credits` row per `(tenant_id, garment_unit_id)` (`009_payroll_core.sql:95-97`) and one `qc_bonus_accruals` row per assembly (`:166-177`). They remain unverified because 3.7 was not run.
- `payroll_run_credits` has both `tenant_id` and `source_tenant_id`; the composite FK at `:113` is sensible, but cross-tenant semantics and RLS need a negative test.
- `overhead_events.period_id` is nullable (`:202`), so events can exist without a linked allocation snapshot. This may be intentional for source events, but the ownership/lifecycle rule is not stated in the migration.
- Several monetary/history tables have mutable `updated_at` columns or no local immutability trigger; M012 later attempts to add append-only triggers. This cross-file ordering is fragile and should be made explicit.
- `CREATE TABLE`/index statements are generally non-idempotent, so retry behavior after a timeout is unknown.

### 011

- M011 creates `job_runs` only (`011_job_idempotency.sql:2-16`), while task 3.5 names both `job_runs` and `idempotency_records`. It relies on M001 for the latter but does not document a task-record reconciliation.
- `job_runs.period_id` has no FK to `payroll_periods` (`:6`), so a job can reference a nonexistent or cross-domain period at the database level.
- The unique key `(tenant_id, kind, period_id)` exists (`:14`), and `BLOCKED` requires an `error_code` (`:15`), but no trigger/check ties job kind to the permitted period/job routine.
- `CREATE TABLE` is not retry-safe.

### 012

- `calculate_weekly_payroll` at `012_payroll_routines_rls.sql:241-282` contains an apparent PostgreSQL query error: its `INSERT ... SELECT` selects ordinary columns plus `string_agg(...)` without a `GROUP BY`. This is a static syntax/semantic finding; it was not executed.
- The same routine appears to create a calculated run even when no wage credits exist, because the aggregate can still produce one row. The required `NO_OUTPUT` behavior is not represented by the shown return type (`uuid`) and needs alignment with the contract.
- `calculate_overhead_allocation` counts `eligibility_events` rather than clearly counting distinct finished/eligible production units (`:307-309`); this could overcount assemblies with the intended production model and needs a source-of-truth decision/test.
- The dynamic RLS loop at `:337-346` creates policies named `payroll_tenant` without dropping/replacing them. A rerun after a timeout will fail if any policy was already created.
- The dynamic RLS list includes `sewing_tallies` and all payroll/QC tables, but omits `idempotency_records` and `audit_events`, which are M001-owned. This is an ownership boundary gap, not proof that those tables lack RLS.
- M012's `DROP TRIGGER payroll_run_credits_immutable ON payroll_run_credits` at `:200` has no `IF EXISTS`; it assumes the earlier dynamic trigger loop completed. A partial failed run can make retry behavior fail.
- M012 adds a trigger to the M008-owned ledger table (`:356-366`) and redefines the M001-owned context function (`:4-34`), as described above.
- `set_request_context` allows a tenant-only context under a legacy sentinel path (`:12-15`) while payroll RLS requires actor/role. That dual mode needs a documented security rationale and tests for missing/invalid context; no such tests were run.
- The routine and policy functions use `SECURITY DEFINER`/`search_path` in places, but the complete privilege model and definer ownership were not verified against a live PostgreSQL instance.

## Implementation report status

An implementation artifact exists: `openspec/changes/lukla-payroll-engine/artifacts/impl-phase12-001.md`. Its title and content identify it as Phase 1–2 evidence; it explicitly says no migration was authored and no database checks were run for that phase. `technical-plan-001.md` also exists, but is a planning artifact. No separate Phase 3 implementation report, migration verification report, or pgTAP result artifact was found.

## Unknowns

- Whether any migration was applied to a database before the timeout; no database connection or execution was attempted.
- Whether the five untracked SQL files are intended to be kept as a draft, discarded, or rewritten; Git history does not establish approval.
- The authoritative owner of `sewing_tallies` and the intended M011 owner of `idempotency_records`.
- Whether `NO_OUTPUT` belongs in the SQL routine return contract or only in the application service.
- Supported PostgreSQL version, migration runner semantics, and whether transaction-wrapped DDL/extension creation is guaranteed.
- Whether upstream migrations for orders, actors, units, files, and production/QC facts will supply the referenced tables/columns exactly as assumed.
- No positive claim is made about SQL validity, migration application, RLS behavior, or invariant enforcement because none was executed.

## Recommended recovery scope for a replacement implementation assistant

1. Treat all five untracked SQL files as an unapproved, partial draft. Do not mark 3.1–3.7 complete and do not review individual migration phases separately.
2. Re-read `design.md`, `tasks.md`, the database schema specification, and the existing M001/M008 migrations. Produce a single ownership/dependency matrix before editing: M001 identities/idempotency/context, M008 ledger, upstream production/QC facts, and payroll-owned tables.
3. Decide and record the ownership resolution for `set_request_context`, `idempotency_records`, `sewing_tallies`, and the M008 ledger currency guard. Remove duplicate ownership rather than layering conflicting replacements.
4. Rewrite or safely repair M006, M007, M009, M011, and M012 as one ordered phase-3 implementation. Preserve the approved constraints: snapshot/unit uniqueness, QC and wage/accrual uniqueness, immutable ledger/no late lines/balanced deferred transactions, pending-rule fail-closed behavior, job idempotency, grants, and FORCE RLS.
5. Fix the apparent M012 aggregate query defect and explicitly define zero-output behavior before implementation. Validate all FK ordering, composite-key references, trigger dependencies, policy names, rerun behavior, and transaction boundaries.
6. Add the phase-3 pgTAP coverage required by `tasks.md:45`, including ledger UPDATE/DELETE rejection, duplicate wage credit rejection, duplicate QC bonus rejection, and cross-tenant/no-context zero-row reads. Add negative tests for ownership, pending rules, late inserts, reruns, and cross-tenant composite references where needed.
7. Run the supported migration runner and pgTAP against the repository-supported PostgreSQL version. Record exact commands, database version, commit, and outputs. Do not claim completion from static inspection.
8. Perform exactly one consolidated review after all phase-3 implementation and verification work is complete. Only then update the phase-3 task checkboxes with the recorded evidence; do not perform or record per-migration phase reviews.
9. Keep phase 4+ HTTP/jobs/frontend work out of this recovery unless separately requested. The requested replacement scope is phase-3 persistence/invariants plus the one post-phase-3 review.
