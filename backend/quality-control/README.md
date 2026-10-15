# Quality Control & MES Module (MOD-04)

Assembly-level quality inspection for the Lukla Operations Engine: the `Pass | Repair | Reject`
disposition state machine, defect capture against the tenant taxonomy, repair routing back to the
original operator, and the first-pass eligibility that Payroll values.

## The frozen contract is the source of truth

This module implements the OpenAPI 3.1 contract authored during planning. The sketch routes in
`docs/MODULES_ARCHITECTURE.md` (`/api/v1/qc-inspections`, `/api/v1/defects`) are superseded by the
paths below and must not be implemented.

- Contract: `openspec/changes/lukla-ops-engine-planning/contracts/openapi.yaml`
- Database schema: `openspec/changes/lukla-ops-engine-planning/11-database-schema-spec.md` §2–§4, §6
- Runtime requirements: `openspec/changes/lukla-qc-mes-engine/specs/qc-mes-runtime/spec.md`
- Plan, decisions, and checklist: `openspec/changes/lukla-qc-mes-engine/`

## Boundaries

Read-only inputs, owned by other modules:

- `garment_units` with a `VERIFIED` source tally and a `piece_rate_snapshots` reference (MOD-03)
- `financial_rule_versions` — the bonus rule version in force, its approval status, and its
  per-pass `bonus_rate` (MOD-05)
- the tenant's defect taxonomy configuration (phase 4 of `tasks.md`)

Written by this module:

- `garment_assemblies`, `assembly_components`, `qc_inspections`, `qc_defects` (migration `M007`)
- `eligibility_events`, `wage_credits` on a first pass, and `qc_bonus_accruals` — the rows are
  written inside this module's classification transaction, while the tables themselves belong to
  the payroll schema in migration `M009`. `lukla-payroll-engine` task 3.2 claimed `M007`; that
  claim is superseded, `M009` is not.

## Rules a reader must not have to rediscover

- **The assembly is the QC target.** `inspectUnit` classifies one finished assembly, not one piece.
  `11-database-schema-spec.md` §6 states this in prose; the function index's
  `classify_qc_unit(p_unit_id, p_disposition, p_defect_code, p_idempotency_key)` signature is not
  implemented, because it cannot express a defect list.
- **`PASS` and `REJECT` are terminal.** A final disposition cannot be overridden in this release.
  A retried delivery is still served, because idempotency is resolved before the state check.
- **A pending rule does not block an inspection.** The disposition and an unvalued
  `eligibility_events` row are recorded; no wage credit and no bonus accrual are produced, and no
  fallback rate is substituted. Later valuation uses the rule version the event carries.
- **The repair operator is derived, never supplied.** `FR-8.2`'s `original_operator_id` is
  superseded by `11-database-schema-spec.md` §2 ("derived from immutable component source, not
  supplied by caller"), and the frozen `Defect` schema has no field to carry it.
- **The defect taxonomy is configuration.** The module ships no code list. The BRD's three named
  defects are examples, not an enum; an unknown code is refused with `VALIDATION_ERROR`. The API
  layer reads the tenant's codes from `config/defect_taxonomy.json` (override the path with
  `QC_DEFECT_TAXONOMY_PATH`): a `default` list and a per-tenant `tenants` map that replaces it.
- **One credit per piece, one accrual per assembly.** Both are structural: eligibility is produced
  on the first pass only, and a pass is terminal, so a repaired unit cannot be credited twice.

## Layout

```
backend/quality-control/
├── src/
│   ├── api/        # placeholder: the routers live in backend/app/api/v1/quality.py (decision 15)
│   ├── models/     # contract-shaped schemas, status vocabularies, taxonomy, bonus rule
│   └── services/   # classification, repair routing, dashboard summary, domain errors
├── config/         # defect_taxonomy.json — deployment configuration, not code
├── tests/          # pytest suite, including the M007 database invariants
├── API_CONTRACTS.md
├── pyproject.toml
├── requirements.txt
└── requirements-dev.txt
```

The HTTP layer cannot live in this directory: `backend/quality-control` carries a hyphen and its
package is the generic `src`, so `backend/app` cannot import it. The routers therefore sit next to
the ledger's in `backend/app/api/v1/quality.py`, with the persistence in
`backend/app/services/qc.py`, and the shared authority between the two layers is the named-error
contract of `M007` plus `API_CONTRACTS.md`. `src/api/` stays a placeholder until the module
directory is importable.

`src/utils/` is absent until it has content: this module needs no shared arithmetic, and an empty
package would be dead weight.

## Database

`backend/migrations/007_assemblies_and_qc.sql` owns `garment_assemblies`, `assembly_components`,
`qc_inspections`, and `qc_defects`. It is applied after `M001` (identities), `M004` (orders), and
`M006` (`garment_units`), which other modules own; the composite foreign keys rely on those tables
carrying `PRIMARY KEY (tenant_id, id)`.

The database enforces what the service also enforces, so a direct SQL caller cannot bypass it:

| Rule | Enforced by |
| --- | --- |
| A final `PASS` or `REJECT` cannot be overridden, and an `ASSEMBLING` assembly is not inspectable | `trg_qc_inspections_prepare`, which also takes the assembly row lock and assigns `sequence_no` |
| The assembly and its pieces follow the disposition | `trg_qc_inspections_apply_disposition` |
| The inspection log cannot be edited or deleted | `trg_qc_inspections_immutable`, `trg_qc_defects_immutable`, plus a `REVOKE UPDATE, DELETE` from `lukla_app` |
| A defect names a piece of the inspected assembly | `trg_qc_defects_verify_piece` |
| `REPAIR` and `REJECT` need a defect, `PASS` must not carry one | `trg_qc_inspections_defect_rules`, a deferred constraint trigger evaluated at `COMMIT` |
| One piece belongs to one assembly | `uq_assembly_components_unit` |
| One tenant cannot read or write another tenant's rows | `ENABLE`/`FORCE ROW LEVEL SECURITY` with the `tenant_isolation_policy` on all four tables |

The runtime role `lukla_app` gets `SELECT, INSERT` on the four tables, and only the `status` and
`updated_at` columns of `garment_assemblies` and `garment_units` — the two columns the disposition
trigger writes. No `SECURITY DEFINER` function is needed, so no trigger silently bypasses row
level security.

## Local checks

```bash
cd backend/quality-control
pip install -r requirements-dev.txt
ruff check .
ruff format --check .
mypy src/ --strict
pytest -q
```

All four must exit 0. The same four commands run as the blocking `qc-mes-quality` job in
`.github/workflows/ci.yml`.

The database invariants need a reachable PostgreSQL, so they skip without one:

```bash
QC_TEST_DATABASE_URL=postgresql://postgres@127.0.0.1:5432/postgres pytest -q tests/test_m007_invariants.py
```

That test builds a throwaway `qc_verify` schema, applies `M001` and `M007` plus a documented
stand-in for the not-yet-authored `M004`/`M006` tables, and drops the schema afterwards. It is
local-only by design, matching how the ledger's database tests are run.

The HTTP layer is verified from the repository root, because the app is imported as
`backend.app`:

```bash
QC_TEST_DATABASE_URL=postgresql://postgres@127.0.0.1:5432/postgres pytest -q backend/tests/test_qc_api.py
```

It builds the same stand-in in the `qc_api_verify` schema, drives the real app through
`fastapi.testclient` as the unprivileged `lukla_app` role, and covers the disposition, the
terminal refusal, the defect rules, the taxonomy, the idempotency replay and conflict, the role
refusals, and the queue.

## Status

The disposition state machine, the defect rules, the first-pass eligibility and wage-credit
boundary, the pending-rule path, idempotent replay and conflict handling, repair routing, and the
dashboard summary are implemented and tested. `M007` is authored and verified against PostgreSQL,
including the append-only log, the tenant isolation, and the cross-assembly defect rule.

`POST /qc-inspections` (`inspectUnit`) and `GET /assemblies` (`listAssemblies`) are implemented in
`backend/app` against the real database, with the contract's roles, `Idempotency-Key` handling, and
`Problem` mapping, and are covered by `backend/tests/test_qc_api.py`. The tenant defect taxonomy is
read from deployment configuration.

Not implemented, with the reason each waits:

- The money a first `PASS` produces — one `eligibility_events` row, one `wage_credits` row per
  allocated piece, one `qc_bonus_accruals` row. Task 3.2's `classify_qc_unit` writes them, and the
  three tables are the payroll migration `M009`, which does not exist yet. Until it lands, an
  inspection records the disposition, the defects, and the piece statuses, and produces no money
  rows: keep the QC and payroll modules on one release, or re-valuate the inspections recorded in
  between, because the routine runs at inspection time and cannot see them afterwards.
- `POST /assemblies` (`createAssembly`) and `GET /production/progress` — both need `orders` (M004)
  and `garment_units`/`sewing_tallies` (M006), which no branch has authored yet.
- The `qc` section of `GET /dashboard` — its route cannot answer until the `orders` and `production`
  sections of the same response can be filled.
- `VIEW-05` (phase 6).

Work proceeds through the phases in `openspec/changes/lukla-qc-mes-engine/tasks.md`.
