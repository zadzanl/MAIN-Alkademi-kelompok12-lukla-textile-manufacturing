# Payroll Engine Worklog

## 2026-10-16

- Added explicit QC/MES adapter and pure payroll calculation orchestration.
- Added contract models for payroll approval, payment evidence, bonus pool, overhead, and jobs.
- Added checked payroll persistence for statements, bonus reads, overhead records/allocation, approvals, payment evidence, and job status.
- Added shared idempotent runtime wrappers and registered all remaining phase-4/5 operation IDs.
- Service jobs require `Bearer service-token`, an explicit `X-Service-Scope`, tenant UUID, and service actor UUID; employee JWTs are not accepted.
- Jobs persist `RUNNING`, then `SUCCEEDED` or `BLOCKED` for `FINANCIAL_RULE_PENDING`.
- Payment remains fail-closed unless an existing `PAYROLL` ledger transaction is already linked by `source_id`; the current `payroll_payments` schema has no ledger transaction foreign key, so no duplicate accounting entry is fabricated.
- Evidence: `PYTHONPATH=backend;backend/payroll-costing python -m pytest -q -p no:cacheprovider backend/payroll-costing/tests backend/tests/test_payroll_api.py` -> `136 passed`.
- Evidence: compileall and OpenAPI operation-ID uniqueness check passed.
- Unverified: live PostgreSQL/RLS/concurrency checks; the configured PostgreSQL listener timed out during the broader backend suite.
- Unrelated blockers: full backend suite also has existing copilot stock assertion failures and workspace hygiene rejects an unrelated root `package-lock.json`.
