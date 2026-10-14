# Research-002: Evidence Map for `04-rbac-matrix.md` and `06-acceptance-tests.md`

**Change:** `lukla-ops-engine-planning`
**Date:** 2026-10-13
**Executor:** Explorer (read-only). No source artifacts modified.
**Scope strictness:** Evidence map only — no design choices, no role
invention, no rule fabrication.

---

## 0. Context confirmation

| Item | Value | Verified by |
|---|---|---|
| Active change | `lukla-ops-engine-planning` | `openspec/changes/lukla-ops-engine-planning/.openspec.yaml` (file inventory `Get-ChildItem … -Name`, `$PWD = C:\Projects\hackathon-MAIN-alkademi`) |
| Task record revision | **7** | `task-record.md` line 3: `**Revision:** 7`, line 5: `**Updated:** 2026-10-12`; rev 7 entry on line 30-31 documents "Phase 0-R COMPLETE", "NEXT: Phase 1-A (BRD audit against register rev 4)" |
| Approved recovery plan | `artifacts/docs-conversion-plan-v2-pickup.md` | `task-record.md` rev-6 entry names it; plan file exists and is referenced as authoritative for Phase 1-A / Phase 2 by `impl-001.md`, `impl-002.md`, and `worklog.md` |
| Phase 1-A state | **COMPLETE** (Phase 2 next) | `impl-002.md` "Required verification outputs" section; `worklog.md` "2026-10-12 — Phase 1-A: BRD audit and repair" entry; BRD bumped to **v2.3.0** (BRD file `LastWriteTime = 13/10/2026 04:54:08`, length 36256) |
| Phase 2 deliverables | **Not yet created** | `Test-Path '…\artifacts\04-rbac-matrix.md'` = `False`; `Test-Path '…\artifacts\06-acceptance-tests.md'` = `False` |
| Authoritative comparison source | `00-deconstruction.md` revision 4 (`LastWriteTime = 13/10/2026 04:54:14`, length 42826, 362 lines) | Header line 6: `**Revision:** 4 (2026-10-12) — Phase 0-R` |

Environment fingerprint: Windows, PowerShell (`pwsh`), repo root `c:\Projects\hackathon-MAIN-alkademi`, openspec CLI 1.6.0, date 2026-10-13.

---

## 1. Provenance policy for this evidence map

Every claim below carries exactly one of:

- **`[slide XX]`** — verbatim or near-verbatim text from a slide 00/01/02/02b/03/04/04b/05/06/08/09 register transcription (slides confirmed on disk; primary source = PDF renders for 02/02b/05/06, photos for the rest).
- **`[slide 07 — chat attachment]`** — verbatim text from the orchestrator's chat-attachment transcription; no on-disk photo of slide 07 exists.
- **`[assumption]`** — content not on any on-disk slide but logically implied (e.g. FR-2.1 RBAC concept exists at the ID-badge level only).
- **`[inferred]`** — content stated nowhere; recorded as `UNRESOLVED - not in source`, or referenced as BRD-side planning detail (e.g. SCRUM/sprint structure, double-entry ledger) that was adopted by user decision.
- **`UNRESOLVED - not in source`** — content the deck names but never specifies; recorded in the register's UNRESOLVED list (lines 454–461) and in the BRD gaps section.

**Known traps (re-stated for the writing phase):**

1. Do not invent permissions for roles. Only the IZIN/PEMBATASAN cells in slide 04 are valid source.
2. Do not turn BRD-only rules into source truth. The BRD's §11.1 RACI table lists **project-delivery roles** (Executive Sponsor / Lead Solution Architect / Lead Software Engineer / Warehouse & Cutting Supervisor / QC Lead) — these are **NOT** the 8 RBAC system roles. They are governance accountabilities, not the RBAC matrix.
3. Do not decide: bonus-pool ÷3 remainder allocation (open question, register UNRESOLVED #6); uang makan base definition vs. ongkos potong (open question, register UNRESOLVED #7); module ownership of FR-6.2 (recorded ambiguity).
4. Do not invent rows in 04-rbac-matrix.md. Slide 04 lists **exactly 8** user-role rows. Project-delivery roles (BRD §11.1) are not RBAC roles and must not be added.

---

## 2. Evidence map: 8 RBAC roles with verbatim IZIN / PEMBATASAN

**Primary source:** `00-deconstruction.md` Slide 04 section — lines **192–230**.
**On-disk photo:** `WhatsApp Image 2026-10-12 at 10.40.55c.jpeg` (mapped at register line 32; photo is legible, all cells transcribed, register line 194).
**Current BRD coverage:** BRD §11.1 (lines 245–254) is a project-delivery RACI matrix — not the system RBAC matrix. **BRD has zero occurrences of the column header `IZIN` and zero occurrences of `PEMBATASAN`** (`Select-String -Pattern 'IZIN' | Measure-Object` count = 0; `PEMBATASAN` count = 3, all in lower-case Indonesian `pembatasan` prose, not as the column header). AC-3 from the pickup plan (`All 8 roles with IZIN and PEMBATASAN in 04-rbac-matrix.md`) is therefore unmet and is exactly what `04-rbac-matrix.md` must deliver.

**Table-format requirement (register line 200):** header row is **`PERAN | IZIN | PEMBATASAN`**. Subgroup labels in parentheses are part of the printed badge (e.g. `(Internal)`, `(Stok)`, `(B2B Portal)`).

| # | Peran | IZIN (verbatim, register lines 204–211) | PEMBATASAN (verbatim, register lines 204–211) | Source |
|---|---|---|---|---|
| 1 | **Owner/Eksekutif** (Internal) | "Analitik tinggi & konfigurasi sistem; Ubah rate card" | "Tidak dapat mengubah histori transaksi yang dikunci" | `[slide 04]` (line 204) |
| 2 | **Tim Sample/Adis** (Sample) | "Catat pemakaian bahan sample; Input time study per komponen; Setujui versi sample" | "Tidak dapat menyetujui pesanan massal tanpa konfirmasi" | `[slide 04]` (line 205) |
| 3 | **Gudang/Warehouse** (Stok) | "Terima bahan + titipan klien; Keluarkan bahan ke cutting; Stok opname" | "Dilarang mengeluarkan bahan jika ID Klien/Pesanan tidak cocok" | `[slide 04]` (line 206) |
| 4 | **Kepala Produksi/Mandor** (Line) | "Atur line + alokasi penjahit; Tentukan rate card komponen; Catat output 30 menit" | "Tidak dapat mengubah formula penggajian atau hasil QC final" | `[slide 04]` (line 207) |
| 5 | **Penjahit/Tailor** (Operator) | "Lihat tugas komponen; Laporkan hasil kerja (diverifikasi mandor)" | "Tidak dapat mengedit catatan output yang sudah diverifikasi" | `[slide 04]` (line 208) |
| 6 | **QC Inspector** (Quality) | "Periksa barang jadi; Set status lolos/reject/repair; Catat jenis cacat" | "Tidak dapat mengubah harga borongan atau data order klien" | `[slide 04]` (line 209) |
| 7 | **Finance & Payroll** (Finance) | "Buat/setujui PO bahan; Terbitkan invoice; Hitung gaji mingguan & bulanan" | "Tidak dapat mengubah fisik stok di gudang" | `[slide 04]` (line 210) |
| 8 | **Klien Maklon/Ext** (B2B Portal) | "Pantau status pesanan; Lihat progres real-time; Lihat stok bahan titipan sendiri" | "Terbatas hanya pada data client_id milik sendiri" | `[slide 04]` (line 211) |

**Recorded source-rationale rules (register lines 218–226; map to capability/control rows in `04-rbac-matrix.md`):**

| Rule (verbatim register extraction) | Where it goes in 04-rbac-matrix.md | Source |
|---|---|---|
| "RBAC matrix has exactly 8 roles with explicit IZIN (permissions) and PEMBATASAN (restrictions) columns." | Cross-cutting header note | `[slide 04]` (line 219) |
| "Locked-history rule: not even the Owner can change locked transaction history." | Row 1 + binding rule | `[slide 04]` (line 220) |
| "Warehouse issuance guardrail: material may not be issued when ID Klien/Pesanan does not match — this is the RBAC-side statement of the cross-client contamination control (see FR-6.2 ambiguity note)." | Row 3 + control FR-6.2 cross-link | `[slide 04]` (line 221); FR-6.2 module-ownership ambiguity carried in register Contradictions (line 466) |
| "Output records become immutable once verified: penjahit cannot edit verified output; mandor verifies penjahit reports." | Rows 4 & 5 + immutability rule | `[slide 04]` (line 222) |
| "Separation of duties: Finance cannot change physical stock; Gudang cannot issue mismatched material; QC cannot change borongan prices or client order data; Kepala Produksi/Mandor cannot change payroll formulas or final QC results." | Rows 3, 4, 6, 7 SoD rule | `[slide 04]` (line 223) |
| "Client portal isolation: external clients see only their own `client_id` data." | Row 8 + tenant boundary rule (cross-link FR-1.1, FR-6.2) | `[slide 04]` (line 224) |
| "Payroll cadence signal: Finance 'Hitung gaji mingguan & bulanan' (weekly AND monthly payroll computation)." | Row 7 cadence constraint + FR-10.x cross-link | `[slide 04]` (line 225) |
| "Rate card governance: Owner can 'Ubah rate card'; Kepala Produksi/Mandor can 'Tentukan rate card komponen'." | Rows 1 & 4 + FR-7.2 cross-link | `[slide 04]` (line 226) |

**Provenance / cross-link anchors for `04-rbac-matrix.md`:**

- BRD §3.1 RBAC rule (line 93, "Matriks Tata Kelola & Kontrol Akses (RBAC): Penegakan hak akses dan pembatasan operasional pada 8 peran pengguna") — exists in §3.1 prose only; cross-link target for `04-rbac-matrix.md`.
- BRD §11.1 RACI table (lines 245–252) is **project-delivery roles**, not the system RBAC. The 8 system RBAC roles appear elsewhere in BRD only as side-references inside FR bullets (e.g. line 162 FR-2.1 description "pembatasan mutlak antara pencatatan operasional dan penyesuaian finansial"; line 196 FR-10.3 names "Mandor 1, Mandor 2, dan Kepala Operasional" — these are the 3 ÷3 pool recipients, not the 8 RBAC rows).

**Terminology variance record (MUST appear in `04-rbac-matrix.md` so the writer does not "decide" it later):** the QC status wording on the matrix's row 6 reads `lolos/reject/repair` (register line 209), slide 05 FR-8.1 badges use English `Pass/Repair/Reject` (register line 273), slide 08 view 05 uses `lolos/repair/scrap` (register line 360). Three wordings for the same status set — carry as a variance row, not a contradiction (register lines 463, 469-470).

**FR-2.1 sourcing caveat for header note:** Row reference "(8-role matrix on slide 04)" is `[slide 04]` fact, but **FR-2.1 the ID itself remains `[assumption]`** because slide 02c is unavailable (register lines 153–159, line 416, UNRESOLVED #1 line 454). This is a header-note caveat, not a row-level claim.

---

## 3. Evidence map: 4 acceptance scenarios on slide 09 (verbatim text and exercised FRs)

**Primary source:** `00-deconstruction.md` Slide 09 section — lines **380–408**.

The four scenarios are **acceptance tests, not feature descriptions** (register line 392). The current BRD (`Lukla Operations Engine - BRD v2.2.1 - FINAL.md` now v2.3.0 after Phase 1-A) has a **text-only** summary in §16.4 (lines 398–403, near-verbatim translation of slide 09) and three AC stubs in §16.6 (lines 409-415). `06-acceptance-tests.md` must expand these into given/when/then + negative-path + boundary cases per scenario.

| # | Scenario title (verbatim) | Verbatim scenario statement | Exercised FRs (register lines 393–397) | Where it must go in 06-acceptance-tests.md |
|---|---|---|---|---|
| 1 | **Penolakan Kontaminasi Silang** | "Sistem menolak pengeluaran bahan milik Klien A untuk order Klien B." (register line 388) | FR-6.2 (cross-client contamination guardrail) `[slide 09]`, guardrail corroborated `[slide 04]` row 3 restriction + `[slide 08]` view 03 warning | Negative path test (`Sistem HARUS reject …`) |
| 2 | **Payroll Headcount Dinamis** | "Penambahan +5 penjahit di tengah minggu berjalan. Perhitungan payroll tetap benar." (register line 389) | FR-7.1 (Alokasi Kapasitas Dinamis) `[slide 09]`; FR-10.1 (weekly Saturday payroll) `[slide 09]` | Boundary / mid-week-add test |
| 3 | **Bonus Pool QC 3000 Unit** | "Output 3000 unit lolos QC. Bonus pool dihitung dan dibagi 3: 2 mandor + 1 kepala operasional." (register line 390) | FR-9.1 (per-unit Pass → pool) `[slide 09]`; FR-9.2 (÷3 split) `[slide 09]`; corroborated FR-10.3 `[slide 07 — chat attachment]` | Numerical correctness test (3000 × rate = pool; pool ÷ 3 = share per recipient) |
| 4 | **Revisi Sample v1 → v2 ke Order Massal** | "Sample direvisi dari v1 ke v2, lalu menjadi order massal skema Semi-CMT. Riwayat spesifikasi v2 terlacak." (register line 391) | FR-3.1 (audit trail) `[slide 09]`; FR-4.1 (sample versioning) `[slide 09]` | Traceability / history-test |

**Key text variables for `06-acceptance-tests.md` test data** (register Slide 09 extraction lines 393–397):

- Numerical anchor: **+5 penjahit** (mid-week add — scenario 2)
- Numerical anchor: **3000 unit** (scenario 3)
- Split constant: **÷3** = 2 mandor + 1 kepala operasional (slide 05 line 278 / slide 09 line 390 / slide 07 — chat attachment)
- Schema anchor: **v1 → v2** sample revision carries spec history into **Semi-CMT** mass order (scenario 4)

**Mapping to current BRD AC stubs (BRD §16.6 lines 411–415):** three ACs already exist but **scenario 1 has no AC in §16.6** (BRD AC-FR-6.2 covers the negative-path in law but is exercised only against the cutting module in the AC stub; scenario 4 has no AC either). `06-acceptance-tests.md` is required to fill these gaps with executable tests. Scenario 2 has an implicit AC inside §16.4 scenario-2 prose (line 401) but no formal Given/When/Then.

---

## 4. Evidence map: required negative-path and boundary tests

### 4.1 Required NEGATIVE tests (must appear in `06-acceptance-tests.md`)

| ID | Negative-path requirement | Source-backed evidence |
|---|---|---|
| **NEG-CONTAM-1** | Sistem **menolak** issuance of Client A's material for Client B order. | `[slide 09]` scenario 1 (register line 388) + FR-6.2 `[slide 02, slide 09]` (register line 421) + warehouse row 3 PEMBATASAN "Dilarang mengeluarkan bahan jika ID Klien/Pesanan tidak cocok" (register line 206) + view 03 "peringatan ketidakcocokan ID Klien" (register line 358). BRD §16.4 scenario 1 prose enforces the same (BRD line 400). BRD AC-FR-6.2 line 413 already encoded as a negative path with the exact error string. |
| **NEG-RBAC-PORTAL-ISOLATION** | Klien Maklon/Ext attempting to read another client's `client_id` data is denied. | `[slide 04]` row 8 PEMBATASAN "Terbatas hanya pada data client_id milik sendiri" (register line 211, 224). |
| **NEG-RBAC-LOCKED-HISTORY** | Even Owner cannot UPDATE/DELETE a locked transaction. | `[slide 04]` row 1 PEMBATASAN "Tidak dapat mengubah histori transaksi yang dikunci" (register line 204, 220). |
| **NEG-RBAC-OUTPUT-FROZEN** | Penjahit cannot UPDATE a verified output record after mandor verification. | `[slide 04]` row 5 PEMBATASAN "Tidak dapat mengedit catatan output yang sudah diverifikasi" (register line 208, 222). |
| **NEG-RBAC-FINANCE-NO-STOCK** | Finance & Payroll cannot mutate physical warehouse stock. | `[slide 04]` row 7 PEMBATASAN "Tidak dapat mengubah fisik stok di gudang" (register line 210, 223). |
| **NEG-QC-NO-BORONGAN-EDIT** | QC Inspector cannot mutate borongan price or client order data. | `[slide 04]` row 6 PEMBATASAN "Tidak dapat mengubah harga borongan atau data order klien" (register line 209). |
| **NEG-PAYROLL-NO-CREDIT-ON-REPAIR** | Re-QC of a Repair unit by the same penjahit does NOT add a fresh borongan credit. | FR-8.2 "Repair tanpa Gaji Ganda" `[slide 05]` (register line 274, 427). BRD AC-FR-8.2 (line 414) is a negative path test. |
| **NEG-MASS-ORDER-WITHOUT-CONFIRM** | Tim Sample/Adis cannot promote a sample revision to a **mass order** without confirmation. | `[slide 04]` row 2 PEMBATASAN "Tidak dapat menyetujui pesanan massal tanpa konfirmasi" (register line 205). |

### 4.2 Required BOUNDARY tests

| ID | Boundary condition | Source-backed evidence |
|---|---|---|
| **BND-PAYROLL-MIDWEEK-HEADCOUNT** | Payroll must remain correct after +5 penjahit added on Thursday (mid-week add). | `[slide 09]` scenario 2 (register line 389) + FR-7.1 dynamic allocation `[slide 06]` (register line 422) + FR-10.1 weekly Saturday + "Tidak ada batasan jumlah penjahit" `[slide 07 — chat attachment]` (register line 337). |
| **BND-PAYROLL-NO-SEWER-LIMIT** | Payroll computation must not impose an upper bound on sewer count. | FR-10.1 "[Tidak ada batasan jumlah penjahit yang dapat diproses]" `[slide 07 — chat attachment]` (register line 337, 430). |
| **BND-BONUS-POOL-3000** | Bonus pool correctness at exactly 3000 QC-Pass units, ÷3 split. | `[slide 09]` scenario 3 (register line 390) + FR-9.1 / FR-9.2 `[slide 05]` (register lines 276, 277, 428, 429) + FR-10.3 pool formula `[slide 07 — chat attachment]` (register line 338, 432). |
| **BND-BONUS-POOL-CROSS-CLIENT** | Bonus pool accumulates across orders AND across clients (NOT per-client). | FR-10.3 "Pool akumulatif lintas order dan lintas klien" `[slide 07 — chat attachment]` (register line 338). |
| **BND-UANG-MAKAN-RANGE** | Uang makan percentage entered manually each period, bounded by 10–15%. | FR-10.2 `[slide 07 — chat attachment]` (register line 337, 431); **base definition is `UNRESOLVED - not in source`** so the boundary test should assert what is on the slide, not extend to bases. |
| **BND-OVERHEAD-MONTHLY** | Overhead per-unit = (∑ electricity + water + internet + factory operations for the month) ÷ (∑ all units produced that month). | FR-10.4 `[slide 07 — chat attachment]` (register line 338, 433). |
| **BND-SAMPLE-SPEC-INHERITANCE** | Sample v2 spec history must carry into a Semi-CMT mass order; no spec re-entry allowed. | `[slide 09]` scenario 4 (register line 391) + FR-3.1 (audit trail) and FR-4.1 (sample versioning) (register lines 417, 418). |
| **BND-LINE-CAPACITY-DYNAMIC** | Adding/removing active sewers must rearrange line allocation without rigid slot caps. | FR-7.1 "Tidak ada slot kaku" `[slide 06]` (register line 422) + scale context ±70 mesin (NOT a cap) register lines 297, 320. |

### 4.3 Tests that REQUIRE explicit UNRESOLVED / open-question handling in the report (not invented assertions)

| Test idea (do NOT silently decide) | Why it cannot be written without an open question | Source of the unresolved gap |
|---|---|---|
| Assertions on bonus-pool remainder allocation (e.g. what to do with Rp 1 leftover when pool isn't divisible by 3) | "Bonus pool ÷3 configurability" — UNRESOLVED (`register line 459, BRD line 338`). Register explicitly says "open question, do not decide". | register UNRESOLVED #6 (line 459); BRD line 338 echoes the open question. |
| Assertions on uang makan base (e.g. does ongkos jahit include ongkos potong? what fraction?) | "Uang makan base definition" — UNRESOLVED (`register line 460`). Ongkos potong appears on no slide (glossary line 18: "ongkos potong listed for domain completeness only" `[inferred]`). | register UNRESOLVED #7 (line 460); glossary line 18. |
| Assertions that FR-6.2 enforcement lives in the Hub Gudang vs. the Cutting module specifically | "FR-6.2 module/behavior tension (recorded, NOT resolved)" (`register line 466`). | register Contradictions #1 (line 466). |
| Negative-path tests against any `[inferred]` BRD rule | Some BRD rules are tagged `[inferred]`/`[assumption]` (sprint plan, accounting impact, DB-trigger logic) — tests should NOT silently widen assertion scope. | BRD §12 sprint plan, §16.2 DB triggers, §9 financial impact; `impl-002.md` documents these as `[inferred]`/`[assumption]` planning detail. |
| FR-1.4 boundary test | "FR-1.4 exact wording — UNRESOLVED" (`register line 458`). Badge is visible (slide 03 Fase 1) but definition text is nowhere. | register UNRESOLVED #5 (line 458). |

---

## 5. Searches, conflicts, unknowns, environment fingerprint

### 5.1 Searches performed (action evidence)

| # | Search | Command (PowerShell on Windows, pwsh) | Output / count |
|---|---|---|---|
| S1 | List change directory files | `Get-ChildItem -Path openspec/changes/lukla-ops-engine-planning -Recurse -Name` | 22 paths; 19 in `artifacts/`, 3 in `DEPRECATED/` |
| S2 | Register slide-section line numbers | `Select-String -Path 00-deconstruction.md -Pattern '^## Slide 0[2-9]\|^## Master FR inventory\|^## Skipped FR numbers\|^## UNRESOLVED\|^## Contradictions'` | Slide 02:94, 02b:121, 02c:149, 03:164, 04:192, 04b:234, 05:266, 06:296, 07:327, 08:349, 09:380, Master:410, Skipped:437, UNRESOLVED:450, Contradictions:463 |
| S3 | `[slide 04]` tag count in register | `Select-String` count | 21 |
| S4 | `[slide 08]` tag count in register | `Select-String` count | 22 |
| S5 | `[slide 09]` tag count in register | `Select-String` count | 18 |
| S6 | BRD contains column-header `IZIN` | `Select-String -Pattern 'IZIN'` (case-sensitive=false) | **0** matches |
| S7 | BRD contains `PEMBATASAN` | `Select-String -Pattern 'PEMBATASAN'` (case-sensitive=false) | **3** matches — lines 85, 93, 162. **All three are Indonesian `pembatasan` (lowercase) prose**, none is the slide-04 column header. **Confirmed: BRD does NOT carry the slide-04 IZIN/PEMBATASAN matrix.** |
| S8 | BRD `Skenario`/`Scenario`/`AC-`/`Headcount`/`Kontaminasi`/`Bonus`/`Revisi`/`3000` | `Select-String` w/ alternation | BRD line 398 (§16.4 heading), lines 400-403 (4 scenarios), line 411 (§16.6 heading), lines 413-415 (3 ACs) |
| S9 | BRD size + line count | `Get-Content … \| Measure-Object -Line` | 286 lines (Phase 1-A removed an embedded base64 mermaid image; current state verified). |
| S10 | Existence checks for Phase-2 deliverables | `Test-Path '…\04-rbac-matrix.md'`, `Test-Path '…\06-acceptance-tests.md'` | **False / False** (neither file exists; Phase 2 has not started). |
| S11 | File metadata fingerprint | `Get-Item … \| Select-Object LastWriteTime, Length` | `LastWriteTime 13/10/2026 04:54` for register, BRD, plan, task-record (all touched in recovery session Phase 0-R/1-A on 2026-10-12, then committed). |

### 5.2 Conflicts surfaced and **left UNRESOLVED in this report** (carried from the register)

| # | Construct | Slides involved | Register location | Writer's action in `04-rbac-matrix.md` and `06-acceptance-tests.md` |
|---|---|---|---|---|
| C-A | QC status wording varies | `[slide 04]` row 6: `lolos/reject/repair`; `[slide 05]` badges: `Pass/Repair/Reject`; `[slide 08]` view 05: `lolos/repair/scrap` | Line 230; Contradictions line 469 | Record as a "terminology variance row" in the row-6 column header; do **not** choose which is canonical. |
| C-B | `Menunggu QC` position | `[slide 04b]`: arrow QC→Payroll; `[slide 06]` FR-7.4: assembly output enters status pre-QC | Line 248; Contradictions lines 470-471 | Carry as a state-diagram note in `04-rbac-matrix.md` SoD/QoQ section; do **not** collapse the variance. |
| C-C | FR-7.3 / FR-7.4 granularity | Earlier revisions: per-komponen vs per-penjahahit; rev 4 reading: `per penjahit/komponen` (both) | Line 247; resolved in register rev 4 (line 311) — **RESOLVED** (recorded for transparency) | No action needed in `06-acceptance-tests.md`. |
| C-D | FR-6.2 module ownership — Cutting vs Gudang | `[slide 03]`: numbered under FR-6 (Cutting); `[slide 04]` row 3 restriction: Gudang; `[slide 08]` view 03 warning: Gudang; `[slide 02]` card: no owning module named; `[slide 09]` scenario 1: who enforces? | Lines 466-468 (Contradictions #1); recorded as **NOT RESOLVED** | In `04-rbac-matrix.md`, tag the row-3 PEMBATASAN with `[module-ownership UNRESOLVED — Cutting-or-Gudang]`. In `06-acceptance-tests.md` NEG-CONTAM-1, write the negative-path test without assigning module ownership. |
| C-E | FR-9.2 vs FR-10.3 = same rule, two IDs | `[slide 05]` FR-9.2 and `[slide 07 — chat attachment]` FR-10.3 describe the same ÷3 split | Line 472 ("Ambiguity (not contradiction)") | Reference both IDs in the FR cross-link row but do **not** treat as two separate rules. |
| C-F | Bonus remainder allocation / configurability | UNRESOLVED #6 (register line 459) | n/a | In `06-acceptance-tests.md` scenario 3, write the test with `pool ÷ 3` only; do **not** assert integer-floor, round-up, or remainder account allocation. |
| C-G | Uang makan base | UNRESOLVED #7 (register line 460) | n/a | In `06-acceptance-tests.md` boundary test BND-UANG-MAKAN-RANGE, write only that 10–15% is configurable per period (FR-10.2) — do **not** extend to the base. |

### 5.3 Open questions (must NOT be silently resolved)

| ID | Question | Source | Suggested writer action |
|---|---|---|---|
| OQ-1 | Where does FR-6.2 enforcement code live — Cutting, Gudang, or both? | Register Contradictions #1 (line 466) | Tag `04-rbac-matrix.md` row 3 + write `06-acceptance-tests.md` NEG-CONTAM-1 without module assignment; escalate later if user wants it decided. |
| OQ-2 | What is the bonus pool remainder allocation when pool is not divisible by 3? | Register UNRESOLVED #6 (line 459); BRD lines 338, 402, 415 echo the open question. | Scenario-3 test asserts plain ÷3 split only. |
| OQ-3 | What is uang makan's base (does it include ongkos potong? what split?) | Register UNRESOLVED #7 (line 460); glossary `ongkos potong` row 18. | BND-UANG-MAKEN-RANGE asserts 10–15% only. |
| OQ-4 | FR-1.4 wording | Register UNRESOLVED #5 (line 458). | Do not write a boundary test against FR-1.4; it has no definition. |
| OQ-5 | Slide 02c has no on-disk photo — FR-2.1 ID remains `[assumption]` | Register slide 02c (lines 149–159); UNRESOLVED #1 (line 454) | In `04-rbac-matrix.md` header, note that the 8 rows are sourced from slide 04 verbatim, but the FR-2.1 ID that points AT the matrix is itself `[assumption]`. |
| OQ-6 | Slide 07 has no on-disk photo — FR-10.1–10.4 wording is `[slide 07 — chat attachment]` | Register slide 07 (lines 327–348); UNRESOLVED #2 (line 455) | In `06-acceptance-tests.md` scenarios 2 and 3 and the boundary tests, mark FR-10.x inputs with provenance `[slide 07 — chat attachment]` (NOT `slide 07`). |

### 5.4 Environment fingerprint

- **OS:** Windows.
- **Shell:** PowerShell (`pwsh`). Reproduction commands above use `Select-String`, `Get-Item`, `Get-Content`, `Test-Path`, `Get-ChildItem`. All commands are shell-language-only and reproducible.
- **Repo root:** `c:\Projects\hackathon-MAIN-alkademi`.
- **Date:** 2026-10-13.
- **Files inspected (read-only, no edits):**
  - `openspec/changes/lukla-ops-engine-planning/artifacts/00-deconstruction.md` (revision 4, 362 lines, last write 13/10/2026 04:54:14, 42826 bytes)
  - `openspec/changes/lukla-ops-engine-planning/artifacts/07-glossary.md` (revision 3, 12584 bytes, last write 12/10/2026 12:23:05)
  - `openspec/changes/lukla-ops-engine-planning/artifacts/Lukla Operations Engine - BRD v2.2.1 - FINAL.md` (BRD v2.3.0 after Phase 1-A, 286 lines, 36256 bytes, last write 13/10/2026 04:54:08). Note: filename still reads "v2.2.1"; per task-record.md rev 7 and impl-002.md the document content was bumped to v2.3.0 inside the file.
  - `openspec/changes/lukla-ops-engine-planning/artifacts/docs-conversion-plan-v2-pickup.md` (revision 1, 12749 bytes, last write 13/10/2026 04:54:10)
  - `openspec/changes/lukla-ops-engine-planning/artifacts/task-record.md` (revision 7, 9044 bytes, last write 13/10/2026 04:54:12)
  - `openspec/changes/lukla-ops-engine-planning/artifacts/impl-001.md` (Phase 0-R impl report)
  - `openspec/changes/lukla-ops-engine-planning/artifacts/impl-002.md` (Phase 1-A impl report)
  - `openspec/changes/lukla-ops-engine-planning/artifacts/worklog.md` (Phases 0-R + 1-A entries)
- **Files confirmed non-existent (Test-Path=False):**
  - `openspec/changes/lukla-ops-engine-planning/artifacts/04-rbac-matrix.md`
  - `openspec/changes/lukla-ops-engine-planning/artifacts/06-acceptance-tests.md`

### 5.5 Completion-claim integrity

This report does NOT claim Phase 2 is complete. It is an evidence map only. Phase 2 deliverables (`04-rbac-matrix.md`, `06-acceptance-tests.md`) were confirmed non-existent by `Test-Path` (False on both, S10). No source content was modified; only this file was created (`research-002.md` itself) in accordance with the explicit exception in the Explorer-mode instructions.

---

## 6. Concise cross-reference sheet for the writing phase (one-screen summary)

**`04-rbac-matrix.md` MUST include:**

- Header: provenance `[slide 04]` for the table body; FR-2.1 ID itself is `[assumption]` (slide 02c missing, register lines 153-159, 416, 454).
- 8 rows × IZIN/PEMBATASAN transcribed from register lines 204-211 (verbatim).
- 8 capability / control rows mapped from register lines 218-226 (locked history, +5 mid-week, warehouse guardrail, immutability, SoD, portal isolation, payroll cadence, rate-card governance).
- Cross-link anchors: BRD §3.1 (line 93), BRD §11.1 RACI table **must NOT be confused** with the 8 RBAC rows (BRD lines 245-252), FR-1.1 (multi-tenant), FR-2.1 (RBAC, `[assumption]`), FR-6.2 (cross-client control, module-ownership UNRESOLVED), FR-7.2 (rate card), FR-10.x (payroll cadence).
- Terminology-variance note: QC status wording shown three ways across `[slide 04]`, `[slide 05]`, `[slide 08]`.
- FR-6.2 module-ownership open-question marker (do **not** decide).

**`06-acceptance-tests.md` MUST include:**

- Four executable tests, one per slide-09 scenario (register lines 388-391), each as Given-When-Then with the verbatim facts involved (Klien A → Klien B order; +5 penjahit Thursday add; 3000 units Pass QC; sample v1→v2 → Semi-CMT order).
- 8 negative tests (table §4.1 above) — covering each row of slide-04 PEMBATASAN that is enforceable.
- 8 boundary tests (table §4.2 above) — including 3000-unit pool, ±70 scale context, mid-week headcount, uang makan 10–15% range, overhead ÷ monthly Σ units, cross-client pool accumulation.
- Open-question explicit markers: bonus-pool remainder (UNRESOLVED #6), uang makan base (UNRESOLVED #7), FR-6.2 module ownership (Contradictions #1), FR-1.4 wording (UNRESOLVED #5).
- Provenance tags for everything: `[slide 04]`, `[slide 05]`, `[slide 06]`, `[slide 07 — chat attachment]`, `[slide 08]`, `[slide 09]`, plus register line references.

---

## 7. End of report
