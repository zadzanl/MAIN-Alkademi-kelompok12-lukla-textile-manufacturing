# Original User Request

## 2026-10-14T06:26:57Z

This is a single self-contained fix; keep it small and focused.

Implement the production backend and database engine for the Immutable Double-Entry Core of the Lukla Operations Engine under `backend/app/`. The engine provides append-only financial and multi-tenant inventory sub-ledger accounting to prevent cross-contamination of custodial client fabric (CMT maklon) and eliminate manual piece-rate payroll reconciliation.

Working directory: `c:\Projects\hackathon-MAIN-alkademi`
Integrity mode: development

## Requirements

### R1. Database Schema, Migration & Invariant Hardening (PostgreSQL)
Establish the foundational schema (`tenants`, `actors`), runtime idempotency table (`idempotency_records`), audit event table (`audit_events`), and core ledger tables (`ledger_accounts`, `ledger_transactions`, `ledger_entries`) using standard sequential migrations under `backend/migrations/` (`001_identities.sql` and `008_double_entry_ledger.sql`):
- **Multi-Tenant Composite Keys & Foreign Keys:** Enforce composite primary keys `(tenant_id, id)` and composite foreign keys on `ledger_entries ((tenant_id, transaction_id) REFERENCES ledger_transactions(tenant_id, id))` and `((tenant_id, account_id) REFERENCES ledger_accounts(tenant_id, id))` to prevent cross-tenant account contamination at the relational level.
- **Strict Immutability:** Disallow in-place `UPDATE` and `DELETE` on posted transactions and entries via PL/pgSQL triggers raising `LEDGER_IMMUTABLE`. Revoke direct `UPDATE` and `DELETE` table privileges from the runtime application role (`lukla_app`). Late-line insertions across database transactions are strictly blocked by checking `created_xid == pg_current_xact_id()`.
- **Zero-Sum Mathematical Balancing & Non-Empty Headers:** Enforce that every transaction strictly balances ($\sum \text{Debits} \equiv \sum \text{Credits}$) per tenant and currency using a deferred constraint trigger evaluated at `COMMIT` on `ledger_transactions`. The trigger must also reject empty transaction headers ($\ge 1$ debit and $\ge 1$ credit required).
- **Table Check Constraints:** Enforce `CHECK (amount_minor > 0)` and `CHECK (direction IN ('DEBIT', 'CREDIT'))` on `ledger_entries`.
- **Compensating Reversals Invariant:** Support forward-only reversals referencing `reversal_of uuid`. Enforce a partial unique index on `ledger_transactions (tenant_id, reversal_of) WHERE reversal_of IS NOT NULL` to prevent duplicate reversals. Forbid reversing an existing reversal transaction.
- **Row Level Security (RLS) & Security Definer:** Apply `ENABLE ROW LEVEL SECURITY` and `FORCE ROW LEVEL SECURITY` on all tenant-scoped tables (`ledger_accounts`, `ledger_transactions`, `ledger_entries`, `idempotency_records`, `audit_events`) with policies reading `current_setting('app.tenant_id', true)`. Harden all stored procedures (`set_request_context`, `append_ledger_transaction`) with `SECURITY DEFINER SET search_path = pg_catalog, public` and zero dynamic SQL.
- **Idempotency & Audit Schemas:**
  - Create `idempotency_records (id, tenant_id, key, operation_id, canonical_payload_hash, status, response_status, response_body, created_at, completed_at)` with unique constraint `(tenant_id, operation_id, key)`.
  - Create `audit_events (id, tenant_id, actor_id, service_principal, action, entity_type, entity_id, request_id, payload, occurred_at)` with index on `(tenant_id, entity_type, entity_id)`.
- **Seeded Operational Accounts:** Seed the 6 canonical accounts per tenant (`CUSTODIAL_MATERIAL`, `CUSTODIAL_OBLIGATION`, `RAW_MATERIAL_ASSET`, `ACCOUNTS_PAYABLE`, `WIP_DIRECT_LABOR`, `WAGES_PAYABLE`).

### R2. Core Ledger Service & OpenAPI Endpoints (FastAPI)
Implement the service layer and REST API conforming strictly to `openspec/changes/lukla-ops-engine-planning/contracts/openapi.yaml` under `backend/app/` using minimal dependencies (`fastapi`, `uvicorn`, `pydantic>=2.0`, `sqlalchemy>=2.0`, `psycopg[binary]>=3.1`, `pytest`, `httpx`):

```text
backend/
├── app/
│   ├── api/v1/          # FastAPI routers (ledger.py)
│   ├── core/            # Database engine, session, pool hooks (database.py), auth context (auth.py)
│   ├── models/          # SQLAlchemy ORM models (ledger.py, idempotency.py, audit.py)
│   ├── schemas/         # Pydantic v2 schemas matching openapi.yaml (ledger.py, problem.py)
│   ├── services/        # Business logic: posting, balancing, reversals, idempotency
│   └── main.py          # FastAPI application entrypoint and exception handlers
├── migrations/          # Sequential plain SQL migrations (001_identities.sql, 008_double_entry_ledger.sql)
└── tests/
    └── test_ledger.py   # Deterministic pytest verification suite
```

- **Authentication, RBAC & Context Derivation:** Enforce Bearer JWT authentication on all ledger endpoints pinning `algorithms=["HS256"]`. Authorize only `Owner` and `FinancePayroll` roles. Derive `tenant_id` and caller scopes strictly from verified token claims; never trust caller-supplied tenant headers.
- **Connection Pool Hygiene:** Implement database connection checkout/checkin lifecycle hooks in `backend/app/core/database.py` that execute `DISCARD ALL` / `RESET ALL` on release, ensuring transaction-local GUCs (`SET LOCAL app.tenant_id = :tenant_id, is_local = true`) never leak across pooled connections.
- **`POST /api/v1/ledger/transactions` (`appendLedgerTransaction`):**
  - Resolve incoming `accountCode` strings to valid, active accounts (`active = true`) matching the transaction currency within the caller's tenant. Map account resolution errors to HTTP `400 Bad Request` with `code: VALIDATION_ERROR` conforming to OpenAPI line 145.
  - Serialize request payload using RFC 8785 canonical JSON sorting before computing SHA-256 hash.
  - Reserve `Idempotency-Key` in `idempotency_records` within the same database transaction under `operation_id = 'appendLedgerTransaction'`. On key collision with matching hash, return stored response; on mismatched hash, return `409 Conflict`. Recheck caller authorization even on idempotent replays. Handle unblocking concurrent transactions cleanly by reading committed responses.
  - Atomically execute `append_ledger_transaction`, record audit event in `audit_events`, and return `201 Created` with `LedgerTransaction` schema.
- **`POST /api/v1/ledger/transactions/{transactionId}/reversals` (`reverseLedgerTransaction`):**
  - Accept `transactionId` in path, header `Idempotency-Key`, and `ReversalRequest` body (`reason: str`) per OpenAPI contract (line 155).
  - Check idempotency in `idempotency_records` under `operation_id = 'reverseLedgerTransaction'`. On key collision with matching hash, return stored response; on mismatched hash, return `409 Conflict`.
  - Fetch original transaction within tenant; reject with `404 Not Found` if missing, or `409 Conflict` if already reversed or if the target is itself a reversal.
  - Construct a new balanced compensating transaction with inverted directions (`DEBIT <-> CREDIT`) and positive amounts, setting `reversal_of = transactionId`, record audit event, and commit atomically, returning `201 Created`.
- **`GET /api/v1/ledger/entries` (`getLedgerEntries`):**
  - Read ledger transactions for the caller's tenant supporting cursor pagination (`cursor: Optional[str]`, `pageSize: int = 50`).
  - Return `200 OK` conforming to `LedgerPage` (`items: List[LedgerTransaction]`, `nextCursor: Optional[str]`).
- **Error Handling & Audit Recovery:**
  - Standardize error responses to RFC 7807/9457 `application/problem+json` matching the OpenAPI `Problem` schema without exposing database traces.
  - Emit sanitized security audit log entries on rejected transactions outside the aborted business transaction.

### R3. Deterministic Verification Test Harness
Provide an automated test suite in `backend/tests/test_ledger.py` that executes directly against PostgreSQL using unprivileged role (`lukla_app`) connection fixtures to verify all invariants:
- **Zero-Sum Balance & Non-Empty Headers:** Unbalanced transactions (e.g. Debit 1,000, Credit 999) and empty transaction headers fail trigger checks and roll back completely.
- **Account Code Validation (Negative Controls):**
  - Unknown `accountCode` strings return HTTP 400 RFC 7807 problem response (`VALIDATION_ERROR`) and roll back.
  - Inactive accounts (`active = false`) return HTTP 400 RFC 7807 problem response (`VALIDATION_ERROR`) and roll back.
  - Mismatched currencies between entry and account return HTTP 400 RFC 7807 problem response (`VALIDATION_ERROR`) and roll back.
- **Composite Foreign Key Isolation:** Attempting to insert an entry linking Tenant A's transaction to Tenant B's account fails database composite FK validation.
- **Strict Immutability:** Direct SQL `UPDATE` or `DELETE` on `ledger_transactions` or `ledger_entries` raises `LEDGER_IMMUTABLE`.
- **Late-Line Insertion Block:** Attempting to append an entry to a previously committed transaction fails transaction ID checking (`created_xid`).
- **Connection Pool Leak Protection:** Reusing a connection across requests with different tenants confirms that `app.tenant_id` resets and does not leak cross-tenant rows.
- **Authentication & RBAC:** Unauthenticated requests return `401 Unauthorized`; non-finance/owner roles return `403 Forbidden`.
- **Idempotency Replay & Conflict (Posting & Reversals):**
  - Posting replay with identical key/payload returns cached response; replay with mismatched payload returns `409 Conflict`.
  - Reversal replay with identical key/payload returns cached `201 Created` response without duplicate reversal transactions; replay with mismatched payload returns `409 Conflict`.
- **Compensating Reversals:** Reversal exactly mirrors original lines with inverted directions (`DEBIT <-> CREDIT`); duplicate reversal returns `409 Conflict`; reversing a reversal is rejected.
- **Pagination & Contract Conformity:** `GET /api/v1/ledger/entries` returns valid `LedgerPage` with working cursor pagination and RFC 7807 problem responses on errors.

## Acceptance Criteria

### Mathematical Balance & Database Invariants
- [ ] Every transaction commit verifies $\sum \text{Debits} == \sum \text{Credits}$ per currency and tenant; unbalanced transactions raise a database exception and roll back.
- [ ] Attempting to commit an empty transaction header without lines raises an explicit database trigger exception.
- [ ] Direct SQL `UPDATE` or `DELETE` on `ledger_transactions` or `ledger_entries` raises `LEDGER_IMMUTABLE`.
- [ ] Appending lines after transaction commit fails due to mismatched `created_xid`.
- [ ] Entries with non-positive amounts (`amount_minor <= 0`) or invalid direction strings fail table check constraints.

### Multi-Tenant Boundary & Connection Pool Safety
- [ ] Composite foreign keys `(tenant_id, transaction_id)` and `(tenant_id, account_id)` reject cross-tenant references at the relational layer.
- [ ] `ENABLE ROW LEVEL SECURITY` and `FORCE ROW LEVEL SECURITY` are active on all tenant tables (`ledger_accounts`, `ledger_transactions`, `ledger_entries`, `idempotency_records`, `audit_events`); unauthorized tenant queries return 0 rows.
- [ ] Reusing pooled connections across distinct tenants demonstrates zero GUC leakage after `RESET ALL`.

### Account Code Resolution & Audit Persistence
- [ ] Attempting to post entries referencing unknown account codes, inactive accounts (`active = false`), or mismatched currencies returns HTTP 400 RFC 7807 problem response (`VALIDATION_ERROR`) and rolls back.
- [ ] Posting and reversal transactions persist an associated `audit_events` row within the same ACID transaction.

### API & Workflow Conformance
- [ ] Unauthenticated requests return `401`; non-finance/owner roles return `403`.
- [ ] `POST /api/v1/ledger/transactions` returns `201 Created` with valid `LedgerTransaction`.
- [ ] Replaying an identical `Idempotency-Key` on transaction posting returns the stored response without duplicate journal writes; payload alterations return `409 Conflict`.
- [ ] `POST /api/v1/ledger/transactions/{transactionId}/reversals` requires header `Idempotency-Key` and `ReversalRequest` body; replaying identical reversal returns stored `201 Created` without duplicating records; payload alterations return `409 Conflict`.
- [ ] Reversal creates a newly balanced transaction with inverted entries referencing `reversal_of`; re-reversing returns `409 Conflict`; reversing a reversal is rejected.
- [ ] `GET /api/v1/ledger/entries` conforms to `LedgerPage` cursor pagination and tenant scoping.
- [ ] Error responses strictly conform to RFC 7807 `application/problem+json` (`Problem` schema).
- [ ] All tests in `backend/tests/test_ledger.py` execute using unprivileged `lukla_app` test fixtures and pass cleanly with exit code 0.
