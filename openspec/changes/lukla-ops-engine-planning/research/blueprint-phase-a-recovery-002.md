# blueprint-phase-a-recovery-002 — bounded read-only recovery

**Date:** 2026-10-13
**Scope:** targeted defect points only, no broad re-research
**Mode:** read-only evidence sweep; no subagents dispatched

## 1. Checkpoint confirmation (verified)

| Item | Status | Evidence |
|------|--------|----------|
| `task-record.md` exists, rev 12 | Present (17118 bytes, 112 lines, last modified 2026-10-13) | `openspec/changes/lukla-ops-engine-planning/task-record.md` |
| `10-technology-stack-and-decisions.md` saved | 5648 B, 2026-10-13 19:42:59 | artifacts dir listing |
| `11-database-schema-spec.md` saved | 17209 B, 2026-10-13 19:42:59 | artifacts dir listing |
| `12-api-contract-plan.md` saved | 6266 B, 2026-10-13 19:16:27 | artifacts dir listing |
| `contracts/openapi.yaml` unchanged checkpoint | 53312 B, 2026-10-13 19:43:42; **42 operations** verified via YAML parse | section 3 inventory below |
| `artifacts/implementation/blueprint-phase-a.md` | **NOT FOUND** (filesystem absent) | `Test-Path` → False |

**Operation count breakdown (openapi.yaml):** 42 ops confirmed; per-domain totals
match the Phase 5 checkpoint (auth 3, ledger/me 3, clients/orders 4, audit 1,
samples 4, time-studies/rate-cards 2, materials/stock 5, cutting/tally/progress
4, QC 1, payroll 2, overhead 2, procurement 3, dashboard 2, files 2, internal
jobs 2, search 1). No drift from rev 11 assertion.

## 2. Targeted defect findings (parent-asserted, evidence-anchored)

Legend: **C** = confirmed via direct read; **Q** = partially confirmed (defect
substantive but expressive form varies); parentheses = file:line citation.

### 2.1 QC recorded on `garment_unit` rather than finished assembly 【C, with caveat】
- `11-database-schema-spec.md:38` — `garment_assemblies` status enum
  `ASSEMBLING|MENUNGGU_QC|QC_PASS|REWORK|REJECT_SCRAP` exists and is the
  business concept that “carries” inspection outcome for the serial.
- `11-database-schema-spec.md:40` — `qc_inspections` carries
  `garment_unit_id uuid` and **no** `assembly_id uuid` column.
- `11-database-schema-spec.md:86` — prose rules state QC applies to the
  **assembly serial** and "`qc_inspections.garment_unit_id` identifies that
  finished serial’s accountable source unit; the implementation must reject
  a serial without the assembly/component chain.”
- Net effect: **enforcement is only in prose** is `qc_inspections`
  a single assembly serial can yield multiple `garment_unit_id` rows;
  no SQL FK or CHECK constraint forces an
  `assembly_components` row presence. The defect is real but reducible to
  a missing FK + missing identity column, not a logical reversal.

### 2.2 `cut_units` + `waste_qty` mixed units 【C】
- `11-database-schema-spec.md:33` — both columns are `numeric(18,3)`.
- Same precision, but **no domain-enforced unit discriminator** (no
  `unit text` column, no table-level constraint linking
  `material_lot_id.unit` to these columns as in `order_components` at
  `:19`). Concretely: cutting line business rule treats `cut_units` as a
  piece count and `waste_qty` as a length/mass; schema permits both as an
  unconstrained decimal — accumulating quantities across rows is unsafe.

### 2.3 Missing operator / line CRUD, full assembly API, payroll approve+pay+read, client-invoice surface, auth-sessions store 【C】
OpenAPI substring sweep against `contracts/openapi.yaml`:

| Expected path segment | Present? | What exists |
|------------------------|----------|-------------|
| `/assemblies` (POST/PATCH) | **No** | zero operations |
| `/lines` CRUD | **No** | only `PUT /lines/{lineId}/operators` |
| `/operators` CRUD | **No** | only the same `assignOperator` PUT |
| `/client-invoices` | **No** | zero operations; only `supplier-invoices` |
| `/invoices` (client) | **No** | supplier-only |
| `/sessions` | **No** | `/auth/{login,refresh,logout}` only; **no** `auth_sessions` table |
| `/payroll/weekly/{periodId}/approve` | **No** | only `calculateWeeklyPayroll` POST + `getBonusPool` GET |
| `/payroll/weekly/{periodId}/pay` | **No** | absent |
| `GET /payroll/weekly/{periodId}` | **No** | absent (read surface missing) |
| `/financial-rules` | **No** | table `financial_rule_versions` exists (`:54`) but no API |

Cross-check at `12-api-contract-plan.md:28` and `:29` confirms the doc only
enumerates `assignOperator`, `recordSewingTally`, `listProductionProgress`,
`inspectUnit`, `getBonusPool`, `calculateWeeklyPayroll`, `recordOverhead`,
`calculateOverhead`. **No** approve/pay, no read-period, no line or operator
creation, no assembly allocate/finish endpoints, no client-invoice archive,
no refresh-token/session persistence endpoint.

### 2.4 Financial rule config 【partially C】
- Table `financial_rule_versions` (`:54`) is present and shaped correctly;
  `parameters jsonb` + `status PENDING/...` + `approved_by uuid NULL`.
- Enforcement present: `12-api-contract-plan.md:42` and
  `11-database-schema-spec.md:90` both return `FINANCIAL_RULE_PENDING`
  rather than silently defaulting.
- **Missing:** CRUD/admin API surface for tenant ops to author rule rows
  (no `/financial-rules` path), no rule-version snapshot binding to the
  payroll period at approve-time, no audit-trail surface for rule edits.

### 2.5 Loose nullability, FK, and RLS posture 【C】
- Same-table NOT NIL visibility is **inconsistent**:
  - `tenants` `:13`, `actors` `:14` explicitly mark `NOT NULL`;
  - `actor_memberships` `:15`, `clients` `:17`, `orders` `:18`,
    `cut_batches` `:33`, `sewing_lines` `:34`, `sewing_tallies` `:36`,
    `garment_units` `:37`, `garment_assemblies` `:38`,
    `assembly_components` `:39`, `qc_inspections` `:40`,
    `payroll_periods` `:50`, `wage_credits` `:51`,
    `qc_bonus_accruals` `:52`, `financial_rule_versions` `:54`,
    `supplier_invoices` `:58`: **no explicit NOT NULL countersignature**.
- FK notation is **prose-only** — no `REFERENCES`/`ON DELETE` clauses in
  the spec (e.g., `cut_batches.order_id`, `sewing_tallies.line_id`,
  `assembly_components.assembly_id`, `qc_inspections.garment_unit_id`):
  nothing in the file is enforceable at migration time.
- RLS posture **C**: `11-database-schema-spec.md:92` is titled “RLS and
  pooled connections”; `:94` mandates `ENABLE ROW LEVEL SECURITY` +
  `FORCE ROW LEVEL SECURITY` with GUC-bound policies. `:96` adds
  `set_request_context` + `SET LOCAL` discipline and the negative-control
  test claim. Posture exists but is documented, not auditable from MD
  alone.

### 2.6 Late ledger insertion 【C, semantic】
- `11-database-schema-spec.md:7` states the ledger is **forward-only**
  after migration; `:47` `ledger_transactions` enforces `**no
  UPDATE/DELETE**`.
- `:51` `wage_credits.reversal_of uuid NULL` permits a reversal pair,
  but there is **no rule ordering** that pins a payroll-driven ledger
  entry to the post-APPROVED transition. Combined with finding 2.3’s
  missing `/payroll/weekly/{periodId}/approve` endpoint, a late
  wage-credit could in principle still succeed against a calc that is
  pre-APPROVED — a real ordering defect to fence.

## 3. Exact remaining scope (Phase A only, before Phase B)

In decreasing priority:

1. **Add real assembly coverage**
   - `assembly_components` row insert/retract API surface
     (`POST /assemblies`, `POST /assemblies/{id}/components`,
     `POST /assemblies/{id}/finish`).
   - Add `qc_inspections.assembly_id uuid NOT NULL` + FK to
     `garment_assemblies.id`, plus CHECK that
     `assembly_components` row count ≥ required per `order_components`.
2. **Payroll workflow gap**
   - Add `POST /payroll/weekly/{periodId}/approve`,
     `POST /payroll/weekly/{periodId}/pay`,
     `GET /payroll/weekly/{periodId}`. Bind approved_at/paid_at to
     immutable ledger events.
3. **Sewing-line + operator CRUD**
   - `POST /lines`, `PATCH /lines/{lineId}`, `POST /operators`,
     `PATCH /operators/{id}`, plus `operators` table (currently absent
     from `:34` area; operators reference `actors` in `sewing_tallies`).
4. **Client invoices**
   - `client_invoices` table mirroring `supplier_invoices`:
     `(tenant_id, invoice_number, beneficiary_tenant_id, total_minor,
     currency, status, ...)` plus corresponding `GET/POST` endpoints.
5. **Auth-sessions persistence**
   - `auth_sessions` table (refresh-token family, family-id, rotated-from,
     revoked_at) + cross-link from `/auth/refresh` rotation rules
     (`12-api-contract-plan.md:7`).
6. **Financial-rule admin API**
   - `POST /financial-rules`, `POST /financial-rules/{id}/approve`,
     `GET /financial-rules?effective_from=…&tenantId=…`. Bind
     `rule_version` to `payroll_periods` at APPROVED.
7. **Schema tightening**
   - Decision block on cut-unit semantic: keep numeric(18,3) and add
     `unit text` selector column on `cut_batches` (`order_components`
     already has one at `:19`), or fix mass vs piece semantic explicitly.
   - Apply `NOT NULL` to FK columns and `REFERENCES … ON DELETE …` to
     all `:15`-`:54` rows so the spec is auditable at migration time.
   - Specify HOW RLS handles `:47` ledger immutability (current
     `FORCE ROW LEVEL SECURITY` does not by itself protect against the
     application pool inserting during payroll, finding 2.6).
8. **Reissue `verify-traceability.ps1`** after (1)–(6) to verify the
   traceability harness still passes (rev-11 verified exits 0 today).

## 4. What I did NOT do (honest boundary)

- No subagent dispatch performed, per user instruction.
- No implementation changes applied; only `read_file`, `Select-String`,
  Python YAML parse, and filesize/lastwritetime probes.
- No review verdict rendered; the eight points above are reported as
  parent-confirmed defects with mechanical evidence, awaiting the
  orchestrator’s review and approve to begin Phase A work.
- OpenSpec `openspec status` / `openspec validate` not re-invoked in
  this session; rev-11 baseline asserts both pass.
