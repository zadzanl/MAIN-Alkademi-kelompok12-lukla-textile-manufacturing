# Technical Design: Lukla Operations Engine

## Context
Lukla Manufacturing manages contract garment production across three commercial schemes: CMT (client supplies materials), Semi-CMT (client supplies shell fabric, Lukla supplies trims), and CMT+Bahan (Lukla procures all materials, standard for internal Snøhund brand). Operational challenges include manual piece-rate payroll for 1 to ~70 operators, untracked sample prototype changes, and lack of system barriers preventing Client A fabric from being issued to Client B orders. The approved planning suite (`00-deconstruction.md` rev 4, BRD v2.3.0, `04-rbac-matrix.md`, `06-acceptance-tests.md`, `storage-architecture-draft.md`, `backend_database_structure.md`) establishes the blueprint.

## Goals / Non-Goals

**Goals:**
- Provide complete traceability across the 20 observed functional requirements (FR-1.1 through FR-10.4).
- Enforce programmatic multi-tenant isolation and material issuance validation at the database level to prevent cross-client contamination (FR-6.2).
- Support dynamic capacity allocation for fluctuating sewing floor headcounts with 30-minute interval touch-terminal reporting.
- Implement an automated piece-rate payroll engine verifying QC acceptance before wage credit and dividing the QC bonus pool 3 ways (2 mandor + 1 kepala operasional).
- Govern all operational operations through an 8-role RBAC matrix with separation of duties.

**Non-Goals:**
- Application code implementation during the planning phase (planning and specification only).
- Specifying unstated inventory transactions for Gudang (FR-5) or Cutting (FR-6) where source is silent (preserved as UNRESOLVED).
- Expanding payroll beyond slide specifications (no BPJS, income tax withholding, or overtime calculations).
- Modifying approved baseline planning documents.

## Decisions

### Decision 1: Immutable Double-Entry Ledger Core
- **Choice:** Maintain all inventory movements and payroll wage claims through an immutable double-entry ledger.
- **Rationale:** Separates custodial assets (client-owned CMT fabric) from proprietary assets and ensures wage disbursements reconcile atomically against verified output.
- **Alternatives Considered:** Single-balance CRUD tables (rejected due to audit drift and lack of historical traceability).

### Decision 2: Database-Level Trigger for Contamination Guardrail (FR-6.2)
- **Choice:** Enforce material dispatch validation via database-level constraint/trigger `validate_material_dispatch()`.
- **Rationale:** Ensures that even if API or frontend layers misroute a request, Client A raw materials cannot be issued to a Client B production batch.
- **Alternatives Considered:** Application-layer checks only (rejected due to risk of bypass during batch operations or script execution).

### Decision 3: 8-Role RBAC Model with RLS Policy Enforcement
- **Choice:** Implement 8 distinct roles (Owner, Sample Team, Warehouse, Production Head, Tailor, QC Inspector, Finance/Payroll, Maklon Client) backed by Supabase Row Level Security.
- **Rationale:** Satisfies slide 04 governance where operators have read-only access to locked records, warehouse staff cannot issue mismatched materials, and clients only access records tagged with their `client_id`.

### Decision 4: Six Capability Modular Specification Architecture
- **Choice:** Group the 20 FRs into 6 cohesive domain capabilities in `specs/`.
- **Rationale:** Mirrors the 6-phase operational workflow and provides modular testability for acceptance scenarios.

## Risks / Trade-offs

- **[Risk: Cross-Client Contamination Bypass]** → **Mitigation:** Enforce tenant checks via RLS and DB triggers on material dispatch.
- **[Risk: Operator Wage Disputes]** → **Mitigation:** Wages are only recognized after explicit QC Pass verification (FR-7.4); repair returns to the same sewer without secondary wage credit (FR-8.2).
- **[Risk: Fluctuation in Sewer Headcount]** → **Mitigation:** Dynamic line allocation without rigid machine slots (FR-7.1) allows daily recalculation of line capacity.
- **[Risk: QC Bonus Pool Rounding Ambiguity]** → **Mitigation:** The ÷3 split is fixed per deck; remainders are directed to factory reserve accounts without invented rounding directions.
