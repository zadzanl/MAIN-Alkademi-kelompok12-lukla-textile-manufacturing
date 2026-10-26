## Why

The Settings page already renders a text-size slider, but `App.tsx` does not provide the slider state or callback, so the frontend does not type-check and users cannot change the interface size. The approved fix restores the control contract and makes the selected size persist locally.

## What Changes

- Add the supported `FontScale` type and state in the sampling/spec frontend.
- Validate and persist 75%, 100%, 125%, and 150% in browser-local storage.
- Apply the selected scale to the authenticated dashboard shell while keeping scaled content reachable by the existing main scroll region.
- Add focused Playwright coverage for interaction, persistence, invalid storage fallback, and scaled content visibility.

## Capabilities

### New Capabilities
- `font-scale-preference`: Provides an accessible, validated, browser-local dashboard text-size preference.

### Modified Capabilities

None.

## Impact

- Frontend source: `prototypes/sampling-spec-rnd/frontend/src/App.tsx` and `prototypes/sampling-spec-rnd/frontend/src/components/Sidebar.tsx`.
- Frontend browser regression coverage: `prototypes/sampling-spec-rnd/frontend/tests/font-scale.spec.ts`.
- No backend endpoint, database, dependency, authentication, font-family, theme, or root E2E harness changes.
