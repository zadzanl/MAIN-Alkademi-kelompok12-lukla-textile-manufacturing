# Advisory Playwright harness — implementation revision 3

## Intent and constraints

User approved implementation after review and selected "Keep harness-only; expose the existing failure". Preserve application source, missing eager SpecVersionPage import, and existing CI jobs. Deliver one read-only Chromium smoke, advisory CI, and generic interactive-browser-first guidance with automated fallback. No fake green, skip, or page stub.

## State

- Branch: chore/advisory-playwright-harness, based on fetched origin/master 69f87a2; existing harness edits preserved.
- Original review NEEDS_REVISION remains historical evidence. Design revision 2 and user decision supersede its proposed app-repair prerequisite.
- First Assistant dispatch returned provider error after writing partial files. Explorer recovery report records files found; no claim that the dispatch made no changes remains valid.
- npm metadata latest 1.64.1 and 1.64.0 install attempts failed due to environment publication-date cutoff. Exact 1.63.0 installed successfully; local Node 24.11.0/npm 11.18.0 differ from CI Node 20.
- Parent inspected config, test, workflow, package and ignore diffs; corrected ESM directory resolution and pinned project viewport after device spread.
- Harness Vite child sets NODE_OPTIONS=--dns-result-order=ipv4first for unchanged localhost proxy and VITE_API_URL=/api/sampling-spec-rnd to avoid local environment redirecting smoke requests.
- AGENTS.md and PR template edits are present; browser policy is generic, not vendor-locked.

## Remaining verification

Install reproducibly, validate service lifecycle and occupied-port rejection, execute real smoke, collect browser-tool evidence, run focused/broader checks, independent Review Orchestrator verdict, truthful task tracking. Do not claim remote workflow or branch-rule verification without evidence. No source repair authorized.