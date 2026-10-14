# Review Orchestrator Record — Advisory Playwright Plan

## Review Identity

- **Identity:** `advisory-playwright-plan-review-001`
- **Subject:** Frozen plan files under `openspec/changes/advisory-playwright-harness/`: `proposal.md`, `design.md`, `tasks.md`, and `specs/**`.
- **Review mode:** Read-only. No source, governance, or plan files were changed. Review records only were added under `reviews/`.
- **Date:** 2026-10-14
- **Repository:** `C:\Projects\hackathon-MAIN-alkademi`
- **Branch:** `feat/payroll-bonus-pool`
- **Working-tree fact:** The change directory is untracked and local; no implementation exists and no remote PR was opened.

## Objective and Acceptance Target

Assess whether the plan is implementation-ready for a minimal, advisory, non-blocking real Chromium smoke that:

1. starts the existing prototype frontend/backend deterministically on ports 3009/8009;
2. verifies only the read-only dashboard heading and backend-backed `Connected` UI state;
3. exposes failures and diagnostics without blocking unrelated jobs or merges;
4. defines safe, portable browser-verification guidance: interactive browser tool first, Playwright fallback, honest unverified state;
5. avoids source behavior changes and unrelated CI changes unless a pre-existing defect makes the requested harness impossible.

## Routing and Dispatch

Controlled route evaluation:

| Dimension | Decision | Reason | Dispatch |
|---|---|---|---:|
| Behavioral (`runtime-or-config`, `observable-behavior`, `behavioral-validation`) | **YES** | The plan depends on module loading, two service processes, health polling, selectors, and CI failure behavior. | 1 |
| Changeability (`interface-contract`, `seam-adapter`, `dependency-shape`, `teammate-safety`) | **YES** | The plan crosses frontend/backend/Playwright/workflow/governance seams and adds a dependency/lockfile. | 1 |
| Security (`trust-boundary`, `secrets-or-privacy`, `external-security-dependency`) | **YES** | CI executes PR-controlled package and browser-test code and uploads reports/traces. Security Assurance is mandatory for this route. | 1 |

**Actual dispatch count:** 3 specialist instances, one per selected route.

- Behavioral: `specialist-b-001.md` — **COMPLETE**
- Changeability: `specialist-c-001.md` — **COMPLETE**
- Security Assurance: `specialist-s-001.md` — **COMPLETE**

No dispatch failed, was partial, or was ambiguous. No additional instance was needed: the three reports independently covered the requested third-pair-of-eyes review and their material findings were reconcilable.

## Evidence Checked

### Frozen plan

- `proposal.md`, `design.md`, `tasks.md`
- `specs/advisory-browser-smoke/spec.md`
- `specs/agent-browser-verification/spec.md`
- `.openspec.yaml`

OpenSpec validation was available as prior evidence and was reported by the changeability specialist as valid. No install, server startup, browser run, or runtime test was performed, per the frozen brief.

### Current repository

- `prototypes/sampling-spec-rnd/frontend/src/App.tsx`
- `prototypes/sampling-spec-rnd/frontend/src/pages/` directory
- `prototypes/sampling-spec-rnd/frontend/package.json`
- `prototypes/sampling-spec-rnd/frontend/vite.config.ts`
- `prototypes/sampling-spec-rnd/frontend/.gitignore`
- `prototypes/sampling-spec-rnd/backend/src/main.py` and backend startup files
- `.github/workflows/prototype-sampling.yml`
- `.github/workflows/ci.yml`
- `.github/pull_request_template.md`
- `AGENTS.md` and `scripts/check_workspace_hygiene.py`

Confirmed facts:

- `App.tsx:8` statically imports `@/pages/SpecVersionPage`.
- `prototypes/sampling-spec-rnd/frontend/src/pages/SpecVersionPage.tsx` is absent; the pages directory contains `index.ts` and `TimeStudyPage.tsx` only.
- The dashboard heading is `Sampling & Spec R&D`.
- The status text is `Connected` or `Local Mode`, inside a `hidden sm:inline` span.
- Vite is configured for port 3009 with `strictPort: true` and proxies `/api` to `http://localhost:8009` without a rewrite.
- The backend exposes `/api/sampling-spec-rnd/health` on port 8009.
- No Playwright dependency, lockfile, config, or test exists yet.
- Existing `prototype-sampling.yml` is advisory, uses `pull_request` and `permissions: contents: read`, but its existing frontend job uses `npm install` and there is no browser job.
- The PR template has no browser-evidence section.

### External sources

The specialists consulted official or primary sources including:

- Playwright web server configuration: <https://playwright.dev/docs/test-webserver>
- Playwright test configuration and `reuseExistingServer`: <https://playwright.dev/docs/api/class-testconfig>
- Playwright CI guidance: <https://playwright.dev/docs/ci>
- Playwright timeouts: <https://playwright.dev/docs/test-timeouts>
- GitHub token permissions: <https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/controlling-permissions-for-github_token>
- GitHub `pull_request_target` security guidance: <https://docs.github.com/en/actions/reference/security/securely-using-pull_request_target>
- GitHub Security Lab pwn-request guidance: <https://securitylab.github.com/resources/github-actions-preventing-pwn-requests/>
- GitHub status checks: <https://docs.github.com/en/pull-requests/reference/status-checks>
- Archived/deprecated Playwright GitHub Action: <https://github.com/microsoft/playwright-github-action>

## Classified Findings

### BLOCKING_DEFECT — B-1 / C-1-001: the plan cannot produce a runnable smoke against the current app

- **Provenance:** Behavioral `B-1`, Changeability `C-1`.
- **Evidence:** `prototypes/sampling-spec-rnd/frontend/src/App.tsx:8` eagerly imports `@/pages/SpecVersionPage`; the target file is missing. `App.tsx` renders the dashboard and Spec Version under one module graph, so avoiding a click does not avoid resolving the import.
- **Affected criterion:** real dashboard smoke must load; the plan must be an executable handoff.
- **Consequence:** Vite/TypeScript/build startup can fail before the root renders. The proposed test would report infrastructure-looking failure while the application cannot cold-boot.
- **Required closure:** The plan must explicitly choose one bounded prerequisite before the harness: (a) add a minimal placeholder `SpecVersionPage.tsx` as a separately labeled stub-only repair, or (b) convert the import to a lazy boundary so the dashboard can boot. If the user forbids either source change, the plan must stop and state that the executable smoke is deferred; “do not click Spec Version” is not sufficient.
- **Validation required after revision:** run frontend `type-check` and `build`; confirm the dashboard cold-starts. Runtime execution remains unverified in this review.

### PROOF_GAP — C-1-005: workflow location and ownership are ambiguous

- **Provenance:** Changeability `C-1`.
- **Evidence:** `tasks.md:2.1` allows either editing `.github/workflows/prototype-sampling.yml` or creating a dedicated workflow, while `design.md` says separate or clearly isolated.
- **Affected criterion:** no unrelated CI changes and precise executable handoff.
- **Consequence:** Different implementers can change different workflow surfaces, triggers, cache keys, and rollback paths. This conflicts with the stated non-goal of leaving existing quality jobs untouched.
- **Required closure:** Pick one exact workflow path. Recommended: a dedicated `.github/workflows/prototype-e2e.yml` with narrow prototype frontend/workflow paths, leaving `prototype-sampling.yml` unchanged. If editing the existing file is chosen, define the exact job boundary and prove existing jobs are unchanged.
- **Validation:** review the unified diff and workflow path filters; run YAML/workflow static validation if available.

### PROOF_GAP — B-2 / C-1-004: selector and viewport contract is underspecified

- **Provenance:** Behavioral `B-1`, Changeability `C-1`.
- **Evidence:** `App.tsx` has no test id or status role; `Connected` is under `hidden sm:inline`.
- **Affected criterion:** deterministic dashboard and Connected assertion.
- **Consequence:** A vague `getByText` choice can break on copy or viewport changes; a narrow viewport hides the asserted text.
- **Required closure:** Pin a desktop viewport, for example `{ width: 1280, height: 720 }`, and explicitly choose either an exact text locator (`getByText('Connected', { exact: true })`) or a minimal status test id. Record the choice in the task and smoke spec, with a bounded assertion timeout.
- **Validation:** inspect the implemented config/spec for the exact locator, viewport, and numeric timeout.

### PROOF_GAP — B-3 / B-4 / C-1-002 / C-1-007: service startup and wrong-process behavior are not fully specified

- **Provenance:** Behavioral `B-1`, Changeability `C-1`.
- **Evidence:** The plan says “Playwright or equivalent” but does not require the two-entry Playwright `webServer` array, service-specific URLs, or `reuseExistingServer` behavior. Official Playwright docs support multiple named web servers and document that reuse checks availability, not service identity.
- **Affected criterion:** deterministic local/CI startup and accurate failures.
- **Consequence:** A stale process on 3009/8009 can be reused or a custom startup script can introduce races and hide the wrong service.
- **Required closure:** Require `webServer: [{...backend...}, {...frontend...}]`, distinct names, explicit commands/cwds, health URL for backend, frontend URL, strict ports, bounded startup timeout, and `reuseExistingServer: !process.env.CI` (or a stricter no-reuse policy if selected). Do not let the harness silently choose alternate ports. State how process cleanup works on the target runner; the Playwright docs note Windows graceful shutdown limitations.
- **Validation:** static config review plus a deliberate stale-port negative check during implementation; no such runtime check was run here.

### PROOF_GAP — B-5: health/proxy contract needs to be frozen

- **Provenance:** Behavioral `B-1`.
- **Evidence:** `api.ts` fetches `/api/sampling-spec-rnd/health`; Vite proxies `/api` without rewrite; backend exposes the full prefixed route. There are also distinct `/health` routes.
- **Affected criterion:** Connected state must prove the intended backend path, not an accidental endpoint.
- **Consequence:** A future rewrite or body assertion can target the wrong route and produce misleading results.
- **Required closure:** State that the smoke is UI-only, uses the full prefixed health path through the Vite proxy, and does not infer a JSON body contract unless the plan pins that contract. Preserve the no-rewrite fact.
- **Validation:** inspect config and test comments/assertions; confirm no unintended rewrite.

### PROOF_GAP — B-6 / S-3: dependency and install reproducibility are not sufficiently pinned

- **Provenance:** Behavioral `B-1`, Security `S-1` F3, Changeability `C-1` F-C1-003/F-C1-006.
- **Evidence:** No lockfile exists. The plan asks for one but does not specify the dependency version or CI install command precisely. Existing `prototype-sampling.yml` uses `npm install` in a separate pre-existing job.
- **Affected criterion:** deterministic CI and safe execution of PR-controlled package code.
- **Consequence:** Implementers may use a floating dependency or `npm install`, mutate/resolve dependencies differently, and run lifecycle scripts in fork PRs.
- **Required closure:** Pin a chosen `@playwright/test` version/range and commit the generated lockfile; require `npm ci` for the new job; install only Chromium with the official CLI (`npx playwright install --with-deps chromium`); define Node 20 and npm cache keying to that lockfile. Do not silently broaden scope by changing the pre-existing frontend job unless separately approved.
- **Validation:** `npm ci` against the committed lockfile, lockfile-diff inspection, and static workflow review. No install was performed here.

### PROOF_GAP — S-1 F1/F2/F6/F7: CI trust boundary, action versions, and headless mode are not pinned in the plan

- **Provenance:** Security Assurance `S-1`.
- **Evidence:** Current workflows use `pull_request` and `contents: read`, but the new workflow is not written and the plan only says “triggered by relevant prototype changes.”
- **Affected criterion:** safe fork PR execution and reproducible advisory job.
- **Consequence:** Future implementation could accidentally use `pull_request_target`, checkout a fork head in a privileged context, omit least-privilege permissions, use a deprecated Playwright action, or vary headed/headless execution.
- **Required closure:** State `on: pull_request` only; forbid `pull_request_target` and fork-head checkout; declare `permissions: contents: read`; use pinned repo-consistent action majors (`checkout@v4`, `setup-node@v4`, `upload-artifact@v4`); use CLI browser installation; pin `headless: true` and deterministic workers.
- **Validation:** static grep of workflow for forbidden trigger/head ref and excessive permissions; inspect action pins.

### PROOF_GAP — S-1 F4: artifact privacy and retention are not specified

- **Provenance:** Security Assurance `S-1`.
- **Evidence:** `tasks.md:2.3` only requests failure artifacts; the plan does not state trace mode, report retention, or whether artifacts are uploaded on cancellation.
- **Affected criterion:** useful diagnostics without unnecessary privacy exposure.
- **Consequence:** Future trace settings may capture more network/DOM data than this read-only smoke needs, and default retention may be longer than intended.
- **Required closure:** Default trace off; use only-on-failure screenshots and a bounded HTML report/retention period; upload with explicit `if` conditions and document fork visibility limitations. Do not claim artifacts exist if startup fails before Playwright creates them; upload logs separately if required.
- **Validation:** inspect config and workflow retention/action conditions.

### LEARN_NOTE — B-11/B-12 and S-1 unknowns: existing drift is real but not a blocker for this plan

- **Provenance:** Behavioral `B-1`, Security `S-1`.
- **Evidence:** `run_frontend.bat` advertises stale 3007/8007 ports while Vite/backend use 3009/8009. Existing prototype frontend CI uses `npm install`. Fork approval/settings and dashboard tenant-data exposure were not verified.
- **Consequence:** Maintainers may be confused, but the planned harness can bypass the stale batch file and the smoke only reads the dashboard/health state.
- **Recommendation:** Record these as explicit out-of-scope notes. Do not expand this change to fix the batch file or retrofit existing CI unless the user approves scope expansion.

## Minimal Hardening Package for the Parent Plan

Before implementation, revise the plan with the smallest exact changes:

1. Add a prerequisite for the missing eager import and obtain the user’s choice: stub-only source repair, lazy import repair, or defer the executable smoke. This is the only material user decision surfaced by review.
2. Choose one workflow path, preferably a dedicated prototype E2E workflow.
3. Specify exact `webServer` entries, service URLs, ports, cwd/commands, reuse policy, cleanup, and numeric timeouts.
4. Specify exact Chromium viewport, headless/workers settings, test directory/match, locator, and assertion timeout.
5. Pin Playwright dependency and lockfile; require `npm ci`, Chromium-only CLI installation, and lockfile-based npm cache.
6. Pin `pull_request`, `contents: read`, action majors, no fork-head checkout, and no deprecated Playwright action.
7. Define trace/screenshot/report modes and bounded artifact retention.
8. Freeze the health proxy contract and distinguish startup failure from assertion failure.
9. Define the PR template evidence choices as interactive / automated / unverified, with tool or run/artifact evidence rather than a bare checkbox.

These changes do not require a broad testing framework, browser matrix, visual regression, or application feature work.

## Execution Health

**COMPLETE.** All three selected specialist instances completed and returned usable records. No specialist failure, partial result, or ambiguity prevented classification. The review did not run installs, servers, browsers, or runtime tests; those remain implementation-phase verification requirements.

## Verdict

**NEEDS_REVISION**

The plan is directionally small and appropriately advisory, but it is not implementation-ready. The missing eager import is an anchored `BLOCKING_DEFECT`; the workflow/startup/selector/dependency/trust-boundary/artifact details are acceptance-linked `PROOF_GAP`s. The reviewer cannot approve a Playwright harness that cannot cold-start the current frontend and whose CI ownership and security contract are left to implementer choice.

## Review Worklog and Retrieval Failures

- Loaded global instructions, repository `AGENTS.md`, `review-protocol`, and `orchestration-policy` before dispatch.
- Read all frozen plan/spec files directly.
- Used semantic search for initial repository mapping; results included stale/irrelevant port documentation, so direct filesystem reads were used for final evidence.
- Confirmed current source/workflow state with PowerShell inspection; no installs, servers, or browser execution.
- Dispatched exactly three specialist reviews through available `Explorer` agents. No named Review Orchestrator agent was available, so this Assistant owns reconciliation and verdict.
- Official Playwright and GitHub sources were searched/fetched by the specialists and cited in their records. The deprecated `microsoft/playwright-github-action` was identified; the CLI is the recommended path.
- Retrieval limitation: no runtime proof was available because the frozen brief prohibited installs and server startup. No claim of smoke execution, artifact generation, or CI behavior is made.
- Specialist path typo in S-1's returned prose (`chackathon-MAIN-alkademi`) was corrected to the verified repository path in this record; the actual file exists at `openspec/changes/advisory-playwright-harness/reviews/specialist-s-001.md`.

## Written Records

- `openspec/changes/advisory-playwright-harness/reviews/specialist-b-001.md`
- `openspec/changes/advisory-playwright-harness/reviews/specialist-c-001.md`
- `openspec/changes/advisory-playwright-harness/reviews/specialist-s-001.md`
- `openspec/changes/advisory-playwright-harness/reviews/plan-review-001.md`
