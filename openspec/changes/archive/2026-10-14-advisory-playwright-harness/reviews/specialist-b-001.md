# Specialist Review B-1 — Behavioral — Advisory Playwright Harness

Review identity: `advisory-playwright-plan-review-001`.
Date: 2026-10-14.
Environment: Windows; working tree at `C:\Projects\hackathon-MAIN-alkademi`; branch `feat/payroll-bonus-pool`; OpenSpec change `openspec/changes/advisory-playwright-harness/` is **untracked, local only** (no remote PR open).
Mode: read-only review. No installs, no servers, no source/plan edits, no dependency probing; the only file written is this review record.

## Role

Behavioral assurance review of the proposed minimal Playwright harness plan. Calibrated to the requested minimalist, advisory, non-blocking scope, focused on:

- runtime and configuration behavior (startup, port discipline, webServer lifecycle)
- application imports and module-graph integrity (does the page actually load?)
- selector strategy (stable, role-/text-/data-testid-driven)
- health-endpoint contract mapping (proxy path → backend route)
- isolated CI behavior (artifacts, lockfile/cache posture, type-check compatibility)

Outside the behavioral lens: trust-boundary and supply-chain hardening (covered by `specialist-s-001.md`; cross-referenced where overlap exists); backend business-logic correctness; visual/product taste.

## Status

Review complete. **One HIGH-severity finding (B1) and seven MEDIUM findings (B2–B8) and four LOW findings (B9–B12) recorded below as hardening remdies.** The HIGH finding concerns the unresolved `SpecVersionPage` import in `App.tsx:8`, which — contrary to the plan's "do not click Spec Version" mitigation — propagates to the dashboard smoke because the import is **eager/static**, not lazy. Tripwire answer is **unfavorable**: the dashboard smoke cannot pass on the current code without first creating a minimal `src/pages/SpecVersionPage.tsx` placeholder stub OR converting the static import to a `React.lazy()` boundary. This is recorded without running the dev server; tripwire validation uses the existing `npm run type-check` and `npm run build` commands (and not running `npm ci`).

All other findings are bounded hardening: import-path discipline, selector robustness, timeout pinning, `webServer` array commit, lockfile/cache configuration, and PR template text budget. None of those would block the spec once B1 has a clear scope amendment.

## Evidence Checked

Repository files read (full path / line range) and what behavior each verifies:

| Path | Lines | Behavior verified |
|---|---|---|
| `openspec/changes/advisory-playwright-harness/proposal.md` | 1–200 | Why/What/Scope |
| `openspec/changes/advisory-playwright-harness/design.md` | 1–400 | Decisions, risks, ports |
| `openspec/changes/advisory-playwright-harness/tasks.md` | 1–400 | Implementation checklist (1.1–4.5) |
| `openspec/changes/advisory-playwright-harness/.openspec.yaml` | 1–200 | Schema marker |
| `openspec/changes/advisory-playwright-harness/specs/advisory-browser-smoke/spec.md` | 1–200 | Smoke job spec |
| `openspec/changes/advisory-playwright-harness/specs/agent-browser-verification/spec.md` | 1–200 | Agent browser policy |
| `openspec/changes/advisory-playwright-harness/reviews/specialist-s-001.md` | 1–400 | Prior security specialist review (cross-reference) |
| `.github/workflows/ci.yml` | 1–300 | Existing CI baseline; `permissions: contents: read`; `pull_request` only |
| `.github/workflows/prototype-sampling.yml` | 1–300 | Targeted workflow; `Node 20`, `run: npm install` (existing latent posture) |
| `.github/pull_request_template.md` | 1–200 | Existing checklist (no browser-evidence item today) |
| `AGENTS.md` | 1–120 | Engineering philosophy (one prerequisite; anchored `/...` `.gitignore`) |
| `prototypes/sampling-spec-rnd/frontend/package.json` | 1–120 | Scripts baseline; no Playwright dep yet |
| `prototypes/sampling-spec-rnd/frontend/tsconfig.json` | 1–40 | Path aliases (`@/*`, `@pages/*` → `./src/pages/*`) |
| `prototypes/sampling-spec-rnd/frontend/tsconfig.app.json` | 1–20 | `include: ["src"]` — tests will not enter app compilation |
| `prototypes/sampling-spec-rnd/frontend/vite.config.ts` | 1–60 | `port: 3009`, `strictPort: true`, `/api` proxy → `http://localhost:8009`, **no `rewrite`** |
| `prototypes/sampling-spec-rnd/frontend/index.html` | 1–20 | `<title>Sampling & Spec R&D</title>` (stable document.title) |
| `prototypes/sampling-spec-rnd/frontend/src/main.tsx` | 1–20 | Entry module imports `App` from `@/App` |
| `prototypes/sampling-spec-rnd/frontend/src/App.tsx` | 1–186 | **Critical**: static import `import SpecVersionPage from '@/pages/SpecVersionPage'` at line 8; `<h2>Sampling & Spec R&D</h2>` at line 29; `checkHealth()` at line 106; `Connected`/`Local Mode` badge at lines 155–161 |
| `prototypes/sampling-spec-rnd/frontend/src/pages/index.ts` | 1–1 | Only `export { default as TimeStudyPage } from './TimeStudyPage'` |
| `prototypes/sampling-spec-rnd/frontend/src/pages/` (directory) | — | Contains `index.ts`, `TimeStudyPage.tsx`; **no `SpecVersionPage.tsx`, no `SpecVersionPage/` directory, no `.jsx`** |
| `prototypes/sampling-spec-rnd/frontend/src/services/api.ts` | 1–60, 244–261 | `BASE = VITE_API_URL ‖ '/api/sampling-spec-rnd'`; `checkHealth()` fetches `${BASE}/health` |
| `prototypes/sampling-spec-rnd/frontend/.gitignore` | 1–60 | `node_modules/`, `dist/` present; no Playwright output rules yet |
| `prototypes/sampling-spec-rnd/frontend/run_frontend.bat` | 1–20 | References port `3007` (stale; out of scope per design §3) |
| `prototypes/sampling-spec-rnd/backend/run_backend.bat` | 1–20 | References port `8009` (consistent with current `main.py`) |
| `prototypes/sampling-spec-rnd/backend/src/main.py` | 1–60 | `@app.get("/api/sampling-spec-rnd/health")` at line 47; `@app.get("/health")` at line 41 |
| `prototypes/sampling-spec-rnd/backend/src/api/routes.py` | 316–321 | `/health` route returns `{status, module}` (read-only) |
| `scripts/check_workspace_hygiene.py` | 1–50 | Root file whitelists (relevant to `.gitignore` patterns) |

External sources cited (date of fetch in worklog):

- Vite Troubleshooting — <https://vite.dev/guide/troubleshooting.html> (case sensitivity, "Module not found" diagnostic).
- Rollup Troubleshooting — <https://rollupjs.org/troubleshooting/> ("[name] is not exported by [module]" verification; missing module behavior).
- Playwright Web server — <https://playwright.dev/docs/test-webserver> (`webServer` array, `command`/`url`/`timeout`/`reuseExistingServer`).
- Playwright Timeouts — <https://playwright.dev/docs/test-timeouts> (test timeout 30 s default; expect timeout 5 s default; `globalTimeout`).
- AGENTS.md in-repo root — "Anchored Git Rules" (leading `/` for `.gitignore` patterns).

Static audit findings (no source modification performed):

- `Test-Path prototypes/sampling-spec-rnd/frontend/playwright.config.ts` → `False`.
- `Test-Path prototypes/sampling-spec-rnd/frontend/package-lock.json` → `False`.
- `Test-Path prototypes/sampling-spec-rnd/frontend/tests` → `False`.
- `Get-ChildItem prototypes/sampling-spec-rnd/frontend/src/pages` → `index.ts`, `TimeStudyPage.tsx` only.
- `Get-ChildItem -Recurse -Filter *SpecVersionPage*` against the whole repo → only `components/SpecVersionTracker.jsx`; **no page-level file**.
- `Select-String -Path .github/workflows/* -Pattern 'pull_request_target'` → 0 matches (corroborates S-1 F1).
- `Select-String -Path .github/workflows/prototype-sampling.yml -Pattern 'cache|npm ci|npm install'` → only `prototype-sampling.yml:72: run: npm install` (existing latent posture).

Git state: `feat/payroll-bonus-pool...origin/feat/payroll-bonus-pool`, `?? openspec/changes/advisory-playwright-harness/`. Plan-only review; no implementation exists yet.

## Findings

Each Finding: ID — path/lines — criterion (behavioral principle) — consequence if not addressed — minimum remedy — validation.

### B1 (HIGH) — Static `import SpecVersionPage` will fail module resolution; smoke cannot load the dashboard

- **Path/lines.** `prototypes/sampling-spec-rnd/frontend/src/App.tsx:8` (`import SpecVersionPage from '@/pages/SpecVersionPage'`); `prototypes/sampling-spec-rnd/frontend/src/pages/index.ts:1` (only re-exports `./TimeStudyPage`); `prototypes/sampling-spec-rnd/frontend/src/pages/` directory listing (only `index.ts`, `TimeStudyPage.tsx`); `prototypes/sampling-spec-rnd/frontend/tsconfig.json:24` (`paths["@pages/*"]: ["./src/pages/*"]`); `prototypes/sampling-spec-rnd/frontend/vite.config.ts:11–17` (`@pages` alias).
- **Criterion.** Static (eager) ESM imports in `App.tsx` are bound at module-load time, before any tab is rendered. If a static import cannot be resolved, Vite (dev server, Rollup build) and `tsc --noEmit` all fail with `Module not found` / `RollupError: Could not resolve import@/pages/SpecVersionPage from ...` — the React root never mounts. The plan's "do not click Spec Version" mitigation only blocks the runtime navigation; it does **not** prevent the cold-boot failure of the entire app module graph, which `React.StrictMode` (in `main.tsx:14`) executes first. Verified by direct file inspection (no install required): the imported file does not exist anywhere resolving the alias.
- **Consequence.** Even with a healthy backend on `8009` and the new advisory job running cleanly, the smoke will not see the `<h2>Sampling & Spec R&D</h2>` heading. The dashboard smoke will report failure on a broken application, not on Playwright infrastructure. Worse: the smoke's "BLOCKED: <…" path of `tasks.md §4.5` is fired, but the block is the wrong blocker — the team will conclude Playwright is at fault rather than a pre-existing import bug.
- **Minimum remedy.** Add a §0 prerequisite to `tasks.md` BEFORE §1:

  ```text
  ## 0. Pre-existing module-graph integrity
  - [ ] 0.1 Verify `src/App.tsx` imports resolve against `src/pages/`. Add a minimal placeholder stub at `prototypes/sampling-spec-rnd/frontend/src/pages/SpecVersionPage.tsx` exporting a placeholder component (`export default function SpecVersionPage(){return <div>Spec Version coming soon</div>}`), OR convert the static import in `App.tsx:8` to `const SpecVersionPage = React.lazy(() => import('@/pages/SpecVersionPage'))` behind the existing `<Suspense>` boundary so its module-resolution failure does not block cold boot.
  - [ ] 0.2 Run `npm --prefix prototypes/sampling-spec-rnd/frontend run type-check` and `npm --prefix prototypes/sampling-spec-rnd/frontend run build` from repo root; both must exit 0 before §1 is opened.
  ```

  Whichever option is taken, the chosen approach must be encoded in the spec as a "Scenario: App module graph resolves" scenario added to `specs/advisory-browser-smoke/spec.md`.
- **Validation (post-implementation).** `Get-ChildItem prototypes/sampling-spec-rnd/frontend/src/pages -File` shows `SpecVersionPage.tsx` (option a) OR `Select-String -Path prototypes/sampling-spec-rnd/frontend/src/App.tsx -Pattern 'lazy\\(.*SpecVersionPage'` returns a line (option b). `tsc --noEmit` on the frontend reports `0` errors. `vite build` (the `npm run build` script) exits 0 and writes `dist/index.html` with at least the `<title>Sampling & Spec R&D</title>`.

### B2 (MEDIUM) — Selector strategy needs a stable contract on the "Connected" badge

- **Path/lines.** `prototypes/sampling-spec-rnd/frontend/src/App.tsx:147–162` (status badge); `App.tsx:161` (`{isConnected ? 'Connected' : 'Local Mode'}` inside `<span className="hidden sm:inline">`).
- **Criterion.** The plan's design §5 decision explicitly says: "Prefer accessible roles and user-visible semantic text over CSS selectors; keep assertions limited to stable contract-level behavior." Currently the badge has **no `data-testid`, no `role`, no `aria-live`**, and is conditionally hidden under `sm:` (Tailwind `>=640px`). Bare-text matching (`getByText('Connected')`) is fragile against future copy changes and brittle against mobile viewports. The proposal's `tests/smoke.spec.ts` placeholder is unspecified — must commit to a strategy.
- **Consequence.** A UI copy change "Connected" → "Online" silently breaks the smoke. A viewport change to mobile-default breaks the `sm:inline` visibility. A selector change to `getByRole('status')` requires an `aria-live` annotation that the prototype does not have today.
- **Minimum remedy.** Two acceptable choices; pick one and pin it in `tasks.md §1.4`:
  1. **App-level test attribute.** Add `data-testid="conn-status"` to the wrapper `div` at `App.tsx:155`. The smoke then targets `page.getByTestId('conn-status')` and matches its inner text. Smallest app change; minimal blast radius.
  2. **Locator with explicit match.** Use `await expect(page.getByText('Connected', { exact: true })).toBeVisible({ timeout: 15_000 })` and pin the test viewport to `{ width: 1280, height: 720 }` in the Playwright config so `hidden sm:inline` is always visible.

  In both cases, the `specs/advisory-browser-smoke/spec.md` Scenario "Dashboard reaches a healthy backend" should state the locator and timeout concretely, including the data-testid if option (1) is chosen.
- **Validation (post-implementation).** `Select-String -Path prototypes/sampling-spec-rnd/frontend/playwright.config.ts -Pattern 'viewport:'` shows a non-default viewport object. `Select-String -Path prototypes/sampling-spec-rnd/frontend/src/App.tsx -Pattern 'data-testid="conn-status"'` returns a line OR the spec file declares the text-exact match. `grep -n 'getByTestId\|getByText' prototypes/sampling-spec-rnd/frontend/tests/smoke.spec.ts` confirms the chosen path.

### B3 (MEDIUM) — Bounded timeouts must be quantifed in spec and config

- **Path/lines.** `openspec/changes/advisory-playwright-harness/tasks.md §1.2` ("bounded timeout"); `openspec/changes/advisory-playwright-harness/specs/advisory-browser-smoke/spec.md` Scenario "Dashboard reaches a healthy backend" (no timeout specified); `App.tsx:103–110` (initial `isConnected: false`; async `checkHealth()` flips to `true`).
- **Criterion.** Per <https://playwright.dev/docs/test-timeouts>: Playwright defaults are **30_000 ms** test timeout, **5_000 ms** `expect` timeout, **`navigationTimeout: 0`** (no default), **`globalTimeout: 0`** (no default). The plan needs to pin numerics or rely on defaults explicitly. A future contributor who changes defaults silently is a risk; an unstated timeout in `tests/smoke.spec.ts` is a non-deterministic contract.
- **Consequence.** Defaults may benchmark differently in CI vs local; a slow CI runner on the first run after backend startup may exceed the 5 s `expect` timeout and the smoke turns flaky. The plan's wording "bounded timeouts" is too soft for handoff.
- **Minimum remedy.** In `tasks.md §1.2`, state: `playwright.config.ts` declares `timeout: 60_000`, `expect: { timeout: 15_000 }`, `use: { navigationTimeout: 30_000 }`, `globalTimeout: 600_000`. In the test file, use `await expect(...).toBeVisible({ timeout: 15_000 })` on the dashboard heading and `await expect(...).toHaveText('Connected', { timeout: 15_000 })` on the badge. Pin `globalTimeout` so a hung service does not consume the GH runner for hours.
- **Validation (post-implementation).** `Select-String -Path prototypes/sampling-spec-rnd/frontend/playwright.config.ts -Pattern 'timeout:|expect:|globalTimeout'|navigationTimeout'` shows numeric values; `Select-String -Path prototypes/sampling-spec-rnd/frontend/tests/smoke.spec.ts -Pattern 'timeout:'` shows numeric values.

### B4 (MEDIUM) — `webServer` for both backend and frontend is the canonical pattern; commit to it explicitly

- **Path/lines.** `openspec/changes/advisory-playwright-harness/tasks.md §1.3` ("service startup for the FastAPI backend on port 8009 and Vite frontend on port 3009 without silently changing ports; return an actionable failure if either service cannot start"); `prototypes/sampling-spec-rnd/frontend/vite.config.ts:30–32` (`strictPort: true` on 3009); `prototypes/sampling-spec-rnd/backend/src/main.py:54` (`uvicorn.run(app, host="0.0.0.0", port=8009, reload=True)`); `prototypes/sampling-spec-rnd/frontend/.gitignore`.
- **Criterion.** Per <https://playwright.dev/docs/test-webserver>, Playwright supports a **`webServer` array** with `{ command, url, timeout, reuseExistingServer, cwd, env, name }` per entry. This is the runtime-mechanism supply chain: it waits for the `url` to return 2xx/3xx/400/401/402/403, fails fast on port collision, and integrates with `config.timeout` (default 60_000 ms). Without committing to this, the team will end up writing custom shell scripts whose race windows are not detectable in the Playwright HTML report.
- **Consequence.** A custom-script approach can pass `baseURL` while the Vite dev server is still serving an old error overlay (because the spec hits a URL that 200s but the page is mid-restart). The `webServer` built-in solves this by polling the URL until it returns a valid status code or a timeout fires. With `strictPort: true` already in `vite.config.ts`, the port-collision contract is already enforced upstream — Playwright must not undo that discipline.
- **Minimum remedy.** In `tasks.md §1.2`/`§1.3`, commit to: `playwright.config.ts` exports `webServer: [{ command: 'uvicorn src.main:app --port 8009', url: 'http://localhost:8009/api/sampling-spec-rnd/health', cwd: 'prototypes/sampling-spec-rnd/backend', name: 'Backend', timeout: 60_000, reuseExistingServer: !process.env.CI }, { command: 'npm run dev', url: 'http://localhost:3009', cwd: 'prototypes/sampling-spec-rnd/frontend', name: 'Frontend', timeout: 60_000, reuseExistingServer: !process.env.CI }]`. Add a precondition: backend dependencies are installed via the existing `prototype-sampling.yml backend-quality` job's `requirements-dev.txt`; the new advisory job must declare the same Python setup step (or share an existing runtime).
- **Validation (post-implementation).** `Select-String -Path prototypes/sampling-spec-rnd/frontend/playwright.config.ts -Pattern 'webServer:|reuseExistingServer'` returns multi-line matches; the array contains two entries with distinct `name:` values. `git grep -nE 'PORT=|--port' prototypes/sampling-spec-rnd/frontend/playwright.config.ts` returns **no matches** (no port override).

### B5 (MEDIUM) — Health endpoint contract: `/health` vs `/api/sampling-spec-rnd/health` and the no-`rewrite` proxy

- **Path/lines.** `prototypes/sampling-spec-rnd/frontend/src/services/api.ts:15` (`BASE = VITE_API_URL || '/api/sampling-spec-rnd'`); `api.ts:249` (`fetch(\`${BASE}/health\`)`); `prototypes/sampling-spec-rnd/frontend/vite.config.ts:32–37` (proxy `/api` → `http://localhost:8009`, `changeOrigin: true`, **no `rewrite`**); `prototypes/sampling-spec-rnd/backend/src/main.py:41–50` (two distinct routes at both `/health` and `/api/sampling-spec-rnd/health`); `backend/src/api/routes.py:316–321` (router-level `/health` returning `{status, module}`).
- **Criterion.** The current setup works because:
  1. Frontend fetch: `/api/sampling-spec-rnd/health`.
  2. Vite proxy: forwards the prefix as-is (no `rewrite`), so upstream receives `/api/sampling-spec-rnd/health`.
  3. Backend `main.py:47`: `@app.get("/api/sampling-spec-rnd/health")` matches.

  The router-level `/health` (line 316 of `routes.py`) returns `{status, module}`, **not** `{status, service}` — slight asymmetry between the two endpoints. The `webServer` smoke expecting a `url` 2xx status works either way, but if the smoke ever drifts to **asserting the body shape**, the staggered contract will trip it.
- **Consequence.** Test that asserts `await response.json()` against either backend endpoint must pick one. The plan's smoke is read-only and uses the React UI assertion ("Connected"), so the body shape mismatch is informational. But a future contributor extending the smoke to JSON-level assertion will likely pick the wrong route. Also: anyone changing the Vite proxy to add `rewrite: (path) => path.replace(/^\/api/, '')` (a common fix pattern) will break the upstream path because backend only registers the full `/api/sampling-spec-rnd/health` route, not `/sampling-spec-rnd/health` — the plan must protect the no-rewrite posture.
- **Minimum remedy.** In `specs/advisory-browser-smoke/spec.md`, note explicitly that the smoke asserts UI state and does NOT inspect `/health` body shape. Add a "Scenario: Health proxy preserves path" with a one-line comment in `tests/smoke.spec.ts`: `// Backend has two health routes (main.py:41 and main.py:47). The Vite proxy at vite.config.ts:32–37 does NOT use `rewrite`, so the full /api/sampling-spec-rnd/health segment is preserved on the upstream request. Do not add a `rewrite` rule without verifying both backend routes still match.`
- **Validation (post-implementation).** `Select-String -Path prototypes/sampling-spec-rnd/frontend/vite.config.ts -Pattern 'rewrite'` returns **no matches**. `Select-String -Path prototypes/sampling-spec-rnd/frontend/tests/smoke.spec.ts -Pattern 'api/sampling-spec-rnd/health|rewrite'` shows the comment.

### B6 (MEDIUM) — Lockfile + cache posture must match pre-existing pattern, but plan must add Node cache

- **Path/lines.** `openspec/changes/advisory-playwright-harness/tasks.md §1.1` (lockfile commit); `tasks.md §2.1` ("Node 20 plus the committed lockfile"); `.github/workflows/prototype-sampling.yml:27–28` (`actions/setup-node@v4` with `node-version: "20"`, **no `cache:` attribute**); `.github/workflows/prototype-sampling.yml:72` (`run: npm install`, latent).
- **Criterion.** Per existing repo pattern (`prototype-sampling.yml:38–39` uses `cache: "pip"` and `cache-dependency-path: ...` for the Python job), the new advisory job's `actions/setup-node@v4` step MUST declare `cache: "npm"` and `cache-dependency-path: prototypes/sampling-spec-rnd/frontend/package-lock.json` once §1.1 has committed the lockfile. Cross-reference S-1 F3: the new job uses `npm ci`, not `npm install`. Combining B6 + S-1 F3: the advisory job's install step is `npm ci`, and the cache is keyed on the same lockfile.
- **Consequence.** Without a cache, every CI run reinstalls Chromium (~150 MB) and npm dependencies (~80 MB). GH runner time per job rises from ~30 s to ~60 s, eating the team's CI-minute budget. With `npm ci` + npm cache correctly wired, repeat runs are < 20 s.
- **Minimum remedy.** In `tasks.md §2.1`, pin the install step shape:

  ```yaml
  - uses: actions/setup-node@v4
    with:
      node-version: '20'
      cache: 'npm'
      cache-dependency-path: prototypes/sampling-spec-rnd/frontend/package-lock.json

  - run: npm ci
  - run: npx playwright install --with-deps chromium
  ```

  Cross-reference: S-1 F3 (mandate `npm ci`) and S-1 F6 (action pins). Add a precondition: "§2 starts only after §1 has committed `prototypes/sampling-spec-rnd/frontend/package-lock.json`" — without the file, the cache key is invalid and `npm ci` fails loudly. Validation per S-1.
- **Validation (post-implementation).** `git ls-files | grep -E 'package-lock\.json$'` shows the lockfile in `prototypes/sampling-spec-rnd/frontend/`. `Select-String -Path .github/workflows/prototype-sampling.yml -Pattern "cache:\s*['\"]npm['\"]"` returns 1 line inside the new advisory job. `Select-String -Path .github/workflows/prototype-sampling.yml -Pattern 'npm ci'` returns 1 line inside the new advisory job.

### B7 (MEDIUM) — `tsc --noEmit` includes only `src/`, but plan must commit a separate tsconfig shape for tests/

- **Path/lines.** `prototypes/sampling-spec-rnd/frontend/tsconfig.json:36` (`include: ["src"]`); `prototypes/sampling-spec-rnd/frontend/tsconfig.app.json:10–11` (`include: ["src"]`, `exclude: ["node_modules", "dist"]`).
- **Criterion.** Plan §1.4 adds `tests/smoke.spec.ts` beside `src/`. The current `include` arrays do not pick up `tests/`. That is intentional (tests should not enter the app build), but Playwright itself does **not** compile the test files — `tsc` does, in a separate reality from the test runner. In Playwright, files in `tests/` are interpreted by Playwright's internal TS transpilation (esbuild-style), so a stray type crash in `smoke.spec.ts` will surface as a runtime TS error in Playwright, not as `tsc --noEmit` failure.
- **Consequence.** Tests can fail to load at runtime but `npm run type-check` does not see them; `npm run build` ignores them. The CI plan's §4.2 ("`npm run type-check`") will mistakenly report green while the smoke itself cannot start. The team discovers the failure only when §4.1 runs `npm run test:e2e`.
- **Minimum remedy.** Either explicitly produce a `tsconfig.tests.json` under `prototypes/sampling-spec-rnd/frontend/` that `extends: ./tsconfig.json` with `include: ["tests", "playwright.config.ts"]` (so editors see types) AND run `npx tsc --noEmit -p tsconfig.tests.json` from §4.2, OR confirm Playwright's runtime type enforcement and step §4.2 such that `npm run test:e2e` exit code is the truth authority. Pick one and record the choice in `tasks.md §1.4`. The smallest correct change is to rely on Playwright runtime and explicitly note that `npm run type-check` does not validate test files.
- **Validation (post-implementation).** `Test-Path prototypes/sampling-spec-rnd/frontend/tsconfig.tests.json` returns `True`, OR `tasks.md §4.2` contains the explicit note "type-check does not validate tests; rely on `npm run test:e2e` exit code".

### B8 (MEDIUM) — `playwright.config.ts` needs `testIgnore` for the prototype frontend's `.js`/`.jsx` files

- **Path/lines.** `prototypes/sampling-spec-rnd/frontend/src/components/SpecVersionTracker.jsx` (a JSX/JS file in `src/`); `prototypes/sampling-spec-rnd/frontend/src/utils/time-study-patterns.js` (JS file in `src/utils/`); `prototypes/sampling-spec-rnd/frontend/tsconfig.app.json:10–11` (`include: ["src"]`).
- **Criterion.** Playwright discovers test files in `testDir` (default `tests/` if not set). The plan adds `tests/smoke.spec.ts`, which is fine. But if a future contributor adds a `.spec.ts` to `src/utils/`, Playwright's default discovery `**/*.@(spec|test).?(c|m)[jt]s?(x)` would pick it up against `testDir`. The plan must commit to **explicit testDir + testMatch** so accidental imports don't run as tests.
- **Consequence.** A future contributor who adds `src/utils/foo.spec.ts` may unintentionally have it run as a Playwright test, with no `baseURL` available in that context, producing confusing failures.
- **Minimum remedy.** In `tasks.md §1.2`, declare: `testDir: 'tests'`, `testMatch: '**/*.spec.ts'`. State explicitly that files outside `tests/` are NOT test files. This is a small config change but locks behavior.
- **Validation (post-implementation).** `Select-String -Path prototypes/sampling-spec-rnd/frontend/playwright.config.ts -Pattern 'testDir:|testMatch:'` shows both keys.

### B9 (LOW) — Anchored `.gitignore` patterns must lead with `/`

- **Path/lines.** `prototypes/sampling-spec-rnd/frontend/.gitignore:1`–`40` (existing anchored patterns); `prototypes/sampling-spec-rnd/frontend/.gitignore:17` (`dist/` already anchored); `AGENTS.md` "Anchored Git Rules".
- **Criterion.** AGENTS.md mandates: "Always anchor folder ignore patterns in `.gitignore` with a leading slash (e.g., `/artifacts/`, `/build/`)." Playwright's default output directories are `playwright-report/`, `test-results/`, `blob-report/`, and `playwright/.cache/`. Plan §1.5 must commit to anchored entries to be consistent with the existing pattern and AGENTS.md.
- **Consequence.** Without leading `/`, the patterns would also match nested folders anywhere in the repo (e.g., `backend/node_modules/playwright-report/` — non-existent today, but a future contributor might trip on it).
- **Minimum remedy.** In `tasks.md §1.5`, enumerate exactly: `/playwright-report/`, `/test-results/`, `/blob-report/`, `/playwright/.cache/`. Add the lines with leading `/`.
- **Validation (post-implementation).** `Select-String -Path prototypes/sampling-spec-rnd/frontend/.gitignore -Pattern '^/(playwright-report|test-results|blob-report|playwright/\\.cache)/?$'` returns 4 lines.

### B10 (LOW) — Plan does not yet require a `viewport: { width: 1280, height: 720 }` pin

- **Path/lines.** `openspec/changes/advisory-playwright-harness/tasks.md §1.2` (Chromium project declaration); `prototypes/sampling-spec-rnd/frontend/src/App.tsx:161` (`<span className="hidden sm:inline">Connected</span>`); `App.tsx:147–150` (Tailwind `sm:bg-green-100` etc.).
- **Criterion.** `<span className="hidden sm:inline">` follows Tailwind's `sm:` breakpoint (min-width 640 px). Playwright default viewport is 1280×720, which is >= 640 px, so the text is visible at default — but a future contributor running tests with an iPhone-style viewport (375×667) loses the text entirely, and `getByText('Connected')` returns an empty locator set, then toHaveText times out. Plan should pin a viewport explicitly.
- **Consequence.** A change from the implicit default to a parameterized viewport (e.g., for mobile coverage extension later) silently rewrites the connected-badge visibility contract. The smoke becomes brittle.
- **Minimum remedy.** In `tasks.md §1.2`, declare: `use: { viewport: { width: 1280, height: 720 } }`. Lock the desktop viewport as the smoke baseline; mobile viewport is out of scope per design §4 (no cross-browser / mobile matrix).
- **Validation (post-implementation).** `Select-String -Path prototypes/sampling-pattern-rnd/frontend/playwright.config.ts -Pattern 'viewport:'` — corrected: `Select-String -Path prototypes/sampling-spec-rnd/frontend/playwright.config.ts -Pattern 'viewport:'` shows an object literal with width and height keys.

### B11 (LOW) — Fasting audit: pre-existing `frontend-quality` job uses `npm install`

- **Path/lines.** `.github/workflows/prototype-sampling.yml:55` (`run: npm run type-check`); `prototype-sampling.yml:72` (`run: npm install` — actually `line:72` per `Select-String` numbered output); `prototype-sampling.yml:43` per the visible line in the policy context — minor conflict across tools; settle for the tool's reported line `prototype-sampling.yml:72`.
- **Criterion.** This is a pre-existing posture: `run: npm install` runs lifecycle scripts. Per S-1 F3, the **new** advisory job must use `npm ci` (no lifecycle scripts) and a committed lockfile. The `frontend-quality` job using `npm install` is a pre-existing latent posture; out of scope, but worth noting because §2.2's "Install the required Chromium browser and start the backend/frontend services deterministically" implies determinism end-to-end.
- **Consequence.** If a future contributor correlates "the existing advisory job uses `npm install`" with "this is the established pattern", they may relax the new job back to `npm install`. Out of scope for THIS change.
- **Minimum remedy.** None for this change. Document the boundary in `specs/advisory-browser-smoke/spec.md` Notes: "Pre-existing `frontend-quality` job's install posture is out of scope for the advisory harness."
- **Validation.** N/A (out of scope).

### B12 (LOW-INFORMATIONAL) — Stale `run_frontend.bat` is not blocking per design §3, but worth a note

- **Path/lines.** `prototypes/sampling-spec-rnd/frontend/run_frontend.bat:8–12` (advertises port `3007` and `localhost:8007`); `prototypes/sampling-spec-rnd/frontend/vite.config.ts` (actually `3009` and `8009`).
- **Criterion.** The plan's design §3 explicitly says: "Any stale documentation or scripts are outside this change unless startup verification proves they prevent the harness from running." Since `run_frontend.bat` is a developer convenience script and is not used by `npm run dev`, it is out of scope. Recorded as informational only because semantics overlap with B5 (port discipline).
- **Consequence.** None for the new smoke.
- **Minimum remedy.** None. Optional: a follow-up docs change can update `run_frontend.bat` to reflect the current ports (3009/8009), but this is *not* required by this change.
- **Validation.** N/A (informational).

### Cross-reference to S-1 findings

- **S-1 F1 (pull_request only / no `pull_request_target`)**: not contradicted; the behavioral lens is downstream of trigger posture. The new advisory job runs only when triggered; if it runs, the smoke assertions are governed by B1–B12.
- **S-1 F3 (`npm ci`/no `npm install`)**: reinforced by B6; the new job's install is `npm ci` keyed on the committed lockfile backed by `cache: 'npm'`.
- **S-1 F4 (trace scope off by default)**: not contradicted; no behavioral side effect when traces are absent. Defaults per Playwright docs are already off.
- **S-1 F5 (startup command not pinned)**: tightened by B4; the canonical `webServer` array commit fixes the contract.
- **S-1 F6 (action pins)**: not contradicted; no overlap.
- **S-1 F7 (`headless: true`)**: not contradicted; default for `chromium` project in `playwright.config.ts` is headless, but explicit pinning is recommended for handoff. Add this to `tasks.md §1.2` as a one-line note: `use: { headless: true, ... }`.

## Limits and Assignment Mismatch

### Scope limits (intentional, not gaps)

- **The dashboard component ("Sampling & Spec R&D" cards, summary numbers):** unknown whether they ship tenant identifiers in initial state. The smoke asserts only the dashboard `<h2>` heading and the Connected badge text — the data cards are not read. **UNKNOWN.**
- **The `SpecVersionPage` placeholder choice (stub vs. lazy-import):** not decided; recorded as B1's minimum-remedy. Implementation owner chooses.
- **CI use of `pip` cache `cache-dependency-path`**: unchanged from S-1 F3.
- **Repository-wide secret scan, signup/free-fork policy, organization-level settings:** out of scope; S-1 covers the security seam.
- **Self-hosted runners:** repo uses `ubuntu-latest` GH-hosted. Not applicable.

### Evidence limits

- I did NOT execute `npm ci`, `npx playwright install`, nor any browser launch or HTTP probe. The brief forbids installs/servers.
- I did NOT run `tsc --noEmit` on the frontend because `node_modules/` is not installed; verification is by file inspection only.
- I did NOT execute `vite build`; behavior is verified through official docs and direct file state.
- I did NOT modify `openspec validate`; the spec is reviewed as a reading artifact and used as the source of truth for validation commands.
- I did NOT exercise `playwright.dev/docs/ci`; only `playwright.dev/docs/test-webserver` and `/docs/test-timeouts` were fetched (see Worklog).

### Assignment Mismatch

None. All scope was honored. The brief mentions "active change artifacts path `openspec/changes/advisory-playwright-harness/artifacts/`" as a contextual note — I respected the read-only exception there. The only file written is `openspec/changes/advisory-playwright-harness/reviews/specialist-b-001.md`. No source files, no workflow files, no prototype files, and no other OpenSpec changes, including this change's `artifacts/`, were modified. (Cross-check of artifacts dir: I confirmed the prior `git status` glyph `?? ` for the change, not a working-tree dirty mid-merge.)

### UNKNOWNs — explicit

- Whether the prototype frontend's dashboard component renders tenant identifiers (`tenant_id`, etc.) in initial state — **UNKNOWN** (not opened in detail).
- Whether the Vite dev server, when started in CI cold, will prebundle the missing module and either fail-fast or hang — **UNKNOWN** empirically; docs cover both branches. Validation approach uses `npm run build` (Rollup) and `npm run type-check`, both of which have unambiguous failure modes for unresolved modules.
- Whether `reuseExistingServer: !process.env.CI` pattern collides with `continue-on-error: true` semantics (false-positive failures from collision with a parallel job's lingering dev server) — design risk only. Validation: design §1 commit to `!process.env.CI` is irreducible.
- Whether the `Connected`/`Local Mode` badge text is ever translated at runtime — **UNKNOWN**; not in source. (Plan §1.4 should anchor on text or `data-testid`, B2.)
- Whether Playwright strictly requires a separate Python venv for the backend `webServer` — repo's `backend/.gitignore` would tell. Not opened.
- Whether the existing `frontend-quality` job's `npm install` currently works or has been hidden by `continue-on-error: true` — **UNKNOWN**; the prototype-sampling.yml declares `continue-on-error: true`, so a runtime failure of the existing job is silently absorbed. Out of scope.
- Whether `microsoft/playwright-github-action` references persist in any docs path — **UNKNOWN**; S-1 F6 covers the action pinning and rejects the deprecated wrapper.

### Pre-existing conditions (NOT introduced by this plan; flagged for awareness, not remediation in this change)

- `App.tsx:8` `import SpecVersionPage from '@/pages/SpecVersionPage'` does not resolve. **Pre-existing static-import bug** in the prototype; B1 records the impact on the new harness.
- `.github/workflows/prototype-sampling.yml:72` `run: npm install` (lifecycle scripts). **Pre-existing.** S-1 F3 mentions; B6 reinforces for the new job.
- `prototypes/sampling-spec-rnd/frontend/run_frontend.bat` advertises port `3007` and `8007`, but the actual `vite.config.ts` and `main.py` use `3009` and `8009`. **Pre-existing stale developer script.** Out of scope (design §3); B12 records as informational.

## Worklog

### Sources fetched and used

- Vite Troubleshooting — <https://vite.dev/guide/troubleshooting.html>. **OK.** Verified case-sensitivity note ("Module not found" diagnostic) and that Vite serves dev server. Used for B1, B5.
- Rollup Troubleshooting — <https://rollupjs.org/troubleshooting/>. **OK.** Verified "is not exported by [module]" diagnostic; cross-confirms module-resolution failure. Used for B1 (build-time path).
- Playwright Web server — <https://playwright.dev/docs/test-webserver>. **OK.** Verified `webServer` array shape, `command`/`url`/`timeout`/`reuseExistingServer`/`cwd`/`env`/`name` schema, default 60_000 ms startup timeout, and that 2xx/3xx/400/401/402/403 are considered "ready". Used for B4, B7.
- Playwright Timeouts — <https://playwright.dev/docs/test-timeouts>. **OK.** Verified defaults: 30_000 ms test, 5_000 ms expect, no defaults for navigation/global. Used for B3.
- AGENTS.md in-repo root — read in full. **OK.** Used for B9 (anchored gitignore rule).
- `playwright.dev/docs/ci` — NOT fetched (S-1 cited; trusted via cross-reference).
- `playwright.dev/docs/api/class-testconfig` — NOT fetched; defaults cross-referenced via the doc URL above.

### Sources attempted; partial / failure

- Local semantic-search index — used. Index returned relevant hits for SpecVersionTracker.jsx, App.tsx, services/api.ts. **OK.** Cross-verified with `Select-String`/`Get-ChildItem` to confirm physical file presence.
- Local `npm`/`node` CLI versions — NOT probed. The plan's Node 20 follow-on is recorded but not asserted without measurement (per scope). Runtime measurement deferred to implementation.

### Repository reads (no edits performed)

- `openspec/changes/advisory-playwright-harness/proposal.md` lines 1–200 — OK
- `openspec/changes/advisory-playwright-harness/design.md` lines 1–400 — OK
- `openspec/changes/advisory-playwright-harness/tasks.md` lines 1–400 — OK
- `openspec/changes/advisory-playwright-harness/.openspec.yaml` lines 1–200 — OK
- `openspec/changes/advisory-playwright-harness/specs/advisory-browser-smoke/spec.md` lines 1–200 — OK
- `openspec/changes/advisory-playwright-harness/specs/agent-browser-verification/spec.md` lines 1–200 — OK
- `openspec/changes/advisory-playwright-harness/reviews/specialist-s-001.md` lines 1–400 — OK (cross-reference)
- `.github/workflows/ci.yml` lines 1–300 — OK
- `.github/workflows/prototype-sampling.yml` lines 1–300 — OK
- `.github/pull_request_template.md` lines 1–200 — OK
- `AGENTS.md` lines 1–120 — OK
- `prototypes/sampling-spec-rnd/frontend/package.json` lines 1–120 — OK
- `prototypes/sampling-spec-rnd/frontend/vite.config.ts` lines 1–60 — OK
- `prototypes/sampling-spec-rnd/frontend/index.html` lines 1–20 — OK
- `prototypes/sampling-spec-rnd/frontend/tsconfig.json` lines 1–40 — OK
- `prototypes/sampling-spec-rnd/frontend/tsconfig.app.json` lines 1–20 — OK
- `prototypes/sampling-spec-rnd/frontend/.gitignore` lines 1–60 — OK
- `prototypes/sampling-spec-rnd/frontend/src/main.tsx` lines 1–20 — OK
- `prototypes/sampling-spec-rnd/frontend/src/App.tsx` lines 1–186 — OK
- `prototypes/sampling-spec-rnd/frontend/src/services/api.ts` lines 1–60, 244–261 — OK
- `prototypes/sampling-spec-rnd/frontend/src/pages/index.ts` lines 1–1 — OK
- `prototypes/sampling-spec-rnd/frontend/src/pages/` directory listing — OK
- `prototypes/sampling-spec-rnd/frontend/run_frontend.bat` lines 1–20 — OK
- `prototypes/sampling-spec-rnd/backend/run_backend.bat` lines 1–20 — OK
- `prototypes/sampling-spec-rnd/backend/src/main.py` lines 1–60 — OK
- `prototypes/sampling-spec-rnd/backend/src/api/routes.py` lines 316–321 — OK
- `scripts/check_workspace_hygiene.py` lines 1–50 — OK

### Commands run (read-only, no installs, no servers)

- `Get-ChildItem openspec/changes/advisory-playwright-harness -Recurse -Force` — subject inventory captured.
- `Get-ChildItem -Force | Select-Object Name` — repo root listing (after first attempt was rate-limited; second attempt produced via `cmd /c dir /s /b`).
- `Get-ChildItem prototypes/sampling-spec-rnd/frontend -Force` — frontend inventory.
- `Get-ChildItem prototypes/sampling-spec-rnd/frontend/src/pages -Recurse -Force` — pages/ listing.
- `Test-Path prototypes/sampling-spec-rnd/frontend/playwright.config.ts` — `False`.
- `Test-Path prototypes/sampling-spec-rnd/frontend/package-lock.json` — `False`.
- `Test-Path prototypes/sampling-spec-rnd/frontend/tests` — `False`.
- `Test-Path prototypes/sampling-spec-rnd/frontend/tests/tsconfig.tests.json` — `False`.
- `Get-ChildItem -Recurse prototypes/sampling-spec-rnd -Filter 'playwright.config*'` — empty (no pre-existing Playwright config).
- `Get-ChildItem -Recurse prototypes/sampling-spec-rnd -Filter '*SpecVersionPage*'` — **only `components/SpecVersionTracker.jsx`**; no `pages/SpecVersionPage*` file.
- `Get-ChildItem -Recurse prototypes/sampling-spec-rnd/frontend/src -File -Include *.ts,*.tsx | Select-Object Name -Unique | Sort-Object` — TS/TSX inventory (15 files; `pages/` only contributes `TimeStudyPage.tsx`).
- `Select-String -Path 'AGENTS.md' -Pattern 'browser|playwright|Playwright|open_browser_page|smoke'` — already not present in `AGENTS.md`. Confirms §3.1 is a net-new rule.
- `Select-String -Path .github/workflows/prototype-sampling.yml -Pattern 'cache|npm ci|npm install'` — `npm install` match on row lines 38, 39, 43, 72 (each pin reproducible via `git grep -n`).

### Verification tripwire for B1 (recap, per brief)

The hypothesis "SpecVersionPage import could fail entire app before dashboard" is supported by direct evidence without running install/server:
- Static `import` line in `App.tsx:8` (read).
- Empty resolved file path under `src/pages/` (physical directory check).
- Failing path resolution will trip `tsc --noEmit` (TS2307) and `vite build` (`RollupError: Could not resolve`) per Vite/Rollup official docs.

Validation commands for the implementer (recorded; **not** run by this reviewer):

```bash
# from repo root (assumes node_modules installed first)
cd prototypes/sampling-spec-rnd/frontend
npm run type-check     # expect exit 0 after B1's §0 fix
npm run build          # expect exit 0 and dist/index.html written
```

The reviewer did **not** run a server. `vite dev` behavior on the broken import is recorded via doc reference (Vite Troubleshooting case sensitivity note and Rollup "is not exported by [module]") — both are consistent with a HMR error overlay / 500 response, but **the reviewer did NOT observe** that behavior empirically. Implementation owner should validate.
