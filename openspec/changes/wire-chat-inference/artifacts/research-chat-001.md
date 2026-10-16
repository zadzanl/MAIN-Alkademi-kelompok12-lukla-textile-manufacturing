# Chat-to-inference research

Task record: initial  
Repository: `c:\Projects\hackathon-MAIN-alkademi`  
Scope: `prototypes/sampling-spec-rnd` and related backend/config  
Secrets: values were not printed; environment values were redacted during inspection.

## Verified findings

### 1. Sampling frontend submit flow

- `prototypes/sampling-spec-rnd/frontend/src/pages/CopilotView.tsx:63-77` defines `handleSend`. It trims the text, appends a local user message, clears the input, and sets loading state.
- `prototypes/sampling-spec-rnd/frontend/src/pages/CopilotView.tsx:78-105` tries three hard-coded URLs in order:
  - `/api/v1/copilot/chat`
  - `http://localhost:8000/api/v1/copilot/chat`
  - `http://127.0.0.1:8000/api/v1/copilot/chat`
- The request at `CopilotView.tsx:84-91` sends `POST`, JSON content type, `X-Roles`, `X-Tenant-Id: tenant-001`, and body `{ message: textToSend, roles: [selectedRole] }`. It does not send the existing message history, despite the backend request contract supporting it.
- `CopilotView.tsx:94-107` maps a successful JSON response from `reply` (fallback `message`), `shortcuts`, and `tools_used` into the assistant message.
- `CopilotView.tsx:110-171` falls back after all candidates fail. The fallback waits 450 ms and generates hard-coded operational claims/shortcuts based on keywords. Therefore the UI can appear to answer even when no inference endpoint was reached.
- `CopilotView.tsx:224-225` labels the UI `Live Gateway`, but this label is static and is not tied to a successful connection.

### 2. Sampling frontend configuration

- `prototypes/sampling-spec-rnd/frontend/src/services/config.ts:18-29` defines `VITE_API_URL` for the sampling API, `VITE_AUTH_URL`, ledger settings, and mock/live mode. No chat endpoint constant is defined or imported by `CopilotView.tsx`.
- `prototypes/sampling-spec-rnd/frontend/.env.example:1-14` documents `VITE_API_URL=/api/sampling-spec-rnd`, `VITE_AUTH_URL=/api/auth`, and ledger variables. It contains no `VITE_COPILOT_*` or inference URL setting.
- `prototypes/sampling-spec-rnd/frontend/playwright.config.ts:37-53` starts the sampling backend on `127.0.0.1:8009` and the frontend on `127.0.0.1:3009`; its frontend test environment forces `VITE_API_URL=/api/sampling-spec-rnd`. This does not configure the root chat backend on port 8000.

### 3. Actual chat endpoint and request handling

- `backend/app/api/v1/__init__.py:5-9` mounts the copilot router under `/api/v1`.
- `backend/app/api/v1/copilot.py:15` defines the router prefix `/copilot`; `:33-43` exposes `POST /api/v1/copilot/chat` with response model `ChatTurnResponse`.
- `backend/app/api/v1/copilot.py:49-60` rejects requests when `AI_COPILOT_ENABLED` is false, derives request/authorization metadata, and reads roles from `X-Roles`, JWT claims, or `body.roles`. The frontend's `X-Roles` and `roles` fields are accepted; `X-Tenant-Id` is not used in this handler.
- `backend/app/api/v1/copilot.py:65-92` filters read-only tools, detects shortcuts, selects the configured provider, and calls `provider.chat_turn(message=body.message, history=body.history, tools=available_tools)`.
- `backend/app/api/v1/copilot.py:95-158` optionally executes provider tool calls through the read-only executor, then performs a second provider turn with tool results. Tool execution is GET-only through the normal catalog/barrier.

### 4. Request and response shape

- `backend/app/copilot/schemas.py:35-42` defines `ChatTurnRequest`: required `message` (1-4000 chars), optional `history` (maximum 10 `ChatMessage` items), optional `roles`, and `stream` (default false).
- `backend/app/copilot/schemas.py:17-33` defines each history message as `{id, sender: "user"|"assistant", text, shortcuts?, timestamp}`.
- `backend/app/copilot/schemas.py:45-53` defines the response as `{reply: string, shortcuts: ActionShortcut[], tools_used: string[], usage: {prompt_tokens, completion_tokens, total_tokens}}`.
- `CopilotView.tsx:100-104` consumes the relevant response fields, but does not display or retain `usage` and does not append the sent turn to a request history payload.

### 5. Inference provider/server path

- `backend/app/copilot/config.py:5-25` reads:
  - `AI_COPILOT_ENABLED` (default true)
  - `COPILOT_DEFAULT_PROVIDER`, falling back to `COPILOT_LLM_PROVIDER` then `mock`
  - `COPILOT_TIMEOUT_SECONDS` (default 30)
  - `COPILOT_MODEL_NAME`
  - `COPILOT_API_KEY`, falling back to `OPENROUTER_API_KEY`
  - `COPILOT_BASE_URL` (default `https://openrouter.ai/api/v1`)
  - `INTERNAL_API_BASE_URL` (default `http://localhost:8000/api/v1`)
- `backend/app/api/v1/copilot.py:91` obtains the provider via `get_llm_provider(...)`.
- `backend/app/copilot/provider.py:171-180` configures the OpenAI-compatible provider from `COPILOT_BASE_URL`, `COPILOT_API_KEY`, and `COPILOT_MODEL_NAME`.
- `backend/app/copilot/provider.py:219-248` sends `POST {COPILOT_BASE_URL}/chat/completions` with `model`, `messages`, `temperature`, and `max_tokens`; tools are added when available. It adds `Authorization: Bearer ...` only when a key is configured.
- `backend/app/copilot/provider.py:250-307` parses OpenAI-compatible `choices[0].message`, usage counters, and optional function tool calls. Provider errors become `ProblemException` responses rather than frontend fallback data.
- `backend/app/copilot/provider.py:310-355` uses Ollama, OpenRouter, OpenAI-compatible, or mock implementations. Unknown/default provider values resolve to `MockLLMProvider`; the mock path returns deterministic text and never calls an inference endpoint.

### 6. Environment/config observations

- A root `c:\Projects\hackathon-MAIN-alkademi\.env` exists. Safe key-only inspection found `COPILOT_DEFAULT_PROVIDER`, `OPENROUTER_API_KEY`, and `COPILOT_MODEL_NAME`; all values were withheld. The file also contains a uvicorn command line after those assignments, which may be shell history/configuration rather than a valid dotenv assignment and should be confirmed by the implementer.
- `prototypes/sampling-spec-rnd/backend/.env.example:1-29` documents sampling backend, auth, database, CORS, and SMTP settings only; it does not document the root copilot provider variables.
- `backend/app/copilot/config.py` reads process environment directly. In the inspected code, no `load_dotenv()` call was found in the root `backend/app` copilot configuration path. Whether the process runner loads the root `.env` externally is therefore unknown.

## Commands run

Read-only commands/tools only:

1. Semantic repository searches for:
   - chat component submit flow and response handling
   - inference endpoint/server route and response shape
   - environment variables/dotenv/API URL configuration
2. File reads for the exact files and ranges cited above.
3. PowerShell safe inspection:
   - `Get-ChildItem -Force -Recurse -File -Include '.env','.env.*' ...` to locate env files.
   - `Get-ChildItem ... | Select-String -Pattern 'AI_COPILOT_ENABLED|...|copilot/chat'` to locate config/endpoint references.
   - `Get-Content c:\Projects\hackathon-MAIN-alkademi\.env | ...` with every value replaced by `***REDACTED***`.

No source files were edited. No build, test, server start, or browser verification was run.

## Unknowns / risks

- It is not verified whether the running frontend's Vite proxy maps `/api/v1` to the root backend on port 8000. The documented sampling proxy path is `/api/sampling-spec-rnd`, and the Playwright config only starts port 8009.
- It is not verified whether the root `.env` is loaded into the process environment when starting `backend.app.main:app`; the copilot config itself does not load dotenv.
- The exact current value of `COPILOT_DEFAULT_PROVIDER` and whether the API key is valid were intentionally not inspected.
- The frontend sends a tenant header, but the copilot handler shown does not consume it; tenant authorization may be implemented elsewhere or may be absent for this path.
- The frontend's `ChatMessage` shape (`sender`/`text`) differs from other historical copilot schema variants in the repository; the target root backend uses the shape documented above.

## Recommendation

Wire `CopilotView` to one configured chat base URL rather than probing three hard-coded candidates, preferably by adding a non-secret Vite public variable such as `VITE_COPILOT_API_URL` (or deriving a documented same-origin `/api/v1/copilot/chat` proxy). Build the request with the backend's exact `{message, history, roles, stream:false}` shape and retain/map the returned `reply`, `shortcuts`, and `tools_used`. Remove or explicitly gate the fabricated fallback so endpoint/provider failures remain visible as errors instead of presenting invented operational data. Separately, ensure the process launching `backend.app.main:app` loads the root `.env` (or exports the variables) and select a non-`mock` provider when real inference is intended; preserve the API key as a secret.
