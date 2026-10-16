# Review Record — Wave 1 Security Repair

## Review identity

- **Review Identity:** `lukla-runtime-wave-1-security-fix-2026-10-16`
- **Task record:** `openspec/changes/lukla-payroll-engine/artifacts/orchestration-task-record.md`, revision 2. Confirmed loaded before review.
- **Objective:** Decide whether the warehouse authentication and tenant-scope blocker from `review-wave1-001.md` is closed.
- **Changed surface:** `backend/app/core/auth.py`, `backend/app/api/v1/stock.py`, `backend/tests/test_stock.py`, and `impl-warehouse-auth-002.md`.
- **Constraint:** No implementation files were edited. No subagents were dispatched, per explicit user instruction.

## Accepted brief

The objective, acceptance target, changed surface, evidence limits, and routing inputs were understandable and admitted. The review is limited to the warehouse authorization repair and its effect on the existing payroll/ledger authorization boundary.

Acceptance criteria:

1. `GET /api/v1/stock` and `POST /api/v1/material-issuances` require authentication.
2. Payroll/ledger `get_current_auth_context` remains restricted to `Owner` and `FinancePayroll`.
3. Stock visibility is derived from authenticated tenant; caller `tenantId` cannot expand it.
4. Stock issuance requires the intended route roles and preserves mismatch rejection/no mutation.
5. No unresolved warehouse policy is invented.
6. Missing PostgreSQL persistence/runtime evidence is recorded as a proof gap, not a success claim.

## Route decisions

| Dimension | Decision | Controlled tags / evidence | Dispatch count | State |
|---|---|---|---:|---|
| Behavioral | NO | No behavioral specialist route requested; this review is explicitly limited to Security Assurance plus a narrow interface check if needed. Focused behavior was checked directly. | 0 | NOT_SELECTED |
| Changeability | NO | No changeability review requested. The narrow dependency-interface check was performed directly because the repair refactored shared auth code. | 0 | NOT_SELECTED |
| Security | YES | `trust-boundary`, `identity-or-authorization`, `untrusted-input`, `security-recovery`; the prior blocker concerned unauthenticated routes and caller-controlled tenant scope. | 0 | NOT_DISPATCHED |

Security Assurance dispatch was prohibited by the explicit user instruction. Under the maintained review protocol, Security coverage is required for a Security route; this is a process/evidence limitation, not evidence that the repair is unsafe.

## Evidence checked

- Current `backend/app/core/auth.py`: shared JWT/tenant/actor validation; `get_current_auth_context` passes exactly `{"Owner", "FinancePayroll"}`; stock uses a separate `{"Owner", "Warehouse"}` dependency.
- Current `backend/app/api/v1/stock.py`: both routes depend on `get_current_stock_auth_context`; reads filter fixture rows by `auth.tenant_id` before applying caller filters; issuance validates the lot/order beneficiary relationship before returning the existing non-persistent `INVALID_STATE` response.
- Current `backend/tests/test_stock.py`: unauthenticated route checks, tenant expansion check, negative role checks, and authorized mismatch rejection.
- `impl-warehouse-auth-002.md`: reports the same repair boundary, focused tests, generated OpenAPI inspection, and explicitly no production persistence claim.
- Prior blocker `review-wave1-001.md`, finding `review-wave1-S-001`: the former routes lacked authentication and trusted caller scope.
- Existing `backend/app/api/v1/*.py` imports: payroll/ledger routes continue using `get_current_auth_context`.

## Verification performed

| Check | Result |
|---|---|
| `PYTHONPATH=backend python -m pytest -q backend/tests/test_stock.py` | PASS — 10 passed; one existing Starlette/httpx deprecation warning |
| Python compile of reviewed auth/stock/test files | PASS |
| Existing ledger authorization-focused tests | BLOCKED — session fixture could not connect to PostgreSQL at `127.0.0.1:5433`; 7 selected tests errored during setup |
| Browser verification | Not applicable to this backend-only review; not run |
| Workspace hygiene | Not rerun; the reported untracked root `package-lock.json` is pre-existing and was not touched by this repair |

## Preserved source evidence

No specialist result exists because subagent dispatch was explicitly prohibited. The implementation report remains source evidence and is not upgraded:

- `impl-warehouse-auth-002.md` reports focused stock/auth tests passing, PostgreSQL-dependent checks blocked, stock remaining demo/non-persistent, and no production persistence claim.
- The prior review’s `review-wave1-S-001` is treated as the repaired source finding; its concrete route-authentication defect is no longer present in the inspected code.

## Classified findings

### CRITICAL — `BLOCKING_DEFECT` — `review-wave1-security-002-S-COVERAGE`

- **Classification:** `BLOCKING_DEFECT` for review execution, not an implementation defect.
- **Provenance:** Review route decision; maintained `review-protocol/SKILL.md` requires Security Assurance coverage for any Security route.
- **Observation:** Security was selected, but no Security Assurance specialist could be dispatched because the user explicitly prohibited subagents.
- **Consequence:** This record cannot claim the required independent Security Assurance coverage or issue an `APPROVED` verdict under the maintained protocol.
- **Required closure:** Run the same frozen brief through Security Assurance coverage when dispatch is permitted; preserve this repair and its focused evidence.
- **Validation:** Complete Security Assurance result covering trust boundary, identity/authorization, untrusted input, and security recovery, with no unresolved blocking finding.

### MAJOR — `PROOF_GAP` — `review-wave1-P-002`

- **Provenance:** `impl-warehouse-auth-002.md`, `orchestration-task-record.md`, and this review’s blocked ledger test run.
- **Criterion/surface:** PostgreSQL persistence/runtime evidence required to establish the runtime boundary; acceptance criterion 6 explicitly requires this gap to remain visible.
- **Observation:** PostgreSQL at `127.0.0.1:5433` was unavailable. Stock remains deterministic demo data and material issuance intentionally returns `INVALID_STATE` without persistence.
- **Consequence:** Database transaction context, durable stock scope enforcement, and persistence-time no-mutation behavior are not proven. Mocked/fixture route tests must not be presented as production persistence evidence.
- **Required closure:** Run approved PostgreSQL-backed warehouse/auth and relevant ledger checks, or retain the explicit non-persistent boundary and mark runtime evidence `BLOCKED`/`NOT_RUN`.
- **Validation:** Record the exact database endpoint and successful integration results before making any persistence or production-readiness claim.

### LEARN_NOTE — `review-wave1-S-001` concrete defect closure

- **Provenance:** Previous review finding `review-wave1-S-001`; current `auth.py`, `stock.py`, and focused tests.
- **Observation:** Both stock routes now require authentication; stock reads are constrained by the authenticated tenant; caller `tenantId` cannot broaden results; `Owner` and `Warehouse` are the route roles; mismatch rejection remains before the non-persistent failure.
- **Assessment:** The original unauthenticated warehouse exposure is closed in the inspected demo route. No separate legal-owner or client-beneficiary policy was invented; the implementation preserves those dimensions and leaves broader policy unresolved.
- **Validation:** Focused stock suite passed with 10 tests. This note is not a production persistence or independent Security Assurance success claim.

## Verdict

`FAILED`

The implementation-level security blocker is closed by the inspected repair, but the review itself cannot be approved because required Security Assurance coverage was explicitly not dispatched. The PostgreSQL/runtime limitation is separately recorded as `PROOF_GAP`; it is not treated as a success claim and does not get attributed to the repair as a defect in `package-lock.json` hygiene.

## Execution health

`BLOCKED` — the selected required Security route has no usable specialist result, and the PostgreSQL-backed ledger authorization run was unavailable. Direct focused stock evidence is positive but cannot override the required coverage rule.

## Remediation validation

No implementation remediation is prescribed by this record. When process constraints permit, obtain the required Security Assurance result against this unchanged brief and retain the PostgreSQL `BLOCKED`/`NOT_RUN` status unless a real database-backed run is completed.