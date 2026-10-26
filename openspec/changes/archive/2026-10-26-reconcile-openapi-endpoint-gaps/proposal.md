# Proposal: Reconcile OpenAPI Endpoint Gaps & Operational Lifecycle Queries

> [!IMPORTANT]
> **MANDATORY DOWNSTREAM AGENT NOTICE: DO NOT IMPLEMENT STRAIGHT AWAY.**  
> Whatever agent picks up this change **MUST refine, enhance, sharpen, and harden the specification further** before running `/opsx:apply` or authoring implementation code. Specifically, the downstream agent must verify filter parameters, schema nullability, cursor pagination edge cases, and role scoping across all 14 endpoints against shop floor workflows.

## Why

A comprehensive multi-vector architectural review conducted by three Principal Systems Architects (Veteran Engineers) revealed critical **"Write-Only Black Holes"** and **"Severed Lifecycle Chains"** in the baseline OpenAPI contract:
1. **Mandor Verification Deadlock:** `POST /sewing-tallies/{tallyId}/verification` requires a `tallyId`, but there is no endpoint to list unverified tallies for a line or shift (`GET /sewing-tallies`). Mandors sitting at shop floor terminals cannot inspect or verify output.
2. **Sewing Input Foreign Key Gap:** Recording a sewing tally (`POST /sewing-tallies`) strictly requires `cutBatchId`, but there is no endpoint to discover or search cut batches produced by cutting operations (`GET /cut-batches`).
3. **Order Lifecycle Deadlock:** The order state machine specifies `DRAFT -> CONFIRMED -> IN_PRODUCTION -> QC -> COMPLETED|CANCELLED`, but orders created directly via `POST /orders` have no API mechanism to transition to `CONFIRMED` or `CANCELLED`.
4. **Procurement Approval Blindness:** Finance and Owner roles must approve purchase orders (`POST /purchase-orders/{id}/approval`), but cannot view PO line items, unit prices, or supplier invoices (`GET /purchase-orders`, `GET /supplier-invoices`).
5. **Ledger Posting Discovery Gap:** Constructing double-entry transactions (`POST /ledger/transactions`) requires valid account codes, but the Chart of Accounts is unqueryable (`GET /ledger/accounts`).

Addressing these gaps at the contract-proposal stage prevents disruptive refactors and broken workflows during frontend (`VIEW-01`–`VIEW-06`) and backend service development.

## What Changes

- **Add 14 Essential Query & Lifecycle Endpoints:**
  - `GET /sewing-tallies`: List recorded 30-minute sewing tallies with filters (`lineId`, `operatorId`, `orderId`, `status`) for Mandor sign-off.
  - `GET /cut-batches`: List available cut batches produced from fabric lots.
  - `POST /orders/{orderId}/confirmation`: Explicit state transition from `DRAFT` to `CONFIRMED`.
  - `POST /orders/{orderId}/cancellation`: Explicit state transition to `CANCELLED` requiring an audited justification.
  - `GET /purchase-orders` & `GET /purchase-orders/{purchaseOrderId}`: Paginated list and detailed inspection of POs.
  - `GET /supplier-invoices`: List recorded AP supplier invoices.
  - `GET /client-invoices/{invoiceId}`: Retrieve line item and tax breakdown for client billing.
  - `GET /ledger/accounts`: List Chart of Accounts for journal validation.
  - `GET /ledger/transactions/{transactionId}`: Inspect posted transaction header and entry legs.
  - `GET /clients/{clientId}`: Single client entity profile lookup.
  - `GET /samples/{sampleId}`: Single sample detail and active revision query.
  - `GET /assemblies/{assemblyId}`: Single assembly detail for QC terminal.
  - `GET /time-studies`: List stopwatch time study observations by sample revision.
- **Enhance Existing Query Capabilities:**
  - Add `serialCode` and `orderId` query parameters to `GET /assemblies` for fast barcode/QR scanner lookups in `VIEW-05`.
- **Preserve Strict Immutability Guardrails:**
  - All additions are strictly read-only query projections or atomic state transition actions. No `PUT`/`PATCH`/`DELETE` mutations on double-entry ledger, tallies, QC results, or audit logs.

## Capabilities

### New Capabilities
- `operational-query-and-lifecycle-endpoints`: Comprehensive REST query projections, barcode scanner lookup parameters, and explicit order lifecycle transitions unblocking shop floor, warehouse, and finance workflows.

### Modified Capabilities
- None. Existing database entities and business rules remain intact; this proposal projects existing data models into the external HTTP contract.

## Impact

- **API Contracts:** `contracts/openapi.yaml` will expand from 69 to 83 operations with 11 new schema components, validated via `validate-blueprint.py`.
- **Architecture Documentation:** `12-api-contract-plan.md`, `14-frontend-architecture.md`, and `task-record.md` will be formally updated.
- **Downstream Teams:** Frontend developers building `VIEW-01` through `VIEW-06` will have complete typed data hooks without mocking missing read endpoints. Backend developers will have explicit request/response schemas to implement.
