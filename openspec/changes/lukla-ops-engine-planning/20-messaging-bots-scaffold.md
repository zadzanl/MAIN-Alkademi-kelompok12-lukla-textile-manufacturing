# 20 — Messaging & Notification Gateway: Breadth-First Scaffolding & Exploration

**Change:** `lukla-ops-engine-planning`  
**Status:** DRAFT / EXPLORATORY SCAFFOLD  
**Purpose:** Initial architectural breadth-first-search (BFS) scaffolding for integrating messaging platforms (Telegram & WhatsApp) into the Lukla Operations Engine. Intentionally preserves loose ends and flexibility for future implementation iterations.

---

## 1. Executive Framing & Architectural Tenet

The Lukla Operations Engine is an apparel manufacturing execution and double-entry accounting engine designed for a facility in Ciwidey, West Java, managing up to ~70 sewing stations and multi-tenant B2B Maklon production.

### Core Invariant
> **The core ERP/MES engine remains the authoritative source of truth. External messaging channels are unprivileged satellite consumers and notification sinks.**
> 
> Under no circumstance will third-party messaging transports (Telegram Bot API, Meta WhatsApp Cloud API) bypass Row-Level Security (RLS), mutate double-entry ledger state, or compromise shop-floor physical tracking.

---

## 2. Breadth-First-Search (BFS) Tradeoff Landscape

To ensure future architectural flexibility, three fundamental architectural dimensions have been evaluated:

```
                      [ CORE FASTAPI / POSTGRESQL ]
                                    │
                         (Atomic Event Emission)
                                    ▼
                          [ outbox_events ]
                                    │
                                    │ (Polled / Dispatched)
                                    ▼
                    [ NOTIFICATION DISPATCHER WORKER ]
                                    │
              ┌─────────────────────┴─────────────────────┐
              ▼                                           ▼
     [ Telegram Transport ]                     [ WhatsApp Cloud API ]
     - Zero recurring API fees                  - 95%+ penetration in West Java
     - Developer-friendly, fast setup           - Requires Meta Business Verification
     - Ideal for Phase 1 Validation             - Ideal for B2B Client Milestones
```

### Dimension A: Channel Strategy Comparison

| Attribute | Telegram Bot API | WhatsApp Business Cloud API | Webhook / Push |
|---|---|---|---|
| **Primary Audience** | Internal operations, managers, tech staff, early testers | B2B Maklon clients, factory owners, tailors | Third-party ERPs, client webhooks |
| **Cost Model** | **Free (zero per-message fee)** | Per 24-hr conversation fee (Meta IDR pricing) | Infrastructure bandwidth only |
| **Onboarding Friction** | Low: create bot via `@BotFather` in 2 minutes | High: Meta Business Manager, NIB/SIUP verification | Low: URL endpoint configuration |
| **Template Restrictions**| None (supports freeform Markdown/HTML) | Strict: Pre-approved HSM templates for utility/alerts | None |
| **Operational Fit** | **Phase 1 Validation & Spikes** | **Production B2B Client Rollout** | Future System Integrations |

### Dimension B: Event Ingestion Model

1. **Option 1 (Chosen Baseline): Transactional Outbox Pattern**
   - Core PostgreSQL transaction writes to business tables AND appends a row to `outbox_events`.
   - An external dispatcher worker polls undispatched rows and sends messages.
   - *Advantage:* Guaranteed consistency; failure in Telegram/WhatsApp network never rolls back a factory floor transaction.
2. **Option 2 (Alternative for future high volume): In-Memory Background Tasks / Redis Queue**
   - Direct Celery/ARQ/Redis worker dispatching from FastAPI.
   - *Tradeoff:* Adds Redis dependency; potential event loss on unexpected process crash.
3. **Option 3 (Loose End): PostgreSQL `LISTEN/NOTIFY`**
   - Trigger dispatches notification instantaneously via PostgreSQL pub/sub.
   - *Tradeoff:* Connection pooling (PgBouncer) complexities; requires long-lived listener connection.

---

## 3. Conceptual Outbox Schema Draft (Flexible)

```sql
-- Scaffolding Draft: outbox_events
-- Flexible JSON payload to allow schema evolution without migrations
CREATE TABLE IF NOT EXISTS outbox_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    event_type VARCHAR(64) NOT NULL,       -- e.g., 'ORDER_MILESTONE', 'PAYROLL_READY', 'BOTTLENECK_ALERT'
    aggregate_type VARCHAR(64) NOT NULL,   -- e.g., 'order', 'payroll_period', 'sewing_line'
    aggregate_id UUID NOT NULL,
    payload JSONB NOT NULL,                -- Event-specific context (order_no, client_name, pieces, timestamp)
    target_role VARCHAR(32),               -- Optional routing hint: 'CLIENT', 'OWNER', 'TAILOR', 'OPS'
    target_recipient_id UUID,              -- Optional explicit user/client ID
    dispatched BOOLEAN NOT NULL DEFAULT FALSE,
    dispatched_at TIMESTAMPTZ,
    retry_count INT NOT NULL DEFAULT 0,
    last_error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_outbox_pending 
    ON outbox_events (created_at) 
    WHERE NOT dispatched;
```

---

## 4. Candidate Event Catalog (Draft Ideas)

These events represent candidate triggers that can be incrementally connected to the outbox:

1. `production.order.milestone_reached`
   - *Trigger:* Order moves to `CUTTING_DONE`, `SEWING_IN_PROGRESS`, or `QC_COMPLETED`.
   - *Target:* External B2B Maklon Client.
   - *Sample Telegram Message:*
     ```text
     📦 Update Pesanan: ORD-2026-089 (Arctic Parka)
     Status: Pemotongan bahan (Cutting) selesai.
     Jumlah: 500 pcs telah dipindahkan ke Meja Jahit (Line 02).
     Estimasi QC: 18 Okt 2026.
     ```
2. `payroll.weekly.statement_ready`
   - *Trigger:* Saturday payroll period calculated and approved by Finance.
   - *Target:* Tailor Operator / Foreperson.
   - *Sample Message:*
     ```text
     💰 Rekap Upah Borongan Mingguan (Sabtu, 17 Okt 2026)
     Nama: Rudi S. (Line 03)
     Total Unit: 142 pcs
     Upah Borongan: Rp 852.000
     Uang Makan: Rp 106.500
     Total Diterima: Rp 958.500
     ```
3. `floor.operational.alert`
   - *Trigger:* Line downtime, excessive defect spike, or stock collision intercepted.
   - *Target:* Foreperson (Mandor) / Head of Operations.
   - *Sample Message:*
     ```text
     ⚠️ Peringatan Operasional: Line 01
     Terdeteksi 5 unit reject berturut-turut pada komponen Front Zipper.
     Mandor: Segera cek setelan mesin jahit #12.
     ```

---

## 5. Phased Rollout Horizons

```
HORIZON 1 (Immediate / Prototype)
└── Telegram Outbound Bot
    ├── Standalone Python dispatcher script / container
    ├── Consumes outbox_events via API service key
    └── Validates message delivery with 0 API cost

HORIZON 2 (Post-Core Stabilization)
└── Meta WhatsApp Cloud API Adapter
    ├── Implements Meta HSM template format
    ├── Binds factory SIM card and verified Meta Business Manager
    └── Pushes order milestones to external B2B clients

HORIZON 3 (Exploratory / Inbound Inquiries)
└── Read-Only Command Spikes
    ├── Inbound query: `/status <ORD-ID>` returns read-only progress
    ├── Inbound query: `/gaji` returns latest Saturday wage summary
    └── Fenced semantic search integration (Qdrant Q&A over factory SOPs)
```

---

## 6. Loose Ends & Leeway Register (Intentionally Unlocked)

The following design decisions are deliberately left open to give future implementation maximum flexibility:

1. **Contact Identification UX:**
   - *Option A:* User registers Telegram `@handle` or starts bot with a one-time OTP link from the PWA portal (`/start <token>`).
   - *Option B:* Administrator manually enters Telegram chat ID or phone number in user profile.
   - *Leeway:* Keep schema as flexible `channel_identities` table or JSON metadata on `app_users` and `clients`.
2. **Worker Runtime Environment:**
   - *Option A:* Serverless AWS Lambda polling on 1-minute EventBridge cron.
   - *Option B:* Lightweight background task running within the FastAPI container or ECS worker service.
   - *Leeway:* Keep worker communication over HTTP `/internal/jobs/dispatch-outbox`, agnostic of where the worker runs.
3. **Template Localization & Formatting:**
   - *Leeway:* Store templates as Python format strings or lightweight Jinja2 snippets, easily customized for Bahasa Indonesia factory phrasing without redeploying database schemas.
4. **Interactive Inbound Expansion:**
   - *Leeway:* Do not build conversational parsers or bot menus now. When needed, build as a separate read-only router pointing to existing `/api/v1` endpoints.

---
*Documented as an exploratory scaffolding artifact for the `lukla-ops-engine-planning` change.*
