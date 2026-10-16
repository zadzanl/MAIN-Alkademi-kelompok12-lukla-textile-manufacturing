# Warehouse implementation report

**Task record revision:** 1  
**Date:** 2026-10-16  
**Scope:** Source-backed anti-cross-contamination guardrail and honest non-persistent stock API boundary.

## Actual changes

- Added `MaterialQuantity`, `MaterialIssueRequest`, and `StockMovement` schemas in `backend/app/schemas/stock.py` using the frozen contract vocabulary.
- Kept `tenantId`, `legalStockOwnerId`, and `orderBeneficiaryId` as separate fields in `MaterialLot` and responses.
- Kept `/api/v1/stock` read-only over the existing fixture, added independent `tenantId` and `orderBeneficiaryId` filters, and added `X-Stock-Data-Source: demo-non-persistent` so the route does not imply durable inventory.
- Added frozen-contract `/api/v1/material-issuances` with `operationId: issueMaterial`.
- Added beneficiary mismatch validation before any possible quantity mutation. A mismatch returns `ORDER_BENEFICIARY_MISMATCH` and does not mutate the fixture.
- Matched-owner dispatch is blocked with `INVALID_STATE` because no stock repository/persistence exists. No backend success response or quantity decrement is claimed.
- Added `backend/tests/test_stock.py` covering separate scope dimensions, mismatch rejection without mutation, persistence-unavailable blocking, and generated OpenAPI route presence.
- Did not change frontend source. The existing `warehouseApi.ts` guardrail already returns a failed result for mismatches, and `WarehouseInventoryView.tsx` only shows the success toast after `res.ok` is true.
- Did not edit payroll files, frozen OpenAPI source, migrations, auth framework, or BRD/PRD files.

## Verification

| Check | Result |
|---|---|
| Backend focused warehouse pytest | **PASS** — `4 passed` (`backend/tests/test_stock.py`) |
| Frontend warehouse/unit test command | **PASS** — `74 passed`, including warehouse ownership and no-balance-mutation tests |
| Frontend TypeScript check | **PASS** — `npm run type-check` |
| Generated OpenAPI route inspection | **PASS** — `/api/v1/stock`, `/api/v1/material-issuances`, and `issueMaterial` present |
| Scoped static diagnostics | **PASS** — no errors in edited backend/schema/test files |
| Workspace hygiene | **PASS** — `python scripts/check_workspace_hygiene.py` |
| Playwright E2E | **NOT RUN** — harness invocation was not trustworthy in the shared persistent terminal and no browser evidence was collected |
| Database/persistence evidence | **BLOCKED / NOT RUN** — no warehouse repository or database-backed stock implementation exists |
| Full backend suite | **NOT RUN** — focused warehouse tests were run; unrelated dirty payroll work was not used as warehouse evidence |

## Known ceiling

The backend still serves deterministic fixture reads and cannot persist receipts, issuances, adjustments, valuation, scrap, or cutting results. This report makes no production-persistence claim. A future repository-backed implementation must preserve the three independent scope dimensions and perform the ownership check inside the same transaction/lock boundary before decrementing stock.
