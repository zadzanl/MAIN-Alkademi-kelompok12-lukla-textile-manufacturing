# Technical Design: Operational AI Copilot Architecture

> [!IMPORTANT]
> **REFINEMENT DIRECTIVE FOR SUBSEQUENT AGENTS:**
> This design document represents the **initial architectural blueprint and boundary definition**.
> Downstream implementing agents MUST:
> 1. **Harden Tool Parameter Validation:** Implement strict Pydantic parsing for all model tool arguments before forwarding to HTTP clients.
> 2. **Refine Context Window Management:** Enforce token limits, summarization thresholds, and pruning strategies for long chat sessions.
> 3. **Benchmark Local Inference Latency:** Conduct load tests comparing quantized local Ollama instances (`qwen2.5:7b-instruct-q4_K_M`) against remote endpoints on high-latency factory internet.
> 4. **Harden Failure Isolation:** Ensure timeout or circuit breaker patterns prevent LLM stalls from consuming API gateway worker pools.

---

## Context

The Lukla Operations Engine operates a hybrid apparel manufacturing facility in Ciwidey, West Java, supporting up to 70 sewing stations and multi-tenant B2B Maklon production. The core engine is built on an immutable double-entry accounting ledger (`NFR-02`) and strict custodial anti-cross-contamination rules.

A conversational Copilot is desired to allow users (Executive, Production Head/Mandor, Maklon Client) to query order status, floor throughput, and inventory balances naturally. However, giving an LLM autonomous mutation capabilities directly against the 69 backend endpoints violates core invariants, introduces financial hallucination risks, and could breach tenant data boundaries.

---

## Goals / Non-Goals

### Goals
- Provide an authenticated conversational interface capable of answering operational inquiries in natural language (Bahasa Indonesia with apparel domain terms).
- Execute read queries strictly through approved, curated `/api/v1` endpoints forwarding the user's verified Bearer JWT (`AuthContext`).
- Dynamically filter tool schemas at runtime based on caller RBAC roles.
- Surface interactive **Action Shortcuts** (deep links) directing users to audited UI forms for mutations.
- Keep the Copilot decoupled from the transactional messaging outbox (`plan_messaging_bots_integration`).

### Non-Goals
- Autonomous state-mutating execution (no direct `POST`, `PUT`, or `DELETE` calls by the LLM).
- Merging outbox push notifications into the LLM chat pipeline.
- Granting ambient superuser credentials or bypassing PostgreSQL Row-Level Security.

---

## Decisions

### Decision 1: Read-Only Tool Execution with JWT Passthrough
- **Choice:** [`ReadOnlyToolExecutor`](file:///C:/Users/lenovo/.gemini/antigravity/worktrees/hackathon-MAIN-alkademi/scaffold_ai_ops_chatbot/prototypes/ai-copilot/backend/executor.py) explicitly enforces `method == "GET"` and forwards incoming `Authorization: Bearer <token>` and `X-Request-Id` headers.
- **Why:** Inherits existing application security, tenant scoping, and PostgreSQL RLS without building a custom security layer.
- **Alternatives Considered:**
  - *Ambient Master Key:* Rejected; allows prompt injection to expose cross-tenant client inventory.
  - *Autonomous Mutation:* Rejected; hallucinations violate double-entry ledger invariants.

### Decision 2: Action Shortcuts Protocol (Deep-Links)
- **Choice:** When user asks to perform an action (e.g. cutting, tallying, QC defect logging), the assistant responds with an actionable UI deep link (e.g., `/cutting/new?orderId=104`) via [`shortcuts.py`](file:///C:/Users/lenovo/.gemini/antigravity/worktrees/hackathon-MAIN-alkademi/scaffold_ai_ops_chatbot/prototypes/ai-copilot/backend/shortcuts.py).
- **Why:** Preserves human-in-the-loop integrity, CSRF tokens, client-side validation, and mandatory `Idempotency-Key` generation.
- **Alternatives Considered:**
  - *Chat-based Write Proposals:* Overengineers conversational confirmations when a verified web form already exists.

### Decision 3: Dynamic Multi-Role Tool Filtering
- **Choice:** Filter the tool catalog per request using [`filter_tools_for_roles(roles)`](file:///C:/Users/lenovo/.gemini/antigravity/worktrees/hackathon-MAIN-alkademi/scaffold_ai_ops_chatbot/prototypes/ai-copilot/backend/registry.py).
- **Why:** Passing all 69 OpenAPI endpoints consumes 35k+ tokens per turn, increases latency, and degrades tool selection accuracy.
- **Alternatives Considered:**
  - *Static tool catalog:* Rejected; exposes forbidden administrative tools to external Maklon clients.

### Decision 4: Decoupling from Messaging Outbox Gateway
- **Choice:** Maintain [`scaffold_ai_ops_chatbot`](file:///C:/Users/lenovo/.gemini/antigravity/worktrees/hackathon-MAIN-alkademi/scaffold_ai_ops_chatbot/prototypes/ai-copilot/README.md) and [`plan_messaging_bots_integration`](file:///C:/Users/lenovo/.gemini/antigravity/worktrees/hackathon-MAIN-alkademi/plan_messaging_bots_integration/openspec/changes/lukla-ops-engine-planning/20-messaging-bots-scaffold.md) as separate, modular layers.
- **Why:** Outbox notifications require 100% deterministic Jinja2 templates (zero LLM in delivery path) to avoid wage hallucinations. Inbound mobile queries can evolve in Phase 2 via deterministic slash commands (`/status`, `/gaji`).

---

## Risks / Trade-offs

- **[Risk] High Latency on Weak Factory Connections:** Cloud LLM calls (OpenAI/Anthropic) may suffer from high latency or connection drops.
  - *Mitigation:* Support on-premise local Ollama inference (`qwen2.5:7b`) deployed on a factory edge machine or LAN server.
- **[Risk] Prompt Injection Exploits:** User crafts prompt to bypass role instructions.
  - *Mitigation:* System instructions do not enforce security; security is enforced at the network proxy layer by `ReadOnlyToolExecutor` and PostgreSQL RLS.
- **[Risk] User Confusion over Read-Only Limitation:** User expects the bot to execute orders directly in chat.
  - *Mitigation:* Clear system prompt expectations and prominent Action Shortcut cards that explain the 1-click transition to the audited form.

---

## Migration & Phasing Plan

1. **Phase 1 (Prototype / Spike):** Verify in-app React widget and FastAPI gateway in `prototypes/ai-copilot/`.
2. **Phase 2 (OpenSpec Graduation):** Downstream agent hardens specifications, defines formal OpenAPI contract for `/api/v1/copilot/chat`, and adds tests.
3. **Phase 3 (Mobile Extension via Messaging Gateway):** Implement deterministic slash-commands on Telegram before connecting conversational LLM capabilities to external mobile channels.
