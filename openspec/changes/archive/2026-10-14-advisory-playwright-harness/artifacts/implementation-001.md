## Implementation Report: Advisory browser harness

**Status:** PARTIAL — implementation present; independent review and remote CI not yet complete.

**Objective:** Add one read-only Chromium smoke, a non-blocking CI job, and generic browser-tool-first pre-commit guidance. Preserve the existing missing application import and its honest failure.

**Changes Made:**
- `prototypes/sampling-spec-rnd/frontend/package.json`, `package-lock.json`: exact `@playwright/test` 1.63.0 pin, `test:e2e` script and reproducible dependency tree.
- `prototypes/sampling-spec-rnd/frontend/playwright.config.ts`, `tests/smoke.spec.ts`, `.gitignore`: one Chromium smoke, two managed local services on strict ports 8009/3009, bounded timeouts, failure screenshot/HTML report, ignored outputs.
- `.github/workflows/prototype-e2e.yml`: separate pull-request workflow, read-only permissions, Node 20/Python 3.11, browser install, advisory job-level `continue-on-error`, seven-day diagnostics.
- `AGENTS.md`, `.github/pull_request_template.md`, prototype frontend `README.md`: portable interactive browser preference, automated fallback, evidence checklist and runnable setup.

**Verification:**
- `npm ci` and `npx playwright install chromium` (prior session): PASS; Chromium and dependencies present locally.
- `npm run test:e2e -- --list`: PASS; exactly one Chromium test.
- `npm run test:e2e`: FAIL as expected (exit 1); Playwright started backend and browser; Vite reported missing `/src/pages/SpecVersionPage` imported by `src/App.tsx`; heading assertion failed and produced screenshot/HTML report. Dashboard success and backend UI connection are NOT verified.
- Occupied-port negative test: PASS; a separate `python -m http.server 3009 --bind 127.0.0.1` occupied port 3009; Playwright exited 1 with explicit `already used` error and did not kill occupant; test process then stopped. No listener remained on ports 3009/8009 after cleanup.
- Interactive `open_browser_page` at `http://127.0.0.1:3009/`, `read_page`, screenshot: blank viewport; Vite log identified same missing import. Interactive dashboard success NOT verified.
- `npm run type-check`: FAIL (exit 2), pre-existing missing import `src/App.tsx:8`.
- `npm run build`: FAIL (exit 2), same missing import.
- `npm run lint`: FAIL (exit 1), 12 `no-explicit-any` errors in existing `src/hooks/usePerformance.ts`, `src/services/api.ts`, `src/types/index.ts`.
- `python scripts/check_workspace_hygiene.py`: PASS.
- `openspec validate advisory-playwright-harness`: PASS.
- `git diff --check`: PASS.
- Remote GitHub workflow execution, branch-rule verification, successful UI connection: NOT RUN / NOT VERIFIED.

**Acceptance Criteria:**
- [x] One read-only test, deterministic startup, honest failure diagnostics and non-blocking separate CI configuration.
- [x] Interactive browser tool preference and automated fallback guidance.
- [ ] Successful dashboard render and Connected status — blocked by explicitly excluded application defect.
- [ ] Independent review verdict and actual remote CI execution — pending.

**Decisions Made:** Keep existing application defect visible; no skip, stub, mock, xfail, or unrelated app repair. Backend Python provided from prototype backend `.venv` on local PATH; CI uses setup-python.

**Failures and Recovery:** Two Assistant dispatches returned provider errors after partial files were written; parent inspected and finished the on-disk work. Initial README virtualenv instructions lacked activation; corrected before smoke. The first post-restart test command returned expected nonzero application checks, not a harness setup failure.

**Risks / Notes:** CI job behavior and merge rules not observed remotely. The smoke cannot establish successful dashboard-to-backend behavior while the eager import is missing. Startup failures may have logs but no screenshot. Local npm audit reported 16 existing findings during install; dependency audit remediation is outside this change.

**Files Modified:** `AGENTS.md`, `.github/pull_request_template.md`, `.github/workflows/prototype-e2e.yml`, `prototypes/sampling-spec-rnd/frontend/{.gitignore,README.md,package.json,package-lock.json,playwright.config.ts,tests/smoke.spec.ts}`, OpenSpec change artifacts.
