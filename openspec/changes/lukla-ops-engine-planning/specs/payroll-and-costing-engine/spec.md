# Capability: Payroll & Costing Engine

## ADDED Requirements

### Requirement: Weekly Saturday Piece-Rate Payroll Calculation
The system SHALL calculate weekly piece-rate wages every Saturday based exclusively on QC-verified component assembly outputs.

#### Scenario: Weekly piece-rate wage compilation
- **WHEN** the Saturday payroll cycle executes
- **THEN** the system SHALL aggregate all QC-passed component counts multiplied by applicable piece rates for each operator

#### Scenario: Unresolved financial rule gate
- **WHEN** a payroll, QC, or financial operation references an `UNRESOLVED / PRODUCTION_BLOCKED` rule
- **THEN** the operation SHALL return `FINANCIAL_RULE_PENDING` and SHALL NOT use a development-only default

### Requirement: Variable Production Meal Allowance Disbursement
The system SHALL calculate floating meal allowances at 10 to 15 percent of total sewing wages generated in a production period.

#### Scenario: Meal allowance calculation
- **WHEN** the weekly payroll is compiled with a configured 12 percent meal allowance rate
- **THEN** the system SHALL calculate the meal allowance as 12 percent of the verified sewing wage total

### Requirement: Quality Bonus Pool Settlement and Payout
The system SHALL disburse the 3-way quality bonus pool alongside the weekly Saturday payroll settlement.

#### Scenario: Bonus pool disbursement with weekly payroll
- **WHEN** weekly payroll statements are generated
- **THEN** the system SHALL include the one-third bonus pool share for each qualifying foreperson and operations head

### Requirement: Monthly Factory Operational Overhead Allocation
The system SHALL calculate monthly factory overhead expenses (electricity, water, internet, facility operations) divided by total units produced during the month.

#### Scenario: Monthly overhead unit allocation
- **WHEN** monthly accounting close is triggered with recorded operational expenses
- **THEN** the system SHALL divide total factory overhead by the aggregate monthly finished unit volume
