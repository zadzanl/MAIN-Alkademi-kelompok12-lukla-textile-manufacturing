## Why

The Sampling & Spec R&D frontend currently mixes Apple-style rounded surfaces, saturated semantic colors, gradients, and per-view radius utilities. That makes the dashboard visually softer and noisier than the requested Frappe/Fastino-inspired Swiss reference direction, especially in dense operational screens. This change establishes a restrained visual system with near-white/near-black foundations, square geometry, hairline structure, and color used only where it carries meaning.

## What Changes

- Rework the shared light and dark theme tokens used by the localhost:3009 Sampling & Spec R&D app.
- Shift surfaces toward near-white and pitch-black values while preserving readable intermediate layers for panels, inputs, tables, and overlays.
- Reduce saturation across persistent UI chrome; retain a small muted blue accent for primary actions and active states, with muted semantic colors limited to status meaning.
- Reduce default corner radii and remove decorative gradients, excessive shadows, and pill-shaped treatment from non-status controls.
- Align shared shell components and representative views with Swiss layout cues: hairline dividers, strong typographic hierarchy, grid structure, and whitespace instead of card chrome.
- Preserve 48px touch targets, keyboard focus visibility, light/dark switching, reduced-motion behavior, and existing application behavior.
- Add before/after screenshots for representative light and dark states to this OpenSpec change, with the existing Frappe/Fastino reference set linked as visual context.

## Capabilities

### New Capabilities
- `swiss-neutral-visual-system`: Defines the shared visual contract for neutral, square-edged, light/dark frontend presentation and screenshot evidence.

### Modified Capabilities
- None. This is a visual implementation change; no application workflow, API, persistence, or authorization requirements change.

## Impact

- Primary stylesheet and Tailwind token bridge in `prototypes/sampling-spec-rnd/frontend/src/index.css` and `tailwind.config.js`.
- Shared shell components in `src/App.tsx`, `src/components/Sidebar.tsx`, and `src/components/Header.tsx`.
- Representative page/view classes where hardcoded rounded or saturated utilities bypass the token system.
- Existing browser smoke/evidence workflow under `prototypes/sampling-spec-rnd/frontend/`.
- No new runtime dependency, API endpoint, backend behavior, or data model.
