# Technical Design: Operational AI Copilot Architecture

> [!IMPORTANT]
> **SPECIFICATION HARDENING & BOUNDARY SYNCHRONIZATION:**
> This design document specifies the architectural foundation, 8-role authorization matrix, canonical Action Shortcut catalog, and factory network token budgeting for `ai-ops-copilot-scaffold`.
> Grounded in `reference-grounding-report.md`, `04-rbac-matrix.md`, `14-frontend-architecture.md`, and the 83 verified OpenAPI operations in `contracts/openapi.yaml`.

---

## 1. Context

The Lukla Operations Engine operates a hybrid apparel manufacturing facility in Ciwidey, West Java, supporting up to 70 sewing stations and multi-tenant B2B Maklon production. The core engine is built on an immutable double-entry accounting ledger (`NFR-02`) and strict custodial anti-cross-contamination rules.

A conversational Copilot enables users (Executive, Mandor/Production Head, Warehouse, QC, Finance, and Maklon Clients) to query order status, floor throughput, and inventory balances naturally. However, giving an LLM autonomous mutation capabilities directly against the 83 backend endpoints violates core invariants, introduces financial hallucination risks, and could breach tenant data boundaries.

---

## 2. Goals / Non-Goals

### Goals
- Provide an authenticated conversational interface capable of answering operational inquiries in natural language (Bahasa Indonesia with apparel domain terms).
- Execute read queries strictly through approved, curated `/api/v1` endpoints forwarding the user's verified Bearer JWT (`AuthContext`).
- Dynamically filter tool schemas at runtime based on caller RBAC roles across all 8 system roles.
- Surface interactive **Action Shortcuts** (deep links) directing users to audited UI forms across `VIEW-01` through `VIEW-06` for mutations.
- Enforce strict token budgeting ($\le 3,600$ tokens) and execution timeouts (15.0s local Ollama / 10.0s cloud / 5.0s internal query) to ensure high responsiveness on constrained factory networks.
- Keep the Copilot decoupled from the transactional messaging outbox (`messaging-bots-integration`).

### Non-Goals
- Autonomous state-mutating execution (no direct `POST`, `PUT`, or `DELETE` calls by the LLM).
- Merging outbox push notifications into the LLM chat pipeline.
- Granting ambient superuser credentials or bypassing PostgreSQL Row-Level Security.

---

## 3. Decisions & Architecture

### Decision 1: Read-Only Tool Execution with JWT Passthrough
- **Choice:** `ReadOnlyToolExecutor` explicitly enforces `method == "GET"` and forwards incoming `Authorization: Bearer <token>` and `X-Request-Id` headers. Any mutating method (`POST`, `PUT`, `PATCH`, `DELETE`) is physically rejected before network dispatch with RFC 7807 HTTP 403 `FORBIDDEN` and an immutable audit log.
- **Why:** Inherits existing application security, tenant scoping, and PostgreSQL RLS without building a custom security layer.
- **Alternatives Considered:**
  - *Ambient Master Key:* Rejected; allows prompt injection to expose cross-tenant client inventory.
  - *Autonomous Mutation:* Rejected; hallucinations violate double-entry ledger invariants.

### Decision 2: Action Shortcuts Protocol (Deep-Links) across VIEW-01..VIEW-06
- **Choice:** When user states intent to perform an action (cutting, tallying, QC defect logging, receiving, journal posting, payroll), the assistant bypasses tool mutation and returns structured, pre-filled `ActionShortcut` cards linking to canonical views.
- **Why:** Preserves human-in-the-loop integrity, CSRF tokens, client-side validation, and mandatory `Idempotency-Key` generation.
- **Alternatives Considered:**
  - *Chat-based Write Proposals:* Overengineers conversational confirmations when a verified web form already exists.

### Decision 3: Dynamic Multi-Role Tool Filtering (8 Roles x 83 Operations)
- **Choice:** Filter the tool catalog per request using `filter_tools_for_roles(roles)` matching `04-rbac-matrix.md`.
- **Why:** Passing all 83 OpenAPI endpoints consumes 15,000+ tokens per turn, degrades model accuracy, and leaks cross-tenant administrative endpoints. Dynamic filtering prunes the prompt to 3–8 authorized tools (~350–500 tokens).
- **Alternatives Considered:**
  - *Static tool catalog:* Rejected; exposes forbidden administrative tools to external Maklon clients.

### Decision 4: Decoupling from Messaging Outbox Gateway
- **Choice:** Maintain `ai-ops-copilot-scaffold` and `messaging-bots-integration` as separate, modular layers.
- **Why:** Outbox notifications require 100% deterministic Jinja2 templates (zero LLM in delivery path) to avoid wage hallucinations. Inbound mobile queries can evolve in Phase 2 via deterministic slash commands (`/status`, `/gaji`).

### Decision 5: Stateless Context Pruning & Shop-Floor Token Budgeting
- **Choice:** Enforce a strict $\le 3,600$ token budget per turn with sliding window FIFO history eviction (maximum 10 messages) and collection result compaction (slicing lists to top 3 items).
- **Why:** Factory cellular uplinks in Ciwidey (1.0–2.0 Mbps) experience serialization delays and latency spikes on large payloads. Strict budgeting guarantees sub-3.0s response times on local Ollama (`qwen2.5:7b-instruct-q4_K_M`) and protects ASGI worker threads.

---

## 4. Canonical Action Shortcut Routing Catalog

Deterministic regex matchers with negative lookbehinds extract parameters and route operational intents across `VIEW-01` through `VIEW-06`:

| Shortcut ID | Canonical Target View | Canonical Route Template | Permitted Query Params | Disambiguated Trigger Keywords | Negative Exclusion Rules | Icon |
|---|---|---|---|---|---|---|
| `cutting-record` | `VIEW-03` Warehouse & Cutting | `/app/materials?action=cutting` | `orderId` | `["potong kain", "hasil potong", "cutting", "pemotongan kain", "catat potong", "buangan kain"]` | Exclude if receiving verbs present (`"terima"`, `"receive"`, `"masuk"`, `"kedatangan"`). Standalone `"kain"` is strictly forbidden. | `scissors` |
| `warehouse-receive` | `VIEW-03` Warehouse & Cutting | `/app/materials?action=receive` | `orderId` | `["terima kain", "penerimaan bahan", "kain masuk", "gudang bahan", "receive material", "kedatangan kain"]` | Exclude if cutting verbs present (`"potong"`, `"cutting"`, `"buangan"`). | `package` |
| `sewing-tally` | `VIEW-04` Sewing Floor Terminal | `/terminal/tally` | `lineId`, `orderId` | `["tally", "tally jahit", "input tally", "hasil jahit", "sewing tally", "output jahit", "jalur jahit"]` | Exclude if defect/QC terms present (`"cacat"`, `"defect"`, `"repair"`, `"reject"`, `"inspeksi"`, `"qc"`). Standalone `"jahit"` is strictly forbidden. | `clipboard-list` |
| `qc-inspection` | `VIEW-05` QC Station | `/app/quality` | `serialCode`, `orderId` | `["qc", "cacat", "defect", "inspeksi qc", "repair", "reject", "cacat jahitan"]` | Takes absolute precedence over sewing tally on defect reports even if containing `"jahit"`/`"jahitan"`. | `alert-triangle` |
| `ledger-entry` | `VIEW-06` Finance & Ledger | `/app/finance?tab=journals` | `orderId` | `["jurnal", "ledger", "transaksi baru", "jurnal penyesuaian", "posting jurnal"]` | Must pair with accounting nouns to prevent collision with generic operational logs. | `book-open` |
| `payroll-approval` | `VIEW-06` Finance & Ledger | `/app/finance?tab=payroll` | `periodId` | `["payroll", "gaji borongan", "upah sabtu", "rekap payroll", "penggajian"]` | Requires payroll-specific composite phrases. | `dollar-sign` |
| `order-action` | `VIEW-01` Operations Dashboard | `/app/overview` | `orderId` | `["konfirmasi order", "batal order", "order baru", "pesanan baru", "buat order"]` | Exclude if purely read inquiry (`"cek status"`, `"lacak order"`). | `file-text` |
| `sample-tracker` | `VIEW-02` Sample & Tech Pack | `/app/samples` | `sampleId` | `["buat sample", "revisi sample", "setujui sample", "input time study", "tech pack"]` | Exclude if purely read inquiry (`"lihat spek"`). | `layers` |

### Hardened Entity Extraction Patterns:
- **Order ID Extractor:** `(?<!\bin\s)\border\s*#?\s*([A-Za-z0-9\-]*\d[A-Za-z0-9\-]*)` (normalized to uppercase, ignores `"in order to"`).
- **Line ID Extractor:** `\b(?:line|jalur)\s*#?\s*([A-Za-z0-9\-]+)` (normalized to 2-digit format `LINE-XX`).
- **Serial Code Extractor:** `\b((?:ASM|SN)-[A-Za-z0-9\-]+)|\b(?:barcode|serial)\s*[-:#]?\s*([A-Za-z0-9\-]*\d[A-Za-z0-9\-]*)` (normalized to uppercase).
- **Period ID Extractor:** `\b(?:period|periode)\s*#?\s*([A-Za-z0-9\-]+)|\b(\d{4}-W\d{2})\b` (normalized to uppercase).

---

## 5. Comprehensive 83-Operation Whitelist & 8-Role Mapping Matrix

All 83 operations from `contracts/openapi.yaml` are cataloged below, classified into Read Tools (37 GET) and Action Shortcuts (46 Mutating), mapped to the 8 roles:
- **R1:** `Owner`
- **R2:** `SampleTeam`
- **R3:** `Warehouse`
- **R4:** `ProductionHead`
- **R5:** `Tailor`
- **R6:** `QCInspector`
- **R7:** `FinancePayroll`
- **R8:** `MaklonClient`

| # | Method | Path | Operation ID | Primary Tag | Copilot Execution Type | Accessible Roles |
|---|---|---|---|---|---|---|
| 1 | `POST` | `/auth/login` | `login` | `auth` | **ACTION_SHORTCUT** (Auth Flow) | R1–R8 |
| 2 | `POST` | `/auth/refresh` | `refreshSession` | `auth` | **ACTION_SHORTCUT** (Session Flow) | R1–R8 |
| 3 | `POST` | `/auth/logout` | `logout` | `auth` | **ACTION_SHORTCUT** (Session Flow) | R1–R8 |
| 4 | `GET` | `/me/context` | `getMyContext` | `auth` | **READ_TOOL** (Session Context) | R1–R8 |
| 5 | `GET` | `/clients` | `listClients` | `workflow` | **READ_TOOL** | R1, R4, R7 |
| 6 | `POST` | `/clients` | `createClient` | `clients-orders` | **ACTION_SHORTCUT** | R1 |
| 7 | `GET` | `/clients/{clientId}` | `getClient` | `clients-orders` | **READ_TOOL** | R1, R2, R7 |
| 8 | `POST` | `/orders` | `createOrder` | `clients-orders` | **ACTION_SHORTCUT** | R1 |
| 9 | `GET` | `/orders` | `listOrders` | `clients-orders` | **READ_TOOL** | R1, R3, R4, R7, R8 |
| 10 | `GET` | `/orders/{orderId}` | `getOrder` | `clients-orders` | **READ_TOOL** | R1, R3, R4, R7, R8 |
| 11 | `POST` | `/orders/{orderId}/confirmation` | `confirmOrder` | `clients-orders` | **ACTION_SHORTCUT** | R1, R4 |
| 12 | `POST` | `/orders/{orderId}/cancellation` | `cancelOrder` | `clients-orders` | **ACTION_SHORTCUT** | R1 |
| 13 | `POST` | `/ledger/transactions` | `appendLedgerTransaction` | `ledger-audit` | **ACTION_SHORTCUT** | R1, R7 |
| 14 | `POST` | `/ledger/transactions/{transactionId}/reversals` | `reverseLedgerTransaction` | `ledger-audit` | **ACTION_SHORTCUT** | R1, R7 |
| 15 | `GET` | `/ledger/entries` | `getLedgerEntries` | `ledger-audit` | **READ_TOOL** | R1, R7 |
| 16 | `GET` | `/ledger/accounts` | `listLedgerAccounts` | `ledger-audit` | **READ_TOOL** | R1, R7 |
| 17 | `GET` | `/ledger/transactions/{transactionId}` | `getLedgerTransaction` | `ledger-audit` | **READ_TOOL** | R1, R7 |
| 18 | `GET` | `/audit/events` | `listAuditEvents` | `ledger-audit` | **READ_TOOL** | R1, R7 |
| 19 | `POST` | `/samples` | `createSample` | `samples-rates` | **ACTION_SHORTCUT** | R1, R2 |
| 20 | `GET` | `/samples/{sampleId}` | `getSample` | `samples-rates` | **READ_TOOL** | R1, R2, R4 |
| 21 | `GET` | `/samples/{sampleId}/revisions` | `listSampleRevisions` | `samples-rates` | **READ_TOOL** | R1, R2, R4, R8 |
| 22 | `POST` | `/samples/{sampleId}/revisions` | `createSampleRevision` | `samples-rates` | **ACTION_SHORTCUT** | R2 |
| 23 | `POST` | `/samples/{sampleId}/lock` | `lockSample` | `samples-rates` | **ACTION_SHORTCUT** | R1, R2 |
| 24 | `POST` | `/time-studies` | `recordTimeStudy` | `samples-rates` | **ACTION_SHORTCUT** | R2, R4 |
| 25 | `GET` | `/time-studies` | `listTimeStudies` | `samples-rates` | **READ_TOOL** | R1, R2, R4 |
| 26 | `PUT` | `/rate-cards` | `upsertRateCard` | `samples-rates` | **ACTION_SHORTCUT** | R1, R4 |
| 27 | `POST` | `/material-receipts` | `receiveMaterial` | `warehouse-cutting` | **ACTION_SHORTCUT** | R1, R3 |
| 28 | `POST` | `/material-issuances` | `issueMaterial` | `warehouse-cutting` | **ACTION_SHORTCUT** | R1, R3 |
| 29 | `GET` | `/stock` | `getStock` | `warehouse-cutting` | **READ_TOOL** | R1, R3, R8 |
| 30 | `POST` | `/stocktakes` | `createStocktake` | `warehouse-cutting` | **ACTION_SHORTCUT** | R1, R3 |
| 31 | `POST` | `/stock-adjustments` | `createStockAdjustment` | `warehouse-cutting` | **ACTION_SHORTCUT** | R1, R3 |
| 32 | `POST` | `/cutting-results` | `recordCuttingResult` | `warehouse-cutting` | **ACTION_SHORTCUT** | R1, R3, R4 |
| 33 | `GET` | `/cut-batches` | `listCutBatches` | `warehouse-cutting, sewing` | **READ_TOOL** | R1, R3, R4 |
| 34 | `PUT` | `/lines/{lineId}/operators` | `assignOperator` | `sewing` | **ACTION_SHORTCUT** | R4 |
| 35 | `POST` | `/sewing-tallies` | `recordSewingTally` | `sewing` | **ACTION_SHORTCUT** | R4 |
| 36 | `GET` | `/sewing-tallies` | `listSewingTallies` | `sewing` | **READ_TOOL** | R1, R4 |
| 37 | `GET` | `/production/progress` | `listProductionProgress` | `sewing` | **READ_TOOL** | R1, R4, R5, R8 |
| 38 | `POST` | `/qc-inspections` | `inspectUnit` | `quality-payroll` | **ACTION_SHORTCUT** | R6 |
| 39 | `POST` | `/payroll/weekly/{periodId}` | `calculateWeeklyPayroll` | `quality-payroll` | **ACTION_SHORTCUT** | R7 |
| 40 | `GET` | `/payroll/weekly/{periodId}/bonus-pool` | `getBonusPool` | `quality-payroll` | **READ_TOOL** | R1, R7 |
| 41 | `POST` | `/overhead` | `recordOverhead` | `quality-payroll` | **ACTION_SHORTCUT** | R7 |
| 42 | `POST` | `/overhead/{periodId}/allocation` | `calculateOverhead` | `quality-payroll` | **ACTION_SHORTCUT** | R7 |
| 43 | `POST` | `/purchase-orders` | `createPurchaseOrder` | `procurement` | **ACTION_SHORTCUT** | R7 |
| 44 | `GET` | `/purchase-orders` | `listPurchaseOrders` | `procurement` | **READ_TOOL** | R1, R7 |
| 45 | `GET` | `/purchase-orders/{purchaseOrderId}` | `getPurchaseOrder` | `procurement` | **READ_TOOL** | R1, R7 |
| 46 | `POST` | `/purchase-orders/{purchaseOrderId}/approval` | `approvePurchaseOrder` | `procurement` | **ACTION_SHORTCUT** | R1, R7 |
| 47 | `POST` | `/supplier-invoices` | `recordSupplierInvoice` | `procurement` | **ACTION_SHORTCUT** | R7 |
| 48 | `GET` | `/supplier-invoices` | `listSupplierInvoices` | `procurement` | **READ_TOOL** | R1, R7 |
| 49 | `GET` | `/dashboard` | `getDashboard` | `files-portal` | **READ_TOOL** | R1, R4, R7 |
| 50 | `GET` | `/portal/orders/{orderId}/status` | `getPortalOrderStatus` | `files-portal` | **READ_TOOL** | R8 |
| 51 | `POST` | `/files/uploads` | `createFileUpload` | `files-portal` | **ACTION_SHORTCUT** | R1, R2, R3, R7, R8 |
| 52 | `POST` | `/files/uploads/{uploadId}/complete` | `completeFileUpload` | `files-portal` | **ACTION_SHORTCUT** | R1, R2, R3, R7, R8 |
| 53 | `POST` | `/internal/jobs/saturday-payroll` | `runSaturdayPayrollJob` | `jobs-search` | **EXCLUDED** (Daemon Job) | ServicePayrollJob |
| 54 | `POST` | `/internal/jobs/monthly-overhead` | `runMonthlyOverheadJob` | `jobs-search` | **EXCLUDED** (Daemon Job) | ServiceOverheadJob |
| 55 | `GET` | `/search/operational-documents` | `searchOperationalDocuments` | `jobs-search` | **READ_TOOL** | R1, R2, R3, R4, R7, R8 |
| 56 | `POST` | `/accounts` | `provisionAccount` | `workflow` | **ACTION_SHORTCUT** | R1 |
| 57 | `GET` | `/lines` | `listLines` | `workflow` | **READ_TOOL** | R1, R4, R7 |
| 58 | `POST` | `/lines` | `createLine` | `workflow` | **ACTION_SHORTCUT** | R4 |
| 59 | `GET` | `/operators` | `listOperators` | `workflow` | **READ_TOOL** | R1, R4, R7 |
| 60 | `POST` | `/operators` | `createOperator` | `workflow` | **ACTION_SHORTCUT** | R4 |
| 61 | `GET` | `/assignments` | `listAssignments` | `workflow` | **READ_TOOL** | R4, R5 |
| 62 | `POST` | `/sewing-tallies/{tallyId}/verification` | `verifySewingTally` | `workflow` | **ACTION_SHORTCUT** | R4 |
| 63 | `GET` | `/assemblies` | `listAssemblies` | `workflow` | **READ_TOOL** | R1, R4, R6 |
| 64 | `POST` | `/assemblies` | `createAssembly` | `workflow` | **ACTION_SHORTCUT** | R4 |
| 65 | `GET` | `/assemblies/{assemblyId}` | `getAssembly` | `sewing, quality-payroll` | **READ_TOOL** | R1, R4, R6 |
| 66 | `GET` | `/sample-catalog` | `listSamples` | `workflow` | **READ_TOOL** | R1, R2 |
| 67 | `POST` | `/samples/{sampleId}/approval` | `approveSample` | `workflow` | **ACTION_SHORTCUT** | R2 |
| 68 | `POST` | `/samples/{sampleId}/orders` | `convertSampleToOrder` | `workflow` | **ACTION_SHORTCUT** | R1 |
| 69 | `GET` | `/rate-card-catalog` | `listRateCards` | `workflow` | **READ_TOOL** | R1, R2, R4 |
| 70 | `POST` | `/payroll-periods` | `createPayrollPeriod` | `workflow` | **ACTION_SHORTCUT** | R7 |
| 71 | `GET` | `/payroll-periods` | `listPayrollPeriods` | `workflow` | **READ_TOOL** | R1, R7 |
| 72 | `GET` | `/payroll/weekly/{periodId}/statement` | `getPayrollStatement` | `workflow` | **READ_TOOL** | R1, R7 |
| 73 | `POST` | `/payroll/weekly/{periodId}/approval` | `approvePayroll` | `workflow` | **ACTION_SHORTCUT** | R7 |
| 74 | `POST` | `/payroll/weekly/{periodId}/payment` | `recordPayrollPayment` | `workflow` | **ACTION_SHORTCUT** | R7 |
| 75 | `GET` | `/financial-rules` | `listFinancialRules` | `workflow` | **READ_TOOL** | R1, R7 |
| 76 | `POST` | `/financial-rules` | `proposeFinancialRule` | `workflow` | **ACTION_SHORTCUT** | R1, R7 |
| 77 | `POST` | `/financial-rules/{ruleId}/approval` | `approveFinancialRule` | `workflow` | **ACTION_SHORTCUT** | R1 |
| 78 | `GET` | `/client-invoices` | `listClientInvoices` | `workflow` | **READ_TOOL** | R1, R7 |
| 79 | `POST` | `/client-invoices` | `createClientInvoice` | `workflow` | **ACTION_SHORTCUT** | R7 |
| 80 | `GET` | `/client-invoices/{invoiceId}` | `getClientInvoice` | `workflow` | **READ_TOOL** | R1, R7, R8 |
| 81 | `POST` | `/client-invoices/{invoiceId}/issue` | `issueClientInvoice` | `workflow` | **ACTION_SHORTCUT** | R7 |
| 82 | `GET` | `/files/{fileId}/download` | `getFileDownload` | `workflow` | **READ_TOOL** (Binary Stream) | R1–R8 |
| 83 | `GET` | `/jobs/{jobId}` | `getJob` | `workflow` | **READ_TOOL** | R1, R7 |

---

## 6. Shop-Floor Token Budgeting & Stateless Pruning

### 6.1 Factory Network Constraints
In Ciwidey, West Java, factory connections operate at 1.0–2.0 Mbps upload bandwidth. Submitting unrestricted tool schemas (15,000+ tokens) wastes 1.8s+ in network transmission and risks ASGI worker pool starvation.

### 6.2 Per-Turn Token Budget Matrix ($\le 3,600$ Tokens)
| Context Component | Token Budget | Pruning & Optimization Policy |
|---|---|---|
| **System Prompt** | **~400 tokens** | Zero conversational fluff. Injects Bahasa Indonesia apparel vocabulary and read-only policy. |
| **Filtered Tool Schemas** | **~350–500 tokens** | Dynamically filtered to 3–8 authorized tools matching caller's active role. |
| **Sliding Chat History** | **~1,200 tokens** | Maximum 10 messages (`maxItems: 10`, 5 user turns + 5 assistant turns). Oldest evicted FIFO. |
| **Tool Response Compactor** | **~300 tokens** | JSON collection responses sliced to top 3 items plus `{ "total": N, "truncated": true }`. |
| **Current User Query** | **~100–200 tokens** | Validated against `1..4000` character bounds. |
| **Model Output Budget** | **~500–800 tokens** | Capped at `max_tokens=800` to prevent runaway generation. |
| **Total Context Window** | **$\le 3,600$ tokens** | Fast sub-3.0s inference on local Ollama (`qwen2.5:7b-instruct-q4_K_M`) and cloud models. |

### 6.3 Timeout & Concurrency Safeguards
- **Local Ollama Timeout:** 15.0 seconds.
- **Cloud Endpoint Timeout:** 10.0 seconds.
- **Internal REST Tool Query Timeout:** 5.0 seconds.
- **Worker Isolation:** Chat endpoint runs in an isolated `asyncio.Semaphore(5)` pool. On timeout, an RFC 7807 HTTP 504 `GATEWAY_TIMEOUT` is returned immediately.

---

## 7. Migration & Phasing Plan

1. **Phase 1 (Specification Hardening & Contract Design):** Complete Gherkin scenarios (`spec.md`), delta OpenAPI contract (`copilot-openapi.yaml`), technical design (`design.md`), and pre-implementation hardening report (`pre-implementation-hardening.md`).
2. **Phase 2 (Gateway Implementation & Mount):** Mount `CopilotRouter` behind `AI_COPILOT_ENABLED` flag, implement `ReadOnlyToolExecutor` and dynamic role filtering with full test suite.
3. **Phase 3 (UI Widget & Action Shortcut Cards):** Wire React chat widget with `ActionShortcut` card renderers.
4. **Phase 4 (Mobile Extension via Messaging Gateway):** Add deterministic slash commands (`/status`, `/gaji`) to Telegram and WhatsApp.
