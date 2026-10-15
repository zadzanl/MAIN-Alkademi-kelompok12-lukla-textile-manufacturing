# QC & MES API Contracts

Binding source: `openspec/changes/lukla-ops-engine-planning/contracts/openapi.yaml`. No operation
ID, path, schema, or enum is changed by this module. This file records, per operation, what the
implementation must honour and what is not implemented yet.

## Operations

| Operation | Path | Roles (`x-roles`) | View | Request → Response | Implemented |
| --- | --- | --- | --- | --- | --- |
| `inspectUnit` | `POST /qc-inspections` | `QCInspector` | VIEW-05 | `QcRequest` → `QcInspection` | Yes, recording only |
| `listAssemblies` | `GET /assemblies` | `ProductionHead`, `QCInspector` | VIEW-04, VIEW-05 | `status` query → `AssemblyPage` | Yes |
| `createAssembly` | `POST /assemblies` | `ProductionHead` | VIEW-04 | `AssemblyRequest` → `Assembly` | No — waits for `orders` (M004) and `garment_units` (M006) |
| `listProductionProgress` | `GET /production/progress` | `Owner`, `ProductionHead`, `Tailor`, `MaklonClient` | VIEW-01, VIEW-04 | cursor → `ProgressPage` | No — waits for `sewing_tallies` (M006) |
| `getDashboard` (`qc` section) | `GET /dashboard` | see contract | VIEW-01 | → `QcSummary` | No — the route needs the `orders` and `production` sections too |

The routers live in `backend/app/api/v1/quality.py` with the persistence in
`backend/app/services/qc.py`, next to the ledger's, because `backend/quality-control/` cannot be
imported: the directory name carries a hyphen and its package is the generic `src`. This module's
`src/` stays the pure domain layer, and the database's named-error contract is what both sides
share. Recorded as decision 15 in `design.md`.

"Recording only" on `inspectUnit` means the disposition, the defects, and the state transition are
recorded and returned; the money a first `PASS` produces is task 3.2 (`classify_qc_unit`), which
waits for migration `M009` and its three tables. See the module README.

## `inspectUnit` — `POST /qc-inspections`

Headers: `Idempotency-Key` (required). Body `QcRequest`:

```json
{ "assemblyId": "55555555-5555-4555-8555-555555555555", "disposition": "REPAIR",
  "defects": [{ "componentUnitId": "…", "code": "puckering", "notes": null }] }
```

Responses:

| Status | When |
| --- | --- |
| `201` | `QcInspection` — the recorded decision; a replay returns the stored decision unchanged |
| `401` | no valid bearer token |
| `403` | the caller's role is not `QCInspector` |
| `409` | `INVALID_STATE` (assembly `ASSEMBLING`, `QC_PASS`, or `REJECT_SCRAP`), `IDEMPOTENCY_CONFLICT` (key reused with a different payload) |
| `400` | `VALIDATION_ERROR` (defect rules, unknown defect code, foreign component piece) |

There is deliberately no `409 FINANCIAL_RULE_PENDING` on this operation: an unapproved bonus rule
records the disposition and an unvalued eligibility event instead of refusing the inspection
(`11-database-schema-spec.md` §6).

Invariants, in this order, and where each is enforced now:

1. The request's `assemblyId` must be the assembly that was loaded. — the request carries only
   `assemblyId`, so this is structural.
2. A blank `Idempotency-Key` is refused. — the header is required and 16..200 characters, as the
   contract declares.
3. A key already recorded for this assembly with the same payload returns the stored decision
   without producing money a second time; with a different payload it is `IDEMPOTENCY_CONFLICT`.
   This check runs before the state check, so a retried delivery of a final disposition succeeds.
   — `idempotency_records`, reserved inside the same transaction.
4. The assembly must be `MENUNGGU_QC` or `REWORK`. — the pre-flight read, and again by
   `trg_qc_inspections_prepare` under the assembly row lock.
5. The assembly must have at least one allocated component piece. — the pre-flight read only: no
   trigger enforces this, so the API layer is the only place it can live.
6. `REPAIR` and `REJECT` require at least one defect whose code is in the tenant taxonomy;
   `PASS` requires none. — the taxonomy check is the API layer's (it is configuration);
   the presence rule is `trg_qc_inspections_defect_rules`, a deferred trigger firing at `COMMIT`.
7. Every defect must name a piece allocated to this assembly, at most once. —
   `trg_qc_defects_verify_piece` and `uq_qc_defects_piece`.
8. `REPAIR` routes each defect to the piece's recorded operator and produces no money. — routing is
   read from `assembly_components`; no money is written for a repair.
9. `REJECT` produces no eligibility, no credit, and no deduction. — no money is written for a
   reject.
10. The first `PASS` produces one eligibility event, one wage credit per allocated piece valued from
    its `piece_rate_snapshots` rate, and one `qc_bonus_accruals` row valued from the approved rule's
    `bonusRate` — or, while the rule version is `PENDING`, the eligibility event alone. —
    **not implemented**: task 3.2, which waits for migration `M009`.

`qc_inspections` is append-only with `unique (assembly_id, sequence_no)`; the database assigns the
next `sequence_no` in the insert trigger, so a caller cannot choose one.

## The tenant defect taxonomy

The frozen schema has no taxonomy table, so the taxonomy is deployment configuration, read by the
API layer from the file named by `QC_DEFECT_TAXONOMY_PATH` (default
`backend/quality-control/config/defect_taxonomy.json`):

```json
{ "default": ["broken stitch", "puckering", "uneven seam"], "tenants": { "<tenant-uuid>": ["hole"] } }
```

A tenant entry replaces the default list; an explicit empty list means that tenant may record no
defect at all. Codes are matched exactly after trimming. An unknown code is refused with
`VALIDATION_ERROR` naming the code, never stored. The three default codes are the BRD's examples,
shipped as editable configuration so the QC terminal works before the QC lead configures theirs.

## Database error mapping (phase 4 implements this)

`M007` raises a named code for every rule it enforces. The API layer maps them to the contract's
`Problem` codes; nothing here needs a new response shape.

| Raised by the database | SQLSTATE | `Problem.code` | Status |
| --- | --- | --- | --- |
| `QC_ASSEMBLY_NOT_FOUND` | `02000` | `VALIDATION_ERROR` | `400` |
| `QC_ASSEMBLY_NOT_READY` | `55000` | `INVALID_STATE` | `409` |
| `QC_DISPOSITION_TERMINAL` | `55000` | `INVALID_STATE` | `409` |
| `QC_DEFECT_REQUIRED`, `QC_DEFECT_NOT_ALLOWED` | `23514` | `VALIDATION_ERROR` | `400` |
| `QC_DEFECT_FOREIGN_COMPONENT` | `23514` | `VALIDATION_ERROR` | `400` |
| `QC_INSPECTION_NOT_FOUND` | `02000` | `VALIDATION_ERROR` | `400` |
| `uq_qc_inspections_sequence` (unique violation) | `23505` | `IDEMPOTENCY_CONFLICT` | `409` |
| `uq_qc_defects_piece` (unique violation) | `23505` | `VALIDATION_ERROR` | `400` |
| `uq_assembly_components_unit` (unique violation) | `23505` | `VALIDATION_ERROR` | `400` |
| foreign key violation | `23503` | `VALIDATION_ERROR` | `400` |
| row level security violation | `42501` | `TENANT_CONTEXT_MISSING` | `400` |
| `QC_INSPECTION_IMMUTABLE` | `55000` | — | never reachable through the API: `lukla_app` holds no `UPDATE`/`DELETE` privilege, so the statement is denied first |

## Contract gaps (escalated, not patched)

- `Defect` has no operator field, so a caller cannot supply the repair operator; the schema rule
  makes it derived. Adding the field would reopen the Phase A review.
- `QcRequest` cannot carry the defect taxonomy version, and `qc_inspections` has no column for it.
  If the QC lead wants the taxonomy version recorded per inspection, that is a schema and contract
  change, not an implementation detail.
- `QcSummary` has three counters and no total, so the summary counts assemblies by current status
  rather than inspection rows; the alternative double counts a repaired-then-passed assembly.
- `inspectUnit` declares only `201`, `401`, `403`, and `409`. Its defect rules and its unknown
  defect code are validation failures, so the implementation answers `400 VALIDATION_ERROR` as this
  file's mapping table says. Declaring `400` (or `422`) on the operation is a contract change.
- `AssemblyPage` carries `items` only and `/assemblies` declares no cursor parameter, so the queue
  is returned whole, newest first. Pagination needs a contract change, not an implementation choice.

## Verification

`backend/tests/test_qc_api.py` runs the real app against a real PostgreSQL instance in a throwaway
schema (M001, M007, and a documented stand-in for the not-yet-authored `orders` and `garment_units`)
and covers the disposition, the terminal refusal, the defect rules, the taxonomy, the idempotency
replay and conflict, the role refusals, and the queue. It skips without a reachable server.

```bash
QC_TEST_DATABASE_URL=postgresql://postgres@127.0.0.1:5432/postgres pytest -q backend/tests/test_qc_api.py
```
