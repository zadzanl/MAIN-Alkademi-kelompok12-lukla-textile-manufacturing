# Unverified Business Decisions — Lukla Operations Engine

**Task record:** `task-record.md`, revision 17  
**Inspection date:** 2026-10-15  
**Scope:** Documentation research only. No application source, design decision, or planning requirement was changed. No subagents were dispatched.

## Executive finding

The planning suite does not contain an approved business baseline. The BRD and PRD are drafts awaiting approval; `19-business-defaults-register.md` explicitly marks every proposed default `UNRESOLVED / PRODUCTION_BLOCKED`. The acceptance plan and schema/API plans also state that no application, migration, runtime, browser, deployment, or executable acceptance tests were run.

The items below are limited to decisions and source/provenance gaps actually found in the inspected documents. “Documented as pending” means the documents explicitly record the issue as unresolved or blocked. “Not tested” means the documents explicitly say execution evidence does not exist; it is not itself evidence that the business rule is wrong.

## 1. Unresolved source / provenance

| Item | Classification and status | Exact references | What remains unverified |
|---|---|---|---|
| Missing slide 02c and FR-2.1 provenance | **Unresolved source/provenance — documented as pending.** | `00-deconstruction.md`, §“Slide 02c — Solusi… — NOT ON DISK” and §Status; `08-client-clarification-register.md` §6.1; BRD §7 RC1 FR-2.1 and §13.3 item 1; PRD A.9 OQ-1. | The original slide and its alleged solution pillars are unavailable. The eight-role matrix is visible on slide 04, but the FR-2.1 badge is not verified on an on-disk slide. Do not treat the missing slide’s content as source-backed. |
| Slide 07 exists only as a chat attachment, not an archived original photo | **Unresolved source/provenance — documented as pending.** | `00-deconstruction.md`, source inventory and §“Slide 07 — Mesin Payroll”; `08-client-clarification-register.md` §6.2; BRD §13.3 item 2; PRD A.9 OQ-2. | Payroll FR-10.1–FR-10.4 are recorded from the chat attachment, but the physical high-resolution original has not been archived/independently verified. |
| FR-1.4 definition is absent | **Unresolved source/provenance — documented as pending.** | `00-deconstruction.md`, extracted FR inventory/UNRESOLVED material; `08-client-clarification-register.md` §6.3; BRD §13.3 item 5 and §16.5 FR-1.4 inventory; PRD A.9 OQ-5 and B.1 “Menunggu klarifikasi”; API plan §3.1 and §4 (`DEFINITION_PENDING`). | The badge is visible in slide 03, but the scope is not. Legal-client onboarding, contacts, tax identity, contract verification, and other possible meanings are not source-confirmed. |
| Group-level FR-5 and FR-6 semantics | **Unresolved source/provenance — documented as pending.** | `00-deconstruction.md`, slides 03/04/09 and FR-5/FR-6 ambiguity notes; BRD §7 RC3 FR-6.2/related items and §13.3 items 3–4; PRD A.9 OQ-3/OQ-4 and B.1 “Menunggu klarifikasi”; API plan §3.1 and §3.1 endpoint note. | The source states warehouse/cutting concepts and mismatched-material rejection, but does not fully define stock transactions, adjustment/stocktake rules, cutting batches/markers/waste, or whether FR-6.2 belongs to Gudang, Cutting, or both. |

## 2. Unapproved business policy

These are not merely implementation details. The documents ask the client/business owner to choose or authorize them; the proposed values in register 19 are development fixtures or safety gates only.

| Item | Classification and status | Exact references | Decision still required |
|---|---|---|---|
| CMT shrinkage, scrap, mill-defect liability, remnants and branded scrap | **Unapproved business policy — documented as pending.** | `08-client-clarification-register.md` §§1.1–1.2; `19-business-defaults-register.md` §4 item 1 and OQ-9. | Contractual tolerance, compensation, ownership/return/disposal, and destruction controls. |
| Semi-CMT pricing, reimbursement, deposit, DP and payment terms | **Unapproved business policy — documented as pending.** | `08-client-clarification-register.md` §§1.3–1.4; `19-business-defaults-register.md` §4 items 3–4 and OQ-9. | Fixed package vs cost-plus vs reimbursement; deposit timing; cutting gate; CBD vs credit terms. |
| Overhead basis and commercial effect | **Unapproved business policy — documented as pending.** | `08-client-clarification-register.md` §2.1; BRD §7 FR-10.4 and §13.3; `19-business-defaults-register.md` OQ-9 and §5; API plan §4. | Unit vs SAM weighting, predetermined rate/idle capacity treatment, and whether overhead changes client billing or is internal analysis only. |
| Custodial inventory valuation and tax treatment | **Unapproved business policy — documented as pending.** | `08-client-clarification-register.md` §§2.2–2.3; `19-business-defaults-register.md` §4 items 6–7/OQ-9; BRD §3.2 and §9.1 are planning/accounting proposals, not authorization. | Quantity-only vs monetary subledger; PKP/PPN status; PPh 23 handling/automation. |
| Meal-pool allocation, bearer, and base | **Unapproved business policy — documented as pending.** | `08-client-clarification-register.md` §§3.1–3.2; `19-business-defaults-register.md` OQ-1/OQ-2; BRD §7 FR-10.2, §13.3 item 7, §16.1; PRD A.7 AS-3 and L.2. | Individual allocation basis (wage, equal headcount, or attendance), who bears the cost, and exact base composition. The 10–15% range is documented; its allocation/base is not approved. |
| QC bonus recipients, dynamic count, remainder, and clawback | **Unapproved business policy — documented as pending.** | `08-client-clarification-register.md` §3.3; `19-business-defaults-register.md` OQ-3/OQ-4/OQ-9; PRD A.9 OQ-6/OQ-9; acceptance `06-acceptance-tests.md` AT-06–AT-08. | Baseline names three recipients, but configurability/dynamic mandor count, nondivisible-currency destination, and post-delivery clawback are not authorized. |
| Payroll cutoff, late QC output, approval authority, payment method, disputes and downtime | **Unapproved business policy — documented as pending.** | `08-client-clarification-register.md` §§3.4 and 4.1–4.2; `19-business-defaults-register.md` OQ-5/OQ-6 and §5; `06-acceptance-tests.md` AT-04 and Additional unresolved assertions. | Saturday cutoff, treatment of uninspected output, bank/cash method, final approver, downtime pay, dispute correction window, and lock timing. |
| Reject/scrap wage and material-loss treatment | **Unapproved business policy — documented as pending.** | `08-client-clarification-register.md` §4.3; `19-business-defaults-register.md` OQ-7; BRD §6.1 and §13.3; schema §5 explicitly says no automatic reject deduction. | Whether a rejected unit receives zero wage, whether material recovery is allowed, lawful maximum deduction, and approval/legal basis. “Reject (scrap/potong gaji)” in BRD is not sufficient authorization. |
| QC acceptance, external inspection, needle detection, returns and warranty | **Unapproved business policy — documented as pending.** | `08-client-clarification-register.md` §§5.1–5.2; `19-business-defaults-register.md` OQ-8; API plan §4 says QC/payment rules remain pending. | AQL and inspection rights; needle detection; RMA responsibility, freight/rework cost, warranty, and claim accounting. |
| Client IP Chinese wall and sample/mass-order sign-off | **Unapproved business policy — documented as pending.** | `08-client-clarification-register.md` §§5.3–5.4; `19-business-defaults-register.md` OQ-9; `06-acceptance-tests.md` AT-09–AT-10; schema §8 says sample approval is not mass-order confirmation. | Required NDA/IP access policy, authorized client signatory/evidence, and internal authority to convert an approved sample to a mass order. |

## 3. Contradictions / conflicting statements

| Item | Classification and status | Exact references | Conflict and current state |
|---|---|---|---|
| QC status vocabulary differs | **Contradiction — documented but unresolved.** | `00-deconstruction.md`, slide 04 extraction and terminology variance; `06-acceptance-tests.md` execution protocol item 3 and Additional unresolved assertions; BRD §6.1/§7 FR-8.1; schema §3. | Slide 04 uses `lolos/reject/repair`; slide 05 uses `Pass/Repair/Reject`; slide 08 UI uses `lolos/repair/scrap`; BRD says `Reject/Scrap`. The acceptance plan deliberately makes no mapping between Reject and scrap. |
| `Menunggu QC` position/meaning differs across source views | **Contradiction — documented but unresolved.** | `00-deconstruction.md`, slide 04b extraction; slide 06 extraction; `06-acceptance-tests.md` AT-04 and Additional unresolved assertions. | Slide 04b places `Menunggu QC` on the QC→Payroll edge, while slide 06 describes assembly output entering `Menunggu QC` before QC. The plan records the discrepancy and does not treat it as resolved by the schema/API proposal. |
| QC bonus rounding remainder | **Contradiction — explicitly documented.** | PRD A.9 OQ-9; BRD §13.2/§16.1; PRD history/legacy reference to v1.3 position; `06-acceptance-tests.md` AT-08; `19-business-defaults-register.md` OQ-4. | One position says a Rp 1 remainder goes to a factory reserve; the BRD says remainder treatment is not determined and must not be assigned to a specific account. Current status is unresolved; register 19’s reserve-account value is only a proposed fixture. |
| Rate-card governance precedence | **Contradiction/ambiguity — documented as unresolved.** | `00-deconstruction.md`, slide 04 extraction; BRD §7 FR-7.2 and §11.1; `06-acceptance-tests.md` Additional unresolved assertions. | Slide 04 gives Owner rate-card change permission and Mandor component-rate determination; BRD FR-7.2 says Owner manages rate cards. Precedence, approval, and scope of the two permissions are not decided. |
| Review/approval status versus business authorization | **Contradiction in status interpretation, not a business rule.** | BRD approval sheet and header: “Draft — Menunggu Persetujuan” and all approvers pending; PRD header: “Draft — Menunggu Persetujuan”; `19-business-defaults-register.md` §§1–2; `task-record.md` revision 17 lines recording structural checks only. | Engineering review/traceability checks can be complete while business approval remains absent. The documents explicitly prohibit treating proposed defaults or planning review as authorization. |

## 4. “Not tested” is separate from “undecided”

The following are documented as **not tested**, not as failed or disproven business decisions:

- `06-acceptance-tests.md` header and execution ledger: all AT-01–AT-07, AT-09–AT-10 and AT-R01–AT-R08 are `NOT RUN`; blocked assertions are both `BLOCKED — decision needed` and `NOT RUN`.
- `11-database-schema-spec.md` §1 says the schema is a logical contract and no migration has executed; §9 says no SQL migration or runtime tests executed during planning.
- `12-api-contract-plan.md` §1 and §5: contract-first proposal; server not implemented and Phase A review remains open.
- `19-business-defaults-register.md` §6: no application, database, payroll, tax, legal, runtime, or deployment verification was performed while authoring the register.
- `task-record.md` revision-17 state: full OpenAPI validator, Spectral, Schemathesis, database/browser/runtime/deployment tests have not run; application runtime tests are not run. The recorded traceability script/structural checks are not semantic approval or runtime evidence.

Therefore, the planning suite supports statements such as “the rule is pending,” “the source is missing,” or “the test was not run.” It does **not** support a statement that the eventual application correctly enforces the rule, because no application/runtime evidence was inspected or reported here.

## Inspected documents

- `00-deconstruction.md`
- `BRD - Lukla Operations Engine - v2.2.1 - FINAL.md`
- `PRD - Lukla Operations Engine - v2.0 - Wagile.md`
- `06-acceptance-tests.md`
- `08-client-clarification-register.md`
- `11-database-schema-spec.md`
- `12-api-contract-plan.md`
- `19-business-defaults-register.md`
- `task-record.md` (revision 17 context)

No claims are made about files outside this inspected set.