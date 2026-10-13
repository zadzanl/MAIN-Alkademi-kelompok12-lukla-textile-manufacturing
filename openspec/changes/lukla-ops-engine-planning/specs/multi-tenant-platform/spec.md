# Capability: Multi-Tenant Platform & Access Control

## ADDED Requirements

### Requirement: Multi-Tenant Data Isolation
The system SHALL strictly isolate all data, orders, raw materials, and production records per client tenant, ensuring external clients access only records associated with their authenticated tenant identifier.

#### Scenario: Tenant data boundary enforcement
- **WHEN** an external maklon client queries production status or inventory balances
- **THEN** the system SHALL return only records matching the client's authenticated `client_id` and deny access to other tenants' data

### Requirement: Client and Order Onboarding
The system SHALL support onboarding of distinct client accounts and production orders across CMT, Semi-CMT, and Full-Package commercial schemes.

#### Scenario: New client order creation
- **WHEN** an administrator or sales lead onboards a new client order
- **THEN** the system SHALL record the commercial maklon scheme and initialize tenant-isolated tracking entities

### Requirement: Role-Based Access Control Governance
The system SHALL enforce permissions and operational boundaries across the eight designated system roles: Owner, Sample Team, Warehouse, Production Head, Tailor, QC Inspector, Finance/Payroll, and Maklon Client.

#### Scenario: Unauthorized action prevention
- **WHEN** a user attempts an action outside their permitted role scope
- **THEN** the system MUST block the transaction and log an access restriction event
