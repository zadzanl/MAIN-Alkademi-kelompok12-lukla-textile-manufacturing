# Specification: Operational Query and Lifecycle Endpoints

> [!IMPORTANT]
> **DOWNSTREAM AGENT REFINEMENT & HARDENING MANDATE**  
> The implementing agent SHALL NOT generate backend or frontend code directly from these requirements without first refining, enhancing, sharpening, and hardening the underlying schema invariants, filter boundaries, and test assertions.

## ADDED Requirements

### Requirement: Mandor Sewing Tally Verification Query
The system SHALL provide a query endpoint `GET /sewing-tallies` that allows authorized production supervisors (Mandors) and owners to list recorded sewing tallies filtered by line, operator, order, and verification status.

#### Scenario: Mandor lists unverified tallies for a sewing line
- **WHEN** an authorized `ProductionHead` requests `GET /sewing-tallies?lineId={lineId}&status=RECORDED`
- **THEN** the system returns a paginated list of unverified half-hour tally records containing pieces, operator ID, cut batch ID, and interval timestamps with a cursor for pagination

### Requirement: Cut Batch Discoverability for Sewing Floor Intake
The system SHALL provide a query endpoint `GET /cut-batches` that allows authorized warehouse and sewing production supervisors to discover available cut batches produced from material cutting.

#### Scenario: Sewing operator queries cut batches for order component
- **WHEN** an authorized user requests `GET /cut-batches?orderId={orderId}&componentCode=SLEEVE`
- **THEN** the system returns a paginated list of cut batch records containing produced pieces, consumed material quantities, and cut batch IDs available for tally recording

### Requirement: Explicit Order Confirmation State Transition
The system SHALL provide an atomic action endpoint `POST /orders/{orderId}/confirmation` to transition an order from `DRAFT` to `CONFIRMED`.

#### Scenario: Owner confirms a draft order
- **WHEN** an authorized `Owner` submits `POST /orders/{orderId}/confirmation` with an `Idempotency-Key` header
- **THEN** the order status transitions from `DRAFT` to `CONFIRMED`, locking production commitments and enabling fabric lot issuance

### Requirement: Audited Order Cancellation
The system SHALL provide an atomic action endpoint `POST /orders/{orderId}/cancellation` requiring an audit reason to cancel an order.

#### Scenario: Owner cancels an order with reason
- **WHEN** an authorized `Owner` submits `POST /orders/{orderId}/cancellation` with a cancellation reason and `Idempotency-Key` header
- **THEN** the order status transitions to `CANCELLED`, halting production and recording the cancellation reason in the audit log

### Requirement: Procurement Purchase Order Inspection
The system SHALL provide endpoints `GET /purchase-orders` and `GET /purchase-orders/{purchaseOrderId}` allowing Finance and Owner roles to list and inspect purchase order lines and unit prices before approval.

#### Scenario: Finance reviews purchase order lines before approval
- **WHEN** an authorized `FinancePayroll` user requests `GET /purchase-orders/{purchaseOrderId}`
- **THEN** the system returns the complete purchase order details including supplier name, order linkage, line items, SKU quantities, unit prices, and approval status

### Requirement: Supplier AP Invoice Querying
The system SHALL provide a query endpoint `GET /supplier-invoices` allowing Finance to list recorded accounts payable invoices from suppliers.

#### Scenario: Finance audits invoices recorded against a purchase order
- **WHEN** an authorized `FinancePayroll` user requests `GET /supplier-invoices?purchaseOrderId={purchaseOrderId}`
- **THEN** the system returns a paginated list of recorded supplier invoices matching the purchase order with invoice numbers and totals

### Requirement: Commercial Client Invoice Breakdown Query
The system SHALL provide an endpoint `GET /client-invoices/{invoiceId}` allowing authorized finance staff and Maklon clients to inspect invoice line item breakdowns and totals.

#### Scenario: Client views owned commercial invoice breakdown
- **WHEN** an authenticated `MaklonClient` requests `GET /client-invoices/{invoiceId}` for an invoice issued to their tenant
- **THEN** the system returns the detailed invoice line items, pieces, unit prices, and total amount

### Requirement: Chart of Accounts Discovery
The system SHALL provide an endpoint `GET /ledger/accounts` allowing authorized finance personnel to discover active ledger accounts for journal creation.

#### Scenario: Finance queries chart of accounts for journal entry
- **WHEN** an authorized `FinancePayroll` user requests `GET /ledger/accounts?active=true`
- **THEN** the system returns the list of active ledger accounts including account codes, names, account classes, and currencies

### Requirement: Ledger Transaction Header and Legs Lookup
The system SHALL provide an endpoint `GET /ledger/transactions/{transactionId}` allowing Finance to inspect posted double-entry transaction headers and entry legs.

#### Scenario: Finance inspects posted journal transaction
- **WHEN** an authorized `FinancePayroll` user requests `GET /ledger/transactions/{transactionId}`
- **THEN** the system returns the immutable transaction record with all debit and credit legs and reversal linkage if applicable

### Requirement: Single-Resource Getter Symmetry
The system SHALL provide single-resource retrieval endpoints for `GET /clients/{clientId}`, `GET /samples/{sampleId}`, `GET /assemblies/{assemblyId}`, and `GET /time-studies`.

#### Scenario: Barcode scanner fetches assembly by ID
- **WHEN** an authorized `QCInspector` requests `GET /assemblies/{assemblyId}`
- **THEN** the system returns the garment assembly details, serial code, status, and immutable component-to-operator attributions

### Requirement: QC Barcode Scanner Assembly Query
The system SHALL support filtering `GET /assemblies` by `serialCode` to enable instantaneous barcode and QR code lookup without full-table scans.

#### Scenario: QC terminal scans physical garment barcode
- **WHEN** an authorized `QCInspector` requests `GET /assemblies?serialCode=LUKLA-ASM-00123`
- **THEN** the system returns the matching assembly record directly for inspection disposition
