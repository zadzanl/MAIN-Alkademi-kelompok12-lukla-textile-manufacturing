# Capability: Warehouse & Cutting Controls

## ADDED Requirements

### Requirement: Warehouse Consignment and Multi-Client Stock Management
The system SHALL manage raw material inventory segregation and consignment stock receipts across multiple client tenants.

#### Scenario: Consignment material receipt
- **WHEN** raw fabric rolls are received under a CMT agreement
- **THEN** the system SHALL record custodial inventory attributed specifically to the originating client tenant

### Requirement: Cutting Phase Operational Controls
The system SHALL track material transfers into the cutting room phase in accordance with scheduled production requirements.

#### Scenario: Material issuance to cutting line
- **WHEN** materials are approved for cutting
- **THEN** the system SHALL verify material availability and log the issuance event

### Requirement: Cross-Client Contamination Rejection Guardrail
The system MUST programmatically reject any material dispatch where raw material client ownership does not match the client assigned to the production order.

#### Scenario: Rejection of mismatched client material
- **WHEN** an operator attempts to issue fabric belonging to Client A for an order belonging to Client B
- **THEN** the system MUST abort the dispatch, return an error, and prevent physical inventory decrement
