# Task record: fix-font-scale-setting

**Current revision:** 5
**Current state:** Implementation complete; review completed with documentation-only remediation requested by the user.

## Intent

Restore the existing Settings text-size control in the sampling/spec prototype so authenticated users can select 75%, 100%, 125%, or 150%, see the dashboard scale, and retain the choice after reload.

## Constraints

- Preserve unrelated dirty edits in `README.md`, `scripts/check_workspace_hygiene.py`, and `USER_GUIDE.md`.
- Change only the sampling/spec frontend and this OpenSpec change folder.
- No new dependencies, backend work, auth changes, login scaling, font-family changes, or theme changes.
- Use local browser verification; do not re-enable GitHub Actions.

## Decisions

- Use `localStorage` key `ui-font-scale`, matching existing `ui-font` and `ui-dark` preference storage.
- Validate the four supported values at the storage and event boundaries; invalid data defaults to 100%.
- Apply CSS `zoom` to the authenticated shell and retain the existing `<main>` scroll region.
- Add focused Playwright coverage in the prototype harness.

## Evidence

- [code] `SettingsView.tsx` already declares `fontScale` and `onFontScaleChange` props and renders the range input.
- [code] `App.tsx` currently has no `FontScale` declaration or props at the Settings call site; compiler diagnostics confirm both failures.
- [code] `playwright.config.ts` targets Chromium at `http://127.0.0.1:3009` and `tests/smoke.spec.ts` provides authenticated session setup.

## Research findings

- `research-001-zoom-layout.md`: CSS `zoom` is the viable layout-scaling mechanism. The shell needs `height: calc(100vh / ratio)`, and `Sidebar.tsx` must change from `height: '100vh'` to `height: '100%'` so the bottom theme control remains reachable at 150%.
- `research-002-browser-coverage.md`: authenticated Playwright setup must run before `goto`; the stable rendered measurement is the Settings `Ukuran Teks` heading; the existing smoke test has an unrelated stale `Overview` assertion and must not be changed in this fix.

## Handoffs

- Explorer risk checks: complete; reports `research-001-zoom-layout.md` and `research-002-browser-coverage.md`.
- Implementation: complete; see `impl-001.md`.
- Review: complete; `reviews/review-001.md` found one documentation-state blocker and one non-blocking test-hardening note. The user requested documentation reconciliation without another review pass.
- Historical recovery: `research-003-recovery.md` records the earlier failed Assistant attempt and is superseded by `impl-001.md`.

## Verification

- Type-check: passed after implementation; baseline failure is recorded in `impl-001.md`.
- Build: passed; existing large-chunk warning recorded in `impl-001.md`.
- Lint: non-zero for pre-existing `setUiFont` and `getActor` unused-symbol diagnostics; no unrelated files changed.
- Unit tests: 74 passed.
- Focused Playwright: 5 passed, including desktop and narrow viewport coverage.
- Interactive browser: review probe verified 150% shell zoom, main-region scrolling, no document scroll competition, sidebar control reachability, unchanged `ui-font`/`ui-dark`, and unscaled login.
- Workspace hygiene: passed.

## Final verification rerun

The frontend checks were rerun from the explicit prototype frontend directory after an initial repository-root invocation mistake:

- `npm run type-check`: passed.
- `npm run build`: passed; Vite emitted the existing 568.26 kB large-chunk warning.
- `npm test`: 74 passed, 0 failed.
- `npx playwright test tests/font-scale.spec.ts --project=chromium --reporter=list`: 5 passed.
- `npm run lint`: failed only on the pre-existing `setUiFont` and `getActor` unused-symbol diagnostics; no unrelated file was changed.
- `python scripts/check_workspace_hygiene.py`: passed.
- `openspec validate fix-font-scale-setting --type change --strict`: passed.

Interactive browser evidence confirmed the 150% output, main-region scrolling with `window.scrollY` unchanged, reachable lower Settings content, and a visible sidebar theme control. The shared browser preference was restored to 100% after verification.
