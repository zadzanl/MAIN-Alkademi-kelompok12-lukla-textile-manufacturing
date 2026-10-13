# Capability: Quality Control & Inspection

## ADDED Requirements

### Requirement: Quality Inspection and Routing Triage
The system SHALL record inspection dispositions for every finished garment unit, categorizing items into Pass, Repair, or Reject.

#### Scenario: Garment disposition triage
- **WHEN** a QC inspector evaluates a finished garment unit
- **THEN** the system SHALL route Pass units to inventory/payroll, Repair units to rework, and Reject units to write-off

### Requirement: Defect Repair Routing Without Double Piece-Rate Credit
The system MUST return Repair units to the original sewing operator while preventing duplicate piece-rate wage credit for the reworked unit.

#### Scenario: Repair return without duplicate wage credit
- **WHEN** a repaired unit passes subsequent QC inspection
- **THEN** the system SHALL credit the single approved piece-rate wage and prevent secondary payment for the repair cycle

### Requirement: Quality Control Bonus Pool Calculation
The system SHALL calculate a quality bonus pool accrued from the volume of units passing QC inspection across production batches.

#### Scenario: Bonus pool accrual from QC-passed units
- **WHEN** 3000 garment units successfully pass QC inspection
- **THEN** the system SHALL calculate the total bonus pool based on the established per-unit rate

### Requirement: Three-Way Equal Quality Bonus Distribution
The system SHALL divide the accrued quality bonus pool equally among three recipients: two line forepersons and one operations head.

#### Scenario: Equal three-way bonus pool division
- **WHEN** the weekly quality bonus pool is finalized for distribution
- **THEN** the system SHALL divide the pool into three equal shares (÷3) for the two forepersons and one operations head
