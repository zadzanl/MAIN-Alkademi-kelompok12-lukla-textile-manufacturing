# Technical Design: Messaging & Notification Gateway

> [!IMPORTANT]
> **HANDOFF DIRECTIVE FOR DOWNSTREAM AGENT / IMPLEMENTER:**
> This design document represents an **initial planning and exploratory architectural baseline**. It outlines the decoupled transactional outbox architecture, transport adapters, and security guardrails.
> **THE DOWNSTREAM AGENT OR DEVELOPER WHO PICKS UP THIS CHANGE MUST:**
> 1. **Refine, enhance, sharpen, and harden** the outbox schema, retry backoff algorithms, and concurrency locking strategies.
> 2. Implement the exact service-principal authentication handshake for `POST /internal/jobs/dispatch-outbox` as defined in `10-technology-stack-and-decisions.md`.
> 3. Verify rate-limiting boundaries (Telegram 30 msgs/sec global limit) and design the dead-letter queue (DLQ) strategy for permanent delivery failures.
> 4. Ensure zero mutation logic is introduced into chat handlers; preserve PostgreSQL Row-Level Security (RLS) invariants.

## Context
Lukla Operations Engine manages contract garment manufacturing in Ciwidey, West Java (~70 sewing machines) across CMT, Semi-CMT, and Full-Package commercial schemes. While core operations are handled via a responsive React PWA and specialized touch terminals on the shop floor, stakeholders require timely asynchronous event notifications:
- B2B Maklon clients want real-time progress updates when cutting finishes or batches clear QC.
- Tailor operators on fluid piece rates need their Saturday wage summaries delivered to their mobile devices.
- Factory leadership requires instant alerts on line bottlenecks and defect rate spikes.

## Goals / Non-Goals

**Goals:**
- Implement an asynchronous Transactional Outbox pattern that records domain events atomically within core PostgreSQL transactions.
- Decouple third-party messaging transports (Telegram, WhatsApp) from the core ERP/MES lifecycle.
- Provide a modular transport interface starting with Telegram Bot API for zero-cost pipeline validation.
- Provide a clear extension path to Meta WhatsApp Business Cloud API for high-penetration client messaging.
- Guarantee that downstream messaging delivery failures or network timeouts never roll back core manufacturing or financial transactions.

**Non-Goals:**
- **Zero Chat Mutations:** Chat channels will not support data entry (no piece tallies, cutting logs, QC approvals, or payroll sign-offs via chat).
- **No Direct Core Database Access:** The notification worker will not connect directly to the core PostgreSQL instance as an administrative superuser; it interacts via authenticated service job endpoints.
- **No Shop Floor MES Chat:** Floor operators in Ciwidey will continue using the offline-capable touch-friendly PWA terminal.

## Architecture & Data Flow

```
┌────────────────────────────────────────────────────────┐
│               LUKLA CORE ENGINE (FASTAPI)              │
│                                                        │
│  [Domain Action] ──> [Atomic PostgreSQL Transaction]   │
│                              │                         │
│                              ├──> Mutate State Tables  │
│                              └──> Insert outbox_events │
└──────────────────────────────┬─────────────────────────┘
                               │
                               │ Polled by Scheduler / Lambda
                               ▼
┌────────────────────────────────────────────────────────┐
│         NOTIFICATION DISPATCHER WORKER SERVICE         │
│                                                        │
│  - Authenticates via X-Service-Principal               │
│  - Fetches pending outbox events (concurrency locked)  │
│  - Resolves recipient contact (Telegram / WhatsApp)    │
│  - Idempotently marks events as dispatched             │
└──────────────────────────────┬─────────────────────────┘
                               │
              ┌────────────────┴────────────────┐
              ▼                                 ▼
    [ Telegram Bot API ]              [ WhatsApp Cloud API ]
    - Zero cost / Free                - High Indonesian adoption
    - Markdown / HTML alerts          - Pre-approved HSM templates
    - Phase 1 validation              - Phase 2 commercial rollout
```

## Decisions

### Decision 1: Transactional Outbox Pattern over Direct Webhooks
- **Choice:** Domain mutations append event records to an `outbox_events` table within the same transaction. A separate worker dispatches messages asynchronously.
- **Rationale:** Direct synchronous webhooks to Telegram/Meta inside API request handlers introduce latency, risk thread starvation, and would cause domain transactions to fail if external chat APIs are unreachable.
- **Alternatives Considered:** In-memory background tasks (risk losing notifications if server restarts), Celery/Redis queue (adds an unnecessary infrastructure dependency at planning stage).

### Decision 2: Telegram-First Rollout with WhatsApp Adapter Interface
- **Choice:** Build and validate the end-to-end notification pipeline using Telegram Bot API first, while defining an abstract `NotificationTransport` interface for future Meta WhatsApp Cloud API integration.
- **Rationale:** Telegram provides instant, free API access via BotFather with zero registration overhead, allowing full functional verification of event formatting and delivery. WhatsApp Business Cloud API requires formal Meta Business verification (NIB/SIUP), phone number onboarding, and per-conversation billing, which can be deferred until business readiness is verified.
- **Alternatives Considered:** WhatsApp-only first (rejected due to immediate billing and account verification blockers), Dual parallel development (wastes resources before validating message formatting).

### Decision 3: Service-Principal Authentication Boundary
- **Choice:** The dispatcher worker interacts with the core engine via dedicated internal job endpoints (e.g., `POST /internal/jobs/dispatch-outbox`) using `X-Service-Principal` headers and mutual service tokens.
- **Rationale:** Aligns with `10-technology-stack-and-decisions.md §3` and prevents external integration scripts from bypassing tenant isolation or requiring broad database credentials.

## Risks / Trade-offs

- **[Risk: Recipient Contact Privacy & Cross-Tenant Leaks]** → **Mitigation:** Recipient routing resolves contact identifiers within the validated `tenant_id` scope. Telegram chat IDs and phone numbers are strictly isolated.
- **[Risk: Telegram API Rate Limits (429 Too Many Requests)]** → **Mitigation:** The dispatcher enforces a client-side token bucket rate limiter (maximum 30 messages/second globally; 1 message/second per individual chat) with exponential backoff.
- **[Risk: Duplicate Message Delivery]** → **Mitigation:** The outbox worker uses atomic `UPDATE ... RETURNING` with `FOR UPDATE SKIP LOCKED` or unique message idempotency keys so concurrent workers do not dispatch the same event twice.

## Migration & Rollout Plan

1. **Phase 1 (Scaffold & Outbox Integration):** Add `outbox_events` schema migration and event emission hooks to core domain services.
2. **Phase 2 (Telegram Worker Spike):** Deploy the standalone Telegram dispatcher worker and verify message delivery on staging using test bot credentials.
3. **Phase 3 (WhatsApp Cloud API Adapter):** Once Meta Business verification is established by Lukla management, implement the WhatsApp adapter implementing the `NotificationTransport` contract.
