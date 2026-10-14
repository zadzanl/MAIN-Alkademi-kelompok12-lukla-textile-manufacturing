# Review Record: Immutable Double-Entry Core Implementation Plan (Round 002)

**Review Identity:** `lukla-double-entry-core-plan-review-002`  
**Date:** 2026-10-14  
**Delivery Mode:** Full Specialist Suite (`behavioral_reviewer`, `changeability_reviewer`, `security_reviewer`)  
**Subject:** Revised Implementation Plan Draft (`prompt_draft.md`) for the Immutable Double-Entry Core of Lukla Operations Engine.  

---

## 1. Objective and Acceptance Target

Evaluate the revised implementation plan draft (`prompt_draft.md`) for the Immutable Double-Entry Core of the Lukla Operations Engine. The objective is to verify whether all 14 blocking defects from Round 001 have been completely resolved, and ensure the plan is technically airtight, fully conformant to `contracts/openapi.yaml` and `11-database-schema-spec.md`, and safe for engineering delegation.

---

## 2. Route Decisions and Execution Health

All three dimensions were routed and evaluated in parallel by specialist subagents:

| Dimension | Route | Status | Specialist Role | Dispatched Instance ID | Findings |
|---|---|---|---|---|---|
| **Behavioral Assurance (`B`)** | `YES` | `COMPLETE` | Behavioral Assurance Specialist | `5b46cb25-6c85-4756-91e9-62e32d1df143` | B-201, B-202, B-203 |
| **Changeability Assurance (`C`)** | `YES` | `COMPLETE` | Changeability Assurance Specialist | `812b6637-9f0b-4902-83ae-71f83acb35bf` | C-008, C-009, C-010 |
| **Security Assurance (`S`)** | `YES` | `COMPLETE` | Security Assurance Specialist | `fd199008-f7fd-4748-b8a4-3f1854b56d2c` | S-008-R2 (All S-001–S-007 resolved) |

**Execution Health:** `COMPLETE`. All three specialists completed evaluations without partial failures or execution warnings.

---

## 3. Evidence Checked

- `C:\Users\lenovo\.gemini\antigravity\brain\4675258f-f156-4576-a875-861ed052592e\prompt_draft.md` (Revised Implementation Plan Draft, Lines 1–84)
- `openspec/changes/lukla-ops-engine-planning/reviews/double-entry-core-plan-review-001.md` (Round 001 Review Record)
- `openspec/changes/lukla-ops-engine-planning/11-database-schema-spec.md` (§1 SQL Conventions, §4 Ledger & Idempotency Tables, §5 Functions & Triggers, §6 RLS & Pooled Connections, §7 Transaction Boundaries, §9 Privilege Matrix & Migrations)
- `openspec/changes/lukla-ops-engine-planning/contracts/openapi.yaml` (Paths `/ledger/transactions`, `/ledger/transactions/{transactionId}/reversals`, `/ledger/entries`; Schemas `LedgerRequest`, `LedgerTransaction`, `LedgerEntry`, `ReversalRequest`, `LedgerPage`, `Problem`)
- `openspec/changes/lukla-ops-engine-planning/10-technology-stack-and-decisions.md` (§2 Database Decisions, §4 Security & Portability Rules)

---

## 4. Verification of Round 001 Blocking Defects

All 14 blocking defects identified in Round 001 were verified against the revised `prompt_draft.md`:

| Round 001 Defect ID | Title | Status | Evidence in Revised Plan |
|---|---|---|---|
| **DEFECT-01 (CRITICAL)** | Absence of `FORCE RLS` & dedicated application role | **RESOLVED** | Lines 19, 23, 70 mandate `ENABLE RLS`, `FORCE RLS`, `app.tenant_id` policies, and revoking direct table mutation from `lukla_app`. |
| **DEFECT-02 (CRITICAL)** | Missing composite FKs on `ledger_entries` | **RESOLVED** | Lines 18, 50, 69 enforce composite FKs `(tenant_id, transaction_id)` and `(tenant_id, account_id)`. |
| **DEFECT-03 (CRITICAL)** | Omission of `idempotency_records` table | **RESOLVED** | Lines 17, 24 create `idempotency_records` with composite unique constraint `(tenant_id, operation_id, key)`. |
| **DEFECT-04 (CRITICAL)** | Missing connection pool reset hooks | **RESOLVED** | Lines 30, 53, 71 mandate pool lifecycle hooks executing `RESET ALL` / `DISCARD ALL` and `is_local = true` transaction boundaries. |
| **DEFECT-05 (CRITICAL)** | Missing Bearer JWT auth, RBAC & context derivation | **RESOLVED** | Lines 29, 34, 54, 74 mandate Bearer JWT, `Owner`/`FinancePayroll` roles, token-derived context, and authorization re-check on replay. |
| **DEFECT-06 (MAJOR)** | Schema contradiction on `GET /ledger/entries` | **RESOLVED** | Lines 40–42, 57, 78 format endpoint to return `LedgerPage` (`items: List[LedgerTransaction]`, `nextCursor: Optional[str]`) with cursor pagination. |
| **DEFECT-07 (MAJOR)** | Reversal route parameter mismatch & missing body | **RESOLVED** | Lines 36–39, 77 standardize parameter to `{transactionId}` and require `ReversalRequest` body (`reason: str`). |
| **DEFECT-08 (MAJOR)** | Reversal direction inversion & duplicate prevention | **RESOLVED** | Lines 22, 38–39, 56, 77 mandate entry direction inversion (`DEBIT <-> CREDIT`), partial unique index on `reversal_of`, and blocking reversals of reversals. |
| **DEFECT-09 (MAJOR)** | Empty-transaction rejection at commit on header | **RESOLVED** | Lines 20, 49, 63 bind deferred constraint trigger evaluated at `COMMIT` to `ledger_transactions`, rejecting empty headers ($\ge 1$ debit, $\ge 1$ credit required). |
| **DEFECT-09B (MAJOR)** | Check constraints on entry amount and direction | **RESOLVED** | Lines 21, 66 mandate `CHECK (amount_minor > 0)` and `CHECK (direction IN ('DEBIT', 'CREDIT'))`. |
| **DEFECT-10 (MAJOR)** | Account code resolution per tenant & active validation | **RESOLVED** | Lines 31–32 mandate resolving `accountCode` against `ledger_accounts` filtered by active `tenant_id`, requiring `active = true` and matching currency. |
| **DEFECT-11 (MAJOR)** | Missing RFC 7807 Problem error envelopes | **RESOLVED** | Lines 43–45, 57, 79 mandate RFC 7807/9457 `application/problem+json` matching OpenAPI `Problem` schema and post-rollback sanitized audit logging. |
| **DEFECT-12 (MAJOR)** | RFC 8785 canonical JSON sorting before hashing | **RESOLVED** | Lines 33–34 mandate RFC 8785 canonical JSON sorting before SHA-256 hashing. |
| **DEFECT-13 (MAJOR)** | Standard layout under `backend/app/` & minimal deps | **RESOLVED** | Lines 9, 28 bound runtime dependencies to standard, minimal libraries (`fastapi`, `uvicorn`, `pydantic>=2.0`, `sqlalchemy>=2.0`, `psycopg[binary]>=3.1`, `pytest`, `httpx`). |
| **DEFECT-14 (MAJOR)** | Stored procedure hardening & zero direct DML | **RESOLVED** | Lines 19, 23 mandate `SECURITY DEFINER SET search_path = pg_catalog, public` and zero dynamic SQL; revoke direct table mutation. |

---

## 5. Round 002 Findings

While the primary architecture has been substantially hardened, three surgical findings remain across the specialist reports:

### 5.1. Blocking Defects (`BLOCKING_DEFECT`)

#### DEFECT-R2-01 (MAJOR) — Missing `Idempotency-Key` Handling on Compensating Reversal Endpoint
- **Provenance:** `C-009`, `B-201` (Independently flagged by both Changeability and Behavioral specialists)
- **Cited Evidence:** `contracts/openapi.yaml` lines 146–157, line 155 (`parameters: [{$ref: '#/components/parameters/TransactionId'}, {$ref: '#/components/parameters/IdempotencyKey'}]`); `prompt_draft.md` lines 36–39.
- **Consequence:** `openapi.yaml` marks `IdempotencyKey` as required for `POST /ledger/transactions/{transactionId}/reversals`. If a client submits a reversal with an `Idempotency-Key` and experiences a network timeout after Lukla commits the reversal, a client retry sending the same key will be evaluated without idempotency cache lookup. The second attempt will encounter "transaction already reversed" or violate the database partial unique index, returning `409 Conflict` instead of the cached `201 Created` reversal transaction.
- **Required Closure:** Specify in R2 that `POST /api/v1/ledger/transactions/{transactionId}/reversals` requires header `Idempotency-Key`, reserves the key in `idempotency_records` under `operation_id = 'reverseLedgerTransaction'`, and returns the stored `201 Created` response on replay.
- **Validation:** Pytest test submitting a reversal with `Idempotency-Key`, followed by a replay of the exact same request, asserting HTTP 201 with identical body and no duplicate transaction.

#### DEFECT-R2-02 (MAJOR) — Relational Seam Gap: `audit_events` Table Omitted from R1 Migrations
- **Provenance:** `C-008`
- **Cited Evidence:** `prompt_draft.md` line 17 vs line 35; `11-database-schema-spec.md` §4 line 65 and §7 line 105.
- **Consequence:** R2 line 35 mandates: *"Atomically execute append_ledger_transaction, record audit event, and return 201 Created with LedgerTransaction schema."* However, R1 line 17 omits `audit_events` from the required migration schema. An atomic insert into `audit_events` during journal posting will fail with undefined relation `audit_events` unless the table is established.
- **Required Closure:** Add `audit_events (id, tenant_id, actor_id, service_principal, action, entity_type, entity_id, request_id, payload, occurred_at)` to the R1 migration requirements with `ENABLE ROW LEVEL SECURITY` and `FORCE ROW LEVEL SECURITY`.
- **Validation:** Automated test confirming that committing a ledger transaction writes a corresponding row to `audit_events` within the same transaction.

---

### 5.2. Proof Gaps (`PROOF_GAP`)

#### PROOF-GAP-R2-01 — Account Code Resolution Failure Test Harness & Acceptance Criteria
- **Provenance:** `B-202`
- **Cited Evidence:** `prompt_draft.md` R2 line 32 vs R3 lines 47–58 and Acceptance Criteria lines 59–81.
- **Consequence:** R2 states that `accountCode` must resolve to active accounts matching transaction currency, but R3 and Acceptance Criteria omit negative verification tests for: (1) unknown account code, (2) inactive account (`active = false`), and (3) account currency mismatch. Without explicit checkboxes, edge-case validation can be skipped during implementation.
- **Required Closure:** Add an explicit test case in R3 and an Acceptance Criteria checkbox asserting that referencing an unknown `accountCode`, an inactive account, or a currency-mismatched account fails with RFC 7807 `application/problem+json` (status 400 or 422, code `VALIDATION_ERROR`) and rolls back completely.
- **Validation:** Pytest negative-control tests asserting RFC 7807 problem responses on invalid account codes.

---

### 5.3. Learn Notes (`LEARN_NOTE`)

- **NOTE-R2-01 (Architecture Layout Tree, `C-010`):** Include an explicit directory layout snippet in `prompt_draft.md` (`backend/app/api/v1/`, `backend/app/core/`, `backend/app/models/`, `backend/app/schemas/`, `backend/app/services/`) to guide the code generation agent away from clustering logic into a monolithic file.
- **NOTE-R2-02 (Concurrent Idempotency In-Flight State, `B-203`):** Clarify that concurrent requests with identical idempotency keys encountering lock unblocking handle the database `UniqueViolation` cleanly by reading the committed response rather than raising an unhandled 500 error.
- **NOTE-R2-03 (Unprivileged Test Harness Connection, `S-008-R2`):** Ensure pytest test fixtures switch to the unprivileged `lukla_app` role when executing RLS negative-control tests, since default PostgreSQL superuser connections bypass RLS policies.

---

## 6. Review Verdict and Remediations

### Verdict: `NEEDS_REVISION` (Round 002 of 3)

**Rationale:** The implementation plan draft has achieved massive quality improvements and resolved all 14 Round 001 blocking defects. However, 2 localized blocking defects (`DEFECT-R2-01` missing `Idempotency-Key` on reversals, `DEFECT-R2-02` missing `audit_events` table in R1) and 1 proof gap (`PROOF-GAP-R2-01` account resolution negative tests) must be resolved to achieve full compliance with `contracts/openapi.yaml` and `11-database-schema-spec.md`.

### Required Remediations for Round 003:

1. **R1 Migrations:** Add `audit_events (id, tenant_id, actor_id, service_principal, action, entity_type, entity_id, request_id, payload, occurred_at)` with `FORCE RLS` to R1 migrations so the atomic audit record insert in R2 succeeds.
2. **R2 Reversal Endpoint:** Mandate `Idempotency-Key` header on `POST /api/v1/ledger/transactions/{transactionId}/reversals` using `operation_id = 'reverseLedgerTransaction'`, returning cached `201 Created` on replay.
3. **R3 Test Harness & Acceptance Criteria:** Add negative verification tests and an acceptance checkbox verifying that unknown accounts, inactive accounts, or currency mismatches reject with RFC 7807 `application/problem+json` (`VALIDATION_ERROR`).
4. **Directory Structure Guidance:** Embed the explicit subpackage tree under `backend/app/` (`api/v1/`, `core/`, `models/`, `schemas/`, `services/`).

Once these 4 focused items are applied to `prompt_draft.md`, resubmit for final Round 003 review and approval.
