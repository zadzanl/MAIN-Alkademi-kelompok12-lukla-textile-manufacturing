# 17 — Fenced Semantic-Search Module

**Change:** `lukla-ops-engine-planning`  
**Status:** PROPOSED / PLANNING ONLY / FEATURE-FLAGGED  
**Date:** 2026-10-14  
**Scope:** Phase B planning artifact. No application code, dependency installation, indexing run, provider call, or runtime conformance is claimed.

## 1. Purpose and boundary

The semantic-search module is an optional read-only extension for finding relevant operational documents, specifications, audit records, contracts, and documentation. It is not an operational command interface, workflow engine, accounting system, payroll calculator, or autonomous agent.

The module is fenced behind `AI_SEARCH_ENABLED`. When the flag is false, the search route is unavailable through the normal application capability check and no embedding, vector-store, or model-provider call is made. The module may be removed without changing ledger rows, ledger triggers, payroll outcomes, stock ownership, or audit-ledger integrity.

This document implements the approved architecture direction in `09-technical-blueprint-completion-plan.md` and `artifacts/tech_plan-blueprint-001.md`: provider-portable embeddings, `VectorStore` abstraction, PostgreSQL/pgvector as the day-one default, and a Qdrant pivot target.

## 2. Contract compatibility

The public boundary is the existing OpenAPI operation:

- `GET /search/operational-documents`
- `operationId: searchOperationalDocuments`
- Required query: `q` (1–500 characters)
- Optional query: `legalOwnerId` and `cursor`
- Response: `SearchPage` containing `PortalSearchResult[]` and nullable `nextCursor`
- Result fields currently guaranteed by the contract: `documentId`, `score`, `excerpt`, and optional `legalOwnerId`
- Declared roles: `Owner`, `SampleTeam`, `Warehouse`, `ProductionHead`, `FinancePayroll`, `MaklonClient`
- Declared views: `VIEW-01`, `VIEW-02`, `VIEW-03`, `VIEW-06`
- Declared invariant: tenant and legal-owner filters are mandatory; search cannot mutate the ledger

The module may add internal metadata, but it must not require clients to know the vector provider, embedding model, collection/table name, chunking strategy, or source-storage layout. Any future public contract change requires a contract review because it would change the reviewed Phase A baseline.

## 3. Trust boundary and authorization

### 3.1 Request flow

1. Authenticate the request using the application auth boundary.
2. Derive tenant, actor, role, legal-owner scope, and beneficiary scope from server-validated identity and grants. Caller-supplied tenant headers are not authorization.
3. Reject the request when `AI_SEARCH_ENABLED` is false, authentication is missing, or the caller lacks search capability.
4. Validate `legalOwnerId` against the caller's permitted legal-owner scope. A caller cannot widen scope by placing another owner ID in the query.
5. Execute retrieval with a mandatory tenant predicate and a legal-owner predicate. Apply beneficiary/order ACLs where a document is additionally restricted to an order beneficiary.
6. Hydrate only documents that remain authorized at read time. A vector hit is never proof of access.
7. Return contract-compatible excerpts and stable document IDs. Do not return hidden snippets, provider prompts, raw embeddings, ACL internals, or cross-scope existence signals.

### 3.2 Scope dimensions

Semantic search is limited to explicitly classified, authorized indexed documents. `getFileDownload`, `createFileUpload`, and `completeFileUpload` are operational file surfaces, not searchable sources by default. A file may enter the search corpus only after an explicit classification and ACL review; its projection must preserve tenant, legal-owner, order-beneficiary, source ACL/version, source ID, and checksum provenance. Unclassified or ACL-incomplete files remain excluded and are quarantined rather than searched.

The module keeps these dimensions separate:

- `tenant_id`: commercial/workspace boundary.
- `legal_owner_id`: legal owner of custodial or operational material/document scope.
- `order_beneficiary_id`: client entitled to a specific order/output.
- `actor_id` and role grants: caller capability and row-level scope.

Every indexed chunk stores enough scope metadata to filter before ranking. Documents with unknown or incomplete scope are not searchable by default; an ingestion validation failure quarantines them rather than widening visibility.

### 3.3 Deny and leakage rules

- Cross-tenant and cross-legal-owner queries return no unauthorized results and do not reveal whether a matching document exists.
- A denied `legalOwnerId` is treated as an authorization failure or empty scoped result according to the existing API error policy, but never as a provider/database error.
- Search does not bypass PostgreSQL RLS, `set_request_context(...)`, or application authorization.
- Service ingestion identity is separate from employee roles and cannot be used by the public search route.
- Search results are not used to authorize mutation, dispatch material, approve payroll, post ledger transactions, or alter audit history.

## 4. Internal module interfaces

The following are planning interfaces, not implementation code.

### 4.1 `EmbeddingsClient`

```text
embed(text: str, *, model: str, dimensions: int | None) -> EmbeddingVector
```

The client accepts one provider-neutral configuration shape:

- `AI_BASE_URL`: OpenAI-compatible API base URL.
- `AI_API_KEY`: secret supplied by the runtime secret manager; never stored in indexed content or returned in errors.
- `AI_EMBEDDING_MODEL`: configured model identifier.
- Optional dimensions and request timeout/retry policy.

OpenRouter is the compatible day-one provider target. The adapter must use the OpenAI-compatible embeddings protocol, but the module must not import OpenRouter-specific behavior into domain code. A later provider is selected by configuration and adapter conformance, not by changing search authorization or the public operation.

Embedding failures fail closed for ingestion. Query failures return an actionable service error without leaking provider details; no partial authorization decision is based on an embedding response.

### 4.2 `VectorStore`

```text
upsert(chunks: Iterable[IndexedChunk]) -> None
search(vector: EmbeddingVector, *, scope: SearchScope, limit: int, cursor: Cursor | None) -> SearchPage
remove(document_ids: Iterable[UUID]) -> None
```

`SearchScope` must contain tenant scope, legal-owner scope, optional beneficiary scope, and any source-type restrictions. The implementation must enforce these filters in the store query, not after an unrestricted top-k query.

The protocol is deliberately small: no ledger methods, no mutation of source operational tables, and no provider-specific query language exposed to callers.

### 4.3 Storage adapters

- **Day one:** PostgreSQL with `pgvector`, using ordinary PostgreSQL connectivity and a scoped vector table/index. Scope columns are stored beside each chunk so filtering is explicit and reviewable.
- **Pivot:** Qdrant Cloud or self-hosted Qdrant behind the same `VectorStore` protocol. Qdrant payload filters must represent the same tenant/legal-owner/beneficiary predicates.
- **Embedding provider:** OpenRouter-compatible OpenAI embeddings endpoint behind `EmbeddingsClient`; another OpenAI-compatible endpoint is a configuration pivot.

The application must not make both stores authoritative at once. During a migration or reindex, the selected store is explicit in configuration, and parity is checked before cutover. A failed index operation cannot change operational truth.

## 5. Ingestion and deletion lifecycle

### 5.1 Sources

Candidate sources include approved specifications, contracts, operational documentation, and audit-log projections. Raw payroll, ledger, or client-confidential content is not automatically indexed merely because it exists. Each source type requires an explicit allowlist and classification decision.

Ingestion is asynchronous or operator-triggered, separate from request-time search. It records source ID, document ID, version, tenant, legal owner, beneficiary restriction if applicable, classification, checksum, embedding model, and indexing status. Ingestion is idempotent by source/version/checksum.

Documents with missing tenant or legal-owner classification are quarantined. Deleting or revoking a source removes its chunks from the selected vector store and prevents future hydration; it does not delete or reverse ledger entries and does not rewrite the source audit history.

### 5.2 Deletion without ledger impact

Deletion is a search-index lifecycle action only:

1. Mark the index projection deleted or revoked.
2. Remove its chunks from `VectorStore`.
3. Invalidate caches and exclude the document from hydration.
4. Record an audit event for the search projection action where required by the audit policy.

The deletion path has no call to ledger append, ledger reversal, payroll, stock movement, or operational-document destruction. If the source is retained by the operational system, it remains intact. If the source itself must be deleted, that is a separate governed workflow and is not implied by semantic-search deletion.

## 6. Query behavior and safety

- Normalize and bound `q` according to the existing contract; reject empty or overlong input.
- Embed the query using the configured `EmbeddingsClient` only after authorization and feature-flag checks.
- Search with mandatory scope filters and a bounded result limit. Cursor pagination must be deterministic for a given index version and scope.
- Hydrate excerpts through an authorized repository/read model. Never trust text or ACL fields from a vector payload alone.
- Preserve result ordering and score semantics without exposing provider-specific score guarantees beyond the contract's numeric `score`.
- Log request correlation ID, tenant, actor, scope decision, index version, result count, latency, and error class. Do not log query text or document content by default where it could expose confidential data.
- Rate-limit and cap query cost; exact thresholds remain configurable and are not business approvals.

## 7. Observability and failure policy

Required operational signals are module-scoped: feature flag state, index version, ingestion failures, quarantine count, provider latency/error class, vector-store latency/error class, authorization-denial count, empty-result count, and deletion completion. Metrics must not contain raw document text, embeddings, API keys, or unredacted client secrets.

Failure behavior is fail-closed for authorization and scope resolution. Provider/vector-store outages must not fall back to an unfiltered store or direct database scan. If search is unavailable, the operational workflows continue without it because search is an extension module.

## 8. Verification plan and limits

Planning-time checks must verify:

- `operationId: searchOperationalDocuments` exists exactly once and the documented path/schema references resolve.
- Feature-disabled requests produce no provider or vector-store call in unit tests.
- Cross-tenant, cross-legal-owner, and beneficiary-restricted documents do not appear in results.
- A vector hit cannot bypass a second authorization check during hydration.
- Index deletion removes search visibility without ledger row mutation or reversal.
- pgvector and Qdrant adapters satisfy the same `VectorStore` contract using the same scope fixtures.
- OpenRouter-compatible embeddings are isolated behind `EmbeddingsClient`.

No runtime test is run by this planning task. PostgreSQL/Qdrant/OpenRouter integration, performance, red-team authorization tests, and production deployment remain future implementation gates.

## 9. Traceability and change control

- Architecture source: `09-technical-blueprint-completion-plan.md` decisions D-2 and D-4; §3 commitment 6.
- Interface source: `artifacts/contracts/openapi.yaml`, `searchOperationalDocuments`, `SearchPage`, and `PortalSearchResult`.
- Persistence/security source: `artifacts/10-technology-stack-and-decisions.md`, `artifacts/11-database-schema-spec.md`, and `artifacts/tech_plan-blueprint-001.md` contract conventions.
- Requirement context: `FR-3.1` is the contract source annotation; search remains an extension and does not expand BRD/PRD behavior.
- Business uncertainty source: `08-client-clarification-register.md`; unresolved legal, commercial, payroll, and QC questions are not answered by search configuration.

Any change to public operation IDs, paths, roles, response fields, ownership dimensions, or ledger isolation reopens the Phase A contract review. Any addition of an indexable data class requires a documented classification and access review.
