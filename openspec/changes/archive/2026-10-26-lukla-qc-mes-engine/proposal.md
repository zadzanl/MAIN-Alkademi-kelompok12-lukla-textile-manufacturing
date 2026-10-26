# Proposal: Quality Control & MES Runtime Implementation

## Why
`lukla-ops-engine-planning` froze the requirements (`specs/quality-control-and-inspection/spec.md`, `specs/production-output-tracking/spec.md`), the OpenAPI 3.1 contract (`contracts/openapi.yaml`), and the database schema (`11-database-schema-spec.md` §2–§4, §6) for the QC and shop-floor module (MOD-04), and authorizes no application code. The module is still listed as `📋 To Be Implemented` in `docs/MODULES_ARCHITECTURE.md` §3, and no `backend/quality-control/` directory exists.

The frozen documents answer *what* must happen but leave five things a coder would otherwise invent: which of the two `classify_qc_unit` signatures in `11-database-schema-spec.md` is authoritative (the function index says `p_unit_id, p_disposition, p_defect_code`; the prose says `p_assembly_id, p_disposition, p_defects jsonb`), whether `FR-8.2`'s caller-supplied `original_operator_id` survives (the contract's `Defect` schema has no such field), where the defect code list comes from (the BRD names three defects; `qc_defects.defect_code` is untyped `text` and the taxonomy is Priority 2), whether an unapproved financial rule blocks an inspection or is recorded unvalued, and who owns migration `M007`. This change resolves all five by written decision and delivers the classification engine that the Payroll module consumes.

## What Changes
- Add the QC & MES runtime module at `backend/quality-control/` implementing the frozen contract operations `inspectUnit`, `listAssemblies`, `createAssembly`, and the `qc` section of `getDashboard`.
- Implement the assembly-level QC state machine: `MENUNGGU_QC | REWORK → PASS | REPAIR | REJECT`, with `QC_PASS` and `REJECT_SCRAP` terminal and no override in this release.
- Implement defect capture: `REPAIR` and `REJECT` require at least one defect whose code exists in the tenant's configured taxonomy; `PASS` carries none; an unknown code is refused instead of stored.
- Implement repair routing derived from the immutable component source, so the operator is never taken from the caller and rework creates no new wage eligibility.
- Implement the first-`PASS` valuation boundary: one eligibility event per assembly, one wage credit per allocated piece/contributor, and exactly one bonus accrual per assembly, all produced only under an `APPROVED` rule version; a `PENDING` rule records the disposition and the unvalued eligibility event and produces no monetary row and no fallback rate.
- Implement idempotent inspection recording keyed on `Idempotency-Key` over the assembly's inspection history, with `IDEMPOTENCY_CONFLICT` on a changed payload and replay served before the terminal-state check.
- Implement the QC queue summary used by `getDashboard` (`QcSummary`), counting each assembly once by its current status.
- Author migration `M007` (`garment_assemblies`, `assembly_components`, `qc_inspections`, `qc_defects`) with the assembly row lock, the state-transition refusal, the append-only triggers, the deferred defect rule, the single-allocation constraint, `ENABLE`/`FORCE ROW LEVEL SECURITY`, and column-level grants to the runtime role, so a direct SQL caller cannot bypass what the service enforces.
- Record the migration ownership decision: `M007` (assemblies, allocations, QC inspections, defects) belongs to this module; `M009` keeps `eligibility_events`, `wage_credits`, and `qc_bonus_accruals` with Payroll.

Out of scope: the HTTP layer, authentication, and the tenant defect taxonomy read (phase 4); the `classify_qc_unit` routine, which lands with `M009` because the tables it writes do not exist yet; the `createAssembly` BOM/verified-piece validation service; `VIEW-05` frontend work; defect-to-time-study drift correlation, which has no join key in the frozen schema; and resolving `OQ-3`, `OQ-4`, `OQ-7`, or `OQ-8`.

## Capabilities

### New Capabilities
- `qc-mes-runtime`: Assembly-level inspection disposition recording with an append-only inspection history, defect-taxonomy-validated Repair and Reject capture, caller-independent repair routing, single-eligibility and single-accrual first-Pass valuation behind the financial rule gate, idempotent inspection recording, and a per-assembly QC queue summary.

### Modified Capabilities
*(None; this change adds a runtime capability and does not alter the product requirements held by `quality-control-and-inspection` and `production-output-tracking` in `lukla-ops-engine-planning`.)*

## Impact
- **Backend:** Adds `backend/quality-control/` (module structure `src/{models,services,utils,api}` plus `README.md` and `API_CONTRACTS.md` per `docs/MODULES_ARCHITECTURE.md` §"Module Development Checklist").
- **CI:** Adds a blocking `qc-mes-quality` job to `.github/workflows/ci.yml` mirroring `payroll-engine-quality` (ruff check, ruff format --check, mypy --strict, pytest).
- **Database:** Adds `backend/migrations/007_assemblies_and_qc.sql` for `garment_assemblies`, `assembly_components`, `qc_inspections`, and `qc_defects`, applied after `M001`, `M004`, and `M006`. The Payroll change's `M007` task (`lukla-payroll-engine` tasks 3.2) is superseded; its `M009` ownership of `eligibility_events`, `wage_credits`, and `qc_bonus_accruals` stands, and `classify_qc_unit` lands with it.
- **Contract:** Consumes `contracts/openapi.yaml` as authored; no operation ID, path, schema, or enum is changed. The contract's inability to carry a defect taxonomy, a caller-supplied repair operator, or a `FINANCIAL_RULE_PENDING` response for `inspectUnit` is recorded as a decision, not patched.
- **Dependencies:** Consumes `MOD-05` (`FinancialRuleFields.bonus_rate` and the rule version status) and, at the HTTP phase, `MOD-01` (identity, RBAC, tenant context) and `MOD-03` (verified tallies feeding assemblies). `M007` additionally requires the `orders` and `garment_units` tables from `M004` and `M006`; until those exist, the database invariant suite builds them as documented test scaffolding rather than weakening the foreign keys.
