# 06 — Manual acceptance tests (Phase 2B)

**Status:** Specification only; no application exists for execution. Every executable assertion below is **NOT RUN**. Assertions whose expected behavior is not decided by the source are **BLOCKED — decision needed**, not failed tests. English Given/When/Then steps are intended for a human tester using the eventual application, not automated test code. Fixture identifiers, amounts, and rates are **[inferred — illustrative test data]**, never prescribed business values.

**Sources:** [00-deconstruction.md](00-deconstruction.md) revision 4 (authoritative slide transcription, especially slides 04–07 and 09); [BRD v2.3.0](Lukla%20Operations%20Engine%20-%20BRD%20v2.2.1%20-%20FINAL.md) (filename retains v2.2.1; see §§7, 13.3, 16.1, 16.4–16.6); [07-glossary.md](07-glossary.md) for domain terms; [04-rbac-matrix.md](04-rbac-matrix.md) for the eight observed IZIN/PEMBATASAN rows. Where the glossary or BRD elaborates beyond or conflicts with the register, these tests follow the register. FR-2.1 is an **[assumption]** ID because slide 02c is absent; its eight role restrictions are observed on [slide 04]. Slide 07 payroll text comes from a chat attachment, not an on-disk photo.

## Execution protocol

1. Use a disposable environment with inspectable order, material, sewing-output, QC, payroll and history views. Set up the named users, fixtures and rates explicitly before each scenario; do not assume defaults or live customer data. Where the eventual application lacks a named workflow, record **NOT RUN — interface unavailable** rather than inventing one. Capture before/after records and any visible rejection, plus screenshots or exported calculations, with the case ID.
2. Run a case only after its stated prerequisites are met. Record actual result, operator, date and evidence against its ID; change **NOT RUN** to PASS/FAIL only after comparison with the stated expected outcome. A case can have a runnable assertion and a separately BLOCKED assertion; do not fail or waive the runnable part because an unrelated rule is open.
3. Currency is written in Rp. All fixture calculations below use whole Rp and exact integer products unless a case expressly probes a nondivisible pool. Do not assume floor rounding, an extra account, or a payout destination for a remainder. `Pass/Repair/Reject` is the slide-05 wording; slide 04 uses `lolos/reject/repair` and slide 08 uses `lolos/repair/scrap` — no mapping between Reject and scrap is assumed.
4. Roles and permissions are checked against explicit slide-04 restrictions only. An absent IZIN is not a new default grant or a source-backed universal denial. Payroll bonus recipients are people, **not** automatically RBAC roles. FR-6.2 requires rejection of mismatched issuance, but its Gudang/Cutting/both module ownership remains **UNRESOLVED**.

## Closing scenario 1 — reject cross-client material issuance

### AT-01 — Mismatched material is rejected (NOT RUN)

**Maps to:** [slide 09] scenario 1; FR-6.2 [slide 02; slide 09], warehouse restriction [slide 04], mismatch warning [slide 08]; FR-1.1 isolation [slide 02b; slide 03].
**Given** an authorized material-issuance tester, Client A and Client B with distinct `client_id`s, material lot A-01 owned by Client A with 10 units available, and order B-01 owned by Client B; record lot A-01's starting quantity and issue history. The identifiers/quantity and tester account are [inferred — illustrative fixture].
**When** the tester attempts to issue 2 units of A-01 to order B-01 through the available material-issuance workflow.
**Then** the system rejects the issuance, shows a recognizable ID-mismatch warning, and does not create a successful issue or consume the 2 units from A-01; compare the recorded quantity and issue history before and after. Rejection is [slide 09; slide 04]; warning is [slide 08]. Exact message, storage mechanism, logging, and owning module are **not** required by the source.

### AT-02 — Matched-owner control (NOT RUN)

**Maps to:** warehouse permission [slide 04], material flow [slide 04b], FR-6.2 [slide 09]; successful control and exact quantity are [inferred — test setup], not a full FR-5 stock-accounting rule.
**Given** an authorized Gudang/Warehouse user, Client A order A-02 and an independent A-02 material lot owned by Client A with 10 units available; capture its initial balance/issue list.
**When** the user issues 2 units for order A-02 via the same workflow.
**Then** matching IDs must not trigger the cross-client rejection, and the authorized issue can complete; verify the recorded issue references Client A and order A-02. An exact ending stock balance, adjustment procedure, and issue-ledger structure are **BLOCKED — FR-5 detail not in source**, unless agreed separately. This control does not override other validation failures.

## Closing scenario 2 — +5 sewers midweek and Saturday piece-rate payroll

### AT-03 — Dynamic headcount and verified per-sewer wages (NOT RUN)

**Maps to:** [slide 09] scenario 2; FR-7.1/7.3/7.4 [slide 06], FR-10.1 [slide 07 — chat attachment], mandor/penjahit verification [slide 04], weekly payroll workspace [slide 08].
**Given** a test production week ending Saturday; two active sewers S1/S2 on Monday; five more S3–S7 added Thursday (**+5 midweek**, no capacity ceiling inferred from ±70). Assign all seven to one illustrative article/component at an explicitly configured sewing rate of **Rp 2,000 per verified component unit**. Have the mandor enter the following 30-minute sewing output and verify each sewer's records; make the finished units eligible by QC verification before Saturday calculation. This is a compact fixture, not an assertion that each sewer works in only one interval. Use no other eligible output, component rate or wage adjustments in this fixture.

| Sewer | Start | Verified eligible component units | Rate [inferred fixture] | Expected Saturday borongan |
|---|---|---:|---:|---:|
| S1 | Monday | 4 | Rp 2,000 | Rp 8,000 |
| S2 | Monday | 6 | Rp 2,000 | Rp 12,000 |
| S3 | Thursday | 2 | Rp 2,000 | Rp 4,000 |
| S4 | Thursday | 3 | Rp 2,000 | Rp 6,000 |
| S5 | Thursday | 4 | Rp 2,000 | Rp 8,000 |
| S6 | Thursday | 5 | Rp 2,000 | Rp 10,000 |
| S7 | Thursday | 6 | Rp 2,000 | Rp 12,000 |

**When** Finance calculates the Saturday weekly borongan for that week.
**Then** compare every sewer's borongan with the table: 30 eligible units × Rp 2,000 = **Rp 60,000 total**, including the five Thursday starters, without a fixed-slot or restart requirement. Per-sewer verified output × rate and Saturday calculation are [slide 07 — chat attachment]; flexible allocation is [slide 06]. This table tests pure borongan, not combined meal/bonus/overhead pay.

### AT-04 — Verification gates and no premature wage recognition (NOT RUN)

**Maps to:** FR-7.4 [slide 06], FR-10.1 [slide 07 — chat attachment], FR-8.1 [slide 05], production→QC→payroll [slide 04b].
**Given** a separate sewer S8 with 1 recorded component unit at an illustrative Rp 2,000 rate, still unverified by the mandor, and a separate mandor-verified finished unit U8 marked `Menunggu QC` with no QC verification; record pre-run eligible totals.
**When** Finance calculates the Saturday wages before those verifications, then the mandor verifies S8's output and QC records `Pass` on U8 and Finance recalculates in the appropriate test period.
**Then** the unverified output must not enter the calculation [slide 07]; wages for the pending finished unit must not be recognized before QC verification [slide 06]. After both gates, eligible component output contributes once at its configured rate. The exact timing of a late verification crossing a closed payroll period is **BLOCKED — not in source**; keep the second calculation in an open test period.

### AT-05 — Same-sewer repair earns no second credit (NOT RUN)

**Maps to:** FR-8.1/8.2 [slide 05], FR-7.4 [slide 06], FR-10.1 [slide 07 — chat attachment].
**Given** one identified unit R-01 from sewer S1 at a configured illustrative Rp 2,000 component rate with its original mandor-verified output; QC marks R-01 `Repair`. Capture S1's credit count and payroll eligible amount for this unit before rework.
**When** R-01 returns to **S1**, S1 repairs it, the mandor verifies the rework output as applicable, and QC inspects the same R-01 again and records `Pass`.
**Then** the unit returns to its original sewer, its QC path is traceable, and rework does **not** add a second piece-rate credit for S1: at most one Rp 2,000 credit for this fixture's original component/unit, not Rp 4,000. Do not infer how failed/rejected units are compensated beyond the stated verification gate.

## Closing scenario 3 — 3,000 Pass QC units and one shared bonus rule

### AT-06 — Per-piece pool and three equal recipients (NOT RUN)

**Maps to:** [slide 09] scenario 3; FR-9.1/9.2 [slide 05] and FR-10.3 [slide 07 — chat attachment] are **one rule**, not two pools; weekly payout [slide 05].
**Given** exactly **3,000 distinct QC-Pass units** from test orders, each with an explicitly configured illustrative bonus rate of **Rp 7 per piece**; assign Mandor 1, Mandor 2 and Kepala Operasional as the three named recipients. Include no other eligible Pass units in this payroll fixture; identify the three recipients independently of their system RBAC accounts.
**When** Finance calculates the bonus pool and its allocation with weekly payroll.
**Then** the pool is **3,000 × Rp 7 = Rp 21,000**, with **Rp 7,000** attributed to each of the three recipients, once only. Verify 3 × Rp 7,000 = Rp 21,000 and no second pool or payout is created under the second FR ID. Every Pass unit contributes; the pool can include units across clients/orders [slide 07 — chat attachment].

### AT-07 — Non-Pass and duplicate-count boundary (NOT RUN)

**Maps to:** FR-8.1 and FR-9.1 [slide 05]; repeat-submission idempotence is [inferred — test technique] to probe the per-unit rule.
**Given** 2 distinct Pass units, 1 Repair and 1 Reject, all at an illustrative Rp 6 bonus rate; preserve unit identities and their QC histories.
**When** the tester calculates the pool, then repeats the calculation with the same underlying 2 Pass records and no new QC Pass event.
**Then** only the Pass units contribute: **2 × Rp 6 = Rp 12** per calculation; re-running the calculation must not count the same units twice in the payable pool. The exact treatment of a repaired unit that later becomes Pass is **BLOCKED — not explicitly specified for bonus event deduplication**; this case does not assert a new pool event for it.

### AT-08 — Nondivisible pool: quotient known, payout remainder undecided (BLOCKED — decision needed; NOT RUN)

**Maps to:** FR-9.2 [slide 05], FR-10.3 [slide 07 — chat attachment], BRD §13.2/§16.1. **Given** a weekly pool of exactly **Rp 100,000** for the same three recipients. **When** the pool is divided by three. **Then** the mathematical quotient is **Rp 100,000 / 3 = Rp 33,333⅓ per person**. The expected integer-currency payouts and destination of the remaining Rp 1 are **BLOCKED — not in source**. Do not turn this into Rp 33,333 floor payouts, a reserve account, a fourth recipient or a hidden loss rule. A human tester can verify the displayed mathematical quotient once available, but cannot mark the payout assertion PASS/FAIL until the business decides the rule.

## Closing scenario 4 — sample v1 → v2 → Semi-CMT mass order

### AT-09 — Traceable v2 specification history (NOT RUN)

**Maps to:** [slide 09] scenario 4; FR-3.1 [slide 02; slide 03], FR-4.1 [slide 02; slide 03], sample tracker [slide 08], Semi-CMT definition [slide 01], Tim Sample permission/restriction [slide 04].
**Given** Client A's sample v1 with an illustrative sleeve-length specification of 60 cm and its recorded per-component time study; have Tim Sample/Adis record v2 changing sleeve length to 62 cm (illustrative distinct values) and approve that sample version. Prepare a mass order for Client A with scheme **Semi-CMT**: client supplies main fabric, Lukla supplies supporting materials/accessories. Capture the v1 and v2 timestamps/identifiers visible in the available history.
**When** the authorized order workflow creates the mass order using approved sample v2 after any required confirmation and a tester opens the order's linked sample/spec history.
**Then** the order identifies v2, its 62 cm specification remains traceable, and the earlier v1/60 cm specification remains available in revision history rather than being overwritten. The source requires traceable v2 history into the Semi-CMT mass order; it does **not** require automatic rate-card inheritance. Whether rate cards or unspecified spec fields are automatically copied is **BLOCKED — not in source**. Who confirms the mass order and how is **BLOCKED — not in source**; do not treat the Sample role's version approval as that confirmation.

### AT-10 — No mass-order approval by Sample without confirmation (NOT RUN; confirmation mechanics BLOCKED)

**Maps to:** Sample role PEMBATASAN [slide 04]; sample versioning [slide 08]. **Given** approved v2 and a Tim Sample/Adis account, but no mass-order confirmation. **When** that account attempts to approve the associated mass order. **Then** the order must not become approved on that action alone [slide 04]. **BLOCKED — not in source:** confirmer identity, approval sequence, message text and evidence shape. Once a business confirmation procedure is agreed, repeat AT-09 using it.

## Explicit RBAC negative checks — all eight slide-04 PEMBATASAN rows

Run each with the named role's own account and an otherwise valid fixture. Observe the attempted action **and** unchanged protected state; no scenario below grants unlisted permissions. Each check is **NOT RUN**. The role-to-FR-2.1 mapping is [assumption], but the restriction itself is [slide 04]. Compare with [04-rbac-matrix.md](04-rbac-matrix.md), not BRD §11.1 project RACI.

| ID | Given / When (fixture and action) | Then (source-backed expected outcome) | Mapping |
|---|---|---|---|
| AT-R01 | **Given** Owner account and existing **locked** transaction history H1; **When** Owner attempts to modify H1's recorded value. | H1 stays unchanged; Owner cannot change locked transaction history. Whether a separate corrective entry/reversal is permitted is **BLOCKED — [assumption] append-only/reversal mechanism**, not a slide-04 guarantee. | [slide 04] Owner; FR-3.1 [slide 02; slide 03] |
| AT-R02 | **Given** Sample account, a sample-version approval and a mass order lacking confirmation; **When** Sample attempts mass-order approval. | Order remains unapproved from this attempt alone; confirmation actor/mechanics **BLOCKED** (see AT-10). | [slide 04] Sample; FR-4.1 [slide 03] |
| AT-R03 | **Given** Gudang account, Client A material and Client B order; **When** Gudang attempts issue. | Issue rejected; protected material state unchanged (AT-01). Module ownership for FR-6.2 remains unresolved. | [slide 04; slide 09]; FR-6.2 |
| AT-R04 | **Given** Mandor account, a payroll formula and an already final QC result; **When** Mandor attempts to change each in separate attempts. | Neither payroll formula nor final QC result changes. This does not remove Mandor's explicit component rate-card permission. | [slide 04] Mandor; FR-8.1 [slide 05] |
| AT-R05 | **Given** Penjahit account and **mandor-verified** output O1; **When** Penjahit tries to edit O1. | O1 remains unchanged. No claim is made about whether editing an unverified report is permitted. | [slide 04] Penjahit; FR-7.3 [slide 06] |
| AT-R06 | **Given** QC Inspector account, existing borongan rate and Client A order data; **When** QC attempts to change each in separate attempts. | Neither borongan price nor client order data changes. QC inspection and defect-recording IZIN remain intact. | [slide 04] QC; FR-7.2 [slide 06] |
| AT-R07 | **Given** Finance & Payroll account and recorded warehouse physical stock; **When** Finance attempts to change physical stock. | Physical warehouse stock remains unchanged; payroll calculation and PO/invoice IZIN are not revoked. | [slide 04] Finance; FR-5 [slide 03] |
| AT-R08 | **Given** Client A portal account and separate A/B orders, progress and consigned-stock data; **When** A attempts to view B's records through the portal (including an explicit B identifier). | No B record is disclosed; A can still view A's order status, progress and own consigned stock. This tests own-`client_id` boundary, not a blanket restriction on internal roles. | [slide 04; slide 02b] Client; FR-1.1 [slide 03] |

## Additional unresolved assertions (BLOCKED — decisions needed)

- **FR-10.2 meal base:** [slide 07 — chat attachment] says manually enter 10–15% per production period and use total ongkos jahit generated in that period; neither the exact base composition versus ongkos potong nor distribution per sewer is decided. A tester may inspect an explicitly supplied base and percentage as arithmetic, but cannot assert a payroll allocation or redefine the base. Do not add an expected amount to AT-03's pure borongan totals. See register unresolved item 7 and BRD §13.3.
- **FR-6.2 ownership:** [slides 02, 04, 08, 09] require rejection and a warehouse mismatch warning; whether the control is implemented in Gudang, Cutting or both is **BLOCKED**, not an extra AT-01 outcome. FR-5 stock transactions and FR-6 cutting batch/wastage detail are likewise not specified.
- **History mechanism and rate governance:** locked-history immutability for Owner [slide 04] is testable in AT-R01; universal append-only ledger and compensating reversal are **[assumption]/[inferred BRD planning]**, not required by that test. [slide 04] names both Owner rate changes and Mandor component-rate determination, while [slide 06] says Owner manages rate cards; precedence and approval are **BLOCKED**.
- **Other source gaps:** FR-1.4 exact meaning, missing slide 02c and slide 07 original photo, bonus recipient-count configurability, QC `Reject`/`scrap` mapping, and placement of `Menunggu QC` on slide 04b versus slide 06 remain undecided; do not manufacture expected outcomes from them. ±70 machines is scale context, not a cap.

**Execution ledger:** AT-01–AT-07, AT-09–AT-10 and AT-R01–AT-R08: **NOT RUN (no application)**; AT-08 payout and the explicitly labeled dependent assertions: **BLOCKED — decision needed; NOT RUN**. No runtime acceptance result is claimed here.