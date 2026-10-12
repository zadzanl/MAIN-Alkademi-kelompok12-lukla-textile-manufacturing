# Lukla Operations Engine: Technical & Product Blueprint

## 1. Business Requirements Document (BRD)

### 1.1 Executive Summary & Business Context

Lukla Manufacturing operates an apparel production facility in Ciwidey, West Java, managing a dynamic floor capacity of up to approximately 70 active sewing machines. The business operates a hybrid manufacturing model: it concurrently fulfills internal manufacturing for its proprietary brand, Snøhund, alongside contract manufacturing (maklon) for external business-to-business (B2B) fashion brands.

Production agreements are structured into three distinct commercial maklon schemes that determine raw material ownership and procurement obligations:

* **CMT (Cut, Make, Trim):** The B2B client supplies 100% of the raw materials, fabrics, and trims. Lukla provides only pattern cutting, sewing assembly, and finishing services(.)

(*) **Semi-CMT:** The B2B client supplies the primary shell fabric, while Lukla sources secondary components, linings, thread, and hardware accessories(.)

(*) **CMT + Bahan (Full Package):** Lukla procures all fabrics and trims while executing end-to-end cutting, manufacturing, and finishing. This scheme is also standard for internal Snøhund production.


### 1.2 Core Business Problems & Impact

The facility encounters three operational bottlenecks that threaten profitability and client trust:

* **Cross-Contamination of Multi-Tenant Inventory:** Raw materials, work-in-progress (WIP), and finished garments from multiple external clients are stored and processed concurrently without programmatic boundary enforcement. Warehouse operators risk issuing fabric owned by Client A to produce an order for Client B, resulting in inventory shortages, contractual disputes, and unrecoverable material write-offs(.)

(*) **Complex, Piece-Rate Payroll Under Fluid Headcount:** The factory floor does not operate on fixed monthly wages; capacity fluctuates between 1 and 70+ operators depending on active batch sizes. The facility requires an automated, auditable system to record piece-rate output at 30-minute intervals, disburse weekly Saturday payroll, apply floating meal allowances (10–15%), divide shared quality control (QC) bonuses across leadership, and allocate monthly factory overhead across finished units(.)

(*) **Loss of Revision Lineage & R&D Drift:** Physical garment prototyping currently lacks centralized digital tracking. Critical technical parameters—fabric yields, component-level time studies, operator rate cards, and defect logs—are scattered across paper logs, resulting in unversioned discrepancies when transitioning from approved sample prototypes to mass factory runs.


### 1.3 Strategic Business Objectives

* **Absolute Multi-Tenant Inventory Segregation:** Programmatically eliminate physical stock mix-ups by establishing mandatory owner-tagging across all raw materials, WIP bundles, and finished SKUs(.)

(*) **Immutable Operational Traceability:** Track piece-level output in 30-minute intervals across sewing lines to ensure that production tracking, inventory debits, and payroll disbursements derive from verified operational metrics(.)

(*) **Transparent Multi-Tier Commercial Settlement:** Support automated invoice and weekly payroll generation across CMT, Semi-CMT, and Full-Package agreements without manual spreadsheet reconciliation.


### 1.4 Stakeholder & Governance Matrix (RBAC)

System operations are governed across eight strict operational roles:

| Role | Operational Scope & Permissions | System Enforced Boundaries & Constraints |
| --- | --- | --- |
| **Owner / Internal Executive** | High-level business intelligence analytics, system configurations, and dynamic rate-card overrides. | Barred from altering locked or reconciled historical financial/inventory ledger records. |
| **Sample Team / Adis Sample** | Logs sample consumption, records component-level time studies, approves sample version iterations. | Cannot convert or approve mass production orders without executive sign-off. |
| **Warehouse / Stock Manager** | Ingests multi-client raw materials, processes consignment stock, issues bundles to cutting, runs stock opname. | Programmatically blocked from issuing materials if Client ID or Order ID fails validation. |
| **Production Head / Line Foreperson** | Allocates operators to parallel lines, configures component rate cards, logs 30-minute station outputs. | Prohibited from modifying payroll calculation formulas or altering final QC disposition states. |
| **Tailor / Operator** | Views assigned component assembly queues, inputs completed piece tallies. | Read-only access to completed records once verified and locked by the foreperson. |
| **QC Inspector** | Inspects assembled garments, logs specific defect taxonomies, categorizes units into Pass, Repair, or Reject. | Barred from modifying order commercial terms or piece-rate wage configurations. |
| **Finance & Payroll Officer** | Approves vendor POs, issues client commercial invoices, calculates weekly piece-rate wages and monthly overhead allocations. | Strictly prohibited from manually adjusting physical inventory stock balances. |
| **Maklon Client (External Portal)** | Monitors order progress, tracks manufacturing milestones, inspects real-time balances of consigned raw materials. | Data isolated by multi-tenant security rules; can only view records matching their explicit `client_id`. |

---

## 2. Architectural Deconstruction & Domain Modeling

### 2.1 Domain Decomposition (Bounded Contexts)

The Lukla Operations Engine operates as an event-driven system anchored by an immutable core state engine.

```
+-----------------------------------------------------------------------------------+
|                           IMMUTABLE DOUBLE-ENTRY CORE                             |
|    +-----------------------------+             +-----------------------------+    |
|    |    Financial Ledger         |             |   Multi-Tenant Inventory    |    |
|    |   (COA, Debits, Credits)    |             |    (Consignment vs Owned)   |    |
|    +-----------------------------+             +-----------------------------+    |
+-----------------------------------------------------------------------------------+
                                          ▲
                                          │ Events / Strict Constraints
                                          ▼
+-----------------------+     +-----------------------+     +-----------------------+
|  Sampling & Spec R&D  |     | Manufacturing Execution|     | Quality Control & MES |
| (Time Study, Versions)|     | (Line, Foreperson UI) |     | (Pass, Repair, Reject)|
+-----------------------+     +-----------------------+     +-----------------------+
                                          │
                                          ▼ Verified Completions
                              +-----------------------+
                              | Dynamic Payroll Engine|
                              | (Piece-Rate, QC Pool) |
                              +-----------------------+

```

### 2.2 Reconciling Manufacturing Operations with the Double-Entry Ledger

The core engine treats every material receipt, stock movement, assembly transition, and wage obligation as an atomic, double-entry financial transaction. This model prevents state drift between physical inventory counts and financial accounts.

#### 1. Consigned Inventory (CMT Scheme)

Fabrics provided directly by a client are not assets of Lukla Manufacturing; they represent custodial obligations.

* **Material Receipt:**
* Debit: `Inventory:Custodial:RawMaterial [Client_ID]`
* Credit: `Liability:CustodialObligation [Client_ID](`)

(*) **Issuance to Cutting (WIP):**
* Debit: `Inventory:Custodial:WIP [Client_ID, Order_ID]`
* Credit: `Inventory:Custodial:RawMaterial [Client_ID]`


#### 2. Owned Inventory (Full Package / Snøhund Scheme)

Materials procured directly by Lukla represent company assets and operational liabilities.

* **Vendor Receipt:**
* Debit: `Inventory:Asset:RawMaterials`
* Credit: `Accounts Payable:Vendor(`)

(*) **Issuance to Floor:**
* Debit: `Inventory:Asset:WIP [Order_ID]`
* Credit: `Inventory:Asset:RawMaterials`


#### 3. Labor & Piece-Rate Transformation

As garments progress through 30-minute intervals and final verification, labor costs are capitalized directly into inventory value:

* **Assembly Verification:**
* Debit: `Inventory:WIP:DirectLaborApplied [Order_ID]`
* Credit: `Payroll:AccruedWagesPayable [Operator_ID]`


### 2.3 Multi-Tenant Inventory Isolation & Anti-Cross Contamination

To enforce requirement FR-6.2, physical items cannot exist as generic SKUs. The inventory schema binds every stock lot to an immutable composite identifier:

$$\text{Stock Unit Identity} = \langle \text{SKU}, \text{Owner ID}, \text{Assigned Order ID}, \text{Consignment Flag} \rangle$$

```
                           [ Warehouse Stock Opname ]
                                       │
                        Request Dispatch for Order_B
                                       │
                                       ▼
                   ┌───────────────────────────────────────┐
                   │    Is Material Owner == Order_B.Owner?│
                   └───────────────────────────────────────┘
                                  │         │
                            YES   │         │  NO
                                  │         ▼
                                  │    [ SYSTEM HALT / ABORT ]
                                  │    - Reject Transaction
                                  │    - Throw Anti-Contamination Error
                                  │    - Log Security Audit Breach
                                  ▼
                    [ Allow Movement to Cutting Floor ]
                    - Generate Balanced Journal Entry
                    - Update Consignment / WIP Balance

```

The database engine enforces this constraint at the transaction level:

```sql
CREATE OR REPLACE FUNCTION validate_material_dispatch()
RETURNS TRIGGER AS $$
DECLARE
    target_order_client_id UUID;
    source_stock_client_id UUID;
BEGIN
    SELECT client_id INTO target_order_client_id 
    FROM mass_production_orders 
    WHERE id = NEW.destination_order_id;

    SELECT client_id INTO source_stock_client_id 
    FROM warehouse_inventory_lots 
    WHERE id = NEW.source_lot_id;

    IF target_order_client_id <> source_stock_client_id THEN
        RAISE EXCEPTION 'CRITICAL VIOLATION (FR-6.2): Attempted to issue stock belonging to Client % to Order % belonging to Client %',
            source_stock_client_id, NEW.destination_order_id, target_order_client_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

```

### 2.4 State Machine Deconstruction: Sample Phase to Mass Production

Garment manufacturing flows through sequential, state-dependent stages:

```
[ Sample Phase v1 ] ──────── (Client Revision) ───────► [ Sample Phase v2 ]
(Time Study, Bill of Mat.)                                  │
                                                            │ (Client Sign-Off)
                                                            ▼
                                                [ Approved Master Spec ]
                                                            │
                            ┌───────────────────────────────┴───────────────────────────────┐
                            ▼                                                               ▼
                 [ CMT Order Created ]                                           [ Semi-CMT / Full Package ]
          - Client fabric delivery wait                                            - Automated POs raised
                            │                                                               │
                            └───────────────────────────────┬───────────────────────────────┘
                                                            ▼
                                              [ Fabric Intake & Verification ]
                                              (Mandatory Client Tagging FR-6.1)
                                                            │
                                                            ▼
                                              [ Cutting & Component Bundling ]
                                              (Scrap & Efficiency Logged FR-6.3)
                                                            │
                                                            ▼
                                              [ Parallel Production Floor ]
                                              (30-Min Output Intervals FR-7.3)
                                                            │
                                                            ▼
                                                [ Quality Control (QC) ]
                                                            ├──► Pass (Triggers QC Bonus Pool FR-10.3)
                                                            ├──► Repair (Route back to Floor)
                                                            └──► Reject / Scrap
                                                            │
                                                            ▼
                                               [ Packaging & Client Invoice ]
                                                            │
                                                            ▼
                                                [ Saturday Payroll Engine ]
                                                (Borongan + Uang Makan Split)

```

---

## 3. Feature Mapping & Capability Matrix

### 3.1 Traceability Matrix

This matrix maps the 6 operational phases of the facility to functional requirements, user access roles, and platform views.

| Phase | Requirement ID | Requirement Scope | Authorized Roles | Target UI View | Core System Deliverable |
| --- | --- | --- | --- | --- | --- |
| **01. Sample Phase**<br> | FR-1 to FR-4 | Prototype tracking, versioning (v1, v2), digital time study stopwatch per component, consumption logs. | Sample Team, Owner | View 02: Sample & Time Study Tracker | Immutable Master Spec & Component Target Matrix. |
| **02. Approval & Order**<br> | FR-4.1 | Commercial contract classification (CMT, Semi-CMT, Full Package), conversion of sample spec to mass work orders. | Owner, Finance, Client Portal | View 01: Executive Operations Dashboard | Production Work Order & Custodial Asset Ledger Accounts. |
| **03. Warehouse & Cutting**<br> | FR-5, FR-6.1, FR-6.2, FR-6.3 | Mandatory client-tag intake, cross-contamination dispatch block, fabric waste/scrap tracking. | Warehouse Team, Production Head | View 03: Multi-Client Warehouse Grid | Tagged Cut Bundle Receipts & Material Efficiency Ledger. |
| **04. Production Line**<br> | FR-7.1, FR-7.2, FR-7.3, FR-7.4 | Fluid floor layout ($\pm70$ machines), article rate cards, touch terminal 30-min output collection, bundle assembly. | Foreperson, Tailor Operator | View 04: 30-Minute Floor Terminal | Verified Component Output Feed & Accrued Piece Wages. |
| **05. QC & Finished Goods**<br> | FR-8, FR-9 | Final inspections, classification (Pass, Repair, Reject), defect taxonomy tagging, bonus pool accruals. | QC Inspector, Foreperson | View 05: QC Inspection Terminal | Disposition Certificates & Locked QC Output Units. |
| **06. Payroll & Financials**<br> | FR-10.1, FR-10.2, FR-10.3, FR-10.4 | Saturday piece-rate payout, 10–15% floating meal allowance, 3-way QC bonus split, monthly overhead division. | Finance & Payroll, Owner | View 06: Payroll & Cost Workspace | Weekly Disbursements, COGS Reconciliations, Invoices. |

---

## 4. Product Requirements Document (PRD)

### 4.1 System Computation Specifications & Formulations

#### 1. Weekly Tailor Piece-Rate Wage ($\text{Borongan}$)


Calculated every Saturday without hard limits on operator count ($N \le 70+$):

$$\text{Wage}_i = \sum_{c=1}^{C} \left( Q_{i, c, \text{verified}} \times R_{c} \right)$$

Where $Q_{i, c, \text{verified}}$ is the sum of verified 30-minute interval outputs for tailor $i$ on component $c$, and $R_c$ is the component rate defined in the client-article rate card.

#### 2. Floating Meal Allowance Pool ($\text{Uang Makan}$)


A percentage $\mu \in [10\%, 15\%]$ configured manually by finance per production cycle:

$$\text{Pool}_{\text{meal}} = \mu \times \sum_{i=1}^{N} \text{Wage}_i$$

#### 3. Three-Way Quality Control Bonus Pool ($\text{Bonus QC}$)


Triggered by all garments passing final QC inspection across all active orders and clients:

$$\text{Pool}_{\text{QC}} = U_{\text{passed, total}} \times R_{\text{bonus\_per\_pc}}$$

The disbursement is distributed equally across leadership roles:

$$\text{Bonus}_{\text{Foreperson 1}} = \text{Bonus}_{\text{Foreperson 2}} = \text{Bonus}_{\text{Head Ops}} = \frac{\text{Pool}_{\text{QC}}}{3}$$

#### 4. Unit Factory Overhead Allocation ($\text{Overhead per Unit}$)


Calculated monthly by aggregating fixed and variable operational costs (power, water, internet, facility rent) divided by actual production volume:

$$\text{Overhead}_{\text{unit}} = \frac{\sum \text{Cost}_{\text{facility, monthly}}}{U_{\text{produced, total month}}}$$

### 4.2 Minimum Required UI View Specifications

The system requires six dedicated user interfaces:

```
+-----------------------------------------------------------------------------------+
| VIEW 01: Executive Operations Dashboard                                           |
| [Line Status: 62/70 Active] [Active Clients: Snøhund, Brand-X] [Run-Rate: 94%]    |
| +-----------------------------------------------+ +-------------------------------+|
| | 30-Min Interval Factory Speed Output Graph    | | Client Order Progress Grid    ||
| +-----------------------------------------------+ +-------------------------------+|
+-----------------------------------------------------------------------------------+
| VIEW 02: Sample & Time Study Tracker                                              |
| Spec: Arctic Parka | Active Version: [v2 (Locked)] | History: [v1 Archive]        |
| [Stopwatch Component: Collar Stitch | Elapsed: 00:04:12.4] -> [Save to Time Study] |
+-----------------------------------------------------------------------------------+
| VIEW 03: Multi-Client Warehouse Inventory Grid                                    |
| [Filter by Client: All] [Search Lot Tag: LOT-2026-99] [Alerts: 0 Collisions]      |
| Item: Poly-Oxford | Owner: Snøhund | Allocated: ORD-401 | Bal: 420m | [Dispatch]  |
| *CRITICAL*: Selecting dispatch to non-matching Order throws blocking modal        |
+-----------------------------------------------------------------------------------+
| VIEW 04: Floor Terminal (30-Minute Interval Touch Interface)                      |
| Line: Line 03 | Mandor: Budi | Interval: [13:30 - 14:00]                         |
| +-------------------------+ +-------------------------+ +-------------------------+|
| | Tailor #14: Rudi S.     | | Tailor #22: Asep M.     | | Tailor #31: Dede K.     ||
| | Sleeve Assembly         | | Front Zipper Attachment | | Collar Topstitch        ||
| | [-]  [  14 pcs  ]  [+]  | | [-]  [   8 pcs  ]  [+]  | | [-]  [  12 pcs  ]  [+]  ||
| +-------------------------+ +-------------------------+ +-------------------------+|
|                                                           [ SUBMIT INTERVAL BLOCK ]|
+-----------------------------------------------------------------------------------+
| VIEW 05: QC Inspection Terminal                                                   |
| Order: ORD-401 (Snøhund) | Garment Unit Serial: SN-401-0891                       |
| Status Actions:   [ (A) PASS ]      [ (B) REPAIR ]       [ (C) SCRAP / REJECT ]   |
| Defect Taxonomy:  [ ] Broken Stitch  [ ] Puckering       [ ] Uneven Seam          |
+-----------------------------------------------------------------------------------+
| VIEW 06: Payroll & Costing Workspace                                              |
| Cycle: Week 41 (Ending Saturday) | Tailors Processed: 68                          |
| Base Borongan: Rp 42.150.000 | Uang Makan (12.5%): Rp 5.268.750                   |
| Passed QC Units: 2.800 pcs   | QC Bonus Pool: Rp 2.800.000 (Split 3 ways: Rp 933k)|
| Monthly Factory Overhead Allocation per Unit: Rp 4.120 / pcs                      |
|                                                      [ EXECUTE PAYROLL RUN (SAT) ] |
+-----------------------------------------------------------------------------------+

```

### 4.3 Acceptance Test Scenarios

Implementation success is evaluated against four end-to-end integration scenarios:

#### Scenario 01: Multi-Tenant Stock Cross-Contamination Prevention

* **Action:** A warehouse worker attempts to dispatch 50 meters of waterproof Taslan fabric tagged with `client_id: Client_A` to satisfy a cutting bundle request for `order_id: ORD-Client_B`(.)

(*) **System Expected Behavior:** The system aborts the database transaction before persistence, logs an access warning, and displays an error indicating an ownership mismatch.


#### Scenario 02: Dynamic Headcount Mid-Week Addition

* **Action:** On Thursday, five new contract tailors are registered on the factory floor without restarting operational cycles. The foreperson records their completed units through the 30-minute terminal on Thursday and Friday. The Saturday payroll run is initiated(.)

(*) **System Expected Behavior:** The system incorporates the 5 new tailors into the batch without schema locks, calculates their piece-rate earnings based on verified output logs, and incorporates their base pay into the 10–15% meal allowance pool calculation.


#### Scenario 03: QC Bonus Pool 3-Way Split

* **Action:** The system aggregates production runs across three clients (e.g., Snøhund, Client X, Client Y) yielding 3,000 units marked as `PASS` by the QC terminal(.)

(*) **System Expected Behavior:** The platform calculates the consolidated bonus pool ($3{,}000 \times R_{\text{bonus}}$) and splits it into three equal disbursements (Foreperson 1, Foreperson 2, and Operations Head). Calculations must handle integer division rounding down to the nearest integer currency unit, allocating remainders to the operational reserve.


#### Scenario 04: Sample Revision to Mass Order Transition

* **Action:** The design team creates prototype "Windbreaker Jacket v1", records time studies, modifies seam parameters to generate "v2", locks "v2", and converts it into a commercial order under the Semi-CMT scheme(.)

(*) **System Expected Behavior:** The system establishes an order record inheriting v2 specifications and target rates. The system generates custodial inventory records for the client-supplied shell fabric, while scheduling internal purchase orders for internal trims and accessories.


---

## 5. Execution Sprints

```
SPRINT 1                  SPRINT 2                  SPRINT 3                  SPRINT 4                  SPRINT 5
Oct 13 - Oct 26           Oct 27 - Nov 09           Nov 10 - Nov 23           Nov 24 - Dec 07           Dec 08 - Dec 21
+-------------------+     +-------------------+     +-------------------+     +-------------------+     +-------------------+
| Double-Entry Core |     | Multi-Tenant      |     | Manufacturing     |     | Dynamic Payroll   |     | Full UI & End-    |
| & RBAC Engine     |────►| Inventory Engine  |────►| Execution (MES)   |────►| & QC Bonus Engine |────►| to-End Validation |
|                   |     |                   |     |                   |     |                   |     |                   |
| - PG Ledger Schema|     | - Client Tagging  |     | - Line Allocation |     | - Saturday Borong.|     | - 6 UI Views      |
| - 8 RBAC Roles    |     | - Cross-Contam.   |     | - 30-min Terminal |     | - 10-15% Food Pool|     | - 4 Test Scenarios|
| - Base Journal API|     | - Waste Tracking  |     | - Time Study Spec |     | - 3-Way QC Split  |     | - Portfolio Polish|
+-------------------+     +-------------------+     +-------------------+     +-------------------+     +-------------------+

```

### Sprint 1: Double-Entry Accounting Core & Strict RBAC

* **Target Objective:** Establish the financial source of truth and user authorization hierarchy.
* **Deliverables:**
* Core PostgreSQL schema: `chart_of_accounts`, `journal_entries`, `journal_lines`, and `app_users`.
* Database transaction triggers enforcing $\sum \text{Debits} \equiv \sum \text{Credits}$.
* RBAC middleware enforcing operational boundaries across the 8 defined user personas(.)

(*) REST/gRPC endpoints to ingest, balance, and lock immutable transactions.


* **Definition of Done (DoD):** System passes unit testing for concurrent ledger writes and rejects invalid balances and unauthorized role mutations.


### Sprint 2: Multi-Tenant Inventory Control & Material Tracking

* **Target Objective:** Build the multi-client inventory domain with programmatic isolation rules.
* **Deliverables:**
* Database structures for `inventory_lots`, `material_movements`, and `scrap_records`(.)

(*) Implementation of FR-6.1 mandatory client and order tagging logic on material intake(.)

(*) PostgreSQL pre-transaction constraint triggers to intercept and abort cross-client stock issuances (FR-6.2)(.)

(*) Raw material waste logging tracking fabric utilization efficiency (FR-6.3).


* **Definition of Done (DoD):** Test Scenario 01 passes; attempting to cross-issue fabric across clients throws a database-level abort.


### Sprint 3: Sample Lifecycle, Orders, & Shop Floor Execution (MES)

* **Target Objective:** Model garment prototyping workflows and real-time floor assembly tracking.
* **Deliverables:**
* Sample versioning engine (`sample_specs`, `time_studies`) supporting v1 to v2 transitions and component timing(.)

(*) Commercial contract workflow handling CMT, Semi-CMT, and Full-Package agreements(.)

(*) Floor management module supporting flexible line assignments for up to 70 sewing stations (FR-7.1)(.)

(*) High-frequency 30-minute interval logging endpoint (FR-7.3).


* **Definition of Done (DoD):** Test Scenario 04 passes; Sample v2 converts into a production order carrying inherited rate profiles and time studies.


### Sprint 4: Dynamic Piece-Rate Payroll & Quality Control Engine

* **Target Objective:** Automate piece-rate production calculations, QC classification, and shared bonus allocations.
* **Deliverables:**
* QC disposition logging API classifying output into Pass, Repair, or Reject (FR-8, FR-9)(.)

(*) Weekly Saturday payroll engine calculating component piece-rate wages ($Q \times R$) across fluid workforces (FR-10.1)(.)

(*) Configurable 10–15% floating meal allowance calculation module (FR-10.2)(.)

(*) Three-way QC bonus pooling engine dividing qualified passed piece shares across operational heads (FR-10.3)(.)

(*) Monthly operational overhead allocation calculator dividing facility utility overhead across finished units (FR-10.4).


* **Definition of Done (DoD):** Test Scenarios 02 and 03 pass with correct calculations verified against manual accounting runs.


### Sprint 5: UI Interfaces & System Integration

* **Target Objective:** Deliver the front-end user experience and execute automated end-to-end operational audits.
* **Deliverables:**
* Implementation of the six target user interfaces in React/TypeScript(:)

(*) View 01: Operations Dashboar(d)

(*) View 02: Sample & Time Study Tracke(r)

(*) View 03: Multi-Client Warehouse Gri(d)

(*) View 04: 30-Minute Touch-Friendly Floor Termina(l)

(*) View 05: QC Inspection Termina(l)

(*) View 06: Payroll & Costing Workspace


* Integration testing validating UI operations against back-end double-entry assertions and RBAC permissions.


* **Definition of Done (DoD):** Complete automated and user-acceptance test runs succeed across all four primary acceptance test scenarios. Clean technical and domain architecture documentation published for the system portfolio.