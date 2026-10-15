# Implementation report — financial-rule repository, revision 2

## Context and boundary

- Confirmed `revision-task-record.md`: Revision 1 baseline restored on `feat/payroll-engine-implementation`, with restored and user-modified files preserved.
- Confirmed `impl-periods-revision2.md`: Package A was narrowly approved and the period repository already uses the caller-owned Session, checked reader, tenant-context verification, page size 1000, and no transaction ownership.
- No reviewer was dispatched, per the user instruction. No further reviewer may be dispatched for this slice.
- No stash, reset, clean, commit, branch switch, dependency installation, migration edit, or fixture rewrite was performed.
- `prototypes/s001-probe/probe_fixture.sql` was not modified. Observed SHA-256 after implementation: `1B108B45868AA1A5F6B31F2518A91A876D80B5664D099059CDFCCC3577902B8D`.

## Changed files

- `backend/payroll-costing/src/repositories/rules.py`
  - Added `list_financial_rules(db, tenant_id)`.
  - Added `get_required_versions(db, tenant_id, rule_names, on_date)`.
  - Added `approve_financial_rule(db, tenant_id, actor_id, role, rule_id, approval)`.
  - Uses only the allowlisted `payroll_read_rows` function for rule reads, with bound parameters and page size 1000.
  - Validates checked JSON rows into the existing `FinancialRule` Pydantic model and verifies the stored effective date matches the contract-shaped parameters.
  - Resolves names and effective dates in Python because the existing checked reader only supports tenant-scoped UUID paging. Missing or pending matches fail closed through `FinancialRulePending`; multiple approved matches fail closed.
  - Verifies the supplied tenant, role, and actor match the transaction-local payroll context.
  - Calls existing `payroll_approve_rule(uuid, uuid)` and checked-reads the result through the same Session.
  - Does not commit, rollback, open another Session, issue raw payroll table SELECT, or persist approval reference/note fields that have no current schema columns.
- `backend/payroll-costing/tests/test_rules_repository.py`
  - Added URL-free unit coverage for Pydantic row mapping, invalid rows, empty results, 1001-row paging, page size, tenant mismatch, effective-date filtering, missing/pending fail-closed resolution, duplicate approved matches, Owner-role validation, context identity checks, approval call order, and transaction neutrality.
- `openspec/changes/lukla-payroll-engine/artifacts/impl-rules-revision2.md`
  - This report.

`backend/payroll-costing/src/repositories/__init__.py` was not changed because the existing package initializer already exposes the repository package and no export was required by the requested slice.

## Explicitly not implemented

- `propose_financial_rule` was not implemented. `FinancialRuleRequest` has no authoritative `rule_name` or version namespace, so adding a public field, generated name, private JSON key, or convention would invent proposal naming.
- No migration was modified.
- No new public model fields, schema columns, evidence-existence lookup, HTTP route, idempotency wrapper, runtime orchestration, payment path, job path, or phase-4/5 behavior was added.
- Approval accepts and validates the existing `FinancialRuleApproval` model and passes its evidence UUID to the existing routine. It does not claim that the UUID points to an existing upstream file because that file table is absent from the current schema. Optional approval reference/note values are validated but are not claimed as persisted.

## Exact verification commands and observed output

All commands ran from `C:\Projects\hackathon-MAIN-alkademi` using explicit Python 3.11:

1. Focused tests:

```text
& C:/Users/lenovo/AppData/Local/Programs/Python/Python311/python.exe -m pytest -q tests/test_rules_repository.py tests/test_financial_rules_service.py
12 passed in 0.83s
exit 0
```

2. Full payroll-costing suite:

```text
& C:/Users/lenovo/AppData/Local/Programs/Python/Python311/python.exe -m pytest -q
131 passed in 1.73s
exit 0
```

3. Cached Ruff:

```text
ruff check src/repositories/rules.py tests/test_rules_repository.py
All checks passed!
exit 0

ruff format --check src/repositories/rules.py tests/test_rules_repository.py
2 files already formatted
exit 0
```

4. Python compilation:

```text
python -m compileall -q backend/payroll-costing/src/repositories backend/payroll-costing/tests/test_rules_repository.py
compile_exit=0
```

5. Workspace hygiene and whitespace:

```text
python scripts/check_workspace_hygiene.py
Workspace hygiene check passed; root and sandbox isolation confirmed.
hygiene_exit=0

git diff --check
diff_check_exit=0
```

6. Fresh disposable migration/catalog check:

- Created unique database `payroll_rules_revision_a290e6cdceda43aab1fffbe4c8d6187b`.
- Applied, with `ON_ERROR_STOP=1 -1`, the unchanged chain `001_identities.sql`, `006_payroll_rate_cards.sql`, `007_payroll_qc_inputs.sql`, `008_double_entry_ledger.sql`, `009_payroll_core.sql`, `011_job_idempotency.sql`, and `012_payroll_routines_rls.sql`.
- PostgreSQL server version: `18.6`.
- `lukla_app` execute privilege on `payroll_read_rows(text,uuid,uuid,integer)`: `t`.
- `lukla_app` execute privilege on `payroll_approve_rule(uuid,uuid)`: `t`.
- `lukla_app` execute privilege on `payroll_transition_period(uuid,text,text)`: `t`.
- `migration_exit=0`.
- Dropped exactly the generated database: `drop_exit=0`.
- Migration emitted expected `NOTICE` messages for skipped non-existing policies/triggers; no migration error occurred.

## Acceptance assessment

- Checked reads, bound parameters, page size <=1000, model validation, tenant context verification, and transaction neutrality are implemented and unit-tested.
- Existing Owner-only pure service behavior is preserved through `assert_may_approve`.
- Approval is wired only to the existing UUID routine and checked read; no evidence existence is invented.
- Required-version resolution does not silently discard unresolved names. It returns approved references, returns pending references for present but unapproved rules, and raises `FinancialRulePending` for absent or out-of-window rules.
- Revision 1 context and the Package A/period slice remain intact. The probe fixture hash is unchanged.

## Limitations and not-run gates

- No restricted-role live CRUD/approval integration test was added in this exact slice. The fresh migration check proves the existing routine/read function definitions and grants, not end-to-end repository behavior under app-role data.
- No concurrency proof was run for approval or pagination.
- Strict mypy was not run because the previously recorded environment has no runnable mypy installation; no installation was attempted.
- pgTAP is unavailable in the inspected PostgreSQL installation and was not installed.
- No independent reviewer was dispatched, as explicitly prohibited by the user.
- Browser verification is not applicable to this backend-only repository slice.
- These results do not claim Phase 3 completion, Phase 1/2 completion, full project completion, or production readiness.
