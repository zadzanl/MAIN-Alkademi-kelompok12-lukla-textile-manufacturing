## Context

The sampling/spec prototype already contains a Settings slider with a `FontScale` import and callback contract, but the parent app has no matching state or props. The dashboard shell is a fixed-height flex layout with an internally scrolling `<main>`, and the existing font-family preference uses `localStorage` on the root document.

## Goals / Non-Goals

**Goals:**

- Make the existing Settings control type-safe and functional.
- Support exactly 75%, 100%, 125%, and 150%.
- Restore the selected value after reload in the same browser.
- Scale the authenticated dashboard shell without hiding content or changing business workflows.
- Cover the regression with the existing local Playwright harness.

**Non-Goals:**

- No login-page scaling, font-family redesign, theme changes, backend persistence, account synchronization, new dependencies, or root E2E harness changes.

## Decisions

1. **Use a typed union and boundary parser.** `FontScale` is `75 | 100 | 125 | 150`; values read from storage and slider events are accepted only when they match that set. Invalid or missing values fall back to `100`.
2. **Reuse `localStorage`.** The existing `ui-font` and `ui-dark` preferences use browser-local storage, so the new `ui-font-scale` key follows the same visible preference boundary. Storage failures are caught so the current session remains usable.
3. **Apply CSS `zoom` to the authenticated shell with height compensation.** The shell already owns the sidebar, header, page content, and footer. `zoom` scales fixed pixel utilities and participates in layout, unlike `transform: scale()`. The root height is set to `calc(100vh / ratio)` so the existing inner `<main>` remains the visible scroll owner instead of creating a second document scroll region.
4. **Make the sidebar fill the scaled shell.** `Sidebar.tsx` currently uses `height: '100vh'`; changing it to `height: '100%'` keeps the bottom theme control inside the compensated shell at 150%.
5. **Keep the Settings control unchanged.** It already exposes a labeled range input, output value, and keyboard-compatible native range behavior. The parent supplies state and callback rather than duplicating the control.

## Risks / Trade-offs

- [Risk] Large zoom can expose existing narrow-screen layout constraints → verify 150% at desktop and narrow viewport sizes and report any unrelated constraint rather than hiding overflow.
- [Risk] A sidebar height fixed to `100vh` can extend beyond the compensated shell → use `height: 100%` on the existing sidebar and verify its bottom controls remain reachable.
- [Risk] `localStorage` can be unavailable or contain malformed data → guard reads and writes; use 100% in the current session when storage fails.
- [Risk] Browser engines differ in CSS `zoom` support → the supported local Chromium harness is the verification target; legacy-browser compatibility remains outside this prototype scope.

## Migration Plan

Add the state, storage boundary, shell style, and focused browser test. Rollback consists of reverting the listed frontend source and test changes; no data migration is needed because the preference is additive browser-local state.

## Open Questions

None. The user approved the four-value dashboard scaling behavior and local persistence plan.
