## ADDED Requirements

### Requirement: State-aware journey
The Ops Engine SHALL display guidance for a selected sample revision or saved order using confirmed business records rather than the current page index. The journey SHALL distinguish `draft`, `pending_approval`, `approved`, `consent_recorded`, `ready_for_production`, `blocked`, and `unavailable` states as applicable, and SHALL never mark a milestone complete solely because a user viewed a page.

#### Scenario: No order exists yet
- **WHEN** a user views a sample revision that has not passed the required approvals
- **THEN** the guide identifies the missing approval or consent and names the responsible role instead of displaying a completed order step

#### Scenario: Saved order is ready
- **WHEN** an authorized user views a saved handoff with team approval and recorded client consent
- **THEN** the guide identifies the order as `READY_FOR_PRODUCTION`, shows the accepted sample revision, and states that production, warehouse, QC, and delivery are outside the connected journey

#### Scenario: Downstream data is unavailable
- **WHEN** the guide cannot verify a downstream production, material, QC, delivery, or order record
- **THEN** it shows an explicit unavailable/waiting state and does not infer completion from mock data, page navigation, or a mismatched identifier

### Requirement: Approval and consent records
The backend SHALL record team approval and staff-recorded external client consent as separate append-only records tied to one sample revision. Consent SHALL capture the staff actor, timestamp, method (`EMAIL`, `DOCUMENT`, or `REFERENCE`), non-empty reference, and optional note. The first release SHALL not require uploading or serving consent files.

#### Scenario: Staff records consent reference
- **WHEN** an authenticated Sample-team staff member submits a valid consent method and reference for an approved revision
- **THEN** the system stores one consent record for that revision and returns the recorded status without adding client approval permissions

#### Scenario: Consent reference is invalid
- **WHEN** the consent method is unsupported or the reference is empty/too long
- **THEN** the system rejects the request with a validation error and does not create a partial consent record

#### Scenario: Duplicate consent submission
- **WHEN** the same consent operation is retried with the same idempotency key and payload
- **THEN** the system returns the original result without creating a second consent record

### Requirement: Authorized order handoff
The backend SHALL allow only an authenticated Owner or Mandor to create a saved order from an approved sample revision that has both team approval and recorded external client consent. The handoff SHALL save the accepted revision snapshot, order number, client identity, positive batch quantity, descriptive production line, optional target delivery date, notes, authorization record, and status `READY_FOR_PRODUCTION`. It SHALL NOT start production, allocate material, purchase stock, perform QC, or mark delivery complete.

#### Scenario: Valid handoff
- **WHEN** an Owner or Mandor submits a valid handoff for a revision with both required records
- **THEN** the system atomically creates one saved order and confirmation, links the revision to that order, and returns the order with status `READY_FOR_PRODUCTION`

#### Scenario: Missing approval or consent
- **WHEN** an Owner or Mandor submits a handoff before team approval or external consent exists
- **THEN** the system rejects the handoff with an actionable blocked reason and creates neither an order nor a partial confirmation

#### Scenario: Unauthorized handoff
- **WHEN** a client, Sample-team user, Warehouse user, Tailor, QC Inspector, or unauthenticated caller submits a handoff
- **THEN** the system rejects the request server-side and creates no order

#### Scenario: Handoff retry
- **WHEN** the same handoff is retried with the same idempotency key and identical payload
- **THEN** the system returns the original order result without creating a second order or confirmation

#### Scenario: Conflicting order number
- **WHEN** a valid handoff uses an order number already used within the tenant
- **THEN** the system rejects the request with a conflict and leaves the existing order unchanged

### Requirement: Tenant and client data scope
The backend SHALL derive tenant and client scope from the authenticated session rather than trusting query parameters. A client SHALL read only records belonging to its mapped client identity; an unmapped client SHALL receive no client records. Staff roles SHALL receive only the records permitted by their role and tenant.

#### Scenario: Client reads own order
- **WHEN** a mapped client requests its own saved order
- **THEN** the system returns the order and its state-aware guidance

#### Scenario: Client attempts cross-client read
- **WHEN** a client requests an order or sample revision belonging to another client
- **THEN** the system returns not-found/denied behavior without revealing the other client's record

#### Scenario: Scope query is forged
- **WHEN** a caller changes tenant or client query parameters without a matching authenticated scope
- **THEN** the server ignores/rejects the forged scope and does not disclose or mutate another scope's data

### Requirement: Accessible guidance controls
The frontend SHALL provide a maintainable source component for the journey with a semantic heading/landmark and ordered steps. Current, waiting, blocked, unavailable, and completed states SHALL be conveyed in text in addition to visual styling. Interactive navigation SHALL use keyboard-operable controls with visible focus, accessible names, and a non-color-only status cue; the guide SHALL not replace the existing sidebar navigation.

#### Scenario: Keyboard navigation
- **WHEN** a keyboard user tabs through the guide
- **THEN** every actionable step and next-action control is reachable, visibly focused, and labeled with its destination or action

#### Scenario: Screen-reader status
- **WHEN** a user opens a guide for a sample or order
- **THEN** the landmark/heading identifies the journey, the current step is programmatically identified, and status text explains who must act or what is unavailable

#### Scenario: Narrow viewport
- **WHEN** the guide is displayed at the existing responsive breakpoint
- **THEN** steps remain readable and actionable in a vertical layout without horizontal clipping or requiring color perception
