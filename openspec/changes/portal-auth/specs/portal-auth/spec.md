# Capability: Portal Authentication

## ADDED Requirements

### Requirement: Internal User Registration
The system SHALL allow an internal factory user to submit a registration with full name, company
email, employee ID, NIK/KTP, phone number, department, password, and explicit consent. A submitted
registration MUST start in the `pending` state and MUST NOT grant access until approved.

#### Scenario: Registration creates a pending account
- **WHEN** a user submits a valid registration form
- **THEN** the system responds `201` with status `pending` and the account cannot log in

#### Scenario: Duplicate identity is rejected
- **WHEN** a registration reuses an email, employee ID, NIK/KTP, or phone already registered
- **THEN** the system responds `409` and creates no account

#### Scenario: Invalid NIK/KTP or missing consent is rejected
- **WHEN** the NIK/KTP is not 16 digits, or consent is not given
- **THEN** the system responds `400` with a corrective message

### Requirement: Admin IT Verification
The system SHALL let an authenticated `admin` actor list pending registrations and approve or
reject each one. Rejected accounts MUST remain unable to log in.

#### Scenario: Admin approves a registration
- **WHEN** an admin approves a pending registration
- **THEN** the account becomes `active` and can log in

#### Scenario: Non-admin cannot access the queue
- **WHEN** an `employee` actor calls an admin endpoint
- **THEN** the system responds `403`

### Requirement: Password Login by Identifier
The system SHALL authenticate a user by any of employee ID, NIK/KTP, email, or phone plus password,
returning an opaque access token and actor context. Pending and rejected accounts MUST be refused.

#### Scenario: Approved user logs in
- **WHEN** an active user submits a matching identifier and password
- **THEN** the system responds `200` with an access token and actor context

#### Scenario: Pending user is blocked
- **WHEN** a pending user submits correct credentials
- **THEN** the system responds `403` and issues no token

#### Scenario: Wrong password is rejected
- **WHEN** the password does not match
- **THEN** the system responds `401` and issues no token

### Requirement: Password Change
The system SHALL allow an authenticated user to change their password by supplying the current
password and a new password meeting the policy, and MUST revoke existing sessions afterwards.

#### Scenario: Successful change revokes sessions
- **WHEN** a user changes their password with a correct current password
- **THEN** the change succeeds and the prior access token is no longer valid

#### Scenario: Wrong current password is rejected
- **WHEN** the supplied current password is incorrect
- **THEN** the system responds `401` and does not change the password

### Requirement: Password Recovery via One-Time Code
The system SHALL allow a user to request a one-time code sent to their registered email and use it
to set a new password. The request response MUST be generic regardless of whether the identifier
exists, to prevent account enumeration.

#### Scenario: Generic response for unknown identifier
- **WHEN** a recovery is requested for an identifier that does not exist
- **THEN** the system responds `200` with the same generic message as for a known identifier

#### Scenario: Reset with a valid code
- **WHEN** a user submits the correct unexpired code and a valid new password
- **THEN** the password is reset and the user can log in with it

#### Scenario: Invalid or expired code
- **WHEN** the submitted code is wrong, reused, or expired
- **THEN** the system responds `400` and does not change the password

### Requirement: Identifier Confidentiality
The system SHALL store passwords using a salted key-derivation function and MUST NOT retain the
plaintext NIK/KTP; only a hash (for lookup) and a masked value (for display) are kept.

#### Scenario: No plaintext NIK/KTP at rest
- **WHEN** a registration is stored
- **THEN** the NIK/KTP is persisted only as a SHA-256 lookup hash plus a masked last-4 value
