# blueprint-contract-resume-002 — bounded read-only resumption of Phase A review

**Date:** 2026-10-13
**Scope:** targeted defect points and inconsistencies across the partial Phase A artifacts (`10-`, `11-`, `12-`, `contracts/openapi.yaml`) versus canonical root documents (`09-`, `tech_plan-blueprint-001.md`, `00-deconstruction.md`, `04-rbac-matrix.md`, `06-acceptance-tests.md`, `08-client-clarification-register.md`) and the rev-13 task-record list. No contract edit, no source edit, no git operation, no subagent dispatched.
**Mode:** read-only evidence sweep; semantic checks only.
**Companion/boundary:** this report does not redo structural openapi validation covered by `blueprint-phase-a-recovery-002.md`. It re-reads several findings and adds new ones found in code paths the prior report did not enumerate.

---

## 1. Checkpoint confirmation (verified)

| Item | Status | Evidence |
|------|--------|----------|
| `task-record.md` exists, rev 13 | Present (lines 1–4 read); header verbatim `**Revision:** 13`, `**Updated:** 2026-10-13`. | `openspec/changes/lukla-ops-engine-planning/task-record.md` |
| `09-technical-blueprint-completion-plan.md` exists at root | 10.4 KB, read fully (300 lines). Plan covers 18 artifact deliverables (A + B + C). | root |
| `artifacts/tech_plan-blueprint-001.md` exists | 17 KB; full plan matches rev 13's "see also" pointer. | `artifacts/tech_plan-blueprint-001.md` |
| `artifacts/10-technology-stack-and-decisions.md` exists | 5.6 KB; rev 12 alignment. | `artifacts/10-…` |
| `artifacts/11-database-schema-spec.md` exists | 29.7 KB; comprehensive schema spec. | `artifacts/11-…` |
| `artifacts/12-api-contract-plan.md` exists | 6.3 KB; 4 sections + §5 compatibility. | `artifacts/12-…` |
| `contracts/openapi.yaml` exists, parseable | 75.6 KB; loaded with `yaml.safe_load`; OpenAPI 3.1.0. | `artifacts/contracts/openapi.yaml` |
| Root `04-rbac-matrix.md` (canonical Phase 2 outcome, rev-5/10) | 7.0 KB; reviewed. | root |
| Root `06-acceptance-tests.md` (Phase 2 outcome) | reviewed; every AT-## + AT-R## marked **NOT RUN** (no application). | root |
| Root `08-client-clarification-register.md` | 6 domains; all answers **CLIENT_DECISION_PENDING**. | root |

**Action evidence:** read_file on the items above; no terminal `python`'d work modifies them. `python C:\Users\lenovo\AppData\Local\Temp\r*.py` scripts ran against the contract only, did not write to disk.

---

## 2. Operation-count drift between contract, doc, and rev-13 claim (Verified)

| Source | Operation count claim | Independent verification |
|---|---|---|
| `task-record.md` rev 13 (line "Parent verification") | "**42 operations**, 42 unique operationIds, zero unresolved local references" | Not currently true. The contract now contains 69 operations and 69 unique IDs. |
| `artifacts/blueprint-phase-a-recovery-002.md` §1 (parent-confirmed check) | "**42 operations**" snapshot table; cites file mtime 2026-10-13 19:43:42, 53312 B | Snapshot was accurate at its authoring time. Contract has since been extended; size 75.6 KB, mtime 2026-10-13 21:26:03. |
| `contracts/openapi.yaml` (current) | 69 operations / 69 unique IDs (verified via `yaml.safe_load` + Python counter) | The recovery-report's "verified" assertion is now stale. |
| `12-api-contract-plan.md` §3 | 10 rows × ≈4 ops each → ~42 ops name-listed | The doc enumeration only names 42 ops; the remaining 27 ops live in the contract under tag `workflow` and are not enumerated in §3. |
| `artifacts/blueprint-platform-001.md` §4.2 / §6 | "20 vs 26 FRs" conflict flagged between `proposal.md` and `09-plan L94` (independent of count). | Unrelated to op count; remains a recap finding. |

**Net finding:** the rev-13 "verified" claim and the doc are both **stale**. The contract is now larger than what either documented. This is a "doc-to-contract" drift, not a regression — the additional operations are precisely the surface the recovery report §3 said was missing (assembly, operator, line, sample-conversion, payroll-approval-payment, client-invoice, financial-rule, session lifecycle). Whoever reads the 12-doc alone will not see that those surfaces exist.

**Minimal proposed fix:** rewrite §3 of `12-api-contract-plan.md` to enumerate at least the 27 `workflow`-tagged operations or, equivalently, reference the contract by tag with the operation count shown as 69. Re-run the rev-13 verification command (`yaml.safe_load` + Python counter) and update the task record's "Parent verification" line. This is **clarification-requiring**: do we preserve the original catalog layout (each row = 1 source cluster) and fold the 27 into existing rows, or break §3 into 11 numbered sub-tables? Default option: keep the current shape, but add a single new §3.X "Workflow endpoint surfaces (added in revision H)" listing the 27 opIds with their tags and source-IDs.

---

## 3. Catalog ↔ contract drift (Verified)

The 12-doc claims the following ledger op name:

> "Ledger/audit | `appendLedgerTransaction`, `reverseLedgerTransaction`, `listLedgerEntries`, `listAuditEvents` | FR-3.1; Owner, Finance"

The contract actually exposes:

| operationId | path | method |
|---|---|---|
| `appendLedgerTransaction` | `/ledger/transactions` | POST |
| `reverseLedgerTransaction` | `/ledger/transactions/{transactionId}/reversals` | POST |
| **`getLedgerEntries`** | `/ledger/entries` | GET |
| `listAuditEvents` | `/audit/events` | GET |

**Finding (rev-13 explicit item):** `listLedgerEntries` vs `getLedgerEntries` is the exact operation-name mismatch the rev-13 task record called out as needing a fix. Either:
- The doc was written first and the contract was edited to use `getLedgerEntries` (most likely — the doc's spelling is conventional plural-noun "list" while the contract is REST-resource "get"). 
- The contract rename is the desired direction and the doc must follow. 
- The contract rename is a typo and should revert.

The contract spelling is internally consistent (e.g., `getLedgerEntries`, `getLedgerEntries` returns `LedgerPage` items, `getPayrollStatement`, `getJob`, `getDashboard`, `getPortalOrderStatus`, `getFileDownload`, `getOrder`, `getMyContext` — all singular-resource "get" verbs). The doc spelling is not. **This is a doc-to-contract inconsistency, not a contract bug**, but it does block any reviewer who treats the doc as ground truth.

**Minimal proposed fix:** rename `listLedgerEntries` → `getLedgerEntries` in `12-api-contract-plan.md` §3 row 3. No clarification needed unless the user wants the contract renamed to match the doc (which would break the established singular-resource naming convention).

---

## 4. `inspectUnit` example-vs-schema misalignment (Verified)

`contracts/openapi.yaml` at the `/qc-inspections` POST `inspectUnit` operation:

- `summary`: **"Classify unit Pass Repair Reject"** (uses "unit")
- `x-invariant`: **"One eligible unit earns at most one wage credit and one bonus accrual; repair keeps original operator."** (uses "unit" once, but the invariant follows the assembly model)
- `x-source-ids`: `['FR-8.1', 'FR-8.2', 'FR-9.1', 'FR-10.3']` (consistent with QC scope)
- `requestBody.content.application/json.example` (read directly):

  ```json
  {"garmentUnitId":"55555555-5555-4555-8555-555555555555",
   "disposition":"PASS",
   "originalOperatorId":"44444444-4444-4444-8444-444444444444"}
  ```

- `requestBody.content.application/json.schema`: `$ref: QcRequest` whose `required` is **[`assemblyId`, `disposition`, `defects`]**.
- `QcRequest.properties`: `assemblyId` (UUID, $ref to Uuid), `disposition` (enum PASS/REPAIR/REJECT), `defects` (array of `Defect`).

**Findings:**
1. The schema correctly enforces `assemblyId` (alignment with rev-13's "QC must target finished assemblies" requirement and with `qc_inspections.assembly_id` column defined in `11-`).
2. The example hard-codes three different fields `garmentUnitId` + `originalOperatorId` — both of which are **NOT in the schema**. Reading the example alone would suggest unit-level QC targeting with operator attribution, contradicting the schema and contradicting the rev-13 fix requirement.
3. The summary still says "unit", not "assembly". The 11-doc uses `assembly` consistently (status enum includes `ASSEMBLING`, `MENUNGGU_QC`, etc.) and `qc_inspections.assembly_id uuid` is the structural key.

**Severity:** documentation defect (example and summary wrong), not a schema bug. The schema is correct. This is exactly the kind of mismatch a downstream agent or human reviewer would propagate into a wrong fixture or wrong test.

**Minimal proposed fix:** rewrite `inspectUnit.example` to use `assemblyId` and `defects[]` matching `QcRequest`. Rewrite `summary` to "Classify assembly Pass/Repair/Reject". Update x-view coverage note. Does not require user clarification.

---

## 5. `approveFinancialRule` schema misuse (Verified)

`contracts/openapi.yaml` `/financial-rules/{ruleId}/approval` POST `approveFinancialRule`:

- `x-roles`: `[Owner]`
- `x-invariant`: "Permission itself is proposed; requires external authorized business approval evidence, not plan approval."
- `requestBody.content.application/json.schema`: `$ref: PaymentEvidence`
- `PaymentEvidence` schema:

  ```yaml
  {type: object, required: [externalReference, evidenceFileId],
   properties: {externalReference: {type: string, minLength: 1},
                evidenceFileId: {$ref: '#/components/schemas/Uuid'}}}
  ```

**Cross-check on meaning:** `PaymentEvidence` is used **correctly** for `recordPayrollPayment` × `PaymentEvidence` (where externalReference+evidenceFileId is the right shape). But on a **financial-rule approval endpoint**, asking for `externalReference` (a payment confirmation reference) and `evidenceFileId` (a payment receipt file) is semantically off:

- A financial-rule approval records a governance decision; the natural shape is `approvedAt` + `note` + `approvedBy` (already implied by x-roles) + an optional evidence file pointer for the audit, but not "externalReference". `externalReference` is a payment-side concept (bank txn id).
- The same op's `x-invariant` says "Permission itself is proposed; requires external authorized business approval evidence, not plan approval." — so evidenceFileId may be intentional, but `externalReference` is not.
- Same problem exists nowhere else in the file: `approvePayroll` → `PayrollApproval` (right); `approveSample` → `ApprovalEvidence` (RevisionId + evidenceFileId, right); `verifySewingTally` → `ApprovalRequest`; `approvePurchaseOrder` → `ApprovalRequest`. Only `approveFinancialRule` reaches for `PaymentEvidence` for a non-payment action.

**Severity:** contract-level misunderstanding; downstream code that consumes `externalReference` on a rule-approval POST would mis-attribute a payment-ref value as a rule-approval reference and lose audit fidelity.

**Minimal proposed fix:** introduce `FinancialRuleApproval` schema `{type: object, additionalProperties: false, properties: {evidenceFileId: {$ref: Uuid}, note: {type: string, maxLength: 500}}}` (no required fields beyond idempotency key on the parameter side) and replace the `$ref` in `approveFinancialRule`. **Clarification-requiring**: should rule approval carry its own evidence file pointer at all, given that `financial_rule_versions.approved_by uuid` already records the actor and `approved_at` would be derived? If the answer is yes (a separate paper trail file is required), then evidenceFileId is the only sensible property. If no, both fields can be omitted.

---

## 6. `createClientInvoice` source-id misattribution (Verified)

`contracts/openapi.yaml` `/client-invoices` POST `createClientInvoice`:

- `x-source-ids`: **`['FR-3.1']`**
- `x-roles`: `['FinancePayroll']`
- `x-invariants`: "Atomic mutation with audit and idempotency; new capability requires approved business permission."

`listClientInvoices` and `issueClientInvoice` also list `x-source-ids: ['FR-3.1']` and `['FR-3.1']` respectively. FR-3.1 in the canonical register is **"Riwayat transaksi immutable (locked transaction history)"** — i.e., the ledger immutability rule.

**Cross-check on what FR-3.1 actually covers**:
- 11-doc says ledger bookkeeping drives from FR-3.1 (lock history). 
- 08-register mentions ledger under §2.3 (PPh23/etc.) but **commercial client invoicing** is §2.2 (custodial valuation) and §5 (QC/after-sales), not §2.3 ledger.
- The only FR that the register cleanly maps to commercial client invoicing is **none of FR-1.1..FR-10.4** — it is an extension surface (similar to a B2B extension outside the 26 FR inventory).

**Severity:** x-source-ids are the primary tool the verifier (per `tech_plan-blueprint-001.md`) uses to assert operational coverage. Mislabeling client invoices under FR-3.1 (ledger) makes the verifier pass-by-spurious-match and obscures the real coverage gap: client invoicing has no formal FR provenance.

**Minimal proposed fix:**
- Either remove `FR-3.1` from `createClientInvoice` / `issueClientInvoice` / `listClientInvoices` (treat as outside-26 surface, label e.g. `extension:commercial-ar` or omit `x-source-ids` per the contract schema convention).
- Or, if the user wants to keep client invoices under the FR coverage umbrella, route them as `x-source-ids: ['extension:commercial-ar']` and add a `tech_plan-blueprint-001.md` decision note explaining the extension convention.

Clarification needed: the recovery report already flagged this surface as missing; the task record calls it a "Required Phase A fix". The default I would pick is to remove `FR-3.1` and either leave `x-source-ids: []` (with a verbose `x-invariant` explaining why) or use an extension label. **Ask user.**

---

## 7. `FinancialRuleRequest` enums hard-code proposed-but-unauthorized defaults (Verified)

`components.schemas.FinancialRuleRequest` of `contracts/openapi.yaml` (and consumed by `proposeFinancialRule`):

```text
mealBasis:               enum: [VERIFIED_WAGES_PROPOSED]
mealBasisPoints:         integer, min 1000, max 1500
mealDistribution:        enum: [PROPORTIONAL_PROPOSED, EQUAL_ACTIVE_PROPOSED]
bonusRate:               Money
bonusRecipientIds:       array, minItems 3, maxItems 3, uniqueItems true,
                         items: Uuid
remainderPolicy:         enum: [BLOCK_NON_DIVISIBLE, RESERVE_PROPOSED]
cutoffLocal:             string
overheadBasis:           enum: [FIRST_PASS_FINISHED_UNITS_PROPOSED]
```

**Findings:**
1. Every configurable business parameter is suffixed `_PROPOSED`, signalling "no client decision yet". That naming convention is consistent with `08-client-clarification-register.md` `Domain 2` and `Domain 3` (every answer is BLOCKED).
2. But the enums are **closed** (one or two values), and the API is the only way to install a rule. A client who answers the questions and wants to set, e.g., `mealDistribution=ABSENTEE_DAYS` cannot do so — the enum does not allow it even after authorization.
3. `bonusRecipientIds` has `minItems: 3, maxItems: 3, uniqueItems: true`. The `08-register` §3.3 explicitly asks: *"Apa yang terjadi jika jumlah mandor yang bertugas berubah … Apakah pembagian bonus menjadi dinamis?"* — i.e., this is BLOCKED. Hard-coding 3 in the contract silently closes the question before the user approves it. `tech_plan-blueprint-001.md` says "None silently invented" — but `minItems: 3` is silent enforcement.
4. `mealBasisPoints: min 1000, max 1500` matches the slide-07 "10–15% of wages" bound. This is **observed** in slide-07 chat-attachment transcription, not authorized as a binding business rule. Bound itself is faithful; it does not silently invent the bounds.
5. There is no `x-source-ids` or `x-invariant` annotation on the schema that says "this enum is provisional; new values accepted after client authorization". This is a documentation gap, not an enforcement bug.

**Severity:** contract-binding-but-provisional state. The blockBusinessRulePending invariant is encoded at the API level — `calculateWeeklyPayroll` exists with the right x-invariant — but the rule *type* offers only "PROPOSED" values.

**Minimal proposed fix:**
- Add a contract-level note (e.g., on `FinancialRuleRequest` or in 12-doc §4 "State and financial rules"): "Enum values suffixed _PROPOSED are placeholders; production deployment must be preceded by client confirmation or by rule-type extension PR adding the authorized alternative".
- **Clarification required:** do we widen `bonusRecipientIds.minItems` from 3 to a tuple `[1..N]`, or keep min 3 and require the client to drop one recipient via a separate ops step if a mandor leaves? The user's `08-register` question 3.3.2 directly drives this.

---

## 8. Verification anchors summary

| Anchor | Source | Claim | Status |
|---|---|---|---|
| 8 roles | `04-rbac-matrix.md` (rows 1..8) + `AccountRequest.properties.role.enum` in YAML | Identity and access modules | **Verified equal** |
| 4 closing scenarios | `06-acceptance-tests.md` (Closing scenarios 1–4) | Acceptance scope | **Verified** (every AT marked NOT RUN) |
| 26 PRD IDs vs 20 register IDs | `09-` L94 + `tech_plan-blueprint-001.md` "Current Reality" | Two distinct coverage sets | **Verified, 26/20 reconciled in spec** |
| Append-only ledger | `11-` §5 `append_ledger_transaction` prose + `ledger_transactions` "no UPDATE/DELETE" | Immutability | **Verified in prose**, not in spec → audit dependency |
| `qc_inspections.assembly_id` (rev-13 first fix) | `11-` §3 row "qc_inspections" + contract `QcRequest.assemblyId` | QC target = assembly | **Verified both in DB spec and in contract schema** |
| Bonus divide-by-three rule | `BonusPool` schema (min/max 3 recipients) + `getBonusPool` x-invariant "FR-9.2 and FR-10.3 are one divide-by-three rule" + `11-` §5 `classify_qc_unit` "ONE bonus per assembly" | One rule, not two | **Verified in YAML invariants**, but `minItems: 3` is undocumented as provisional (see §7 above) |
| `FINANCIAL_RULE_PENDING` stable code | `11-` §5 + `12-api-contract-plan.md` §2 | Stable error code while rules pending | **Verified in prose** — does not appear in the YAML `components.responses.FinancialRulePending` (that's a *response* template, not the *code* itself). Confirm whether the response body actually emits `code = FINANCIAL_RULE_PENDING`. |
| Provision defaults blocked | `11-` §5 + `10-` §4 ¶5 ("Financial rules are configurable but unresolved rules carry FINANCIAL_RULE_PENDING and block production payroll approval") | No silent defaults | **Verified in prose**; the only available enum values are PROPOSED (see §7) |
| RLS posture | `11-` §6 ("ENABLE + FORCE …" + `current_setting('app.tenant_id', true)` audit) | RLS as the boundary | **Verified**, but no SQL migration example is included (only prose rules). Plan-of-record `09-` AC-2 says "define every table, RLS policy, and trigger needed"; migration ordering is in `tech_plan-blueprint-001.md` "Migration sequence M012". |
| Service principal separation | `10-` §3 + `12-api-contract-plan.md` §1 ("X-Service-Principal + service credential") | Distinct from employee roles | **Verified** in contract (`serviceAuth` securityScheme + `runSaturdayPayrollJob` x-roles `ServicePayrollJob`); the role is not present in `AccountRequest` enum, which is correct (it's a non-employee role). |

---

## 9. Other minor items (Verified)

| # | Finding | File:line | Severity | Fix |
|---|---------|-----------|----------|-----|
| M1 | `listFinancialRules` operation has `summary: None`, `description: None`, `description: ""` | `openapi.yaml` path `/financial-rules` GET | Minor (doc) | Add summary "List financial rule versions" + description "Returns versioned rules with status filter" |
| M2 | `createPayrollPeriod`, `listPayrollPeriods`, `approvePayroll`, `getPayrollStatement`, `createClientInvoice`, `listClientInvoices`, `issueClientInvoice`, `getJob`, `createLine`, `createOperator`, `listAssemblies`, `listAssignments`, `listOperators`, `listLines`, `getFileDownload`, `listSamples`, `listRateCards` — all have `summary: None`. | (workflow tag in YAML) | Minor (doc consistency) | Add minimum useful summary to each. None of these block parallel work because the schema is complete. |
| M3 | `inspectUnit.summary = "Classify unit Pass Repair Reject"` while schema uses `assemblyId` (see §4) | `openapi.yaml` `/qc-inspections` POST | Doc | Already covered in §4 — change to "Classify assembly as Pass/Repair/Reject". |
| M4 | `12-api-contract-plan.md` does not list the `Idempotency-Key` parameter for many operation rows | 12-doc §3 | Minor (doc) | Add "(`Idempotency-Key` required for write ops)" note once in §3 prologue rather than row-by-row. |
| M5 | `61` line of `12-api-contract-plan.md` says "FR-5 and FR-6 are group-level status markers only" — accurate. But the list under "Warehouse/cutting" maps `recordCuttingResult → FR-6, FR-6.1..FR-6.3`. | 12-doc | Internal check | Cross-verify FR-5 and FR-6 do not get both group-only and child-specific tags — they are mixed (group, child, group, child). Consider separating. Minor. |
| M6 | The `Idempotency-Key` parameter is a single concrete value `IdempotencyKey` (header) referenced wherever needed. Verified to be declared under `components.parameters.IdempotencyKey`. | openapi.yaml | OK | None. |
| M7 | `PeriodRequest` schema (used by `createPayrollPeriod`) requires `periodId: Uuid` — that is a **write** page that asks for an `id` to be supplied by the caller. Set-the-id-on-create is unusual but consistent with the rest of the contract (Postel-like: "be liberal in what we accept"). | `openapi.yaml` `PeriodRequest.required` `[periodId]` | Minor | If the team wants server-generated IDs, add a note that `periodId` is treated as request assertion and the server may re-key it. Clarification likely needed because the 11-doc suggests server-generated UUIDs as the default. |

---

## 10. What I did NOT do (honest boundary)

- **No subagent dispatched.** Per the user's instruction this report was assembled by direct file reads and Python parsing scripts in `C:\Users\lenovo\AppData\Local\Temp\r*.py` (no installation, no edits).
- **No contract or source edits.** All findings are read-only observations.
- **No OpenSpec CLI re-invocation**, no `git diff --check`, no `python openspec_spec_validator` (per `tech_plan-blueprint-001.md` §"Verification Commands", none of those tools are installed and must not be installed for this change).
- **No runtime tests, no Schemathesis, no Spectral, no Playwright.** Phase A is a planning/contract phase only; I did not run any tools that touch a server, browser, or database.
- **No endpoint-count-as-coverage claim.** I have not asserted that "69 operations = 100% Phase A coverage". The 69 operations are the operationId set; coverage relative to FRs, views, and acceptance tests is something only a layered handbook (per 12-doc §3) can attest.
- **No promise of success.** Phase A review is a bounded reading; the partial files remain unreviewed — the rev-13 task record explicitly says "Phase B/C have NOT started; contract review gate remains closed." This report moves the gate forward one notch only.

---

## 11. Unknowns and clarifications needed (in priority)

1. **Doc-vs-contract surface representation (Finding §2).** Should 12-doc §3 be expanded to list the 27 workflow ops, or keep the high-level table and reference the contract tag count? Default: expand.
2. **`approveFinancialRule` schema misuse (§5).** Should rule-approval capture `evidenceFileId` at all? Default: keep as pointer with no required field except the idempotency key on the parameter side.
3. **`createClientInvoice` source-id misattribution (§6).** Is the user OK with `x-source-ids: []` (extension surface outside 26 FRs) or wants an extension label like `extension:commercial-ar`? Default: empty list with an `x-invariant` note.
4. **`FinancialRuleRequest.bonusRecipientIds` cardinality (§7).** Keep min/max 3 until client decides on dynamic recipients, or open to `[1..N]`? Default: open with a proposed-amendment gate.
5. **Internal job lifecycle (BONUS).** The recovery report and rev-13 both call out "session lifecycle" as a missing contract surface. The YAML has `getJob`, `runSaturdayPayrollJob`, `runMonthlyOverheadJob`, and `JobAccepted` schema. Is a `createJob` / list-equivalent for human-initiated jobs missing on purpose, or should we add `POST /jobs`? Not a blocker; flagging for Phase B attention.

---

## 12. Citations / sources searched

No web search performed; this is a code/spec-level review. The only external reference consulted (one read of PostgreSQL RLS docs was already collapsed into the 11-doc prose rule, so I did not re-fetch). All citations are local files.

| Local file | Read window | Purpose |
|---|---|---|
| `task-record.md` (rev 13) | lines 1–400 read; rev 13 confirmed | Context |
| `09-technical-blueprint-completion-plan.md` | lines 1–300 read | Plan scope |
| `artifacts/tech_plan-blueprint-001.md` | lines 1–400 read | Detailed plan |
| `artifacts/10-technology-stack-and-decisions.md` | lines 1–300 read | Stack ADRs |
| `artifacts/11-database-schema-spec.md` | lines 1–400 read | Schema spec |
| `artifacts/12-api-contract-plan.md` | lines 1–300 read | API plan |
| `artifacts/contracts/openapi.yaml` | 75.6 KB loaded via `yaml.safe_load` | Contract source of truth |
| `04-rbac-matrix.md` (root) | lines 1–200 read | RBAC verbatim |
| `06-acceptance-tests.md` (root) | lines 1–200 read | Acceptance scope (NOT RUN) |
| `08-client-clarification-register.md` (root) | full read | Decision register |
| `artifacts/research/blueprint-phase-a-recovery-002.md` | full read | Prior checkpoint |

**No web fetch, no `mcp_mcp-omnisearc_web_search` invoked.** This is a planning blueprint consistency review, not a research report requiring external facts.

---

## 13. Final summary

- The contract is **structurally valid** (refs resolve, IDs are unique, 69 ops); the doc is **out of date** (42 ops listed; 27 ops in `workflow` tag not enumerated).
- The rev-13 fix list is **partially accounted for**: assembly target for QC ✓ in schema ✗ in example; wage credits per component + 1 bonus per assembly ✓ in invariants/specs; ledger operation-name renamed in contract ✗ in doc; missing surfaces ✓ in contract (assembly/operator/line/sample-conversion/payroll-approval-payment/client-invoice/financial-rule/session) ✗ in doc enumeration; FK/nullability/RLS matrix ✓ in 11-doc §9; deferred ledger balance + late-line insertion protection ✓ in 11-doc §5 prose; operation-name mismatch partially fixed.
- One real contract misunderstanding: `approveFinancialRule` uses `PaymentEvidence` (see §5) — this is an action needed.
- One real authoritarian hardening: `FinancialRuleRequest.bonusRecipientIds` `min/max 3` — closes §3.3 of the register without an authorized user decision (see §7).
- One real wiring mistake: client invoice ops use FR-3.1 (ledger) as `x-source-ids` instead of an empty list / extension label (see §6).
- Five clarifications requested per §11. No implementation or contract edits proposed in this report — Phase A review gate still pending user direction.
