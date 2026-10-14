# 19 — Business Defaults Register

**Change:** `lukla-ops-engine-planning`  
**Status:** PROPOSED / PENDING CLIENT AUTHORIZATION / `PRODUCTION_BLOCKED`  
**Date:** 2026-10-14  
**Scope:** Phase B planning artifact only. This register records configurable proposals; it does not approve, replace, or reinterpret BRD/PRD rules.

## 1. Decision discipline

The entries below are defaults for controlled development, test fixtures, and explicit configuration surfaces. They are not approved business policy. A deployment or payroll/QC/financial release must reject unresolved values and remain `PRODUCTION_BLOCKED` until an authorized decision is recorded with evidence, owner, effective date, and an audit event.

A proposed value must never silently become:

- a BRD or PRD requirement;
- a financial-rule approval;
- a payroll payment instruction;
- a legal-title or client-compensation decision;
- a QC bonus entitlement;
- a statutory or employment-law conclusion.

Configuration changes are versioned, tenant-scoped where applicable, validated against the contract, and auditable. Historical calculations retain the rule version used; changing a default does not rewrite prior payroll, QC, ledger, or invoice records.

## 2. Status and authorization fields

- **Status:** Every row is `UNRESOLVED` and `PRODUCTION_BLOCKED` unless an authorized business owner changes it through the financial/business-rule approval workflow.
- **Owner:** `BusinessOwner` is the accountable decision role; the technical team may propose and implement a configuration surface but cannot approve the value.
- **Effective date:** `PENDING_CLIENT_DECISION`; no effective date is inferred from the date of this document.
- **Audit event:** An eventual decision must emit an immutable business-rule decision event containing question ID, selected option/value, approver identity, authority basis, effective timestamp, superseded value, and rule version. Draft/default edits emit a separate `business_default_proposed` event and do not authorize production use.

## 3. Unresolved decisions OQ-1–OQ-9

| ID | Unresolved question and source uncertainty | Proposed configurable value for development only | Owner | Effective date | Required audit event | Status |
|---|---|---|---|---|---|---|
| **OQ-1** | **Meal-pool allocation basis (FR-10.2):** the source defines a total 10–15% pool but does not define whether individual allocation is proportional to wage, equal per active head, or attendance/mandays. Source: `08-client-clarification-register.md` §3.1; `FR-10.2`. | `meal_pool_allocation = ATTENDANCE_MANDAYS`; allowed alternatives: `WAGE_PROPORTIONAL`, `ACTIVE_HEAD_EQUAL`, `ATTENDANCE_MANDAYS`. Fixtures use attendance/mandays only to exercise configuration. | BusinessOwner + FinancePayroll | PENDING_CLIENT_DECISION | `business_default_proposed`; final `business_rule_approved` | `UNRESOLVED / PRODUCTION_BLOCKED` |
| **OQ-2** | **Meal-pool bearer (FR-10.2):** unclear whether the 10–15% burden is Lukla operating expense or a client surcharge. Source: register §3.2. | `meal_pool_bearer = LUKLA_OPERATING_EXPENSE`; alternatives: `CLIENT_SURCHARGE`, `CONTRACT_SPECIFIC`. No invoice behavior is enabled by this proposal. | BusinessOwner + FinancePayroll + Commercial | PENDING_CLIENT_DECISION | `business_default_proposed`; final `business_rule_approved` | `UNRESOLVED / PRODUCTION_BLOCKED` |
| **OQ-3** | **QC bonus recipients and dynamic headcount (FR-9.2 / FR-10.3):** source fixes a three-way pool in the baseline, while the register asks whether QC participates and whether active mandor count changes allocation. Source: register §3.3; approved review notes preserve the shared divide-by-three rule but do not authorize alternatives. | `qc_bonus_recipient_policy = FIXED_THREE_WAY_BASELINE`; `recipients = [MandorA, MandorB, HeadOfOperations]`; `dynamic_headcount = false`. Any proposed restructuring remains pending and cannot be enabled by default. | BusinessOwner + Operations + FinancePayroll | PENDING_CLIENT_DECISION | `business_default_proposed`; final `business_rule_approved` | `UNRESOLVED / PRODUCTION_BLOCKED` |
| **OQ-4** | **QC bonus remainder (FR-10.3):** division-by-three may leave fractional minor currency units. Destination is not authorized by the source. Source: register §3.3; technical plan risk §7. | `qc_bonus_remainder = FACTORY_RESERVE_ACCOUNT`; alternatives: `HEAD_OF_OPERATIONS`, explicit carry-forward. The proposal does not post a remainder. | BusinessOwner + FinancePayroll | PENDING_CLIENT_DECISION | `business_default_proposed`; final `business_rule_approved` | `UNRESOLVED / PRODUCTION_BLOCKED` |
| **OQ-5** | **Payroll Saturday cut-off and uninspected output (FR-10.1):** source says weekly/Saturday processing but does not define local cut-off or the treatment of output not yet inspected. Source: register §3.4. | `payroll_cutoff_local = Saturday 12:00 Asia/Jakarta`; `uninspected_output = DEFER_TO_NEXT_PERIOD`; both are configurable and must block payroll approval while unresolved. | BusinessOwner + Operations + FinancePayroll | PENDING_CLIENT_DECISION | `business_default_proposed`; final `business_rule_approved` | `UNRESOLVED / PRODUCTION_BLOCKED` |
| **OQ-6** | **Payroll approval authority and payment method:** source does not authorize the final approver or bank-versus-cash execution. Source: register §3.4; API has separate `approvePayroll` and `recordPayrollPayment` operations. | `payroll_final_approver_role = Owner`; `payment_method = BANK_TRANSFER`; these are test fixtures only and cannot authorize a payment. | BusinessOwner + FinancePayroll | PENDING_CLIENT_DECISION | `business_default_proposed`; final `business_rule_approved` | `UNRESOLVED / PRODUCTION_BLOCKED` |
| **OQ-7** | **Reject/scrap wage and material-loss treatment:** source mentions Reject and possible wage deduction but does not define a lawful penalty or maximum deduction. Source: register §4.3. | `reject_compensation_policy = NO_AUTOMATIC_DEDUCTION`; route to manual governed review. No material-cost recovery or wage deduction is implemented from this proposal. | BusinessOwner + HR/Legal + FinancePayroll | PENDING_CLIENT_DECISION | `business_default_proposed`; final `business_rule_approved` | `UNRESOLVED / PRODUCTION_BLOCKED` |
| **OQ-8** | **QC acceptance and post-delivery returns:** AQL, external inspection, needle detection, RMA responsibility, and warranty/claim accounting are absent from the source baseline. Source: register §5.1–§5.2. | `external_aql = NOT_CONFIGURED`; `post_delivery_rma = MANUAL_CASE_REVIEW`; no automated acceptance threshold, chargeback, or warranty liability is enabled. | BusinessOwner + Quality + Commercial | PENDING_CLIENT_DECISION | `business_default_proposed`; final `business_rule_approved` | `UNRESOLVED / PRODUCTION_BLOCKED` |
| **OQ-9** | **Scope/provenance and commercial ownership uncertainties:** source gaps include slide 02c/07 evidence, FR-1.4 definition, fabric scrap/remnant ownership, Semi-CMT billing/deposit, tax status, client sign-off authority, IP isolation policy, and missing definitions for group FR-5/FR-6. Sources: register §1, §2, §5.3–§5.4, §6; technical plan §2 and §5. | `source_gap_policy = BLOCK_UNRESOLVED`; `fr_1_4 = DEFINITION_PENDING`; `fr_5_and_fr_6 = NO_INVENTED_BEHAVIOR`; `legal_owner_and_beneficiary = EXPLICIT_REQUIRED`; `tax_behavior = OUT_OF_SCOPE_UNTIL_AUTHORIZED`. These are safety gates, not business approvals. | BusinessOwner + Legal/Commercial + Product | PENDING_CLIENT_DECISION | `business_default_proposed`; final `business_rule_approved` per item | `UNRESOLVED / PRODUCTION_BLOCKED` |

## 4. Source-uncertainty inventory outside the nine IDs

The OQ rows consolidate the register, but the following uncertainties remain visible and must not be lost in implementation:

1. CMT shrinkage/scrap tolerance, compensation, and mill-defect liability (`08` §1.1).
2. Remnant/end-of-roll ownership and branded-scrap destruction (`08` §1.2).
3. Semi-CMT supplemental-material pricing, reimbursement, and deposit timing (`08` §1.3).
4. Down-payment/cutting gate and client payment terms (`08` §1.4).
5. Overhead allocation basis, commercial effect, and idle-capacity treatment (`08` §2.1; FR-10.4).
6. Custodial-material monetary valuation versus quantity-only subledger (`08` §2.2).
7. PKP/PPN and PPh 23 status/automation (`08` §2.3); no statutory tax rule is proposed here.
8. Payroll cut-off, absence/downtime handling, transfer/cash method, dispute window, and correction lock (`08` §3.4, §4.1–§4.2).
9. QC bonus clawback, AQL, client audit, needle detection, and RMA (`08` §3.3, §5.1–§5.2).
10. Client IP Chinese-wall policy and sample sign-off authority (`08` §5.3–§5.4).
11. Missing Slide 02c, original Slide 07, and undefined FR-1.4 / grouped FR-5 / FR-6 semantics (`08` §6; `00-deconstruction.md`).

These are either represented by OQ-1–OQ-9 or intentionally remain blocked under OQ-9. No item is promoted to an approved rule by appearing in this list.

## 5. Configuration and release gates

When a payroll, QC, or financial operation references a rule whose status is `UNRESOLVED / PRODUCTION_BLOCKED`, the contract error is `FINANCIAL_RULE_PENDING`. The operation must not calculate, approve, pay, or post using a development-only default.

A configuration record must include `rule_id`, `scope`, `value`, `allowed_values`, `status`, `source_question_id`, `proposed_by`, `approved_by`, `effective_at`, `version`, and `audit_event_id`. `approved_by` and `effective_at` are null for every entry in this document.

Production gates:

- Reject release when any required financial, payroll, QC, ownership, or tax value is `UNRESOLVED`.
- Reject payroll calculation or payment approval when its referenced rule version is unresolved; this aligns with the existing `calculate_weekly_payroll(period, rule_version)` contract boundary.
- Reject financial-rule approval unless the authorization evidence required by `FinancialRuleApproval` is present; a draft/default proposal is not authorization evidence.
- Preserve prior rule versions and their calculations; never mutate posted ledger entries to apply a later decision.
- Log proposed, approved, activated, superseded, and blocked transitions as separate audit events.

## 6. Traceability and verification limits

- Source register: `08-client-clarification-register.md`.
- Approved plan: `09-technical-blueprint-completion-plan.md` §7 and §8.
- Contract: `artifacts/contracts/openapi.yaml`, especially `calculateWeeklyPayroll`, `approveFinancialRule`, `FinancialRuleApproval`, and `searchOperationalDocuments`.
- Database invariants: `artifacts/11-database-schema-spec.md` and `artifacts/tech_plan-blueprint-001.md`.
- Review baseline: `artifacts/review/blueprint-contract-review.md`, which states that financial defaults remain proposed/pending and production-blocked.

This is a planning register. No application, database, payroll, tax, legal, runtime, or deployment verification was performed while authoring it.
