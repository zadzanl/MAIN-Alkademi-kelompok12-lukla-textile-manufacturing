# Review Record — Wave 1

## Review identity

- **Review Identity:** `lukla-runtime-wave-1-2026-10-16`
- **Task record:** `openspec/changes/lukla-payroll-engine/artifacts/orchestration-task-record.md`, revision 2. Confirmed loaded before review.
- **Objective:** Review the first Lukla runtime implementation wave before next-phase work.
- **Verdict:** `FAILED`
- **Execution health:** `BLOCKED`

## Accepted brief

The objective, acceptance target, changed surface, evidence limits, and route inputs were understandable and admitted. The review was limited to the declared first-wave files and implementation reports. Unrelated dirty-tree changes were not reviewed or attributed to this wave.

Acceptance target:

- DB invariant regression tests only; no migration change.
- Weekly payroll uses the SQL-backed aggregate path while retaining rule gating/idempotency and leaving policy-dependent operations blocked.
- Warehouse exposes separate scope dimensions, validates material-issuance beneficiary mismatch before mutation, and states its demo/non-persistent boundary.
- No PostgreSQL runtime or production inventory persistence claims; no unresolved policy is silently defaulted.

## Route decisions

| Dimension | Decision | Controlled tags / evidence | Dispatch count | State |
|---|---|---|---:|---|
| Behavioral | YES | `observable-behavior`, `data-integrity`, `error-recovery`, `behavioral-validation`; payroll and warehouse behavior changed | 0 | Not dispatched per explicit user instruction |
| Changeability | YES | `interface-contract`, `module-responsibility`, `teammate-safety`; new repositories, routes, schemas, and transaction seams | 0 | Not dispatched per explicit user instruction |
| Security | YES | `trust-boundary`, `identity-or-authorization`, `untrusted-input`; tenant, legal-owner, and order-beneficiary scope is exposed | 0 | Not dispatched per explicit user instruction |

No specialist was dispatched because the user explicitly prohibited subagent dispatch. Under the maintained protocol, Security coverage is required for a Security route; this missing required coverage prevents approval and makes execution health `BLOCKED`.

## Evidence checked

- `impl-db-001.md`: reports only invariant test additions, no migration edits, and PostgreSQL runtime blocked at `127.0.0.1:5433`.
- `impl-payroll-api-001.md`: reports SQL-backed weekly aggregate wiring, rule-gate/idempotency reuse, 501 statement boundary, and no database-backed runtime claim.
- `impl-warehouse-001.md`: reports separate scope fields, mismatch rejection, blocked matched issuance, demo header, and no persistence claim.
- Current contents of all declared implementation and test files, including the user/formatter-edited `backend/payroll-costing/src/repositories/payroll.py`.
- Current router wiring and authentication convention in `backend/app/api/v1/__init__.py`, `backend/app/main.py`, and `backend/app/core/auth.py`.
- Focused local checks: `6 passed` for `backend/tests/test_payroll_api.py` and `backend/tests/test_stock.py`; Python compilation and scoped whitespace checks passed.
- No PostgreSQL runtime evidence was obtained for this review. The DB report’s limitation was preserved; no runtime success was inferred from mocked tests or static inspection.

## Preserved source results

No specialist result exists because dispatch was explicitly prohibited. The three implementation reports remain the source evidence and were not rewritten or silently upgraded:

- DB-001: implementation report complete for test-only scope; runtime verification `NOT RUN / BLOCKED`.
- Payroll API-001: implementation report complete for API scope; corrected backend suite had PostgreSQL connection errors and no database-backed runtime success claim.
- Warehouse-001: implementation report complete for demo boundary; persistence and Playwright evidence not run.

## Classified findings

### MAJOR — `BLOCKING_DEFECT` — `review-wave1-S-001`

- **Provenance:** current `backend/app/api/v1/stock.py:107-174`; route wiring in `backend/app/api/v1/__init__.py:4,10`; auth convention in `backend/app/core/auth.py:42-161`.
- **Criterion/surface:** warehouse tenant/legal-owner/order-beneficiary trust boundary and authentication.
- **Observation:** `GET /api/v1/stock` and `POST /api/v1/material-issuances` have no `Depends(get_current_auth_context)` or equivalent authorization dependency. `tenantId`, `legalOwnerId`, and `orderBeneficiaryId` are caller-supplied query filters, while issuance accepts only a lot ID and order ID. The server does not derive tenant scope from an authenticated principal or authorize legal-owner access.
- **Consequence:** an unauthenticated caller can enumerate the deterministic stock fixture and submit issuance validation requests across tenant/owner/order scopes. The current route blocks persistence, but that does not make the trust boundary safe; the same omission becomes a direct cross-tenant/cross-owner mutation risk when persistence is added.
- **Required closure:** require the existing authentication/context boundary for these endpoints and authorize/filter scope from trusted server-side identity and policy inputs rather than caller-controlled tenant/owner scope. Preserve the explicit non-persistent failure behavior until persistence exists.
- **Validation:** add route-level unauthenticated and cross-scope authorization tests, then run the focused stock tests and generated OpenAPI inspection with the authenticated dependency wired.

### MAJOR — `PROOF_GAP` — `review-wave1-P-001`

- **Provenance:** `impl-db-001.md`, `impl-payroll-api-001.md`, and current payroll route/repository files.
- **Criterion/surface:** database-backed payroll runtime acceptance and no unavailable-runtime claims.
- **Observation:** no PostgreSQL runtime was available at the configured `127.0.0.1:5433` endpoint. The payroll API tests are mocked at the route seam, and the DB invariant tests were skipped/blocked in the reported environment.
- **Consequence:** SQL function invocation, aggregate row completeness, transaction rollback, and idempotent replay cannot be proven for this wave from the available execution evidence.
- **Required closure:** run the focused DB/API integration checks against an approved disposable PostgreSQL instance before claiming runtime completion. Do not change the current honest boundary or claim production readiness meanwhile.
- **Validation:** record the exact database endpoint and migration/test command, with successful focused invariant and payroll API integration results; retain the no-runtime claim if the environment remains unavailable.

## Non-blocking observations

- The payroll statement endpoint remains an explicit 501 boundary and does not invent meal, bonus, reserve, allocation, or payment policy.
- The warehouse matched issuance path returns `INVALID_STATE` without mutating the fixture, and mismatch rejection occurs before that boundary.
- The scoped local regression tests and syntax checks passed. Browser verification was not required for this backend review and was not run.
- No migration edit or production inventory persistence claim was observed in the declared wave.

## Final decision

`FAILED`. Approval is not permitted: a major warehouse authorization defect is present, and required Security Assurance coverage was not dispatched as prohibited by the user instruction. Execution health is `BLOCKED` because the required Security route has no usable specialist review and PostgreSQL runtime proof is unavailable.
