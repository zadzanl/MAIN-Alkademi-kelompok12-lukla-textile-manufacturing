# 09 — Technical Blueprint Completion Plan
**Change:** `lukla-ops-engine-planning`
**Date:** 2026-10-13 (Updated: 2026-10-14)
**Status:** COMPLETED & REVIEW-APPROVED (Planning Phase) on 2026-10-14. Phase A, Phase B, and Phase C completed and approved across review records (`blueprint-contract-review.md`, `blueprint-phase-b-review.md`, `blueprint-phase-c-review.md`). Implementation handoff ready; runtime implementation and cloud deployment remain out of scope for this planning change.
**Purpose:** Extend the existing planning baseline (requirements layer) into an all-encompassing, end-to-end technical specification: from empty repo to deploy-ready, parallelizable across developers, AWS-first but platform-agnostic, with an AI-agent-verifiable test harness.

---

## 1. Grounding & Confirmed Decisions

Decisions locked with the user on 2026-10-13:

| # | Decision | Source |
|---|----------|--------|
| D-1 | Backend: **FastAPI (Python) + plain PostgreSQL**. Business logic in Python; invariants (RLS, `validate_material_dispatch()`) in the database. | [user: "FastAPI + plain PostgresQL should be the simplest right? lets stick with that"] |
| D-2 | AI layer: **one fenced semantic-search module** over specs/audit logs/contracts/docs via Qdrant + OpenRouter. Isolated from the ledger core. | [user: "likely some sort of AI search feature: maybe a semantic search over specs/audit logs/contracts/other files/documentation via Qdrant and openrouter"] |
| D-3 | Test harness: **Playwright browser E2E + API contract tests**, executable by an AI review-orchestrator agent with machine-readable evidence. | [user: selected "Browser E2E + API contract tests"] |
| D-4 | Deploy fully on AWS; pivot targets: FastAPI Cloud (backend), Qdrant (vector store), OpenRouter (model provider), Vercel (frontend). | [user: request item 1] |
| D-5 | Planning must satisfy all BRD v2.3.0 + PRD v2.0 conditions and be split/parallelize-ready with API definitions at planning stage. | [user: request items 2–3] |

Research-verified facts that constrain the design (all fetched 2026-10-13):

- **AWS App Runner is closed to new customers** (effective 2026-04-30); AWS recommends **ECS Express Mode** as replacement. [doc: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/express-service-overview.html; doc: https://x.com/AWSSupport/status/2043243058402046237]
- **FastAPI Cloud** is public beta; CLI/GitHub deploys, env-var secrets, Postgres-only DB integrations (Neon/Supabase), $0 Hobby / $20-seat Pro; **no documented background workers or cron** — scheduled jobs must be HTTP endpoints triggered externally. [doc: https://fastapicloud.com/pricing; doc: https://fastapicloud.com/docs/ — workers unverified, treated as absent]
- **RLS + PL/pgSQL triggers are portable** across RDS/Aurora/Neon/Supabase/self-host IF policies bind to a self-controlled session variable (e.g., `app.current_tenant`), never Supabase-only `auth.uid()`. [doc: https://www.postgresql.org/docs/current/ddl-rowsecurity.html]
- **RDS db.t4g.micro**: free tier first year, ~$12/mo after. Neon/Supabase-as-plain-PG remain connection-string pivots. [doc: https://aws.amazon.com/rds/postgresql/pricing/]
- **OpenRouter embeddings exist**: OpenAI-compatible `POST /api/v1/embeddings`, 37 models; default `openai/text-embedding-3-small` ($0.02/M tok). One `base_url` env var swaps providers. [doc: https://openrouter.ai/docs/api_reference/embeddings]
- **Vector store**: `pgvector` 0.8+ in the existing Postgres is the boring day-1 default at tens-of-thousands-of-chunks scale; Qdrant (Cloud free tier or self-host container) is the documented pivot behind a `VectorStore` protocol. [doc: https://www.postgresql.org/about/news/pgvector-080-released-2952/; doc: https://qdrant.tech/cloud/]
- **Playwright 1.64**: built-in `json` + `junit` reporters, `trace: on-first-retry`, official Test Agents (Planner/Generator/Healer) and `@playwright/cli` for coding agents. [doc: https://playwright.dev/docs/test-reporters; doc: https://playwright.dev/docs/test-agents]
- **Schemathesis 4.31**: actively maintained OpenAPI 3.1 contract testing, CLI + pytest plugin, JUnit reports. [doc: https://github.com/schemathesis/schemathesis]
- **testcontainers-python + pgTAP 1.3.4**: boring-standard for FastAPI+Postgres integration tests and trigger/RLS unit tests. [doc: https://github.com/testcontainers/testcontainers-python; doc: https://pgtap.org/]
- **React/Vite portability**: produce a static bundle; avoid framework-specific server APIs; AWS path = S3 + CloudFront or a standard static/container host.

---

## 2. Gap Analysis Summary (what exists vs. what this plan adds)

Existing and reused (not rewritten): `00-deconstruction.md`, BRD v2.3.0, PRD v2.0, `04-rbac-matrix.md`, `06-acceptance-tests.md`, `07-glossary.md`, `08-client-clarification-register.md`, `storage-architecture-draft.md` (S3 design, promote from DRAFT), `design_guideline.md` (Apple HIG + React/Vite structure), 6 capability spec deltas.

Superseded: `backend_database_structure.md` (830-byte Supabase sketch → replaced by artifact 11); `task_assignment.md` (Supabase/Vercel assumptions → replaced by artifact 18); `design.md` Decision 3 wording ("Supabase Row Level Security" → portable RLS; design.md updated).

New artifacts this plan authors (all inside `openspec/changes/lukla-ops-engine-planning/artifacts/` unless noted):

| Artifact | Title | Unblocks |
|----------|-------|----------|
| `10-technology-stack-and-decisions.md` | ADRs: stack, portability matrix, forbidden APIs | Everything |
| `11-database-schema-spec.md` | Full ERD, table inventory, migration ordering, RLS policies, triggers | Backend, tests |
| `12-api-contract-plan.md` + `contracts/openapi.yaml` | Endpoint inventory from 26 FRs + 6 views, error model, auth scheme, versioning | **All parallel dev** |
| `13-authn-authz-design.md` | JWT/session model, floor-tablet auth, RLS context propagation, B2B portal provisioning | Backend, frontend |
| `14-frontend-architecture.md` | Route map for 6 views, data layer, PWA offline (NFR-05 incl. tally terminal), component↔endpoint bindings | Frontend devs |
| `15-deployment-and-operations.md` | AWS topology, Docker, Terraform layout, environments, secrets, CI/CD, scheduled-jobs strategy, observability, backups, budget alternative | DevOps, deploy |
| `16-test-harness-and-agent-verification.md` | pytest/testcontainers, pgTAP, Schemathesis, Playwright E2E mapped to AT IDs, fixtures, evidence-bundle contract, agent invocation protocol | QA, review orchestrator |
| `17-semantic-search-module.md` | Fenced AI module: ingestion, query API, VectorStore protocol, feature flag, tenant filtering | AI dev (parallel) |
| `18-parallelization-and-workstreams.md` | Workstream dependency graph, contract-first slicing, per-dev briefs with stop conditions | Whole team |
| `19-business-defaults-register.md` | Configurable defaults for the 8 UNRESOLVED business items (OQ-1..OQ-9 + 08-register) | Payroll, QC |
| `tasks.md` (update) | New phases 6–9 + implementation workstreams | Tracking |
| `specs/agent-verifiable-testing/spec.md` (new delta) | Test-harness capability requirements | OpenSpec |
| `specs/semantic-search/spec.md` (new delta) | AI module capability requirements | OpenSpec |
| `design.md` (update) | Correct Decision 3 (Supabase→portable RLS), add D-1..D-5 | OpenSpec |

---

## 3. Key Architectural Commitments (the non-negotiables)

1. **Portability rules** (artifact 10): `DATABASE_URL` as the only host-specific backend config; RLS policies bind `current_setting('app.current_tenant')`; S3 access behind a `StorageService` interface (presigned URLs per `storage-architecture-draft.md`); AI calls behind one OpenAI-compatible client with `AI_BASE_URL` env var; vector store behind a `VectorStore` protocol (pgvector day-1, Qdrant pivot); React/Vite emits a static bundle with no framework-specific server APIs.
2. **Scheduled jobs as HTTP endpoints** (artifact 15): Saturday payroll (FR-10.1) and monthly overhead (FR-10.4) are internal POST endpoints invoked by AWS EventBridge Scheduler; pivot = cron-job.org / GitHub Actions schedule. Never in-process cron — preserves FastAPI Cloud pivot.
3. **Contract-first parallelization** (artifacts 12 + 18): `openapi.yaml` is authored BEFORE implementation; frontend devs build against Prism mock of the contract; backend devs implement to it; Schemathesis proves conformance. [doc: https://hub.docker.com/r/stoplight/prism/]
4. **DB-level invariants stay in the DB** (artifact 11): `validate_material_dispatch()` trigger, append-only ledger (no UPDATE/DELETE, reversal entries only), RLS on every tenant-scoped table — enforced identically on every Postgres host.
5. **Agent-verifiable evidence contract** (artifact 16): every test run emits `results.json` + `results.xml` (Playwright), `results-api.xml` (pytest), `schemathesis-report.xml`, and per-failure `trace.zip`/screenshots/video. One command (`pnpm verify` / `make verify`) runs the full bundle; a review-orchestrator agent parses JSON/XML only — never HTML.
6. **AI module is fenced** (artifact 17): separate router, separate config, feature-flagged (`AI_SEARCH_ENABLED`), read-only against operational data, tenant-filtered, deletable without touching the ledger core. Flagged as beyond-BRD scope (extension module; BRD addendum optional).

---

## 4. Execution Phases (planning artifacts) — STATUS: COMPLETED

**Phase A — Contracts first (sequential, blocks all parallel work): COMPLETED & APPROVED**
- [x] A1. Artifact 10 (`10-technology-stack-and-decisions.md`): Stack ADRs (FastAPI + PostgreSQL + React/Vite), portability matrix.
- [x] A2. Artifact 11 (`11-database-schema-spec.md`): Full DB schema, DDL, RLS policies (`app.current_tenant`), triggers, index design, migration ordering.
- [x] A3. Artifact 12 (`12-api-contract-plan.md`) + `contracts/openapi.yaml`: Complete OpenAPI 3.1 contract (69 operations, 69 unique `operationId`s, 111 schemas, 630 local `$ref`s). Validated with `validate-blueprint.py`.
- [x] A4. Phase A Review (`review/blueprint-contract-review.md`): Direct recovery review approved on 2026-10-13. Repaired defects: sewing tally fields (`cutBatchId`, `lineId`, `pieces`), QC assembly linkage (`assemblyId`, `defects`), FinancialRule schema composition, Idempotency-Key on `createClient`, aligned human API catalog.

**Phase B — Parallel specification modules: COMPLETED & APPROVED**
- [x] B1. Artifact 13 (`13-authn-authz-design.md`): JWT model, floor-tablet mandor auth, RLS session context propagation, B2B portal provisioning.
- [x] B2. Artifact 14 (`14-frontend-architecture.md`): 6 view route maps, React/Vite static frontend, offline PWA tally queue for 30-min resilience per NFR-05.
- [x] B3. Artifact 15 (`15-deployment-and-operations.md`): AWS ECS Express Mode + RDS + S3 + EventBridge cron endpoints + Terraform layout + budget EC2 fallback.
- [x] B4. Artifact 16 (`16-test-harness-and-agent-verification.md`): Deterministic test harness (Playwright E2E mapped 1:1 to AT-01..10 + PRD scenarios, Schemathesis contract tests, pytest+testcontainers, pgTAP, machine-readable `results.json`/JUnit).
- [x] B5. Artifact 17 (`17-semantic-search-module.md`): Fenced pgvector module with `VectorStore` protocol for Qdrant pivot, OpenRouter embeddings, read-only tenant isolation.
- [x] B6. Artifact 19 (`19-business-defaults-register.md`): 8 unconfirmed business items pinned as configurable defaults flagged `PRODUCTION_BLOCKED`.
- [x] B7. Phase B Review (`review/blueprint-phase-b-review.md`): Approved on 2026-10-14. Six non-blocking `LEARN_NOTE`s recorded and closed in Phase C.

**Phase C — Close-out & OpenSpec Integration: COMPLETED & APPROVED**
- [x] C1. Artifact 18 (`18-parallelization-and-workstreams.md`): 4-developer concurrent workstreams (Dev 1: Core Ledger & RBAC; Dev 2: Warehouse & MES; Dev 3: Payroll & QC Engine; Dev 4: Frontend & PWA) with exact inputs, operations, schemas, branch-safe boundaries, and stop conditions.
- [x] C2. OpenSpec integration: Updated `design.md` (Decision 5 added, Decision 3 corrected to portable RLS), capability specifications (`multi-tenant-platform`, `payroll-and-costing-engine`, `audit-and-sample-tracking`), and `tasks.md` (Phases 6.1–6.8 complete).
- [x] C3. Phase C Review (`review/blueprint-phase-c-review.md`): Approved on 2026-10-14. Closed all Phase B `LEARN_NOTE`s.
- [x] C4. Extended verification: `verify-traceability.ps1` updated with Phase C catalog assertions, negative controls, and contract validation.

**Implementation workstreams (defined in artifact 18, ready for handoff):**
WS-0 scaffold/CI → WS-1 ledger+RBAC (MOD-01) → WS-2 warehouse+guardrail (MOD-02) → WS-3 samples+MES (MOD-03/04) → WS-4 payroll+QC (MOD-05); WS-5 frontend views 1–6 (parallel per view after A3); WS-6 AI search (parallel, isolated); WS-7 test harness (contract tests from A3 day one, E2E per view); WS-8 AWS deploy + E2E validation of the 4 PRD scenarios.

---

## 5. Acceptance Criteria Evaluation

- [x] AC-1: `contracts/openapi.yaml` covers every endpoint implied by the 26 FRs and 6 UI views (69 paths/operations); passes custom schema validation and example checks via `validate-blueprint.py`.
- [x] AC-2: Artifact 11 defines every table, RLS policy, and trigger needed by the capability specs, including `validate_material_dispatch()` and append-only ledger, with migration ordering.
- [x] AC-3: Artifact 15 produces a runnable AWS topology (ECS Express Mode + RDS db.t4g.micro + S3 + CloudFront + EventBridge Scheduler) with Terraform layout and documented pivot runbook for FastAPI Cloud / Neon / Qdrant Cloud / another standard host.
- [x] AC-4: Artifact 16 defines the one-command verification bundle and machine-readable evidence files (`results.json`, JUnit XML); each AT-01..AT-10 / AT-R01..R08 and 4 PRD scenarios map to test IDs.
- [x] AC-5: Artifact 18 lets 4 devs start simultaneously with no unresolved interface question (every interaction references an OpenAPI operationId or DB object name).
- [x] AC-6: Every UNRESOLVED business item (OQ-1..OQ-9, 08-register) has a configurable default recorded in artifact 19 flagged `PRODUCTION_BLOCKED` — none silently invented.
- [x] AC-7: `openspec validate lukla-ops-engine-planning` passes (exit code 0); `tasks.md` accurately reflects completion.
- [x] AC-8: Portability rules (§3.1) are stated as explicit checks (no provider-specific imports, session variable `app.current_tenant`).

---

## 6. Non-Goals (Preserved Boundaries)

- Writing application code (this change strictly authors planning deliverables).
- Re-opening approved requirement documents (BRD/PRD stay fixed; AI module is an isolated extension).
- Statutory payroll (BPJS/PPh21), full financial accounting, logistics, MRP, native mobile — per BRD §3.2.
- Kubernetes, service mesh, multi-region — deliberately boring AWS topology.
- Runtime execution of PostgreSQL, Playwright, Schemathesis, or AWS infrastructure in this planning change.

---

## 7. Risks & Mitigations (Status)

- **FastAPI Cloud scheduled-job support unverified** → Mitigated: design uses HTTP-triggered jobs via EventBridge / external webhooks; works everywhere.
- **OpenAPI-first drift** → Mitigated: `openapi.yaml` authored and validated before coding; CI will check Schemathesis baseline against contract.
- **Scope creep via AI module** → Mitigated: fenced router + feature flag (`AI_SEARCH_ENABLED`) + read-only; excluded from core ledger/payroll path.
- **Junior team vs. Terraform** → Mitigated: flat `infra/` with `envs/dev` and `envs/prod`, verification commands per module.
- **Offline tally terminal (NFR-05)** → Mitigated: Artifact 14 defines IndexedDB queue + idempotency keys for 30-min offline operations.
- **OQ-9 rounding conflict** → Mitigated: Artifact 19 records default "remainder → factory reserve account" flagged `PRODUCTION_BLOCKED` and configurable.

---

## 8. Verification Results of Planning Suite

1. **OpenSpec Validation:** `openspec validate lukla-ops-engine-planning` passes with zero errors (exit code 0).
2. **Contract Schema & Reference Check:** `validate-blueprint.py` passes 69 operations, 69 unique IDs, 630 local `$ref`s, 111 component schemas, and 5 inline media examples.
3. **Traceability Verification:** `verify-traceability.ps1` passes all 26 PRD/FR identifiers, 20 source IDs, 8 RBAC roles, 4 closing scenarios, and production-blocked defaults (with one honest preserved WARN for FR-10.4 test coverage).
4. **Independent Review Approval:** Formal review records completed with APPROVED verdicts for Phase A (`blueprint-contract-review.md`), Phase B (`blueprint-phase-b-review.md`), and Phase C (`blueprint-phase-c-review.md`).
5. **Planning Boundary:** Application implementation, runtime tests, and cloud deployments remain explicitly gated for Phase D / implementation workstreams.
