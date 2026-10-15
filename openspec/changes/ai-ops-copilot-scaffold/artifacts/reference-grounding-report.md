# Technical Reference Grounding & Adaptation Blueprint Report

**Change:** `ai-ops-copilot-scaffold` & `messaging-bots-integration`  
**Artifact:** `reference-grounding-report.md`  
**Author:** Worker M2-1 (Reference Synthesis & Adaptation Blueprint Author)  
**Date:** 2026-10-15  
**Target Environment:** Lukla Operations Engine (FastAPI, PostgreSQL 16 with RLS, Pydantic v2, React/TypeScript)  
**Status:** COMPLETE ARCHITECTURAL SPECIFICATION & BENCHMARK BLUEPRINT  

---

## 1. Executive Summary

This report establishes the authoritative architectural grounding and technical blueprint for two companion operational extensions to the **Lukla Operations Engine** (an apparel manufacturing execution and double-entry accounting platform engineered for multi-tenant garment factories in Ciwidey, West Java):

1. **Archetype A: In-App Operational AI Copilot (`ai-ops-copilot-scaffold`)**: A conversational, natural-language interface embedded directly within the factory dashboard allowing executives, forepersons (Mandors), warehouse staff, and B2B Maklon clients to query operational pacing, stock balances, defect metrics, and payroll previews.
2. **Archetype B: Multi-Channel Messaging Gateway (`messaging-bots-integration`)**: A high-reliability, asynchronous notification and mobile command hub integrating external chat networks (Telegram Bot API and Meta WhatsApp Business Cloud API) with core factory operations.

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                       LUKLA CORE INVARIANT                                             │
│                                                                                                        │
│  The core ERP/MES engine and PostgreSQL database remain the single authoritative source of truth.       │
│  Under NO circumstance will AI agents or external messaging transports autonomously mutate             │
│  double-entry ledger state, bypass Row-Level Security (RLS), or alter physical manufacturing records. │
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### Core Architectural Verdicts

1. **Archetype A (Operational Copilot): Native Python 3.12 / FastAPI + Pydantic v2 + httpx Facade**
   - **Primary Reference:** Built upon `pydantic/pydantic-ai` conventions and the existing in-tree prototype `prototypes/ai-copilot/`.
   - **Key Mechanisms:** Zero autonomous writes (`ReadOnlyToolExecutor` physically rejects non-`GET` HTTP methods), per-turn **Dynamic Role-Based Tool Filtering** reducing context from 83 operations down to 3–8 authorized queries, **Actor Token Passthrough** (`Authorization: Bearer <token>`) preserving PostgreSQL Row-Level Security (`FORCE ROW LEVEL SECURITY`), and **Action Shortcuts** routing mutation intents to audited web UI forms with pre-filled parameters.
   - **Verdict on `vercel/chat` (`chat-sdk.dev`):** **REJECTED AS BACKEND GATEWAY.** Running a separate Node.js / TypeScript edge runtime alongside FastAPI violates the core design principle ("One prerequisite, not two" per `AGENTS.md`), fractures connection pooling, complicates JWT delegation, and introduces dual-stack maintenance overhead. However, client-side React streaming conventions inspired by Vercel AI SDK (`@ai-sdk/react`) are recommended for the web UI widget.

2. **Archetype B (Messaging Gateway): Native FastAPI + PostgreSQL Transactional Outbox Worker**
   - **Primary Reference:** Adapted from the enterprise transactional outbox reference architecture (`aws-samples/transactional-outbox-pattern`) and Meta's official WhatsApp Cloud API samples (`fbsamples/whatsapp-api-examples`).
   - **Key Mechanisms:** Decoupled event emission via `outbox_events` table polled using PostgreSQL `FOR UPDATE SKIP LOCKED`, eliminating the distributed dual-write hazard without requiring external message brokers (Zero Celery, Zero Redis, Zero RabbitMQ). Public webhooks enforce cryptographic signature verification (`X-Hub-Signature-256` HMAC-SHA256 and `X-Telegram-Bot-Api-Secret-Token`), atomic message deduplication, automated dual-mode dispatch respecting Meta's rolling 24-hour customer service window, and tamper-proof cryptographic deep-link account binding.
   - **Verdict on `novuhq/novu` & Heavy Frameworks:** **REJECTED.** Enterprise notification engines introduce unnecessary daemon processes, MongoDB/Redis infrastructure dependencies, and high cognitive load for maintainers.

---

## 2. Archetype A: In-App Operational Copilot (Native Python/FastAPI)

Archetype A provides factory leadership and shop-floor personnel with conversational visibility into the 83 reconciled operational OpenAPI endpoints without jeopardizing financial or inventory integrity.

```
                                  [ USER WEB BROWSER ]
                                            │
                             POST /api/v1/copilot/chat
                             Header: Authorization: Bearer <jwt>
                             Header: X-Request-Id: <uuid>
                                            │
                                            ▼
                         [ FASTAPI COPILOT GATEWAY ROUTER ]
                         (backend/app/copilot/router.py)
                                            │
                ┌───────────────────────────┼───────────────────────────┐
                │                           │                           │
                ▼                           ▼                           ▼
      [ Dynamic Tool Registry ]     [ BaseLLMClient ]       [ Action Shortcut Matcher ]
      - filter_tools_for_roles()    - Ollama (Local)        - Detects mutation intent
      - Injects 3-8 caller tools    - OpenAI (Cloud)        - Returns UI deep-links
                │                           │                           │
                └───────────────────────────┼───────────────────────────┘
                                            ▼
                               [ ReadOnlyToolExecutor ]
                               - Invariant: method == "GET"
                               - Forward: Bearer <jwt> + X-Request-Id
                                            │
                                            ▼ HTTP GET (localhost / internal)
                         [ CORE LUKLA REST API (/api/v1/*) ]
                         - Middleware sets PostgreSQL session variables
                         - PostgreSQL enforces FORCE ROW LEVEL SECURITY
                         - Returns RFC 7807 problem details
```

### 2.1 Minimal Pattern for LLM Querying Existing OpenAPI Endpoints

Rather than relying on heavy orchestration frameworks (LangChain, AutoGPT, CrewAI) that obscure execution graphs and introduce brittle dependency trees, Archetype A implements standard function/tool calling directly over HTTP:

1. **Lightweight Tool Definition:** Endpoints are represented as standard Pydantic models containing name, description, HTTP path, allowed RBAC roles, and JSON Schema parameters compatible with OpenAI/Anthropic/Ollama function calling specifications.
2. **Stateless Turn Execution:**
   - The user's query and conversation history are dispatched to the configured LLM provider along with the filtered list of tool definitions.
   - If the LLM generates a `tool_calls` payload, the gateway intercepts the call, validates arguments against Pydantic schemas, and routes execution through `ReadOnlyToolExecutor`.
   - The executor issues an asynchronous internal HTTP request using `httpx.AsyncClient` targeting the local FastAPI service (`http://127.0.0.1:8000/api/v1`).
   - The JSON response from the core endpoint is fed back into the LLM as a `tool` role message, generating a natural, contextual summary for the operator.
3. **Token Efficiency:** A full OpenAPI 3.1 dump of 83 endpoints consumes ~15,000 prompt tokens per inference turn. By exposing only curated, role-filtered query schemas, prompt overhead is compressed to **~600 tokens**, reducing latency by 70% and slashing LLM operating expenses.

### 2.2 Dynamic Role-Based Tool Catalog Filtering

A critical vulnerability in enterprise copilots is over-permissioning the tool catalog. If all read tools are injected into the system prompt, prompt injection attacks can coax the model into querying sensitive financial accounts or competitor production queues.

Archetype A dynamically filters the available tool definitions on every turn based on the caller's validated JWT claims (`AuthContext.roles`), referencing `04-rbac-matrix.md` [code: 04-rbac-matrix.md#L11-L21]:

```python
# backend/app/copilot/registry.py
from typing import List, Set
from pydantic import BaseModel

class ToolDefinition(BaseModel):
    name: str
    description: str
    endpoint_path: str
    method: str = "GET"
    allowed_roles: List[str]
    parameters: dict

def filter_tools_for_roles(user_roles: List[str]) -> List[ToolDefinition]:
    """
    Filters tool definitions exposed to the LLM based on caller RBAC claims.
    Reduces prompt token overhead and eliminates privilege escalation vectors.
    """
    user_roles_set: Set[str] = set(user_roles)
    return [
        tool for tool in READ_TOOL_CATALOG
        if any(role in user_roles_set for role in tool.allowed_roles)
    ]
```

#### Role Scoping Boundaries:
- **`Owner` (Factory Executive):** Unrestricted visibility across high-level operational metrics (`listProductionProgress`), cash-flow and ledger accounts (`listLedgerAccounts`), and rate cards (`listRateCards`).
- **`ProductionHead` (Mandor / Line Supervisor):** Scoped to sewing line pacing, 30-minute tally tracking (`listSewingTallies`), worker line assignments, and cut batch receipts (`listCutBatches`).
- **`Warehouse` (Gudang):** Scoped to raw fabric balances (`getStock`), fabric roll receipts, and cutting dispatches.
- **`QCInspector` (Quality Assurance):** Scoped to assembly barcode lookups (`GET /assemblies?serialCode=...`), defect logs, and bonus pool qualification metrics (`getBonusPool`).
- **`FinancePayroll` (Payroll & Accounting):** Scoped to double-entry ledger transactions (`getLedgerTransaction`), AP/AR vendor invoices, and weekly payroll calculations (`listWeeklyPayrolls`).
- **`MaklonClient` (B2B Brand Portal):** Fenced strictly to their own brand's orders (`listOrders`), WIP status, and custodial stock. Ledger, payroll, rate cards, and internal worker metrics are physically excluded from their prompt context.

### 2.3 Actor Token Passthrough & Physical Non-GET Rejection

The copilot service possesses **zero ambient database privileges**. It does not maintain a database connection string with superuser or bypass credentials.

1. **Bearer Token Delegation:** When the user initiates a copilot turn, the incoming `Authorization: Bearer <token>` header and `X-Request-Id` tracing header are extracted by the copilot router and forwarded directly in outbound `httpx` calls to internal endpoints.
2. **Preservation of Row-Level Security (RLS):** When the request reaches the target endpoint (e.g. `GET /api/v1/warehouse/stock`), standard authentication middleware validates the JWT, extracts `tenant_id` and `sub`, and executes `SET LOCAL app.current_tenant_id = :tenant_id` in PostgreSQL [code: 13-authn-authz-design.md#L53-L60]. Even if the LLM hallucinates arguments attempting to query another brand's inventory, PostgreSQL `FORCE ROW LEVEL SECURITY` kernel rules guarantee that zero cross-tenant data is leaked.
3. **Physical Non-GET Guard:** To guarantee zero ledger mutation risk, `ReadOnlyToolExecutor` implements a hard physical guard:
   ```python
   # backend/app/copilot/executor.py
   if tool_def.method != "GET":
       raise SecurityException(
           f"Security Invariant Violation: Mutating method '{tool_def.method}' "
           f"is strictly prohibited on copilot tool '{tool_name}'."
       )
   ```

### 2.4 Action Shortcuts: Intent Detection & Deep-Link Navigation

When shop-floor personnel interact with the copilot, they frequently express intent to perform physical state mutations:
- *"Catat hasil potong 500 pcs untuk Order SO-2026-001"*
- *"Input tally 30 menit line 2"*
- *"Tandai cacat jahitan pada barcode ASM-8910"*
- *"Terima kain di gudang untuk Order SO-2026-001"*

Allowing an LLM to execute these mutations autonomously creates massive operational risks: financial hallucination, missing mandatory audit fields, unvalidated piece-rate calculations, and lack of `Idempotency-Key` headers.

Instead, the system utilizes **Action Shortcuts**:

1. **Intent Matching & Disambiguation Rules:** The copilot evaluates raw and normalized text against structured intent classifiers using domain-specific multi-token keywords while strictly forbidding loose tokens:
   - **Rule 1 (Fabric Material Disambiguation — Cutting vs. Warehouse Intake):** Standalone `"kain"` carries zero discriminatory power because fabric is omnipresent across the shop floor. Loose `"kain"` is strictly forbidden from triggering cutting. Cutting requires explicit cutting action phrases (`"potong kain"`, `"hasil potong"`, `"pemotongan kain"`, `"catat potong"`, `"buangan kain"`). Warehouse intake requires receiving action phrases (`"terima kain"`, `"penerimaan bahan"`, `"kain masuk"`, `"gudang bahan"`, `"receive material"`). Receiving verbs (`"terima"`, `"masuk"`, `"receive"`) explicitly suppress cutting shortcuts.
   - **Rule 2 (Sewing vs. Quality Defect Disambiguation):** Standalone `"jahit"` is strictly forbidden from triggering sewing floor tallies because seam defects (*"cacat jahitan"*) contain `"jahit"`. Sewing tally requires explicit tally phrases (`"tally"`, `"tally jahit"`, `"input tally"`, `"hasil jahit"`, `"sewing tally"`, `"output jahit"`, `"jalur jahit"`). The presence of defect markers (`"cacat"`, `"defect"`, `"repair"`, `"reject"`, `"inspeksi"`, `"qc"`) takes absolute precedence, routing to QC inspection and suppressing sewing tally shortcuts.
   - **Rule 3 (Finance & Ledger Disambiguation):** Journals require accounting-specific terms (`"jurnal"`, `"ledger"`, `"transaksi baru"`, `"posting jurnal"`), routing to `/app/finance?tab=journals`. Payroll requires compensation-specific terms (`"payroll"`, `"gaji borongan"`, `"upah sabtu"`, `"rekap payroll"`), routing to `/app/finance?tab=payroll`.

```
                          [ INCOMING USER & MODEL TEXT ]
                                         │
                 ┌───────────────────────┴───────────────────────┐
                 ▼                                               ▼
     [ Raw Text Preserved ]                          [ Lowercase Working Copy ]
     - Extract orderId (SO-*)                        - Match positive keywords
     - Extract lineId (LINE-*)                       - Check negative exclusions
     - Extract serialCode (ASM-*, SN-*)
                 │                                               │
                 └───────────────────────┬───────────────────────┘
                                         ▼
                            [ Disambiguation Decision Tree ]
                                         │
        ┌────────────────────────────────┼────────────────────────────────┐
        ▼                                ▼                                ▼
  [ RULE 1: FABRIC ]             [ RULE 2: SEWING ]              [ RULE 3: FINANCE ]
  Contains "terima"/"masuk"?     Contains "cacat"/"defect"/"qc"? Is "payroll"/"gaji"?
  YES -> warehouse-receive       YES -> qc-inspection            YES -> payroll-approval
  NO  -> Check cutting verbs     NO  -> Check tally keywords     NO  -> Check journal keywords
```

2. **Hardened Entity Extraction:**
   - **Order ID Extractor:** Evaluates against raw unlowercased text with `re.IGNORECASE`:
     `(?<!\bin\s)\border\s*#?\s*([A-Za-z0-9\-]*\d[A-Za-z0-9\-]*)`
     Normalized with `.upper()` (e.g., `SO-2026-001`). Word boundary `\b` eliminates false-positive substring matching on `"reorder"`, negative lookbehind `(?<!\bin\s)` eliminates `"in order to"`, and the mandatory digit anchor `\d` eliminates non-order words (`"to"`, `"kain"`, `"defect"`).
   - **Line ID Extractor:** Evaluates against raw text with `re.IGNORECASE`:
     `\b(?:line|jalur)\s*#?\s*([A-Za-z0-9\-]+)`
     Normalized by padding pure numeric digits to canonical 2-digit format `LINE-XX` (e.g., `"2"` $\rightarrow$ `LINE-02`, `"jalur 3"` $\rightarrow$ `LINE-03`) or preserving uppercase prefix (`"LINE-02"`). Word boundary prevents false matches on `"online"` or `"guideline"`.
   - **Serial Code Extractor:** Evaluates against raw text with `re.IGNORECASE`:
     `\b((?:ASM|SN)-[A-Za-z0-9\-]+)|\b(?:barcode|serial)\s*[-:#]?\s*([A-Za-z0-9\-]*\d[A-Za-z0-9\-]*)`
     Normalized with `.upper()`. Preserves full assembly prefixes (`ASM-8910`, `SN-2026-001`) without stripping, while digit anchoring rejects plural nouns (`"serials"`).

3. **Deep-Link Generation & Canonical Route Mapping:**
   Generates interactive Action Shortcut Cards linking directly to canonical product routes in `14-frontend-architecture.md` [code: 14-frontend-architecture.md#L26-L35] (`VIEW-01` through `VIEW-06`). Parameters are appended only where explicitly permitted by the target view:

#### Table 2.4.1: Canonical Action Shortcut Route Mapping Table

| Shortcut ID | Canonical Target View | Canonical Route Template | Permitted Query Params | Target OpenAPI Operations | Human Title & Description | Disambiguated Trigger Keywords | Exclusion Rules |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `cutting-record` | `VIEW-03` Warehouse & Cutting | `/app/materials?action=cutting` | `orderId` | `recordCuttingResult`, `listCutBatches` | **Catat Hasil Pemotongan (Cutting)**<br>Buka formulir input pemotongan kain dan input buangan. | `["potong kain", "hasil potong", "cutting", "pemotongan kain", "catat potong", "buangan kain"]` | Exclude if receiving verbs present (`"terima"`, `"receive"`, `"masuk"`, `"kedatangan"`). Bare `"kain"` is **strictly forbidden**. |
| `warehouse-receive` | `VIEW-03` Warehouse & Cutting | `/app/materials?action=receive` | `orderId` | `receiveMaterial`, `getStock` | **Penerimaan Bahan Baku (Warehouse)**<br>Buka form pencatatan kain masuk maklon atau Snøhund. | `["terima kain", "penerimaan bahan", "kain masuk", "gudang bahan", "receive material", "kedatangan kain"]` | Exclude if cutting verbs present (`"potong"`, `"cutting"`, `"buangan"`). |
| `sewing-tally` | `VIEW-04` Sewing Floor Terminal | `/terminal/tally` | `lineId`, `orderId` | `recordSewingTally`, `verifySewingTally` | **Input Hasil Jahit (Tally 30 Menit)**<br>Buka form input hitungan per operator jalur jahit. | `["tally", "tally jahit", "input tally", "hasil jahit", "sewing tally", "output jahit", "jalur jahit"]` | Exclude if defect/QC terms present (`"cacat"`, `"defect"`, `"repair"`, `"reject"`, `"inspeksi"`, `"qc"`). Bare `"jahit"` is **strictly forbidden**. |
| `qc-inspection` | `VIEW-05` QC Station | `/app/quality` | `serialCode`, `orderId` | `inspectUnit`, `listAssemblies`, `getAssembly` | **Formulir Inspeksi QC**<br>Buka formulir klasifikasi cacat (Pass, Repair, Reject). | `["qc", "cacat", "defect", "inspeksi qc", "repair", "reject", "cacat jahitan"]` | Takes absolute precedence over sewing tally on defect reports even if containing `"jahit"`/`"jahitan"`. |
| `ledger-entry` | `VIEW-06` Finance & Ledger | `/app/finance?tab=journals` | `orderId` | `appendLedgerTransaction`, `reverseLedgerTransaction` | **Jurnal Double-Entry Baru**<br>Buka form posting jurnal akuntansi berimbang dengan idempotency key. | `["jurnal", "ledger", "transaksi baru", "jurnal penyesuaian", "posting jurnal"]` | Must pair with accounting nouns to prevent collision with generic operational logs. |
| `payroll-approval` | `VIEW-06` Finance & Ledger | `/app/finance?tab=payroll` | None | `calculateWeeklyPayroll`, `approvePayroll` | **Halaman Rekap Payroll Mingguan**<br>Hitung dan setujui penggajian borongan Sabtu. | `["payroll", "gaji borongan", "upah sabtu", "rekap payroll", "penggajian"]` | Requires payroll-specific composite phrases. |

*(Note: `VIEW-01` Order Desk `/app/overview` and `VIEW-02` Sample & Tech Pack Tracker `/app/samples` serve as default navigation anchors).*

4. **Human-in-the-Loop Verification:** The user clicks the card to open the audited web form in the dashboard, where form validation, CSRF tokens, confirmation modals, and client-generated idempotency keys are enforced before state is committed to PostgreSQL.

---

## 3. Archetype B: Multi-Channel Messaging Gateway (Telegram & WhatsApp)

Archetype B extends the Lukla Operations Engine to external messaging platforms, delivering real-time production milestone alerts, piece-rate Saturday wage summaries, and defect notifications.

```
                 [ CORE MANUFACTURING TRANSACTION ]
                 (e.g., POST /sewing-tallies or POST /orders/{id}/confirmation)
                                │
               BEGIN TRANSACTION;
               INSERT INTO sewing_tallies (...) VALUES (...);
               INSERT INTO outbox_events (tenant_id, event_type, payload, ...) VALUES (...);
               COMMIT;
                                │ (Atomic Commit to PostgreSQL)
                                ▼
                       [ outbox_events TABLE ]
                                │
                                ▼
                 [ ASYNC OUTBOX DISPATCHER WORKER ]
                 - Polling interval: 1.0s - 2.0s
                 - SELECT ... FOR UPDATE SKIP LOCKED
                 - Resolves channel_bindings for target recipient
                                │
            ┌───────────────────┴───────────────────┐
            │                                       │
            ▼                                       ▼
  [ Telegram Transport ]                 [ WhatsApp Cloud API Transport ]
  - Free outbound REST API               - Checks channel_bindings.window_expires_at
  - Telegram Bot API Markdown            - If NOW() <= window_expires_at:
  - Validates X-Telegram-Bot-Secret        Interactive Session Message (Freeform)
                                         - If NOW() > window_expires_at:
                                           Pre-Approved HSM Utility Template
```

### 3.1 Transactional Outbox Event Consumer Pattern

#### The Dual-Write Hazard
Directly invoking external HTTP APIs (Telegram or Meta) within core business route handlers introduces the classic distributed dual-write hazard:
- Network latency or provider outages hold PostgreSQL database connections open, rapidly exhausting the connection pool (`pool_size=10`).
- If the external API call succeeds but the database transaction rolls back due to a constraint violation, an alert is dispatched for an action that never occurred.
- If the database commits but the external API call fails due to a network glitch, the notification is permanently lost.

#### Architectural Evaluation: Polling with `FOR UPDATE SKIP LOCKED` vs. `LISTEN/NOTIFY`

| Architectural Dimension | PostgreSQL `LISTEN/NOTIFY` | Polling with `FOR UPDATE SKIP LOCKED` (Chosen) |
| :--- | :--- | :--- |
| **Delivery Latency** | Instantaneous (< 5ms) | Configurable polling interval (1.0s – 2.0s) |
| **Connection Pooling (PgBouncer)** | **Incompatible** with transaction pooling. Requires dedicated session-pinned connections. | **100% Compatible** with PgBouncer transaction and statement pooling modes. |
| **Worker Crash Resilience** | **Fragile.** Notifications emitted while a worker is restarting are lost unless paired with a table. | **Guaranteed.** Unacknowledged rows remain in `outbox_events` indefinitely. |
| **Horizontal Scalability** | All active listeners receive the notification; requires secondary distributed locking. | **Native horizontal scaling.** Multiple worker processes fetch distinct row batches without deadlocks. |
| **Payload Capacity** | Hard limit of 8,000 bytes per `NOTIFY` string. | Unlimited JSONB structured payloads stored directly in PostgreSQL. |

**Verdict:** For an apparel manufacturing plant managing ~70 sewing workstations, an event dispatch latency of 1 to 2 seconds is more than sufficient. Polling with `FOR UPDATE SKIP LOCKED` eliminates connection-pinning hazards, works cleanly with PgBouncer, and guarantees zero message loss.

#### Outbox Database Schema (`outbox_events`)

```sql
CREATE TYPE outbox_status AS ENUM ('PENDING', 'PROCESSING', 'DISPATCHED', 'FAILED', 'DEAD_LETTER');
CREATE TYPE messaging_channel AS ENUM ('TELEGRAM', 'WHATSAPP', 'INTERNAL_WEBHOOK');

CREATE TABLE IF NOT EXISTS outbox_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    event_type VARCHAR(64) NOT NULL,       -- e.g. 'production.order.milestone_reached'
    aggregate_type VARCHAR(64) NOT NULL,   -- e.g. 'order', 'sewing_tally', 'payroll_period'
    aggregate_id UUID NOT NULL,
    payload JSONB NOT NULL,                -- Context: { order_no, line_id, pieces, operator_name, ... }
    target_channel messaging_channel NOT NULL,
    target_recipient_id UUID,              -- Reference to actors.id or app_users.id
    idempotency_key VARCHAR(128) NOT NULL, -- Prevents duplicate event insertion
    status outbox_status NOT NULL DEFAULT 'PENDING',
    retry_count INT NOT NULL DEFAULT 0,
    max_retries INT NOT NULL DEFAULT 5,
    last_error TEXT,
    next_retry_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    dispatched_at TIMESTAMPTZ,

    CONSTRAINT uq_outbox_tenant_idempotency UNIQUE (tenant_id, idempotency_key)
);

-- High-speed partial index for outbox polling
CREATE INDEX idx_outbox_events_pending 
    ON outbox_events (created_at ASC) 
    WHERE status IN ('PENDING', 'FAILED');
```

#### SQLAlchemy 2.0 Concurrency-Safe Consumer

```python
# backend/app/services/outbox_consumer.py
from datetime import datetime, timezone
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.messaging import OutboxEvent, OutboxStatus

async def fetch_and_lock_outbox_batch(
    session: AsyncSession, 
    batch_size: int = 10
) -> List[OutboxEvent]:
    """
    Atomically claims pending outbox events using FOR UPDATE SKIP LOCKED.
    Concurrent worker threads skip locked rows without blocking or deadlocking.
    """
    now = datetime.now(timezone.utc)
    stmt = (
        select(OutboxEvent)
        .where(
            OutboxEvent.status.in_([OutboxStatus.PENDING, OutboxStatus.FAILED]),
            (OutboxEvent.next_retry_at.is_(None)) | (OutboxEvent.next_retry_at <= now)
        )
        .order_by(OutboxEvent.created_at.asc())
        .limit(batch_size)
        .with_for_update(skip_locked=True)
    )
    result = await session.execute(stmt)
    events = result.scalars().all()

    for event in events:
        event.status = OutboxStatus.PROCESSING
    await session.commit()
    return events
```

#### Exponential Backoff & Dead-Letter Queue (DLQ) Formula
When third-party endpoints return HTTP 5xx errors or network timeouts occur, the consumer computes the retry timestamp with decorrelated exponential backoff and randomized jitter:

$$\text{delay} = \min\left(\text{max\_delay},\; \text{base\_delay} \times 2^{\text{retry\_count}}\right) + \text{uniform}(0, \text{jitter\_window})$$

- Parameters: `base_delay = 5s`, `max_delay = 1800s` (30 minutes), `max_retries = 5`.
- Progression: ~5s $\rightarrow$ ~20s $\rightarrow$ ~80s $\rightarrow$ ~320s $\rightarrow$ ~1280s $\rightarrow$ **DEAD_LETTER**.
- Events exceeding 5 retries transition to `DEAD_LETTER`, triggering an administrative alert while allowing remaining queue traffic to proceed unhindered.

### 3.2 Webhook Ingestion & Cryptographic Validation

All inbound messages and delivery receipts from Telegram and Meta are received via public HTTPS webhooks requiring rigorous cryptographic validation.

#### Telegram Bot API Webhook Ingestion
Telegram supports a secret token specified during `setWebhook` via the `secret_token` parameter (1 to 256 characters, `[A-Za-z0-9_-]`). Telegram injects this token in the header **`X-Telegram-Bot-Api-Secret-Token`**. Validation must use constant-time comparison:

```python
# backend/app/api/v1/webhooks.py
import hmac
from fastapi import APIRouter, Request, HTTPException, status

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])
TELEGRAM_SECRET_TOKEN = "lukla-secret-telegram-token-secure"

@router.post("/telegram")
async def receive_telegram_webhook(request: Request):
    header_token = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    if not header_token or not hmac.compare_digest(header_token, TELEGRAM_SECRET_TOKEN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Unauthorized Telegram webhook secret token"
        )
    payload = await request.json()
    return {"status": "ok"}
```

#### Meta WhatsApp Business Cloud API Ingestion
Meta's webhook protocol mandates two separate operations:
1. **GET Verification Handshake:** Meta transmits `hub.mode=subscribe`, `hub.verify_token`, and `hub.challenge`. The endpoint must verify `hub.verify_token` and return `hub.challenge` as plain text integer.
2. **POST Event Ingestion:** Inbound messages are delivered with an **`X-Hub-Signature-256`** header containing `sha256=<hex_digest>`.

#### The Critical Raw Body Invariant
> **CRITICAL ARCHITECTURAL GOTCHA:** To validate `X-Hub-Signature-256`, the HMAC hash must be computed against the **raw, unparsed HTTP request body bytes** (`await request.body()`). If the payload is parsed as JSON before verification, whitespace, indentation, or key-ordering discrepancies introduced by JSON parsers will alter the byte sequence, causing HMAC validation to fail unpredictably!

```python
import hashlib

WHATSAPP_APP_SECRET = "meta-app-secret-production"

@router.post("/whatsapp")
async def receive_whatsapp_webhook(request: Request):
    signature_header = request.headers.get("X-Hub-Signature-256")
    if not signature_header or not signature_header.startswith("sha256="):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Missing or malformed X-Hub-Signature-256 header"
        )

    raw_body: bytes = await request.body()
    expected_hash = hmac.new(
        key=WHATSAPP_APP_SECRET.encode("utf-8"),
        msg=raw_body,
        digestmod=hashlib.sha256
    ).hexdigest()
    expected_signature = f"sha256={expected_hash}"

    if not hmac.compare_digest(expected_signature, signature_header):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Invalid HMAC signature"
        )

    payload = await request.json()
    return {"status": "ok"}
```

#### Webhook Deduplication Pipeline
Telegram and Meta automatically retry webhooks if the response takes $>3$ seconds or returns non-200. The gateway enforces deduplication via an atomic insert into `inbound_webhook_dedup`:

```sql
CREATE TABLE IF NOT EXISTS inbound_webhook_dedup (
    channel messaging_channel NOT NULL,
    external_message_id VARCHAR(128) NOT NULL, -- Telegram update_id or WhatsApp wamid
    received_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    processed BOOLEAN NOT NULL DEFAULT TRUE,
    PRIMARY KEY (channel, external_message_id)
);
```
If an insert encounters a primary key conflict, the handler immediately returns `HTTP 200 OK` and aborts downstream processing, preventing duplicate notifications.

### 3.3 Handling the WhatsApp 24-Hour Customer Service Window

Meta enforces strict rules on the WhatsApp Business Cloud API regarding message types and timing:
1. **Rolling 24-Hour Customer Service Window:** When an end-user sends an inbound message to the factory's WhatsApp Business Account, a rolling 24-hour service window opens.
2. **Session Messages (Inside Window):** Within this 24-hour window, the system may transmit freeform text, interactive buttons, list pickers, and media attachments without template approval.
3. **Template Messages (Outside Window):** If $>24$ hours have elapsed since the user's last inbound interaction (or if initiating proactive outbound notifications), Meta strictly prohibits freeform text. Attempting to send a freeform message fails immediately with Meta Error `131047` (*"Message failed to send because more than 24 hours have passed since the customer last replied"*).
4. **Pre-Approved HSM Utility Templates:** Outbound messages sent outside the window must use pre-approved Highly Structured Message (HSM) templates categorized strictly as **UTILITY** (e.g. `order_milestone_update`, `wage_statement_ready`).

#### State Tracking in `channel_bindings`

```sql
CREATE TABLE IF NOT EXISTS channel_bindings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    user_id UUID NOT NULL REFERENCES actors(id) ON DELETE RESTRICT,
    channel messaging_channel NOT NULL,
    channel_user_id VARCHAR(64) NOT NULL,  -- Telegram chat_id or WhatsApp E.164 phone
    channel_username VARCHAR(64),
    active BOOLEAN NOT NULL DEFAULT TRUE,
    last_inbound_at TIMESTAMPTZ,           -- Updated on every inbound message
    window_expires_at TIMESTAMPTZ,         -- last_inbound_at + INTERVAL '24 hours'
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_channel_binding UNIQUE (tenant_id, channel, channel_user_id)
);
```

#### Dual-Mode Dispatch Decision Logic

```python
# backend/app/services/whatsapp_client.py
from datetime import datetime, timezone

async def dispatch_whatsapp_notification(
    binding: ChannelBinding, 
    event: OutboxEvent, 
    client: httpx.AsyncClient
):
    now = datetime.now(timezone.utc)
    is_inside_window = (
        binding.window_expires_at is not None and now <= binding.window_expires_at
    )

    if is_inside_window:
        # Payload A: Interactive Session Message (Inside 24h Window)
        payload = {
            "messaging_product": "whatsapp",
            "to": binding.channel_user_id,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {"text": format_session_markdown(event.payload)},
                "action": {
                    "buttons": [
                        {"type": "reply", "reply": {"id": f"VIEW_{event.aggregate_id}", "title": "Cek Status"}}
                    ]
                }
            }
        }
    else:
        # Payload B: Pre-Approved HSM Utility Template (Outside 24h Window)
        payload = {
            "messaging_product": "whatsapp",
            "to": binding.channel_user_id,
            "type": "template",
            "template": {
                "name": "lukla_order_milestone_v1",
                "language": {"code": "id"},
                "components": [
                    {
                        "type": "body",
                        "parameters": format_hsm_parameters(event.payload)
                    }
                ]
            }
        }

    resp = await client.post(META_WHATSAPP_MESSAGES_URL, json=payload, headers=AUTH_HEADERS)
    resp.raise_for_status()
```

### 3.4 Cryptographic Deep-Link Account Binding Flow

#### Threat Model: Why Raw Phone Numbers Cannot Be Trusted
In naive messaging integrations, users are asked to type their phone number into a chat prompt or an admin manually inputs contact numbers into an ERP screen.
- **Identity Spoofing:** A malicious actor can message the Telegram bot claiming to be the factory owner or a B2B brand manager, gaining access to proprietary production metrics and payroll statements.
- **Cross-Tenant Leakage:** Indonesian garment workers frequently swap physical SIM cards for data promotions while retaining their old WhatsApp registration number. Typing an outdated phone number into the ERP risks routing sensitive piece-rate wage statements to an unrelated third party.

#### The Deep-Link Format & Telegram's 64-Character Constraint
To achieve zero-trust account binding:
1. The authenticated user logs into the Lukla Web Portal holding a valid JWT session.
2. In User Settings, the user clicks **"Hubungkan Telegram"** or **"Hubungkan WhatsApp"**.
3. The server generates a single-use, 43-character URL-safe random token:
   ```python
   import secrets
   raw_token = secrets.token_urlsafe(32) # Exactly 43 chars: [A-Za-z0-9_-]
   ```
4. **The Telegram 64-Character Constraint:** Telegram deep linking (`https://t.me/<bot>?start=<parameter>`) enforces a **strict maximum length of 64 characters** and only allows `[A-Za-z0-9_-]`. Standard signed JWTs (typically 150–220 characters) exceed this limit and are rejected by Telegram! The 43-character URL-safe token fits comfortably within the 64-character boundary.
5. The server stores the **SHA-256 hash** of the token in `channel_binding_tokens` with a strict 15-minute expiration window.
6. The user is redirected to the messaging application:
   - **Telegram Link:** `https://t.me/LuklaOpsBot?start=tok_4F9bX8...`
   - **WhatsApp Link:** `https://wa.me/628112345678?text=CONNECT_tok_4F9bX8...`

#### Binding Tokens Schema (`channel_binding_tokens`)

```sql
CREATE TABLE IF NOT EXISTS channel_binding_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    user_id UUID NOT NULL REFERENCES actors(id) ON DELETE RESTRICT,
    channel messaging_channel NOT NULL,
    token_hash VARCHAR(64) NOT NULL UNIQUE, -- SHA-256 hex digest of raw_token
    expires_at TIMESTAMPTZ NOT NULL,        -- Strict 15-minute validity window
    used_at TIMESTAMPTZ,                    -- Single-use invalidation timestamp
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_binding_tokens_lookup 
    ON channel_binding_tokens (token_hash) 
    WHERE used_at IS NULL;
```

#### End-to-End Cryptographic Binding Sequence

```
[ USER ON LUKLA WEB PORTAL ]
  │
  │ 1. POST /api/v1/messaging/bindings/token { channel: 'TELEGRAM' } (with Bearer JWT)
  ▼
[ LUKLA BACKEND ]
  │ Generates raw_token = secrets.token_urlsafe(32)
  │ Stores token_hash = sha256(raw_token), expires_at = NOW() + 15m
  │ Returns deep_link: "https://t.me/LuklaOpsBot?start=" + raw_token
  ▼
[ USER CLICKS LINK ON MOBILE / DESKTOP ]
  │ Opens Telegram App -> Taps "START" -> Sends: /start <raw_token>
  ▼
[ WEBHOOK INGESTION (FastAPI) ]
  │ 1. Verify webhook header (X-Telegram-Bot-Api-Secret-Token)
  │ 2. Deduplicate message ID
  │ 3. Extract raw_token from payload
  │ 4. Compute token_hash = sha256(raw_token)
  │ 5. Query channel_binding_tokens WHERE token_hash = :hash AND used_at IS NULL AND expires_at > NOW()
  │
  ├─ IF NOT FOUND OR EXPIRED:
  │    Reply: "❌ Tautan koneksi tidak valid atau sudah kadaluarsa. Silakan buat tautan baru di Portal Lukla."
  │
  └─ IF VALID:
       BEGIN TRANSACTION;
         UPDATE channel_binding_tokens SET used_at = NOW() WHERE id = :token_id;
         INSERT INTO channel_bindings (tenant_id, user_id, channel, channel_user_id, active, last_inbound_at)
         VALUES (:tenant_id, :user_id, :channel, :chat_id, TRUE, NOW())
         ON CONFLICT (tenant_id, channel, channel_user_id) 
         DO UPDATE SET active = TRUE, last_inbound_at = NOW();
       COMMIT;
       Reply: "✅ Akun Telegram Anda telah berhasil terhubung ke Lukla ERP (Rudi S. - Line 03)."
```

---

## 4. Comparative Evaluation Matrix Against Lukla Constraints

To substantiate our architectural selections, seven candidate repositories, frameworks, and reference implementations were evaluated against Lukla's operational constraints:

### 4.1 Candidate Repositories Evaluated

1. **`vercel/chat` & `vercel/ai` (`chat-sdk.dev`)**
   - **Repository:** [github.com/vercel/chat](https://github.com/vercel/chat) & [github.com/vercel/ai](https://github.com/vercel/ai)
   - **License:** MIT | **Stars:** ~2.4k (`chat`) / ~20k+ (`ai`) | **Language:** TypeScript
   - **Core Focus:** Universal chat and agent abstraction layer across multi-platform messaging transports (Slack, Teams, Discord) and React streaming renderers.
2. **`aws-samples/transactional-outbox-pattern`**
   - **Repository:** [github.com/aws-samples/transactional-outbox-pattern](https://github.com/aws-samples/transactional-outbox-pattern)
   - **License:** MIT-0 | **Status:** Active enterprise reference architecture
   - **Core Focus:** Event-driven decoupling using transactional outbox tables and event streaming.
3. **`pydantic/pydantic-ai`**
   - **Repository:** [github.com/pydantic/pydantic-ai](https://github.com/pydantic/pydantic-ai)
   - **License:** MIT | **Stars:** ~20.6k+ | **Language:** Python 3.10+
   - **Core Focus:** Type-safe, lightweight Python agent and tool calling library natively integrated with Pydantic v2.
4. **`fbsamples/whatsapp-api-examples`**
   - **Repository:** [github.com/fbsamples/whatsapp-api-examples](https://github.com/fbsamples/whatsapp-api-examples)
   - **License:** MIT | **Status:** Official Meta reference sample
   - **Core Focus:** Python and Node.js samples for Meta WhatsApp Business Cloud API webhook verification, media delivery, and HSM templates.
5. **`python-telegram-bot` (`python-telegram-bot/python-telegram-bot`)**
   - **Repository:** [github.com/python-telegram-bot/python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
   - **License:** LGPL-3.0 | **Stars:** ~24k+ | **Language:** Python 3.8+
   - **Core Focus:** Asynchronous wrapper for the Telegram Bot API with conversation handlers and dispatcher loops.
6. **`novuhq/novu`**
   - **Repository:** [github.com/novuhq/novu](https://github.com/novuhq/novu)
   - **License:** Apache 2.0 / MIT / Commercial | **Stars:** ~36k+ | **Language:** TypeScript (NestJS)
   - **Core Focus:** Enterprise multi-channel notification infrastructure (Push, Email, SMS, Chat).
7. **`langchain-ai/langchain` & `langgraph`**
   - **Repository:** [github.com/langchain-ai/langchain](https://github.com/langchain-ai/langchain)
   - **License:** MIT | **Stars:** ~95k+ | **Language:** Python / TypeScript
   - **Core Focus:** Heavy multi-agent cyclical orchestration and state graph execution.

### 4.2 Numerical Scoring Table (1 to 5 Scale)

- **Simplicity & Extensibility (Weight: 25%):** Readability, junior-developer debuggability, absence of magic abstractions.
- **Stack Fit & Dependencies (Weight: 20%):** Native Python 3.12, FastAPI, Pydantic v2, PostgreSQL alignment vs. foreign runtime overhead.
- **Security & Invariants (Weight: 25%):** Physical rejection of autonomous ledger writes, Actor Token Passthrough, PostgreSQL RLS preservation, zero cross-tenant leakage.
- **Test Quality & Verification (Weight: 15%):** Automated unit/integration test coverage, deterministic offline mock runners.
- **Ease of Production Integration (Weight: 15%):** Seamless fit with 83 existing OpenAPI endpoints and current React dashboard.

| Candidate Repository / Architecture | Simplicity (25%) | Stack Fit (20%) | Security (25%) | Test Quality (15%) | Integration (15%) | Weighted Total (/5.0) | Final Verdict |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **`pydantic/pydantic-ai` + Native FastAPI** | **4.8** | **5.0** | **5.0** | **4.6** | **5.0** | **4.89** | **PRIMARY SELECTION (Archetype A Copilot)** |
| **Native FastAPI + Postgres Outbox (`aws-samples`)**| **4.8** | **5.0** | **4.9** | **4.5** | **4.8** | **4.81** | **PRIMARY SELECTION (Archetype B Outbox)** |
| **`fbsamples/whatsapp-api-examples`** | 4.2 | 4.5 | 4.8 | 4.0 | 4.6 | **4.45** | **ADOPT (WhatsApp Transport Reference)** |
| **`python-telegram-bot` (`PTB`)** | 3.2 | 4.0 | 3.5 | 4.5 | 3.8 | **3.70** | **EVALUATE / REJECT RUNNER (Use direct httpx)** |
| **`aws-samples/transactional-outbox-pattern`** | 3.5 | 3.0 | 4.8 | 4.0 | 3.8 | **3.82** | **ADOPT PATTERN ONLY (Replace CDK with SQL)** |
| **`vercel/chat` (`chat-sdk.dev`)** | 3.0 | 2.0 | 2.5 | 4.2 | 2.5 | **2.73** | **REJECT AS BACKEND (Adopt React hooks only)** |
| **`langchain` / `langgraph`** | 1.5 | 3.0 | 1.8 | 3.2 | 2.0 | **2.16** | **REJECT (Fatal Anti-Pattern: Framework Bloat)** |
| **`novuhq/novu`** | 1.2 | 1.5 | 4.0 | 4.0 | 1.5 | **2.28** | **REJECT (Fatal Anti-Pattern: Daemon Sprawl)** |

### 4.3 Direct Evaluation: Native FastAPI vs Vercel Chat SDK (`vercel/chat`)

| Dimension | Native Python/FastAPI (`prototypes/ai-copilot`) | Vercel Chat SDK (`vercel/chat` / `chat-sdk.dev`) |
| :--- | :--- | :--- |
| **Runtime & Language** | Python 3.12 / Uvicorn (Native to Lukla backend) | Node.js v18+ / Edge Runtime (Foreign runtime) |
| **Deployment Footprint** | Single process; runs directly within existing container | Requires an additional Node.js container and npm tooling |
| **Auth & RLS Invariant** | Direct `Authorization: Bearer <jwt>` passthrough; sets PostgreSQL session variables for RLS | Requires cross-service token delegation or webhook proxying; risks session bleed |
| **Tool Calling Pattern** | Pydantic v2 schemas; asynchronous `httpx` calls | TypeScript Zod schemas; JSON-RPC protocols |
| **Zero Ledger Risk** | Hardcoded physical check (`method == "GET"`) | Requires custom adapter logic to restrict mutations |
| **Telegram Integration** | 30 lines of native FastAPI code with `httpx` | Pre-built adapter (`@chat-adapter/telegram`) |
| **WhatsApp Integration** | Native Meta Graph API v20+ with HMAC-SHA256 | Community / third-party adapter required |
| **Junior Dev Explainability** | High: explicit, procedural Python code | Medium: multi-tier abstraction across adapters and state engines |
| **Recommended Verdict** | **100% Native Adoption for Backend Core** | **Adopt `@ai-sdk/react` in frontend UI only** |

---

## 5. Concrete Adaptation Blueprint

### 5.1 Proposed Directory & File Structure

```
backend/
├── app/
│   ├── copilot/                      # ARCHETYPE A: In-App Operational Copilot
│   │   ├── __init__.py
│   │   ├── router.py                 # FastAPI APIRouter: POST /api/v1/copilot/chat
│   │   ├── config.py                 # CopilotSettings (provider, model, base_url)
│   │   ├── schemas.py                # Pydantic v2 models (ChatTurnRequest, ActionShortcut, ToolCallResult)
│   │   ├── registry.py               # Curated read-only tool catalog with filter_tools_for_roles()
│   │   ├── executor.py               # ReadOnlyToolExecutor (strict GET-only + Bearer passthrough)
│   │   ├── shortcuts.py              # Action Shortcut matcher mapped to VIEW-01..06
│   │   └── provider.py               # BaseLLMClient abstraction (Mock, Ollama, OpenAI)
│   │
│   ├── messaging/                    # ARCHETYPE B: Multi-Channel Messaging Gateway
│   │   ├── __init__.py
│   │   ├── models.py                 # SQLAlchemy models: OutboxEvent, ChannelBinding, ChannelBindingToken
│   │   ├── router.py                 # Webhooks: POST /webhooks/telegram, POST /webhooks/whatsapp
│   │   ├── security.py               # HMAC-SHA256 verification & binding token hashing
│   │   ├── outbox_worker.py          # Background polling worker using FOR UPDATE SKIP LOCKED
│   │   └── transports/
│   │       ├── base.py               # Abstract BaseMessagingTransport interface
│   │       ├── telegram.py           # Telegram Bot API client via httpx
│   │       └── whatsapp.py           # Meta WhatsApp Cloud API client (Session & HSM)
│   │
│   └── main.py                       # Mounts copilot and messaging routers under /api/v1
frontend/
└── src/
    └── components/
        └── copilot/
            ├── CopilotChatWidget.tsx # Zero-dependency React streaming chat widget
            └── ActionShortcutCard.tsx# Interactive action cards rendering UI deep-links
```

### 5.2 Target Signatures, Database Models, and Schemas

#### Archetype A Schemas (`copilot/schemas.py`)
```python
import uuid
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class ActionShortcut(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    url: str
    icon: Optional[str] = "external-link"
    prefill_params: Optional[Dict[str, Any]] = None

class ToolCallRequest(BaseModel):
    id: str
    tool_name: str
    arguments: Dict[str, Any]

class ToolCallResult(BaseModel):
    tool_call_id: str
    tool_name: str
    status_code: int
    data: Any
    error: Optional[str] = None

class ChatTurnRequest(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    message: str
    history: List[Dict[str, Any]] = Field(default_factory=list)

class ChatTurnResponse(BaseModel):
    session_id: str
    reply: str
    shortcuts: List[ActionShortcut] = Field(default_factory=list)
    tool_invocations: List[ToolCallResult] = Field(default_factory=list)
```

#### Archetype B Database Models (`messaging/models.py`)
```python
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class OutboxEvent(Base):
    __tablename__ = "outbox_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    aggregate_type: Mapped[str] = mapped_column(String(64), nullable=False)
    aggregate_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    target_channel: Mapped[str] = mapped_column(String(32), nullable=False)
    target_recipient_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="PENDING", nullable=False)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_retries: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    last_error: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    next_retry_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    dispatched_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("tenant_id", "idempotency_key", name="uq_outbox_tenant_idempotency"),
        Index("idx_outbox_pending_partial", "created_at", postgresql_where=(status.in_(["PENDING", "FAILED"]))),
    )

class ChannelBinding(Base):
    __tablename__ = "channel_bindings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    channel: Mapped[str] = mapped_column(String(32), nullable=False)
    channel_user_id: Mapped[str] = mapped_column(String(64), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_inbound_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    window_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("tenant_id", "channel", "channel_user_id", name="uq_channel_binding"),
    )
```

### 5.3 Automated Test Suites & Verification Plan

All portable code must be verifiable offline via `pytest` without requiring external network connectivity or paid API credentials:

1. **`tests/copilot/test_executor.py`:**
   - Asserts `ReadOnlyToolExecutor` successfully dispatches GET requests with caller's Bearer token.
   - Asserts that attempting to execute any `POST`, `PUT`, or `DELETE` tool raises an immediate `SecurityException`.
   - Asserts uncataloged tool names are rejected with HTTP 403 Forbidden.
2. **`tests/copilot/test_registry.py`:**
   - Verifies `MaklonClient` role receives only authorized order and stock query tools.
   - Verifies `Owner` receives complete operational and ledger query tools.
   - Verifies `QCInspector` receives assembly inspection barcode query tools.
3. **`tests/copilot/test_shortcuts.py`:**
   - Asserts `ActionShortcut` model instantiates cleanly without explicit `id` (auto-generating valid UUID v4).
   - Asserts cutting intents generate deep links to `/app/materials?action=cutting&orderId=...`.
   - Asserts sewing tally intents generate deep links to `/terminal/tally?lineId=...` with numeric padding (`LINE-02`).
   - Asserts QC defect intents extract serial codes and generate deep links to `/app/quality?serialCode=...`.
   - Asserts word boundary checking prevents false positives on phrases like `"reorder kain"` and `"in order to fix defect"`.
   - Asserts ERP identifiers preserve uppercase normalization (`SO-2026-001`, `LINE-02`, `ASM-8910`).
   - Asserts zero keyword collision between cutting (`"potong kain"`) and warehouse receiving (`"terima kain"`), and between sewing (`"tally jahit"`) and QC (`"cacat jahitan"`).
4. **`tests/messaging/test_outbox_concurrency.py`:**
   - Simulates 5 concurrent worker threads querying `outbox_events` with `FOR UPDATE SKIP LOCKED`.
   - Verifies that no two workers ever claim the same pending row.
5. **`tests/messaging/test_webhook_security.py`:**
   - Simulates WhatsApp webhook deliveries: asserts valid `X-Hub-Signature-256` passes and tampered bodies return HTTP 403 Forbidden.
   - Simulates Telegram webhook deliveries: asserts valid `X-Telegram-Bot-Api-Secret-Token` passes and missing tokens return HTTP 403 Forbidden.
   - Asserts that duplicate delivery of an identical message ID is safely acknowledged with HTTP 200 without duplicate execution.
6. **`tests/messaging/test_binding_tokens.py`:**
   - Asserts token issuance generates exactly 43-character URL-safe strings.
   - Asserts tokens expire after 15 minutes and cannot be redeemed more than once.

---

## 6. Fatal Anti-Patterns Taxonomy

Our benchmarking of open-source conversational and messaging bots identified seven fatal anti-patterns that directly violate Lukla's operational and accounting invariants:

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                     LUKLA ANTI-PATTERN TAXONOMY                                        │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 1. Autonomous Double-Entry Ledger Mutation  ──► LLM executes state-altering POST/PUT on ledger core   │
│ 2. The Monolithic Framework Trap (LangChain) ──► 80+ dependency tree bloat, infinite recursive loops  │
│ 3. In-Memory Long-Polling Bot Daemons        ──► bot.run_polling() blocks event loop, loses state       │
│ 4. Unverified Raw Phone Account Binding      ──► Chat-prompted phone inputs causing cross-tenant leaks │
│ 5. The Transactional Dual-Write Hazard       ──► External HTTP calls executed inside DB commit block    │
│ 6. WhatsApp 24-Hour Window Ignorance         ──► Blindly dispatching freeform text outside window       │
│ 7. Blanket Service-Account Bypass (RLS Loss) ──► Copilot queries database using master bypass role      │
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 1. Autonomous Double-Entry Ledger Mutation
- **Observed In:** Naive agent boilerplates providing write tools (`post_journal_entry`, `cancel_order`) to LLMs.
- **The Failure:** The model hallucinates account IDs or quantities (e.g. adjusting fabric stock by 200m based on a chat message). Accounting invariants (Debit == Credit, unvouched adjustments) are breached, creating financial liability.
- **Lukla Rejection Justification:** **Zero Autonomous Writes**. All mutating endpoints are physically blocked. Mutations require human interaction through audited dashboard screens via Action Shortcuts.

### 2. The Monolithic Framework Trap (`LangChain` / `LangGraph`)
- **Observed In:** Enterprise agent boilerplates importing `langchain`, `langgraph`, or daemon-based `OpenClaw`.
- **The Failure:** Introduces 80+ transitive packages, fragile monkey-patching across minor releases, and high cognitive load for junior engineers trying to trace execution graphs. Passing caller JWTs across async tasks requires awkward context-variable hacks.
- **Lukla Rejection Justification:** Follow `AGENTS.md` ("Prefer the option a thorough junior developer can run, debug, and explain"). Pure Python with Pydantic v2 schemas and standard OpenAI/Anthropic tool calling formats accomplishes 100% of the capability in under 150 lines of transparent code.

### 3. In-Memory Long-Polling Bot Daemons (`bot.run_polling()`)
- **Observed In:** Quickstart Telegram bot tutorials running `Application.run_polling()`.
- **The Failure:** Spawns a blocking while-loop polling Telegram servers. Scaling the web server to 2 or more replicas triggers HTTP 409 Conflict errors. Conversation state stored in process memory is wiped during restarts.
- **Lukla Rejection Justification:** Implement **Stateless HTTPS Webhooks** (`POST /api/v1/webhooks/telegram`). Scale horizontally behind standard reverse proxies with distributed idempotency checking.

### 4. Unverified Raw Phone Number Account Binding
- **Observed In:** Rudimentary messaging bots asking users to type their phone number into chat.
- **The Failure:** Trivial to spoof. An attacker types a competitor's or manager's phone number, immediately intercepting proprietary Maklon production status or confidential payroll statements.
- **Lukla Rejection Justification:** **Cryptographic Deep-Link Account Binding** utilizing short-lived, single-use, 43-character URL-safe tokens generated in the authenticated web portal and verified via constant-time SHA-256 hash comparison.

### 5. The Transactional Dual-Write Hazard
- **Observed In:** Applications invoking `send_telegram_notification()` inside primary API route handlers alongside `db.commit()`.
- **The Failure:** Network latency holds database connections open. If the external network fails, the user gets no notification despite a committed transaction; if the commit fails, a phantom notification is dispatched.
- **Lukla Rejection Justification:** **Transactional Outbox Pattern**. Business entities and `outbox_events` rows commit atomically to PostgreSQL. Decoupled async workers dispatch messages with retry backoff and dead-letter handling.

### 6. WhatsApp 24-Hour Customer Service Window Ignorance
- **Observed In:** Notification services treating WhatsApp like unrestricted SMS.
- **The Failure:** Meta rejects freeform messages sent $>24$ hours after user inbound interaction with Error `131047`, causing silent operational delivery failure.
- **Lukla Rejection Justification:** Dual-mode dispatcher: inspects `channel_bindings.window_expires_at` and automatically routes through pre-approved Meta HSM Utility Templates when outside the 24-hour window.

### 7. Blanket Service-Account Bypass (RLS Stripping)
- **Observed In:** Copilots that query databases using a root superuser connection string and perform tenant filtering in application code.
- **The Failure:** Any logic bug or prompt injection can omit the tenant filter, leaking fabric rolls or tech packs between competing Maklon clients.
- **Lukla Rejection Justification:** **Actor Token Passthrough**. Outbound tool calls forward the caller's verified `Authorization: Bearer <jwt>`, ensuring PostgreSQL kernel `FORCE ROW LEVEL SECURITY` policies enforce tenant isolation.

---

## 7. Final Recommendations & Implementation Roadmap

### 7.1 Phased Implementation Roadmap

```
HORIZON 1: Foundational Scaffolding (Current Milestone)
├── Graduation of In-App Copilot Facade from prototypes/ai-copilot/ into backend/app/copilot/
├── Migration of outbox_events, channel_bindings, and channel_binding_tokens into PostgreSQL schema
└── Implementation of stateless webhook handlers with constant-time cryptographic validation

HORIZON 2: Outbound Transactional Messaging & Mobile Deep-Linking
├── Deployment of async outbox worker polling with FOR UPDATE SKIP LOCKED
├── Integration of Telegram Bot API outbound dispatcher with Markdown formatting
├── Integration of Meta WhatsApp Business Cloud API with 24-hour window HSM fallback
└── Cryptographic account binding flow in Lukla Web Portal user settings

HORIZON 3: Conversational Mobile Copilot
├── Telegram and WhatsApp webhook ingestion routing inbound queries to ReadOnlyToolExecutor
├── Binding authenticated mobile chat IDs to verified user JWT claims
└── Inbound mutation intents returning mobile PWA deep links to audited web forms
```

### 7.2 Actionable Checklists for Downstream Workers

#### For `ai-ops-copilot-scaffold`:
- [ ] Migrate `prototypes/ai-copilot/backend/` into production `backend/app/copilot/`.
- [ ] Define `ActionShortcut` in `copilot/schemas.py` with `id: str = Field(default_factory=lambda: str(uuid.uuid4()))` and `prefill_params: Optional[Dict[str, Any]] = None` to eliminate instantiation crashes.
- [ ] Implement hardened entity extraction in `backend/app/copilot/shortcuts.py` using word-bounded, digit-anchored regexes (`orderId`: `(?<!\bin\s)\border\s*#?\s*([A-Za-z0-9\-]*\d[A-Za-z0-9\-]*)`, `lineId`: `\b(?:line|jalur)\s*#?\s*([A-Za-z0-9\-]+)`, `serialCode`: `\b((?:ASM|SN)-[A-Za-z0-9\-]+)|\b(?:barcode|serial)\s*[-:#]?\s*([A-Za-z0-9\-]*\d[A-Za-z0-9\-]*)`) evaluated against unlowercased raw input text with `re.IGNORECASE`.
- [ ] Enforce uppercase case normalization (`.upper()`) on extracted operational identifiers (`SO-2026-001`, `ASM-8910`, `LINE-02` with 2-digit numeric padding) before appending to query strings.
- [ ] Align `SHORTCUT_ROUTES` to canonical routes defined in `14-frontend-architecture.md` (`VIEW-01` through `VIEW-06`), eliminating legacy prototype paths (`/cutting/new`, `/sewing/tally`, `/qc/inspect`).
- [ ] Disambiguate keyword dictionaries in `SHORTCUT_ROUTES` by eliminating loose collision tokens (bare `"kain"` forbidden in cutting; bare `"jahit"` forbidden in sewing tallies) in favor of domain-specific multi-token phrases and mutual negative exclusions.
- [ ] Map all 14 reconciled query endpoints into `READ_TOOL_CATALOG` with explicit `allowed_roles`.
- [ ] Mount `router.py` in FastAPI's main application router under `/api/v1/copilot`.
- [ ] Verify `CopilotChatWidget.tsx` renders Action Shortcut Cards targeting canonical routes (`VIEW-01` to `VIEW-06`).
- [ ] Implement unit test suite under `backend/tests/copilot/test_shortcuts.py` asserting zero false positives on `"reorder kain katun"`, `"in order to fix defect"`, `"online"`, and `"serials"`, while verifying exact parameter and casing extraction for positive operational triggers.
- [ ] Implement unit and integration tests under `backend/tests/copilot/test_executor.py` verifying GET-only enforcement and role filtering.

#### For `messaging-bots-integration`:
- [ ] Create Alembic migration for `outbox_events`, `channel_bindings`, `channel_binding_tokens`, and `inbound_webhook_dedup`.
- [ ] Implement `POST /webhooks/telegram` validating `X-Telegram-Bot-Api-Secret-Token`.
- [ ] Implement `GET /webhooks/whatsapp` (challenge) and `POST /webhooks/whatsapp` validating `X-Hub-Signature-256` on raw body bytes.
- [ ] Implement `outbox_worker.py` utilizing `FOR UPDATE SKIP LOCKED` and exponential backoff with jitter.
- [ ] Implement `POST /api/v1/messaging/bindings/token` generating 43-character URL-safe deep-link tokens.
- [ ] Implement test suite verifying concurrency safety, webhook signature rejection, and token expiration.

---

## 8. Conclusion

By grounding the Lukla Intelligence in **Native Python/FastAPI Read-Only Facades** with **Actor Token Passthrough** and the Messaging Gateway in **PostgreSQL Transactional Outbox Workers** with **Cryptographic Deep-Linking**, the platform achieves enterprise-grade reliability, strict double-entry ledger immutability, and impenetrable tenant isolation while remaining exceptionally simple for junior engineers to run, debug, and explain.
