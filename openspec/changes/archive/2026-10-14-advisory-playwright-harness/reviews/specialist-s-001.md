# Specialist Review S-1 — Security Assurance — Advisory Playwright Harness

Review identity: `advisory-playwright-plan-review-001`.
Date: 2026-10-14.
Environment: Windows; working tree at `C:\Projects\hackathon-MAIN-alkademi`; branch `feat/payroll-bonus-pool`; OpenSpec change `openspec/changes/advisory-playwright-harness/` is **untracked, local only** (no remote PR open).
Mode: read-only. No installations, no servers, no source edits; the only file written is this review.

## Role

Security assurance review of the proposed minimal Playwright harness plan. Calibrated to the requested minimalist, advisory, non-blocking scope. Specifically tasked to surface:

- trust boundary at the workflow / PR / runner seam
- secret exposure
- read/write API leakage from the application surface the smoke touches
- action permissions and version pins
- fork PR handling (fork vs. same-repo branch, fork approval policy)
- trace/report privacy (artifacts retained for maintainer view)

Outside the security lens: test design taste, lint hygiene, dashboard product behavior, backend business-logic correctness.

## Status

Review complete. No blocking vulnerabilities identified in the planned scope. Tripwire answer is favorable — the plan does not invoke `pull_request_target` anywhere, and no current workflow uses it. Seven Findings (F1–F7) recorded below as hardening remdies, all severity LOW or MEDIUM, none a security blocker. One pre-existing condition is noted out-of-scope.

## Evidence Checked

Repository files read (full path / line range), with cross-source verification used:

| Path | Lines | Purpose |
|---|---|---|
| `openspec/changes/advisory-playwright-harness/proposal.md` | 1–200 | Why/What/Scope |
| `openspec/changes/advisory-playwright-harness/design.md` | 1–400 | Decisions, risks, ports |
| `openspec/changes/advisory-playwright-harness/tasks.md` | 1–400 | Implementation checklist |
| `openspec/changes/advisory-playwright-harness/.openspec.yaml` | 1–200 | Schema marker |
| `openspec/changes/advisory-playwright-harness/specs/advisory-browser-smoke/spec.md` | 1–200 | Spec for the smoke job |
| `openspec/changes/advisory-playwright-harness/specs/agent-browser-verification/spec.md` | 1–200 | Spec for the governance policy |
| `.github/workflows/ci.yml` | 1–300 | Existing CI trigger/permissions baseline |
| `.github/workflows/prototype-sampling.yml` | 1–300 | Targeted workflow for the new advisory job |
| `.github/pull_request_template.md` | 1–200 | PR checklist (will be extended by §3.3) |
| `prototypes/sampling-spec-rnd/frontend/package.json` | 1–120 | Scripts/devDependencies baseline (no Playwright yet) |
| `prototypes/sampling-spec-rnd/frontend/vite.config.ts` | 1–120 | Port `3009`, `strictPort: true`, `/api` proxy |
| `prototypes/sampling-spec-rnd/frontend/.gitignore` | 1–60 | Lockfile commit posture |
| `prototypes/sampling-spec-rnd/backend/src/api/routes.py` | 1–80 | Confirms `/api/sampling-spec-rnd/health` exists and is read-only |

External sources cross-referenced (cited inline below):

- GitHub Docs, *Securely using `pull_request_target`* — <https://docs.github.com/en/actions/reference/security/securely-using-pull_request_target>. Verified: token scope, secrets exposure, default policy for `pull_request_target` from 2026-11-02, the pwn request flaw shape (check out PR head, then run code from it).
- GitHub Security Lab, *Keeping your GitHub Actions and workflows secure Part 1: Preventing pwn requests* — <https://securitylab.github.com/resources/github-actions-preventing-pwn-requests/>. Verified: rationale for the `pull_request`/`pull_request_target` split, the canonical insecure example, and the remediation list (prefer `pull_request`; minimal `permissions`; do not execute forked code in privileged context).
- GitHub Docs, *Controlling permissions for GITHUB_TOKEN* — <https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/controlling-permissions-for-github_token>. Verified: fork behavior and the `permissions:` key scope.
- GitHub Docs repo settings, *Run workflows from fork pull requests* behavior — <https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository>. Verified: fork PRs run with read-only `GITHUB_TOKEN` and no secrets by default.
- Playwright official docs, *Continuous Integration* — <https://playwright.dev/docs/ci>. Verified: recommended `pull_request` GitHub Actions shape, default headless mode, `workers: 1` in CI, `globalTimeout` discipline.
- `microsoft/playwright-github-action` (archived 2025-01-23, **deprecated**) — <https://github.com/microsoft/playwright-github-action>. Verified: the official recommendation is now the CLI (`npx playwright install --with-deps chromium` then `npx playwright test`), not the third-party GH Action wrapper.

Static audit findings, recorded (no source modification performed):

- `Select-String -Path .github/workflows/* -Pattern 'secrets:|pull_request|permissions:'`: zero matches for `secrets:`; zero matches for `pull_request_target`; both workflows expose only `pull_request` triggers; both declare `permissions: contents: read` at workflow level (`prototype-sampling.yml:19`, `ci.yml:13`).
- `Test-Path prototypes/sampling-spec-rnd/frontend/playwright.config.ts` and `package-lock.json` and `tests/smoke.spec.ts`: all `False`. **Plan-only review, no implementation exists yet.** Verified before relying on plan text — i.e., this is a static review of intent.

Git state:

- `git status --short --branch` shows `feat/payroll-bonus-pool...origin/feat/payroll-bonus-pool` and `?? openspec/changes/advisory-playwright-harness/`. The subject change is **untracked, local only** — no remote PR is open at this point. No governance gap caused by remote; risk posture for the review is "what this draft will produce when submitted".

## Findings

Each Finding: ID — path/lines — criterion (security principle) — consequence if not addressed — minimum remedy/validation.

### F1 — Workflow event trigger not pinned in design/spec (TRUST BOUNDARY EXPLICITNESS)

- **Path/lines.** `openspec/changes/advisory-playwright-harness/design.md` (Decision §4, Goals); `openspec/changes/advisory-playwright-harness/tasks.md` §2.1 ("triggered by relevant prototype changes"); the workflow it appends to is `.github/workflows/prototype-sampling.yml`.
- **Criterion.** To make the trust boundary unambiguous and prevent the canonical pwn-request trap, the new advisory workflow MUST trigger on `on: pull_request` only. It MUST NOT use `on: pull_request_target`. It MUST NOT pass `actions/checkout` a `ref:` or `repository:` that points at the fork head. Per GitHub Docs (<https://docs.github.com/en/actions/reference/security/securely-using-pull_request_target>), `pull_request` runs the workflow file from the PR merge commit but, for forks, restricts `GITHUB_TOKEN` to read-only and withholds secrets. Per the GitHub Security Lab (<https://securitylab.github.com/resources/github-actions-preventing-pwn-requests/>), `pull_request_target` runs in the base repo's default-branch context with **read/write token and secrets exposed**; combining it with `actions/checkout` of the PR head is the canonical insecure shape.
- **Consequence.** Without an explicit pin, a future contributor or reviewer could (a) switch to `pull_request_target` because they "need secrets to do X", and (b) add `ref: ${{ github.event.pull_request.head.sha }}`. Together, that is the textbook pwn-request pattern and exposes base-repo secrets and write tokens to attacker-supplied PR code.
- **Minimum remedy.** Add to `design.md` an "Events & permissions" subsection stating: trigger is `pull_request`; `pull_request_target` is forbidden; `actions/checkout` uses default ref. Encode in `tasks.md §2.1` a checkbox: "verify trigger wording is `pull_request`, not `pull_request_target`, and `actions/checkout` does not set a fork `ref`." Encode in `specs/advisory-browser-smoke/spec.md` a Scenario: "new advisory job runs on `on: pull_request`; declared `permissions: contents: read`; no checkout `ref` overrides."
- **Validation (post-implementation).** `git grep -nE 'pull_request_target|github\.event\.pull_request\.head' .github/workflows/*.yml` returns **no matches**. `git grep -nE '^\s*permissions:\s*contents:\s*read' .github/workflows/prototype-sampling.yml` returns a line in the new job's `jobs:` block.

### F2 — Workflow `permissions:` block not pinned in the plan (LEAST PRIVILEGE)

- **Path/lines.** `openspec/changes/advisory-playwright-harness/design.md`; `tasks.md` §2.1, §2.3; baselines are `.github/workflows/ci.yml:13` and `.github/workflows/prototype-sampling.yml:19`, both at `permissions: contents: read`.
- **Criterion.** Match the existing minimal posture. The new advisory job MUST declare `permissions: contents: read` (at workflow level, optionally restated per job) and MUST NOT request `issues`, `pull-requests`, `repository-projects`, `actions: write`, `contents: write`, or any org-scoped permission. Per <https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/controlling-permissions-for-github_token>, omitting the key leaves the default scopes (which include write on a same-repo `pull_request`).
- **Consequence.** A permissive default widens the blast radius in any future pwn-request scenario (does not introduce a new vulnerability today because the smoke does not use those scopes, but expands the surface if F1 is later partly relaxed).
- **Minimum remedy.** Add to `tasks.md §2.1` a checkbox: "declare `permissions: contents: read`." Add to `specs/advisory-browser-smoke/spec.md` a Requirement "Least privilege" with Scenario "declared token is `contents: read` and no other scopes are requested."
- **Validation.** `git grep -nE '^\s*permissions:\s*\{' .github/workflows/*.yml` returns **no matches**. `git grep -nE 'contents:\s*write|issues:\s*write|pull-requests:\s*write' .github/workflows/*.yml` returns **no matches**.

### F3 — CI install path: mandate `npm ci`, not `npm install` (FORK PR LIFECYCLE SCRIPTS)

- **Path/lines.** `openspec/changes/advisory-playwright-harness/tasks.md §2.2` ("Install the required Chromium browser"); §4.1 already says `npm ci` for local; lockfile posture in `prototypes/sampling-spec-rnd/frontend/.gitignore` (no exclusion of `package-lock.json`, intended).
- **Criterion.** Use `npm ci` in CI (deterministic, lockfile-pinned, **does not run lifecycle scripts**) rather than `npm install` (rewrites lockfile, **runs `preinstall`/`install`/`postinstall`**). The CI run must depend on the committed `package-lock.json` produced by §1.1. Per the Security Lab piece ("…build scripts like `make` or `powershell` files or redefine the build script in the `package.json` file. … Npm packages for example may have custom `preinstall` and `postinstall` scripts, so running `npm install` would already trigger any malicious code if the attackers added a new package reference"), `npm install` is the documented attack surface.
- **Consequence.** With `on: pull_request` and a fork PR whose `package.json` is modified to add a malicious lifecycle hook, `npm install` runs attacker code on the GH-hosted runner. The token is read-only and no secrets leak — but compute is consumed, network egress is opened, and probing of secrets-from-env is possible.
- **Minimum remedy.** In `tasks.md §2.1`/§2.2, write the install step as `run: npm ci` and the browser install as `run: npx playwright install --with-deps chromium`. Add a precondition: "§2 starts only after §1.1 has committed `prototypes/sampling-spec-rnd/frontend/package-lock.json`." Add validation: `git ls-files | grep -E '^prototypes/sampling-spec-rnd/frontend/package-lock\.json$'` returns one row before §2 begins.
- **Validation.** `git grep -nE 'run:\s*npm\s+install' .github/workflows/prototype-sampling.yml` returns **no matches** in the new advisory job. (Pre-existing: the existing `frontend-quality` advisory job at `prototype-sampling.yml` line ~43 uses `npm install`. **Pre-existing condition, not introduced by this plan; out of scope** for this F3 remedy.)

### F4 — Trace scope and artifact retention not constrained (TRACE/REPORT PRIVACY)

- **Path/lines.** `openspec/changes/advisory-playwright-harness/design.md` Goals / Risks; `tasks.md` §2.3 ("failure artifacts"); `specs/advisory-browser-smoke/spec.md` Scenario "Browser smoke fails in CI".
- **Criterion.** Default Playwright `trace.zip` captures a full network HAR (URL, request, response), DOM snapshots, console logs, and a timeline of actions. For an advisory smoke that only touches the dashboard and `GET /api/sampling-spec-rnd/health` (read-only), the trace is **bigger than necessary** and introduces a privacy surface for future contributors who extend the smoke to routes that may render tenant identifiers. GitHub artifact retention defaults can reach 90 days. Per <https://playwright.dev/docs/ci>, traces are off by default.
- **Consequence.** Artifacts uploaded from fork PR runs are visible only to maintainers (fork PR artifacts are not pubicly downloadable for the PR author), which is good — but every retained artifact is a delayed-disclosure surface if the application later surfaces anything sensitive.
- **Minimum remedy.** Add a Requirement to `specs/advisory-browser-smoke/spec.md`: "Advisory trace scope" with Scenario "Default trace recording is off; only `only-on-failure` screenshots and the Playwright HTML report are uploaded; retention is bounded." In the design, specify `use: { trace: 'off', screenshot: 'only-on-failure' }`. In `tasks.md §2.3` clarify artifact upload:
  - screenshots: `if: failure() || cancelled()`, retention ≤ 14 days
  - HTML report: `if: always()`, retention ≤ 7 days
- **Validation.** `git grep -nE "trace:\s*['\"]on" prototypes/sampling-spec-rnd/frontend/playwright.config.ts` returns **no matches**. `git grep -nE 'retention-days:' .github/workflows/prototype-sampling.yml` shows numeric values.

### F5 — Service startup command not pinned to declared ports / entries

- **Path/lines.** `openspec/changes/advisory-playwright-harness/design.md` Decision §1, §3; `tasks.md` §1.3; `prototypes/sampling-spec-rnd/frontend/vite.config.ts:30` (`strictPort: true`, port `3009`, `/api` proxy → `http://localhost:8009`); `prototypes/sampling-spec-rnd/backend/README.md:168` (`GET /api/sampling-spec-rnd/health`).
- **Criterion.** The startup in CI must rely on the application entry the team already declared: Vite `dev` (caught by `vite.config.ts` `strictPort: true` on 3009) and the FastAPI app on 8009. No `PORT=` environment override and no `--port` flag from the harness; failure if the port is unavailable; no silent fallback port.
- **Consequence.** A harness that reads `PORT` from environment or from a fork-PR-modified `.env` could report green against a different backend (e.g., a developer's local instance) or against a misrouted service. Silent fallback ports would mask startup bugs.
- **Minimum remedy.** Add to `specs/advisory-browser-smoke/spec.md` a Scenario "Service startup fails fast": if the webServer health check does not pass in N seconds, the step exits non-zero, the Playwright run does not start, traces/screenshot are captured, the advisory job still maintains `continue-on-error: true`, but the failure is recorded as "startup-not-assertion." In `tasks.md §1.3` add: "start Playwright `webServer` only via `playwright.config.ts`; do not pass `--port`; do not set `PORT` env." Confirm the read-only assertion is unchanged.
- **Validation.** `git grep -nE 'PORT=|--port' prototypes/sampling-spec-rnd/frontend/playwright.config.ts` returns **no matches**. `git grep -nE 'strictPort' prototypes/sampling-spec-rnd/frontend/vite.config.ts` returns the existing match (don't drop it).

### F6 — Action version pins not pinned (SUPPLY-CHAIN HYGIENE; AGENTS.md consistency)

- **Path/lines.** `openspec/changes/advisory-playwright-harness/tasks.md §2.1` ("Node 20 plus the committed lockfile"); baselines at `.github/workflows/ci.yml:14` (`actions/checkout@v4`), `.github/workflows/ci.yml:20` (`actions/setup-python@v5`), `.github/workflows/prototype-sampling.yml:33` (`actions/checkout@v4`), `.github/workflows/prototype-sampling.yml:39` (`actions/setup-node@v4`); `AGENTS.md` workflow-version rule.
- **Criterion.** Pin actions to majors consistent with the repo. Recommended set for the new advisory job (avoid mixing majors across the same workflow file):
  - `actions/checkout@v4`
  - `actions/setup-node@v4` (with `node-version: "20"`)
  - `actions/upload-artifact@v4`
- **Consequence.** Mixed majors across workflow files increase the supply-chain review surface per change, and silently pull in deprecation warnings or breaking changes. Note: `microsoft/playwright-github-action` was **deprecated in January 2025** and archived; using it would be a wrong choice irrespective of version (<https://github.com/microsoft/playwright-github-action>). Use the CLI (`npx playwright install --with-deps chromium`) per the same source.
- **Minimum remedy.** Add a "Workflow action pins" row in `tasks.md §2.1` listing the three action pins above and explicitly rejecting `microsoft/playwright-github-action`. Confirm version-set consistency with `AGENTS.md`.
- **Validation.** `git grep -nE '@v[0-9]+' .github/workflows/prototype-sampling.yml` shows consistent majors; no `microsoft/playwright-github-action` reference anywhere.

### F7 — `headless: true` not pinned in spec (REPRODUCIBILITY & RESOURCE POSTURE)

- **Path/lines.** `openspec/changes/advisory-playwright-harness/design.md` Decision §1; `tasks.md` §1.2; Playwright docs default behavior per <https://playwright.dev/docs/ci>.
- **Criterion.** Spell out `headless: true` on the Chromium project. Playwright's CI default is headless; in CI on GH-hosted Ubuntu runners, the absence of `headless: true` does not require a display server because of Playwright's CI daemon behavior, but a contributor running locally headed can produce different artifacts than CI.
- **Consequence.** Soft signal only — does not block CI, but reproducibility is reduced; a future contributor running headed locally at desktop resolution would generate screenshots at a non-CI viewport.
- **Minimum remedy.** In `tasks.md §1.2` add: "`use: { headless: true, baseURL: 'http://localhost:3009' }` for the Chromium project."
- **Validation.** `git grep -nE 'headless' prototypes/sampling-spec-rnd/frontend/playwright.config.ts` should show an explicit `true`.

## Limits and Assignment Mismatch

### Scope limits (intentional, not gaps)

- **Application backend:** `prototypes/sampling-spec-rnd/backend/src/api/routes.py` has writes (`POST /studies/create`, `/start`, `/add-sample`, `/complete`). This review confirms the smoke does not exercise them, but does NOT assess their authorization, validation, or tenant-isolation. Out of brief.
- **`src/pages/*` of the prototype frontend:** not opened. The smoke asserts headline + `Connected`/`Local Mode` text. Unknown whether the dashboard component ships tenant IDs in component-initial state. **UNKNOWN** — flagged.
- **Existing `prototype-sampling.yml` advisory jobs** using `npm install`: pre-existing posture, not modified by this plan. Out of scope for this review; mentioned only because F3 mitigation requires "the NEW job uses `npm ci`".
- **Repository-wide secret scan, signup/free-fork policy, organization-level settings:** out of scope.
- **Self-hosted runners:** repo uses `ubuntu-latest` GH-hosted. Not applicable.

### Evidence limits

- I did NOT execute `npm ci`, `npx playwright install`, nor any browser launch. The brief forbids installs/servers. Playwright CLI behavior was verified only via official docs (<https://playwright.dev/docs/ci>) and the deprecation note from `microsoft/playwright-github-action`.
- `openspec validate` was NOT executed; brief is review-only and readable artifacts only.
- No semantic-search tool was used because the brief notes the index may be stale and the subject is small enough for direct reads.

### Assignment Mismatch

None. All scope was honored. The plan's "active change artifacts path" is a contextual note (`openspec/changes/advisory-playwright-harness/artifacts/`); the only file written is this review record at `openspec/changes/advisory-playwright-harness/reviews/specialist-s-001.md`. No source files, no workflow files, no prototype files, and no other OpenSpec changes were modified.

### UNKNOWNs — explicit

- Whether forks are enabled for the repo (`Settings → Actions → General → Fork pull request workflows`) is **UNKNOWN** to me. Default is *Require approval for first-time contributors*, which means fork PRs do not run workflows until a maintainer approves them. The plan does not hinge on fork PRs running automatically; it hinges on the run being safe WHEN it does run. F1 and F2 remedies are sufficient regardless of fork-approval mode.
- Whether the prototype frontend dashboard persists tenant identifiers in initial component state — **UNKNOWN** (not loaded).
- Whether `vite dev` plus `strictPort: true` reliably returns a non-zero exit on port conflict in CI — **UNKNOWN** empirically; design risk only. The webServer health check in Playwright covers it.
- Whether `actions/setup-node@v4`'s `node-version: "20"` corresponds to the lockfile `engines` field — **UNKNOWN** because the planned `package.json` amendment (§1.1) is not yet made. Recommend `engines.node: ">=20"` plus `.nvmrc` if needed.

### Pre-existing conditions (NOT introduced by this plan)

- `.github/workflows/prototype-sampling.yml` uses `run: npm install` in the existing `frontend-quality` advisory job. Lifecycle scripts can fire from fork PRs. **Pre-existing.** The new advisory job must NOT replicate this (F3 captures it). A follow-up hardening change is out of the brief of this review.
- The brief asks to look at "secret exposure": the repo has no `secrets:` references in any workflow; `GITHUB_TOKEN` is `contents: read` only. No secrets exist to expose today.

## Worklog

### Sources used

- GitHub Docs, *Securely using `pull_request_target`* — <https://docs.github.com/en/actions/reference/security/securely-using-pull_request_target>. **OK.** Verified trigger posture, default policy, pwn request flaw text. Used for F1, F2.
- GitHub Security Lab, *Preventing pwn requests* — <https://securitylab.github.com/resources/github-actions-preventing-pwn-requests/>. **OK.** Verified remediation list, canonical insecure example, `pull_request` preference. Used for F1, F3.
- GitHub Docs, *Controlling permissions for GITHUB_TOKEN* — <https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/controlling-permissions-for-github_token>. **OK.** Used for F2.
- GitHub Docs repo settings, *Managing GitHub Actions settings for a repository* — <https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository>. **OK.** Confirmed fork posture (read-only token, no secrets). Used for F1, F2.
- Playwright docs, *Continuous Integration* — <https://playwright.dev/docs/ci>. **OK.** Confirmed headless default, recommended GH Actions shape, `workers: 1`, `globalTimeout`, `--with-deps`. Used for F4, F7.
- `microsoft/playwright-github-action` — <https://github.com/microsoft/playwright-github-action>. **OK.** Confirmed the GH Action wrapper is **deprecated/archived 2025-01-23** and that the CLI is now official. Used for F6.

### Sources attempted; partial / failure

- GitHub Changelog, *Control permissions for GITHUB_TOKEN (2021-04-20)* — referenced in Brave search snippets; not fetched in full. **PARTIAL** (snippet only: "Actions generates a new token for each job…[read] access to a number of API endpoints except in the case of pull requests from forks which are always read"). Cited inline in F1, F2 only as triangulation; primary citations remain the official GitHub Docs links above.
- GitHub Changelog, *Safer `pull_request_target` defaults for actions/checkout (2026-06-18)* — referenced; not fetched in full. **PARTIAL** (snippet only: "This change only blocks checkouts of the fork pull request head and merge commits"). Triangulated against the GitHub Docs piece. Not relied on as sole authority.
- GitHub Security Changelog, *Safer checkout blocks common pwn request attack patterns* (2026-06 Hacker News aggregator) — third-party summary of GitHub Changelog; cited F6 light only.

### Repository reads (no edits performed)

- `openspec/changes/advisory-playwright-harness/proposal.md` lines 1–200 — OK
- `openspec/changes/advisory-playwright-harness/design.md` lines 1–400 — OK
- `openspec/changes/advisory-playwright-harness/tasks.md` lines 1–400 — OK
- `openspec/changes/advisory-playwright-harness/.openspec.yaml` lines 1–200 — OK
- `openspec/changes/advisory-playwright-harness/specs/advisory-browser-smoke/spec.md` lines 1–200 — OK
- `openspec/changes/advisory-playwright-harness/specs/agent-browser-verification/spec.md` lines 1–200 — OK
- `.github/workflows/ci.yml` lines 1–300 — OK
- `.github/workflows/prototype-sampling.yml` lines 1–300 — OK
- `.github/pull_request_template.md` lines 1–200 — OK
- `prototypes/sampling-spec-rnd/frontend/package.json` lines 1–120 — OK (no Playwright dependency present)
- `prototypes/sampling-spec-rnd/frontend/vite.config.ts` lines 1–120 — OK
- `prototypes/sampling-spec-rnd/frontend/.gitignore` lines 1–60 — OK
- `prototypes/sampling-spec-rnd/backend/src/api/routes.py` lines 1–80 — OK

### Commands run (read-only, no installs, no servers)

- `Test-Path openspec/changes/advisory-playwright-harness` — `True`.
- `Get-ChildItem openspec/changes/advisory-playwright-harness -Recurse -Force` — subject inventory captured.
- `git status --short --branch` — confirmed `feat/payroll-bonus-pool` HEAD; subject change is untracked local only.
- `git log -8 --oneline --decorate` — branch context captured (HEAD `d37f6a3`).
- `Get-ChildItem .github/workflows -Name` — workflows enumerated (`ci.yml`, `prototype-sampling.yml`).
- `Select-String -Path .github/workflows/* -Pattern 'secrets:|pull_request|permissions:'` — confirmed **zero matches** for `secrets:`; zero for `pull_request_target`; both workflows use `pull_request` triggers; both declare `permissions: contents: read`.
- `Test-Path prototypes/sampling-spec-rnd/frontend/playwright.config.ts|package-lock.json|tests/smoke.spec.ts` — all `False`. Plan-only review confirmed.
- `Get-ChildItem prototypes/sampling-spec-rnd/frontend -Force` — confirmed frontend layout; **no `package-lock.json`** yet present (commit before §2 starts — F3).
- `Select-String -Path 'prototypes/sampling-spec-rnd/backend/**' -Pattern '/api/sampling-spec-rnd/health'` — confirmed the read-only health route exists; write paths (`POST /studies/create`, `/start`, `/add-sample`, `/complete`) are present but **not** exercised by the planned smoke.

### Commands NOT run (per brief: no installs, no servers, no source edits)

- `npm ci`, `npm install`, `npx playwright install`, any browser launch.
- `python scripts/check_workspace_hygiene.py`, `npm run type-check`, `npm run lint`, `pytest`, `ruff`, `mypy`.
- `openspec validate`.
- `git diff`, `git checkout`, `git push`, `gh pr *`, `git add`.
