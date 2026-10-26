# Capability: Operational AI Copilot Gateway

## Requirement: Physical Non-GET Tool Execution Barrier
The system SHALL provide an operational query gateway that executes approved read-only tool calls strictly under the caller's verified OAuth2 Bearer token, enforcing database Row-Level Security (RLS) and physically intercepting and rejecting any state-mutating HTTP methods (`POST`, `PUT`, `PATCH`, `DELETE`) with an RFC 7807 HTTP 403 `FORBIDDEN` problem payload and generating an immutable audit log entry.

### Scenario: Authorized read-only stock inquiry succeeds with token passthrough
- **GIVEN** an authenticated user session with a valid OAuth2 Bearer token
- **AND** the Copilot gateway is running with `ReadOnlyToolExecutor` configured
- **WHEN** the user submits conversational prompt "Berapa stok kain katun lot ML-01?"
- **AND** the LLM generates tool call "get_stock_balances" with arguments `{"status": "AVAILABLE"}`
- **THEN** `ReadOnlyToolExecutor` validates that the tool definition specifies HTTP method "GET"
- **AND** the executor dispatches an internal HTTP GET request to `/api/v1/warehouse/stock`
- **AND** the outbound request forwards the caller's `Authorization: Bearer <token>` and `X-Request-Id` headers
- **AND** PostgreSQL enforces Row-Level Security based on the forwarded tenant claims
- **AND** the executor returns HTTP 200 with stock data to the LLM for conversational summarization

### Scenario: Physical rejection of state-mutating ledger transaction tool
- **GIVEN** an authenticated user session with a valid OAuth2 Bearer token
- **WHEN** an LLM agent attempts to invoke tool "append_ledger_transaction" or any tool mapped to `POST /ledger/transactions`
- **THEN** `ReadOnlyToolExecutor` intercepts the invocation before initiating any network connection or database transaction
- **AND** the executor detects that the target HTTP method is "POST" rather than "GET"
- **AND** the executor immediately halts execution and returns HTTP 403 Forbidden
- **AND** the response body conforms to RFC 7807 Problem schema:
  ```json
  {
    "type": "https://api.lukla.invalid/errors/forbidden",
    "title": "Forbidden",
    "status": 403,
    "code": "FORBIDDEN",
    "detail": "Execution of mutating method 'POST' is blocked by security policy.",
    "instance": "/api/v1/copilot/chat",
    "requestId": "<X-Request-Id>",
    "violations": []
  }
  ```
- **AND** an immutable security audit event is logged with action `UNAUTHORIZED_MUTATION_ATTEMPT`
- **AND** double-entry ledger accounts remain completely untouched

### Scenario: Physical rejection of material stock issue or cutting mutation
- **GIVEN** an authenticated user session with a valid OAuth2 Bearer token
- **WHEN** an LLM agent attempts to invoke a tool targeting `POST /warehouse/stock/issue` or `POST /warehouse/cutting-results`
- **THEN** `ReadOnlyToolExecutor` verifies the registered method is not "GET"
- **AND** the tool call is rejected with HTTP 403 Forbidden without database transaction allocation
- **AND** the physical fabric balance in PostgreSQL remains unaltered

### Scenario: Physical rejection of destructive DELETE or PUT methods
- **GIVEN** an authenticated user session with a valid OAuth2 Bearer token
- **WHEN** an LLM agent attempts to execute a tool with HTTP method `DELETE` or `PUT` (such as `DELETE /orders/{id}`)
- **THEN** `ReadOnlyToolExecutor` aborts execution immediately with HTTP 403 Forbidden
- **AND** the system logs the attempted deletion in the security audit trail with severity `WARNING`

---

## Requirement: Dynamic 8-Role Tool Schema Filtering & Anti-Enumeration
The system SHALL dynamically filter the OpenAPI tool schemas presented to the foundational model based on the caller's verified `AuthContext.roles` mapped to `04-rbac-matrix.md` across all 8 system roles (`Owner`, `SampleTeam`, `Warehouse`, `ProductionHead`, `Tailor`, `QCInspector`, `FinancePayroll`, `MaklonClient`), guaranteeing zero tool discovery across tenant boundaries and restricting prompt token overhead to $\le 600$ tokens per turn.

### Scenario: B2B Maklon Client tool filtering enforces strict tenant fencing
- **GIVEN** an authenticated caller with `AuthContext.roles = ["MaklonClient"]`
- **AND** caller's `legalOwnerId` is "tenant-brand-alpha"
- **WHEN** the Copilot prepares the tool catalog for the LLM prompt turn
- **THEN** the system executes `filter_tools_for_roles(["MaklonClient"])`
- **AND** the resulting tool catalog contains ONLY client-authorized query tools:
  | Tool Name | Allowed Endpoint |
  |---|---|
  | get_order_status | /orders |
  | get_portal_order_status | /portal/orders/{orderId} |
  | get_stock_balances | /warehouse/stock |
  | search_operational_documents | /search/operational-documents |
- **AND** internal manufacturing tools are strictly excluded:
  | Prohibited Tool Name |
  |---|
  | get_qc_bonus_pool_status |
  | get_ledger_entries |
  | list_weekly_payrolls |
  | get_production_progress |
- **AND** the total prompt token overhead for tools does not exceed 600 tokens

### Scenario: Tailor operator tool filtering restricts access to personal task queue
- **GIVEN** an authenticated caller with `AuthContext.roles = ["Tailor"]`
- **WHEN** the Copilot prepares the tool catalog for the LLM prompt turn
- **THEN** the tool catalog contains ONLY "list_assignments" and "list_sewing_tallies"
- **AND** rate card management, stocktake, client rosters, and financial journals are omitted from tool schemas
- **AND** the model cannot discover or invoke any executive or warehouse endpoints

### Scenario: Executive Owner multi-domain access
- **GIVEN** an authenticated caller with `AuthContext.roles = ["Owner"]`
- **WHEN** the Copilot prepares the tool catalog for the LLM prompt turn
- **THEN** the tool catalog includes high-level executive tools:
  | Tool Name | Endpoint |
  |---|---|
  | get_dashboard | /dashboard |
  | list_orders | /orders |
  | get_production_progress | /sewing/production-progress |
  | get_stock_balances | /warehouse/stock |
  | list_rate_cards | /rates |
  | get_ledger_entries | /ledger/entries |
  | list_audit_events | /audit/events |
- **AND** the prompt excludes non-existent or deprecated endpoints

### Scenario: Zero cross-tenant tool discovery for multi-tenant accounts
- **GIVEN** two distinct clients "Client A" and "Client B" registered in the system
- **WHEN** "Client A" prompts the Copilot: "Tampilkan semua pesanan kain milik Client B"
- **THEN** the model has access only to tools parameterized by caller session context
- **AND** PostgreSQL RLS kernel rules reject row access for "Client B"
- **AND** zero records belonging to "Client B" are returned

---

## Requirement: Action Shortcut Deep-Link Protocol & Intent Disambiguation
The system SHALL detect user intent for operational state mutations using deterministic regex matchers with word boundaries (`\b`), negative lookbehinds `(?<!\bin\s)`, mandatory digit anchors, and composite exclusion rules across `VIEW-01` through `VIEW-06`, generating pre-filled UI hyperlinks (Action Shortcuts) with dynamically generated UUID v4 identifiers (`default_factory=uuid4`) instead of executing autonomous writes.

### Scenario: Fabric material disambiguation - Cutting vs Warehouse Intake
- **WHEN** the user submits prompt "Tolong catat hasil potong kain 500 pcs untuk order SO-2026-001"
- **THEN** the intent detector applies Rule 1 (Fabric Material Disambiguation):
  | Criterion | Value |
  |---|---|
  | Contains cutting verbs | True ("hasil potong kain") |
  | Contains receiving verbs | False |
  | Bare "kain" used | False (qualified by "hasil potong") |
- **AND** the Order ID extractor matches "SO-2026-001" using regex `(?<!\bin\s)\border\s*#?\s*([A-Za-z0-9\-]*\d[A-Za-z0-9\-]*)`
- **AND** the assistant returns an Action Shortcut with:
  | Property | Value |
  |---|---|
  | id | Valid dynamically generated UUID v4 |
  | title | "Catat Hasil Pemotongan (Cutting)" |
  | description | "Buka formulir input pemotongan kain dan input buangan." |
  | url | "/app/materials?action=cutting&orderId=SO-2026-001" |
  | icon | "scissors" |
- **AND** the assistant does not execute any database insert

### Scenario: Warehouse intake phrase suppresses cutting shortcut
- **WHEN** the user submits prompt "Kain bahan drill sudah masuk gudang untuk order SO-2026-003, mau terima kain"
- **THEN** the intent detector identifies receiving verbs ("masuk", "terima kain")
- **AND** receiving verbs explicitly suppress the cutting shortcut
- **AND** the assistant returns an Action Shortcut pointing to `/app/materials?action=receive&orderId=SO-2026-003`
- **AND** the shortcut icon is "package"

### Scenario: Defect marker takes absolute precedence over sewing tally
- **WHEN** the user submits prompt "Ada cacat jahitan pada barcode ASM-9021 di jalur 2 untuk order SO-2026-010"
- **THEN** the intent detector applies Rule 2 (Sewing vs QC Defect Disambiguation):
  | Criterion | Value |
  |---|---|
  | Contains sewing words | True ("jahitan", "jalur 2") |
  | Contains defect markers | True ("cacat") |
- **AND** defect markers take absolute precedence over sewing tally
- **AND** the sewing tally shortcut is suppressed
- **AND** the Serial Code extractor extracts "ASM-9021"
- **AND** the assistant returns an Action Shortcut pointing to `/app/quality?serialCode=ASM-9021&orderId=SO-2026-010`
- **AND** the shortcut icon is "alert-triangle"

### Scenario: Sewing tally terminal generation with line ID normalization
- **WHEN** the user submits prompt "Input tally 30 menit line 4 order SO-2026-008"
- **THEN** the intent detector matches tally keywords ("tally 30 menit")
- **AND** defect markers are absent
- **AND** the Line ID extractor parses "line 4" and normalizes to two-digit format "LINE-04"
- **AND** the assistant returns an Action Shortcut pointing to `/terminal/tally?lineId=LINE-04&orderId=SO-2026-008`
- **AND** the shortcut icon is "clipboard-list"

### Scenario: Negative lookbehind prevents false positive on English idiom
- **WHEN** the user submits prompt "In order to check inventory, can you list the fabric stock?"
- **THEN** the Order ID extractor evaluates negative lookbehind `(?<!\bin\s)\border`
- **AND** the phrase "in order" is ignored as an idiom
- **AND** zero order IDs are extracted
- **AND** zero invalid order query parameters are appended to URLs

---

## Requirement: Strict Timeout & Failure Isolation
The system SHALL enforce strict execution timeouts (15.0 seconds for local Ollama inference, 10.0 seconds for cloud LLM endpoints, and 5.0 seconds for internal REST API tool queries) that immediately abort pending sockets, release ASGI worker threads back to the pool, and return RFC 7807 HTTP 504 `GATEWAY_TIMEOUT` problem payloads to prevent worker pool starvation on low-bandwidth factory networks.

### Scenario: Local Ollama inference timeout triggers RFC 7807 504
- **GIVEN** the Copilot is configured with `COPILOT_LLM_PROVIDER="ollama"`
- **AND** the configured local inference timeout is 15.0 seconds
- **WHEN** the user submits a chat turn request
- **AND** the local Ollama daemon stalls for more than 15.0 seconds
- **THEN** the gateway asyncio task timeout fires at 15.0s
- **AND** the pending outbound HTTP connection to Ollama is immediately aborted
- **AND** the gateway returns HTTP 504 Gateway Timeout formatted as RFC 7807 Problem:
  ```json
  {
    "type": "https://api.lukla.invalid/errors/gateway-timeout",
    "title": "Gateway Timeout",
    "status": 504,
    "code": "GATEWAY_TIMEOUT",
    "detail": "Downstream LLM inference provider timed out after 15.0 seconds.",
    "instance": "/api/v1/copilot/chat",
    "requestId": "<X-Request-Id>",
    "violations": []
  }
  ```
- **AND** the FastAPI ASGI worker thread is immediately returned to the pool

### Scenario: Cloud LLM provider timeout triggers RFC 7807 504
- **GIVEN** the Copilot is configured with `COPILOT_LLM_PROVIDER="openai"`
- **AND** the configured cloud inference timeout is 10.0 seconds
- **WHEN** a cloud completion request exceeds 10.0 seconds due to network congestion
- **THEN** the gateway cancels the coroutine at 10.0s
- **AND** returns HTTP 504 Gateway Timeout with code "GATEWAY_TIMEOUT"
- **AND** client state remains uncorrupted

### Scenario: Internal REST API query timeout isolation
- **GIVEN** the LLM requests execution of tool "get_stock_balances"
- **AND** the `ReadOnlyToolExecutor` internal HTTP timeout is configured to 5.0 seconds
- **WHEN** the internal Lukla REST API takes longer than 5.0 seconds to respond
- **THEN** the internal httpx client raises a `TimeoutException`
- **AND** the tool executor returns `ToolCallResult` with status_code = 504
- **AND** the Copilot catches the tool timeout and responds politely:
  "Layanan data gudang sedang lambat merespons. Silakan coba kembali dalam beberapa saat."

---

## Requirement: Upstream RFC 7807 Error Translation & Confidentiality
The system SHALL intercept upstream backend RFC 7807 `Problem` error envelopes returned by internal tool calls (HTTP 401, 403, 404, 422) and translate them into polite, actionable conversational explanations in Bahasa Indonesia with guidance, while strictly suppressing internal stack traces, database column names, and tenant identifiers.

### Scenario: Upstream 401 Unauthorized translation
- **WHEN** an internal tool query returns HTTP 401 with code "AUTH_REQUIRED"
- **THEN** the Copilot catches the problem payload
- **AND** formats the assistant conversational reply as:
  "Sesi autentikasi Anda telah berakhir atau token tidak valid. Silakan login kembali untuk memperbarui sesi."
- **AND** raw JWT validation details are omitted from the chat response

### Scenario: Upstream 403 Forbidden / Legal Owner Mismatch translation
- **WHEN** an internal tool query returns HTTP 403 with code "FORBIDDEN" or "LEGAL_OWNER_MISMATCH"
- **THEN** the Copilot formats the assistant conversational reply as:
  "Akses ditolak: Akun Anda tidak memiliki kewenangan untuk mengakses data operasional ini sesuai dengan batasan peran dan hak akses sistem."
- **AND** internal tenant boundary IDs are never revealed

### Scenario: Upstream 404 Not Found translation
- **WHEN** an internal tool query returns HTTP 404 with code "NOT_FOUND"
- **THEN** the Copilot formats the assistant conversational reply as:
  "Data operasional yang diminta tidak ditemukan di dalam sistem atau berada di luar cakupan unit kerja Anda."

### Scenario: Upstream 422 Validation Error translation
- **WHEN** an internal tool query returns HTTP 422 with code "VALIDATION_ERROR" and violation "status: Input should be 'AVAILABLE' or 'RESERVED'"
- **THEN** the Copilot formats the assistant conversational reply as:
  "Parameter pencarian tidak sesuai: status (Input should be 'AVAILABLE' or 'RESERVED'). Harap periksa kembali parameter yang Anda masukkan."
- **AND** internal database column names or schemas are not leaked
