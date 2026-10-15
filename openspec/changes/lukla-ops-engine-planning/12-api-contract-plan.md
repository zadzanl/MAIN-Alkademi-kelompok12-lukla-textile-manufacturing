# Phase A3 — API Contract Plan

**Task record:** revision 14. **Contract:** `contracts/openapi.yaml`. **Status:** proposed, contract-first; no server has been implemented and the Phase A review gate remains open.

## 1. Protocol baseline

The portable baseline is HTTPS JSON with an OAuth2/OIDC-compatible bearer access token at `Authorization: Bearer <token>`, short-lived access tokens, and an opaque rotating refresh token at `/auth/refresh`. The issuer, audience, signing-key rotation, password/floor-device enrollment, and final identity provider remain Phase B decisions. The proposed endpoint shapes become the baseline only after Phase A review: login returns `accessToken`, `expiresIn`, `refreshToken`, and actor context; refresh rotates the refresh token; logout revokes the presented refresh token. No API accepts a tenant header as authority.

Every request gets `X-Request-Id`; every retryable write gets `Idempotency-Key`. The server authenticates first, resolves the actor's memberships/grants, rechecks authorization in the database transaction, installs `SET LOCAL` context, and only then reads or writes. Internal jobs use `X-Service-Principal` plus a service credential and an allowed service scope; a caller's employee role is never accepted as job authority.

## 2. Stable error and paging contract

Errors use `Problem {type,title,status,code,detail,instance,requestId,violations[]}`. Stable codes include `AUTH_REQUIRED`, `FORBIDDEN`, `TENANT_CONTEXT_MISSING`, `LEGAL_OWNER_MISMATCH`, `ORDER_BENEFICIARY_MISMATCH`, `IDEMPOTENCY_CONFLICT`, `INVALID_STATE`, `LEDGER_IMMUTABLE`, `DUPLICATE_REPAIR_CREDIT`, `FINANCIAL_RULE_PENDING`, `VALIDATION_ERROR`, `INSUFFICIENT_STOCK`, `OVER_CONSUMPTION`, and `SERVICE_SCOPE_REQUIRED`. List responses use `{items,nextCursor}` and opaque cursor tokens; no offset is required for correctness.

Idempotency is scoped by `(authenticated tenant, operationId, key)`, never by key alone. The server stores a canonical JSON hash after removing transport-only headers and normalizing property order. Same hash returns the original status/body. A different hash returns `409 IDEMPOTENCY_CONFLICT`. An in-progress retry waits briefly or returns the same conflict state; a crashed request is safely retried under the unique row and transaction lock. The canonical payload includes ownership and beneficiary fields, so a replay cannot change legal meaning.

## 3. Endpoint catalog and ownership rules

The OpenAPI document is the machine-readable source. Each operation has source IDs, roles, view, and invariant metadata. Unresolved IDs are cataloged as `status-only` and do not receive invented business behavior.

| Area | Operations | Primary source IDs / roles |
|---|---|---|
| Auth/session | `login`, `refreshSession`, `logout`, `getMyContext` | FR-2.1; all roles |
| Provisioning/clients/orders | `provisionAccount`, `listClients`, `createClient`, `getClient`, `createOrder`, `getOrder`, `listOrders`, `confirmOrder`, `cancelOrder` | FR-1.1, FR-1.4 (status-only), FR-2.1, FR-4.3; scoped roles per operation |
| Ledger/audit | `appendLedgerTransaction`, `reverseLedgerTransaction`, `getLedgerEntries`, `listLedgerAccounts`, `getLedgerTransaction`, `listAuditEvents` | FR-3.1; Owner, Finance |
| Samples/time study/rates | `createSample`, `getSample`, `listSamples`, `createSampleRevision`, `listSampleRevisions`, `lockSample`, `approveSample`, `convertSampleToOrder`, `recordTimeStudy`, `listTimeStudies`, `upsertRateCard`, `listRateCards` | FR-4.1..FR-4.3; scoped roles per operation |
| Warehouse/cutting | `receiveMaterial`, `issueMaterial`, `getStock`, `createStocktake`, `createStockAdjustment`, `recordCuttingResult`, `listCutBatches` | FR-5, FR-5.1..FR-5.2, FR-6, FR-6.1..FR-6.3, FR-7.3; Warehouse, Owner, ProductionHead |
| Sewing/assembly | `listLines`, `createLine`, `listOperators`, `createOperator`, `listAssignments`, `assignOperator`, `recordSewingTally`, `listSewingTallies`, `verifySewingTally`, `listAssemblies`, `createAssembly`, `getAssembly`, `listProductionProgress` | FR-7.1..FR-7.4, FR-8.1; scoped roles per operation |
| QC/payroll | `inspectUnit`, `getBonusPool`, `createPayrollPeriod`, `listPayrollPeriods`, `calculateWeeklyPayroll`, `getPayrollStatement`, `approvePayroll`, `recordPayrollPayment`, `recordOverhead`, `calculateOverhead` | FR-8.1..FR-8.2, FR-9.1..FR-9.2, FR-10.1..FR-10.4; scoped roles per operation |
| Financial governance | `listFinancialRules`, `proposeFinancialRule`, `approveFinancialRule` | Inferred approval workflow supporting FR-10.1..FR-10.4; permissions and business values pending authorized approval |
| Client billing | `listClientInvoices`, `createClientInvoice`, `getClientInvoice`, `issueClientInvoice` | Proposed commercial workflow; FR-3.1; Finance, Owner, MaklonClient |
| Procurement | `listPurchaseOrders`, `createPurchaseOrder`, `getPurchaseOrder`, `approvePurchaseOrder`, `listSupplierInvoices`, `recordSupplierInvoice` | BRD/PRD in-scope manual PO/invoice; FR-3.1; Finance, Owner |
| Files/portal/dashboard | `createFileUpload`, `completeFileUpload`, `getFileDownload`, `getDashboard`, `getPortalOrderStatus` | FR-1.1, FR-3.1, six PRD views; scoped role |
| Jobs/search | `runSaturdayPayrollJob`, `runMonthlyOverheadJob`, `getJob`, `searchOperationalDocuments` | FR-10.1, FR-10.4; service scope or authorized read role; search is a fenced extension |

This catalog enumerates 83 operation IDs, not 83 independently proven requirements. The YAML specifies each operation's roles and required headers. Source-ID presence is only an inventory check; requirement semantics, error completeness, and six-view usability still need independent review.

### 3.1 Reconciled operational query and lifecycle endpoint catalog

The 14 operational query and lifecycle endpoints bridge critical visibility and lifecycle gaps identified in `reconcile-openapi-endpoint-gaps`:

| Operation ID | Method & Path | Summary | Tags | x-roles | x-source-ids | Key Request/Response Schemas |
|---|---|---|---|---|---|---|
| `getClient` | `GET /clients/{clientId}` | Get client profile detail | `clients-orders` | `Owner`, `FinancePayroll`, `SampleTeam` | `FR-1.1` | Resp: `Client` |
| `confirmOrder` | `POST /orders/{orderId}/confirmation` | Confirm a draft order to lock production commitments | `clients-orders` | `Owner`, `ProductionHead` | `FR-1.1`, `FR-4.3` | Req: `OrderConfirmationRequest`, Resp: `Order` |
| `cancelOrder` | `POST /orders/{orderId}/cancellation` | Cancel an order with required audit justification | `clients-orders` | `Owner` | `FR-1.1` | Req: `OrderCancellationRequest`, Resp: `Order` |
| `listLedgerAccounts` | `GET /ledger/accounts` | List chart of accounts for double-entry journals | `ledger-audit` | `FinancePayroll`, `Owner` | `FR-3.1` | Query: `active`, Resp: `LedgerAccountPage` |
| `getLedgerTransaction` | `GET /ledger/transactions/{transactionId}` | Get posted ledger transaction header and legs | `ledger-audit` | `FinancePayroll`, `Owner` | `FR-3.1` | Resp: `LedgerTransaction` |
| `getSample` | `GET /samples/{sampleId}` | Get sample detail and current active revision metadata | `samples-rates` | `SampleTeam`, `Owner`, `ProductionHead` | `FR-4.1`, `FR-4.2` | Resp: `Sample` |
| `listTimeStudies` | `GET /time-studies` | List stopwatch time study observations for sample revisions | `samples-rates` | `SampleTeam`, `Owner`, `ProductionHead` | `FR-4.2` | Query: `sampleRevisionId`, `componentCode`, Resp: `TimeStudyPage` |
| `listCutBatches` | `GET /cut-batches` | List cut batches available for sewing line intake | `warehouse-cutting`, `sewing` | `Warehouse`, `ProductionHead`, `Owner` | `FR-6`, `FR-6.3`, `FR-7.3` | Query: `orderId`, `componentCode`, Resp: `CutBatchPage` |
| `listSewingTallies` | `GET /sewing-tallies` | List recorded 30-minute sewing tallies for Mandor verification | `sewing` | `ProductionHead`, `Owner` | `FR-7.3`, `FR-7.4` | Query: `lineId`, `operatorId`, `orderId`, `status`, Resp: `SewingTallyPage` |
| `listPurchaseOrders` | `GET /purchase-orders` | List purchase orders with status filter | `procurement` | `FinancePayroll`, `Owner` | `FR-3.1` | Query: `status`, Resp: `PurchaseOrderPage` |
| `getPurchaseOrder` | `GET /purchase-orders/{purchaseOrderId}` | Get purchase order detail including lines and approval state | `procurement` | `FinancePayroll`, `Owner` | `FR-3.1` | Resp: `PurchaseOrder` |
| `listSupplierInvoices` | `GET /supplier-invoices` | List recorded supplier AP invoices | `procurement` | `FinancePayroll`, `Owner` | `FR-3.1` | Query: `purchaseOrderId`, Resp: `SupplierInvoicePage` |
| `getAssembly` | `GET /assemblies/{assemblyId}` | Get garment assembly detail, attached components, and inspection state | `sewing`, `quality-payroll` | `QCInspector`, `ProductionHead`, `Owner` | `FR-7.4`, `FR-8.1` | Resp: `Assembly` |
| `getClientInvoice` | `GET /client-invoices/{invoiceId}` | Get detailed commercial invoice breakdown | `workflow` | `FinancePayroll`, `Owner`, `MaklonClient` | `FR-3.1` | Resp: `ClientInvoice` |

`FR-5` and `FR-6` are group-level status markers only. Their child endpoints are mapped to the specific child IDs. `FR-1.4` has only an onboarding/order contract shape and remains `DEFINITION_PENDING`; it does not assert missing source text.

## 4. State and financial rules

Order flow is `DRAFT -> CONFIRMED -> IN_PRODUCTION -> QC -> COMPLETED|CANCELLED`. Sample revisions are append-only; only a locked approved revision may seed a mass order. Material is received before issue; issue is atomically validated against stock lot legal owner and order beneficiary. A sewing tally identifies a cut batch, line, operator, component and integer piece count. Components are linked into a finished assembly before assembly-level QC. Repair preserves component-to-original-operator attribution. Eligible component contributions receive at most one wage credit each at their immutable rate snapshots; a finished assembly receives at most one bonus accrual. Multiple contributors do not multiply the assembly bonus.

Money is `{amountMinor: integer, currency: string}`. Material quantities are `{value: decimal-string, unit: enum}` to preserve precision across JSON implementations; sewing output uses integer `pieces`. Material conservation compares compatible material units, never meters plus garment counts. Times are RFC 3339 with explicit offset; business periods include IANA timezone and cutoff. No financial calculation uses floating point.

The three-way QC pool is one rule shared by `FR-9.2` and `FR-10.3`, not two bonuses. Recipient mapping, meal basis (10–15%), rounding/remainder destination, payroll eligibility, and overhead denominator are `PENDING` until authorized. APIs return `FINANCIAL_RULE_PENDING` rather than silently using a demo default. Zero-output periods return a non-error `NO_OUTPUT` calculation state and do not divide by zero.

Financial-rule enums describe supported proposals, not arbitrary policy plug-ins. An authorized alternative outside those enums requires a reviewed contract/calculation change before production, not a free-form value. The fixed three-way baseline remains unless an explicit business amendment changes it. Rule approval still requires external authorization evidence; planning approval is not business authorization.

## 5. Compatibility and change control

`/api/v1` operation IDs, error codes, ownership dimensions, and core schemas are stable. Additive optional properties and new endpoints are compatible. Renaming/removing an operation, changing required fields, changing an enum/state, changing idempotency scope, or merging tenant/legal-owner/beneficiary fields requires a versioned contract change and review. Backend and frontend work may begin from this document only after A3 review; Phase B may refine auth implementation without changing the frozen protocol shape.
