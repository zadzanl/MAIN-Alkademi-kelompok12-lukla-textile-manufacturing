# swiss-neutral-visual-system Specification

## Purpose
TBD - created by archiving change sampling-frontend-swiss-neutral-theme. Update Purpose after archive.
## Requirements
### Requirement: Neutral light and dark foundations
The frontend SHALL use near-white light page/panel surfaces and near-black dark page/panel surfaces with at least one intermediate surface level in each theme.

#### Scenario: Light theme surfaces
- **WHEN** the application is rendered in light mode
- **THEN** page, panel, input, and overlay surfaces remain visually distinct without saturated backgrounds

#### Scenario: Dark theme surfaces
- **WHEN** the application is rendered in dark mode
- **THEN** page, panel, input, and overlay surfaces remain visually distinct without relying on pure white text everywhere

### Requirement: Restrained color semantics
Persistent UI chrome SHALL use neutral colors with a muted blue reserved for primary/active states, while success, warning, and error colors remain distinguishable and lower-saturation.

#### Scenario: Primary and active states
- **WHEN** a primary action or active navigation item is rendered
- **THEN** it uses the shared muted brand token rather than a hardcoded saturated color

#### Scenario: Operational status
- **WHEN** a success, warning, or error status is rendered
- **THEN** its semantic distinction remains visible through color plus existing text/icon context

### Requirement: Swiss geometry and separation
Shared surfaces and controls SHALL prefer square or minimally rounded geometry, hairline borders, whitespace, and typographic hierarchy over decorative gradients, large radii, and heavy shadows.

#### Scenario: Shared surface
- **WHEN** a shared card, panel, table, or shell surface is rendered
- **THEN** it uses the shared neutral surface and hairline token with no decorative gradient

#### Scenario: Status badge
- **WHEN** a compact status badge is rendered
- **THEN** it MAY retain a compact rounded shape when that shape communicates status, without forcing all controls to be pills

### Requirement: Existing interaction contracts remain intact
The visual change SHALL preserve theme switching, preference persistence, keyboard focus visibility, reduced-motion behavior, 48px touch targets, routes, API calls, and application workflows.

#### Scenario: Theme toggle
- **WHEN** the user switches between light and dark mode
- **THEN** the existing class-based theme state and persistence behavior continue to work

#### Scenario: Accessibility behavior
- **WHEN** the user navigates with keyboard or reduced-motion preferences
- **THEN** visible focus indicators remain available and essential information does not depend on animation

### Requirement: Screenshot evidence
The change SHALL include representative before/after screenshots for light and dark modes, with viewport and state notes.

#### Scenario: Evidence set
- **WHEN** implementation is complete
- **THEN** the OpenSpec change contains four honest screenshots or an explicit record of any unavailable capture

