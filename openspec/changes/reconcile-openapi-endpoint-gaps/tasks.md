# Implementation Tasks: Reconcile OpenAPI Endpoint Gaps & Operational Lifecycle Queries

> [!IMPORTANT]
> **MANDATORY DOWNSTREAM AGENT NOTICE: DO NOT IMPLEMENT STRAIGHT AWAY.**  
> Whatever agent or engineer picks up this change **MUST refine, enhance, sharpen, and harden the specification further** before running `/opsx:apply` or authoring backend/frontend implementation code. The downstream agent must verify filter parameters, schema nullability, cursor pagination edge cases, and role scoping across all 14 endpoints against shop floor workflows.

## 1. Phase 1 — Pre-Implementation Hardening & Refinement (MANDATORY)

- [ ] 1.1 Audit query filter parameters and indexing against PostgreSQL schema in `11-database-schema-spec.md` (e.g. `cut_batches.order_id`, `sewing_tallies.line_id`, `assemblies.serial_code`)
- [ ] 1.2 Harden schema nullability, default values, and cursor pagination edge cases across all 11 new schema components
- [ ] 1.3 Map and standardize error envelopes (`400 Bad Request`, `401 Unauthorized`, `403 Forbidden`, `404 Not Found`, `409 Conflict`, `422 Unprocessable Entity`) for all 14 endpoints
- [ ] 1.4 Reconcile role scoping (`x-roles`) against `04-rbac-matrix.md` with explicit permissions for `Owner`, `ProductionHead`, `WarehouseHead`, `FinancePayroll`, and `QCInspector`
- [ ] 1.5 Detail state transition invariants and idempotency rules for `POST /orders/{orderId}/confirmation` and `POST /orders/{orderId}/cancellation`

## 2. Phase 2 — Contract Specification & Blueprint Validation

- [ ] 2.1 Integrate the 14 refined endpoints into `contracts/openapi.yaml` (expanding total operations from 69 to 83)
- [ ] 2.2 Add and validate all 11 accompanying schema components in `contracts/openapi.yaml`
- [ ] 2.3 Execute `python validate-blueprint.py --self-test` to ensure schema conformance and operation count
- [ ] 2.4 Execute `pwsh verify-traceability.ps1` to maintain cross-document traceability

## 3. Phase 3 — Architecture & UI View Alignment

- [ ] 3.1 Update `12-api-contract-plan.md` catalog with the 14 new endpoints and data structures
- [ ] 3.2 Update `14-frontend-architecture.md` linking `VIEW-01` through `VIEW-06` data hooks to new query endpoints
- [ ] 3.3 Update task and audit records documenting the completed reconciliation
