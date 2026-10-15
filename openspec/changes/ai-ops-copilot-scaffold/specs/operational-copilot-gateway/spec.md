# Capability: Operational AI Copilot Gateway

> [!IMPORTANT]
> **REFINEMENT & HARDENING DIRECTIVE FOR DOWNSTREAM AGENTS:**
> This capability specification is a **scaffolding contract and planning baseline**.
> Downstream implementing agents MUST:
> 1. Expand the test scenarios to cover specific OpenAPI query endpoints (stock lot checks, line throughput pacing, defect tallies).
> 2. Define formal JSON schema contracts for error handling when tools return RFC 7807 `ProblemException`.
> 3. Add explicit rate-limiting and token abuse prevention requirements per tenant.
> 4. Specify token rotation handling when chat sessions exceed JWT expiration.

---

## ADDED Requirements

### Requirement: Authenticated Read-Only Tool Execution
The system SHALL provide an operational query gateway that executes approved read-only tool calls strictly under the caller's verified OAuth2 Bearer token, enforcing database Row-Level Security (RLS) and rejecting any state-mutating HTTP methods (`POST`, `PUT`, `DELETE`).

#### Scenario: Authorized read-only stock inquiry
- **WHEN** an authenticated user with role `Warehouse` or `Owner` queries fabric stock availability via conversational prompt
- **THEN** the system SHALL execute `GET /warehouse/stock` using the caller's `Authorization: Bearer <token>` and `X-Request-Id`
- **AND** the system SHALL return only inventory records authorized for the caller's active tenant and legal owner scope

#### Scenario: Rejection of mutating tool invocation
- **WHEN** an LLM agent attempts to invoke a state-mutating endpoint (such as `POST /ledger/transactions` or `POST /warehouse/stock/issue`)
- **THEN** the gateway executor SHALL reject the execution with HTTP 403 Forbidden
- **AND** the system SHALL log a security audit event without altering double-entry ledger or inventory state

---

### Requirement: Dynamic Multi-Role Tool Schema Filtering
The system SHALL dynamically filter the OpenAPI tool schemas presented to the foundational model based on the caller's verified `AuthContext.roles`, preventing context window bloat and cross-tenant privilege discovery.

#### Scenario: Role-restricted tool definition generation
- **WHEN** a client user with role `MaklonClient` initiates a chat session
- **THEN** the system SHALL provide tool schemas restricted to their client-specific operations (e.g. `listOrders`, `getPortalOrderStatus`, `getStock` scoped to their client ID)
- **AND** the system SHALL NOT expose internal manufacturing tools (e.g. `getBonusPool`, `getLedgerEntries`, `calculateWeeklyPayroll`)

---

### Requirement: Action Shortcut Deep-Link Generation
The system SHALL detect user intent for operational mutations and provide pre-filled, clickable Action Shortcut hyperlinks to audited web UI views instead of attempting autonomous execution.

#### Scenario: Cutting entry intent generates action shortcut
- **WHEN** a user states intent to record cutting results for an active order
- **THEN** the system SHALL generate a structured Action Shortcut containing the target URL (e.g., `/cutting/new?orderId=<id>`)
- **AND** the system SHALL NOT commit cutting data directly to the database

---

### Requirement: Model-Agnostic Inference Abstraction
The system SHALL abstract LLM interaction behind a provider-portable client interface supporting local on-premise inference engines (e.g., Ollama) alongside commercial cloud APIs without changing the tool execution layer.

#### Scenario: Offline local inference fallback
- **WHEN** the system is configured with `COPILOT_LLM_PROVIDER=ollama`
- **THEN** the gateway SHALL dispatch completions to the configured local OpenAI-compatible endpoint without transmitting client operational data to external third-party cloud servers
