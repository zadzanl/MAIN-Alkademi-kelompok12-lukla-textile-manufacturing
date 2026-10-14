# Capability: Payroll Engine Runtime

## ADDED Requirements

### Requirement: Versioned Payroll Run Lifecycle
The system SHALL persist every payroll calculation as a versioned run bound to a payroll period, and MUST NOT mutate a run once it has been approved. Each run SHALL carry the rule version it was calculated under and an input hash over its consumed credits, and a recalculation SHALL produce a new version rather than overwriting the previous one. Corrections after approval SHALL be expressed as a compensating reversal or an authorized adjustment, never as an edit of a posted run.

#### Scenario: Recalculation creates a new version
- **WHEN** a payroll period that already has a calculated run is recalculated after new verified output is assigned to it
- **THEN** the system SHALL create a new run version with its own rule version and input hash, and SHALL leave the previous version readable and unchanged

#### Scenario: Approved run is immutable
- **WHEN** an approved run is targeted by a recalculation or an edit
- **THEN** the system SHALL reject the mutation and SHALL require a reversal or an authorized adjustment instead

---

### Requirement: Calculation-Time Financial Rule Enforcement
The system SHALL resolve every financial rule version referenced by a payroll, bonus, or overhead calculation, and MUST return `FINANCIAL_RULE_PENDING` without persisting any monetary amount when any referenced rule version is not `APPROVED`. The system MUST NOT substitute a development default, a seeded demo value, or an environment variable for an unapproved rule, and only the `Owner` role SHALL be able to approve a rule version, with evidence recorded.

#### Scenario: Unapproved rule blocks computation
- **WHEN** a calculation is requested for a period whose referenced rule version has status `PENDING`
- **THEN** the system SHALL respond `409 FINANCIAL_RULE_PENDING`, SHALL leave the period in `PENDING_RULE`, and SHALL write no wage credit, payroll item, bonus accrual, or overhead allocation

#### Scenario: Proposal is not authorization
- **WHEN** a financial rule is proposed without an approval record carrying an evidence file
- **THEN** the system SHALL keep the rule version at `PENDING` and SHALL continue to block every calculation that references it

---

### Requirement: Verified-Output-Only Wage Eligibility
The system SHALL compute piece-rate wages exclusively from verified sewing tallies and quality-passed garment units that carry an immutable piece-rate snapshot, and MUST exclude unverified tallies and units still awaiting inspection from wage eligibility. A unit returned for repair SHALL receive at most one wage credit across all inspection cycles, and a duplicate credit attempt SHALL be rejected.

#### Scenario: Unverified and pending units earn nothing
- **WHEN** a period contains a recorded-but-unverified tally and a unit awaiting quality inspection
- **THEN** the calculation SHALL exclude both from eligible units and from the wage total

#### Scenario: Repair does not double-credit
- **WHEN** a unit previously credited is returned for repair and subsequently passes inspection
- **THEN** the system SHALL credit that unit once in total and SHALL reject a second credit for the same unit

---

### Requirement: Idempotent Service-Authenticated Job Invocation
The system SHALL expose the scheduled payroll and overhead runs as HTTP endpoints authenticated by a service credential, and MUST NOT accept an employee session token as authority for them. Each invocation SHALL be idempotent on its key so that a retried delivery produces a single job run, and a job SHALL record a terminal status of `SUCCEEDED`, `BLOCKED`, or `FAILED` that is readable through the job readback operation.

#### Scenario: Duplicate delivery produces one run
- **WHEN** the same job invocation is delivered twice with the same idempotency key
- **THEN** the system SHALL execute it once and SHALL return the original accepted result for the replay

#### Scenario: Employee token is not job authority
- **WHEN** a job endpoint is called with an employee bearer token
- **THEN** the system SHALL refuse the request and SHALL NOT execute the job

#### Scenario: Blocked rule is not reported as success
- **WHEN** a job runs while a referenced rule version is not approved
- **THEN** the job run SHALL record status `BLOCKED` and SHALL NOT be reported as successful

---

### Requirement: Tenant-Isolated Payroll Data Access
The system SHALL enforce row level security on every tenant-scoped payroll table with both `ENABLE` and `FORCE ROW LEVEL SECURITY`, SHALL install the request context before executing any operation, and MUST reject a request that lacks a valid tenant context instead of returning rows. Reads SHALL remain scoped by tenant, and where applicable by legal stock owner and order beneficiary, independently of any caller-supplied filter header.

#### Scenario: Missing context is refused
- **WHEN** a payroll read is executed without an installed tenant context
- **THEN** the system SHALL reject the request with `TENANT_CONTEXT_MISSING` and SHALL return no rows

#### Scenario: Cross-tenant read yields nothing
- **WHEN** an authenticated user requests payroll records belonging to another tenant
- **THEN** the system SHALL return no rows and SHALL NOT disclose the existence of those records

---

### Requirement: Machine-Readable Payroll Verification Evidence
The system SHALL emit a machine-readable verification bundle for every payroll test run, containing the stable test identifiers assigned to the payroll and quality-control acceptance tests and reporting each test as `PASS`, `FAIL`, `BLOCKED`, or `NOT_RUN`. A test layer that was not executed MUST be reported as `NOT_RUN` or `BLOCKED` and MUST NOT be reported as `PASS`, and a run whose required evidence file is missing SHALL cause the evidence collector to exit non-zero.

#### Scenario: Unresolved remainder is reported blocked
- **WHEN** the bonus pool division test is executed while the remainder policy is unresolved
- **THEN** the bundle SHALL report that test as `BLOCKED` and SHALL NOT assert a payout split

#### Scenario: Missing layer is not a pass
- **WHEN** a required evidence file is absent from the bundle
- **THEN** the evidence collector SHALL exit non-zero and SHALL identify the missing file
