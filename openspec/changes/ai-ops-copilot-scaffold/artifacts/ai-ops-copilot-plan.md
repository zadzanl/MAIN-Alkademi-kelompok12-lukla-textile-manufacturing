# Lukla Intelligence — Master Architectural Plan & Planning Stub

> [!IMPORTANT]
> **REFINEMENT, SHARPENING, AND HARDENING MANDATE FOR DOWNSTREAM AGENTS:**
> This document serves as the master planning stub for the `ai-ops-copilot-scaffold` change.
> Any agent, engineer, or team picking up this change in subsequent iterations:
> **MUST refine, enhance, sharpen, and harden this specification further.**
> - Do not bypass the Delegation Gate: Target files, signatures, error handling, and test scripts must be pinned down before production implementation.
> - Ensure zero-mutation guarantees for the double-entry accounting core remain non-negotiable.
> - Expand the Action Shortcut route mappings to cover cutting, tallying, defect classification, and payroll workflows.

---

## 1. Executive Summary

This change scaffolds an in-app **Operational AI Copilot** designed to give factory management, sewing floor forepersons (mandors), and B2B Maklon clients a conversational natural-language interface for interrogating operational status, inventory balances, and factory pacing.

The architecture strictly adheres to the **Read-Only Facade + Action Shortcut Navigation Pattern**:
- **Zero Autonomous Writes:** State mutations (ledger entries, stock issues, piece tallies, payroll approvals) are NEVER performed autonomously by the LLM.
- **Action Shortcuts:** The assistant surfaces interactive deep links to audited web forms with pre-filled parameters.
- **Dynamic Role Filtering:** Tools presented to the LLM are filtered based on the caller's verified `AuthContext.roles`.
- **Bearer Token Delegation:** Queries forward the user's active Bearer JWT and `X-Request-Id`, preserving PostgreSQL Row-Level Security (`FORCE ROW LEVEL SECURITY`).

---

## 2. Decoupling & Stepping-Stone Strategy with Messaging Bots

The in-app Copilot is intentionally kept decoupled from the asynchronous notification gateway (`plan_messaging_bots_integration`):

```
┌───────────────────────────────────────────────────────────────────────────────────┐
│ PHASE 1: FOUNDATION (Current Baseline)                                            │
│                                                                                   │
│  [ Web Dashboard Copilot ]                 [ Transactional Messaging Gateway ]    │
│  (scaffold_ai_ops_chatbot)                 (plan_messaging_bots_integration)      │
│  - Authenticated via JWT                   - Asynchronous outbox_events polling   │
│  - Read-only queries + Action Shortcuts    - 100% deterministic Jinja2 templates  │
│  - Zero ledger risk                        - Free outbound Telegram alerts        │
└─────────────────────────────────────────┬─────────────────────────────────────────┘
                                          │
                                          ▼
┌───────────────────────────────────────────────────────────────────────────────────┐
│ PHASE 2: DETERMINISTIC MOBILE COMMANDS (Zero LLM, Instant & Free)                 │
│                                                                                   │
│  User sends Telegram slash-command:                                               │
│  - `/status ORD-104` ───────► Calls GET /orders/ORD-104                           │
│  - `/stok FLEECE-01` ───────► Calls GET /warehouse/stock                          │
│  - `/gaji`           ───────► Calls GET /payroll/statements                       │
└─────────────────────────────────────────┬─────────────────────────────────────────┘
                                          │
                                          ▼
┌───────────────────────────────────────────────────────────────────────────────────┐
│ PHASE 3: TRUE MOBILE COPILOT (Natural Evolution)                                  │
│                                                                                   │
│  - Telegram bot forwards freeform natural language queries to ReadOnlyToolExecutor│
│  - Cryptographic OTP link binds Telegram Chat IDs to JWT claims                   │
│  - Mutations return authenticated mobile deep-links to the PWA form               │
└───────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Reference Prototype Scaffolding

An operational BFS prototype has been scaffolded under [`prototypes/ai-copilot/`](file:///C:/Users/lenovo/.gemini/antigravity/worktrees/hackathon-MAIN-alkademi/scaffold_ai_ops_chatbot/prototypes/ai-copilot):
- `backend/config.py`: Environment and LLM provider settings (Mock, Ollama, OpenAI).
- `backend/schemas.py`: Pydantic definitions for `ChatTurnRequest`, `ActionShortcut`, `ToolDefinition`.
- `backend/registry.py`: Curated catalog of read-only endpoints with `filter_tools_for_roles`.
- `backend/executor.py`: `ReadOnlyToolExecutor` with Bearer token delegation and non-GET rejection.
- `backend/shortcuts.py`: Rule-based intent matcher generating UI deep links (e.g. `/cutting/new?orderId=...`).
- `backend/provider.py`: Model-agnostic LLM client abstraction.
- `frontend/CopilotChatWidget.tsx`: React chat widget with streaming UI, role badges, and action shortcut cards.
- `SPEC_ALTERATION_PROPOSAL.md`: Specific amendments for BRD §3.3 and PRD §A.8 / Bagian B when graduating to production.
