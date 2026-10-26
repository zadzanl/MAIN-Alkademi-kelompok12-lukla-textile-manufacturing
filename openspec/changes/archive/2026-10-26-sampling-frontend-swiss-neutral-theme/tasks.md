## 1. Theme foundation

- [x] 1.1 Rework light/dark semantic tokens in `prototypes/sampling-spec-rnd/frontend/src/index.css` to neutral near-white/near-black surfaces, muted accent/status colors, reduced radii, and restrained shadows.
- [x] 1.2 Align the Tailwind semantic bridge in `prototypes/sampling-spec-rnd/frontend/tailwind.config.js` without removing runtime safelist coverage.

## 2. Shared UI and representative views

- [x] 2.1 Update shared shell selectors/components for square geometry, hairline separation, focus visibility, and preserved touch targets.
- [x] 2.2 Audit and fix representative view-level gradients, excessive radii, saturated hardcoded chrome, and shadow conflicts without changing workflows or status meaning.

## 3. Evidence and verification

- [x] 3.1 Capture honest before/after light and dark screenshots from the localhost:3009 app and document viewport/state evidence under the change artifacts. (After captures saved; unavailable pristine before captures explicitly documented.)
- [ ] 3.2 Run type-check, build, lint, unit tests, browser smoke, and workspace hygiene; record results and update the change worklog.
