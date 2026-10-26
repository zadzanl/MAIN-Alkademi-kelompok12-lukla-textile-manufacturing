# Tasks: Operational AI Copilot Gateway

> [!IMPORTANT]
> **SPECIFICATION HARDENING & IMPLEMENTATION ROADMAP:**
> Phase 1 specification hardening tasks are synchronized and verified.
> Implementation phases (Phase 2 through Phase 4) must strictly observe the hardened contracts and boundaries defined in `specs/operational-copilot-gateway/spec.md`, `contracts/copilot-openapi.yaml`, and `design.md`.

---

## 1. Specification Hardening & Contract Design (Phase 1 - Completed)

- [x] 1.1 **Harden OpenAPI Copilot Endpoint Schema:** Formalize `POST /api/v1/copilot/chat` in `contracts/copilot-openapi.yaml` with explicit request/response schemas (`ChatTurnRequest`, `ChatTurnResponse`, `ActionShortcut`, `TokenUsage`) and RFC 7807 problem payloads (400, 401, 403, 422, 504), validated via `validate-blueprint.py`.
- [x] 1.2 **Sharpen RBAC Catalog & Query Sanitizers:** Audit all 83 OpenAPI operations against `04-rbac-matrix.md` across all 8 roles, establishing the 37 GET read-only tool whitelist and 46 mutating operations converted to Action Shortcuts.
- [x] 1.3 **Specify Context & Token Window Policies:** Define rolling context compaction, conversation pruning thresholds (10 turns, collection top 3 items), and factory bandwidth token budgeting ($\le 3,600$ tokens).
- [x] 1.4 **Formulate Cost & Latency Benchmark SLAs:** Establish performance baselines and strict timeouts (15.0s local Ollama, 10.0s cloud LLM, 5.0s internal queries) returning RFC 7807 HTTP 504 `GATEWAY_TIMEOUT`.
- [x] 1.5 **Author Pre-Implementation Hardening Report:** Document complete specification hardening deliverables, traceability, and verification evidence in `artifacts/pre-implementation-hardening.md`.

## 2. Gateway Implementation & Integration (Phase 2)

- [ ] 2.1 Mount `CopilotRouter` onto FastAPI application behind `AI_COPILOT_ENABLED` feature flag.
- [ ] 2.2 Wire `ReadOnlyToolExecutor` to internal test/HTTP client forwarding verified `Authorization: Bearer <token>` and `X-Request-Id`.
- [ ] 2.3 Implement unit tests ensuring any non-`GET` tool invocation is rejected with HTTP 403 Forbidden and generates security audit log.
- [ ] 2.4 Verify dynamic role tool filtering prevents unauthenticated Maklon clients from viewing internal financial/production tools.

## 3. UI Component Integration & User Experience (Phase 3)

- [ ] 3.1 Integrate `CopilotChatWidget.tsx` into the web dashboard layout.
- [ ] 3.2 Implement Action Shortcut card renderer verifying deep links navigate to audited forms across `VIEW-01`..`VIEW-06` with populated query parameters.
- [ ] 3.3 Add Indonesian apparel terminology system prompt tuning (*maklon*, *CMT*, *buangan kain*, *ongkos jahit*, *mandor*).

## 4. Verification & Regression Testing (Phase 4)

- [ ] 4.1 Write integration test proving the Copilot cannot mutate double-entry ledger rows under any prompt injection attempt.
- [ ] 4.2 Validate tenant isolation: verify Maklon Client A receives zero search results or stock records belonging to Client B.
- [ ] 4.3 Run `python scripts/check_workspace_hygiene.py` to confirm zero workspace drift.
