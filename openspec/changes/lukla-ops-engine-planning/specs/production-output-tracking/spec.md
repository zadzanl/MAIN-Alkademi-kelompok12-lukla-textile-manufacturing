# Capability: Production Output Tracking

## ADDED Requirements

### Requirement: Dynamic Sewing Line Capacity Allocation
The system SHALL allocate operators dynamically across parallel sewing lines based on active daily sewer headcount without rigid machine slot limits.

#### Scenario: Midweek active headcount adjustment
- **WHEN** five additional sewing operators are added to the floor mid-week
- **THEN** the system SHALL dynamically reallocate line stations and record piece output for the expanded headcount

### Requirement: Article and Client Piece-Rate Cards
The system SHALL maintain per-component piece-rate cards differentiated by garment article and client commercial terms.

#### Scenario: Component rate lookup during sewing assignment
- **WHEN** a sewer is assigned to a specific component operation
- **THEN** the system SHALL apply the active rate card established for that specific article and client

### Requirement: High-Frequency Thirty-Minute Output Logging
The system SHALL provide a touch-friendly interface for floor forepersons to record sewing piece output per operator and component in 30-minute intervals.

#### Scenario: Touch terminal sewing tally submission
- **WHEN** a foreperson inputs completed component counts at a 30-minute interval
- **THEN** the system SHALL record the timestamped output tally against the operator's queue

### Requirement: Assembly Queue to Quality Control Staging
The system SHALL transition completed garment assemblies into the QC inspection queue and defer piece-rate wage recognition until quality verification.

#### Scenario: Transfer of assembled units to QC queue
- **WHEN** garment assembly completes on the sewing line
- **THEN** the system SHALL place units into status Menunggu QC without immediately crediting payroll balances
