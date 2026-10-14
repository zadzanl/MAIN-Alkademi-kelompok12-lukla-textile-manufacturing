## Why

The repository has frontend lint/type checks and backend smoke coverage, but no executable browser E2E harness. A small Chromium smoke test will provide visible integration evidence while remaining advisory and unable to block merges.

Agents also need a portable rule for browser verification: use an available interactive browser tool for manual inspection when present; otherwise use the automated Playwright smoke suite and report unavailable interactive verification explicitly.

## What Changes

- Add a minimal Playwright test harness inside `prototypes/sampling-spec-rnd/frontend/`.
- Add one read-only browser smoke covering dashboard load and the backend connection indicator.
- Add deterministic frontend/backend startup configuration for local and CI execution.
- Add an advisory CI job with `continue-on-error: true`, failure artifacts, and no merge-blocking status.
- Add generated Playwright report directories to the prototype frontend ignore file.
- Document browser verification precedence and fallback behavior in `AGENTS.md`.
- Add a pull-request checklist item requiring browser evidence or an explicit automated-only fallback note.

## Capabilities

### New Capabilities
- `advisory-browser-smoke`: Provides a minimal, read-only Playwright browser smoke test and advisory execution path.
- `agent-browser-verification`: Defines tool-agnostic browser verification defaults and the automated Playwright fallback.

### Modified Capabilities
- None.

## Impact

Affected areas are the prototype frontend package and test directory, the prototype advisory workflow, the prototype frontend ignore file, `AGENTS.md`, and `.github/pull_request_template.md`. The application API, business logic, existing quality jobs, and blocking CI workflows remain unchanged.
