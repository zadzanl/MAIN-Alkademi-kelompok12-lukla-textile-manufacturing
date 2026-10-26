# Implementation Tasks: Reconcile OpenAPI Endpoint Gaps & Operational Lifecycle Queries

> [!IMPORTANT]
> **MANDATORY DOWNSTREAM AGENT NOTICE: DO NOT IMPLEMENT STRAIGHT AWAY.**  
> Whatever agent or engineer picks up this change **MUST refine, enhance, sharpen, and harden the specification further** before running `/opsx:apply` or authoring backend/frontend implementation code. The downstream agent must verify filter parameters, schema nullability, cursor pagination edge cases, and role scoping across all 14 endpoints against shop floor workflows.

## 1. Phase 1 — Pre-Implementation Hardening & Refinement (MANDATORY)

- [x] 1.1 Audit query filter parameters and indexing against PostgreSQL schema in `11-database-schema-spec.md` (e.g. `cut_batches.order_id`, `sewing_tallies.line_id`, `assemblies.serial_code`) — *Completed in `openspec/changes/reconcile-openapi-endpoint-gaps/artifacts/pre-implementation-hardening.md` §1.1-1.2, including base keyset indexes for unfiltered queries and functional barcode normalization index `uq_garment_assemblies_norm_serial`*
- [x] 1.2 Harden schema nullability, default values, and cursor pagination edge cases across all 11 new schema components — *Completed in `openspec/changes/reconcile-openapi-endpoint-gaps/artifacts/pre-implementation-hardening.md` §1.3-1.5, mandating ISO 8601 UTC 6-digit microsecond cursor precision (`.ffffffZ`), explicit ASC keyset SQL template, dual sorting architecture, and non-whitespace regex pattern (`pattern: '\S'`) on `OrderCancellationRequest.reason`*
- [x] 1.3 Map and standardize error envelopes (`400 Bad Request`, `401 Unauthorized`, `403 Forbidden`, `404 Not Found`, `409 Conflict`, `422 Unprocessable Entity`) for all 14 endpoints — *Completed in `openspec/changes/reconcile-openapi-endpoint-gaps/artifacts/pre-implementation-hardening.md` §2.1-2.5*
- [x] 1.4 Reconcile role scoping (`x-roles`) against `04-rbac-matrix.md` with explicit permissions for `Owner`, `ProductionHead`, `WarehouseHead`, `FinancePayroll`, and `QCInspector` — *Completed in `openspec/changes/reconcile-openapi-endpoint-gaps/artifacts/pre-implementation-hardening.md` §3.1-3.3*
- [x] 1.5 Detail state transition invariants and idempotency rules for `POST /orders/{orderId}/confirmation` and `POST /orders/{orderId}/cancellation` — *Completed in `openspec/changes/reconcile-openapi-endpoint-gaps/artifacts/pre-implementation-hardening.md` §2.3-2.4, specifying 60-second in-flight idempotency lease recovery and reconciling `IN_PRODUCTION` cancellation with WIP quarantine protocol*

## 2. Phase 2 — Contract Specification & Blueprint Validation

- [x] 2.1 Integrate the 14 refined endpoints into `contracts/openapi.yaml` (expanding total operations from 69 to 83) — *Verified in `openspec/changes/lukla-ops-engine-planning/contracts/openapi.yaml`*
- [x] 2.2 Add and validate all 11 accompanying schema components in `contracts/openapi.yaml` — *Verified with Phase 1 hardening (nullable verifiedBy/verifiedAt, OrderCancellationRequest non-whitespace regex, OrderConfirmationRequest bounds)*
- [x] 2.3 Execute `python validate-blueprint.py --self-test` to ensure schema conformance and operation count — *Passed: 83 operations, 762 refs, 122 schemas, 5 negative controls passing*
- [x] 2.4 Execute `pwsh verify-traceability.ps1` to maintain cross-document traceability — *Passed: operationId values unique (83), exit code 0*

## 3. Phase 3 — Architecture & UI View Alignment

- [x] 3.1 Update `12-api-contract-plan.md` catalog with the 14 new endpoints and data structures — *Completed in `12-api-contract-plan.md` §3 (catalog expanded to 83 operations across 12 functional areas) and §3.1 (catalog detailing 14 query & lifecycle endpoints)*
- [x] 3.2 Update `14-frontend-architecture.md` linking `VIEW-01` through `VIEW-06` data hooks to new query endpoints — *Completed in `14-frontend-architecture.md` §2 (all 83 operations mapped across VIEW-01..06 and Shell), §3 (action bindings and mutation policies for 14 endpoints), and §9 (83-operation parity assertion script)*
- [x] 3.3 Update task and audit records documenting the completed reconciliation — *Completed in `openspec/changes/reconcile-openapi-endpoint-gaps/artifacts/joint-review-phase2-phase3.md` (unanimous multi-agent approval) and `phase3-recovery-checkpoint.md`*
