# Review — specialist C-001 (Changeability)

- **Review identity:** advisory-playwright-plan-review-001
- **Specialist instance:** C-1 (Changeability), single instance
- **Subject (frozen):** `openspec/changes/advisory-playwright-harness/{proposal.md,design.md,tasks.md,specs/**}`
- **Stage:** pre-implementation plan, review-only
- **Branch:** `feat/payroll-bonus-pool` @ `d37f6a3` (untracked change folder)
- **Dispatched routes:** Changeability (`module-responsibility`, `interface-contract`, `seam-adapter`, `dependency-shape`, `architecture-refactor`, `teammate-safety`)
- **Not dispatched:** Security, Behavioral — out of route per brief and frozen subject.

## Role

Review the Playwright harness plan as a Changeability specialist. Confirm the proposal produces one smallest, deterministic, repository-consistent executable handoff that does not violate the existing seam topology (frontend ↔ backend ↔ CI ↔ governance). Identify any change that would silently drift critical seams, force a second install path, or hide a wrong-service attachment. **No source edits, no installs, no test runs.**

## Status

`COMPLETE` for Changeability coverage based on actual current files and current Playwright docs.

- `openspec validate advisory-playwright-harness --strict` → **valid** (no schema or task structural errors).
- Evidence sufficient for findings F-C1-001 through F-C1-010.
- No execution warnings; all evidence paths verified.

## Evidence Checked

**Files inspected (read-only):**

- `openspec/changes/advisory-playwright-harness/proposal.md` (50 lines) — confirms "no write workflow, no auth, no cross-browser, advisory only, ports 3009/8009".
- `openspec/changes/advisory-playwright-harness/design.md` (90 lines) — Decisions §1–§6, risks table, Open Questions empty.
- `openspec/changes/advisory-playwright-harness/tasks.md` (33 lines) — §1 package, §2 advisory CI, §3 governance, §4 verification.
- `openspec/changes/advisory-playwright-harness/specs/advisory-browser-smoke/spec.md` (Scenario: dashboard reaches a healthy backend; smoke does not mutate state; CI remains non-blocking).
- `openspec/changes/advisory-playwright-harness/specs/agent-browser-verification/spec.md` (preference rule + honest-evidence rule).
- `openspec/changes/advisory-playwright-harness/.openspec.yaml` — `created: 2026-10-14`, schema `spec-driven`.

**Repository state at HEAD `d37f6a3`:**

- `prototypes/sampling-spec-rnd/frontend/package.json` — has `dev/build/preview/type-check/lint`; **no `test:e2e`**, **no `@playwright/test`**, **no Jest/Vitest**. Lint scope is `eslint src --ext .ts,.tsx`. Build is `tsc && vite build`. `type-check` is `tsc --noEmit`.
- `prototypes/sampling-spec-rnd/frontend/.gitignore` — has `node_modules/`, `coverage/`, `dist/`, `build/`, `.env*`, `.eslintcache`. **Missing** anchored `/test-results/`, `/playwright-report/`, `/blob-report/`, `/playwright/.cache/`.
- `prototypes/sampling-spec-rnd/frontend/tsconfig.json` — `include: ["src"]` only; `paths` for `@/*` etc. defined.
- `prototypes/sampling-spec-rnd/frontend/tsconfig.app.json` — `include: ["src"]`, `exclude: ["node_modules","dist"]`, `noEmit: true`. **Therefore `playwright.config.ts` at frontend root is NOT type-checked** by the application build.
- `prototypes/sampling-spec-rnd/frontend/vite.config.ts` — `server.port: 3009`, `server.strictPort: true`, `proxy: '/api' → http://localhost:8009`.
- `prototypes/sampling-spec-rnd/frontend/index.html` — `<title>Sampling & Spec R&D</title>`.
- `prototypes/sampling-spec-rnd/frontend/run_frontend.bat` — claims **port 3007/8007** (DRIFT vs. `vite.config.ts`).
- `prototypes/sampling-spec-rnd/backend/run_backend.bat` — port 8009 (consistent).
- `prototypes/sampling-spec-rnd/backend/src/main.py` — exposes `GET /api/sampling-spec-rnd/health` returning `{"status":"healthy","service":"sampling-spec-rnd-api"}`. CORS allows `localhost:3009` and `localhost:3007`.
- `prototypes/sampling-spec-rnd/frontend/src/App.tsx` — imports `SpecVersionPage from '@/pages/SpecVersionPage'`; **`pages/SpecVersionPage.tsx` does NOT exist** (`Select-String` over the entire `prototypes/sampling-spec-rnd/frontend` returned **zero** matches for either `SpecVersionPage` or `SpecVersionTracker` — see Extraction failures).
- `prototypes/sampling-spec-rnd/frontend/src/pages/index.ts` re-exports only `TimeStudyPage`. Only `TimeStudyPage.tsx`, `SpecVersionTracker.jsx` (components), and `index.ts` exist.
- `prototypes/sampling-spec-rnd/frontend/src/App.tsx` Connection indicator: `<span className="hidden sm:inline">{isConnected ? 'Connected' : 'Local Mode'}</span>` — **visible only at `sm:` (≥ 640 px) Tailwind breakpoint**. (Default Playwright `Desktop Chrome` viewport is 1280×720 — would show; safe by default but frangible under smaller viewports.)
- `prototypes/sampling-spec-rnd/frontend/src/App.tsx` Dashboard heading: `<h2 className="text-3xl font-bold mb-2 text-gray-900">Sampling &amp; Spec R&amp;D</h2>` (visible at any viewport).
- `.github/workflows/ci.yml` — workspace-hygiene + contract-validation + payroll-engine-quality (Python only; not relevant).
- `.github/workflows/prototype-sampling.yml` — `backend-quality` (Python/Ruff/Mypy) and `frontend-quality` (Node 20, **uses `npm install`**, `npm run type-check`, `npm run lint`); both `continue-on-error: true`. **Path trigger:** `prototypes/sampling-spec-rnd/**`.
- `.github/pull_request_template.md` — type-of-change + hygiene checklist; **no browser-evidence item**.
- `AGENTS.md` (root) — Root & Sandbox Isolation, anchored ignore rules required, workspace-hygiene gate (`scripts/check_workspace_hygiene.py`).
- `scripts/check_workspace_hygiene.py` — whitelists root dirs; `frontend/` is whitelisted but absent at repo root; `prototypes/` is whitelisted; no `playwright.config.*` would be added at root.
- `.gitignore` — no Playwright output patterns at root level; mirrors `/build/`, `/artifacts/` style.

**External sources (web) cited:**

- Playwright official docs — `https://playwright.dev/docs/test-webserver` — Multiple web servers section (`webServer: [{...},{...}]` array form, per-project `name`, `timeout`, `reuseExistingServer`, `url`, `wait`). `reuseExistingServer` documented as "If true, it will re-use an existing server on the port or url when available" with no body verification.
- Playwright official docs — `https://playwright.dev/docs/api/class-testconfig` — `reuseExistingServer: !process.env.CI` is the CI-safe idiom.
- Playwright official docs — `https://playwright.dev/docs/ci` — cache `~/.cache/ms-playwright` keyed by Playwright version; `npm ci`; `npx playwright install --with-deps`.
- Playwright official docs — `https://playwright.dev/docs/test-global-setup-teardown` — for multiple services that need ordered startup.
- npm — `@playwright/test` latest stable `1.64.0`.
- Microsoft Playwright GitHub issue #29273 — historical discussion of multiple webServer config that confirms the array form is the canonical path.

**Environment fingerprint:**

- Windows path: `C:\Projects\hackathon-MAIN-alkademi`
- `openspec 1.6.0`
- Node `v24.11.0`
- npm `11.18.0`
- Python `3.11.4`
- git `2.47.0.windows.2`
- PowerShell (pwsh) terminal
- Working tree: `git status` shows only `?? openspec/changes/advisory-playwright-harness/`.
- HEAD: `d37f6a3` on `feat/payroll-bonus-pool`. `origin/master` at `42b3ed1`.

**Extraction failures / open evidence requests:**

- **Resolved:** `Select-String`-style search for `SpecVersionPage` across the prototype frontend returned **zero hits** — confirmed by literal filesystem inspection of `pages/`. Only `SpecVersionTracker.jsx` exists as a component, never imported. The current `App.tsx` import is unresolvable.
- **Not measured (read-only):** Final Playwright-cache hit rate; exact binary download behavior in this CI; whether `pip install pip-audit` is rejected — none required for plan-only review.

## Findings

Severity in this review is **reviewer classification**, used by the Review Orchestrator only. The Review Orchestrator retains authority for the official verdict.

---

### F-C1-001 — Frontend currently imports an unresolvable `@/pages/SpecVersionPage`; the smoke cannot start

- **Path / lines:** `prototypes/sampling-spec-rnd/frontend/src/App.tsx` line ~6 import; `prototypes/sampling-spec-rnd/frontend/src/pages/` directory listing.
- **Criterion:** `seam-adapter` (playwright ↔ Vite) AND `module-responsibility` (frontend-owned harness). The plan claims "Start the frontend through Playwright or an equivalent CI-safe service lifecycle" (design.md Decision #1) but does not address whether the frontend even compiles today.
- **Consequence:** `vite dev` uses esbuild for per-file transpile; an unresolvable static import (`import SpecVersionPage from '@/pages/SpecVersionPage'` with no `pages/SpecVersionPage.tsx`) blocks the entire dev server from serving the index page. The Playwright smoke's `page.goto('/')` will fail with a 500 or a connection-refused; the test never reaches the assertion. Acceptance criterion **"the harness can be run with one command"** is unmet on the current repository state.
- **Conflict with the proposal:** design.md Non-Goals says "Do not modify application behavior, API contracts, `ci.yml`, or existing quality jobs" — fixing the import is technically application behavior. The proposal is therefore self-blocked.
- **Precise minimum change (one of the following):**
  1. Add a minimal stub at `prototypes/sampling-spec-rnd/frontend/src/pages/SpecVersionPage.tsx` exporting a one-liner component (`export default function SpecVersionPage() { return <div>TBD</div>; }`). This is not a behavior change to existing pages — it makes an import unresolvable-but-empty and is the smallest seam repair. The proposal must explicitly carve this out as in-scope and label it "stub only, not feature work" so it can be deleted by the Spec-version fix change later.
  2. **Or** amend the smoke spec Scenario to `BLOCKED: SpecVersionPage import is unresolvable; smoke relies on Vite dev startup which currently fails` and defer the executable handoff to a separate change.
- **Validation:** Run `npx tsc --noEmit -p prototypes/sampling-spec-rnd/frontend/tsconfig.app.json` locally and `npm run dev` (in CI Linux) and confirm both succeed before declaring the smoke runnable. (This is the Apply Change step, not the review step. The reviewer's job is to flag.)

---

### F-C1-002 — `reuseExistingServer` semantics NOT specified in the plan; trap from brief confirmed real

- **Path / lines:** `openspec/changes/advisory-playwright-harness/tasks.md` §1.2, §1.3; `openspec/changes/advisory-playwright-harness/design.md` Decision #1.
- **Criterion:** `interface-contract` AND `seam-adapter`. Playwright official docs (`https://playwright.dev/docs/api/class-testconfig`) document `reuseExistingServer` as: **"If true, it will re-use an existing server on the port or url when available. If no server is running on that port or url, it will run the command…"** — no content/body verification.
- **Consequence:** A developer who has any prior process bound to port 3009 (stale `npm run dev`, `vite preview --port 3009`, a debug session, a different frontend) would have Playwright silently attach to whichever process responded first. Playwright then runs against an unexpected app, producing false green. Same trap on the backend `url` `http://127.0.0.1:8009` if anything else is bound; the proposal's read-only smoke cannot distinguish backend identity from "any 200 at that URL".
- **Precise minimum change:**
  1. In `playwright.config.ts`, set `reuseExistingServer: !process.env.CI` (the docs-recommended CI-safe idiom).
  2. Make the backend `webServer.url` **specific to its service identity**: `http://127.0.0.1:8009/api/sampling-spec-rnd/health` rather than `http://127.0.0.1:8009`. Playwright probes that URL and accepts any 2xx/3xx/4xx (per docs); the path filter reduces accidental binding and the HTTP body assertion in the test disambiguates identity.
  3. Add a distinct `name: 'backend'` and `name: 'frontend'` to each webServer entry so logs and the array form are unambiguous.
- **Validation:** Apply the config; in a dev environment where `python -m http.server 8009` is already running, run `npx playwright test --project=chromium` and confirm the test is `BLOCKED` with an identity-failure assertion rather than silently green. Document this exact preflight recipe in `design.md` Risks.

---

### F-C1-003 — Two install paths in the same prototype CI workflow; `npm install` will mutate the new `package-lock.json`

- **Path / lines:** `openspec/changes/advisory-playwright-harness/tasks.md` §1.1; `.github/workflows/prototype-sampling.yml` `frontend-quality` step "Install Dependencies: run: npm install".
- **Criterion:** `dependency-shape` AND `teammate-safety`. AGENTS.md §Anchored Git Rules requires anchored ignores; AGENTS.md §Pre-Archive Gate requires "Configuration Drift … match the single source of truth". Plan mandates committing `package-lock.json` for reproducibility, but the existing advisory CI uses `npm install` which writes back to the lockfile on every CI run.
- **Consequence:** First time the `frontend-quality` job runs after this change lands, `npm install` will rewrite `prototypes/sampling-spec-rnd/frontend/package-lock.json` (likely adding transitive `@playwright/*` resolution bookkeeping or hoisting new entries). The next CI run will see a dirty working tree and a misleading diff against master — false collaborator-safety signal.
- **Precise minimum change:** Change the existing `prototype-sampling.yml` `frontend-quality` step from `npm install` to `npm ci` (one-line edit), aligned with the new advisory Playwright job. This is a contained edit to one workflow file already touched by the change scope.
- **Validation:** Apply; confirm `git status` after a CI run shows no lockfile drift; confirm `npm ci` succeeds against committed `package-lock.json` (`Lockfile invalid` errors become blocking).

---

### F-C1-004 — Connection-indicator text "Connected" is hidden below the `sm:` Tailwind breakpoint; the assertion can flake on narrow viewports

- **Path / lines:** `prototypes/sampling-spec-rnd/frontend/src/App.tsx` `<span className="hidden sm:inline">{isConnected ? 'Connected' : 'Local Mode'}</span>`.
- **Criterion:** `interface-contract`. Plan says "observes the `Connected` status" (`specs/advisory-browser-smoke/spec.md`).
- **Consequence:** Tailwind `sm:` = 640 px. Default Playwright `Desktop Chrome` device is 1280×720 (visible), but a CI runner configured for `--browser=chromium` without an explicit device can use a smaller default viewport, and any future developer adding a smaller device project (e.g., mobile matrix) would silently fail this assertion. The plan's spec is phrased as if the indicator is universally visible.
- **Precise minimum change:** In `playwright.config.ts` under `projects[chromium].use`, set `viewport: { width: 1280, height: 720 }` explicitly, OR add `test.use({ viewport: ... })` inside `smoke.spec.ts`. Document the viewport lock in the spec Scenario as part of the contract.
- **Validation:** Add a deliberately-narrow project (e.g., 600×800) on a feature branch; the smoke must remain deterministically green or the test must be marked project-disabled, not silently fail.

---

### F-C1-005 — Workflow file placement is ambiguous; the plan conflicts with itself on editing an existing workflow

- **Path / lines:** `openspec/changes/advisory-playwright-harness/tasks.md` §2.1 ("`.github/workflows/prototype-sampling.yml` OR a dedicated prototype E2E workflow"); `openspec/changes/advisory-playwright-harness/design.md` Decisions #4 ("separate or clearly isolated and advisory").
- **Criterion:** `architecture-refactor` AND `teammate-safety`. Choosing "edit `prototype-sampling.yml`" mutates an existing workflow; choosing "new file" creates a new workflow. Each has a different rollback shape per design.md §Migration Plan #4. The plan cannot be reviewed without picking one.
- **Consequence:** Reviewer cannot confirm whether the change adds `paths: 'prototypes/sampling-spec-rnd/**'` triggers (already present in the existing workflow) or narrower `prototypes/sampling-spec-rnd/frontend/**` triggers. Two reviewers could interpret the same plan and review different surface area.
- **Precise minimum change:** Pick **exactly one** path. Recommended: a new dedicated workflow `.github/workflows/prototype-e2e.yml`. Rationale:
  - preserves the existing `prototype-sampling.yml` untouched (Non-Goals already says don't change it);
  - narrower path trigger (`prototypes/sampling-spec-rnd/frontend/**` plus the workflow file) avoids triggering on backend-only PRs;
  - separate cache key and Playwright-version pin keep the install graph from contaminating `frontend-quality` Node 20 cache;
  - rollback per Migration Plan becomes "delete the file and revert governance text only", no executive of `prototype-sampling.yml` needed.
- **Validation:** Apply the new workflow with `paths` set; on a dummy PR touching only `backend/payroll-costing/**`, confirm the E2E workflow does **not** trigger and `prototype-sampling.yml` does.

---

### F-C1-006 — `@playwright/test` is not pinned to a version range in the plan; reproducibility requires both lockfile AND caret-pin

- **Path / lines:** `openspec/changes/advisory-playwright-harness/tasks.md` §1.1 (only "Add `@playwright/test` as a development dependency").
- **Criterion:** `dependency-shape`. Latest stable `@playwright/test` is `1.64.0` (npm registry). Plan does not specify a `^X.Y.Z` pin.
- **Consequence:** With only the lockfile pinning (no package.json range), an `npm install` later on a clean clone will install whatever range was committed — and if the lockfile regeneration happens (see F-C1-003), the resolved version drifts. The plan's CI determinism is then a single source of truth (lockfile alone) that fails the AGENTS.md Configuration Drift rule.
- **Precise minimum change:** In `package.json` `devDependencies`, add `@playwright/test` with caret pin matching the latest stable at the time of authoring, e.g. `"@playwright/test": "^1.64.0"`. Document the pin rationale (latest stable; LTS track) in design.md Decision §1.
- **Validation:** Apply; force-regenerate the lockfile locally (`rm package-lock.json && npm install`); confirm the resolved version is inside the caret range; commit and re-check `npm ci` succeeds.

---

### F-C1-007 — Plan does not mandate the canonical `webServer: []` array form for two services; ownership collision is the explicit brief trap

- **Path / lines:** `openspec/changes/advisory-playwright-harness/tasks.md` §1.3; `openspec/changes/advisory-playwright-harness/design.md` Decision #1.
- **Criterion:** `seam-adapter` AND `teammate-safety`. Brief explicitly flagged "two startup owners could collide". Playwright official docs (`https://playwright.dev/docs/test-webserver` "Multiple web servers") document the array form `webServer: [{...},{...}]` with per-entry `name`, `url`, `timeout`, `reuseExistingServer`. Before the array form, project issue #29273 confirmed this is the canonical path.
- **Consequence:** Without the array form, implementer might reach for `globalSetup`/manual spawning. Two ownership sources (Playwright + script) coexist; one will be the "first to bind" and the other will fail. `reuseExistingServer: true` on the second will mask the failure (see F-C1-002). Plan is silent on which form to use, leaving implementer to choose.
- **Precise minimum change:** State explicitly that the config will use `webServer: [{ name: 'backend', command: 'uvicorn src.main:app --port 8009', url: 'http://127.0.0.1:8009/api/sampling-spec-rnd/health', reuseExistingServer: !process.env.CI, timeout: 60_000 }, { name: 'frontend', command: 'npm run dev', url: 'http://127.0.0.1:3009', reuseExistingServer: !process.env.CI, timeout: 60_000 }]`. Add the per-entry assertion that `strictPort: true` in `vite.config.ts` (already present) is a prerequisite — confirmed.
- **Validation:** Apply; bring up a stale backend (any HTTP listener on 8009) before the Playwright run; confirm the test fails loudly rather than attaches to the wrong service. Add an idempotency check that confirms both services are healthy at the test start.

---

### F-C1-008 — PR template evidence wording can collapse into "checked the box"; missing distinct interactive vs automated marker

- **Path / lines:** `openspec/changes/advisory-playwright-harness/tasks.md` §3.3; `openspec/changes/advisory-playwright-harness/specs/agent-browser-verification/spec.md` "Honest browser evidence" requirement.
- **Criterion:** `teammate-safety` AND `interface-contract`. Spec mandates distinguishing interactive vs automated vs unverified, but the proposed checklist item (only described in tasks.md §3.3 as "name whether it came from an interactive browser tool or automated Playwright") is loose and easy to fill with checkmarks without specifying the path used.
- **Consequence:** PR evidence reverts to silent assumption that browser was reviewed. The "honest evidence" capability becomes ineffective.
- **Precise minimum change:** Replace the single checkbox with a forced-choice dropdown (if template supports it) or a 3-line radio: `[ ] interactive browser tool (tool + commit SHA)`, `[ ] automated Playwright (run id + url of artifacts)`, `[ ] neither — evidence unverified, blocked by <reason>`. Specify in tasks.md the exact markdown to add to `.github/pull_request_template.md` so the Review Orchestrator can compare it to AGENTS.md rule §3.
- **Validation:** Open a test PR with a checked `interactive browser tool` box; confirm reviewers can see the recorded tool name and SHA in the PR body.

---

### F-C1-009 — `.gitignore` for Playwright output is missing the canonical buckets; risk of accidental commits

- **Path / lines:** `prototypes/sampling-spec-rnd/frontend/.gitignore`; AGENTS.md "Anchored Git Rules".
- **Criterion:** `dependency-shape` AND `module-responsibility`. AGENTS.md requires anchored (leading slash) ignore patterns. Plan mentions "anchored ignore rules" but does not enumerate them.
- **Consequence:** Without anchored lines, `playwright-report/`, `test-results/`, `blob-report/`, `playwright/.cache/` may either be silently tracked at repo root via inheritance from the root `.gitignore` (none matches) or pollute the prototype-frontend tree. Tracked `playwright-report/` then carries a binary `index.html` + data — recurring diff churn.
- **Precise minimum change:** Append to `prototypes/sampling-spec-rnd/frontend/.gitignore` (anchored):
  ```
  # Playwright outputs
  /test-results/
  /playwright-report/
  /blob-report/
  /playwright/.cache/
  ```
- **Validation:** Run Playwright locally; confirm `git status` shows no new files; commit a test-artifact file at the frontend root and confirm `git check-ignore` returns `true` for each path.

---

### F-C1-010 — `run_frontend.bat` documents stale ports (3007/8007) vs. `vite.config.ts` (3009/8009)

- **Path / lines:** `prototypes/sampling-spec-rnd/frontend/run_frontend.bat` (echoes port 3007 / 8007); `prototypes/sampling-spec-rnd/frontend/vite.config.ts` (`server.port: 3009` + `proxy target http://localhost:8009`).
- **Criterion:** `interface-contract` AND Configuration Drift rule in AGENTS.md §Pre-Archive Gate ("Confirm target ports … match the single source of truth … without drift"). Design.md Decision #3 carves this out as out-of-scope.
- **Consequence:** Documentation drift confuses the next maintainer/junior developer. Out of plan scope by an explicit Decision; mark as `LEARN_NOTE` rather than blocker. The smoke workflow uses `npm run dev` directly, bypassing the .bat, so the smoke is not affected. The .bat is not in the Playwright ownership graph.
- **Precise minimum change (recommended, not required for this change):** Update `run_frontend.bat` echo lines to reflect `3009 / 8009`. Defer to a `docs(chore): sync frontend startup ports` change.
- **Validation:** Add a `// TODO` in `design.md` Risks noting this drift; reviewer evidence check is the existence of the TODO, not the .bat fix.

---

## Limits and Assignment Mismatch

1. **Out of route (by brief):** Security (`S`) and Behavioral (`B`) controlled tags are NOT reviewed here. Security-related surface (CI trust boundaries, `.npmrc` registry pinning, downloaded browser binaries travel with the workflow image, secrets in test logs) is for the Security Assurance specialist or the Review Orchestrator to escalate.
2. **Plan-only review:** All findings are anchored to the written proposal, not to eventual implementation. Applying any change re-runs the same trap survey against the actual artifacts, because F-C1-001 (stub requirement) and F-C1-003 (workflow edit) connect directly to file mutations in the Apply Change step.
3. **Traps I cannot verify here without execution:** exact GitHub Actions cache hit rate on first run; whether `setup-node@v4`'s built-in npm cache key (`npm-` + lockfile hash) conflicts with a hand-rolled `actions/cache@v4` block on `~/.npm`; the actual failure mode of an unresolvable `@pages/SpecVersionPage` import in `vite dev` on a Linux runner (Behavior specialist to confirm).
4. **Assignment mismatch with the brief's claim that the plan covers "all relevant dimensions":**
   - The brief's "smallest maintainable executable handoff" is **not yet met** because F-C1-001 (missing import) blocks standalone local execution today.
   - The brief's "one dependency/install path" is contradicted by F-C1-003 (existing `npm install` vs plan's `npm ci`).
   - The brief's "repository-consistent package/workflow/config" is contradicted by F-C1-005 (workflow placement ambiguity).
   - The brief's "no architecture creep" is satisfied (no application backends or new layers added) — CHANG-2026-10-14-C1 confirms.
5. **What I deliberately did NOT do (mode constraints):** did not edit any source file; did not run the smoke; did not install Playwright; did not modify or create anything inside the change folder other than this review record.
6. **Unknown:** exact resolution outcome when both `webServer[].url` probes are made service-specific per F-C1-002 — cannot test without Playwright runtime. Marked UNVERIFIED in worklog.

---

## Worklog (sources, extractions, failures)

| # | When | Action | Source / Tool | Outcome |
|---|------|--------|--------------|---------|
| 1 | review | Read proposal.md, design.md, tasks.md | `read_file`, lines 1–400 | Captured |
| 2 | review | Read `specs/advisory-browser-smoke/spec.md`, `specs/agent-browser-verification/spec.md`, `.openspec.yaml` | `read_file` | Captured |
| 3 | review | `Get-ChildItem openspec/changes/advisory-playwright-harness -Recurse -Force -Name` | pwsh | 8 files (1 yaml, 1 proposal, 1 design, 1 tasks, 2 spec dirs, 2 spec files). Confirmed no `artifacts/` present. |
| 4 | review | `git status --short --branch; git rev-parse HEAD; git log -3 --oneline` | pwsh | Branch `feat/payroll-bonus-pool` @ `d37f6a3`. Untracked only `openspec/changes/advisory-playwright-harness/`. |
| 5 | review | Read `AGENTS.md`, `.github/pull_request_template.md`, `scripts/check_workspace_hygiene.py` first 100 lines | `read_file` | Root & Sandbox Isolation rule confirmed; PR template lacks browser evidence; hygiene script whitelists known dirs. |
| 6 | review | Read `prototypes/sampling-spec-rnd/frontend/package.json` | `read_file` | No `test:e2e`, no `@playwright/test`. Scripts limited to dev/build/preview/type-check/lint. |
| 7 | review | Read `vite.config.ts`, `tsconfig.json`, `tsconfig.app.json`, `.eslintrc.cjs`, `.gitignore` for frontend | `read_file` | Vite uses `port: 3009`, `strictPort:true`; proxy to 8009. tsconfig.app includes only `["src"]`. ESLint scope `eslint src`. |
| 8 | review | Read frontend `App.tsx` | `read_file` | Confirmed `import SpecVersionPage from '@/pages/SpecVersionPage'`. Confirmed `<span className="hidden sm:inline">{isConnected ? 'Connected' : 'Local Mode'}</span>` (sm: breakpoint). |
| 9 | review | Read backend `src/main.py` first 80 lines | `read_file` | Confirms `GET /api/sampling-spec-rnd/health` returns `{"status":"healthy","service":"sampling-spec-rnd-api"}`. CORS allows 3009 and 3007. |
| 10 | review | Read `.github/workflows/ci.yml`, `prototype-sampling.yml`; both use Node 20 / Python 3.11, hardware `ubuntu-latest` | `read_file` | Existing frontend-quality uses `npm install`, not `npm ci`. Path trigger `prototypes/sampling-spec-rnd/**`. |
| 11 | review | `Test-Path` for frontend `package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`, `playwright.config.ts`, `.gitignore`, `tests` | pwsh | All False except `.gitignore` (True) and parent `frontend` dir. |
| 12 | review | Read `prototypes/sampling-spec-rnd/frontend/run_frontend.bat`, `backend/run_backend.bat` | `read_file` | Frontend .bat claims port 3007/8007 (DRIFT). Backend .bat uses 8009 (consistent). |
| 13 | review (web) | Web search: "Playwright webServer config reuseExistingServer semantics official docs 2024" | `mcp_mcp-omnisearc_web_search` (brave) | 10 hits. Top hits: `https://playwright.dev/docs/test-webserver`, `https://playwright.dev/docs/api/class-testconfig`. `reuseExistingServer` does not verify body. |
| 14 | review (web) | Web search: "Playwright globalSetup globalTeardown webServer multiple services single config official" | `mcp_mcp-omnisearc_web_search` | 9 hits. Confirms `webServer: [...]` array form is the canonical path (issue #29273). |
| 15 | review (web) | `fetch_webpage` `https://playwright.dev/docs/test-webserver` | `fetch_webpage` | Extracted: Multiple web servers section with per-entry `name`, `url`, `timeout`, `reuseExistingServer`. Wait condition unions `url` and `wait`. `gracefulShutdown` SIGTERM not supported on Windows. |
| 16 | review (web) | Web search: "@playwright/test latest stable version npm 2024 official pinning" | `mcp_mcp-omnisearc_web_search` | Latest stable `1.64.0` per npm registry. |
| 17 | review (web) | Web search: "Vite React TypeScript missing module import dev server startup error unresolvable typescript path alias" | `mcp_mcp-omnisearc_web_search` | Confirms: Vite dev server fails to serve when any static import is unresolvable; "A single unresolvable import blocks the entire page from rendering in the browser" (FixDevs). |
| 18 | review (web) | Web search: "Playwright CI cache action setup-node cache-dependency-path node_modules lockfile best practice github actions" | `mcp_mcp-omnisearc_web_search` | 10 hits. Pattern: `actions/cache@v4` keyed by Playwright version for `~/.cache/ms-playwright`, plus `npm ci`, plus `npx playwright install --with-deps`. |
| 19 | review | `Select-String` for `SpecVersionPage` and `SpecVersionTracker` across `prototypes/sampling-spec-rnd/frontend` | pwsh | **Zero hits for `SpecVersionPage`** — confirmed pre-existing broken import. Only `SpecVersionTracker.jsx` exists. **Extraction failure to note (resolved as: confirmed missing)**, not an actual extraction failure but a confirmed absence. |
| 20 | review | `openspec validate advisory-playwright-harness --strict` | pwsh | "Change 'advisory-playwright-harness' is valid". |
| 21 | review | `openspec list` | pwsh | Shows three changes; advisory-playwright-harness is `0/17 tasks 44m ago`. |
| 22 | review | Environment fingerprint: `node`, `npm`, `python`, `git` versions | pwsh | Recorded above. |
| 23 | review | `mkdir openspec/changes/advisory-playwright-harness/reviews` | `create_directory` | Pre-existing parent `reviews/` was absent; created (the **only** file-system write permitted by mode rules, plus this review record itself). |
| 24 | review | Write this review record to `openspec/changes/advisory-playwright-harness/reviews/specialist-c-001.md` | `create_file` | Captured. |

**Sources searched (consolidated):** see Evidence Checked §External sources; sources 1–18 above.

**Conflicts found:** None requiring third-source resolution. The Playwright docs and two independent community write-ups agree on `reuseExistingServer` semantics and the array-form `webServer`. The Vite import-resolution behavior is corroborated by Vite issues tracker (`vitejs/vite#21889`) and two independent blogs.

**No claims made without action evidence:** every "Confirmed", "Captured", "Verified" tag in this record is backed by a `read_file`, `run_in_terminal`, `fetch_webpage`, or `mcp_mcp-omnisearc_web_search` invocation in the worklog table above.

---

## Return

- **Path of written review record:** `openspec/changes\advisory-playwright-harness\reviews\specialist-c-001.md`
- **Specialist status:** `COMPLETE` for Changeability coverage.
- **Blocking findings surfaced:** F-C1-001, F-C1-002, F-C1-003, F-C1-005, F-C1-007 (5 BLOCKING_DEFECT).
- **Major findings surfaced:** F-C1-004, F-C1-006, F-C1-008, F-C1-009 (4 PROOF_GAP / BLOCKING_DEFECT).
- **LEARN_NOTE:** F-C1-010.
- **No other file mutated** (mode constraint honored).
