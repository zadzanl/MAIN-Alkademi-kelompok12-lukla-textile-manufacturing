## 1. Preference wiring

- [x] 1.1 Add the typed `FontScale` union, safe local-storage parser, state, persistence, and Settings props in `prototypes/sampling-spec-rnd/frontend/src/App.tsx`.
- [x] 1.2 Apply the selected scale to the authenticated dashboard shell with compensated height, and make the existing sidebar fill that shell without changing the login path or navigation behavior.

## 2. Regression coverage

- [x] 2.1 Add `prototypes/sampling-spec-rnd/frontend/tests/font-scale.spec.ts` covering slider interaction, all supported values, reload persistence, invalid-storage fallback, and scaled content measurement.
- [x] 2.2 Verify the scaled Settings view remains scrollable at desktop and narrow viewport sizes using the existing Playwright harness.

## 3. Verification and record

- [x] 3.1 Run type-check, build, lint, unit tests, focused Playwright tests, and workspace hygiene; record exact results in the implementation artifact. Lint remains non-zero only for pre-existing unused-symbol diagnostics documented in `artifacts/impl-001.md`.
