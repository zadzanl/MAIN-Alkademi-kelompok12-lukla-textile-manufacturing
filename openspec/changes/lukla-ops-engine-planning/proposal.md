# Proposal: Lukla Operations Engine Planning Baseline

## Why
Lukla Manufacturing operates a hybrid garment manufacturing facility (~70 sewing machines) in Ciwidey, West Java, fulfilling internal production for Snøhund alongside multi-client B2B maklon (CMT, Semi-CMT, CMT+Bahan). The facility suffers from multi-tenant inventory cross-contamination risks, complex piece-rate payroll calculations under fluid operator headcounts, and R&D specification drift during sample prototyping iterations. This change formalizes the operational and technical blueprint to build an auditable, multi-tenant operations platform.

## What Changes
This change establishes the formal planning specification suite for the Lukla Operations Engine across 6 core functional capability areas, incorporating 20 observed functional requirements (FR-1.1 through FR-10.4), an 8-role RBAC governance framework, and 4 verified operational acceptance scenarios:
- Multi-tenant tenant data isolation and client/order onboarding with 8-role RBAC governance.
- Immutable audit logging and sample prototyping revision lineage (v1 to v2) into mass orders.
- Multi-client warehouse consignment inventory controls, cutting stage workflows, and database-level cross-contamination rejection guardrails.
- High-frequency 30-minute sewing output tracking, dynamic sewer line capacity allocation, and article piece-rate cards.
- Comprehensive quality control triage (Pass, Repair, Reject), non-duplicate wage repair routing, and 3-way QC bonus pool accrual.
- Automated weekly Saturday piece-rate payroll, variable meal allowances (10–15%), 3-way bonus pool distribution (÷3 across 2 mandor + 1 kepala operasional), and monthly facility overhead allocation.

## Capabilities

### New Capabilities
- `multi-tenant-platform`: Multi-tenant data segregation, client/order onboarding, and 8-role RBAC matrix governance (FR-1.1, FR-1.4, FR-2.1).
- `audit-and-sample-tracking`: Immutable operational audit logging and sample prototype version lineage from v1 to v2 (FR-3.1, FR-4.1).
- `warehouse-and-cutting-controls`: Multi-client consignment inventory receiving, cutting phase controls, and cross-client contamination rejection guardrail (FR-5, FR-6, FR-6.2).
- `production-output-tracking`: Dynamic sewer line capacity allocation without rigid machine slots, article piece-rate cards, 30-minute touch-terminal output logging, and assembly QC queue staging (FR-7.1, FR-7.2, FR-7.3, FR-7.4).
- `quality-control-and-inspection`: Finished garment inspection triage (Pass/Repair/Reject), repair without double piece-rate pay, and 3-way QC bonus pool derivation (FR-8.1, FR-8.2, FR-9.1, FR-9.2).
- `payroll-and-costing-engine`: Weekly Saturday piece-rate payroll calculation, floating meal allowance (10–15%), 3-way bonus pool distribution, and monthly facility overhead unit allocation (FR-10.1, FR-10.2, FR-10.3, FR-10.4).

### Modified Capabilities
*(None; baseline planning change)*

## Impact
- **Architecture:** Establishes event-driven state boundaries and immutable double-entry ledger foundations across manufacturing and payroll domains.
- **Data Models:** Defines tenant, consignment inventory, sewing output, QC inspection, and payroll ledger schemas with Row Level Security (RLS).
- **Stakeholders & Roles:** Enforces strict operational boundaries across 8 roles (Owner, Sample Team, Warehouse, Production Head/Mandor, Tailor/Operator, QC Inspector, Finance/Payroll, Maklon Client).
- **Execution Delivery:** Directly structures sprint deliverables across 4 engineering tracks (Dev 1 Admin/Warehouse UI, Dev 2 Touch Floor UI, Dev 3 Backend/DB/RLS, Dev 4 Payroll/QA/DevOps).
