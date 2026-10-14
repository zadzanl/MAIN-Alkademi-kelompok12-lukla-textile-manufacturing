# Prototype Spike: Lukla Operational AI Copilot

> **Status:** Experimental Breadth-First-Search (BFS) Prototype  
> **Location:** `prototypes/ai-copilot/`  
> **Boundary:** Completely isolated from core ledger invariants; 100% Read-Only + Action Shortcuts Navigation.

---

## 🎯 Architecture & Design Philosophy

This prototype scaffolds a foundational model chatbot (ChatGPT-like interface) that interacts with the Lukla Operations Engine endpoints as callable tools.

```
+-----------------------------------------------------------------------------------+
|                                 USER BROWSER                                      |
|    +-------------------------------------------------------------------------+    |
|    |     CopilotChatWidget.tsx (Streaming Chat + Action Shortcut Cards)       |    |
|    +-------------------------------------------------------------------------+    |
+------------------------------------------▲----------------------------------------+
                                           │ SSE / JSON + Bearer JWT
                                           ▼
+-----------------------------------------------------------------------------------+
|                        COPILOT GATEWAY (prototypes/ai-copilot)                    |
|                                                                                   |
|    +----------------------+     +----------------------+     +---------------+    |
|    |   Dynamic Registry   |     |    LLM Provider      |     | Action Route  |    |
|    |  (Role-based Tools)  |     | (Ollama/Claude/GPT4) |     |   Shortcuts   |    |
|    +----------▲-----------+     +----------▲-----------+     +-------▲-------+    |
|               │                            │                         │            |
|               └────────────────────────────┼─────────────────────────┘            |
|                                            ▼                                      |
|                             +------------------------------+                      |
|                             |    ReadOnlyToolExecutor      |                      |
|                             | (Strict GET-Only + Bearer)   |                      |
|                             +--------------▲---------------+                      |
+--------------------------------------------┼--------------------------------------+
                                             │ HTTP GET (with actor JWT)
                                             ▼
+-----------------------------------------------------------------------------------+
|                          CORE LUKLA ENGINE (/api/v1)                              |
|                                                                                   |
|   +-------------------+  +-------------------+  +------------------------------+  |
|   | /warehouse/stock  |  | /sewing/progress  |  | /orders                      |  |
|   +-------------------+  +-------------------+  +------------------------------+  |
|   | /qc/bonus-pool    |  | /ledger/entries   |  | /search/operational-docs     |  |
|   +-------------------+  +-------------------+  +------------------------------+  |
+-----------------------------------------------------------------------------------+
```

---

## 🔑 Core Guarantees & Loose Ends

### 1. Strictly Read-Only Assistant (Zero Ledger Risk)
- The model **never** executes state-mutating endpoints (`POST`, `PUT`, `DELETE`).
- Invariant: [ReadOnlyToolExecutor](file:///C:/Users/lenovo/.gemini/antigravity/worktrees/hackathon-MAIN-alkademi/scaffold_ai_ops_chatbot/prototypes/ai-copilot/backend/executor.py) explicitly rejects any non-`GET` method and restricts calls strictly to [`READ_TOOL_CATALOG`](file:///C:/Users/lenovo/.gemini/antigravity/worktrees/hackathon-MAIN-alkademi/scaffold_ai_ops_chatbot/prototypes/ai-copilot/backend/registry.py).
- Result: Impossible for hallucinated arguments to create unvouched double-entry transactions or cross-contaminate client fabric inventory.

### 2. Action Shortcuts Navigation (Deep-Links)
- When a user asks the Copilot to perform an action (e.g. *"Saya mau input hasil potong kain Order #104"*), the Copilot responds with explanation and renders an interactive **Action Shortcut Card** (e.g., `[Catat Hasil Pemotongan Order #104](/cutting/new?orderId=104)`).
- The human clicks the link and executes the transaction on the audited UI form with full client-side validation, `Idempotency-Key` generation, and audit logging.

### 3. Dynamic Multi-Role Tool Filtering
- Instead of exposing all 69 endpoints at once (which explodes token cost and causes hallucination), [`filter_tools_for_roles`](file:///C:/Users/lenovo/.gemini/antigravity/worktrees/hackathon-MAIN-alkademi/scaffold_ai_ops_chatbot/prototypes/ai-copilot/backend/registry.py) inspects the caller's verified JWT roles (`AuthContext.roles`) and supplies only authorized query tools.
- A Maklon Client sees only order status and their own stock; a Mandor sees sewing lines and defect tallies; an Owner sees macro financial entries.

### 4. Provider Agnosticism
- Through [`BaseLLMClient`](file:///C:/Users/lenovo/.gemini/antigravity/worktrees/hackathon-MAIN-alkademi/scaffold_ai_ops_chatbot/prototypes/ai-copilot/backend/provider.py), the prototype can run against local offline models (e.g., Ollama running `qwen2.5:7b` or `llama3.1:8b` for cost and privacy) or hosted cloud endpoints (OpenAI / Anthropic).

---

## 📂 File Manifest

| File | Purpose |
| :--- | :--- |
| `backend/config.py` | Environment and provider configuration. |
| `backend/schemas.py` | Pydantic models for chat turns, tools, and action shortcuts. |
| `backend/registry.py` | Curated read-only tool catalog and dynamic role-based filtering. |
| `backend/executor.py` | HTTP client proxy dispatching GET queries with caller JWT passthrough. |
| `backend/shortcuts.py` | Rule-based intent matcher generating deep-link shortcut cards. |
| `backend/provider.py` | Model-agnostic LLM client (supporting Mock, Ollama, OpenAI). |
| `frontend/CopilotChatWidget.tsx` | React widget with streaming chat, role badge, and shortcut cards. |
| `SPEC_ALTERATION_PROPOSAL.md` | Detailed proposal for formal BRD v2.3 / PRD v2.0 Wagile graduation. |
