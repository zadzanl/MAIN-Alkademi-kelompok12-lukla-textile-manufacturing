# Tasks: Payroll Engine Runtime Implementation

Every task starts unchecked; a task is only marked complete after its verification step has actually been executed and its output recorded, and after its branch has merged, because root artifacts are integrated after workstream review.

## 0. Branch Chain and Merge Order

The work is delivered as a linear stack. Each branch adds exactly one commit over its parent, and each is green at its own tip (`ruff check`, `ruff format --check`, `mypy src/ --strict`, `pytest`, and `python scripts/check_workspace_hygiene.py`).

| Order | Branch | Pull request base | Delivers |
| --- | --- | --- | --- |
| 1 | `chore/hygiene-allow-backend` | `master` | Tasks 1.1–1.4: `backend/` allowed in the hygiene allow-list, module scaffold, blocking CI job |
| 2 | `feat/payroll-rule-registry` | `chore/hygiene-allow-backend` | Contract schemas, the financial rule gate, propose and approve |
| 3 | `feat/payroll-period-lifecycle` | `feat/payroll-rule-registry` | Period schemas and the status transition guard |
| 4 | `feat/payroll-wage-calculation` | `feat/payroll-period-lifecycle` | Quality-passed-only borongan aggregation behind the gate |
| 5 | `feat/payroll-bonus-pool` | `feat/payroll-wage-calculation` | Bonus pool consolidation and the refused three-way split |

Set each pull request's base to the branch above it, not to `master`. GitHub retargets the remaining pull requests automatically as each one merges, so no rebase is needed; merging out of order is what makes a diff carry another branch's commit.

Still open after this chain: persistence and migrations (phase 3), the HTTP layer and the remaining operations of phase 4, the jobs of phase 5, the harness of phase 6, View 06 of phase 7, and the escalations of phase 8.

## 1. Scaffold and CI Gate

Implemented on branch `chore/hygiene-allow-backend`; tick these boxes once that branch merges, since root artifacts are integrated after workstream review.

- [x] 1.1 Extend `scripts/check_workspace_hygiene.py` `ALLOWED_ROOT_DIRS` with `backend` and document the reason inline.
- [x] 1.2 Create `backend/payroll-costing/` with `README.md`, `API_CONTRACTS.md`, and the `src/{models,services,utils,api}` layout named in `docs/MODULES_ARCHITECTURE.md`.
- [x] 1.3 Add a payroll CI job (ruff check, ruff format --check, mypy --strict) scoped to `backend/payroll-costing/**` in `.github/workflows/ci.yml` as a blocking job. pytest joined this job on `feat/payroll-rule-registry`, where the first tests landed.
- [x] 1.4 Verify: `python scripts/check_workspace_hygiene.py` exits 0 with the module present, and the new CI job fails on a deliberately broken lint input, then passes once reverted.

## 2. Recorded Design Decisions Before DDL

- [x] 2.1 Confirm Decision 2 (`payroll_periods` container plus versioned `payroll_runs`) against `11-database-schema-spec.md` §4 and §8, and note the resolution in the module `README.md`.
- [x] 2.2 Confirm Decision 3 (`overhead_events` cost log plus `overhead_periods` allocation snapshot) and record it in the module `README.md`.
- [x] 2.3 Confirm Decision 4 (module location and allow-list amendment) with the maintainers, since it changes a shared CI gate.
- [x] 2.4 Verify: both decisions are written down with their alternatives, and no migration is authored before this step is done.

## 3. Database Migrations and Invariants

- [x] 3.1 Author M006: `rate_cards` exclusion constraint plus `piece_rate_snapshots` and `garment_units` with the one-snapshot-per-unit rule.
- [x] 3.2 Author M007: `garment_assemblies`, `assembly_components`, `qc_inspections`, and `qc_defects`.
- [x] 3.3 Author M008: `ledger_accounts`, `ledger_transactions`, `ledger_entries` with the no-UPDATE/no-DELETE trigger, same-`created_xid` rule, and deferred balanced-transaction check.
- [x] 3.4 Author M009: `financial_rule_versions`, `eligibility_events`, `payroll_periods`, `payroll_runs`, `payroll_run_credits`, `payroll_items`, `payroll_payments`, `wage_credits`, `payroll_adjustments`, `qc_bonus_accruals`, `overhead_events`, and `overhead_periods`.
- [x] 3.5 Author M011: `job_runs` and `idempotency_records` with the `(tenant_id, key, operation_id)` unique constraint.
- [x] 3.6 Author M012: `set_request_context`, `calculate_weekly_payroll`, `calculate_overhead_allocation`, grants, and `ENABLE`/`FORCE ROW LEVEL SECURITY` policies for every tenant-scoped payroll table.
- [ ] 3.7 Verify with pgTAP: ledger UPDATE/DELETE rejected with `LEDGER_IMMUTABLE`; a second `wage_credits` row for the same `garment_unit_id` rejected; a second `qc_bonus_accruals` row for the same `assembly_id` rejected; the same read under the non-owner role returns zero rows without tenant context.

## 4. Contract Operations (Employee-Facing)

- [ ] 4.1 Implement `createPayrollPeriod` and `listPayrollPeriods` with the `PeriodRequest` validation rules (`Asia/Jakarta`, `cutoffLocal` pattern, inclusive start and exclusive end).
- [ ] 4.2 Implement `calculateWeeklyPayroll` returning `PayrollResult{status ∈ CALCULATED | NO_OUTPUT | PENDING_RULE}` and `409 FINANCIAL_RULE_PENDING` when a referenced rule version is not `APPROVED`, writing no monetary rows on the gated path.
- [ ] 4.3 Implement `getPayrollStatement` with `version`, `inputHash`, per-recipient `base`/`meal`/`bonus`, and `reserve` held at zero while OQ-4 is unresolved.
- [ ] 4.4 Implement `getBonusPool` with exactly three `BonusRecipient` entries and the same rule gate.
- [ ] 4.5 Implement `approvePayroll` pinning `PayrollApproval{version, inputHash}` to the calculated run, and `recordPayrollPayment` accepting `PaymentEvidence{externalReference, evidenceFileId}` against an approved run only.
- [ ] 4.6 Implement `recordOverhead` and `calculateOverhead`, with `NO_OUTPUT` for a zero-production month and the gate on the allocation path.
- [ ] 4.7 Implement `listFinancialRules`, `proposeFinancialRule`, and `approveFinancialRule` (`Owner` only, `FinancialRuleApproval.evidenceFileId` required, proposal alone never sufficient).
- [ ] 4.8 Implement the shared `Problem` model for all fourteen error codes, the `Idempotency-Key` middleware over `(tenant, operationId, key)` with `409 IDEMPOTENCY_CONFLICT` on a changed payload, and role enforcement matching each operation's `x-roles`.
- [ ] 4.9 Verify: Schemathesis run against `contracts/openapi.yaml` for the payroll/finance paths, plus a request asserting the gated `409` body and one asserting `IDEMPOTENCY_CONFLICT`.

## 5. Service-Authenticated Jobs

- [ ] 5.1 Implement `runSaturdayPayrollJob` and `runMonthlyOverheadJob` behind `serviceAuth` bearer `service-token` with `x-roles` `ServicePayrollJob` / `ServiceOverheadJob`.
- [ ] 5.2 Implement `getJob` readback for `Owner` and `FinancePayroll`.
- [ ] 5.3 Record `job_runs` with `RUNNING | SUCCEEDED | BLOCKED | FAILED` and a single row per `(kind, period)`.
- [ ] 5.4 Verify: delivering the same job twice with one `Idempotency-Key` produces one run; an employee JWT on a job endpoint is refused; a `PENDING` rule leaves the job `BLOCKED`, not `SUCCEEDED`.

## 6. Verification Evidence

- [ ] 6.1 Wire the harness commands for this module and the evidence collector output (`results.json`, `results.xml`, `api-results.xml`, `db-results.xml`, `system-results.json`, `manifest.json`).
- [ ] 6.2 Map and run `API-AT-03` / `DB-AT-03` (seven sewers, Rp 2,000 per verified unit, 30 units, Rp 60,000, borongan only), `API-AT-06` / `DB-AT-06` (3,000 pass units at Rp 7 = Rp 21,000, three equal shares of Rp 7,000), and `API-AT-07` / `DB-AT-07` (two pass and one repair at Rp 6 yields Rp 12, unchanged on recalculation).
- [ ] 6.3 Run `DB-AT-04` / `DB-AT-05` (unverified tally and `MENUNGGU_QC` unit earn nothing; a repaired unit earns at most one credit) and `DB-ATR04`..`DB-ATR07` (mandor cannot change the payroll formula, penjahit cannot edit verified output, QC cannot change the borongan rate, Finance cannot change physical stock).
- [ ] 6.4 Report `API-AT-08` as `BLOCKED` while the remainder policy is unresolved, and assert that no floor payout, reserve account, fourth recipient, or hidden-loss rule is produced.
- [ ] 6.5 Verify: the collector exits 0 on a passing bundle, exits non-zero on a `FAIL` or a missing required file, and the negative control that removes one requirement ID exits 1.

## 7. View 06 Integration

- [ ] 7.1 Implement the payroll surface of `VIEW-06` (period list, calculation trigger, blocked state, statement, approval, payment, rule approval) against the contract hooks, not raw `fetch`.
- [ ] 7.2 Render `FINANCIAL_RULE_PENDING` as a blocking state, never as zero or success.
- [ ] 7.3 Verify: Playwright run showing the blocked state on a `PENDING` rule and the approved path once the rule version is approved.

## 8. Escalations (Not Implementable in This Change)

- [ ] 8.1 Escalate the `FinancialRuleFields` gap for OQ-2 (meal bearer), OQ-3 (recipient policy), OQ-5 (uninspected output), and OQ-6 (approver role, payment method) through the Phase A review reopen rule.
- [ ] 8.2 Escalate that `bonusRecipientIds` is pinned to exactly three while OQ-3 asks whether recipients are configurable, and that `remainderPolicy: RESERVE_PROPOSED` conflicts with BRD §13.2.
- [ ] 8.3 Escalate that `approvePayroll` is restricted to `FinancePayroll` while OQ-6 proposes an `Owner` final approver.
- [ ] 8.4 Resolve the workstream ownership inconsistency between `09-technical-blueprint-completion-plan.md` (Dev 3 payroll) and `18-parallelization-and-workstreams.md` (Dev 4 payroll) before two developers touch `payroll_items` / `wage_credits`.
