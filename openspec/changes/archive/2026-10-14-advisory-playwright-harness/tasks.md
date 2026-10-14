## 1. Package and Harness Configuration

- [x] 1.1 Add `@playwright/test` as a development dependency under `prototypes/sampling-spec-rnd/frontend/`, generate and commit `package-lock.json`, and add a `test:e2e` script.
- [x] 1.2 Add `prototypes/sampling-spec-rnd/frontend/playwright.config.ts` with one Chromium project, the 3009 frontend base URL, bounded timeout, deterministic workers, and failure diagnostics.
- [x] 1.3 Configure service startup for the FastAPI backend on port 8009 and Vite frontend on port 3009 without silently changing ports; return an actionable failure if either service cannot start.
- [x] 1.4 Add `prototypes/sampling-spec-rnd/frontend/tests/smoke.spec.ts` using accessible selectors to verify the dashboard heading and `Connected` status only; do not click Spec Version or perform writes.
- [x] 1.5 Add anchored ignore rules for Playwright output directories inside the prototype frontend.

## 2. Advisory CI Integration

- [x] 2.1 Create `.github/workflows/prototype-e2e.yml` with the exact revision-2 trigger, permission, action, timeout and advisory contracts in design.md; leave existing workflows unchanged.
- [x] 2.2 Install the required Chromium browser and start the backend/frontend services deterministically before running `npm run test:e2e`.
- [x] 2.3 Set the job to `continue-on-error: true`, retain report/trace/screenshot artifacts on failure, and leave `.github/workflows/ci.yml` and existing quality jobs unchanged.
- [x] 2.4 Verify the workflow cannot report a false green when startup fails: service readiness must be checked before the Playwright command and the Playwright command must preserve its exit evidence even though the job is advisory. (Locally tested occupied-port failure; remote workflow not executed.)

## 3. Agent and Pull Request Guidance

- [x] 3.1 Add a concise `AGENTS.md` rule preferring an available interactive browser tool for pre-commit user-visible web verification; define “interactive browser tool” generically and mention `open_browser_page` only as this environment's example.
- [x] 3.2 Define the fallback: when no interactive browser tool is available, run the automated Playwright smoke; when neither is available, mark browser verification unverified rather than substituting API-only evidence.
- [x] 3.3 Add a pull-request checklist item requiring browser evidence, naming whether it came from an interactive browser tool or automated Playwright, and recording unavailable checks honestly.

## 4. Verification and Review

- [x] 4.1 From `prototypes/sampling-spec-rnd/frontend`, run `npm ci`, install Chromium, and run `npm run test:e2e` with the backend/frontend service prerequisites. (Smoke exited 1 on known missing import; see implementation report.)
- [x] 4.2 Run `npm run type-check`, `npm run build`, and existing lint checks; confirm test files and Playwright config do not enter the application TypeScript compilation unexpectedly. (Existing app checks fail; see implementation report.)
- [x] 4.3 Run `python scripts/check_workspace_hygiene.py`, inspect `git diff` top-to-bottom, and verify no application behavior or blocking workflow changed.
- [x] 4.4 Perform an interactive browser smoke when an environment tool is available; otherwise record the automated-only fallback and its exact command in the PR evidence. (Interactive blank page and automated failure recorded.)
- [x] 4.5 If any port, selector, startup contract, or existing workflow differs from this brief, stop with `BLOCKED: <difference> | <file and lines> | <question>` rather than widening scope. (No newly discovered divergence.)

## 5. Review closure before implementation handoff

- [x] 5.1 Resolve the exact compatible Playwright version and backend command/address contract using current metadata and source evidence; freeze commands and absolute target paths in the handoff.
- [x] 5.2 Apply design revision 2 to all harness configuration and policy tasks; do not repair or conceal the missing eager page import. User selected harness-only with honest existing-failure evidence.
- [x] 5.3 Re-review the revised plan against reviews/plan-review-001.md. Preserve the original NEEDS_REVISION verdict until a new review explicitly closes the applicable findings. (Implementation review `implementation-review-001.md` approved the revised scope; original review remains unchanged.)
