# Review Record: Immutable Double-Entry Core Implementation Plan

**Review Identity:** `lukla-double-entry-core-plan-review-001`  
**Date:** 2026-10-14  
**Delivery Mode:** Full Specialist Suite (`behavioral_reviewer`, `changeability_reviewer`, `security_reviewer`)  
**Subject:** Implementation Plan Draft (`prompt_draft.md`) for the Immutable Double-Entry Core of Lukla Operations Engine.  

---

## 1. Objective and Acceptance Target

Admit and rigorously evaluate the implementation plan draft (`prompt_draft.md`) for the production backend and database migrations of the Immutable Double-Entry Core of the Lukla Operations Engine under `backend/`. The core engine acts as an append-only operational sub-ledger to eliminate two severe manufacturing risks:
- Multi-tenant fabric cross-contamination (segregating custodial CMT maklon material from company-owned Snøhund/Full Package stock at the database transaction boundary).
- Weekly piece-rate payroll errors (establishing an immutable record of labor applied, QC pass bonuses, and piece-rate wage accruals without manual reconciliation).

The acceptance target is an implementation plan that is technically exhaustive, teammate-safe, strictly conformant to OpenAPI 3.1 contracts (`contracts/openapi.yaml`) and database specifications (`11-database-schema-spec.md`), and hardened against multi-tenant data leakage and accounting invariant bypass.

---

## 2. Route Decisions and Execution Health

All three dimensions were admitted, routed, and independently dispatched to dedicated specialist subagents:

| Dimension | Route | Reason | Result | Dispatched Instance ID |
|---|---|---|---|---|
| **Behavioral Assurance (`B`)** | `YES` | Critical data-integrity invariants: mathematical balance ($\sum \text{Debits} == \sum \text{Credits}$), database immutability triggers, late-line insertion prevention, and idempotency replay. | `COMPLETE` | `2bbbf1f1-792b-4ece-8e5b-b81e0cf76911` |
| **Changeability Assurance (`C`)** | `YES` | Teammate-safety, module responsibility, OpenAPI 3.1 interface contracts (`/ledger/transactions`, `/ledger/entries`), cursor pagination, and clean repository layout under `backend/`. | `COMPLETE` | `a147828f-f61b-46c0-b800-c056b4456cf5` |
| **Security Assurance (`S`)** | `YES` | Strict multi-tenant isolation, `FORCE ROW LEVEL SECURITY`, connection pool hygiene (GUC reset), non-owner application roles, SQL injection prevention, and RFC 7807 error sanitization. | `COMPLETE` | `5e3ed6af-83c6-423f-96ae-864ea705494c` |

**Execution Health:** `COMPLETE`. All three specialist instances completed their analyses without execution warnings, partial evaluations, or ambiguous outputs.

---

## 3. Evidence Checked

- `C:\Users\lenovo\.gemini\antigravity\brain\4675258f-f156-4576-a875-861ed052592e\prompt_draft.md` (Subject implementation plan draft)
- `openspec/changes/lukla-ops-engine-planning/11-database-schema-spec.md` (§1 SQL conventions, §4 ledger & idempotency tables, §5 functions & triggers, §6 RLS & pooled connections, §9 privilege matrix & migration sequence M001/M008/M011/M012)
- `openspec/changes/lukla-ops-engine-planning/contracts/openapi.yaml` (Paths `/ledger/transactions`, `/ledger/transactions/{transactionId}/reversals`, `/ledger/entries`; components `LedgerRequest`, `LedgerTransaction`, `LedgerEntry`, `ReversalRequest`, `LedgerPage`, `Problem`)
- `openspec/changes/lukla-ops-engine-planning/10-technology-stack-and-decisions.md` (§2 Database & framework decisions, §4 Security & portability rules)
- `openspec/changes/lukla-ops-engine-planning/12-api-contract-plan.md` (§1 Protocol baseline, §2 RFC 7807/9457 Problem error envelopes & cursor paging, §3 Endpoint catalog)
- `openspec/changes/lukla-ops-engine-planning/18-parallelization-and-workstreams.md` (§4 Dev 3 Backend brief)
- Workspace environment and repository state (`.gitignore`, non-existence of root `backend/`)

---

## 4. Classified Findings by Severity

Findings are synthesized across specialist reports (`B-001`–`B-011`, `C-001`–`C-007`, `S-001`–`S-007`), preserving source provenance IDs and validation criteria.

### 4.1. Critical Blocking Defects (`BLOCKING_DEFECT`)

#### DEFECT-01 (CRITICAL) — Absence of Row-Level Security (`FORCE RLS`) and Dedicated Non-Owner Application Role
- **Provenance:** `S-001`, `B-010`
- **Cited Evidence:** `11-database-schema-spec.md` §6 lines 97–102; `10-technology-stack-and-decisions.md` §4 lines 42–43; `prompt_draft.md` R1.
- **Consequence:** Without `ENABLE ROW LEVEL SECURITY` and `FORCE ROW LEVEL SECURITY`, tenant isolation relies solely on application SQL `WHERE` clauses. Any missing filter in joins or pagination exposes cross-tenant financial records. Connecting as table owner or superuser bypasses RLS policies entirely.
- **Required Closure:** 
  1. Mandate in R1: execute `ALTER TABLE ... ENABLE ROW LEVEL SECURITY;` and `ALTER TABLE ... FORCE ROW LEVEL SECURITY;` on `ledger_accounts`, `ledger_transactions`, `ledger_entries`, and `idempotency_records`.
  2. Define explicit RLS policies enforcing `tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid`.
  3. Establish a dedicated application database role (`lukla_app`) without `BYPASSRLS` or superuser privileges.
  4. Add an Acceptance Criterion verifying negative controls: queries executed without an initialized `app.tenant_id` return zero rows.
- **Validation:** Automated test under `lukla_app` asserting zero rows returned when `app.tenant_id` is unset.

#### DEFECT-02 (CRITICAL) — Missing Composite Foreign Key Constraints on `ledger_entries`
- **Provenance:** `B-006`, `S-007`
- **Cited Evidence:** `11-database-schema-spec.md` §1 lines 8–11; `prompt_draft.md` R1 & Acceptance Criteria.
- **Consequence:** Single-column foreign keys (`transaction_id REFERENCES ledger_transactions(id)` and `account_id REFERENCES ledger_accounts(id)`) allow an entry to reference Tenant B's account inside Tenant A's transaction, defeating database-level tenant isolation.
- **Required Closure:** Explicitly mandate in R1 that `ledger_entries` must enforce composite foreign keys:
  - `FOREIGN KEY (tenant_id, transaction_id) REFERENCES ledger_transactions(tenant_id, id) ON DELETE RESTRICT`
  - `FOREIGN KEY (tenant_id, account_id) REFERENCES ledger_accounts(tenant_id, id) ON DELETE RESTRICT`
  - Enforce `account_class` check constraint on `ledger_accounts` to segregate custodial vs company-owned accounts.
- **Validation:** Automated test attempting to insert an entry with Tenant A's `tenant_id` and `transaction_id`, but Tenant B's `account_id`, asserting database foreign key constraint violation.

#### DEFECT-03 (CRITICAL) — Omission of `idempotency_records` Table from Migration Specification
- **Provenance:** `B-001`, `S-003`, `C-003`
- **Cited Evidence:** `11-database-schema-spec.md` §4 line 66, §5 line 93; `openapi.yaml` line 817; `prompt_draft.md` R1.
- **Consequence:** R2 mandates idempotency replay and 409 conflict detection, but R1 omits the storage table. The backend cannot store cached HTTP status codes or response payloads, nor can it differentiate in-flight leases from completed mutations. Global keys without tenant partitioning allow cross-tenant front-running and response cache theft.
- **Required Closure:** Add `idempotency_records` to R1 migrations with composite unique constraint `(tenant_id, key, operation_id)`, `canonical_payload_hash bytea`, `status text`, `response_status smallint`, `response_body jsonb`, `created_at timestamptz`, `completed_at timestamptz NULL`, and `FORCE RLS`. Require re-checking authorization before returning cached replay responses.
- **Validation:** Pytest tests verifying that identical idempotency keys used across different tenants do not collide, and replay fetches stored responses.

#### DEFECT-04 (CRITICAL) — Missing Connection Pool Reset Hooks and Transaction Isolation
- **Provenance:** `S-004`
- **Cited Evidence:** `11-database-schema-spec.md` §6 lines 100–101, §9 line 155; `prompt_draft.md` Acceptance Criteria.
- **Consequence:** If `app.tenant_id` is set outside a transaction or connection checkout/checkin lacks reset hooks, pooled connections leak Tenant A's context to subsequent requests executed by Tenant B.
- **Required Closure:**
  1. Mandate that all ledger requests run inside an explicit transaction context manager with `set_config('app.tenant_id', ..., true)` (`is_local = true`).
  2. Implement connection pool event hooks (`checkout` and `checkin`) executing `DISCARD ALL` / `RESET ALL`.
  3. Add an automated test capturing a single pooled connection, executing Tenant A operations (including aborted transactions), returning it to the pool, and verifying `app.tenant_id` is null before Tenant B sets context.
- **Validation:** Deterministic connection-reuse pytest test proving zero GUC leakage across checkin/checkout cycles.

#### DEFECT-05 (CRITICAL) — Missing Authentication, Role Authorization, and Safe Tenant Derivation
- **Provenance:** `S-002`
- **Cited Evidence:** `openapi.yaml` lines 7–8, 80–82, 134–168; `10-technology-stack-and-decisions.md` §4 line 44; `prompt_draft.md` R2.
- **Consequence:** Without FastAPI dependency-injected Bearer JWT authentication and RBAC checks (`Owner`, `FinancePayroll`), endpoints are unauthenticated or allow client-supplied headers (e.g. `X-Tenant-Id`) to dictate tenant context, allowing complete ledger tampering.
- **Required Closure:** Mandate FastAPI dependencies validating Bearer JWT and enforcing roles `Owner` or `FinancePayroll`. Derive `tenant_id` passed to `set_request_context` strictly from verified token claims; treat client tenant headers strictly as non-authoritative filters. Add Acceptance Criteria: unauthenticated requests return 401 (`AUTH_REQUIRED`), unauthorized roles return 403 (`FORBIDDEN`).
- **Validation:** Automated tests asserting 401 on missing token, 403 on non-financial role (e.g. `Tailor`), and 200/201 on valid `Owner`/`FinancePayroll` credentials.

---

### 4.2. Major Blocking Defects (`BLOCKING_DEFECT`)

#### DEFECT-06 (MAJOR) — Schema and Semantic Contradiction on `GET /api/v1/ledger/entries`
- **Provenance:** `B-005`, `C-001`, `C-006`
- **Cited Evidence:** `openapi.yaml` lines 158–168, lines 854–856; `prompt_draft.md` R2.
- **Consequence:** Prompt describes the endpoint as returning "scoped ledger lines", but OpenAPI 3.1 contract mandates returning `LedgerPage` containing `items: List[LedgerTransaction]` (with nested `entries`) and `nextCursor: Optional[str]`. Returning flat lines breaks OpenAPI schema compliance.
- **Required Closure:** Clarify R2 to state: `GET /api/v1/ledger/entries` returns `LedgerPage` containing `items: List[LedgerTransaction]` (each containing nested `entries`) and cursor query parameters (`cursor: Optional[str]`, `pageSize: int = 50 (max 100)`). Add an acceptance criterion verifying read-path pagination and tenant isolation.
- **Validation:** Schemathesis / pytest test asserting response structure matches `LedgerPage` schema and cursor pagination works correctly.

#### DEFECT-07 (MAJOR) — Reversal Endpoint Parameter Inconsistency and Omission of Request Body
- **Provenance:** `B-011`, `C-002`
- **Cited Evidence:** `openapi.yaml` lines 146–157, line 855; `prompt_draft.md` R2 & Acceptance Criteria.
- **Consequence:** Acceptance criteria uses `{id}` while OpenAPI and R2 use `{transactionId}`. The prompt omits the required `ReversalRequest` body (`{"reason": "string"}`), causing 422 Unprocessable Entity errors when called by standard OpenAPI clients.
- **Required Closure:** Standardize parameter name to `{transactionId}` across R2 and Acceptance Criteria. Specify that `POST /api/v1/ledger/transactions/{transactionId}/reversals` requires request body `ReversalRequest` with mandatory `reason: str`.
- **Validation:** Automated test confirming reversal endpoint accepts `ReversalRequest` JSON payload and succeeds.

#### DEFECT-08 (MAJOR) — Reversal Invariants: Double-Reversal Prevention, Direction Inversion, and Chained Reversal Prohibition
- **Provenance:** `B-004`
- **Cited Evidence:** `11-database-schema-spec.md` §5 line 87; `openapi.yaml` line 154; `prompt_draft.md` R1, R2.
- **Consequence:** Without partial unique index on `reversal_of`, transactions can be reversed repeatedly, duplicating debits/credits. Without specifying entry direction inversion, original entries could be copied without flipping `DEBIT <-> CREDIT`.
- **Required Closure:**
  1. Add partial unique index: `CREATE UNIQUE INDEX ON ledger_transactions (tenant_id, reversal_of) WHERE reversal_of IS NOT NULL;`.
  2. Mandate direction inversion: for each original entry, insert matching account and amount with flipped direction (`DEBIT <-> CREDIT`).
  3. Disallow reversing a transaction that is already a reversal (`reversal_of IS NOT NULL`).
  4. Add Acceptance Criteria: duplicate reversal returns 409 Conflict; reversal of a reversal returns 400/409 error.
- **Validation:** Pytest tests verifying entry direction inversion (`sum(original + reversal) == 0`), 409 on duplicate reversal, and rejection of reversing a reversal.

#### DEFECT-09 (MAJOR) — Missing Empty-Transaction Rejection via Deferred Constraint Trigger on Transaction Header
- **Provenance:** `B-003`
- **Cited Evidence:** `11-database-schema-spec.md` §5 line 87; `prompt_draft.md` R1 & Acceptance Criteria.
- **Consequence:** Attaching the deferred balance trigger only to `ledger_entries` allows an empty transaction header with zero lines to commit successfully, corrupting journal sequences.
- **Required Closure:** Bind the deferred constraint trigger evaluated at `COMMIT` to `ledger_transactions` (or both header and entries), asserting that every header has $\ge 1$ debit and $\ge 1$ credit line. Add an Acceptance Criterion checkbox verifying that committing an empty transaction raises an exception and rolls back.
- **Validation:** Pytest test attempting to commit a transaction header without entries, asserting database trigger exception and complete rollback.

#### DEFECT-09B (MAJOR) — Table Check Constraints on Entry Amounts and Directions
- **Provenance:** `B-009`
- **Cited Evidence:** `11-database-schema-spec.md` §4 line 53; `openapi.yaml` line 853; `prompt_draft.md` R1.
- **Consequence:** Without `CHECK (amount_minor > 0)` and `CHECK (direction IN ('DEBIT', 'CREDIT'))`, negative or zero entries could satisfy mathematical balance, corrupting financial reporting.
- **Required Closure:** Explicitly mandate `CHECK (amount_minor > 0)` and `CHECK (direction IN ('DEBIT', 'CREDIT'))` in R1 schema requirements for `ledger_entries`.
- **Validation:** Automated test attempting to insert `amount_minor <= 0` or invalid direction, asserting database constraint violation.

#### DEFECT-10 (MAJOR) — Account Code Resolution and Inactive Account Guardrails
- **Provenance:** `B-007`, `C-007`
- **Cited Evidence:** `openapi.yaml` lines 852–853; `11-database-schema-spec.md` §4 line 51; `prompt_draft.md` R2.
- **Consequence:** `LedgerRequest` accepts `accountCode: str`, but `ledger_entries` stores `account_id uuid`. Missing resolution logic or failing to filter by `tenant_id` and `active = true` produces unhandled 500 errors or cross-tenant account references.
- **Required Closure:** Mandate in R2 that the service resolves `accountCode` against `ledger_accounts` filtered by active `tenant_id`, verifying `active = true` and currency match. Non-existent, cross-tenant, or inactive accounts must return RFC 7807 problem response (status 400/422, code `VALIDATION_ERROR`).
- **Validation:** Pytest tests verifying valid resolution, 400/422 on non-existent account, and 400/422 on inactive account.

#### DEFECT-11 (MAJOR) — Missing RFC 7807/9457 `application/problem+json` Error Envelopes and Sanitized Audit Recovery
- **Provenance:** `S-006`, `C-004`
- **Cited Evidence:** `openapi.yaml` lines 828–842; `11-database-schema-spec.md` §9 line 151; `12-api-contract-plan.md` §2; `prompt_draft.md` R2.
- **Consequence:** Default FastAPI exception handling returns `{ "detail": ... }` in `application/json`, violating `openapi.yaml`. Raw database exceptions leak internal schema details, table names, and stack traces. Rolled-back transactions discard in-transaction audit rows, leaving no audit trail of malicious attempts without post-rollback logging.
- **Required Closure:**
  1. Add centralized FastAPI exception handlers mapping database integrity errors, triggers (`LEDGER_IMMUTABLE`), and idempotency conflicts to `application/problem+json` conforming to `Problem` schema (with `code`, `detail`, `instance`, `requestId`).
  2. Mandate post-rollback security logging to a sanitized log stream for aborted transactions.
- **Validation:** Automated test asserting `content-type: application/problem+json` and schema compliance on error responses, with no leaked SQL or stack traces.

#### DEFECT-12 (MAJOR) — Canonical JSON Hashing and Concurrent Idempotency Race Handling
- **Provenance:** `B-008`
- **Cited Evidence:** `11-database-schema-spec.md` §5 line 93; `prompt_draft.md` R2.
- **Consequence:** Non-canonical JSON serialization causes identical payloads with reordered keys or whitespace variations to produce different SHA-256 hashes, falsely triggering 409 Conflict. Simultaneous requests with the same key crash on unhandled database unique constraint errors.
- **Required Closure:** Mandate RFC 8785 / sorted-key compact UTF-8 JSON encoding before SHA-256 hashing. Specify that concurrent in-flight requests either await the active transaction lock or return a retryable 409 Conflict with Problem code `IDEMPOTENCY_CONFLICT`.
- **Validation:** Pytest tests with reordered payload keys verifying successful replay, and concurrent requests verifying no 500 crashes.

#### DEFECT-13 (MAJOR) — Undefined Directory Layout and Dependency Specifications
- **Provenance:** `C-005`
- **Cited Evidence:** `prompt_draft.md` working directory; `10-technology-stack-and-decisions.md` §2; `18-parallelization-and-workstreams.md` §4 Dev 3 brief.
- **Consequence:** Omitting directory layout and dependency boundaries leads to ad-hoc monolithic file structures that conflict with future workstreams (Dev 1, Dev 2, Dev 4).
- **Required Closure:** Standardize layout under `backend/`:
  - `backend/app/api/v1/` (FastAPI routers)
  - `backend/app/core/` (database engine, session, pool event hooks, request context)
  - `backend/app/db/migrations/` (plain SQL migrations M001, M008, M011, M012)
  - `backend/app/models/` (SQLAlchemy models)
  - `backend/app/schemas/` (Pydantic v2 schemas matching `openapi.yaml`)
  - `backend/app/services/` (ledger posting, balancing, idempotency hashing)
  - `backend/tests/test_ledger.py`
  - Minimal boring dependencies: Python 3.11+, `fastapi`, `uvicorn`, `pydantic>=2.0`, `sqlalchemy>=2.0`, `psycopg[binary]>=3.1`, `pytest`, `httpx`.
- **Validation:** Directory layout inspection and `pyproject.toml` dependency verification.

#### DEFECT-14 (MAJOR) — Zero-Direct-DML Runtime Role and Database Function Security Hardening
- **Provenance:** `B-002`, `S-005`
- **Cited Evidence:** `11-database-schema-spec.md` §5 lines 75, 87; §9 lines 146, 151; `prompt_draft.md` R1.
- **Consequence:** Granting direct `INSERT`/`UPDATE`/`DELETE` to application roles violates least privilege. Functions defined without `SECURITY DEFINER SET search_path = pg_catalog, public` are vulnerable to search-path hijacking.
- **Required Closure:**
  1. Revoke direct `UPDATE` and `DELETE` on ledger tables from the application role; rely on database triggers as defense-in-depth.
  2. Implement `set_request_context` and `append_ledger_transaction` with `SECURITY DEFINER SET search_path = pg_catalog, public` and no dynamic SQL.
  3. Revoke `PUBLIC` execute permissions, granting execution strictly to `lukla_app`.
- **Validation:** Migration DDL verification asserting `SET search_path` and privilege grants.

---

### 4.3. Learn Notes (`LEARN_NOTE`)

- **NOTE-01:** Chart of Accounts Seeding: Ensure standard operational accounts (`CUSTODIAL_MATERIAL`, `CUSTODIAL_OBLIGATION`, `RAW_MATERIAL_ASSET`, `ACCOUNTS_PAYABLE`, `WIP_DIRECT_LABOR`, `WAGES_PAYABLE`) are pre-seeded in migration M008 or test fixtures per tenant.
- **NOTE-02:** Idempotency Retention Policy: Long-term TTL and purge routines are pending business policy and appropriately excluded from this core double-entry milestone.

---

## 5. Review Verdict and Remediations

### Verdict: `NEEDS_REVISION`
**Rationale:** The implementation plan draft outlines an essential foundation, but contains 5 Critical and 9 Major blocking defects spanning schema omissions (`idempotency_records`, composite FKs, `FORCE RLS`), OpenAPI contract discrepancies (`GET /ledger/entries`, `ReversalRequest`, RFC 7807 Problem format), security boundaries (Bearer auth, connection pool reset hooks), and accounting invariants (direction inversion, empty header rejection).

### Required Remediations for Resubmission

The Primary / Planning Agent must revise `prompt_draft.md` to incorporate the following exact specifications:

1. **R1 Schema & Migrations Update:**
   - Include tables: `tenants`, `actors`, `ledger_accounts`, `ledger_transactions`, `ledger_entries`, and `idempotency_records`.
   - Apply `ENABLE ROW LEVEL SECURITY` and `FORCE ROW LEVEL SECURITY` with explicit `app.tenant_id` policies on all tenant tables.
   - Mandate composite foreign keys: `(tenant_id, transaction_id)` and `(tenant_id, account_id)` on `ledger_entries`.
   - Enforce check constraints on `ledger_entries`: `CHECK (amount_minor > 0)` and `CHECK (direction IN ('DEBIT', 'CREDIT'))`.
   - Add partial unique index on `ledger_transactions(tenant_id, reversal_of) WHERE reversal_of IS NOT NULL`.
   - Bind deferred balance constraint trigger evaluated at `COMMIT` to `ledger_transactions` to reject empty headers as well as unbalanced entries.
   - Harden functions (`set_request_context`, `append_ledger_transaction`) with `SECURITY DEFINER SET search_path = pg_catalog, public`.

2. **R2 API & Service Update:**
   - Enforce Bearer JWT authentication and RBAC (`Owner`, `FinancePayroll`). Derive tenant context strictly from verified token claims.
   - Enforce connection pool lifecycle hooks (`checkout`/`checkin`) executing `DISCARD ALL` / `RESET ALL`, running transactions with `is_local = true`.
   - Align `GET /api/v1/ledger/entries` with `openapi.yaml`: return `LedgerPage` (`items: List[LedgerTransaction]`, `nextCursor: Optional[str]`) with query parameters `cursor` and `pageSize`.
   - Standardize reversal route to `POST /api/v1/ledger/transactions/{transactionId}/reversals` requiring `ReversalRequest` body (`reason: str`), flipping entry directions (`DEBIT <-> CREDIT`), and blocking reversals of reversals.
   - Implement RFC 8785 canonical JSON serialization before SHA-256 hashing; partition idempotency records by `(tenant_id, operation_id, key)`.
   - Add centralized FastAPI exception handlers returning `application/problem+json` conforming to `Problem` schema for all 4xx/5xx errors, with post-rollback sanitized audit logging.
   - Standardize layout under `backend/app/` with minimal standard dependencies.

3. **R3 Acceptance Criteria & Test Harness Update:**
   - Add checkbox for empty transaction rejection raising a database trigger exception and rolling back.
   - Add checkbox for composite foreign key cross-tenant account rejection.
   - Add checkbox for connection pool reuse asserting zero GUC context leakage across requests.
   - Add checkbox for unauthenticated (401) and unauthorized role (403) rejection.
   - Add checkbox for duplicate reversal rejection (409 Conflict) and inverted entry verification.
   - Add checkbox for `GET /api/v1/ledger/entries` pagination and tenant isolation matching `LedgerPage`.
   - Add checkbox for RFC 7807 `application/problem+json` error responses.

Once `prompt_draft.md` is updated with these specifications, resubmit for Review Round 2.
