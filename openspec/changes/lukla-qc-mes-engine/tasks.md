# Tasks: QC & MES Runtime Implementation

Every task starts unchecked; a task is only marked complete after its verification step has actually been executed and its output recorded, and after its branch has merged, because root artifacts are integrated after workstream review. The branch delivered so far is `feat/qc-mes-engine` (base `origin/master`), which carries phases 1, 2, and the domain layer of phases 4 and 5 below.

## 0. Branch Chain and Merge Order

The work is delivered as a linear stack. Each branch adds commits over its parent, and each is green at its own tip (`ruff check`, `ruff format --check`, `mypy src/ --strict`, `pytest`, and `python scripts/check_workspace_hygiene.py`).

| Order | Branch | Pull request base | Delivers |
| --- | --- | --- | --- |
| 1 | `feat/qc-mes-engine` | `master` | Tasks 1.1–1.4, 2.1–2.5, and the contract models plus the classification, routing, and summary services with their tests (task 4.1, 4.8, 4.9 partially) |
| 2 | `feat/qc-mes-migrations` | `feat/qc-mes-engine` | Tasks 3.1, 3.3, 3.4: `M007`, its RLS policies, its append-only triggers, and the database invariant suite |
| 3 | `feat/qc-mes-api` | `feat/qc-mes-migrations` | Tasks 3.2 (once `M009` exists), 4.2–4.7: the FastAPI routers, authentication, tenant context, idempotency reservation, and the taxonomy read |
| 4 | `feat/qc-mes-terminal` | `feat/qc-mes-api` | Tasks 6.1–6.3: `VIEW-05` |

Set each pull request's base to the branch above it, not to `master`. GitHub retargets the remaining pull requests automatically as each one merges, so no rebase is needed; merging out of order is what makes a diff carry another branch's commit.

## 1. Scaffold and CI Gate

- [ ] 1.1 Create `backend/quality-control/` with `README.md`, `API_CONTRACTS.md`, and the `src/{models,services,utils,api}` layout named in `docs/MODULES_ARCHITECTURE.md`.
- [ ] 1.2 Add a `qc-mes-quality` CI job (ruff check, ruff format --check, mypy --strict, pytest) scoped to `backend/quality-control/**` in `.github/workflows/ci.yml` as a blocking job, mirroring `payroll-engine-quality`.
- [ ] 1.3 Confirm `backend` is already in `scripts/check_workspace_hygiene.py` `ALLOWED_ROOT_DIRS`; add no allow-list change in this branch.
- [ ] 1.4 Verify: `python scripts/check_workspace_hygiene.py` exits 0 with the module present, and the new CI job fails on a deliberately broken lint input, then passes once reverted.

## 2. Recorded Design Decisions Before DDL

- [ ] 2.1 Confirm Decision 1 (assembly is the QC target; the function-index signature is superseded) against `11-database-schema-spec.md` §2, §4, and §6, and record it in the module `README.md`.
- [ ] 2.2 Confirm Decision 2 (a pending rule records an unvalued eligibility event rather than returning `FINANCIAL_RULE_PENDING`) against §6 and the absence of that response on `inspectUnit` in `contracts/openapi.yaml`.
- [ ] 2.3 Confirm Decision 3 (the repair operator is derived from the immutable component source; `FR-8.2`'s caller-supplied `original_operator_id` is superseded) against §2, §6, and the `Defect` schema.
- [ ] 2.4 Confirm Decision 4 (the defect taxonomy is configuration, and no code list ships in this module) and record the phase-4 dependency it creates.
- [ ] 2.5 Confirm Decision 8 (this module owns `M007`; `qc_bonus_accruals` stays in Payroll's `M009`) and notify the Payroll author that `lukla-payroll-engine` task 3.2 is superseded.
- [ ] 2.6 Verify: every decision above is written down with its alternatives in `design.md`, and no migration is authored before this step is done.

## 3. Database Migrations and Invariants

Delivered on `feat/qc-mes-migrations`; the boxes stay unchecked until that branch merges, per the
rule at the top of this file.

- [ ] 3.1 Author `M007`: `garment_assemblies` (unique `(tenant_id, serial_code)`, status enum), `assembly_components` (unique `garment_unit_id`), `qc_inspections` (unique `(assembly_id, sequence_no)`, append-only trigger), and `qc_defects` (FK to inspection and component, component must belong to the inspection's assembly). Delivered as `backend/migrations/007_assemblies_and_qc.sql`, with the assembly row lock, the sequence assignment, the disposition transition, and the deferred defect rule as triggers.
- [ ] 3.2 Author the `classify_qc_unit(p_assembly_id uuid, p_disposition text, p_defects jsonb, p_idempotency_key text)` routine: lock the assembly row, enforce `MENUNGGU_QC | REWORK → PASS | REPAIR | REJECT`, refuse to override a terminal disposition, and write the first-`PASS` eligibility event, wage credits, and bonus accrual in one transaction. **Rescoped to `feat/qc-mes-api`:** the tables it writes (`eligibility_events`, `wage_credits`, `qc_bonus_accruals`) are the payroll migration `M009`, which does not exist yet, so a routine authored now would be a runtime landmine. The locking, the transition, and the terminal refusal are already in `M007`'s triggers, so the routine that remains is the money block.
- [ ] 3.3 Add `ENABLE`/`FORCE ROW LEVEL SECURITY` policies for the four `M007` tables reading `current_setting('app.tenant_id', true)`, plus the `qc_inspections`/`qc_defects` no-`UPDATE`/no-`DELETE` trigger raising `LEDGER_IMMUTABLE`-style append-only errors. Delivered, with column-level `UPDATE` grants to `lukla_app` instead of table-level ones, and no `SECURITY DEFINER` function that would bypass row level security.
- [ ] 3.4 Verify: a second inspection for a terminal assembly is refused; an assembly still `ASSEMBLING` is refused; a piece cannot be allocated to two assemblies; a `qc_defects` row naming a component of another assembly is refused; `REPAIR`/`REJECT` without a defect and `PASS` with one are refused at `COMMIT`; `UPDATE`/`DELETE` on the inspection log is refused for the owner and denied for `lukla_app`; a component allocation cannot cross tenants; and the runtime role without tenant context reads zero rows. Delivered as `tests/test_m007_invariants.py` (17 checks, pytest and psycopg2 against a real server) rather than pgTAP, because the module's toolchain is already pytest and the extension would be a second prerequisite to install.

## 4. Contract Operations

- [x] 4.1 *(domain layer only)* Implement the classification service behind `inspectUnit`: the state machine, defect validation, first-`PASS` eligibility, wage credits, bonus accrual, and idempotent replay, all pure and connection-free.
- [ ] 4.2 Implement `POST /qc-inspections` (`inspectUnit`) returning `QcInspection`, with `x-roles: [QCInspector]`, the `Idempotency-Key` header, and `409` for `INVALID_STATE` and `IDEMPOTENCY_CONFLICT`.
- [ ] 4.3 Implement `GET /assemblies` (`listAssemblies`) with the `status` filter and `AssemblyPage` cursor pagination for `ProductionHead` and `QCInspector`.
- [ ] 4.4 Implement `POST /assemblies` (`createAssembly`) with the locked-BOM count check, verified-tally check, same-order check, and distinct-unallocated-piece check, inserting the assembly and its allocations atomically in `MENUNGGU_QC`.
- [ ] 4.5 Implement `GET /production/progress` (`listProductionProgress`) over assemblies and tallies, scoped by tenant and, where applicable, by order beneficiary.
- [ ] 4.6 Implement the `qc` section of `GET /dashboard` from the summary service.
- [ ] 4.7 Implement the tenant defect-taxonomy read that `inspectUnit` requires, and record the taxonomy version on the inspection if the QC lead confirms it is needed.
- [ ] 4.8 Implement the shared `Problem` model responses for the error codes this module can raise (`VALIDATION_ERROR`, `INVALID_STATE`, `IDEMPOTENCY_CONFLICT`, `DUPLICATE_REPAIR_CREDIT`, `FORBIDDEN`, `TENANT_CONTEXT_MISSING`) and the role enforcement matching each operation's `x-roles`.
- [ ] 4.9 Verify: Schemathesis run against `contracts/openapi.yaml` for the QC and assembly paths, plus one request asserting the `409 INVALID_STATE` body for a terminal assembly and one asserting `IDEMPOTENCY_CONFLICT` on a changed payload.

## 5. Verification Evidence

- [x] 5.1 *(domain layer only)* Cover the state machine, defect rules, pending-rule path, idempotency replay and conflict, repair routing, and the summary in `backend/quality-control/tests/`.
- [ ] 5.2 Map and run `DB-AT-05` (a repaired unit earns at most one credit) and the QC half of `DB-AT-04` (a `MENUNGGU_QC` assembly earns nothing) against PostgreSQL.
- [ ] 5.3 Wire the harness commands and the evidence collector output (`results.json`, `results.xml`, `api-results.xml`, `db-results.xml`, `system-results.json`, `manifest.json`) for this module.
- [ ] 5.4 Report any QC acceptance assertion that depends on `OQ-3`, `OQ-4`, `OQ-7`, or `OQ-8` as `BLOCKED`, never as `PASS`.
- [ ] 5.5 Verify: the collector exits 0 on a passing bundle and non-zero on a `FAIL` or a missing required file.

## 6. View 05 Integration

- [ ] 6.1 Implement `VIEW-05` (`/app/quality`) against the contract hooks, not raw `fetch`: the QC queue with the status filter, the scan/serial lookup, and the `Pass | Repair | Reject` disposition control.
- [ ] 6.2 Render the defect picker from the tenant taxonomy, with no free-text code entry, and render the no-override rule for a terminal assembly as a blocking state rather than a disabled button with no explanation.
- [ ] 6.3 Verify: interactive browser run showing a repair with a defect, the re-inspection of the same assembly, and the terminal state after a final `PASS`.

## 7. Escalations (Not Implementable in This Change)

- [ ] 7.1 Defect-to-time-study drift correlation (MOD-04's stated purpose in `docs/MODULES_ARCHITECTURE.md`): `qc_defects` has no join key to `time_study_observations`, so the correlation needs either a component-code convention or a schema addition. Escalate to the blueprint owner; do not invent a key.
- [ ] 7.2 Post-delivery returns, AQL thresholds, and needle detection (OQ-8): no automated acceptance threshold, chargeback, or warranty liability may be implemented before the business decides.
- [ ] 7.3 Reject compensation and material-loss recovery (OQ-7): no deduction is implemented from this proposal, and `payroll_adjustments` requires an explicit authorization and reason when it eventually is.
- [ ] 7.4 A correction path for a final `PASS` or `REJECT`: requires a separately authorized policy; this endpoint refuses overrides until then.
