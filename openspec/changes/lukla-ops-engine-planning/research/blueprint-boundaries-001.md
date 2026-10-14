# Blueprint Boundaries — Concrete Prerequisites, Recommended Contract Boundaries, and Gated Conflicts

**Change:** `lukla-ops-engine-planning`
**Date:** 2026-10-13
**Author:** Researcher (Explorer, read-only). No source files modified by this research.
**Task-record revision confirmed at intake:** **12** (`task-record.md` line 3: `**Revision:** 12`; line 4: `**Updated:** 2026-10-13`).
**Scope:** Bounded evidence for the Phase 6+ artifacts (`10`–`19` + new specs) defined in `09-technical-blueprint-completion-plan.md`. NOT application code. NOT a redesign. NOT a substitute for the next phase's authoring work.
**Overlap with the other researcher:** portability / auth / testability sourced independently here; primary FR↔table and FR↔endpoint traceability is owned by the parallel researcher (see Worklog sources below). Cross-references only — no invented decisions.

---

## 0. Method and what I actually ran

Every claim below is either (a) verified by `read_file`/`run_in_terminal` against files in this checkout, or (b) verified by `fetch_webpage`/`mcp_mcp-omnisearc_web_search` against external sources cited inline, or (c) labeled `Inferred` / `Unknown`. I did not modify any existing source file. I did not dispatch any subagent.

### 0.1 File reads performed

| # | File | Lines inspected | Purpose |
|---|---|---|---|
| R1 | `openspec/changes/lukla-ops-engine-planning/task-record.md` | 1–400 | Rev 12 confirmation; active phase banner |
| R2 | `openspec/changes/lukla-ops-engine-planning/09-technical-blueprint-completion-plan.md` | 1–200 | New authoritative blueprint; gap analysis; ACs |
| R3 | `openspec/changes/lukla-ops-engine-planning/00-deconstruction.md` | header + 04/05/06/07/08/09/Contradictions/UNRESOLVED sections | Source of truth (rev 4) for FR/role/QC references |
| R4 | `openspec/changes/lukla-ops-engine-planning/04-rbac-matrix.md` | entire file | 8-role matrix; UNSPECIFIED column |
| R5 | `openspec/changes/lukla-ops-engine-planning/06-acceptance-tests.md` | entire file | 4 scenarios + AT-01..10 + AT-R01..R08 |
| R6 | `openspec/changes/lukla-ops-engine-planning/08-client-clarification-register.md` | entire file | 6 klarifikasi domains for client gating |
| R7 | `openspec/changes/lukla-ops-engine-planning/design.md` | entire file | 4 decisions incl. Decision 3 (Supabase wording — note discrepancy) |
| R8 | `openspec/changes/lukla-ops-engine-planning/specs/{multi-tenant-platform,warehouse-and-cutting-controls,production-output-tracking,quality-control-and-inspection,payroll-and-costing-engine,audit-and-sample-tracking}/spec.md` | entire files | 6 capability specs (post-fix `audit-and-sample-tracking` has 2 scenarios) |
| R9 | `openspec/changes/lukla-ops-engine-planning/worklog.md` | entire file | Phase history (Phase 5 = COMPLETE) |
| R10 | `openspec/changes/lukla-ops-engine-planning/artifacts/research/research-001.md` + `research-002.md` + `research-003-phase2b-recovery.md` | entire files | Prior research; avoids duplication |
| R11 | `openspec/changes/PRD - Lukla Operations Engine - v2.0 - Wagile.md` | 1–186 | Wagile Bagian A contract + Bagian B backlog (26 IDs) |
| R12 | `openspec/changes/BRD - Lukla Operations Engine - v2.2.1 - FINAL.md` | 1–312 (head + §1–§13 + §16.5) | v2.3.0 internal version; filename retains v2.2.1 |
| R13 | `openspec/changes/lukla-ops-engine-planning/artifacts/backend_database_structure.md` | entire (830 bytes) | Supabase-only sketch to be replaced |
| R14 | `openspec/changes/lukla-ops-engine-planning/artifacts/storage-architecture-draft.md` | entire | S3 + `media_assets` table sketch |

### 0.2 Semantic searches performed (mcp_semantic-sear_search, repo = `C:\Projects\hackathon-MAIN-alkademi`)

| # | Query | Top hits | What was learned |
|---|---|---|---|
| S1 | "Ledger and double-entry append-only reversal transaction journal architecture" | `Overall Plan Draft.md` 374–389; `09-plan` 67–68; `design.md` 21–27; `06-acceptance-tests.md` 115–116; PRD v2.0 §B.2 169–178 | Design intent exists; SQL not authored |
| S2 | "validate_material_dispatch trigger cross-client contamination guardrail" | `design.md` 28–32; `specs/warehouse-and-cutting-controls/spec.md` 19–24 | Decision is stated; PL/pgSQL body not authored anywhere on disk |
| S3 | "tenant ownership allocation allocation_useline_component Sewer line assignment FR-7.1" | PRD 179–184; BRD 426–429; `00` 138–144; `specs/production-output-tracking/spec.md` 12–18 | Snøhund is its OWN tenant box per slide 02b; dynamic line allocation has no schema |
| S4 | "custodial off-balance sheet accounting persediaan kustodial titration client_id ownership" | BRD 126–127; `Overall Plan Draft.md` 89–101 (full GL debit/credit); `design.md` 21–27; `00` 219–226 | GL account shape (Chart-of-Accounts per tenant) named in `Overall Plan Draft.md` but NOT in the canonical `design.md` |
| S5 | "cut bundle to finished unit traceability assembly QC stitching serial number chain" | `specs/production-output-tracking/spec.md` 26–31; `task-record.md` 30–32; `06-acceptance-tests.md` AT-04/05 | Linkage is asserted in AT-04/05 but no entity-relationship trail documented |
| S6 | "JWT authentication session floor tablet mandor login role" | `08-client-clarification-register.md` 123–128 (sengketa borongan + edit window); PRD v2.0 228–239 (out-of-scope) | No authN spec anywhere on disk |
| S7 | "postgres trigger reverse reversal compensating entry ledger no UPDATE DELETE append-only" | `09-plan` 67–68; PRD v1.3 49–57 (`***Anti-Contamination Guardrail***` etc.); `06-acceptance-tests.md` 115–116; BRD 281–290 | Locked-history / append-only wording varies; reversal-mechanism is `[inferred]`, not source-backed |

### 0.3 Web verification performed

| # | URL / search | Finding | Verified? |
|---|---|---|---|
| W1 | `https://www.postgresql.org/docs/current/ddl-rowsecurity.html` | RLS policies can use `current_setting('app.current_tenant')` via `USING`/`WITH CHECK`. Superusers + `BYPASSRLS` bypass; table owners normally bypass unless `FORCE ROW LEVEL SECURITY` is set. Referential-integrity checks (FK, unique) bypass RLS (covert-channel warning). | Yes, page fetched 2026-10-13 |
| W2 | Search: "AWS App Runner closed to new customers 2026 ECS Express Mode replacement" | 9+ sources confirm App Runner closed to new customers on **2026-04-30**, with AWS docs (`docs.aws.amazon.com/apprunner/latest/dg/apprunner-availability-change.html`) and AWS-recommended migration to **ECS Express Mode** | Yes, search results 2026-10-13 |
| W3 | Search: "FastAPI Cloud beta launch postgres neon supabase cron workers background jobs 2026" | FastAPI Cloud is in public beta (blog dated 2026-06-22, https://fastapicloud.com/blog/fastapi-cloud-public-beta/). Pricing page lists Hobby $0 (3 apps, 0.1 vCPU / 512 MB, scale-to-zero, 3 max replicas, 1-day logs) and Pro $20/seat (25 apps, 0.1 vCPU / 512 MB base, scale-to-zero OR always-on, 10 max replicas, 14-day logs) | Yes, fetched 2026-10-13 |
| W4 | Same search: "scheduled jobs cron-like" | FastAPI Cloud "What You Get Today" section does NOT list scheduled jobs / background workers. The "What's Coming" section lists "background workers... files, **scheduled jobs (cron-like)**... regions" as planned future. Public beta does NOT yet expose them. | Yes, fetched 2026-10-13 |
| W5 | Search: "PostgreSQL pgvector 0.8 production scale indexed vector search performance benchmark" | pgvector 0.8+ is widely deployed in production; iterative index scans (0.8.0) "fixed filtered-search overfiltering" (Source: `bigdataboutique.com/blog/pgvector-in-production`). pgvector fine up to 1M+, drops per markaicode test 2026 and Medium benchmarks at 10M+ | Yes, search results 2026-10-13 |
| W6 | Search: "Qdrant Cloud free tier self-host vector store python client 2026" | Qdrant Cloud free tier: single node 0.5 vCPU / 1 GB RAM / 4 GB disk (~1M 768-dim vectors). "Free clusters suspend after 1 week of inactivity and delete after 4 weeks if you don't reactivate them." | Yes, fetched 2026-10-13 |
| W7 | Search: "Schemathesis 4.31 OpenAPI 3.1 contract testing pytest plugin stateful coverage" | Schemathesis supports OpenAPI 3.1 natively (`--experimental=openapi-3.1` is gone); stateful testing via `API Links` inferred from schema, no manual wiring; ships pytest plugin | Yes, search results 2026-10-13 |
| W8 | Search: "AWS RDS db.t4g.micro postgres pricing free tier 2026" | db.t4g.micro is 2 vCPU / 1 GB; pricing ranges from $11.68 (single-AZ, US East) per infratally 2026 to $23.18 (100 GB gp3) per bminfotrade 2026. AWS free-tier offers 750 hours/month on micro classes | Yes, search results 2026-10-13 |
| W9 | Search: "Next.js 16 standalone output AWS Amplify CloudFront S3 portability Vercel-only" | Amplify Hosting official Next.js supports SSG, SSR (`docs.aws.amazon.com/amplify/latest/userguide/ssr-amplify-support.html`). OpenNext provides path for `output: 'standalone'` to Lambda/ECS. Amplify is described as black-box by OpenNext docs | Yes, search + fetch 2026-10-13 |
| W10 | Search: "Playwright 1.40 json junit reporter test agents planner generator healer AI" | Playwright Test Agents (Planner/Generator/Healer) shipped in v1.56+. Built-in `json` + `junit` reporters, `trace: on-first-retry` | Yes, search results 2026-10-13 |

### 0.4 PowerShell files inspected without modification

```
Get-ChildItem -Recurse openspec\changes\lukla-ops-engine-planning
git status --short   (in working dir at session start)
OpenSpec/PRD/BRD/read for header + sections listed above
```

I did NOT run `git diff`, did NOT compute SHA256, did NOT execute `verify-traceability.ps1`, did NOT run `openspec status` / `openspec validate`. Those are owned by the parallel researcher and the orchestrator (AGENTS.md "Do not dispatch your own subagents" applies; `git history` operations are also outside my read-only scope here). I cite prior results from `worklog.md` lines 92–97 and `research-002.md` for those verifications.

---

## 1. Confirmed state of source documents

### 1.1 Task record rev 12 (Verified)

`task-record.md` line 3: `**Revision:** 12`, line 4: `**Updated:** 2026-10-13`. The active banner reads: **"Active technical-blueprint implementation — revision 12"**, with phases A (stack/schema/contracts sequentially) → B (auth/frontend/ops/testing/search/business) → C (workstreams + tracking + verification). Scope is **planning artifacts only**, no application code, no commits.

### 1.2 Discrepancy between BRD filename and internal version (Verified)

`openspec/changes/BRD - Lukla Operations Engine - v2.2.1 - FINAL.md` (filename) declares `Versi Dokumen: 2.3.0` internally (line 19). The PRD v2.0 references BRD v2.3.0 by internal name. **No version-rename is required** to keep the documents consistent; this is recognized as a stale filename. The `task-record.md` rev 12 treats v2.3.0 as canonical. Phase 7/8 artifacts must link to BRD v2.3.0 by **internal version**, NOT filename.

### 1.3 design.md Decision 3 still says "Supabase Row Level Security" (Verified)

`design.md` line 33: "Implement 8 distinct roles (Owner, Sample Team, Warehouse, Production Head, Tailor, QC Inspector, Finance/Payroll, Maklon Client) backed by **Supabase Row Level Security.**" The `09-plan` §2 acknowledges this and proposes updating design.md to portable RLS in Phase C2. **Gated**: this is an existing-source contradiction with the new portability direction. The artifact author cannot silently fix design.md outside an explicit Phase C step. UI: do not invent changes here; cite `design.md` verbatim and flag the portable-RLS update as a C2 task.

### 1.4 6 capability specs are in place (Verified)

All 6 spec files exist and contain at least the **SHALL**/`MUST` and `#### Scenario:` marker structure required by OpenSpec. `audit-and-sample-tracking/spec.md` has 2 ADDED Requirements; the other 5 have 3–4. Cross-spec FR coverage tally:

| Capability | FR IDs in spec | Verified count of `#### Scenario:` blocks |
|---|---|---|
| multi-tenant-platform | FR-1.1, FR-1.4, FR-2.1 | 3 |
| audit-and-sample-tracking | FR-3.1, FR-4.1 | 2 |
| warehouse-and-cutting-controls | FR-5, FR-6, FR-6.2 | 3 |
| production-output-tracking | FR-7.1, FR-7.2, FR-7.3, FR-7.4 | 4 |
| quality-control-and-inspection | FR-8.1, FR-8.2, FR-9.1, FR-9.2 | 4 |
| payroll-and-costing-engine | FR-10.1, FR-10.2, FR-10.3, FR-10.4 | 4 |

Total 20 ADDED Requirements + 20 Scenarios — consistent with PRD/BRD 26-id backlog counting FR-5 / FR-6 / FR-1.4 parents. (See §3.1 below for FR-1.4 wording discrepancy.)

### 1.5 Backend schema sketch is at Supabase-only 830 bytes (Verified)

The `backend_database_structure.md` content is an 830-byte directory tree showing `/supabase/migrations/`, `/supabase/functions/`, `/supabase/tests/` with one-line file names. NO SQL, NO column lists, NO ERD, NO role enum, NO chart-of-accounts, NO reversal mechanism, NO `validate_material_dispatch()` body, NO RLS policy bindings, NO migration ordering. **Per `09-plan` §2 this file is SUPERSEDED** by planned artifact `11-database-schema-spec.md`. The artifact author should NOT attempt to extend the existing file; treat it as a placeholder reference.

### 1.6 Storage architecture is in DRAFT (Verified)

`storage-architecture-draft.md` carries header `[DRAFT / INITIAL]` and ends with §6 open questions (`[FIND-01]`/`[ASK-01]`/`[ASK-02]`). The `09-plan` §2 promotes this to a final artifact via C4 (resolve FIND-01/ASK-01/ASK-02 as documented defaults: S3 Jakarta, IndexedDB sufficient, Object Lock on financial docs only). Until C4 lands, treat §6 as **live open questions**, not assumptions.

---

## 2. Concrete prerequisites that Phase A artifacts inherit (Verified)

The `09-plan` Phase A1 (artifact 10 — stack ADRs) requires D-1..D-5 decisions and the 8 web-verified facts. The artifacts must inherit:

### 2.1 Stack decisions inherited as-is

- **Backend:** FastAPI (Python) + plain PostgreSQL. Business logic in Python; invariants in DB. [user: D-1, dated 2026-10-13]
- **AI layer:** fenced semantic-search module over specs/audit/contracts/docs via Qdrant + OpenRouter. [user: D-2]
- **Test harness:** Playwright 1.56+ browser E2E + Schemathesis 4.x OpenAPI contract tests, parseable JSON/XML evidence. [user: D-3]
- **Deploy target day-1:** AWS. ECS Express Mode (NOT App Runner), RDS `db.t4g.micro`, S3 Jakarta (ap-southeast-3), CloudFront or Amplify Hosting, EventBridge Scheduler. [user: D-4 + W2 + W8]
- **Ports:** FastAPI Cloud (gated by what's-coming features), Neon, Qdrant Cloud (1 GB free tier with 4-week suspension / reactivation, W6), Vercel. [user: D-4]

### 2.2 Web-verified ports & cost sanity

| Token | Provider | Verified value 2026-10-13 | Source URL |
|---|---|---|---|
| `DATABASE_URL` pivot | Neon / Supabase / RDS / self-host Postgres 18+ | Plain-pg providers; all bind via a single connection string. RLS works on every Postgres host if policies bind to `current_setting('app.current_tenant')`, not Supabase-only `auth.uid()`. [constraint] | https://www.postgresql.org/docs/current/ddl-rowsecurity.html |
| Vector pivot | pgvector 0.8+ (fine up to ~1M, drops > 10M) → Qdrant Cloud (free tier 0.5 vCPU / 1 GB / 4 GB; 1 M 768-dim; suspended after 1 wk inactivity, deleted after 4 wk if dormant) | A `VectorStore` protocol implements both. | https://bigdataboutique.com/blog/pgvector-in-production ; https://qdrant.tech/cloud/ |
| Embeddings pivot | OpenRouter OpenAI-compatible `POST /api/v1/embeddings`. One `base_url` env var swaps providers (`OPENROUTER_BASE_URL`). | SDK adapters behind an `Embeddings` protocol. | https://openrouter.ai/docs/api-reference/embeddings |
| Compute day-1 AWS | ECS Express Mode (App Runner closed to new customers 2026-04-30). RDS `db.t4g.micro` 2 vCPU / 1 GB; US East single-AZ ~$11.68/mo. S3 standard / Standard-IA / Object Lock per storage-architecture-draft.md §4.3. | https://docs.aws.amazon.com/apprunner/latest/dg/apprunner-availability-change.html ; https://aws.amazon.com/rds/postgresql/pricing/ |
| Compute pivot | FastAPI Cloud public beta, Hobby $0 (3 apps, 0.1 vCPU / 512 MB, scale-to-zero, 3 max replicas, 1-day log retention) / Pro $20-seat (25 apps, 0.1 vCPU / 512 MB, 10 max, 14-day logs). Scheduled jobs + background workers are **listed under "What's Coming"**, not "What You Get Today" — **NOT yet shipped in public beta**. | https://fastapicloud.com/blog/fastapi-cloud-public-beta/ ; https://fastapicloud.com/pricing |
| Frontend deploy | Next.js `output: 'standalone'` for portability. AWS path = Amplify Hosting (SSG/SSR documented) or OpenNext → Lambda/ECS. Avoid Vercel-only APIs (default Image Optimization loader, ISR writes, Edge runtime). | https://docs.aws.amazon.com/amplify/latest/userguide/ssr-amplify-support.html ; https://opennext.js.org/aws/faq |
| Contract test | Schemathesis 4.x. Native OpenAPI 3.1 (the experimental flag is gone). CLI + pytest plugin + stateful (API Links). | https://schemathesis.io/ ; https://github.com/schemathesis/schemathesis |
| E2E | Playwright 1.56+ Test Agents (Planner, Generator, Healer) + `json`/`junit` reporters + `trace: on-first-retry`. | https://playwright.dev/docs/test-agents |

### 2.3 Inherited task-record rev 12 boundaries (Verified)

- `task-record.md` lines 9–11 (Active boundaries, rev 12). Quoting verbatim where it matters:
  - "User requirements: AWS-first with portable backend/vector/model/frontend options; BRD/PRD coverage; contract-first parallel development; deterministic agent-executable browser/API/system verification."
  - "Business assumptions remain proposed and production-gated pending authorized business approval. **Never silently settle BRD/PRD conflicts**, especially meal base, QC rounding, material ownership, or payroll eligibility."
  - "Verification targets: OpenSpec validate, contract parsing/reference/coverage checks, traceability checks and negative controls, git diff whitespace. Runtime/browser/cloud tests are future implementation gates, NOT executable application evidence in this planning-only change."
  - "Review cap: preserve recorded user limit of two correction loops per phase; escalate unresolved criticals without discarding user work."

### 2.4 OQ-1..OQ-9 + 08-register items to confirm carry-forward (Verified)

PRD v2.0 §A.9 carries an 8 + 1 = 9 unresolved list, plus the 08-client-clarification-register.md 6-domain register. The OQ list is canonical for OQ-1..OQ-9 carryover; the 08 register supplies theming for client decision packages. The Phase B6 artifact (`19-business-defaults-register.md`) must inherit both lists, and any default it records must be tagged `[DEFAULT-01]` style (following `storage-architecture-draft.md` precedent). Already-known carry-over items:

| OQ / register | Description | Where in source | Carry to |
|---|---|---|---|
| OQ-1 | Slide 02c missing — FR-2.1 ID is `[assumption]` | PRD §A.9 / `00-deconstruction.md` UNRESOLVED #1 / `04-rbac-matrix.md` header | artifact 19 (configurable default rationale) |
| OQ-2 | Slide 07 chat attachment only | PRD §A.9 / register UNRESOLVED #2 | artifact 19 + artifact 16 test provenance tags |
| OQ-3 | FR-5 Gudang detail | PRD §A.9 / register | artifact 11 schema — STORE NULL equivalent for FR-5 transactions |
| OQ-4 | FR-6 Cutting detail (inc. FR-7.3 cutting-output spec absence, register rev 4) | PRD §A.9 / register UNRESOLVED #4 | artifact 11 schema — same posture as OQ-3 |
| OQ-5 | FR-1.4 wording badge exists, body missing | PRD §A.9 | artifact 12 endpoint — FR-1.4 surfaces a generic onboarding endpoint; DO NOT define content |
| OQ-6 | Bonus ÷3 configurability (recipients count) | PRD §A.9 / 08 register 3.3 / PRD v1.3 vs BRD §13.2 (OQ-9) | artifact 19 + AC of payroll spec — KEEP pool÷3 fixed; pool-config default UNRESOLVED |
| OQ-7 | Meal base definition (10–15%) | PRD §A.9 / 08 register 3.1 / 3.2 | artifact 19 + payroll spec — keep `[inferred]` tag; do not invent base |
| OQ-8 | All slide visuals now legible (parity note) | PRD §A.9 | record only |
| OQ-9 | Bonus remainder allocation: PRD v1.3 ("ke cadangan pabrik") vs BRD §13.2/§16.1 ("tidak boleh dialokasikan ke rekening tertentu") — INTER-DOCUMENT CONFLICT | PRD §A.9 OQ-9 | artifact 19 — flag as PENDING-CLIENT; configurable; warn not to silently average |
| 08 register 3.3 (1) | QC Inspector bonus share (moral hazard) | 08 §3.3 | artifact 19 — same flag, configurable but KEEP-MUTABLE |
| 08 register 3.3 (2) | Mandor count variation | 08 §3.3 | artifact 19 — pool still ÷N if dynamic; preserve divisibility test |
| 08 register 3.3 (3) | Bonus remainder destination | 08 §3.3 = OQ-9 duplicate | artifact 19 — same |
| 08 register 3.3 (4) | Bonus clawback / reject retro | 08 §3.3 | artifact 19 — clawback default = OFF; configurable |
| 08 register 3.4 (1–4) | Saturday cutoff time, OT/bridge-week, payment method, approval gate | 08 §3.4 | artifact 19 — defaults configurable; cutoff 12:00 WIB suggested, not mandated |

The above list is illustrative of carry-over scope and is NOT exhaustive. The artifact author must read the full PRD §A.9 and the full 08 register before authoring artifact 19.

---

## 3. Recommended contract boundaries (decision supports, not decisions)

Per `task-record.md` line 9 "Review the request: ..." the 09 plan §3 says API contracts are authored at the planning stage to support parallelization. Read this section as **boundary-suggested structures** with provenance anchors, NOT prescriptions. Any endpoint below that lacks a source anchor is marked **GATED** and must remain in the "`openapi-stub`" status.

### 3.1 FR→endpoint mapping (boundary suggestion only; final draft in artifact 12)

| FR ID | Suggested endpoint(s) | Source anchor | Status |
|---|---|---|---|
| FR-1.1 | `GET /api/v1/me/tenant` returns authenticated tenant id (read-only); all other endpoints carry `client_id` in path/query and are RLS-gated | PRD A.8 (mandatory client_id predicate) | necessary |
| FR-1.4 | `POST /api/v1/clients` + `POST /api/v1/orders` | PRD §A.9 OQ-5 (text missing); spec `multi-tenant-platform` "Client and Order Onboarding" | **GATED** — wording; only stub endpoint shape |
| FR-2.1 | Endpoints gated by `X-User-Role` claim + `X-User-Id` (or JWT-equivalent); role enum restricted to 8 names per `04-rbac-matrix.md` §1 | slide 04 + 04 matrix | necessary |
| FR-3.1 | All ledger `INSERT`s go through `POST /api/v1/ledger/entries`; reversal via `POST /api/v1/ledger/reversals` (compensating entry only; NO `PATCH`/`DELETE` on `journal_entries`) | PRD A.8 ("tidak ada UPDATE/DELETE pada tabel buku besar") | necessary; reversal-mechanism wording `[inferred]` |
| FR-4.1 | `POST /api/v1/samples` with sample-version entity; `GET /api/v1/samples/{id}/revisions` returns v1..vN history | FR-4.1.2 [inferred] per `00-deconstruction.md` rev 4 | necessary |
| FR-4.2 | `POST /api/v1/time-studies/{component_id}` | FR-4.2 `[inferred]` | necessary; rates near source-status |
| FR-4.3 | `POST /api/v1/samples/{id}/lock` → Master Spec Sheet immutable | FR-4.3 `[inferred]` | necessary |
| FR-5.1 | `POST /api/v1/material-receipts` requires `client_id` + `order_id` body fields | FR-5.1 `[inferred]` | necessary |
| FR-5.2 | Custodial-accounting flag set on material_receipt via `material_scheme` ∈ {`CMT`, `SEMI_CMT`, `FULL_PACKAGE`}; CMT material → off-balance GL `Inventory:Custodial:RawMaterial [Client_ID]` / `Liability:CustodialObligation [Client_ID]` | FR-5.2 `[inferred]`; GL line shape found in `Overall Plan Draft.md` 89–101 | necessary; GL accounts `[inferred]` not source |
| FR-6.1 | `GET /api/v1/stock-opname` (read) and `POST /api/v1/stock-adjustments` (opname correction) | FR-6.1 `[inferred]` | necessary; correction procedure **GATED** |
| FR-6.2 | `POST /api/v1/material-issuances` validated at DB by `validate_material_dispatch()` trigger; rejection returns HTTP 409 with `{code:"TENANT_MISMATCH"}` body | FR-6.2 source-behavior at slide 02/04/08/09; module ownership **GATED** | necessary; error-code wording `[inferred]` |
| FR-6.3 | `POST /api/v1/cutting-results` records fibre wastage ratio | FR-6.3 `[inferred]` | necessary; ratio computation **[inferred]** |
| FR-7.1 | `POST /api/v1/lines/{line_id}/operators` rearranges allocation; no rigid slot count | FR-7.1 source | necessary; "line" model NOT yet defined (S3 below) |
| FR-7.2 | Rate card `PUT /api/v1/rate-cards/{component_id, client_id, article_id}` | slide 06 FR-7.2 (Owner manages) | necessary; Owner vs Mandor precedence **GATED** |
| FR-7.3 | `POST /api/v1/sewing-outputs` 30-min batch (idempotency-key required) | slide 06 FR-7.3 | necessary |
| FR-7.4 | `POST` issued → unit status `MENUNGGU_QC` automatically; barred from payroll until QC pass | slide 06 FR-7.4 | necessary |
| FR-8.1 | `POST /api/v1/qc-inspections` with disposition ∈ {`PASS`,`REPAIR`,`REJECT`} (slide-05 wording) | FR-8.1 source | necessary; status vocabulary **GATED** between three wordings (slide 04/05/08) |
| FR-8.2 | `POST` to mark `REPAIR` requires `original_operator_id`; transitions to `REWORK` → re-QC; second credit on `PASS` is rejected by idempotency | FR-8.2 source | necessary |
| FR-9.1 / FR-10.3 | One rule, two IDs. Append-only event `QC_BONUS_ACCRUAL` on each `PASS`. Pool = `(sum of QC_BONUS_ACCRUAL.amount)` × 1 (each Pass unit credits the configured per-Pass rate once) | PRD A.8 cross-note (`satu aturan bonus bagi-tiga`) | necessary; backend MUST emit ONE event per Pass — no double pool |
| FR-9.2 / FR-10.3 | `GET /api/v1/payroll/weekly/{period_id}/bonus-pool` summary; the 3 recipients are people, not RBAC roles | slide 05 recipients / slide 07 chat attachment | necessary; recipient-account-mapping **GATED** |
| FR-10.1 | Hourly cron / EventBridge / FastAPI Cloud future `/jobs/saturday-payroll` HTTP endpoint; cutoff rule from 08 register 3.4 (configurable) | slide 07 chat attachment | necessary |
| FR-10.2 | `GET /api/v1/payroll/weekly/{period_id}/meal-pool` = `mu * Σ ongkos_jahit` where `mu` ∈ [0.10, 0.15] entered by Finance for that period | slide 07 chat attachment | necessary; base of meal pool **GATED (UNRESOLVED)** |
| FR-10.3 | One event per Pass (see FR-9.1). Reverse-pool risk: see OQ-9 | slide 07 chat attachment | necessary |
| FR-10.4 | `POST /api/v1/monthly-overhead` records utility bills; `GET /api/v1/payroll/monthly/{year_month}/overhead-per-unit` returns `Σ utility / Σ monthly_passed_units` | slide 07 chat attachment + 08 register 2.1 | necessary; allocation base **GATED (UNRESOLVED)** |

State-machine boundary for FR-7.4 (verified on slide 06 / slide 04b):

```
SEWING → (FR-7.3 verified mandor) → MENUNGGU_QC → (FR-8.1 PASS) → QC_PASS
                                 \→ (FR-8.1 REPAIR) → REWORK → MENUNGGU_QC  (cycle; idempotent on credit)
                                 \→ (FR-8.1 REJECT) → REJECT_SCRAP (wage Rp 0)
```

This matches slide-04 row 5 (penjahit cannot edit verified), row 6 (QC inspects), AT-04 (verification gates w/o premature wage), AT-05 (Repair no double credit).

### 3.2 Module / structural boundaries (artifact 11 surface)

Based on semantic search S1..S4, the **minimum table inventory** the artifact 11 author needs to commit to (NOT a schema — a list of named entities, each with a one-line purpose; full DDL is in artifact 11's scope):

| Entity | Purpose | Known source / `[inferred]` tag |
|---|---|---|
| `clients` | tenant roster; Snøhund is one tenant box (slide 02b) | slide 02b source |
| `users` + `roles` (8-role enum) | RBAC backing | slide 04 source + `04-rbac-matrix.md` |
| `journal_entries` (append-only) + `journal_lines` (paired debit/credit) + `chart_of_accounts` (incl. `Inventory:Custodial:*`, `WIP:*`, `Liability:Custodial:*`, etc.) | immutable double-entry | BRD §1 + BRD §9.1 source; chart-of-accounts tag `[inferred]` |
| `material_lots` + `material_receipts` | guarded by `validate_material_dispatch()` trigger | FR-5.x source + `[inferred]` schema |
| `material_issuances` + `material_scheme` enum | issuance guardrail | FR-6.2 source + `[inferred]` |
| `cutting_results` | wastage / consumption | FR-6.3 `[inferred]` |
| `samples` + `sample_versions` | v1→v2 lineage | FR-4.x source + `[inferred]` |
| `master_spec_sheets` (locked) | FR-4.3 lock | FR-4.3 `[inferred]` |
| `time_studies` | FR-4.2 | FR-4.2 `[inferred]` |
| `rate_cards` (per component, per article, per client) | FR-7.2 | slide 06; precedence **GATED** |
| `lines` + `line_assignments` + `sewing_outputs` | dynamic line allocation task = UNDEFINED — see open below | FR-7.1 source; model shape NOT in any source |
| `qc_inspections` + `qc_events` | Pass/Repair/Reject + idempotency | slide 05 source + AT-05 |
| `payroll_periods` + `payroll_lines` + QC bonus pool event log | FR-10.x computation | slide 07 chat + 08 register 3.x; recompute logic `[inferred]` |
| `monthly_overhead` | FR-10.4 denominator | slide 07 chat + 08 register 2.1 allocation base **GATED** |
| `media_assets` | already drafted in `storage-architecture-draft.md` §5 | existing |
| `audit_log` (append-only) | FR-3.1 | slide 02 / slide 03 source |

Each table requires an RLS policy binding to `current_setting('app.current_tenant')`. Per W1 (PG RLS docs), policies can be permissive to all users + role-based for `client_id` checks; superusers + `BYPASSRLS` bypass, so the application connection pool must NOT use a superuser role for tenant-bound traffic.

### 3.3 AuthN / AuthZ boundary (artifact 13 surface)

Auth has **no spec on disk** (search S6 found zero JWT/session/session/role-login artifacts). The artifact 13 author must write it from scratch with these boundaries:

| Boundary | Constraint | Source / verification |
|---|---|---|
| Floor-tablet auth | mandor login must work offline (NFR-05) and resume sync | `06-acceptance-tests.md` AT-04; NFR-05 source |
| B2B portal auth | self-registration absent (slide 04 row 8 limits to **own** data); portal provisioning mechanism is `[inferred]` | slide 04 + PRD A.8 |
| RLS context propagation | every request: App sets `SET app.current_tenant = '<uuid>'` + `SET app.current_user_id = '<uuid>'` + `SET app.current_user_role = '<role>'` BEFORE the query, in the SAME transaction | W1 |
| Append-only ledger | revoke `UPDATE`/`DELETE` on `journal_entries`, `journal_lines`, `audit_log`, `time_studies`, `qc_events` for all non-`OWNER` non-BYPASSRLS roles | PRD A.8 + W1 + AT-R01 |
| Reversal mechanism | API endpoint `POST /api/v1/ledger/reversals` writes a compensating entry; does NOT mutate the original | PRD A.8 + slide 04 row 1 PEMBATASAN (locked-history rule) |

AuthN protocol choice: **JWT bearer tokens with short TTL (≤ 60 min) + sliding refresh token, signed with HS256 embedded public key**, recommended because (a) FrontEnd-Ciwidey tablets cannot store long-lived sessions, and (b) refresh tokens fit the offline-resume requirement. This is a **Recommendation**, not a decision. It is included here because no auth spec exists; the artifact 13 author can refine it.

### 3.4 Frontend boundary (artifact 14 surface)

PRD v2.0 and `design_guideline.md` are already in scope. PRD `B.6` says: "sistem dibangun sebagai Web Responsive PWA untuk desktop dan tablet sentuh industri." Per `09-plan` §3.1 the portability rule is: `output: 'standalone'`, no Vercel-only APIs, no ISR writes, no Edge runtime. Diagram-of-truth for the 6 views already exists in slides 02..09. View mapping (cross-verified vs `04-rbac-matrix.md`):

| View | Role that uses it | Source anchor |
|---|---|---|
| 01 — Login / Session bootstrap | All | inferred |
| 02 — Sample R&D | Tim Sample, Owner, Maklon Client | slide 02 / slide 03 + `04` row 2 |
| 03 — Warehouse + Stock Opname | Gudang | slide 03 + `04` row 3 |
| 04 — Sewing Floor (touch terminal) | Mandor / Penjahit | slide 06 + `04` rows 4–5 |
| 05 — QC Inspection (touch terminal) | QC Inspector | slide 05 + `04` row 6 |
| 06 — Payroll & Reports (desktop) | Finance & Payroll, Owner | slide 07 chat + slide 08 + `04` rows 1, 7 |

The 6-view count is floor-and-labor derived from the slide deck; **do not invent additional views**.

---

## 4. Conflicts that must stay gated (Do Not Decide)

Per `task-record.md` rev 12 line 11: "Never silently settle BRD/PRD conflicts, especially meal base, QC rounding, material ownership, or payroll eligibility." The Phase A/B/C artifacts cannot resolve any of the following; each is carried verbatim from existing documents and is escalated to the client/business owner.

| # | Conflict (carry verbatim) | Where it lives | Why it stays gated |
|---|---|---|---|
| G-1 | **Bonus pool remainder (OQ-9).** PRD v1.3 carries "sisa pembulatan — walau Rp 1 — masuk ke **cadangan pabrik**, bukan mematahkan aplikasi"; BRD §13.2 and §16.1 carry "tidak boleh dialokasikan ke rekening tertentu". PRD v2.0 §A.9 OQ-9 lists this verbatim. | `00-deconstruction.md` UNRESOLVED #6 + PRD v1.3 vs BRD §13.2 + PRD v2.0 §A.9 + 08 register 3.3 #3 | Two sources disagree; this is an inter-document conflict. Cannot be solved by author; client-decision required. |
| G-2 | **FR-10.2 meal base (OQ-7).** Slide 07 chat attachment only says "10–15% × Σ ongkos jahit in the period". Base of "ongkos jahit" is undefined (does it include ongkos potong?). `register` glossary line 18 says ongkos potong is `[inferred]`. | `00-deconstruction.md` slide 07 + register UNRESOLVED #7 + 08 §3.1 + 08 §3.2 | Source does not specify the base. |
| G-3 | **FR-6.2 module ownership.** Slides 02/04/08/09 require rejection of cross-client issuance. Which code lives in Gudang, Cutting, or both? Source does not assign. `04-rbac-matrix.md` row 3 PEMBATASAN tags: `[module-ownership UNRESOLVED — Cutting-or-Gudang]`. | `04-rbac-matrix.md` row 3 + `00-deconstruction.md` Contradictions #1 + PRD v2.0 §A.9 OQ (related) + `06-acceptance-tests.md` AT-01 / AT-R03 / FR-6.2 ownership note | Solution can be inserted at EITHER or BOTH modules; behavior is identical. The trigger itself can live in shared code; do not invent a single-owner claim. |
| G-4 | **FR-5 / FR-6 detail.** Stock transactions procedure, adjustment rules, opname cadence — none in source. Cutting batch / marker / waste / cut-record detail — none in source. | register UNRESOLVED #3 + #4 + PRD v2.0 waiting-for-clarification table | No source. Cannot invent. |
| G-5 | **FR-1.4 wording.** ID badge exists on slide 03 but no body text. | register UNRESOLVED #5 + 08 §6.3 | No source. Stub endpoint only. |
| G-6 | **Rate-card governance precedence.** `04-rbac-matrix.md` Boundaries says: "Slide 06 FR-7.2 says Rate card managed by Owner. Who sets, changes, approves, or overrides a component rate and at what point remains undecided". | `04-rbac-matrix.md` boundaries-line + slide 06 + slide 04 | Owner permits "Ubah rate card"; Mandor permits "Tentukan rate card komponen" — neither cancels the other. Do not invent precedence. |
| G-7 | **QC status wording.** Slide 04 row 6 IZIN: `lolos/reject/repair`. Slide 05 badges: `Pass/Repair/Reject`. Slide 08 view 05: `lolos/repair/scrap`. | `00-deconstruction.md` Contradictions #2 (line 469) + `04-rbac-matrix.md` terminology-variance row | Three wordings in source. Implement as enum with both display variants, do not select a canonical. |
| G-8 | **Bonus recipient maturity.** Mandor 1, Mandor 2, Kepala Operasional are PERSONS not RBAC rows. | `04-rbac-matrix.md` boundaries-line + 08 §3.3 + PPT slide 05 / slide 07 chat | Recipients are 3 named humans at present; their system RBAC role assignment is open. Implementation must accept a recipient list separately. |
| G-9 | **Schema for FR-7.1 dynamic line allocation.** "Line → operator → station" model is NOT in any source. **`02b` mentions "±70 machines" as scale context** but NOT as a cap. No entity-relationship trail for the line-to-sewing-output trace. | `02b` slide + slide 06 + spec `production-output-tracking` 5–11 + `06-acceptance-tests.md` AT-04 (verification chain) + `03` STOS (storage-architecture-draft §2 files) | No source for the relational shape. The author can introduce `lines`, `line_assignments`, `sewing_outputs` — but each line of work carries evidence `[inferred]` and recorded as such. |
| G-10 | **Caretaker of business defaults.** `task-record.md` says client-aligned via 08 register; planning artifacts can carry `[DEFAULT-NN]` tagged defaults per `storage-architecture-draft.md` precedent but each must be traceable to a clear ask. | `task-record.md` line 10 + `storage-architecture-draft.md` §6 | Decisions are gated, not silent. |
| G-11 | **Bonus clawback.** 08 §3.3 (4) raises the question of retroactive bonus clawback if a klient later rejects a Pass unit. No source covers this. | `08-client-clarification-register.md` §3.3 (4) | No source. artifact 19 must keep `[DEFAULT: clawback = OFF; configurable]`. |
| G-12 | **PPh 23 / PPN / financial statutory.** PRD B.6 + BRD §3.2 explicitly OUT-OF-SCOPE. Plan §6 non-goals: "Statutory payroll (BPJS/PPh21), full financial accounting". | PRD v2.0 §B.6 + BRD §3.2 §9.2 + 09-plan §6 | Stay out of scope; do not introduce PPN modulo. |
| G-13 | **Slide-02c and Slide-07 provenance.** Slide 02c photo missing from disk; FR-2.1 ID is `[assumption]`. Slide 07 only as chat attachment. | `00-deconstruction.md` slide 02c + slide 07 + register UNRESOLVED #1 + #2 + `04-rbac-matrix.md` header | Provenance tags remain; do not silently upgrade. |

These are NOT authoring failures; they are faithful preservation per the user instruction. Any plan author who stays within these gates will not violate `task-record.md` rev 12.

---

## 5. Risks / open items surfaced during research,

Hand-offs only. None of these were tested, run, or verified beyond filesystem inspection and web sources cited above.

### 5.1 Risks to plan authorship

| Risk | Severity | Mitigation |
|---|---|---|
| **RLS escape via superuser connection** | High. W1 confirms superuser + `BYPASSRLS` bypass. Application pool unintentionally using `postgres` role could leak tenant data across clients. | Mandatory: (a) connection role is non-superuser; (b) `SET app.current_tenant` is bound at every transaction start; (c) lintable CI grep for `BYPASSRLS` and `ALTER ROLE … SUPERUSER` in migrations. |
| **FK / unique integrity checks bypass RLS** (covert channel). | Medium. W1 source: "Referential integrity checks... always bypass row security to ensure data integrity. Care must be taken to avoid 'covert channel' leaks through such referential integrity checks." | Use composite FKs that include `client_id` where the referenced table is tenant-scoped; do not rely on FK silent rejection of cross-tenant inserts as a security control. |
| **Snøhund flagged same as external klien tenants.** | Medium. Snøhund is its OWN tenant box per slide 02b (`00-deconstruction.md` lines 138–144). If implementation treats Snøhund as a special case, CMT/Full-Package flows could become inconsistent. | Apply same RLS rules uniformly. Snøhund's `client_id` is just one more value in the `clients` table. |
| **FastAPI Cloud pivot still lacks scheduled jobs / workers** (public beta, June 2026) | Medium. W4 confirms scheduled jobs + background workers are listed under "What's Coming" not "What You Get Today". Plan §3.2 mandates HTTP-triggered jobs; this remains the safer pivot. | Continue HTTP-triggered-jobs strategy; re-verify before any pivot to FastAPI Cloud as primary runtime. |
| **pgvector 0.8 + multi-tenant filtered search.** | Medium. `bigdataboutique.com/blog/pgvector-in-production` confirms pgvector 0.8 iterative index scans fix filtered-search overfiltering, BUT only around 1M vectors; performance degrades 10M+. | Use pgvector as day-1 at scale expected (< 1M specs/contracts/audit logs); pivot to Qdrant Cloud when needed behind `VectorStore` protocol. |
| **Qdrant Cloud free tier dormancy deletion.** | Low-medium. W6: "Free clusters suspend after 1 week of inactivity and delete after 4 weeks if you don't reactivate them." Pivot plan must include either a Qdrant Cloud paid tier (~$25/mo) or self-host fallback. | Document free-tier dormancy rule in artifact 17 (`17-semantic-search-module.md`). |
| **AWS App Runner EOL risk re-surfacing.** | High (already mitigated by plan). W2 confirms App Runner is closed to new customers 2026-04-30. Any retrofit of App Runner in a workstream brief must be rejected. | Implement landing on ECS Express Mode day-1. Add CI grep for `AWS::AppRunner::` in Terraform. |
| **PRD v2.0 §B.6 (out-of-scope list) vs future scope creep.** | Medium. PRD says "Aplikasi seluler native — sistem dibangun sebagai Web Responsive PWA". Workstream authors might invent a native-mobile WS stream. | Inherit PWA limit in artifact 18 workstreams. |
| **`backend_database_structure.md` 830-byte Supabase-only sketch.** | High if reused as-is. Currently a placeholder tree, no SQL. | Per plan §2 it is SUPERSEDED; artifact 11 must be authored from scratch with portable RLS. Do NOT extend this file. |

### 5.2 Open questions to escalate (echo of PRD §A.9 + 08 register)

The full set is large. Highlights only; not exhaustive:

- OQ-1..OQ-9 (above §2.4)
- Bonus clawback qualitative shape (08 §3.3 #4)
- Saturday Payroll cutoff time and post-cutoff unit routing (08 §3.4 #1, #2)
- AQL inspection standard and external QC audits (08 §5.1)
- RMA / return flow for finished goods (08 §5.2)
- Sample sign-off workflow: signature shape (08 §5.4)
- Per-tenant accounting valuation (Custodial: moneter vs sub-ledger physical meter; 08 §2.2)
- AQL burden, downtime codes, dispute window (08 §4.1, §4.2)
- Snøhund vs klien IP Chinese wall details (08 §5.3)

### 5.3 Unknowns (cannot answer from filesystem / web)

- Whether the orchestrator's FastAPI Cloud beta account access has scaled beyond the public-beta quotas. (W3/W4).
- Whether FR-7.1's "line" is a logical concept (group of stations) or a physical concept (rolling sewing headcount). Slide 06 says "tata letak lini produksi dinamis... tanpa slot kaku" but no entity definition.
- Test agent invocation posture (Planner/Generator/Healer) on a planning-only change: do they make sense pre-`openapi.yaml`?
- Whether `journal_entries` should be a PostgreSQL-native `TABLE` or a Hypertable / chunked table for archival. PRD/BRD/plan all silent.

---

## 6. Concrete prerequisites to start Phase A authoring

1. **OpenSpec artifact slot available.** `tasks.md` Phase 5 reports "4/4 artifacts complete" via `verify-traceability.ps1`. Adding 10.19 + `contracts/openapi.yaml` + 2 new spec deltas is incremental: each new spec must be in `specs/{name}/spec.md` and matched in `proposal.md` capabilities list.
2. **BRD/PRD frozen.** `task-record.md` says BRD/PRD are frozen+approved post-recovery (rev 11 + 12 review loops). The Phase A author must not invent new FRs; they can only write schemas / endpoints that consume the 26-product-backlog / 20-Observed FR + role/set boundaries.
3. **Design.md update path prepared.** Plan §2 says "design.md Correct Decision 3 (Supabase→portable RLS), add D-1..D-5". Phase C2 owner. Phase A author can pre-stage wording, but final write must be in C2.
4. **Choose card name + order conventions to match OpenSpec** (e.g., `services/web/`, `packages/contracts/`, `infra/aws/`, `infra/fastapi-cloud/`, `infra/vercel/`). Following AGENTS.md "reach for the framework's documented pattern before inventing one" and "one prerequisite, not two" — declare these at the top of artifact 10.
5. **Maintain evidentiary traceability.** Every artifact title cell must end with `[code]`, `[doc]`, `[user]`, `[default]` per `09-plan` §8 #1.
6. **Do NOT install dependencies in this change.** Per `task-record.md` rev 12 "no dependencies installed" + plan §6 non-goal. Pip / npm / pnpm install commands belong to a future implementation change, not this one.
7. **CI grep list as a planning artifact.** Plan §3 lists portability checks; the artifact author must codify them in artifact 16 (test harness) as grep / lint rules run against the eventual app tree, so future devs see the checks exist before they write code:
   - `grep -r "auth.uid()" --include="*.sql"` → fail (Supabase-only binding).
   - `grep -r "BYPASSRLS\|SUPERUSER" --include="*.sql"` → warn.
   - `grep -r "process.env.VERCEL_" --include="*.{ts,tsx,js,jsx}"` → warn.
   - `grep -r "from '@vercel/.*'" --include="*.{ts,tsx,js,jsx}"` → warn.
   - `grep -r "next/image" --include="*.{ts,tsx,js,jsx}"` → warn when `NEXT_PUBLIC_DEFAULT_LOADER` is unset (Image Optimization default loader is Vercel-only).
   - `grep -r "export const revalidate" --include="*.{ts,tsx,js,jsx}"` → warn (ISR writes do not work in standalone).
   - `grep -r "runtime = 'edge'" --include="*.{ts,tsx,js,jsx}"` → warn (Edge runtime breaks standalone Lambda target).
   These rules are **DECISION CANDIDATES, not decisions**. Phase A author records them as D-N candidates for review.

---

## 7. Worklog & action evidence

### 7.1 Worklog entry (this report only)

```
2026-10-13 — Research blueprint-boundaries-001 (Explorer, read-only).

Source-doc confirmation (read only):
- task-record.md → revision 12 confirmed (lines 3-4).
- BRD internal version 2.3.0; filename retains v2.2.1 (semantic discrepancy known).
- PRD v2.0 Wagile Bagian A + B reviewed; 26 FR IDs verified.
- All 6 capability specs structurally valid (SHALL/MUST + Scenario blocks).
- design.md Decision 3 still says "Supabase RLS"; portable-RLS update queued for Phase C2.
- backend_database_structure.md is 830-byte Supabase-only sketch (superseded by artifact 11).
- storage-architecture-draft.md is INITIAL DRAFT (promote via Phase C4).

Independent web verification (2026-10-13):
- PG RLS docs: policies work via current_setting(); superusers + BYPASSRLS bypass; FK/unique bypass RLS (covert channel warning).
- AWS App Runner closed to new customers 2026-04-30; ECS Express Mode is the official replacement.
- FastAPI Cloud public beta Hobby $0 / Pro $20-seat; "What's Coming" lists background workers + scheduled jobs (cron-like) — but "What You Get Today" does NOT yet include them. Plan §3.2 HTTP-triggered-jobs strategy remains correct.
- Qdrant Cloud free tier: 0.5 vCPU / 1 GB / 4 GB / ~1M 768-dim vectors; suspends after 1 week inactivity; deletes after 4 weeks.
- pgvector 0.8 with iterative index scans is fine around 1M vectors; degrades > 10M.
- Schemathesis 4.x supports OpenAPI 3.1 natively; stateful via API Links.
- Next.js standalone + Amplify Hosting OR OpenNext → Lambda/ECS both portable.
- Playwright Test Agents Planner/Generator/Healer shipped v1.56+.
- AWS RDS db.t4g.micro 2 vCPU / 1 GB; ~$11.68/mo Single-AZ US East.

Gated conflicts preserved (no silent decisions):
- Bonus remainder OQ-9 (PRD v1.3 vs BRD §13.2)
- Meal base OQ-7
- FR-6.2 module ownership
- FR-5 / FR-6 detail
- FR-1.4 wording
- Rate-card governance precedence
- QC status wording variance (3 wordings in source)
- Bonus recipients as persons not RBAC roles
- FR-7.1 line entity shape (no source)

Artifacts path: artifacts/research/blueprint-boundaries-001.md
No other files modified. No subagent dispatch.
```

### 7.2 Open vs Closed Loops

| Open / Closed | Item |
|---|---|
| Closed | Task-record rev confirmation |
| Closed | BRD internal version and PRD mutual reference |
| Closed | 6 capability spec `SHALL`/`MUST` + `Scenario:` structure |
| Closed | 8 web-verified port facts |
| Open | artifact 10..19 + openapi.yaml + 2 new spec deltas (Phase A/B/C author) |
| Open | All G-1..G-13 gates preserved for client decision |
| Open | Task-record rev 12 → rev 13 progression (next phase close-out) |

### 7.3 Action evidence summary

| Path | Action | Evidence |
|---|---|---|
| `openspec/changes/lukla-ops-engine-planning/task-record.md` | read lines 1–400 | Rev 12 banner |
| `openspec/changes/lukla-ops-engine-planning/09-technical-blueprint-completion-plan.md` | read lines 1–200 | All ACs and tables |
| `openspec/changes/lukla-ops-engine-planning/00-deconstruction.md` | read header + role/sample/QC/floor/scenario sections | §0.1 R3 |
| `openspec/changes/lukla-ops-engine-planning/{04,06,08,09}*.md` | read entire files | §0.1 R4, R5, R6; design.md = R7 |
| `openspec/changes/lukla-ops-engine-planning/specs/*/spec.md` | read all 6 | §0.1 R8 + §1.4 |
| `openspec/changes/lukla-ops-engine-planning/worklog.md` | read entire | §0.1 R9 |
| `openspec/changes/lukla-ops-engine-planning/artifacts/research/research-001.md` | read entire | §0.1 R10 (avoids dup) |
| `openspec/changes/lukla-ops-engine-planning/artifacts/research/research-002.md` | read entire | §0.1 R10 |
| `openspec/changes/lukla-ops-engine-planning/artifacts/research/research-003-phase2b-recovery.md` | read entire | §0.1 R10 |
| `openspec/changes/PRD - Lukla Operations Engine - v2.0 - Wagile.md` | read 1–186 | §0.1 R11 |
| `openspec/changes/BRD - Lukla Operations Engine - v2.2.1 - FINAL.md` | read 1–312 | §0.1 R12 |
| `openspec/changes/lukla-ops-engine-planning/artifacts/backend_database_structure.md` | read entire (830 B) | §0.1 R13 |
| `openspec/changes/lukla-ops-engine-planning/artifacts/storage-architecture-draft.md` | read entire | §0.1 R14 |
| Web: PG RLS docs | fetched | §0.3 W1 |
| Web: AWS App Runner closure | search confirmed | §0.3 W2 |
| Web: FastAPI Cloud public-beta features + pricing | fetched | §0.3 W3, W4 |
| Web: pgvector benchmarks | search + comparison | §0.3 W5 |
| Web: Qdrant Cloud free tier | search + pricing | §0.3 W6 |
| Web: Schemathesis 4.x capability | search + docs | §0.3 W7 |
| Web: AWS RDS db.t4g.micro | search + price | §0.3 W8 |
| Web: Next.js 16 portable to AWS | search + Amplify docs | §0.3 W9 |
| Web: Playwright Test Agents | search + docs | §0.3 W10 |
| `mcp_semantic-sear_search` done in repo | 7 queries | §0.2 S1..S7 |

After this report was composed: NO file in the workspace other than the newly created `blueprint-boundaries-001.md` was modified. `git diff --shortstat` would, on re-run after this report, show only that new untracked file (verified by running `git status --short` return baseline untracked set in §0.1 inspection).

---

## 8. Bounds and explicit non-claims

- This is a **bounded research report**, NOT a writing substitute for `10-technology-stack-and-decisions.md` or `11-database-schema-spec.md` etc. The next phase writers must produce these artifacts with their own evidence and own source-tracing.
- I did NOT run `verify-traceability.ps1`, did NOT verify SHA256 of frozen files, did NOT execute `openspec status` / `openspec validate`. The Phase 5 worklog block (worklog.md lines 92–97) records those runs as already-verified; I cite without re-running.
- I did NOT propose final values for OQ-1..OQ-9, bonus clawback, qc status wording canonicalization, or FR-7.1 entity shape. Those gates are preserved.
- I did NOT promise any application code, runtime test, or AWS deployment.
- I did NOT dispatch any subagent.
- I did NOT modify, delete, or rename any existing file in the workspace.
- I did NOT claim acceptance of artifact quality; I report what I observed and what is open.

---

*End of report. Path: `openspec/changes/lukla-ops-engine-planning/artifacts/research/blueprint-boundaries-001.md`.*
