# Change Proposal: Lukla Intelligence Scaffolding & Planning Stub

> [!IMPORTANT]
> **HANDOFF DIRECTIVE FOR DOWNSTREAM AGENTS / ENGINEERS:**
> This change is an **initial architectural planning stub and breadth-first exploration scaffold**.
> Whatever agent or engineer picks up this change in subsequent iterations **MUST refine, enhance, sharpen, and harden this specification further** before proposing production implementation. Specifically:
> 1. Harden the dynamic RBAC tool catalog and argument sanitizers.
> 2. Formulate concrete latency and cost SLAs for on-premise Ollama vs. cloud providers.
> 3. Define formal OpenAPI schemas for `/api/v1/copilot/chat` endpoints.
> 4. Ensure absolute zero-mutation guarantees for the double-entry ledger remain cryptographically and programmatically enforced.

---

## Why

Factory executives, sewing line forepersons (mandors), and B2B Maklon clients currently have to navigate complex tabular ERP screens to track order milestones, monitor sewing station pacing, check fabric balances, and detect QC bottlenecks. 

Providing a ChatGPT-like conversational AI Copilot dramatically accelerates operational visibility. However, directly giving an autonomous LLM write access to the Lukla double-entry ledger and custodial inventory endpoints introduces catastrophic hallucination, financial, and multi-tenant leakage risks. 

This change establishes the formal architectural planning stub for a **Read-Only Operational Copilot Gateway with Action Shortcut Navigation (Deep Links)**, decoupling in-app human intelligence queries from external push notification pipelines (e.g. `plan_messaging_bots_integration`).

---

## What Changes

- **Introduces Operational AI Copilot Gateway (`operational-copilot-gateway`):** A fenced, model-agnostic assistant interface that queries existing read-only `/api/v1` endpoints under the caller's verified OAuth2 Bearer token.
- **Enforces Zero Autonomous State Mutations:** The LLM cannot execute state-mutating endpoints (`POST`, `PUT`, `DELETE`).
- **Introduces Action Shortcut Protocol:** When users express intent to perform a transaction (e.g., recording cutting, inputting defect tallies, approving payroll), the Copilot responds with deep links to audited web UI forms with pre-filled parameters.
- **Dynamic Role-Based Tool Filtering:** Tools are dynamically filtered at runtime matching caller roles (`AuthContext.roles`) to prevent prompt bloat and cross-tenant privilege escalation.
- **Architectural Decoupling from Messaging Outbox:** Keeps the in-app Copilot cleanly decoupled from the asynchronous outbox notification gateway (`plan_messaging_bots_integration`), establishing a phased stepping stone for future mobile extensions.

---

## Capabilities

### New Capabilities
- `operational-copilot-gateway`: Read-only conversational intelligence gateway with dynamic RBAC tool filtering, actor token passthrough, and action shortcut navigation.

### Modified Capabilities
*(None; baseline planning stub)*

---

## Impact

- **Backend:** Scaffolds gateway adapters under `prototypes/ai-copilot/` and plans future `/api/v1/copilot/chat` endpoint. No core double-entry accounting or inventory database schemas are altered.
- **Frontend:** Provides `CopilotChatWidget.tsx` React component capable of rendering streaming markdown and clickable Action Shortcut cards.
- **Security & RBAC:** Enforces strict Bearer JWT token delegation; caller context inherits PostgreSQL Row-Level Security (`set_db_tenant_context`).
- **Dependencies:** Supports zero-cost local LLM inference (Ollama `qwen2.5:7b`) with optional OpenAI/Anthropic-compatible adapters.
