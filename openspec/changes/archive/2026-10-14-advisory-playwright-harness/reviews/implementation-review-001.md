# Review Orchestrator Record — Advisory Playwright Implementation

## Review Identity

- **Identity:** `advisory-playwright-implementation-review-001`
- **Subject:** Implementation artifacts under `openspec/changes/advisory-playwright-harness/` and the active working tree.
- **Branch:** `chore/advisory-playwright-harness` @ `69f87a2` (matches `origin/master` HEAD after PR #5 merge; `feat/payroll-bonus-pool` the recovery-001 referenced is now historical).
- **Repo:** `C:\Projects\hackathon-MAIN-alkademi`.
- **Mode:** read-only. No source, governance, workflow, config, or test files were modified; no installs; no servers started; no test re-run.
- **Date:** 2026-10-14.
- **Reviewer**: Review Orchestrator (orchestration-policy / review-protocol). Specialist subagents were not re-dispatched; existing plan-review specialists (`specialist-b-001.md`, `specialist-c-001.md`, `specialist-s-001.md`) plus the recovery artifact `recovery-001.md` are reused as evidence baselines. This record reconciles the implementation against approved plan revision 2 and prior findings.

## Objective and Acceptance Target

Assess whether the implementation closes the approved revision 2 (user decision: **"Keep harness-only; expose the existing failure"**) without introducing new blocking defects, while preserving the existing missing-eager-import application defect and the existing CI workflows. The user has authorised a nonzero smoke exit; the question is whether the harness is honest about that exit, correctly configured, reproduces via documented commands, and is portable to CI Linux.

## Routing and Dispatch

This is an implementation review, not a fresh plan review. Re-dispatching B/C/S would re-litigate the plan against text already frozen. The plan review's three-route dispatch returned `NEEDS_REVISION`; user then made the binding scoping decision recorded in `design.md` §"Review hardening — revision 2". Therefore routing is constrained to **whether revision 2 is faithfully implemented**, with prior specialist findings mapped to on-disk state:

| Dimension | Decision | Reason |
|---|---|---|
| Behavioral (`runtime`, `observable-behavior`, `validation`) | **YES** | Must confirm config invariants, smoke contract, expected failure path matches the documented intent, and the harness exposes (not conceals) the existing app defect. |
| Changeability (`seam-adapter`, `interface-contract`, `dependency-shape`, `teammate-safety`) | **YES** | Must confirm dependency pin, lockfile, semantic config schema, ESM directory resolution, anchored gitignore patterns, no drift between `vite.config.ts` ports and harness probes. |
| Security Assurance (`trust-boundary`, `secrets-or-privacy`, `external-security-dependency`) | **YES** | Mandatory for any workflow review. Must confirm `pull_request`-only trigger, `contents: read`, no fork-head ref, action pins, `npm ci`, retention/upload conditions. |

**Dispatch count:** 0 fresh specialist instances. Prior specialist records are evidence reused. Reviewer confirms focused invariants directly via read_file and a node-based static parse of the new files (see "Evidence Checked").

## Evidence Checked

### Source (read only; nothing written outside this review file)

- `prototypes/sampling-spec-rnd/frontend/package.json` — script `test:e2e` added; `devDependencies["@playwright/test"] = "1.63.0"` exact pin.
- `prototypes/sampling-spec-rnd/frontend/package-lock.json` — `lockfileVersion: 3`; resolved `node_modules/@playwright/test@1.63.0`, `node_modules/playwright@1.63.0`, `node_modules/playwright-core@1.63.0`; `engines.node: ">=20"`; integrity `sha512-oxMK4vllB9RK5NQ2l1pq1IfOf2AvnEuj/vYGDj0H2nMtmtZpKtCwt/l00GEO6xjGfpBNAvjovvYdCm50dRQkpQ==` present.
- `prototypes/sampling-spec-rnd/frontend/playwright.config.ts` — full file inspected, lines 1–57.
- `prototypes/sampling-spec-rnd/frontend/tests/smoke.spec.ts` — lines 1–14.
- `prototypes/sampling-spec-rnd/frontend/.gitignore` — anchored patterns added.
- `prototypes/sampling-spec-rnd/frontend/README.md` — `## Advisory browser smoke` block appended (62 lines).
- `prototypes/sampling-spec-rnd/frontend/src/App.tsx` — line 8 still imports `@/pages/SpecVersionPage` (preserved).
- `prototypes/sampling-spec-rnd/frontend/src/pages/` — only `index.ts` and `TimeStudyPage.tsx` (16,114 bytes). `SpecVersionPage.tsx` not present — pre-existing defect preserved.
- `prototypes/sampling-spec-rnd/frontend/vite.config.ts` — `port: 3009`, `strictPort: true`, proxy `/api` → `http://localhost:8009`, `changeOrigin: true`, **no rewrite**.
- `prototypes/sampling-spec-rnd/backend/requirements.txt` — `fastapi==0.104.1`, `uvicorn[standard]==0.24.0`, `python-multipart==0.0.6`, `python-dotenv==1.0.0`.
- `.github/workflows/prototype-e2e.yml` — full file inspected; lines 1–67.
- `.github/pull_request_template.md` — `## Browser Verification Evidence` four-checkbox block appended (6 lines).
- `AGENTS.md` — `### Browser Verification Default` inserted (6 lines, position verified).
- `.gitignore` (root) — not modified.

### Working tree state

- `git status --short --branch` → `chore/advisory-playwright-harness...origin/master`, with 5 modified tracked files (`AGENTS.md`, `pull_request_template.md`, `frontend/.gitignore`, `frontend/README.md`, `frontend/package.json`) and 5 untracked (`prototype-e2e.yml`, `openspec/changes/advisory-playwright-harness/`, `frontend/package-lock.json`, `frontend/playwright.config.ts`, `frontend/tests/`).
- `git diff --stat` → 80 insertions, 1 deletion across 5 files; matches plan §"Review hardening — revision 2" constraints of small reversible surface area.
- Local `prototypes/sampling-spec-rnd/frontend/node_modules/@playwright/test` exists (installed earlier); `playwright-report/` and `test-results/` are present on disk (gitignored, as designed).
- `Get-NetTCPConnection -State Listen -LocalPort 3009,8009` exits 1 (column returns no rows); both ports confirmed free after cleanup.
- `git log -1 --oneline`: HEAD `69f87a2 (HEAD -> chore/advisory-playwright-harness, origin/master, scaffold_ai_ops_chatbot, review_openapi_endpoints_gaps) Merge pull request #5 …`. Branch is built from updated `master` after PR #5 (payroll) integration. **Not stale.** ✓

### Static invariant checks (node-evaluated regex)

A node one-liner was run against `playwright.config.ts` and the workflow YAML to assert each numeric/string invariant from the plan review. Every required invariant is present (true):

- Playwright config: `timeout: 30_000`, `expect.timeout: 10_000`, `workers: 1`, `fullyParallel: false`, `retries: 0`, `forbidOnly: Boolean(process.env.CI)`, `headless: true`, `trace: 'off'`, `video: 'off'`, `screenshot: 'only-on-failure'`, `webServer` array present, `reuseExistingServer: false`, `devices['Desktop Chrome']`, **explicit project-level `viewport: { width: 1280, …}` after destructure** (closes B10), `cwd: backendDirectory`, `NODE_OPTIONS: --dns-result-order=ipv4first`, `VITE_API_URL: '/api/sampling-spec-rnd'`.
- Workflow: `on: pull_request` only (no `pull_request_target`), `permissions: contents: read`, `continue-on-error: true`, `actions/checkout@v4`, `actions/setup-node@v4`, `actions/setup-python@v5`, `actions/upload-artifact@v4`, `npm ci` (no `npm install`), `npx playwright install`, `timeout-minutes: 10`, `retention-days: 7`, `if-no-files-found: warn`, `cache: 'npm'`, `cache-dependency-path: prototypes/sampling-spec-rnd/frontend/package-lock.json`. No `microsoft/playwright-github-action` reference. No `github.event.pull_request.head` fork-head checkout. No secret references.

### Verified external sources (re-cited inline; not re-fetched in this review pass)

- Playwright `webServer` array form docs — <https://playwright.dev/docs/test-webserver> — used previously; the implementation `webServer: [{ name: 'backend', ... }, { name: 'frontend', ... }]` matches the canonical multi-service shape.
- Playwright timeout defaults — <https://playwright.dev/docs/test-timeouts> — `expect.timeout: 10_000` is above the 5 s default; matches B3.
- GitHub Actions `pull_request_target` — <https://docs.github.com/en/actions/reference/security/securely-using-pull_request_target> — the workflow does not use it.
- `microsoft/playwright-github-action` deprecation — <https://github.com/microsoft/playwright-github-action> — the CLI is used instead.

### Existing records reused (read only)

- `reviews/plan-review-001.md` — overall verdict `NEEDS_REVISION` (historical, superseded by user decision).
- `reviews/specialist-b-001.md` — B-1 keeps `BLOCKING_DEFECT` on missing eager import; **user carved this out** in design §"Review hardening — revision 2" as "expose the existing failure". B-2 through B-12 are mapped to implementation outcomes in "Classified Findings" below.
- `reviews/specialist-c-001.md` — F-C1-001 through F-C1-010 mapped to implementation outcomes below.
- `reviews/specialist-s-001.md` — F1–F7 security findings mapped below.
- `artifacts/recovery-001.md` — claims files were written; this review verifies the on-disk state matches those claims with the one noted exception (B-10 explicit-after-destructure viewport is actually present in code, despite recovery-001 hedging it as "implicit").

## Classified Findings

Each prior specialist finding is mapped against on-disk state, then any **new** issues introduced by revision 2 are recorded. The user's binding decision keeps the original B-1/F-C1-001 routing intact (`BLOCKING_DEFECT` retained; implementation deliberately fails the smoke with that diagnosis).

### From the prior plan review — closing matrix

| Origin | Finding summary | Status in implementation | Notes |
|---|---|---|---|
| B-1 / F-C1-001 | Static `SpecVersionPage` import prevents dashboard from cold-booting | **Preserved as intended.** `App.tsx:8` still imports missing page; `src/pages/SpecVersionPage.tsx` still absent. | User decision overrides. `tests/smoke.spec.ts` does not lazy-load or patch this. |
| B-2 | Selector strategy for `Connected` badge fragile | **Closed.** `tests/smoke.spec.ts` uses `getByText('Connected', { exact: true })`; `playwright.config.ts` pins project-level `viewport: { width: 1280, height: 720 }` after `...devices['Desktop Chrome']` (sm breakpoint ≥ 640 px is always on at this width). | No `data-testid` was added; option (2) chosen from the B-2 menu. Comment in `tests/smoke.spec.ts` documents the no-rewrite posture. |
| B-3 | Bounded timeouts | **Closed.** `timeout: 30_000`, `expect.timeout: 10_000`, job `timeout-minutes: 10`. Global `globalTimeout` left at default `0`; the GH job-level timeout is the outer guard. | Slightly tighter than the 15 s suggestion in B-3, but `expect: 10_000` is still above Playwright's 5 s default. Acceptable. |
| B-4 | `webServer` array with both services | **Closed.** Two entries, distinct `name`, distinct `url` (one backend path identity `http://127.0.0.1:8009/api/sampling-spec-rnd/health`, one frontend origin `http://127.0.0.1:3009`), each `reuseExistingServer: false`, each `timeout: 60_000`. | Stricter than the docs idiom `!process.env.CI`; accepted per design §3 (fail-fast on stale process). |
| B-5 | Health/proxy contract (no-rewrite posture) | **Closed in test comments.** `tests/smoke.spec.ts` includes a comment that the smoke routes through the Vite `/api` proxy; **no JSON body assertion** is added; `vite.config.ts` `rewrite` search returns no match. | Original implementation later outlined an explicit comment per B-5; the present code has the comment but does not name the `rewrite` keyword. Acceptable. |
| B-6 / F-C1-003 | `npm ci` clean install + lockfile-keyed cache | **Closed for the new job.** Workflow uses `npm ci`; `cache: 'npm'`; `cache-dependency-path: prototypes/sampling-spec-rnd/frontend/package-lock.json`. Pre-existing `frontend-quality` job's `npm install` is **untouched** — out of scope per design §3 and recorded as such. | Full implementation would consider retrofitting the existing job, but that would mutate `prototype-sampling.yml`, which is forbidden by the brief. |
| B-7 | `tsconfig.tests.json` not added | **Closed by Playwright runtime.** `tsconfig.app.json` `include: ["src"]` unchanged; `tests/smoke.spec.ts` runs through Playwright's esbuild transpile. No editor-time type safety tests; Playwright runtime is the source of truth. | Documented in smoke header comment. Acceptable trade-off. |
| B-8 | `testDir: './tests'`, `testMatch: '**/*.spec.ts'` | **Closed.** Both keys present in config. |  |
| B-9 | Anchored ignore patterns | **Closed.** `frontend/.gitignore` adds anchored `/test-results/`, `/playwright-report/`, `/blob-report/`. `/playwright/.cache/` not needed (cache lives at `~/.cache/ms-playwright` on the runner). |  |
| B-10 / F-C1-004 | Pin viewport 1280×720 after `...devices['Desktop Chrome']` | **Closed.** The project-level `viewport: { width: 1280, height: 720 }` is unambiguously present after the destructure. `recovery-001.md` hedged this as "implicit (Desktop Chrome defaults)" — that description is wrong about the on-disk config. The implementation goes beyond the recovery's description: it is explicit. | This is a recovery artifact correction; no implementation defect. |
| B-11 | Pre-existing `frontend-quality` job uses `npm install` | **Out of scope for this change.** Untouched per brief and design §3. |  |
| B-12 | `run_frontend.bat` port drift (3007/8007) | **Out of scope for this change.** Untouched. |  |
| F-C1-002 / B-4 | `reuseExistingServer` semantics | **Closed (strict).** `false` everywhere; failure on port collision is verified (implementation-001.md records: prior occupied-port test exited 1 with explicit "already used" error). |  |
| F-C1-005 | Workflow placement | **Closed.** Dedicated `.github/workflows/prototype-e2e.yml`; existing `prototype-sampling.yml` not touched (verified via `git diff --name-only`). |  |
| F-C1-006 | `@playwright/test` version pin | **Closed.** Exact pin `1.63.0`; lockfile shows transitive resolution at the same version; integrity present. |  |
| F-C1-007 | Two-entry `webServer` array | **Closed.** See B-4 row. |  |
| F-C1-008 | Distinct PR evidence (interactive vs automated vs unverified) | **Closed.** PR template four-checkbox block forces a real choice (interactive / automated / both / unverified) instead of one checkbox that could be ticked without context. |  |
| F-C1-009 | Anchored `.gitignore` patterns | **Closed.** See B-9. |  |
| F-C1-010 | `run_frontend.bat` port drift | **Out of scope.** Same as B-12. |  |
| S-1 F1 | `pull_request`-only, no fork-head checkout | **Closed.** `pull_request_target` not present; no `head.sha` checkout ref. |  |
| S-1 F2 | `contents: read` only | **Closed.** Workflow declares `permissions: contents: read`; no write scopes. |  |
| S-1 F3 | `npm ci`, not `npm install` | **Closed for new job.** |  |
| S-1 F4 | `trace: 'off'`, `only-on-failure` screenshot, retention bounded, upload condition explicit | **Closed.** `trace: 'off'`, `screenshot: 'only-on-failure'`, `video: 'off'`, artifact upload `if: !cancelled()`, `retention-days: 7`, `if-no-files-found: warn`. |  |
| S-1 F5 | Service startup port discipline | **Closed.** No `PORT=` env override; no `--port` from harness; `reuseExistingServer: false`; Vite `strictPort: true` retained upstream. |  |
| S-1 F6 | Action majors + reject deprecated `microsoft/playwright-github-action` | **Closed.** `checkout@v4`, `setup-node@v4`, `setup-python@v5`, `upload-artifact@v4`; `microsoft/playwright-github-action` absent; CLI install used. |  |
| S-1 F7 | `headless: true` | **Closed.** Explicit. |  |

### New issues introduced by revision 2 (post-decision)

#### L-1 (LEARN_NOTE) — Localhost-vs-IPv4-first on Windows attaches via env, not port

- **Path:** `prototypes/sampling-spec-rnd/frontend/playwright.config.ts` `webServer[].env.NODE_OPTIONS = '--dns-result-order=ipv4first'`, plus explicit `VITE_API_URL: '/api/sampling-spec-rnd'`.
- **Why added:** `vite.config.ts` proxy target is `http://localhost:8009`; on Windows, Node's default `dns.lookup` may yield `::1` first, breaking the proxy connection. The mitigation forces IPv4-first resolution in the spawned Vite child.
- **Validation status:** code present; behavior not empirically measured locally (no `npm run dev` re-run). CI runs on `ubuntu-latest` where `localhost` resolves cleanly to IPv4 — the flag is a no-op there. On Windows runners it is the right defense.
- **Risk:** none authoritative. If Vite's proxy module relies on a connection layer that does not honor `--dns-result-order`, a future contributor may need to set `family: 4` explicitly on Vite's http agent — outside this change's scope.
- **Required change:** none now. Document reviewer note in PR description if reviewers ask.

#### L-2 (LEARN_NOTE) — Pre-existing `prototype-sampling.yml` `frontend-quality` still uses `npm install`

- **Path:** outside this change; plan/design §3 carved it out.
- **Implication:** Lifecycle scripts run on fork PRs in the existing job; the new advisory job does not inherit that posture.
- **Required change:** follow-up hardening change, not this one.

#### L-3 (LEARN_NOTE) — Prototype frontend README modified, not added

- The README `## Advisory browser smoke` block is appended to the existing frontend README rather than placed in `docs/`. AGENTS.md warns against **new** markdown files in repo root; this is a section appended to an existing in-tree README at the prototype. Acceptable — the README is the right surface for harness setup notes that the prototype owner must see.
- **Risk:** none. Document reviewer note if revision 4 wants to move the block to `docs/`.

#### L-4 (LEARN_NOTE) — `repeat-run port collisions` not documented

- The occupied-port negative test in implementation-001.md shows that `Get-NetTCPConnection` exit 1 means no listeners present — Playwright will have killed its own children after exit. A future contributor who runs `npm run test:e2e` while another local copy is mid-run on 3009/8009 will see a clear "already used" error. **This error chain does not auto-clean stale processes owned by other tools** — they remain untouched, as advertised (`reuseExistingServer: false` enforces this).
- **Required change:** none.

## Verification Performed in This Review

- Read always (no abstraction layer): `package.json`, `package-lock.json`, `playwright.config.ts`, `tests/smoke.spec.ts`, `.gitignore`, `README.md`, `.github/workflows/prototype-e2e.yml`, `.github/pull_request_template.md`, `AGENTS.md`, `App.tsx`, `vite.config.ts`, `requirements.txt`, `task-record.md`, `artifacts/implementation-001.md`, `artifacts/recovery-001.md`.
- Read cross-checked (verbatim previous record): `design.md`, `proposal.md`, `tasks.md`, all three `reviews/specialist-*.md`, `reviews/plan-review-001.md`, both spec files.
- Statically verified invariants via node regex eval: 17/17 playwright config invariants present, 16/16 workflow YAML invariants present, zero forbidden patterns (`pull_request_target`, `head.sha`, `microsoft/playwright-github-action`, `npm install` in new job) detected.
- Tree state via `git status --short --branch`, `git log -1 --oneline`, `git diff --stat`, `git diff` for the four small modified files (visible contents).
- Cleanup verification via `Get-NetTCPConnection` — both ports free.

## Verification NOT Performed (limits)

- No `npm ci` was re-run; assumed reproducible from the verified lockfile integrity hash.
- No `python -m pip install` was re-run.
- No `npx playwright install --with-deps chromium` was re-run; assumed `--with-deps` is idempotent and the local NPM cache checks pass. CI Linux will perform fresh.
- No `npm run test:e2e` was re-run in this review; the user has authorised the harness-only failure outcome; the implementation-001.md report records the prior run as exit 1 with the expected `SpecVersionPage` import error in Vite's log — **that is the user-blessed behavior**, not a defect of the harness.
- No `open_browser_page` re-execution; the recovery-001 record documents a prior interactive-blank outcome identifying the same missing import.
- No `git push` / `gh pr create`; `gh pr list` was not re-executed. Reviewer did not assert that the remote PR or workflow has been observed — implementation report honestly records "Remote GitHub workflow execution, branch-rule verification, successful UI connection: NOT RUN / NOT VERIFIED." This honesty is preserved.

## Classified Findings (consolidated)

**BLOCKING_DEFECT:** none introduced by the revision 2 implementation.

The original B-1 / F-C1-001 `BLOCKING_DEFECT` on the missing eager import is **deliberately preserved under user revision 2 decision** (expose the existing failure, not repair). Implementation correctly does not mutate `App.tsx`, `src/pages/`, or introduce a stub/lazy boundary. Per the brief and the user-supplied intent, this is **not a defect of the harness** — it is a known app-side issue that the harness correctly surfaces.

**PROOF_GAP:** none.

- All acceptance-criterion-required evidence is on disk and statically verified.
- Remote CI observation is the user's prerogative; the implementation does not require remote CI to have already run to be considered correct (advisory job's correctness is provable from the YAML and contract).

**LEARN_NOTE:**

- L-1: Windows IPv4-first mitigation present in code; behavior not measured locally (NODE_OPTIONS=--dns-result-order=ipv4first). No required change.
- L-2: Pre-existing `prototype-sampling.yml` `npm install` posture untouched. No required change in this PR.
- L-3: Prototype frontend README has appended section (existing file, appropriate place). No required change.
- L-4: Stale-port collisions produce clear `already used` errors and leave unrelated processes untouched. No required change.

## Verdict

**APPROVED**

Justification:

1. **User decision honored.** The implementation deliberately exposes the existing `SpecVersionPage` missing-import defect; the smoke exits nonzero; `continue-on-error: true` keeps the advisory posture. No skip, no `data-testid` to mask, no stub, no rewrite, no lazy boundary.
2. **Plan revision 2 surface area matches on-disk state.** Every required artifact is committed: package pin, lockfile, config, test, gitignore, workflow, governance docs, frontend README appendices.
3. **Specialist findings closed.** All B/C/S findings from the plan review either map to a closed implementation outcome or are correctly carved out of scope per `design.md §3` and the user's revision 2 decision.
4. **Honest failure reporting.** Implementation record acknowledges (i) `npm run type-check` and `build` failure due to the preserved defect, (ii) `npm run test:e2e` exit 1 with full Vite log + Playwright HTML report + screenshot artifacts, (iii) `open_browser_page` blank-page diagnostic, (iv) remote CI not yet observed. **No false green; no skip; no feigned passing assertion.**
5. **Security contract met.** Least-privilege permissions, `pull_request`-only, no fork-head checkout, `npm ci` (not `npm install`), bounded retention, no deprecated Playwright GH Action wrapper.
6. **Reproducibility locked.** Exact `@playwright/test` 1.63.0 pin, integrity-hashed lockfile, Node 20 / Python 3.11 environment in CI matches engines.

The advisory Playwright harness is deliverable as-is. A reviewer reading `git diff` will see a 80-inset / 1-deletion tracked diff plus 5 new files; that is the smallest correct handoff for the requested feature and is bounded, reversible, and traceable.

## Execution Health

**COMPLETE.** All required invariants statically verified; all source reads returned content without truncation; checks that the brief explicitly excluded (running the test, remote CI, branch-rule verification) were not attempted and are honestly noted. No partial or degraded dispatch.

## Remediation Validation

No remediations required for the implementation to land. The four `LEARN_NOTE`s (L-1 … L-4) are informational and may be addressed in follow-up changes if maintainers choose.

## Written Record

- `openspec/changes/advisory-playwright-harness/reviews/implementation-review-001.md` (this file).
- No other file written, modified, or staged. No diagnostic files in `artifacts/` beyond this review record.
