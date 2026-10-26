# qc-mes-runtime Specification

## Purpose
TBD - created by archiving change lukla-qc-mes-engine. Update Purpose after archive.
## Requirements
### Requirement: Assembly-Level Inspection Disposition
The system SHALL record every quality inspection against a finished garment assembly, not against an individual component piece, and SHALL persist each inspection as an append-only row carrying the assembly it classifies, the inspector, the disposition, and a sequence number unique within that assembly. The assembly's status SHALL move to `QC_PASS`, `REWORK`, or `REJECT_SCRAP` according to the recorded disposition, and an assembly that is still `ASSEMBLING` MUST NOT be inspectable.

#### Scenario: Disposition moves the assembly
- **WHEN** an inspector records `PASS`, `REPAIR`, or `REJECT` for an assembly awaiting inspection
- **THEN** the system SHALL append one inspection row with the next sequence number for that assembly and SHALL set the assembly status to `QC_PASS`, `REWORK`, or `REJECT_SCRAP` respectively

#### Scenario: Assembly in progress is not inspectable
- **WHEN** an inspection is requested for an assembly whose status is `ASSEMBLING`
- **THEN** the system SHALL reject the request with `INVALID_STATE` and SHALL append no inspection row

---

### Requirement: Terminal Dispositions Without Override
The system SHALL treat `QC_PASS` and `REJECT_SCRAP` as terminal assembly states, and in this release MUST NOT allow a new inspection to override a final `PASS` or `REJECT`. A correction after final quality control SHALL require a separately authorized policy rather than a further inspection through this operation.

#### Scenario: Final pass cannot be re-inspected
- **WHEN** a new inspection is requested for an assembly already in `QC_PASS`
- **THEN** the system SHALL reject the request with `INVALID_STATE` and SHALL leave the recorded inspection history unchanged

#### Scenario: Rework may be re-inspected
- **WHEN** an inspection is requested for an assembly in `REWORK`
- **THEN** the system SHALL accept it and SHALL append a new inspection row with the next sequence number

---

### Requirement: Defect Taxonomy Selection for Repair and Reject
The system SHALL require at least one defect for a `REPAIR` or `REJECT` disposition, MUST require every defect code to exist in the tenant's configured defect taxonomy, and MUST refuse an unknown code instead of storing it. A `PASS` disposition MUST NOT carry a defect. Each defect SHALL identify a component piece allocated to the inspected assembly, and a component piece MUST NOT appear twice in one inspection.

#### Scenario: Repair without a defect is refused
- **WHEN** a `REPAIR` disposition is submitted with an empty defect list
- **THEN** the system SHALL reject the request with `VALIDATION_ERROR` and SHALL record no inspection

#### Scenario: Unknown defect code is refused
- **WHEN** a `REJECT` disposition names a defect code that is not in the configured taxonomy
- **THEN** the system SHALL reject the request with `VALIDATION_ERROR` naming the code and SHALL record no inspection

#### Scenario: Defect must belong to the assembly
- **WHEN** a defect names a component piece that is not allocated to the inspected assembly
- **THEN** the system SHALL reject the request with `VALIDATION_ERROR` and SHALL record no inspection

---

### Requirement: Repair Routing Derived From the Immutable Component Source
The system SHALL route each defect of a `REPAIR` disposition to the operator recorded on that component piece's immutable allocation, and MUST NOT accept a repair operator from the caller. Repair SHALL create no new wage eligibility, and a unit returned for repair and later passed SHALL receive at most one wage credit across all inspection cycles.

#### Scenario: Repair returns to the original operator
- **WHEN** an assembly is marked `REPAIR` with a defect on a component piece sewn by operator S1
- **THEN** the system SHALL produce exactly one repair route for that piece naming S1, and SHALL produce no wage credit and no bonus accrual

#### Scenario: Rework does not double-credit
- **WHEN** a repaired assembly is inspected again and passes
- **THEN** the system SHALL credit each allocated component piece exactly once in total, and SHALL NOT credit the rework cycle

---

### Requirement: Single First-Pass Wage Eligibility and Single Bonus Accrual
On the first `PASS` of an assembly the system SHALL produce exactly one eligibility event for that assembly, exactly one wage credit per allocated component piece valued from that piece's immutable piece-rate snapshot, and exactly one quality bonus accrual for the assembly valued from the approved rule's bonus rate. A `REJECT` disposition SHALL produce no eligibility event, no wage credit, and no bonus accrual, and MUST NOT apply an automatic wage deduction or material-cost recovery.

#### Scenario: First pass credits each piece once
- **WHEN** an assembly of three allocated component pieces passes inspection
- **THEN** the system SHALL produce one eligibility event for the assembly, three wage credits valued from the respective piece-rate snapshots, and one bonus accrual

#### Scenario: Reject earns nothing and deducts nothing
- **WHEN** an assembly is marked `REJECT`
- **THEN** the system SHALL produce no eligibility event, no wage credit, and no bonus accrual, and SHALL NOT create a deduction against the operators

---

### Requirement: Unvalued Eligibility Under a Pending Rule
When the bonus rule version in force is not `APPROVED`, the system SHALL still record the disposition and the eligibility event carrying that rule version reference, and MUST NOT produce a bonus accrual, a valued wage credit, or any substitute amount derived from a fallback constant, environment variable, or demo value. Later valuation SHALL use the rule version carried by the eligibility event.

#### Scenario: Pending rule records an unvalued event
- **WHEN** an assembly passes while the rule version in force is `PENDING`
- **THEN** the system SHALL record the inspection and an eligibility event referencing that rule version, SHALL produce no bonus accrual and no valued wage credit, and SHALL report no error

#### Scenario: The recorded event pins the rule version
- **WHEN** an assembly passes while the rule version in force is `PENDING`
- **THEN** the recorded eligibility event SHALL carry that rule version reference and the disposition timestamp, so that a later valuation can resolve that version instead of whichever rule is current at valuation time

---

### Requirement: Idempotent Inspection Recording
The system SHALL make inspection recording idempotent on the caller's idempotency key. A replayed request whose key matches a stored inspection of the same assembly and whose payload is unchanged SHALL return the stored decision without appending a second inspection row, and a replay whose payload differs SHALL be rejected with `IDEMPOTENCY_CONFLICT`. A replay SHALL be served before the terminal-state check, so a retried delivery of the inspection that produced a final `PASS` or `REJECT` SHALL succeed.

#### Scenario: Retried delivery returns the stored decision
- **WHEN** the same inspection request is delivered twice with one idempotency key
- **THEN** the system SHALL append one inspection row and SHALL return the original decision for the replay

#### Scenario: Changed payload on the same key conflicts
- **WHEN** an inspection request reuses a key already recorded for the assembly with a different disposition or defect list
- **THEN** the system SHALL reject the request with `IDEMPOTENCY_CONFLICT` and SHALL append no inspection row

#### Scenario: Retry after a final disposition is not an override
- **WHEN** the delivery that produced `QC_PASS` is retried after the assembly reached its terminal state
- **THEN** the system SHALL return the stored decision and SHALL NOT reject it as an invalid state

---

### Requirement: QC Queue Summary by Current Assembly Status
The system SHALL produce the quality summary consumed by the operations dashboard by counting each assembly exactly once according to its current status: passed assemblies as `passCount`, assemblies in `REWORK` as `repairCount`, and `REJECT_SCRAP` assemblies as `rejectCount`. Assemblies still awaiting inspection or still assembling SHALL NOT be counted in any of the three, and an assembly inspected more than once MUST NOT be counted more than once.

#### Scenario: Reworked assembly counts once
- **WHEN** an assembly is repaired and later passes
- **THEN** the summary SHALL count it as one pass and SHALL NOT also count it as a repair

#### Scenario: Awaiting inspection is not a disposition
- **WHEN** the queue contains assemblies in `MENUNGGU_QC`
- **THEN** the summary SHALL leave all three counters unchanged for them

---

### Requirement: Database-Enforced QC Invariants
The system SHALL enforce the assembly state transitions, the append-only inspection log, the defect rules, the single-allocation rule, and tenant isolation in the database itself, so that a caller writing SQL directly as the runtime role cannot bypass them. The runtime role MUST NOT hold any privilege to edit or delete a recorded inspection or defect, and MUST NOT hold a general update privilege on the shop-floor tables it reads.

#### Scenario: The database refuses an override
- **WHEN** an inspection row is inserted for an assembly already in `QC_PASS` or `REJECT_SCRAP`
- **THEN** the database SHALL refuse the row and SHALL leave the recorded inspection history unchanged

#### Scenario: The database refuses an unready assembly
- **WHEN** an inspection row is inserted for an assembly still in `ASSEMBLING`
- **THEN** the database SHALL refuse the row

#### Scenario: A disposition moves the pieces with the assembly
- **WHEN** a first `PASS` is recorded
- **THEN** the assembly and every component piece allocated to it SHALL hold the disposition's status within the same transaction, so that the payroll engine's quality-passed filter sees them

#### Scenario: The inspection log cannot be rewritten
- **WHEN** the runtime role attempts to update or delete a recorded inspection or defect
- **THEN** the database SHALL deny the statement

#### Scenario: A tenant without context reads nothing
- **WHEN** the runtime role reads the QC tables without an installed tenant context
- **THEN** the database SHALL return zero rows

#### Scenario: An allocation cannot cross tenants
- **WHEN** a component allocation references a piece or an assembly belonging to another tenant
- **THEN** the database SHALL refuse the row at the relational layer

