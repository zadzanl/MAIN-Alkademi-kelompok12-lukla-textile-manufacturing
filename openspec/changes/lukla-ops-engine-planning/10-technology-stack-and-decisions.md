# Phase A1 — Technology Stack and Portability Decisions

**Change:** `lukla-ops-engine-planning`  
**Task record:** revision 12 (2026-10-13)  
**Status:** contract proposal; not runtime implementation or deployment authorization.

## 1. Boundary and traceability

This artifact implements A1 of `09-technical-blueprint-completion-plan.md`. It is subordinate to the canonical BRD v2.3.0 (the filename retains `v2.2.1`), PRD v2.0, and `00-deconstruction.md` revision 4. It does not rewrite any of those documents.

The PRD inventory is **26 IDs**: the 23 child IDs `FR-1.1`, `FR-2.1`, `FR-3.1`, `FR-4.1..FR-4.3`, `FR-5.1..FR-5.2`, `FR-6.1..FR-6.3`, `FR-7.1..FR-7.4`, `FR-8.1..FR-8.2`, `FR-9.1..FR-9.2`, `FR-10.1..FR-10.4`, plus unresolved grouping/status IDs `FR-1.4`, `FR-5`, and `FR-6`. The source register's approved **20-ID traceability set**, copied from `artifacts/verify-traceability.ps1`, is `FR-1.1`, `FR-1.4`, `FR-2.1`, `FR-3.1`, `FR-4.1`, `FR-5`, `FR-6`, `FR-6.2`, `FR-7.1`, `FR-7.2`, `FR-7.3`, `FR-7.4`, `FR-8.1`, `FR-8.2`, `FR-9.1`, `FR-9.2`, `FR-10.1`, `FR-10.2`, `FR-10.3`, `FR-10.4`. This is a distinct checked set, not a count of every historical FR token in the register. `FR-1.4`, `FR-5`, and `FR-6` remain status-only and have no invented source behavior.

## 2. Decisions

| Area | Decision | Portable boundary | Explicit non-decision |
|---|---|---|---|
| API | FastAPI/Python, JSON over HTTPS, OpenAPI 3.1 contract | ASGI deployment and standard HTTP only | No provider-specific framework extension |
| Relational store | Plain PostgreSQL; Python owns workflows, database owns invariants | `DATABASE_URL`, SQL migrations, SQL/RLS/PL/pgSQL available on RDS, Neon, Supabase, or self-hosted PostgreSQL | No Supabase `auth.uid()` dependency |
| Tenant context | Validated actor context is installed with `set_config(..., true)`/`SET LOCAL` inside each transaction | PostgreSQL GUC names and policies are application-owned | Never trust a caller-supplied tenant header |
| Files | `StorageService` interface with object key, content hash, metadata, and short-lived download/upload capability | S3-compatible implementation; local test implementation allowed | No direct AWS SDK calls in domain code |
| Vectors | `VectorStore` interface; pgvector is an optional same-Postgres adapter, Qdrant an external adapter | adapter receives an already-authorized tenant/legal-owner scope | Search is read-only and cannot write the ledger |
| Models | `EmbeddingsClient` and chat/provider adapter behind configurable base URL | OpenAI-compatible HTTP shape permits OpenRouter or another provider | No model name, price, or CVE claim is frozen here |
| Web | Responsive Next.js PWA, `output: standalone` | standard browser APIs; Vercel, CloudFront/Amplify, or a container can host it | No Edge-only, ISR-write, or Vercel-only API |
| Jobs | Internal authenticated HTTP job endpoints | AWS Scheduler invokes Lambda, Lambda POSTs the endpoint; other platforms use an external scheduler | No in-process cron and no claim that Scheduler directly targets arbitrary HTTP |
| Test | pytest/database checks, Schemathesis contract checks, Playwright browser checks | JSON/JUnit/XML evidence contract; deterministic exit status | Tools are future implementation gates, not run in Phase A |

## 3. AWS-first deployment shape

Day-one deployment may use ECS Express Mode/Fargate, plain PostgreSQL on RDS, S3, a standard browser host, and EventBridge Scheduler. The design does not require NAT: private-subnet egress, VPC endpoints, public/private topology, and cost controls are deployment decisions for Phase B/C. No speculative versions, prices, or security advisories are pinned.

The scheduler boundary is:

```text
EventBridge Scheduler -> Lambda target -> HTTPS POST /internal/jobs/{job}
  -> authenticated service scope + Idempotency-Key -> one database transaction
```

The Lambda-to-API call uses a dedicated service credential or mTLS-backed service identity, not an employee role and not a user JWT. The same endpoint shape works with GitHub Actions, FastAPI Cloud external scheduling, or another scheduler.

## 4. Security and portability rules

1. The API authenticates the actor, resolves allowed client/legal-owner/beneficiary scopes, and sets all three scopes transaction-locally. `tenant_id` is access scope; `legal_stock_owner_id` is legal title/custody; `order_beneficiary_id` is the party entitled to order output. They are never silently copied into one field.
2. PostgreSQL application connections use a non-owner role with no `BYPASSRLS`. Tenant-scoped tables use RLS and `FORCE ROW LEVEL SECURITY`; transaction pooling must not leak GUC values between requests.
3. An administrative cross-client operation requires an explicit authorized capability and an audited scope set. `X-Tenant-Id`, `client_id`, and similar request values are filters, never authorization.
4. Ledger, stock, wage, QC, and idempotency invariants are checked again at commit under row locks/unique constraints. API validation is convenience, not the trust boundary.
5. Financial rules are configurable but unresolved rules carry `FINANCIAL_RULE_PENDING` and block production payroll approval. Demo defaults are not approvals.

## 5. Phase A exit criteria

The database artifact may name concrete objects against this vocabulary. The API artifact may reference only those objects and stable public concepts. A later artifact may refine authentication details, hosting, or adapter internals only through a contract change record; it must not change operation IDs, error codes, or ownership semantics silently.
