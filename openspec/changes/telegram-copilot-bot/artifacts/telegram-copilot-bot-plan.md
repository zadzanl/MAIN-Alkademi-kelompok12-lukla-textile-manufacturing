# Plan: Telegram Copilot Bot

## ASK and NEED

- **ASK:** Add a Telegram bot that sends each message through the same operational Copilot path used by `/copilot/`, with deterministic role assignment from an admin-controlled passphrase.
- **NEED:** Give workers, stakeholders, owners, and clients a low-friction mobile read-only view of the data they are allowed to see, without allowing a Telegram user to self-claim `Owner` or bypass the existing role-filtered tool catalog.

## Evidence and current architecture

- The browser frontend on port 3009 proxies `/api/v1` to the root backend on port 8000 [code: `prototypes/sampling-spec-rnd/frontend/vite.config.ts`#L20-L31].
- The effective Copilot route is `POST /api/v1/copilot/chat`, implemented by `chat_turn`, which delegates to `_execute_copilot_turn` [code: `backend/app/api/v1/copilot.py`#L228-L249].
- `_execute_copilot_turn` filters read-only tools with `filter_tools_for_roles(roles)` and returns mutation requests as action shortcuts rather than executing writes [code: `backend/app/api/v1/copilot.py`#L104-L116].
- The current handler accepts `X-Roles` and `body.roles` before falling back to `Owner`; a Telegram adapter must not forward untrusted Telegram role input [code: `backend/app/api/v1/copilot.py`#L78-L103].
- The root API mounts the Copilot router under `/api/v1` [code: `backend/app/api/v1/__init__.py`#L1-L10].
- The root auth module currently exposes `get_current_auth_context` and `get_current_stock_auth_context`, whose allowed-role sets are limited to ledger/stock boundaries; it does not currently expose a general admin dependency for Telegram management [code: `backend/app/core/auth.py`#L145-L182].
- The root migration set currently contains `001_identities.sql`, `006_payroll_rate_cards.sql`, `007_payroll_qc_inputs.sql`, `008_double_entry_ledger.sql`, `009_payroll_core.sql`, `011_job_idempotency.sql`, and `012_payroll_routines_rls.sql`; no Telegram migration exists in the current checkout [code: `backend/migrations/001_identities.sql`#L1-L45; code: `backend/tools/run_payroll_db_tests.py`#L81-L93].
- The current checkout has broad uncommitted changes, including the Copilot/auth/app routers and multiple OpenSpec changes; this plan's paths and line references are a snapshot, not a promise that implementation may overwrite those files [code: `git status --short` observed 2026-10-16].
- Existing messaging planning already defines Telegram transport work, channel identities, tenant isolation, and a future webhook route, but is explicitly an exploratory outbound-notification stub [code: `openspec/changes/messaging-bots-integration/proposal.md`#L1-L20; code: `openspec/changes/messaging-bots-integration/design.md`#L42-L58].
- Telegram supports webhook delivery with an `X-Telegram-Bot-Api-Secret-Token` header, and Telegram does not allow `getUpdates` while a webhook is configured [doc: `https://core.telegram.org/bots/api`].

## Recommended scope

1. Add an inbound Telegram webhook route to the root FastAPI app.
2. Validate Telegram's webhook secret header before parsing or processing an update.
3. Resolve the Telegram `chat.id` to a server-side binding containing a verified actor identity, assigned role grant(s), tenant/scope, and active/revoked state. A bare role string is insufficient for client data isolation.
4. Add an admin-only enrollment flow that creates a single-use, short-lived enrollment code for a selected role. The user sends the code to the bot; the code is consumed once and binds that Telegram account persistently until revoked.
5. Convert the Telegram message into `ChatTurnRequest` and invoke the existing Copilot execution path with server-derived roles, never Telegram-supplied roles.
6. Send the Copilot reply back through Telegram's `sendMessage`, with bounded formatting and safe fallback to plain text.
7. Add idempotency for Telegram `update_id` so Telegram retries do not run the same Copilot turn twice.
8. Keep chat read-only: action shortcuts may be represented as text, but Telegram must not execute them or expose state-mutating endpoints.

## Target files

### Existing files to modify

- `c:\Projects\hackathon-MAIN-alkademi\backend\app\api\v1\__init__.py` — include the Telegram webhook/admin router alongside `copilot_router` [code: `backend/app/api/v1/__init__.py`#L1-L10].
- `c:\Projects\hackathon-MAIN-alkademi\backend\app\api\v1\copilot.py` — extract or reuse the existing `_execute_copilot_turn` seam so the webhook can call the same inference path without making an HTTP loopback request [code: `backend/app/api/v1/copilot.py`#L45-L76]. Preserve the web route's existing behavior unless a security fix is required.
- `c:\Projects\hackathon-MAIN-alkademi\backend\app\core\config.py` — add Telegram enablement, bot token, webhook secret, public webhook URL, and bounded message settings; do not invent an admin authorization setting in configuration [code: `backend/app/core/config.py`#L1-L13].
- `c:\Projects\hackathon-MAIN-alkademi\backend\app\main.py` — preserve request IDs/audit handling and expose the new routes through the existing application [code: `backend/app/main.py`#L1-L45].

### New files to create

- `c:\Projects\hackathon-MAIN-alkademi\backend\app\telegram\__init__.py` — package marker only.
- `c:\Projects\hackathon-MAIN-alkademi\backend\app\telegram\schemas.py` — strict Telegram update, enrollment, binding, and admin response models; reject oversized messages and malformed updates.
- `c:\Projects\hackathon-MAIN-alkademi\backend\app\telegram\security.py` — constant-time webhook-secret comparison, code hashing, single-use code generation/verification, and redacted audit helpers. Do not log bot tokens, enrollment secrets, or full Telegram message text.
- `c:\Projects\hackathon-MAIN-alkademi\backend\app\telegram\store.py` — persistence boundary for Telegram bindings, enrollment codes, processed update IDs, and revocation. Reuse the repository's existing database/session conventions rather than adding an ORM or second auth system; store actor/tenant/scope foreign keys where the verified identity model supports them.
- `c:\Projects\hackathon-MAIN-alkademi\backend\app\telegram\transport.py` — minimal async Telegram Bot API client for `sendMessage` and webhook setup, with timeout handling and no unbounded retries.
- `c:\Projects\hackathon-MAIN-alkademi\backend\app\api\v1\telegram.py` — webhook route and admin enrollment/revocation routes.
- `c:\Projects\hackathon-MAIN-alkademi\backend\tests\test_telegram_copilot.py` — focused regression tests for webhook authentication, enrollment, role derivation, idempotency, Telegram API failure, and read-only behavior.
- `c:\Projects\hackathon-MAIN-alkademi\backend\migrations\013_telegram_copilot_bindings.sql` — proposed next additive migration, only if the migration owner confirms 013 is still available; otherwise use the next authoritative number. It must not rewrite 001–012.

## Signatures and contracts

- `POST /api/v1/telegram/webhook` — accepts a Telegram `Update`; requires the exact configured `X-Telegram-Bot-Api-Secret-Token`; returns a fast success response after safely claiming the update. Invalid secret returns 401/403 without invoking Copilot.
- `POST /api/v1/telegram/admin/enrollment-codes` — admin-authenticated request containing `role`, optional tenant/scope, and expiry; returns the one-time code once. The raw code is never persisted or logged.
- `POST /api/v1/telegram/admin/bindings/{telegram_chat_id}/revoke` — admin-authenticated revocation; subsequent messages receive a generic authorization response.
- Internal adapter function: `handle_telegram_update(request: Request, update: TelegramUpdate) -> TelegramWebhookResponse`.
- Internal binding function: `resolve_active_telegram_binding(chat_id: str) -> TelegramBinding | None`.
- Internal enrollment function: `consume_enrollment_code(code: str, chat_id: str) -> TelegramBinding`.
- Internal transport function: `send_message(chat_id: str, text: str) -> None`.
- Copilot invocation must pass `ChatTurnRequest(message=<Telegram text>, history=<bounded Telegram conversation history or None>, roles=<server-derived binding roles>, stream=False)` and must not copy Telegram fields into `roles`.
- The binding must also provide the trusted `actor_id`, `tenant_id`, and legal-owner/beneficiary scope required by the downstream read tools. If the Copilot executor cannot consume this context today, the first implementation must be role-filtered/demo-only and must not claim production client isolation.

## Behavioral requirements

- `/start <code>` is the only enrollment command in the first release. It consumes a valid code once, binds the actual Telegram `chat.id`, and does not trust username/display name as identity.
- Unbound users receive instructions to contact an administrator; the bot must not reveal whether a supplied code exists, is expired, or belongs to another account.
- Expired, already-consumed, revoked, malformed, or over-attempted codes are rejected without changing bindings.
- A binding is persistent until an admin revokes it. Re-enrollment for an already-bound chat must require explicit admin revocation or a separate controlled replacement operation; do not silently change roles.
- Admin-generated codes must be high-entropy, short-lived, single-use, attempt-limited, and stored only as a salted/hashed verifier.
- Telegram user input is bounded and treated as untrusted text. HTML/Markdown output must be escaped or sent as plain text on formatting failure.
- Telegram API timeouts/429/5xx must not roll back enrollment or Copilot processing; record a bounded failure and return a webhook response that allows safe retry behavior. Duplicate `update_id` must not cause duplicate inference or duplicate outbound replies.
- The Telegram adapter must not accept caller-provided `X-Roles`, `Authorization`, tenant headers, or body roles. It supplies only the server-resolved binding context.
- Copilot remains read-only. No Telegram command may approve payroll, record payments, mutate stock, or execute an action shortcut.
- Production startup must fail clearly if Telegram is enabled without a bot token, webhook secret, or required persistence configuration. Local development may keep the feature disabled by default.

## Implementation phases

### Phase 0 — Drift and authority preflight (mandatory immediately before implementation)

- Re-read `AGENTS.md`, the OpenSpec change artifacts, and the target files from the current checkout.
- Run `git status --short` and identify overlapping edits in `backend/app/api/v1/__init__.py`, `backend/app/api/v1/copilot.py`, `backend/app/core/auth.py`, `backend/app/main.py`, and migration files.
- Compare the current OpenAPI route inventory and migration inventory with this plan.
- If any target has changed materially since this artifact was written, rebase the plan against the current code and record the changed assumptions in an implementation artifact. Never discard or revert unrelated local work.

Stop condition: `BLOCKED: working-tree drift changes a target contract | evidence: git diff -- <target> | question: which current implementation is authoritative?`.

### Phase 1 — Contract and security seam

- Harden the OpenSpec requirements and define the exact update/binding schemas.
- Refactor the Copilot execution seam only as needed to accept trusted server-derived context without changing browser behavior.
- Integrate with the existing verified admin/auth dependency. Do not use `get_current_auth_context` for this by assumption: its current allowed roles are only `Owner` and `FinancePayroll`, and it derives context from JWT claims rather than proving general membership/grants [code: `backend/app/core/auth.py`#L27-L169].
- Add or reuse a server-side identity resolver that can map the enrolled binding to an active actor and verified membership/scope. A `telegram_bindings.roles` text array without actor/scope validation is not implementation-complete.

Stop condition: if the root admin/auth boundary or actor-to-tenant membership cannot be proven from code, return `BLOCKED: admin or scope authority is not runtime-verified | evidence: current auth dependency and migration inventory | question: which existing identity/membership implementation is authoritative?`.

### Phase 2 — Persistence and enrollment

- Add the additive migration and store methods for bindings, hashed enrollment codes, processed update IDs, revocation, unique constraints, actor identity, tenant scope, and audit correlation. Apply it only through the repository's authoritative migration procedure.
- Add admin routes and focused tests for code lifecycle and persistent role assignment.

Stop condition: if the repository migration runner, current migration number, or table ownership differs from this brief, return `BLOCKED: migration source of truth differs | evidence: repository migration inventory and migration runner | question: which migration procedure and next number are authoritative?`.

### Phase 3 — Webhook and Copilot adapter

- Add secret validation, Telegram update parsing, enrollment handling, active-binding lookup, duplicate update claiming, bounded history, Copilot invocation, and safe reply formatting.
- Pass a server-created auth context to tool execution. Do not merely set `body.roles`; that would filter the prompt but would not establish tenant, actor, legal-owner, or beneficiary authorization for downstream reads.
- Add the Telegram transport with bounded timeout/retry behavior.

Stop condition: if the existing Copilot provider requires a network path or request context that cannot be safely reused in-process, return `BLOCKED: Copilot seam cannot be reused safely | evidence: provider/executor contract | question: approve a narrow internal HTTP adapter or keep webhook disabled?`.

### Phase 4 — Operational setup and verification

- Document BotFather setup, secret injection, webhook registration, HTTPS requirement, local testing strategy, admin enrollment, revocation, and rollback.
- Verify with unit/API tests and an interactive browser/API smoke path where applicable. Do not enable the disabled GitHub Actions Playwright workflow [code: `AGENTS.md`#Browser Verification Default].

## Acceptance criteria

- **AC-1:** A valid Telegram webhook update from a bound chat reaches the same Copilot inference/tool-filtering path as `POST /api/v1/copilot/chat`.
- **AC-2:** The role used by the Telegram request is exactly the active server-side binding role; Telegram input cannot elevate it.
- **AC-2a:** The Telegram binding resolves to an active actor and verified tenant/scope grant; role filtering alone is not accepted as proof of client isolation.
- **AC-3:** An admin can create a one-time enrollment code, a Telegram chat can consume it once, and the resulting binding survives process restart when persistence is enabled.
- **AC-4:** An admin can revoke a binding; revoked chats cannot query Copilot.
- **AC-5:** Invalid webhook secrets, malformed updates, unbound chats, expired codes, and duplicate updates are handled deterministically without Copilot invocation or data leakage.
- **AC-6:** Telegram cannot perform operational mutations; mutation intent remains a non-executable response/shortcut.
- **AC-7:** Telegram API failures do not roll back core data or create unbounded retries.
- **AC-8:** Tests cover role isolation for at least Owner, worker/production, stakeholder, and client-facing roles represented in the existing tool catalog [code: `backend/app/copilot/registry.py`#L49-L69].

## Non-goals

- WhatsApp integration.
- Telegram outbound event notifications or payroll alert subscriptions; those belong to the existing outbound messaging change.
- Telegram media, file uploads, group-chat authorization, multi-user shared identities, or voice messages.
- Autonomous writes, approvals, payments, stock changes, or execution of action shortcuts.
- Permanent role passwords shared by a whole role.
- Replacing the repository's existing web/admin authentication system.

## Verification commands

0. **Single-Command Automated Gate (Pre- and Post-Implementation):**
   `python scripts/verify_telegram_copilot_gate.py`
   *(Executes workspace hygiene, target-file & compilation checks, OpenAPI contract checks, `backend/tests/test_telegram_copilot.py` with in-process `FakeTelegramAPIServer` mocking `api.telegram.org`, and `backend/tests/test_copilot_api.py` regression checks).*
1. `python -m pytest -q backend/tests/test_telegram_copilot.py`
2. `python -m compileall -q backend/app/telegram backend/app/api/v1/telegram.py backend/app/api/v1/copilot.py`
3. `python -c "from backend.app.main import app; paths=app.openapi()['paths']; assert '/api/v1/telegram/webhook' in paths; assert '/api/v1/copilot/chat' in paths; print('telegram contract: PASS')"`
4. Run the repository workspace hygiene check: `python scripts/check_workspace_hygiene.py`.
5. Manual/local smoke: configure a test bot and webhook secret, send `/start <single-use-code>` then a read-only question, confirm a reply; revoke the binding and confirm subsequent requests are rejected. Evidence must state whether it used interactive browser/API tooling, automated tests, both, or neither.
6. Before implementation begins, save a drift record containing `git status --short`, the current commit, target-file hashes or diff summaries, and the final migration number. Re-run this comparison before handoff.

## Risks and mitigations

- **Permanent account compromise:** persistent binding is convenient but long-lived; mitigate with explicit admin revocation, audit logs, and no role self-selection.
- **Wrong scope despite correct role:** role alone may not encode tenant/client scope; derive tenant/actor/scope from the same server-side identity model used by protected APIs before claiming client isolation.
- **Telegram retries:** claim `update_id` transactionally before inference and store reply status to prevent duplicate processing.
- **Current Copilot trust model:** browser route currently accepts caller-supplied roles; preserve compatibility for the prototype but ensure the Telegram route never uses that untrusted path.
- **Missing general runtime identity boundary:** the current root auth code is not proof of general actor membership/scope authorization; block production Telegram access until the binding-to-actor/scope path is implemented and tested.
- **Prototype persistence ceiling:** if only in-memory storage is available in the selected runtime, explicitly mark Telegram persistence as development-only and block production enablement rather than silently losing role bindings on restart.

## Defaults I chose

- Webhook delivery is the default because deployment is the intended use; long polling is not included in the first release [default].
- One Telegram private chat maps to one binding; group chats are rejected in the first release [default].
- Enrollment codes expire after a short configurable period, are single-use, and are hashed at rest [default].
- Plain-text reply fallback is preferred over risking malformed Markdown/HTML [default].
- The bot is disabled by default in local development until explicit configuration is supplied [default].

## Open questions deliberately deferred to implementation discovery

- The root backend's authoritative admin-authentication dependency must be selected from the current runtime, because the currently verified root helpers are ledger/stock-specific rather than a general admin boundary [code: `backend/app/core/auth.py`#L145-L182].
- Tenant/client scope binding cannot be inferred from a Telegram role string alone; implementation must use a verified actor/scope source or explicitly narrow the first release to role-filtered demo data [unverified].
- Migration 013 is a proposed number, not a guaranteed number; the implementation agent must verify it immediately before authoring DDL [unverified].
- The current checkout is actively changing; all line references, target file assumptions, and route contracts must be revalidated immediately before implementation [code: `git status --short` observed 2026-10-16].
