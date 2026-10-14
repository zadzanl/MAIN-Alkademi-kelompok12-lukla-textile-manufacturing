## Context

The working prototype is a React/Vite frontend at `prototypes/sampling-spec-rnd/frontend/` using port 3009 and proxying `/api` to the FastAPI service on port 8009. Its backend exposes `GET /api/sampling-spec-rnd/health`; the frontend renders a `Connected`/`Local Mode` status indicator. There is currently no Playwright dependency, config, browser spec, or browser CI job.

The harness is advisory by design. It must not mutate in-memory prototype state, require authentication, or alter the existing blocking CI pipeline.

## Goals / Non-Goals

**Goals:**

- Install `@playwright/test` in the prototype frontend and commit a deterministic npm lockfile.
- Configure one Chromium project, a stable `baseURL`, bounded timeouts, and failure diagnostics.
- Start the backend and frontend through Playwright or an equivalent CI-safe service lifecycle.
- Test only the dashboard smoke path: page loads, the expected heading is visible, and the health-backed connection indicator becomes `Connected`.
- Run the CI job as advisory with `continue-on-error: true` and upload report/trace artifacts when available.
- Establish a general policy: interactive browser tools are preferred for pre-commit inspection; automated Playwright is the fallback when no interactive browser tool is available.

**Non-Goals:**

- No write workflow, database fixture, authentication, visual regression, cross-browser matrix, mobile matrix, or performance budget.
- Do not repair the missing SpecVersionPage import in this change. It is eagerly imported, so avoiding its tab does not prevent a dashboard load failure. The harness must expose that existing defect rather than skip, mock, or soften the assertion.
- Do not modify application behavior, API contracts, `ci.yml`, or existing quality jobs.
- Do not claim an interactive browser review occurred when only Playwright ran.

## Decisions

1. **Use a real Chromium smoke rather than request-only tests.** The request is for Playwright E2E; a browser page load plus visible connection state proves the frontend-to-backend path. Request fixtures may be added later for API-only diagnostics but are not the primary acceptance test.
2. **Use one read-only test.** The backend stores workflow state in memory, so a read-only health path avoids cleanup and parallel-run collisions.
3. **Use the existing ports 3009/8009 as the initial source of truth.** The Vite proxy and FastAPI app use these ports. Any stale documentation or scripts are outside this change unless startup verification proves they prevent the harness from running.
4. **Keep the CI job separate or clearly isolated and advisory.** A failure must produce evidence without changing merge eligibility. Existing quality checks remain untouched.
5. **Use generic browser-tool language in governance docs.** The policy says “interactive browser tool” and “automated Playwright runner.” This environment's `open_browser_page` is an example of the former, not a hard-coded requirement for all agents.
6. **Fallback rule.** If an agent has no interactive browser tool, it runs the automated Playwright command and records that interactive verification was unavailable. If Playwright is also unavailable, the agent reports the browser check as unverified rather than substituting a generic HTTP request as equivalent evidence.

## Risks / Trade-offs

- [Browser installation increases CI time] → Install only Chromium, cache npm/Playwright assets where supported, and keep one test.
- [Advisory jobs can be ignored] → Upload traces/screenshots/reports and expose the result clearly in the PR checklist.
- [Port collision can cause false failures] → Use strict, documented ports and Playwright-managed services or an explicit preflight failure; do not silently select another port.
- [UI copy changes can break the smoke] → Prefer accessible roles and user-visible semantic text over CSS selectors; keep assertions limited to stable contract-level behavior.
- [Known broken Spec tab may tempt scope expansion] → Exclude it explicitly and return `BLOCKED` if the requested smoke scope requires it.

## Migration Plan

1. Add the package, lockfile, config, test, ignore rules, CI job, and governance checklist text on a feature branch.
2. Run local type/build checks plus the Playwright smoke with services available.
3. Run workspace hygiene and inspect the unified diff.
4. If the harness is reverted, remove only the new Playwright files, dependency/lockfile entries, CI job, ignore entries, and governance text; application runtime behavior is unaffected.

## Open Questions

The exact Playwright package version and backend command/address compatibility still require evidence before implementation handoff. Browser matrix, write workflows, and visual testing remain intentionally deferred.

## Review hardening — revision 2

User decision after review: "Keep harness-only; expose the existing failure". A correctly reported failing smoke is acceptable evidence of harness failure detection, not evidence that the application works. Successful dashboard coverage remains unverified until the separate application defect is repaired. Do not add a placeholder, lazy import, skip, or expected-failure marker to conceal it.

This section supersedes conflicting alternatives above. Review provenance: `reviews/plan-review-001.md` and its three specialist records. That frozen review returned NEEDS_REVISION; this revision has not been re-reviewed.

- Workflow target: create `.github/workflows/prototype-e2e.yml`; leave both existing workflows unchanged. Use `pull_request` targeting main/master with paths covering the entire prototype (backend included) and the new workflow. Declare `permissions: contents: read`, no secrets, no `pull_request_target`, and default checkout rather than a custom fork-head checkout. Use checkout@v4, setup-node@v4, setup-python@v5, upload-artifact@v4.
- Advisory means job-level `continue-on-error: true`, not suppressing command exit codes. Do not use shell success coercion. Do not configure this check as required; repository rulesets are external settings and must be checked before claiming merge eligibility is unaffected.
- Use Playwright's two-entry `webServer` array with explicit backend/frontend working directories, commands and readiness URLs. Use `reuseExistingServer: false` locally and in CI, startup timeout 60 seconds per service, and no reload mode. Occupied ports must fail without killing unrelated processes. Playwright owns only its launched processes and cleans them up; verify Windows and CI lifecycle behavior. Freeze exact commands after checking localhost address resolution against the unchanged Vite proxy.
- Browser config: Chromium only, headless, viewport 1280 by 720, one worker, zero retries, test timeout 30 seconds, assertion timeout 10 seconds, CI job timeout 10 minutes. Test directory `./tests`, match `**/*.spec.ts`, CI forbidOnly enabled.
- Smoke locators: `getByRole('heading', { name: 'Sampling & Spec R&D', exact: true })` and `getByText('Connected', { exact: true })`. No assertion accepting Local Mode. Keep the full `/api/sampling-spec-rnd/health` request through the unchanged Vite `/api` proxy; do not invent a health JSON body assertion.
- Pin the selected compatible @playwright/test version exactly and commit package-lock.json. Resolve the concrete version from current package metadata before handoff. New CI uses Node 20, Python 3.11, npm ci, lockfile-keyed npm cache and `npx playwright install --with-deps chromium`. Do not modify the old npm install job.
- Diagnostics: list and HTML reporters, HTML open never, screenshot only-on-failure, trace off, video off. Upload only playwright-report and test-results with `if: !cancelled()`, retention 7 days, missing files warn. Startup failure may produce logs without browser artifacts; record that honestly. Use only local synthetic/test services, no production credentials or data.
- Governance: available interactive browser tools are preferred for relevant user-visible pre-commit checks; otherwise use automated Playwright. Neither path substitutes for unrelated required checks. PR evidence selects interactive, automated, both, or unverified and records URL/scenario, command/tool, result and evidence link or limitation. Documentation-only changes can say not applicable with a reason. A failure must be recorded, not converted to a passing checkbox.
- Verification must distinguish config discovery, service readiness, browser launch, assertion failure, and successful end-to-end behavior. Test occupied-port rejection without killing the occupant. With the current missing import, expect and preserve a nonzero smoke result; do not claim a successful dashboard run. Structural OpenSpec validation alone does not close runtime proof gaps.
