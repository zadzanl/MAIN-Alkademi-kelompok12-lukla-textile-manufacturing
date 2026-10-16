# Orchestration Task Record

## Intent
Implement the approved multi-subject Lukla runtime plan with discrete agent ownership and maximum safe parallelism.

## Constraints
- Preserve existing uncommitted work; do not overwrite unrelated changes.
- Do not invent unresolved finance, warehouse, QC, legal, or approval policy.
- Reuse frozen OpenAPI/database contracts and existing auth, problem, idempotency, and evidence patterns.
- One owner per file; integration owner resolves shared seams.

## Decisions
- Execute as a dependency DAG, not a serial chain.
- First wave: database/runtime verification, payroll HTTP completion, warehouse guardrail.
- Copilot/chat inference excluded from this shipment.

## Evidence
- Tracker: 40 subjects, zero production-ready claims.
- Payroll routes and stock persistence are incomplete or demo-backed.
- Existing dirty-tree ownership must be respected.

## Handoffs
- Pending first-wave agents.

## Verification
- Pending.

## Revisions
- Revision 1: approved plan entered implementation on 2026-10-16.

## Handoffs
- DB-001: added invariant regression tests; PostgreSQL runtime blocked at 127.0.0.1:5433.
- Payroll API-001: implemented SQL-backed weekly aggregate route and tests; statement and policy-dependent operations remain bounded/blocked.
- Warehouse-001: added scoped stock/issuance contract boundary and mismatch rejection; persistence remains blocked.

## Current revision
- Revision 2: first implementation wave returned; pending review before next wave.
