# QC & MES API Contracts

Binding source: `openspec/changes/lukla-ops-engine-planning/contracts/openapi.yaml`. No operation
ID, path, schema, or enum is changed by this module. This file records, per operation, what the
implementation must honour and what is not implemented yet.

## Operations

| Operation | Path | Roles (`x-roles`) | View | Request → Response | Implemented |
| --- | --- | --- | --- | --- | --- |
| `inspectUnit` | `POST /qc-inspections` | `QCInspector` | VIEW-05 | `QcRequest` → `QcInspection` | Domain service only |
| `listAssemblies` | `GET /assemblies` | `ProductionHead`, `QCInspector` | VIEW-04, VIEW-05 | `status` query → `AssemblyPage` | No |
| `createAssembly` | `POST /assemblies` | `ProductionHead` | VIEW-04 | `AssemblyRequest` → `Assembly` | No |
| `listProductionProgress` | `GET /production/progress` | `Owner`, `ProductionHead`, `Tailor`, `MaklonClient` | VIEW-01, VIEW-04 | cursor → `ProgressPage` | No |
| `getDashboard` (`qc` section) | `GET /dashboard` | see contract | VIEW-01 | → `QcSummary` | Domain service only |

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

Invariants the domain service enforces, in this order:

1. The request's `assemblyId` must be the assembly that was loaded.
2. A blank `Idempotency-Key` is refused.
3. A key already recorded for this assembly with the same payload returns the stored decision
   without producing money a second time; with a different payload it is `IDEMPOTENCY_CONFLICT`.
   This check runs before the state check, so a retried delivery of a final disposition succeeds.
4. The assembly must be `MENUNGGU_QC` or `REWORK`.
5. The assembly must have at least one allocated component piece.
6. `REPAIR` and `REJECT` require at least one defect whose code is in the tenant taxonomy;
   `PASS` requires none.
7. Every defect must name a piece allocated to this assembly, at most once.
8. `REPAIR` routes each defect to the piece's recorded operator and produces no money.
9. `REJECT` produces no eligibility, no credit, and no deduction.
10. The first `PASS` produces one eligibility event, one wage credit per allocated piece valued from
    its `piece_rate_snapshots` rate, and one `qc_bonus_accruals` row valued from the approved rule's
    `bonusRate` — or, while the rule version is `PENDING`, the eligibility event alone.

`qc_inspections` is append-only with `unique (assembly_id, sequence_no)`; the service returns the
next `sequence_no` for the caller to persist.

## Contract gaps (escalated, not patched)

- `Defect` has no operator field, so a caller cannot supply the repair operator; the schema rule
  makes it derived. Adding the field would reopen the Phase A review.
- `QcRequest` cannot carry the defect taxonomy version, and `qc_inspections` has no column for it.
  If the QC lead wants the taxonomy version recorded per inspection, that is a schema and contract
  change, not an implementation detail.
- `QcSummary` has three counters and no total, so the summary counts assemblies by current status
  rather than inspection rows; the alternative double counts a repaired-then-passed assembly.
