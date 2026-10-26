# uhuy-b2b-portal Specification

## Purpose
TBD - created by archiving change uhuy-b2b-portal. Update Purpose after archive.
## Requirements
### Requirement: External Client Registration
The system SHALL allow an external maklon client to submit a registration with company name,
contact name, email, phone, password, and explicit consent. A submitted registration MUST
start in the `pending` state and MUST NOT grant access until approved by an internal actor.

#### Scenario: Registration creates a pending client
- **WHEN** a client submits a valid registration form
- **THEN** the system responds `201` with status `pending` and a generated `client_id`, and the account cannot log in

#### Scenario: Duplicate identity is rejected
- **WHEN** a registration reuses an email or phone already registered
- **THEN** the system responds `409` and creates no account

#### Scenario: Invalid input is rejected
- **WHEN** the email is malformed, the phone is not 9–15 digits, the password lacks a letter or digit, or consent is not given
- **THEN** the system responds `400` with a corrective message

### Requirement: Internal Approval of Client Accounts
The system SHALL let an authenticated internal `admin` actor list pending client registrations
and approve or reject each one. Rejected accounts MUST remain unable to log in.

#### Scenario: Admin approves a registration
- **WHEN** an admin approves a pending registration
- **THEN** the account becomes `active` and can log in as role `client`

#### Scenario: Client cannot access the approval queue
- **WHEN** a `client` actor calls an admin endpoint
- **THEN** the system responds `403`

### Requirement: External Client Login
The system SHALL authenticate a client by email or phone plus password, returning an opaque
access token and actor context that includes the client's `clientId`. Pending and rejected
accounts MUST be refused.

#### Scenario: Active client logs in
- **WHEN** an active client submits matching credentials
- **THEN** the system responds `200` with an access token and actor context containing `clientId`

#### Scenario: Pending client is blocked
- **WHEN** a pending client submits correct credentials
- **THEN** the system responds `403` and issues no token

### Requirement: Password Change and Recovery
The system SHALL allow an authenticated client to change their password (revoking existing
sessions) and to recover access via a one-time code sent to their registered email, with a
generic response for unknown identifiers.

#### Scenario: Successful change revokes sessions
- **WHEN** a client changes their password with the correct current password
- **THEN** the change succeeds and the prior access token is no longer valid

#### Scenario: Recovery request is generic
- **WHEN** a recovery is requested for an identifier that does not exist
- **THEN** the system responds `200` with the same generic message as for a known identifier

### Requirement: Client-Scoped Data Visibility
The system SHALL return orders, consigned stock, and request history scoped to the
authenticated client's `client_id` only. The `client_id` MUST be resolved from the session
and MUST NOT be accepted from the request body or query.

#### Scenario: Own data is visible
- **WHEN** an active client requests their orders, stock, or requests
- **THEN** every returned row carries that client's `client_id`

#### Scenario: Another client's record is inaccessible
- **WHEN** a client requests an order id that belongs to a different client
- **THEN** the system responds `404` and discloses nothing about that record

#### Scenario: Client data endpoints require authentication
- **WHEN** an unauthenticated caller requests client data
- **THEN** the system responds `401`

#### Scenario: Internal admin is not a client actor
- **WHEN** an `admin` actor calls a client data endpoint
- **THEN** the system responds `403`

### Requirement: Order and Sample Request Submission
The system SHALL allow an authenticated client to submit a production-order request and a
design/sample request. A submitted request MUST start in the `submitted` state and be visible
only to its owning client.

#### Scenario: Client submits an order request
- **WHEN** a client submits an order request with an article name, positive quantity, and a valid maklon scheme
- **THEN** the system responds `201` with status `submitted` and the request appears in that client's request list

#### Scenario: Invalid scheme is rejected
- **WHEN** the submitted scheme is not one of CMT, Semi-CMT, or Full Package
- **THEN** the system responds `400` and creates no request

#### Scenario: Requests do not leak across clients
- **WHEN** a client submits a request
- **THEN** it never appears in another client's request list

### Requirement: External Portal Marker
The external portal frontend SHALL be visually and configurationally distinguishable from the
internal dashboard, using a dedicated accent, a persistent "PORTAL EKSTERNAL" marker, and the
`VITE_PORTAL_SCOPE=external` build flag.

#### Scenario: Marker is present
- **WHEN** the external portal loads (login or authenticated shell)
- **THEN** the "PORTAL EKSTERNAL" marker is visible and the accent differs from the internal app

