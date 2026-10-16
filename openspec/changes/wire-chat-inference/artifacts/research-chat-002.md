# Research: sampling prototype chat-to-inference wiring

- **Task record:** initial
- **Scope:** repository inspection only; no source files edited; no secrets printed.
- **Repository:** `C:\Projects\hackathon-MAIN-alkademi`
- **Target prototype:** `prototypes/sampling-spec-rnd/frontend`
- **Status labels:** `Verified` means directly observed in the cited file; `Inferred` means a consequence of those observations; `Unknown` means not established by this inspection.

## Executive finding

**Verified:** `prototypes/sampling-spec-rnd/frontend/src/pages/CopilotView.tsx:24-29,80-101` already sends a POST when a chat message is submitted, but it tries hard-coded `/api/v1/copilot/chat` and port-8000 URLs rather than reading the prototype's existing Vite configuration. If all candidates fail, it generates a local fabricated answer at `CopilotView.tsx:105-184`, so the UI can look successful without inference.

**Verified:** The inference contract implemented in the repository's root backend is `POST /api/v1/copilot/chat`, registered by `backend/app/api/v1/copilot.py:30-45` through the API router. The sampling prototype backend at `prototypes/sampling-spec-rnd/backend/src/api/routes.py:34-46` registers `/api/sampling-spec-rnd/health` and sampling/workflow routes, but no copilot/chat route was found there. Therefore the Vite proxy on port 3009 to the sampling backend on port 8009 cannot satisfy `/api/v1/copilot/chat` without an additional backend/proxy deployment decision.

**Verified:** The prototype's existing Vite env configuration is intended for sampling/auth/ledger services, not inference. `frontend/src/services/config.ts:16-29` reads `VITE_API_URL`, `VITE_AUTH_URL`, `VITE_LEDGER_API_URL`, `VITE_LEDGER_TOKEN`, and `VITE_LEDGER_MODE`; `frontend/.env.example:1-15` documents the first, auth, and ledger values. `frontend/vite.config.ts:19-27` proxies `/api` to `http://localhost:8009`. Vite exposes only variables prefixed with `VITE_` to client code; this project follows that convention through `import.meta.env`.

## Files and relevant snippets

### 1. Chat UI and current request behavior

- **`prototypes/sampling-spec-rnd/frontend/src/pages/CopilotView.tsx:1-21`**
  - Defines the UI-local `ChatMessage` shape: `sender` is `user|assistant`, `text`, optional shortcuts/tools, and a display timestamp.
  - No import from `src/services/config.ts`, `http.ts`, or `authSession.ts` is present in the inspected file.

- **`CopilotView.tsx:24-29`**
  - Defines `CANDIDATE_ENDPOINTS` as:
    - `/api/v1/copilot/chat`
    - `http://localhost:8000/api/v1/copilot/chat`
    - `http://127.0.0.1:8000/api/v1/copilot/chat`
  - These are not derived from `.env` or the sampling service base.

- **`CopilotView.tsx:65-103`**
  - On submit, adds the user message to local state, clears the input, and sets loading.
  - Sends `POST` with `Content-Type: application/json`, `X-Roles: selectedRole`, and `X-Tenant-Id: tenant-001`.
  - Current JSON body is `{ message: textToSend, roles: [selectedRole] }`.
  - On any successful HTTP response, reads JSON and maps `reply` (or fallback `message`) to the assistant message; maps `shortcuts` and `tools_used`.
  - It does not send `history`, `stream`, `sessionId`, or the current portal bearer token.
  - Non-2xx responses are ignored and the loop tries the next candidate; response bodies are not surfaced.

- **`CopilotView.tsx:105-184`**
  - If no endpoint succeeds, waits 450 ms and creates deterministic hard-coded answers based on keywords such as stock, cutting, sewing, QC, and sample.
  - This is a UX fallback, not inference. It can conceal endpoint/configuration failures.

- **`CopilotView.tsx:188-195` and later render code**
  - Shortcut navigation is local UI navigation; it does not execute backend writes. The component is designed around read-only assistant results and deep links.

### 2. Existing frontend API/configuration patterns

- **`prototypes/sampling-spec-rnd/frontend/src/services/config.ts:1-31`**
  - Uses a guarded `import.meta.env` read so service modules remain importable outside Vite.
  - `SAMPLING_BASE = env.VITE_API_URL || 'http://localhost:8009/api/sampling-spec-rnd'`.
  - `AUTH_BASE = env.VITE_AUTH_URL || 'http://localhost:8009/api/auth'`.
  - Ledger values use `VITE_LEDGER_API_URL`, `VITE_LEDGER_TOKEN`, and `VITE_LEDGER_MODE`.
  - No inference/copylit-specific base URL or token constant exists.

- **`frontend/src/vite-env.d.ts:3-12`**
  - Declares only `VITE_API_URL`, `VITE_LEDGER_MODE`, `VITE_LEDGER_API_URL`, and `VITE_LEDGER_TOKEN` in `ImportMetaEnv`.
  - Any new public Vite variable would need a matching declaration for TypeScript consistency.

- **`frontend/.env.example:1-15`**
  - Documents `VITE_API_URL=/api/sampling-spec-rnd`, `VITE_APP_NAME`, `VITE_AUTH_URL=/api/auth`, and ledger mock/live settings.
  - It explicitly recommends relative paths through the Vite proxy for the sampling/auth APIs.
  - No inference variable is documented. The actual `.env` file was not printed; only `.env.example` was inspected.

- **`frontend/vite.config.ts:19-27`**
  - Dev server runs on port `3009`, strict port.
  - A single `/api` proxy targets `http://localhost:8009`.
  - Consequently, `/api/v1/copilot/chat` would be proxied to the sampling backend's port 8009 and currently has no matching route there.

- **`frontend/src/services/http.ts:38-114`**
  - Existing shared transport uses `SAMPLING_BASE`, JSON bodies, a 10-second abort timeout, normalized FastAPI/RFC-7807 error handling, and optional bearer token support.
  - Non-GET requests automatically receive an `Idempotency-Key`; this is appropriate for domain writes but is not necessarily needed for a chat turn.
  - This transport does not currently provide an inference-specific client.

- **`frontend/src/services/api.ts:1-75`**
  - Sampling API functions consistently use the shared `http` client and typed `ApiResult` envelopes.
  - No chat/inference function was found in the inspected service module.

### 3. Auth/session behavior relevant to chat

- **`frontend/src/services/authSession.ts:1-77`**
  - Exposes `getToken()`, `getActor()`, and `getSession()`.
  - The opaque token is held in memory and mirrored to `sessionStorage` under `portal-auth-session`.
  - The chat component does not currently import or use `getToken()`.
  - The existing prototype auth token may not be accepted by the root copilot backend; compatibility is **Unknown**.

- **`frontend/tests/smoke.spec.ts:7-29,32-67`**
  - Smoke tests inject a synthetic `portal-auth-session` into `sessionStorage` and verify auth/dashboard rendering, backend connection text, sidebar Copilot visibility, and Copilot navigation.
  - The synthetic token is a test value only; no live secret is exposed.

### 4. Implemented inference endpoint contract in the root backend

- **`backend/app/api/v1/copilot.py:30-45`**
  - Implements `POST /copilot/chat` on a router with prefix `/api/v1`, giving the effective endpoint `/api/v1/copilot/chat`.
  - The route returns `ChatTurnResponse` and accepts `ChatTurnRequest`.

- **`backend/app/copilot/schemas.py:29-68`**
  - `ChatTurnRequest`:
    - required `message: string`, minimum length 1, maximum length 4000;
    - optional `history: ChatMessage[]`, maximum 10 items;
    - optional `roles: string[]`;
    - `stream: boolean`, default false.
  - `ChatMessage` in the request history is `{ id?, sender: 'user'|'assistant', text, shortcuts?, timestamp? }`.
  - `ChatTurnResponse` is `{ reply: string, shortcuts: ActionShortcut[], tools_used: string[], usage: TokenUsage }`.
  - `TokenUsage` fields are snake_case: `prompt_tokens`, `completion_tokens`, `total_tokens`.
  - This response shape matches the current UI's `reply`, `shortcuts`, and `tools_used` reads.
  - The schema does **not** declare `session_id`; the frontend should not assume a session ID is returned by this implementation.

- **`backend/app/api/v1/copilot.py:48-83`**
  - The handler checks the `AI_COPILOT_ENABLED` setting and can return 503 when disabled.
  - Roles are resolved from `X-Roles`, then bearer JWT claims, then request `roles`, then default `Owner`.
  - The current frontend already supplies `X-Roles` and `roles`, but it does not supply `Authorization`.

- **`backend/app/api/v1/copilot.py:84-150`**
  - The handler filters read-only tools by role, detects mutation intent into action shortcuts, then calls the configured LLM provider.
  - Tool execution enforces read-only behavior; mutation intents are represented as shortcuts rather than autonomous writes.

- **`backend/app/main.py:11-12,247-248`**
  - The root service includes `api_router`, which is the service containing `/api/v1/copilot/chat`.
  - This is a different FastAPI application from `prototypes/sampling-spec-rnd/backend/src/main.py`.

### 5. Sampling prototype backend contract

- **`prototypes/sampling-spec-rnd/backend/src/main.py:6-46`**
  - Loads backend `.env` with `load_dotenv()`.
  - Runs the sampling FastAPI app with CORS for frontend ports 3009 and 8009.
  - Includes `create_api_router()` and auth routes.

- **`prototypes/sampling-spec-rnd/backend/src/api/routes.py:34-46`**
  - Creates router prefix `/api/sampling-spec-rnd`.
  - Registers `GET /health` and sampling/workflow/study/spec/sample-version routes.
  - No `/api/v1/copilot/chat` or inference route exists in this file or the inspected prototype backend route surface.

## Vite environment behavior and configuration conclusion

- **Verified from project usage:** browser configuration is read through `import.meta.env`, and project declarations only allow `VITE_*` values in `vite-env.d.ts`.
- **Verified from project files:** `.env.example` uses relative `VITE_API_URL`/`VITE_AUTH_URL` values so requests travel through the Vite `/api` proxy; the proxy target is fixed to port 8009.
- **Inferred:** an inference URL cannot safely be made to work by merely changing `VITE_API_URL`, because that variable is the sampling base and the sampling backend does not implement the copilot route. A separate inference base variable or a backend gateway/proxy route is needed, and its target must point at the root backend (or another service that implements the same contract).
- **Security risk:** any `VITE_*` value is bundled into browser JavaScript. A bearer/API secret must not be placed in a `VITE_*` variable. The existing `VITE_LEDGER_TOKEN` is already a client-exposed token pattern; do not copy it for a privileged inference provider key.

## Existing tests and verification gaps

- **Verified:** `frontend/package.json` provides `type-check`, `build`, `lint`, `test`, and `test:e2e` scripts.
- **Verified:** `frontend/tests/smoke.spec.ts` currently contains two browser smoke tests only; it does not submit a Copilot message, inspect the request URL/body/headers, mock or assert an inference response, or assert fallback/error behavior.
- **Verified:** `frontend/playwright.config.ts:37-56` starts the sampling backend on 8009 and Vite on 3009; the frontend web server override sets `VITE_API_URL=/api/sampling-spec-rnd`. It does not start the root inference backend.
- **Unknown:** whether a root backend service is running in the developer's current environment, whether its `AI_COPILOT_ENABLED` flag is enabled, and whether its configured provider credentials/model are valid. No server or test command was run for this research task.

## Recommended implementation shape (for the implementation agent)

1. Decide and document the deployment topology first: direct root-backend URL, a Vite proxy route to the root backend, or a route added to the sampling backend. Do not point the chat at the sampling base unless that backend is extended with the inference contract.
2. Add a non-secret, public base/path configuration using an appropriately named `VITE_*` variable only for the URL/path, not for provider/API credentials. Update `vite-env.d.ts` and `.env.example` together.
3. Replace the candidate loop with one configured request, or make fallback behavior visibly an error state rather than fabricated operational data. Silent fabricated data is the highest correctness risk.
4. Send the implemented request shape: at minimum `message` and `roles`; preferably bounded `history` converted to the backend's `sender/text` schema. Add the current portal bearer token only if the target service accepts the prototype auth token format.
5. Preserve the implemented response keys `reply`, `shortcuts`, and `tools_used`; handle non-2xx responses and malformed JSON explicitly.
6. Add a focused browser regression test that intercepts the configured inference request and asserts method, URL, JSON body, and assistant response. Keep the existing backend-startup smoke separate because its current webServer only starts port 8009.

## Risks and open questions

- **Endpoint topology risk (Verified/Inferred):** `/api/v1/copilot/chat` belongs to the root backend, while the prototype's Vite proxy points to the sampling backend. A relative URL currently reaches the wrong service.
- **Configuration collision risk (Verified):** repurposing `VITE_API_URL` for inference would break the documented sampling service base and existing service clients.
- **Secret exposure risk (Verified):** Vite client env variables are public bundle inputs; provider keys must remain server-side.
- **False-success risk (Verified):** the current hard-coded fallback produces plausible operational claims even when all network calls fail.
- **Auth compatibility risk (Unknown):** the prototype's session token and root backend JWT expectations are not proven compatible.
- **Contract version risk (Verified):** the root backend response has `tools_used` and snake_case usage fields; any alternative inference service may use a different response shape.
- **History/session semantics (Verified/Unknown):** the root schema accepts bounded history but has no session ID field; persistence across page reloads is not defined by this contract.

## Commands used (read-only)

- `Get-ChildItem -Path .\\prototypes\\sampling-spec-rnd -Recurse -File | Select-Object -ExpandProperty FullName` (file inventory; output was noisy because generated virtual-environment files are present).
- Semantic repository searches for chat submission, Vite env usage, inference schemas, and sampling tests.
- `Get-ChildItem ... -Filter '.env*'` (listed env-file paths only; no values printed).
- Targeted `Get-ChildItem ... | Select-String` over source/config/docs excluding `node_modules`, `.venv`, `dist`, and `build` for endpoint/env/auth references.
- Read-only file inspection of the paths cited above.

No source build, test, server, browser, install, or mutation command was run. No secret values were printed.

## Verification ideas after implementation

- **Static:** run `npm run type-check` and `npm run lint` in `prototypes/sampling-spec-rnd/frontend`.
- **Focused browser:** use Playwright route interception for the configured inference URL; submit a message; assert one POST, exact JSON keys, role/header behavior, and rendered `reply`.
- **Contract:** run a request against the actual root backend with a non-secret test token/configuration and verify 200 response fields; separately verify expected 503/4xx error rendering when the service is disabled or unreachable.
- **Topology:** run the prototype Playwright web servers and confirm the inference request reaches the intended service, not port 8009's sampling router.
- **Negative:** confirm no provider key appears in built assets, `.env.example`, request bodies, logs, or test fixtures.
