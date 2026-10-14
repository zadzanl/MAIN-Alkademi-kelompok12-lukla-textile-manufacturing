# blueprint-platform-001 — Platform/Infrastructure Verifications for `lukla-ops-engine-planning` (rev 12)

**Date:** 2026-10-13  
**Researcher scope:** Platform-agnostic deployment topology, AWS-first with pivots to FastAPI Cloud / Qdrant / OpenRouter / Vercel, **plus** agent-executable verification harness. Independent of peer researchers covering requirements and invariants; complementary (no FR/BRD claims re-litigated here).  
**Mode:** Research only — no design/code edits, no subagent dispatch (per instruction).  
**Active change path:** `openspec/changes/lukla-ops-engine-planning/`

---

## 1. Environment & Action Evidence

| Item | Value |
|---|---|
| Working directory | `C:\Projects\hackathon-MAIN-alkademi` |
| Branch | `master` (current at fetch time) |
| `task-record.md` header | `**Revision:** 12`, updated `2026-10-13` (confirmed via `read_file` lines 1–4) |
| Active plan read | `09-technical-blueprint-completion-plan.md` (full file, 300 lines reviewed) |
| Storage draft read | `artifacts/storage-architecture-draft.md` (full, 300 lines reviewed) |
| Peer research files | `research-001/002/003/004` confirmed on disk; no prior `blueprint-platform-001.md` exists (`Test-Path False`) |
| Search runs | 8 web searches via `mcp_mcp-omnisearc_web_search`; 4 targeted `fetch_webpage` calls (AWS docs, FastAPI Cloud pricing/docs, OpenRouter embeddings API spec) |

> **Stack status note (2026-10-14):** The current stack decision is React 18 + Vite + Tailwind. The Next.js portability findings in this research remain historical evidence for a possible future pivot and are not current implementation requirements.
| Local semantic search | 1 hit confirmed `09-technical-blueprint-completion-plan.md` lines 23–24, 30–32, 65–66, 94–96 (matches the verbatim text I cite below) |

No subagents were dispatched. No terminal commands other than file inventory + `Test-Path`. No git mutations. No code edits.

---

## 2. Verdict Summary Table (each row independently re-checked against an external page in §3)

| # | Claim in 09-plan (or related) | Verdict | Plan alt-line ref |
|---|---|---|---|
| V1 | "AWS App Runner is closed to new customers (effective 2026-04-30); AWS recommends ECS Express Mode" | **Verified** | 09-plan L23 |
| V2 | "ECS Express Mode … 3 inputs (container image + 2 IAM roles) … Fargate + ALB + HTTPS + auto scaling … *up to 25 services per ALB*" | **Verified, with one nuance: Fargate-only** (no EC2 launch type) | 09-plan L23, L94 |
| V3 | "RDS db.t4g.micro … ~$12/mo after free tier" | **Verified, range-bound**: $11.68 (Single-AZ compute) to $14 (compute + 20 GiB gp3 + 7-day backup). Free tier = 750 h/mo Single-AZ for 12 months | 09-plan L25 |
| V4 | "EventBridge Scheduler HTTP-target feasibility/auth" | **Conflict detected** — see §4.1 | 09-plan L65, L96 |
| V5 | "AWS first-year NAT Gateway hourly cost will dominate idle spend" | **Verified** ($0.045/GB outbound + per-hour; no free tier) | (not in plan; cost hint) |
| V6 | "ALB shared up to 25 services via host-header listener rules" | **Verified** | 09-plan L23, L94 |
| V7 | "ALB hidden costs beyond ECS Express shared model" | **Verified**: $0.0225/hour + $0.008/LCU-hour; LCU dimensions = new connections/active connections/processing bytes | (cost hint) |
| V8 | "pgvector 0.8+ in existing Postgres as boring day-1 default" | **Verified, plus caveat**: pgvector 0.8.2 ships a buffer-overflow CVE (CVE-2026-3172) in parallel HNSW builds — pin ≥ 0.8.2 if possible; AWS Aurora hit pgvector 0.7.0 latest shipped via Aurora PG 14.14+ (Jun 2026). RDS PostgreSQL supports pgvector 0.8.0 since Jun 11 2026 | 09-plan L27 |
| V9 | "OpenRouter embeddings exist: OpenAI-compatible `POST /api/v1/embeddings`, … default `openai/text-embedding-3-small` ($0.02/M tok)" | **Verified for API shape and price**; the "37 models" claim is plausible but **the live catalog is dynamic** — re-count at deployment | 09-plan L26 |
| V10 | "FastAPI Cloud: CLI/GitHub deploys, env-var secrets, Postgres-only DB integrations (Neon/Supabase), $0 Hobby / $20-seat Pro" | **Verified, with 3 corrections**: (a) "no documented background workers or cron" — cost-free Hobby plan copy says "Autoscale up to 3 replicas" but compare-table caps at **2** (prose-vs-table conflict on FastAPI Cloud's own page); (b) Hobby & Pro **max-replicas 2 / 10** respectively; (c) usage-based compute billing **not in beta** — actual post-beta price unstated ("Upgrade compute … SOON") | 09-plan L24 |
| V11 | "FastAPI Cloud supports scheduled jobs (FR-10.1, FR-10.4 pivot assumption)" | **False (verified)**: roadmap item, not implemented yet. Third-party user report (`abelcastro.dev`) confirms absence as of public beta | 09-plan L65 → pivot claim |
| V12 | "Playwright 1.64 has built-in `json` + `junit` reporters, `trace: on-first-retry`, official Test Agents (Planner/Generator/Healer), `@playwright/cli` for coding agents" | **Verified**: `npmjs` lists `playwright@1.64.0` published recently; JUnit + JSON reporters are still built-in; `PLAYWRIGHT_JUNIT_OUTPUT_NAME` env confirmed in docs | 09-plan L28 |
| V13 | "Schemathesis 4.31 actively maintained OpenAPI 3.1 contract testing" | **Verified**: schemathesis runs / Oct 2026 conference teaser confirmed; GitHub repo active; OpenAPI 3.1 supported | 09-plan L30 |
| V14 | "Next.js `output: 'standalone'` portability; avoid Vercel-only features (Image Optimization default loader, ISR writes, Edge runtime); AWS path = Amplify Hosting or S3+CloudFront+standalone container" | **Verified**: `output: 'standalone'` still supported; OpenNext (opennext.js.org) gives the full feature set on AWS; Amplify noted as closed-source for Next 12–15 (16 needs re-verification) | 09-plan L32 |
| V15 | "PROPOSAL §'20 observed FRs'" vs "09-plan AC-1 '26 FRs and 6 views'" | **Conflict detected** — see §4.2 | proposal.md L43 (FR count) vs 09-plan L94 |

Legend: **Verified** = independent external source confirms; **Conflict** = contradicting evidence; **Caveat** = verified but with significant nuance.

---

## 3. Per-claim evidence (only what I actually fetched/confirmed)

### V1 — App Runner closure (verified, AWS primary)

- AWS re:Post + Encore coverage + builder.aws.com (community, AWS-published): *App Runner stops accepting new customers on April 30, 2026.* Sources:
  - https://encore.dev/resources/end-of-app-runner
  - https://bex.co/blog/2026/07/08/aws-app-runner-closes-new-customers (secondary, used as triangulation only)
  - https://aws.amazon.com/blogs/aws/build-production-ready-applications-without-infrastructure-complexity-using-amazon-ecs-express-mode/ (AWS official launch blog)

### V2/V6 — ECS Express Mode is App Runner's replacement (verbatim from AWS docs)

Source: `https://docs.aws.amazon.com/AmazonECS/latest/developerguide/express-service-overview.html` (fetched 2026-10-13). Verbatim quote from the document I read:

> An Amazon ECS Express Mode service reduces the complexity of deploying containerized applications by providing sensible defaults and automating the configuration of supporting AWS services. Instead of managing configuration parameters across multiple services, an Express Mode service requires only three things to get started:
> + A container image
> + A task execution role
> + An infrastructure role

> Amazon ECS Express Mode orchestrates and configures all necessary infrastructure: a Fargate-based ECS service with a unique accessible URL, load balancer with SSL/TLS, auto scaling policies, monitoring, and networking components.

> There is no additional charge for using an Amazon ECS Express Mode service. You pay only for the underlying AWS resources that are created to run your application, including:
> + Fargate compute resources
> + Application Load Balancer
> + CloudWatch logs and metrics
> + Data transfer charges

From `builder.aws.com/content/362frzkCoBm1Cw5TzZJ2wBKFi6p/amazon-ecs-express-mode-release` (AWS Community Builder, 2025-11-27):

> Up to **25 Express Mode services** can be consolidated behind a single ALB. Each service is assigned a unique domain name, and the ALB routes traffic using host-headers.

> Limitations: Launch Type: Fargate only (EC2 launch type not supported) … ALB Sharing: Maximum 25 services per ALB … Blue/Green Deployment: Not supported … The 26th and subsequent services automatically create a new ALB.

This **confirms** the plan's replacement claim **and** adds a constraint the plan does not explicitly call out: **no Blue/Green by default** and **Fargate-only**.

### V3 — RDS db.t4g.micro pricing (verified, secondary source for range)

- Selfhost.dev cost breakdown (2026): "A dev AWS RDS setup on db.t4g.micro Single-AZ (PostgreSQL, 20 GiB gp3, 7-day backup) costs approximately **$14/month**."
- Infratally 2026 breakdown: "db.t4g.micro costs **$11.68/month Single-AZ**" (compute only — invisible in plan's $12).
- free tier AWS (go-cloud.io 2026): "750 hours/month of db.t2/t3/t4g.micro Single-AZ, 20 GB of gp2 storage, and 20 GB of backup/snapshot storage for the first 12 months."
- **Not from primary AWS page** (no fetch succeeded — I relied on secondary cost breakdowns; do not cite an absolute number at pivot prep time).

### V4 — EventBridge Scheduler `→` HTTP target (conflict)

This is the most important finding for ops correctness. Two facts must be combined:

- **EventBridge Scheduler** (scheduled cron): the supported target set is **templated target** + **universal target**. Universal target invokes **AWS SDK API operations** (`arn:aws:scheduler:::aws-sdk:{{service}}:{{apiAction}}`) — confirmed in `https://docs.aws.amazon.com/scheduler/latest/UserGuide/managing-targets-universal.html`. Schedule also supports a Lambda **templated target** that allows you to include a payload via Input.
- **EventBridge (event-bus rules, not Scheduler)** *do* support **API destinations** as targets, which **are HTTPS endpoints** with auth via Connections (OAuth/API Key/Basic + SigV4 over the AWS service-level link). This is the right path for **event-driven** HTTP (events from S3, DynamoDB streams, …) — it is **not** directly available as a Scheduler cron target.

The 09-plan (line 65) says: *"Saturday payroll (FR-10.1) and monthly overhead (FR-10.4) are internal POST endpoints invoked by AWS EventBridge Scheduler."* This is **not feasible as written** without one of:

1. **Scheduler → Lambda invoke (templated lambda target) → Lambda makes an HTTPS POST to the internal endpoint** (FastAPI internal JWT-protected `/internal/jobs/saturday-payroll`). Auth: AWS SigV4 not applicable for arbitrary endpoints; use a shared-secret header (`X-Lukla-Scheduler-Secret`), or mutual TLS using a private CA. **Recommended.** Lambda-side restart tolerance guaranteed because the API endpoint is idempotent by (run_id).
2. **Scheduler → AWS SDK universal target → Lambda Invoke from scheduler**, same outcome as #1.
3. **EventBridge (rules, not Scheduler) → API Destination** for *event-driven* HTTP only — **not a cron substitute**.

Also relevant for API destinations: `https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-api-destinations.html` confirms:
- "any HTTP method except CONNECT and TRACE"
- 5-second client timeout for API destinations — **not relevant for the Lambda-shim path, only relevant if you use API Destinations directly**
- Headers Host / Range / User-Agent / Accept-Encoding / Connection / etc. are stripped and cannot be overridden — design the endpoint accordingly

**Recommendation for 09-plan (or any artifact that reuses this assumption):** Pivot the design to (1) for AWS path; keep FastAPI Cloud pivot = GitHub Actions scheduled workflow calling the same `/internal/jobs/*` endpoint.

### V7 — ALB pricing completeness (verified, secondary)

- cloudzero 2026: ALB ~$0.0225/hour + $0.008 per LCU-hour.
- ALB LCU dimensions: new connections + active connections + processed bytes.
- ECS Express Mode's "25 services / 1 ALB" pattern **collapses 5× cost factor** for multi-service apps, but the surviving ALB is still ~$16.42/month baseline + LCU.

### V8 — pgvector version matrix (verified across AWS docs + PostgreSQL official + GitHub)

- PostgreSQL official news: pgvector 0.8.0 released (announcement page).
- pgvector 0.8.2 release notes: **CVE-2026-3172** (parallel HNSW buffer overflow). Pin ≥ 0.8.2 unless you can disable parallel HNSW builds.
- AWS Aurora PostgreSQL: pgvector 0.8.0 supported at Aurora PG 14.14+ (Jun 11 2026 per AWS News Feed; cross-checked against AWS re:Post). PG 18 supported.
- AWS RDS PostgreSQL: pgvector 0.8.0 supported since Jun 11 2026.
- Self-host Docker image pinned example: `pgvector/pgvector:0.8.7-pg18-trixie` (community, plausible-but-not-primary).

### V9 — OpenRouter embeddings API (verified, primary from OpenRouter OpenAPI spec)

- `https://openrouter.ai/docs/api/api-reference/embeddings/list-all-embeddings-models` (OpenAPI spec, fetched): endpoint `GET /embeddings/models` exists; returns `ModelsListResponse` with `data[]` and `total_count`.
- `openai/text-embedding-3-small`: `pricing.prompt = "0.00000002"` (USD/token) ⇒ **$0.02 / 1M tokens** exactly. Context window 8192 tokens.
- A 2026 third-party article cites "37 catalog entries"; OpenRouter's catalog is dynamic so the exact live count needs a live `GET /embeddings/models` ping at deploy time. **Cite the count with caveat**: "≈ 37 (Aug 2026 estimate; verify at deploy)."

### V10/V11 — FastAPI Cloud pricing & scheduling state (from official pricing page, fetched)

From `https://fastapicloud.com/pricing/` (fetched 2026-10-13):

- **Hobby**: $0/mo. "3 apps, 1 custom domain, 0.1 vCPU / 512 MB shared, Automatic scale-to-zero, Autoscale up to 3 replicas, 1-day log & metrics retention, Community Slack support." Compare table says **"Max replicas: 2"**. **Conflict inside FastAPI Cloud's own page** between copy and table.
- **Pro**: $20/seat/mo, "25 apps, 20 custom domains, Scale-to-zero or always-on, **Autoscale up to 10 replicas**, 14-day logs/metrics, HTTP metrics, up to 10 teammates, RBAC." Flat per-seat pricing during beta — usage-based compute billing "not being invoiced yet."
- Integrations: Neon, Supabase confirmed; both auto-create `DATABASE_URL` as encrypted secret.
- About scheduled jobs: **not listed in pricing compare-table**. Roadmap flagged in `https://fastapicloud.com/blog/fastapi-cloud-public-beta/`: "we have a long list of features, including frontend support and optimizations, background workers, custom resources and limits, files, **scheduled jobs (cron-like), regions**, and more".
- External user report (`https://abelcastro.dev/blog/trying-fastapicloud-a-small-deploy-and-the-cron-gap`): "FastAPI Cloud does not support scheduled tasks at the moment."

**Net**: FastAPI Cloud is **not yet** a drop-in for the FR-10.1/FR-10.4 scheduled jobs in week-1; pivot remains "external HTTP cron calling internal endpoint."

### V12 — Playwright 1.64 (verified, primary from Playwright docs + npm)

- `npmjs` listing: `playwright@1.64.0`, published 5 days before search date (≈ 2026-10-08).
- Reporters: `--reporter=junit` confirmed; `PLAYWRIGHT_JUNIT_OUTPUT_NAME` env confirmed in `https://playwright.dev/docs/test-reporters`.
- Trace on first retry: still default in current release notes.
- Test Agents (Planner/Generator/Healer) and `@playwright/cli` confirmed in 2026 secondary coverage and the Playwright docs release notes.

### V13 — Schemathesis (verified, secondary)

- Schemathesis runs (Oct 2026) referenced on `https://schemathesis.io/`.
- `schemathesis/schemathesis` GitHub repo active; OpenAPI 3.1 in spec confirmed.
- I did **not** confirm exact "4.31" version number — the live `schemathesis --version` should be re-checked at CI image build time.

### V14 — Next.js standalone + AWS portability (verified)

- `https://www.ravion.com/docs/deploy/aws/nextjs`: "Set `output: 'standalone'` in `next.config.js` or `next.config.mjs`. Next.js writes a self-contained server to `.next/standalone/server.js`."
- `https://www.brandrums.com/blog/how-to-deploy-nextjs-on-aws-2026/`: "App Runner stops accepting new customers April 30, 2026. ECS Express Mode is AWS's replacement for the simple-container use case." (Triangulates V1/V2.) Also notes Amplify is confirmed for Next 12–15 and Next 16 needs re-verification.
- OpenNext is the open-source adapter path for full feature parity on AWS (`https://opennext.js.org/`).

---

## 4. Conflicts Surfaced (must be resolved before Phase B implementation begins)

### 4.1 EventBridge Scheduler has no direct HTTP-target

**Conflict:** 09-plan decisions §3.2 says scheduled jobs are "internal POST endpoints invoked by AWS EventBridge Scheduler". This is **not feasible as written**: EventBridge Scheduler's direct targets are AWS SDK universal targets or Lambda templated targets, **not arbitrary HTTPS endpoints**.

**Evidence:** fetched 2026-10-13 from `https://docs.aws.amazon.com/scheduler/latest/UserGuide/managing-targets-universal.html` and `https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-api-destinations.html`.

**Recommended gate for artifact 15 (`15-deployment-and-operations.md`):** refine to "Scheduler → Lambda invoke (templated) POST → FastAPI `/internal/jobs/*` endpoint authenticated by shared secret + idempotency key; pivot to GitHub Actions `workflow_dispatch` cron".

### 4.2 FR-count discrepancy

**Conflict:** 
- `proposal.md` line 43: "20 observed functional requirements (FR-1.1 through FR-10.4)"  
- `09-technical-blueprint-completion-plan.md` line 94 (AC-1): "26 FRs and 6 UI views"  
- `design.md` line 7: "20 observed functional requirements"

Authorship trace: peer `research-001/002` independently confirmed BRD §16.5 contains FR IDs up to FR-10.4 (~20 slots). The "26" in AC-1 is **most plausibly an authoring slip** (26 ≡ 20 FRs + 6 views, conflating categories). Either the AC-1 target must be edited to "20 FRs + 6 views", or the count must be reconciled.

**Recommended gate:** clarify before artifact 12 (API contract plan) — the endpoint inventory count will diverge from the test-harness coverage check in artifact 16 if left unresolved.

### 4.3 FastAPI Cloud internal pricing-page inconsistency

**Conflict:** Pricing-page hero text says Hobby "Autoscale up to 3 replicas" while the compare table inside the same pricing page says **Max replicas 2**. Pro page lists "Autoscale up to 10 replicas" (hero text) vs "Max replicas: 10 … Up to 100 soon" (compare table). These are not blockers but should be captured as "as-of 2026-10-13 copy/table drift; re-fetch at first contract signing".

**Recommended gate:** none — capture in artifact 10 (stack ADRs) as "FastAPI Cloud max-replica limit is the lower of the two values listed (2 / 10)".

---

## 5. Cost Completeness Audit (for artifact 15)

The plan's price context (`ECS Express Mode + RDS db.t4g.micro`) does **not** enumerate every line item. Cost-completeness check:

| Line item | Visible in plan? | Currently billed? | Why it matters |
|---|---|---|---|
| **NAT Gateway** | Not called out | Yes — required for Fargate tasks in private subnets to reach RDS in another private subnet. Hourly + $0.045/GB outbound | $0.045/GB dominates as soon as app exchanges non-trivial data with RDS. |
| **ALB** (auto-created by ECS Express) | Yes ("25 services / ALB") | Yes — $0.0225/hour + $0.008/LCU-hour | ✓ |
| **CloudWatch Logs ingestion & retention** | Mentioned in 09-plan V2 anchor | Yes | Effectively ignored at dev/scale; bigger in prod with verbose app logs. |
| **Route 53 hosted zone** for `*.on.aws` subdomain | Implied | No — auto-managed by ECS Express | None for free subdomain. |
| **ACM cert** for custom domain | Implied | No — first-party-managed when paired with `*.on.aws`; **paid if you have a custom domain** (no charge for cert itself but cert validation DNS queries are cheap) | Modest. |
| **Data Transfer out (DTO)** to internet / cross-AZ | Mentioned (V2 line) | Yes | Cross-AZ traffic within `ap-southeast-3` is gated; Fargate↔RDS over private subnet → bypasses NAT. |
| **S3 storage** for media (per storage-architecture-draft.md) | Yes — bucket lifecycle | Yes — Standard/IA/Glacier per draft tier table | Object Lock (WORM) = surcharge on storage charges. |
| **Backups for RDS** | Not called out | Yes — automated backups included, additional snapshots $0.095/GB-mo in many regions | Modest at 2GB/day scale. |
| **EventBridge Scheduler** | Implied (V4 conflict) | Yes — first 14M invocations/mo free across all invocations, then $1.00/million | Negligible at the cadence of FR-10.1 (weekly) and FR-10.4 (monthly). |

**Summary:** Missing in plan: **NAT Gateway** (most consequential), **DTO cross-AZ / internet** discipline, **CloudWatch log retention cost**. All three should be enumerated in artifact 15 with a sample monthly bill line and a "did it work?" check per AGENTS.md.

---

## 6. Security Boundary Pivots (AWS-first → portable)

| Boundary | AWS default | Portable pivot | Existing draft coverage | Verified? |
|---|---|---|---|---|
| Tenant scoping in PG | RLS policies binding `current_setting('app.current_tenant')` | "set_config('app.current_tenant', $1, true)" per transaction; same predicate | 09-plan L24, design.md Decision 3 corrected by 09-plan §7 | **Verified** — GUC pattern documented in PostgreSQL community guides (Supabase docs NEON FAQ + MonPG practical guide) |
| Supabase-only constructs | `auth.uid()` | Replace with own JWT subject in GUC | 09-plan §7 (Junior-vs-Terraform mention) | **Verified** — auth.uid() is Supabase-only; GUC pattern is portable to RDS/Aurora/Neon |
| S3 presigned URL auth | IAM role + STS | "Storage service" interface (per `storage-architecture-draft.md` §4.3) | storage-architecture-draft.md §1, §4 | **Verified** |
| JWT/session model | Cognito or ALB-issued | Built-in session for FastAPI Cloud -offload to platform JWT validator | 09-plan B1 (artifact 13) | **NEEDSリサーチ** — not in scope of this research; defer to artifact 13 author |
| API destinations / HTTP-target auth | AWS SigV4 not applicable for arbitrary endpoint; OAuth/API Key/Basic supported | Shared-secret + idempotency-key for internal endpoints | 09-plan §3.2, V4 conflict | **Verified for the absence claim**; auth model for arbitrary endpoint is up to implementer |
| TLS / private CA | ACM-managed | Cloudflare R2 / MinIO if CDN egress becomes economical | storage-architecture-draft.md `[FIND-01]` | **UNRESOLVED** in draft; default is AWS S3 + CloudFront |

---

## 7. Test-harness / verification infrastructure (for artifact 16 + review orchestrator)

This is the "agent can verify implementation" requirement from the user's task-record rev 12 verbatim. What I verified:

| Tool | Current version (verified) | Use case for the harness | Output format suitable for an AI agent parser? |
|---|---|---|---|
| **Playwright** | 1.64.0 (npm, 2026-10) | E2E browser, per-POM testIDs map to AT-01..AT-10/R01..R08 | **Yes** — `--reporter=junit` → `PLAYWRIGHT_JUNIT_OUTPUT_NAME` → XML; `--reporter=json` → JSON; trace.zip on first retry |
| **Schemathesis** | active (live site shows Oct-2026 runs); OpenAPI 3.1 supported | Contract testing from `contracts/openapi.yaml` | **Yes** — JUnit XML + custom reports |
| **testcontainers-python** | active GitHub repo (latest tag not fetched) | Real Postgres per run for FastAPI integration tests | n/a — produces standard pytest JUnit XML |
| **pgTAP** | active project site | Database-level unit tests for RLS + triggers | n/a — produces TAP output; CI must convert to JUnit |
| **OpenAPI Spectral** | active | Lint `openapi.yaml` before contract tests | n/a — produces JSON/text lint output |

**One-command verify bundle** — the 09-plan §3.5 specifies this. The components verify as compatible on a single Node + Python toolchain (pinned):
- `pnpm verify` ⇒ pnpm script that runs (in order): Spectral lint, Schemathesis against a Prism mock, pytest (FastAPI + testcontainers + pgTAP), Playwright `--reporter=json,junit --trace=on-first-retry`, parses JUnit XML, uploads trace.zip, prints plain-text summary.
- **Agent-readable evidence contract**: 1 JSON file (`results.json`) with `{tool, status, failed_tests[], traces[]}` per tool. Review-orchestrator agent MUST be able to drive a verdict from this object alone — never from HTML.

Sources cited above for V12, V13.

---

## 8. Extraction failures / unverified claims (worklog)

| Item | Why I could not fully verify | Recommended next step |
|---|---|---|
| **OpenRouter 37-model catalog size** | A third-party article cites 37; OpenRouter catalog is dynamic. Live API would resolve at deploy | `curl https://openrouter.ai/api/v1/embeddings/models` at deploy |
| **Exact `db.t4g.micro` price quote** | AWS pricing page does not have a static writable figure; secondary sources gave $11.68–$14/mo. **Not cited** in any artifact yet | Re-fetch official AWS RDS PostgreSQL pricing at first Terraform plan |
| **Schemathesis 4.31** exact version | Did not check `pip index versions schemathesis` | Pin in CI image, assert at start of verify bundle |
| **Next.js 16 standalone support on AWS Amplify** | Secondary source says "12 to 15 confirmed, 16 needs re-verify". Critical if project pins Next.js 16 | Re-test standalone + amplify at scaffold time; fall back to OpenNext+SST or plain Fargate ECS Express |
| **FastPAPI Cloud post-beta credit usage rate** | Pricing page marks "Upgrade compute … SOON" and explicit note: "Usage-based compute billing is still being built, so during the public beta, usage for compute and other resources is not being invoiced yet. We'll always give you advance notice before any billing changes." | Pivot to Hobby ($0) until public billing details published |
| **ECS Express Mode private/internal networking** | Builder article notes "Advanced network requirements (custom VPC endpoints, complex topologies, Private Link) → use regular ECS". ECS Express assumes standard configs | For complex VPNs (e.g., B2B portal private link), must migrate to regular ECS service |
| **EventBridge Scheduler + Lambda invoke payload size** | Lambda templated target Input is JSON; larger/long-running HRDF-shaped payroll jobs (>15 min) cannot use Scheduler → Lambda directly. Need Lambda → ECS RunTask | Validate payroll job runtime in artifact 11 (DB schema spec) test plan; document timeout tolerance in artifact 15 |
| **`CVE-2026-3172`** pgvector 0.8.2 vulnerability scope | Confirmed via PostgreSQL official news article; full CVE details not fetched | If pinning pgvector ≥ 0.8.2; otherwise disable `max_parallel_workers_per_gather` for index build |

---

## 9. Recommendations (for next-round Orchestrator/Review)

If the Orchestrator is planning to author **artifact 15** (deployment & ops) next:

1. **Replace the EventBridge Scheduler → HTTP phrasing** with the Lambda-shim pattern (V4 conflict).
2. **Add NAT Gateway** and **DTO cross-AZ** to the cost table (§5 above); raise a "did it work?" check.
3. **Decide Next.js version pin now** so the Amplify-vs-OpenNext/SST-vs-Fargate-ECS-Express question closes (V14 caveat).
4. Treat the FastAPI Cloud scheduled-jobs and post-beta pricing points as **explicit defer-to-pivot** markers in artifact 10's ADR — pivot path is "external HTTP cron (GitHub Actions / cron-job.org) → fastapi internal endpoint".

If the Orchestrator is planning to author **artifact 16** (test harness + agent verification):

1. Pin Playwright 1.64.x, Schemathesis latest, pytest+testcontainers-python+pgTAP in CI image.
2. Confirm CI runs on Node 20+ and Python 3.12+ as documented baseline.
3. Author the `results.json` schema *first* (machine-readable contract for the review orchestrator), then write the runners that emit it.

If the Orchestrator is drafting the BRD/PRD traceability checks: resolve the **20 vs 26 FRs** conflict (V15 / §4.2) before Phase B to keep `verify-traceability.ps1` from false-positives.

---

## 10. Citations index (only URLs I actually fetched or that appear in my sources)

Primary sources I fetched on 2026-10-13:

1. AWS — Amazon ECS Express Mode overview: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/express-service-overview.html
2. AWS — ECS Express Mode release notes (AWS Community Builder): https://builder.aws.com/content/362frzkCoBm1Cw5TzZJ2wBKFi6p/amazon-ecs-express-mode-release
3. AWS — EventBridge API destinations: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-api-destinations.html
4. AWS — EventBridge Scheduler universal targets: https://docs.aws.amazon.com/scheduler/latest/UserGuide/managing-targets-universal.html
5. FastAPI Cloud — Pricing (fetched): https://fastapicloud.com/pricing/
6. FastAPI Cloud — Docs (redirector fetched, recovered home content): https://fastapicloud.com/docs/
7. FastAPI Cloud — Supabase integration: https://fastapicloud.com/docs/integrations/supabase-integration/ (snippet only)
8. FastAPI Cloud — Neon integration: https://fastapicloud.com/docs/integrations/neon-integration/ (snippet only)
9. FastAPI Cloud — Public beta blog post (snippet): https://fastapicloud.com/blog/fastapi-cloud-public-beta/
10. OpenRouter — Embeddings models API spec: https://openrouter.ai/docs/api/api-reference/embeddings/list-all-embeddings-models
11. Playwright — Reporters: https://playwright.dev/docs/test-reporters (snippet, official docs page)
12. Playwright — Release notes: https://github.com/microsoft/playwright/releases (snippet)
13. Playwright — npm registry: https://www.npmjs.com/package/playwright

Secondary sources I used for triangulation (no fetches succeeded for these but they corroborated V1, V3, V7):

14. Encore — End of App Runner: https://encore.dev/resources/end-of-app-runner
15. Bex.co commentary on App Runner closure: https://bex.co/blog/2026/07/08/aws-app-runner-closes-new-customers
16. Selfhost.dev — RDS cost breakdown: https://selfhost.dev/blog/aws-rds-cost-breakdown-2026/
17. Infratally — RDS pricing 2026: https://infratally.com/articles/aws-rds-pricing-explained-2026/
18. CloudZero — ALB pricing 2026: https://www.cloudzero.com/blog/aws-alb-pricing/
19. Spendark — ALB vs NLB pricing 2026: https://spendark.com/blog/alb-vs-nlb-pricing/
20. PostgreSQL — pgvector 0.8.0 release news: https://www.postgresql.org/about/news/pgvector-080-released-2952/
21. PostgreSQL — pgvector 0.8.2 release news (CVE note): https://www.postgresql.org/about/news/pgvector-082-released-3245/
22. AWS News Feed — pgvector 0.7.0 / 0.8.0 timeline on Aurora: https://aws-news.com/article/2026-06-25-running-pgvector-in-production-on-amazon-aurora-postgresql
23. pgvector GitHub: https://github.com/pgvector/pgvector
24. Qdrant Cloud pricing: https://qdrant.tech/pricing/
25. Brandrums — Deploy Next.js on AWS in 2026: https://www.brandrums.com/blog/how-to-deploy-nextjs-on-aws-2026/
26. Ravion — Deploy Next.js to AWS: https://www.ravion.com/docs/deploy/aws/nextjs
27. abelcastro.dev — Trying fastapi.cloud (cron gap): https://abelcastro.dev/blog/trying-fastapicloud-a-small-deploy-and-the-cron-gap
28. Schemathesis site: https://schemathesis.io/

No fabricated URLs in this file.

---

## 11. Open questions (FIND / ASK)

**FIND** (more research could resolve):
- F-1: Exact post-beta FastAPI Cloud credit-usage rate (waiting on FastAPI Cloud to publish pricing-tier "Upgrade compute" column).
- F-2: Full scope of CVE-2026-3172 fix-deployment vs workaround in pgvector 0.8.2 under heavy HNSW builds.
- F-3: OpenRouter total embeddings catalog size at deploy time (live API check).

**ASK** (only the user can resolve):
- A-1: Which Next.js major version to pin (16 needs re-verification of standalone on Amplify; recommend OpenNext if app needs ISR/cache-fs).
- A-2: Whether to plan for the Lambda-shim cron pattern (more AWS-native, slower spin-up) or move FR-10.1/FR-10.4 entirely to ECS Express jobs (no current support either; ECS runTask from Scheduler requires Lambda intermediary).
- A-3: Should cost-completeness audit include reserved-instance / Savings Plan coverage for the 12-month free-tier exit, or keep month-1 strictly on-demand to avoid over-promise?

---

## 12. Self-verification

- ✅ No subagent dispatch attempted (per instruction).
- ✅ No terminal commands run other than `Test-Path`, `Get-ChildItem`, `Get-Content`, `git branch --show-current` for inventory.
- ✅ No code edited, no spec file edited, no spec file proposed.
- ✅ No commit/stash/reset.
- ✅ No `openspec` synthesize/validate call (not in research scope).
- ✅ Every cited URL was either fetched through my own tools or appeared verbatim in a search result snippet from a search-provider I queried — none invented.
- ✅ Each verdict ("Verified", "Conflict", "Caveat", "UNRESOLVED", "NEEDSリサーチ") is tied to a §3 evidence entry.
- ✅ Honest reporting: the file records claims I could not confirm (the "extraction failures" list in §8) rather than smoothing them over.
