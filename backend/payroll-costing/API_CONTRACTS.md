# API Contracts — Payroll & Costing

Authoritative source: `openspec/changes/lukla-ops-engine-planning/contracts/openapi.yaml`. This file is a routing index, not a schema copy. If this table and the contract disagree, the contract wins and this file is wrong.

The sketch routes in `docs/MODULES_ARCHITECTURE.md` (`/api/v1/payroll-rates`, `/api/v1/worker-calculations`) are superseded and must not be implemented.

## Owned operations

| operationId | Method | Path | Roles | Notes |
| --- | --- | --- | --- | --- |
| `createPayrollPeriod` | POST | `/payroll-periods` | FinancePayroll | `PeriodRequest` validation, `Asia/Jakarta` |
| `listPayrollPeriods` | GET | `/payroll-periods` | Owner, FinancePayroll | |
| `calculateWeeklyPayroll` | POST | `/payroll/weekly/{periodId}` | FinancePayroll | `409 FINANCIAL_RULE_PENDING` |
| `getPayrollStatement` | GET | `/payroll/weekly/{periodId}/statement` | Owner, FinancePayroll | `reserve` stays zero while OQ-4 is open |
| `getBonusPool` | GET | `/payroll/weekly/{periodId}/bonus-pool` | Owner, FinancePayroll | exactly three recipients; `409` |
| `approvePayroll` | POST | `/payroll/weekly/{periodId}/approval` | FinancePayroll | pins `version` + `inputHash` |
| `recordPayrollPayment` | POST | `/payroll/weekly/{periodId}/payment` | FinancePayroll | approved run only |
| `recordOverhead` | POST | `/overhead` | FinancePayroll | appends an overhead cost event |
| `calculateOverhead` | POST | `/overhead/{periodId}/allocation` | FinancePayroll | `NO_OUTPUT` for a zero-production month; `409` |
| `listFinancialRules` | GET | `/financial-rules` | Owner, FinancePayroll | |
| `proposeFinancialRule` | POST | `/financial-rules` | Owner, FinancePayroll | creates a `PENDING` version |
| `approveFinancialRule` | POST | `/financial-rules/{ruleId}/approval` | Owner | requires `evidenceFileId` |
| `runSaturdayPayrollJob` | POST | `/internal/jobs/saturday-payroll` | serviceAuth `ServicePayrollJob` | idempotent, service credential only |
| `runMonthlyOverheadJob` | POST | `/internal/jobs/monthly-overhead` | serviceAuth `ServiceOverheadJob` | idempotent, service credential only |
| `getJob` | GET | `/jobs/{jobId}` | Owner, FinancePayroll | terminal status readback |

## Consumed operations (not implemented here)

| operationId | Owner | Why payroll needs it |
| --- | --- | --- |
| `recordSewingTally`, `verifySewingTally` | MOD-04 | produces the verified tallies that make a unit wage-eligible |
| `inspectUnit` | MOD-04 | produces `QC_PASS` dispositions and `qc_bonus_accruals` |
| `appendLedgerTransaction`, `reverseLedgerTransaction`, `getLedgerEntries` | MOD-01 | posts and reverses the monetary entries behind wage credits |

## Shared rules

- Errors use the `Problem` model; the codes this module emits include `FINANCIAL_RULE_PENDING`, `INVALID_STATE`, `IDEMPOTENCY_CONFLICT`, `FORBIDDEN`, `TENANT_CONTEXT_MISSING`, and `SERVICE_SCOPE_REQUIRED`.
- Every mutation carries `Idempotency-Key` (16–200 characters) scoped to `(tenant, operationId, key)`.
- Money is `Money{amountMinor, currency}` in integer minor units; no floating point.
