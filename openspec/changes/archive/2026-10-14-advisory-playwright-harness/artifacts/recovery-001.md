# Recovery Research 001 — Advisory Playwright Harness

- **Identity:** `advisory-playwright-harness-recovery-001`
- **Recovered from:** interrupted Orchestrator dispatch after pre-implementation planning and review were complete; configuration, spec, workflow, governance, and dependency lockfile were written but execution verification is incomplete.
- **Mode:** read-only research. No installs, no servers, no source edits beyond this report. The only file write permitted by mode rules was this report at `openspec/changes/advisory-playwright-harness/artifacts/recovery-001.md`.
- **Date:** 2026-10-14.
- **Repository:** `C:\Projects\hackathon-MAIN-alkademi`.
- **Branch:** `feat/payroll-bonus-pool` (`HEAD d37f6a3`, even with `origin/feat/payroll-bonus-pool`).
- **Tooling fingerprint:** Python 3.11.4, Node v24.11.0, npm 11.18.0, git 2.47.0.windows.2, PowerShell pwsh, Windows.

## 1. Scope of this report

The user-approved brief instructs me to record where the implementation stopped and the exact remaining work for the `advisory-playwright-harness` OpenSpec change, with no edits except this report. The user explicitly cited "harness-only; expose the existing failure" — which means the unrepaired `SpecVersionPage` import in `src/App.tsx` is intentional and must NOT be touched. Parent agent will run install, browser launch, and verification commands; this report does not run any of them.

## 2. Where implementation stopped

The previous Orchestrator dispatch wrote the design revision 2 harness material and then aborted before parent-side verification could be executed. State on disk at this moment:

### Tracked-file diffs (modified, not yet staged)

| File | Diff summary (verified) |
|---|---|
| `.github/pull_request_template.md` | +6 lines: new `## Browser Verification Evidence` section with four checkbox options (Verified by inspection of `git diff`). |
| `AGENTS.md` | +6 lines: new `### Browser Verification Default` subsection inserted between the existing engineering bar and the junior-developer guidance (Verified by inspection of `git diff`). |
| `prototypes/sampling-spec-rnd/frontend/.gitignore` | +3 anchored lines `/test-results/`, `/playwright-report/`, `/blob-report/` at lines 8–10 (Verified via `Select-String`). |
| `prototypes/sampling-spec-rnd/frontend/package.json` | +2 lines: `test:e2e` script and devDependency `"@playwright/test": "1.63.0"`. No `engines` field added. Verified via `read_file`. |

### Untracked files (new, not yet committed; not yet staged)

| Path | Verified content |
|---|---|
| `.github/workflows/prototype-e2e.yml` | Dedicated advisory workflow. `on: pull_request` only. `permissions: contents: read`. No `pull_request_target`. `timeout-minutes: 10`. `continue-on-error: true` at job level. `actions/checkout@v4`, `actions/setup-node@v4` with `cache: 'npm'` keyed on the lockfile, `actions/setup-python@v5`, `actions/upload-artifact@v4`. Steps: `npm ci` (frontend), `pip install -r requirements.txt` (backend with explicit `working-directory`), `npx playwright install --with-deps chromium`, `npm run test:e2e`, then `if: ${{ !cancelled() }}` artifact upload of `playwright-report/` and `test-results/` with `retention-days: 7` and `if-no-files-found: warn`. Path trigger: `prototypes/sampling-spec-rnd/**` and the workflow file itself. |
| `openspec/changes/advisory-playwright-harness/` (entire directory, untracked) | `proposal.md`, `design.md` (revision 2 noted inline), `tasks.md`, `.openspec.yaml`, `specs/advisory-browser-smoke/spec.md`, `specs/agent-browser-verification/spec.md`, `reviews/plan-review-001.md`, `reviews/specialist-s-001.md`, `reviews/specialist-b-001.md`, `reviews/specialist-c-001.md`. **No `artifacts/`** before this write — parent receives this file first. |
| `prototypes/sampling-spec-rnd/frontend/package-lock.json` | `lockfileVersion: 3`. Resolved entry `node_modules/@playwright/test` at `1.63.0` (`engines.node: ">=20"`), `playwright` at `1.63.0`, `playwright-core` at `1.63.0`. Integrity hashes present for all three tarballs. Verified via `read_file` and `Select-String`. |
| `prototypes/sampling-spec-rnd/frontend/playwright.config.ts` | Two-entry `webServer` array with explicit `cwd`/`name`/`command`/`url`/`timeout: 60_000`/`reuseExistingServer: false`. Backend `command: 'python -m uvicorn src.main:app --host 127.0.0.1 --port 8009'`, `url: http://127.0.0.1:8009/api/sampling-spec-rnd/health`. Frontend `command: 'npm run dev -- --host 127.0.0.1 --port 3009'`, `url: http://127.0.0.1:3009`. `testDir: ./tests`, `testMatch: **/*.spec.ts`, `timeout: 30_000`, `expect.timeout: 10_000`, `workers: 1`, `retries: 0`, `fullyParallel: false`, `forbidOnly: Boolean(process.env.CI)`. `reporter: [['list'], ['html', { open: 'never' }]]`. Single `chromium` project spread from `devices['Desktop Chrome']`. `use.baseURL: http://127.0.0.1:3009`, `headless: true`, `viewport: { width: 1280, height: 720 }`, `screenshot: 'only-on-failure'`, `trace: 'off'`, `video: 'off'`. |
| `prototypes/sampling-spec-rnd/frontend/tests/smoke.spec.ts` | One spec, one test. Loads `/`, expects `getByRole('heading', { name: 'Sampling & Spec R&D', exact: true })` visible, expects `getByText('Connected', { exact: true })` visible. Read-only. |

### Verification outcome from this read-only pass

- `openspec validate advisory-playwright-harness --strict` returns "Change 'advisory-playwright-harness' is valid".
- `openspec list` reports `advisory-playwright-harness 0/20 tasks 37m ago`.
- Local install is already on disk: `prototypes/sampling-spec-rnd/frontend/node_modules/@playwright/test/package.json` reports `version: 1.63.0`; `node_modules/playwright/package.json` reports `version: 1.63.0`. `playwright-core` is present. The Chromium browser cache `~/.cache/ms-playwright/` is **not** present locally — `npx playwright install --with-deps chromium` will download it.

## 3. Items the user asked to spot-check

### 3.1 Viewport device override (B10 / C-1-004)

- **Implementation (verified):** `playwright.config.ts` declares both a global `use.viewport = { width: 1280, height: 720 }` and a project `use: { ...devices['Desktop Chrome'] }`.
- **Official docs (Verified, source <https://playwright.dev/docs/emulation>):** "It is important to define the `viewport` property after destructuring `devices`, since devices also define the `viewport` for that device."
- **Result:** the project-level device spread overrides the global `viewport`. `devices['Desktop Chrome']` defaults to `1280 × 720`, so the smoke still runs at 1280×720 functionally; however, the explicit-after-destructure pinning recommended by the B10 finding and the design revision 2 is **NOT** applied. The plan's intent (anchored viewport, resilient against future device descriptor changes) is not code-explicit.
- **Risk:** low (Desktop Chrome defaults are stable). The narrower visibility contract from review B10 is satisfied only by happenstance, not by design.
- **Honest status:** the smoke is expected to render at 1280×720 width during runs; the review-finding pattern was not enforced. Recommend `use: { ...devices['Desktop Chrome'], viewport: { width: 1280, height: 720 } }` for future revisions to make intent obvious.

### 3.2 Backend imports & deps (B1 adjacent)

- **Verified:** Backend layout is intact and matches the imports in `src/api/routes.py`:
  - `src/main.py`
  - `src/api/routes.py`
  - `src/api/__init__.py`
  - `src/models/time_study_recorder.py`, `src/models/spec_version_tracker.py`, `src/models/__init__.py`
  - `src/services/sampling_rnd_workflow.py`, `src/services/__init__.py`
  - `src/utils/time_study_patterns.py`, `src/utils/spec_version_patterns.py`, `src/utils/__init__.py`
- **Verified:** `python -m py_compile` over `main.py`, `api/routes.py`, `services/sampling_rnd_workflow.py`, `models/time_study_recorder.py`, `models/spec_version_tracker.py`, `utils/time_study_patterns.py`, `utils/spec_version_patterns.py` produced no output — static syntax is sound.
- **Verified:** `requirements.txt` pins `fastapi==0.104.1`, `uvicorn[standard]==0.24.0`, `python-multipart==0.0.6`, `python-dotenv==1.0.0`. The workflow uses `pip install -r requirements.txt` — sufficient for `routes.py`'s direct imports (no `pydantic`-top-level, no `requests`, no `httpx` referenced at import time).
- **Risk remaining:** the workflow has no Python venv; system pip install into GH-hosted Python 3.11 is acceptable but not best practice. `pydantic` is a transitive of `fastapi==0.104.1`; no override declared.

### 3.3 Local proxy localhost vs IPv4 listener

- **Verified:** `vite.config.ts` proxy `'/api'` target is `http://localhost:8009` (no `rewrite` rule). CORS on the backend allows `http://localhost:3009` and `http://127.0.0.1:3009` (and the stale `3007`).
- **Verified:** Playwright `webServer` launches the backend with `--host 127.0.0.1 --port 8009` and the frontend with `--host 127.0.0.1 --port 3009`. `reuseExistingServer: false` means both are owned by Playwright; if either port is occupied Playwright throws (it does not probe or attach).
- **Implication:** On Linux CI runners, `localhost` resolves cleanly to the IPv4 loopback and the Vite proxy works. **On Windows, Node's HTTP client honors `localhost` via `dns.lookup`, which on some Windows builds returns both `127.0.0.1` and `::1`.** If the first attempt uses `::1` and uvicorn is bound to `127.0.0.1` only, ECONNREFUSED can occur. The smoke is short-circuited by `webServer` health polling against the explicit `127.0.0.1` URLs; the proxy target value is the application-defined surface area and is intentionally NOT modified by this change.
- **Mitigation already encoded:** `main.py` runs `uvicorn.run(app, host="0.0.0.0", port=8009, reload=True)` — but the Playwright-launched instance overrides with `--host 127.0.0.1`. The Playwright-launched instance is IPv4-only; Windows callers must resolve `localhost` consistently.
- **Owns vs. mitigated:** Cannot change `vite.config.ts` proxy target (out of scope per design revision 2). Risk is environmental and the smoke will work in CI (Linux); on Windows the loopback-resolution behavior remains an unverified runtime variable. **Marked UNVERIFIED; cannot be resolved without running `npm run dev` + browser.**

### 3.4 Package version 1.63.0 and lockfile

- **Verified:** `package.json` declares `"@playwright/test": "1.63.0"` (exact pin, not caret).
- **Verified:** `package-lock.json` resolves `node_modules/@playwright/test` at `1.63.0`, dep `playwright: 1.63.0`; transitive `playwright` at `1.63.0`; `playwright-core` at `1.63.0`. Integrity hashes present.
- **Verified:** `@playwright/test@1.63.0` engines is `node >= 20` — compatible with CI's `node-version: '20'` and the local `v24.11.0`.
- **Verified:** `@playwright/test@1.63.0` is a published version on npm at <https://www.npmjs.com/package/@playwright/test/v/1.63.0>. Last publish date metadata present in the registry; the version is real and frozen.

### 3.5 Env overrides

- **Verified:** `api.ts` reads `import.meta.env.VITE_API_URL` with default `/api/sampling-spec-rnd`. No `.env` is committed (`.gitignore` blocks `.env`, `.env.local`, `.env.*.local`). `.env.example` only declares the relative path and explicitly warns `JANGAN pakai http://localhost:...`.
- **Verified:** Playwright config does not set `_API_URL`-style env vars and does not pass any `env` overrides to its `webServer` entries. `BASE` resolves to `/api/sampling-spec-rnd` in the bundled smoke path — the proxy, not a direct backend connection, is what the smoke exercises.
- **Verified:** `webServer.command` for the backend invokes `python -m uvicorn` without `PYTHONUNBUFFERED`, no extra env. The backend `src/main.py` calls `load_dotenv()` and reads `API_PORT`/`API_HOST` from env if present; CI uses the literal CLI-flag port 8009, which `main.py` honors only when launched as a script (the Playwright-launched instance passes `--port 8009` directly, bypassing the env).
- **Risks:** None introduced by the harness. The drifted `backend/.env.example` (`API_PORT=8007`, `CORS_ORIGINS=http://localhost:3007`) is pre-existing and design §3 carves it out of scope.

### 3.6 Branch provenance

- **Verified:** Local HEAD at `d37f6a3 docs(ops): record payroll PR integration` on `feat/payroll-bonus-pool`. Upstream `origin/feat/payroll-bonus-pool` is even (same SHA). Recent chain (back 7 commits): `d37f6a3`, `0e58ae5 merge(master): resolve payroll integration conflict`, `42b3ed1 Merge pull request #3 ...`, `59048d1 feat(ledger): ...`, `9a1a57a feat(payroll): consolidate the quality bonus pool`, `775e649 feat(payroll): calculate weekly borongan wages`, `24bba84 feat(payroll): add the payroll period schemas`, `db0ee53 feat(payroll): add the financial rule registry domain`. No churn in the harness files on the branch yet — all harness files are local-only and untracked.
- **Verified:** `gh pr list` shows only PR #2 (`feat/lukla-ops-engine-planning`, OPEN, DRAFT). The advisory harness branch has **no remote PR**. Therefore no GitHub-side environment gates apply yet.

## 4. What pre-existing failure is preserved (B1 / design revision 2)

- **Verified:** `prototypes/sampling-spec-rnd/frontend/src/App.tsx:8` contains `import SpecVersionPage from '@/pages/SpecVersionPage';` (eager, static, top-of-file import).
- **Verified:** `src/pages/` contains only `index.ts` and `TimeStudyPage.tsx` (16,114 bytes). The file `src/pages/SpecVersionPage.tsx` does NOT exist. `src/pages/index.ts` only re-exports `./TimeStudyPage`.
- **Verified:** `src/components/SpecVersionTracker.jsx` exists (component, NOT page) and is not imported by `App.tsx`.
- **Expected consequence:** `vite dev` prebundle / Rollup / `tsc --noEmit` all error on this missing module. The dashboard root cannot mount. `getByRole('heading', { name: 'Sampling & Spec R&D' })` will not find the heading; `expect(...).toBeVisible()` will time out at the test timeout (30 s) or the 10 s `expect` timeout. **No skip, mock, lazy boundary, or annotation has been inserted — the harness exposes the existing defect instead of repairing or concealing it.** This matches the user's "harness-only; expose the existing failure" decision.

## 5. What still needs parent-agent verification (and was NOT done here)

Per mode rules I did not perform any install, server startup, browser run, or test execution. The following commands remain parent-side responsibilities, each anchored to a tasks.md §4 checkbox:

1. `python scripts/check_workspace_hygiene.py` (tasks.md §4.3). Expected to pass: every modified/new file sits inside `.github/`, `AGENTS.md` is root-allowed, prototype frontend files are inside `prototypes/`, change folder is inside `openspec/`. No spurious root entries.
2. `npm ci --prefix prototypes/sampling-spec-rnd/frontend` and `pip install -r prototypes/sampling-spec-rnd/backend/requirements.txt` (tasks.md §4.1). Lockfile and `requirements.txt` already on disk.
3. `npx playwright install --with-deps chromium` (tasks.md §4.1). Will populate `~/.cache/ms-playwright/chromium-{revision}/` on the runner.
4. `npm --prefix prototypes/sampling-spec-rnd/frontend run type-check` (tasks.md §4.2). Expected to fail at `App.tsx:8` per the B1 finding unless the application-side repair lands separately. The CI's existing `frontend-quality` job uses `npm install` (lifecycle scripts) and runs the same `type-check` already — pre-existing latent posture, not introduced here.
5. `npm --prefix prototypes/sampling-spec-rnd/frontend run build` (tasks.md §4.2). Expected to fail for the same `SpecVersionPage` reason.
6. `npm run test:e2e` (tasks.md §4.1). Expected behavior:
   - `webServer` array launches backend on `127.0.0.1:8009` and frontend on `127.0.0.1:3009`.
   - Vite dev pre-bundle likely fails on `SpecVersionPage`; the page.goto(`/`) responds with a Vite error overlay OR a 500.
   - `getByRole('heading', { name: 'Sampling & Spec R&D', exact: true })` cannot locate any visible heading → assertion times out.
   - Playwright reports `expect.toBeVisible` failure with a `TimeoutError`, generates `playwright-report/` HTML and `test-results/` artifacts; uploads both with `if: !cancelled()`.
   - **Job exits nonzero but `continue-on-error: true` keeps the advisory status green** — the PR remains mergeable, the defect is recorded, no claim of successful E2E is made.
7. Interactive browser fallback (tasks.md §4.4). When an interactive browser tool is available it should be used for the failed heading lookup to confirm the Vite error overlay and visually distinguish a startup-time failure from an assertion-time one. If only automated Playwright is run, the PR evidence records that explicit limitation per `specs/agent-browser-verification/spec.md`.

## 6. Remaining tasks.md items not in code yet

Tasks listed 1.1–1.5, 2.1–2.4, 3.1–3.3 are physically present in the working tree (verified above). Tasks §5 "Review closure before implementation handoff" have **NOT** been closed:

- **5.1 "Resolve the exact compatible Playwright version and backend command/address contract using current metadata."** Partial: 1.63.0 pinning is correct and verified against npm; `python -m uvicorn src.main:app --host 127.0.0.1 --port 8009` is concrete. **Still open:** the IPv4-vs-localhost resolver contract on Windows (Sec. 3.3) was not measured.
- **5.2 "Apply design revision 2 to all harness configuration and policy tasks."** Partial: design-tasks alignment is mostly satisfied, but the explicit-after-destructure viewport override for the chromium project (Sec. 3.1) is not applied.
- **5.3 "Re-review the revised plan against reviews/plan-review-001.md."** Not done. The frozen `plan-review-001.md` verdict is `NEEDS_REVISION`. No new review record at `reviews/plan-review-002.md` exists.

Other design-review findings (per `reviews/`) recorded below for completeness; none of them is a blocker for the user's "harness-only" decision but each remains formally OPEN:

| Origin | Finding | Status in code |
|---|---|---|
| B1 (HIGH) | Static `SpecVersionPage` import prevents module resolution. | Preserved as intended. |
| B2 (MEDIUM) | Selector strategy pins `getByText('Connected', { exact: true })`. | Implemented (`tests/smoke.spec.ts:5`). No `data-testid` added — kept per design revision 2's "exact text match" instruction. |
| B3 (MEDIUM) | Bounded timeouts. | Implemented: `timeout: 30_000`, `expect.timeout: 10_000`. |
| B4 (MEDIUM) | `webServer` array with two entries. | Implemented. |
| B5 (MEDIUM) | Health proxy contract — UI-only, no JSON-body assertion. | Smoke assertion is text-only; comment in `smoke.spec.ts` documenting the no-rewrite proxy is NOT present (reviewer recommendation not encoded). |
| B6 (MEDIUM) | `npm ci` + npm cache. | Implemented in workflow. Local `frontend-quality` job still uses `npm install`; pre-existing latent posture, out of scope. |
| B7 (MEDIUM) | `tsconfig.tests.json`. | Not added. Playwright runtime 1.63.0 enforces types at test load; editor support for `tests/` is at user-discretion. |
| B8 (MEDIUM) | `testDir: ./tests`, `testMatch: **/*.spec.ts`. | Implemented. |
| B9 (LOW) | Anchored `/test-results/`, `/playwright-report/`, `/blob-report/`. | Implemented (lines 8–10 of frontend `.gitignore`). `/playwright/.cache/` not added — Playwright browser cache is in `~/.cache/ms-playwright` on the runner, not the project. |
| B10 (LOW) | Explicit `viewport: 1280×720` after `...devices['Desktop Chrome']`. | Implicit (Desktop Chrome defaults to 1280×720); not code-explicit. |
| B11/B12 (LOW-INFORMATIONAL) | `run_frontend.bat` port drift (3007/8007). | Out of scope per design §3. |
| C-1-001 (BLOCKING_DEFECT) | Same as B1. | Preserved as intended. |
| C-1-002 (PROOF_GAP) | `reuseExistingServer: !process.env.CI`. | Strictly enforced: `reuseExistingServer: false` everywhere; fails fast if port is occupied. Stricter than the docs idiom. |
| C-1-003 (PROOF_GAP) | Existing `frontend-quality` job's `npm install`. | Untouched; pre-existing latent posture. |
| C-1-004 (PROOF_GAP) | Same as B10. | Same status. |
| C-1-005 (PROOF_GAP) | Workflow placement. | Resolved: dedicated `.github/workflows/prototype-e2e.yml`. `prototype-sampling.yml` is untouched (verified by repo diff). |
| C-1-006 (PROOF_GAP) | Pin `@playwright/test` with caret. | Pinned exact `1.63.0` (no caret). Stricter; correct for a single-version lockfile. |
| C-1-007 (PROOF_GAP) | Two-entry `webServer` array. | Implemented. |
| C-1-008 (PROOF_GAP) | PR template evidence wording. | Implemented four-checkbox enumeration. |
| C-1-009 (PROOF_GAP) | `.gitignore` Playwright outputs. | Implemented. |
| C-1-010 (LEARN_NOTE) | `run_frontend.bat` port drift. | Out of scope; not addressed. |
| S-1 F1/F2/F5/F7 | `pull_request` only, `contents: read`, fork-head checkout absent, `headless: true`. | Implemented in workflow + config. `actions/setup-node@v4`'s `node-version: "20"` matches `@playwright/test@1.63.0` engines `>=20`. |
| S-1 F3 | `npm ci`, no `npm install`. | Resolved for new advisory job; pre-existing `frontend-quality` job untouched. |
| S-1 F4 | Trace off, bounded retention. | Implemented (`trace: 'off'`, `retention-days: 7`, `if: !cancelled()`, `if-no-files-found: warn`). |
| S-1 F6 | Action majors (`checkout@v4`, `setup-node@v4`, `upload-artifact@v4`). | Implemented; `setup-python@v5` matches existing `ci.yml` (consistent). `microsoft/playwright-github-action` is NOT referenced. |

## 7. Recap: exact remaining work for the orchestrator/parent

1. Stage and commit the modified tracked files and the untracked harness files as a single commit on `feat/payroll-bonus-pool`.
2. Push; open a PR (none open today per `gh pr list`).
3. Confirm `python scripts/check_workspace_hygiene.py` exits 0 locally.
4. Wait for the new `prototype-e2e` advisory job to run on the PR; expect a `continue-on-error: true` job whose underlying test fails on the heading/connection assertions due to the preserved `SpecVersionPage` defect.
5. Inspect the uploaded `prototype-playwright-reports` artifact — `playwright-report/index.html` should show the dashboard smoke `TimeoutError` for the heading, screenshots, and console output.
6. Update `openspec/list` task state by recording the verified outcome in `artifacts/recovery-001.md` (this file) and adding `reviews/plan-review-002.md` to close the original `NEEDS_REVISION` verdict with an explicit close-out note that the "harness-only; expose the existing failure" decision was honored.

No further source edits were performed by this research. The harness shape, the dependency pin, the workflow contract, and the policy text remain as they were when the previous Orchestrator dispatch terminated.

## 8. Useful paths produced/consumed

- `openspec/changes/advisory-playwright-harness/artifacts/recovery-001.md` — this file.
- `openspec/changes/advisory-playwright-harness/{proposal.md,design.md,tasks.md,specs/**,reviews/**}` — verified intact.
- `prototypes/sampling-spec-rnd/frontend/{playwright.config.ts,tests/smoke.spec.ts,package.json,package-lock.json,.gitignore}` — verified intact, untracked except for the package.json and frontend .gitignore diff.
- `.github/{workflows/prototype-e2e.yml,pull_request_template.md}` — verified intact.
- `AGENTS.md` — verified intact.

End of recovery research 001.
