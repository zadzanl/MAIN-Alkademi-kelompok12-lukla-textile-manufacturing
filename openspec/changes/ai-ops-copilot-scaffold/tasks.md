# Tasks: Operational AI Copilot Gateway

> [!IMPORTANT]
> **REFINEMENT, SHARPENING, AND HARDENING MANDATE FOR DOWNSTREAM AGENTS:**
> Whatever agent or engineer picks up this change in subsequent development cycles
> **MUST refine, enhance, sharpen, and harden this specification and its test suites further**.
> Do NOT jump to production deployment until Phase 2 tasks (formal OpenAPI schema, token safety gates, and regression tests) are rigorously specified and validated.

---

## 1. Specification Hardening & Contract Design (Phase 2 - Next Agent Mandate)

- [ ] 1.1 **Harden OpenAPI Copilot Endpoint Schema:** Formalize `/api/v1/copilot/chat` in `contracts/openapi.yaml` with explicit request/response schemas, SSE streaming response types, and RFC 7807 problem payloads.
- [ ] 1.2 **Sharpen RBAC Catalog & Query Sanitizers:** Audit all 69 operation IDs to finalize the complete read-only whitelist, defining strict Pydantic argument validators for each tool.
- [ ] 1.3 **Specify Context & Token Window Policies:** Define rolling context compaction, conversation pruning thresholds, and session timeout boundaries.
- [ ] 1.4 **Formulate Cost & Latency Benchmark SLAs:** Establish performance baselines for on-premise Ollama (`qwen2.5:7b`) vs cloud models under variable factory internet connectivity.

## 2. Gateway Implementation & Integration

- [ ] 2.1 Mount `CopilotRouter` onto FastAPI application behind `AI_COPILOT_ENABLED` feature flag.
- [ ] 2.2 Wire `ReadOnlyToolExecutor` to internal test/HTTP client forwarding verified `Authorization: Bearer <token>` and `X-Request-Id`.
- [ ] 2.3 Implement unit tests ensuring any non-`GET` tool invocation is rejected with HTTP 403 Forbidden.
- [ ] 2.4 Verify dynamic role tool filtering prevents unauthenticated Maklon clients from viewing internal financial/production tools.

## 3. UI Component Integration & User Experience

- [ ] 3.1 Integrate `CopilotChatWidget.tsx` into the web dashboard layout.
- [ ] 3.2 Implement Action Shortcut card renderer verifying deep links navigate to audited forms with populated query parameters.
- [ ] 3.3 Add Indonesian apparel terminology system prompt tuning (*maklon*, *CMT*, *buangan kain*, *ongkos jahit*, *mandor*).

## 4. Verification & Regression Testing

- [ ] 4.1 Write integration test proving the Copilot cannot mutate double-entry ledger rows under any prompt injection attempt.
- [ ] 4.2 Validate tenant isolation: verify Maklon Client A receives zero search results or stock records belonging to Client B.
- [ ] 4.3 Run `python scripts/check_workspace_hygiene.py` to confirm zero workspace drift.
