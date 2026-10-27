# Design: Reconcile OpenAPI Endpoint Gaps & Operational Lifecycle Queries

> [!IMPORTANT]
> **PRE-IMPLEMENTATION HARDENING MANDATE**  
> This is an architectural design proposal. Any downstream agent or engineer picking up this change **MUST NOT implement code immediately**. You are required to **refine, enhance, sharpen, and harden** the contract schemas, RBAC constraints, parameter validation rules, error mappings, and idempotency invariants before executing `/opsx:apply` or authoring backend/frontend code.

## Context

The Lukla Operations Engine is an event-driven apparel manufacturing MES with an immutable double-entry ledger. During a comprehensive multi-vector architectural review by three Principal Systems Architects (Veteran Engineers), 14 critical endpoint gaps were discovered in the OpenAPI baseline ([`contracts/openapi.yaml`](../../../../openspec/changes/lukla-ops-engine-planning/contracts/openapi.yaml)):
- Shop floor Mandors could verify tallies (`POST /sewing-tallies/{tallyId}/verification`), but could not list unverified tallies by line and date.
- Sewing terminal operators required `cutBatchId` to record tallies, but could not discover available cut batches produced by cutting.
- Orders created directly via `POST /orders` were permanently stranded in `DRAFT` because no state machine confirmation or cancellation routes existed.
- Finance approvers were asked to approve purchase orders blindly without endpoints to inspect lines, unit prices, or supplier invoices.
- Callers posting double-entry journals could not discover the Chart of Accounts.

These gaps cause operational deadlocks across all 6 core UI views (`VIEW-01` through `VIEW-06`).

## Goals / Non-Goals

**Goals:**
- Provide typed REST query endpoints for all core operational entities (`sewing_tallies`, `cut_batches`, `purchase_orders`, `supplier_invoices`, `ledger_accounts`, `time_studies`).
- Provide single-resource detail getters (`/clients/{id}`, `/samples/{id}`, `/assemblies/{id}`, `/purchase-orders/{id}`, `/client-invoices/{id}`, `/ledger/transactions/{id}`).
- Provide explicit, audited order lifecycle transitions (`confirmOrder`, `cancelOrder`).
- Support high-speed barcode/QR scanning in the QC terminal (`VIEW-05`) via `serialCode` search parameter.
- Maintain strict database immutability: zero `PUT`/`PATCH`/`DELETE` mutations on ledger, audit, or tally records.

**Non-Goals:**
- Automated MRP calculation or replenishment algorithms (explicitly out of scope per BRD §3.2).
- Statutory payroll taxes (PPh 21, BPJS) or corporate income tax.
- External payment gateway integrations or automated bank feeds.
- Mutable ledger or tally editing (compensating reversal entries remain the sole modification path).

## Decisions

### 1. Explicit Action Endpoints for State Transitions
- **Decision:** Use `POST /orders/{orderId}/confirmation` and `POST /orders/{orderId}/cancellation` rather than open-ended `PATCH /orders/{orderId}` with a mutable `status` string.
- **Rationale:** Enforces state machine invariants in code. Orders can only transition from `DRAFT` to `CONFIRMED` under Owner or ProductionHead authority, and cancellations require an audited `reason` payload.
- **Alternatives Considered:** Generic `PATCH /orders/{id}` with status payload (rejected: allows invalid transitions and bypasses validation gates).

### 2. Cursor-Based Pagination for All Operational Collections
- **Decision:** All collection query endpoints (`GET /sewing-tallies`, `GET /cut-batches`, `GET /purchase-orders`, `GET /supplier-invoices`, `GET /ledger/accounts`, `GET /time-studies`) use opaque cursors (`cursor` query parameter) and return `{items: [...], nextCursor: ...}`.
- **Rationale:** Aligns with `12-api-contract-plan.md` Section 2 standard paging contract and guarantees O(1) performance over append-only PostgreSQL tables without offset drift.

### 3. Read-Only Chart of Accounts Discovery
- **Decision:** Expose `GET /ledger/accounts` returning list of active `LedgerAccount` items (`code`, `name`, `accountClass`, `currency`, `active`).
- **Rationale:** Clients constructing manual journals or viewing balances require dynamic account resolution rather than hardcoded magic strings.

### 4. Barcode Scanner Support for QC Inspection Terminal
- **Decision:** Add `serialCode: string` query parameter to `GET /assemblies`, alongside `GET /assemblies/{assemblyId}`.
- **Rationale:** Floor inspectors in `VIEW-05` scan physical barcode/QR tags. Searching by serial code directly avoids loading full assembly queues into browser memory on low-spec Android tablets.

### 5. Downstream Agent Hardening Mandate
- **Decision:** The downstream agent picking up this change must perform explicit schema hardening before implementation:
  - Validate query filter indexing against PostgreSQL tables (`cut_batches`, `sewing_tallies`).
  - Verify error status code consistency (ensure `422 Unprocessable Entity` is standard across validation errors).
  - Verify role scoping in `x-roles` against `04-rbac-matrix.md`.
  - Ensure all new schemas and endpoints pass `validate-blueprint.py --self-test` and `verify-traceability.ps1`.

## Risks / Trade-offs

- **[Risk] Premature implementation before schema refinement:** Downstream agent rushes to write code without validating parameter constraints.  
  → *Mitigation:* Explicit gating tasks in `tasks.md` requiring refinement, hardening, and test plan sign-off prior to code implementation.
- **[Risk] Ledger immutability violation:** Developers might attempt to add update endpoints to ledger tables.  
  → *Mitigation:* Hard constraint in design and specs: ledger entries and transactions are strictly append-only; corrections require compensating reversals.
- **[Risk] Scope creep into automated procurement/accounting:** Teams might try to build full ERP accounts payable.  
  → *Mitigation:* Non-goals explicitly bounded; manual PO and invoice recording only.
