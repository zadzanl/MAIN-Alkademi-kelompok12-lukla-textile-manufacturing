## Context

The Sampling & Spec R&D React/Vite frontend already centralizes most visual tokens in `src/index.css` and bridges semantic colors through Tailwind. It currently mixes Apple-like rounded surfaces, saturated accents, gradients, and shadows. The approved change is visual only and must coexist with unrelated uncommitted product work in this checkout.

## Goals / Non-Goals

**Goals:**
- Establish a neutral, high-contrast Swiss-inspired light/dark visual system.
- Use square or minimally rounded geometry, hairlines, whitespace, and typography for hierarchy.
- Preserve semantic status colors, interaction behavior, accessibility, and existing workflows.
- Produce honest before/after browser evidence for both themes.

**Non-Goals:**
- No API, data, auth, routing, dependency, or workflow changes.
- No redesign of the UHUY portal or root E2E harness.
- No blind replacement of every radius or color where it encodes status or interaction meaning.

## Decisions

1. **Token-first implementation.** Update the existing CSS variable layer before component selectors. This minimizes drift and keeps dark mode class-based. A new design-system dependency would add cost without solving the existing token bypasses.
2. **Neutral foundation with muted blue accent.** Use near-white light surfaces and near-black dark surfaces with intermediate levels for hierarchy. Reserve muted blue for primary actions and active navigation. Keep muted green/amber/red for semantic states so status is not flattened into gray.
3. **Borders before shadows.** Use hairline borders and surface contrast as the primary separation mechanism. Retain only restrained shadows for overlays where depth is necessary.
4. **Minimal geometry change.** Lower shared radii and remove decorative gradients in shared chrome, while allowing compact status badges to remain rounded when their shape communicates status.
5. **Evidence from the running app.** Capture screenshots through the available browser at the existing localhost:3009 app. If a view is unavailable, record the limitation rather than fabricate evidence.

## Risks / Trade-offs

- [Risk] Pure black/white can flatten surface hierarchy → use explicit near-black panel/input levels and light-mode gray levels.
- [Risk] Desaturation can weaken status recognition → preserve semantic hues and pair status with text/icons already present.
- [Risk] Existing hardcoded utilities can bypass tokens → audit representative pages and shared components, not perform unsafe global replacement.
- [Risk] Unrelated working-tree edits can be overwritten → limit edits to the change's target files and inspect diffs before verification.

## Migration Plan

Apply CSS tokens and shared selectors first, then targeted component/view cleanup. Revert the change by restoring only the files listed in the implementation diff; no data migration or deployment migration is involved.

## Open Questions

None. The visual direction and scope were approved by the user.
