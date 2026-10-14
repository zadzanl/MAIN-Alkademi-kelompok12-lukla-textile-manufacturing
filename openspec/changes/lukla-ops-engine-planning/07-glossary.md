# 07 — Domain Glossary (Indonesian ↔ English)

**Change:** `lukla-ops-engine-planning`
**Date:** 2026-10-12
**Revision:** 3 (2026-10-12) — payroll formulas re-anchored to `[slide 07 — chat attachment]`; other source mappings remain as in revision 2.
**Purpose:** Working glossary for the Lukla Operations Engine document suite. Indonesian domain terms are kept untranslated in the English documents; this table is their definition of record. Definitions are scoped to *this system's* context as deconstructed in `00-deconstruction.md` — they are not general dictionary entries.

| Indonesian term | Literal English | Working definition in this system's context |
|---|---|---|
| maklon | toll manufacturing / contract manufacturing | B2B arrangement where a client outsources garment production to Lukla; every order runs under exactly one of three maklon schemes (CMT / Semi-CMT / Full Package) that fix who supplies raw material `[slide 01]` |
| CMT (Cut, Make, Trim) | Cut, Make, Trim | Maklon scheme: client supplies ALL raw materials; Lukla supplies cutting, sewing, and finishing labor only `[slide 01]` |
| Semi-CMT | Semi-CMT | Maklon scheme: client supplies main material; Lukla supplies supporting materials and accessories `[slide 01]` |
| Full Package (CMT + Bahan) | Full Package (CMT + Materials) | Maklon scheme: Lukla supplies all raw materials and production service; also used for internal Snøhund brand orders `[slide 01]` |
| konveksi | convection (garment industry sense) | Small/mid-scale garment production business — Lukla's factory type `[slide 00]`, located in Ciwidey `[slide 01]`; scale context ±70 sewing machines `[slide 01]`, `[slide 06]` |
| borongan | piece-rate / lump-sum piecework | Pay model where sewers are paid per output unit, not per hour; manual borongan payroll is a named pain point `[slide 02]`; "gaji borongan mingguan" (weekly) computed in the payroll workspace `[slide 08]`; "harga borongan" protected from QC edits `[slide 04]`; every Saturday, verified component output × rate jahit per artikel, after mandor verification `[slide 07 — chat attachment]` |
| mandor | foreman / line supervisor | Factory-floor supervisor: records 30-minute cutting/assembly output per komponen (FR-7.3/FR-7.4) `[slide 06]`; RBAC row "Kepala Produksi/Mandor" can "Catat output 30 menit" and verifies penjahit reports `[slide 04]`; 2 mandor receive QC bonus pool shares `[slide 05]`, `[slide 09]` |
| penjahit | sewer / sewing operator | Production worker (RBAC role "Penjahit/Tailor") who views component tasks and reports work results verified by the mandor `[slide 04]`; line headcount adjusts dynamically (FR-7.1) `[slide 06]`; +5 mid-week headcount scenario `[slide 09]`; view 04 describes per-penjahit output input `[slide 08]` |
| kepala operasional | head of operations | Senior operations role that receives 1 of the 3 QC bonus pool shares `[slide 05]`, `[slide 09]`. NOTE: "kepala operasional" is NOT one of the 8 RBAC roles on `[slide 04]` — which system role receives the share is `[inferred]`-level mapping, not stated in source |
| kepala produksi | head of production | RBAC role "Kepala Produksi/Mandor (Line)": atur line + alokasi penjahit; tentukan rate card komponen; catat output 30 menit; cannot change payroll formulas or final QC results `[slide 04]` |
| uang makan | meal allowance | Payroll allowance computed in the payroll workspace `[slide 08]`; 10–15% of total ongkos jahit generated in a production period, percentage entered manually per period `[slide 07 — chat attachment]` |
| ongkos jahit | sewing fee / sewing piece-rate earnings | Total sewing fee generated in one production period, the base for the uang makan percentage `[slide 07 — chat attachment]`; its exact computation vs. ongkos potong is UNRESOLVED - not in source |
| ongkos potong | cutting fee | Cutting-side piece rate; **not shown on any slide** — listed for domain completeness only; content is UNRESOLVED - not in source |
| rate card | rate card | FR-7.2 "Rate Card per Artikel & Klien": every article has a per-component rate card derived from time-study results; clients may have different rates for the same article `[slide 06]`; governance: Owner "Ubah rate card", Kepala Produksi/Mandor "Tentukan rate card komponen" `[slide 04]` |
| time study | time study | Per-component timing of garment work: Fase 2 of the operational flow `[slide 03]`; Tim Sample/Adis "Input time study per komponen" `[slide 04]`; digital stopwatch + recording table in the Sample & Time Study Tracker view `[slide 08]`; basis of the rate card `[slide 06]` |
| stok opname | stock opname / physical inventory count | Physical stock count, listed as a Gudang/Warehouse permission `[slide 04]`; procedure/rules not specified on any slide — detail UNRESOLVED - not in source |
| titipan / bahan titipan | consigned / consignment material | Client-owned material deposited at Lukla's warehouse under CMT/Semi-CMT schemes `[slide 01]`; mixing of different clients' titipan is the named contamination risk `[slide 02]`; received by Gudang ("Terima bahan + titipan klien") `[slide 04]`; consignment receiving form + own-stock visibility in views 03/portal `[slide 08]`, `[slide 04]` |
| WIP | work in progress | `[inferred]`; the concept is approximated by the `Menunggu QC` status that assembly output enters (FR-7.4) `[slide 06]` and the flow label on `[slide 04b]` |
| barang jadi | finished goods | Completed products inspected by QC ("Periksa barang jadi", QC Inspector row) `[slide 04]` |
| lolos | pass | QC inspection status: item passed inspection (FR-8.1) `[slide 05]`, `[slide 08]` |
| repair | repair | QC inspection status: item failed but is reworkable (FR-8.1) `[slide 05]`, `[slide 08]` |
| scrap | scrap | QC inspection status: item failed and is discarded (FR-8.1) `[slide 05]`, `[slide 08]`; note: slide 04's QC row says "reject" instead of "scrap" — terminology variance recorded in the register, not resolved |
| defect / cacat | defect | Category of quality fault selected when an item is marked repair/scrap (FR-8.2) `[slide 05]`; QC Inspector "Catat jenis cacat" `[slide 04]` |
| pool bonus / bonus pool | bonus pool | QC-derived bonus fund calculated from QC-passed output (FR-9.1) `[slide 05]`, split ÷3 to 2 mandor + 1 kepala operasional (FR-9.2) `[slide 05]`, `[slide 09]`; 3-way split computed in the payroll workspace `[slide 08]` |
| overhead | overhead | Monthly factory operational cost, recapped ("rekap alokasi overhead operasional pabrik") in the payroll workspace `[slide 08]`; electricity, water, internet, and factory operations total ÷ all units produced in that month `[slide 07 — chat attachment]` |
| line produksi | production line | Sewing line whose capacity adjusts dynamically to active sewers and running orders (FR-7.1 "Alokasi Kapasitas Dinamis") `[slide 06]`; arranged by Kepala Produksi/Mandor ("Atur line + alokasi penjahit") `[slide 04]` |
| output 30 menit | 30-minute output | Output recorded by the mandor every 30 minutes: cutting output per komponen (FR-7.3) and assembly output per komponen entering `Menunggu QC` (FR-7.4) `[slide 06]`; view 04 describes the input as pcs per penjahit `[slide 08]` — granularity variance recorded in the register, not resolved; feeds dashboard graph `[slide 08]` and payroll `[slide 04b]` |
| multi-tenant / multi-klien | multi-tenant / multi-client | One central platform serving many clients with data isolated per client `[slide 02b]`; restated as a system goal `[slide 09]`; FR-1.1 badge `[slide 03]` |
| kontaminasi silang | cross-contamination | Risk of Client A's consigned material being used for Client B's order `[slide 02]`; system must REJECT such issuance `[slide 09]`; warehouse restriction "Dilarang mengeluarkan bahan jika ID Klien/Pesanan tidak cocok" `[slide 04]`; ID-mismatch warning in view 03 `[slide 08]` (FR-6.2; module ownership ambiguity recorded in register) |
| B2B portal | B2B portal | Client-facing access of RBAC role "Klien Maklon/Ext (B2B Portal)": monitor order status, real-time progress, own consigned stock; restricted to own `client_id` data `[slide 04]` |
| gudang | warehouse | Phase 3 of the operational flow: multi-client material receiving and stock (FR-5 — named only, detail UNRESOLVED) `[slide 03]`; RBAC role "Gudang/Warehouse (Stok)" `[slide 04]`; view 03 `[slide 08]`; one of three platform modules `[slide 02b]` |
| cutting | cutting | Phase 4: mass cutting of material (FR-6 — named only, detail UNRESOLVED; guardrail FR-6.2 applies) `[slide 03]`, `[slide 02]`; cutting output recorded per komponen per 30 min (FR-7.3) `[slide 06]`; Gudang issues material "ke cutting" `[slide 04]` |
| sample | sample | Prototype garment versioned v1, v2, …; revisions tracked with spec history into mass orders (FR-4.1) `[slide 03]`, `[slide 09]`; managed by Tim Sample/Adis `[slide 04]`; tracker view `[slide 08]` |
| order | order | Client production order, always under one maklon scheme `[slide 01]`; origin of the integrated data flow Order → Gudang → Cutting → Produksi → QC → Payroll `[slide 04b]` |
| mesin jahit | sewing machine | Factory capacity unit; ±70 machines = current scale context, NOT a system cap `[slide 01]`, `[slide 06]` |
| platform sentral | central platform | The single central system serving all tenants, containing Modul Produksi, Modul Gudang, Modul Payroll `[slide 02b]` |
| audit trail | audit trail | Recorded, traceable history — the named cure for untraceable sample revisions (FR-3.1) `[slide 02]`, `[slide 03]`; locked transaction history cannot be changed even by Owner `[slide 04]` |
| RBAC | role-based access control | Access control by role; 8 roles with IZIN/PEMBATASAN columns `[slide 04]`; the FR-2.1 badge itself appears on no on-disk slide `[assumption]` (slide 02c not on disk) |
| IZIN | permission(s) | "Allowed" column of the RBAC matrix `[slide 04]` |
| PEMBATASAN | restriction(s) | "Restricted" column of the RBAC matrix `[slide 04]` |
| Owner / Eksekutif | owner / executive | Top internal RBAC role: high analytics & system configuration; can change rate cards; CANNOT change locked transaction history `[slide 04]` |
| Tim Sample/Adis | sample team | RBAC role: records sample material usage, inputs time study per component, approves sample versions; cannot approve mass orders without confirmation `[slide 04]` |
| Gudang/Warehouse (Stok) | warehouse staff | RBAC role: receives material + client consignments, issues material to cutting, performs stok opname; forbidden to issue material when ID Klien/Pesanan mismatches `[slide 04]` |
| QC Inspector | QC inspector | RBAC role: inspects barang jadi, sets status lolos/reject/repair, records defect types; cannot change borongan prices or client order data `[slide 04]`; FR-8.1/FR-8.2 `[slide 05]` |
| Finance & Payroll | finance & payroll | RBAC role: creates/approves material POs, issues invoices, computes weekly & monthly wages; cannot change physical warehouse stock `[slide 04]` |
| Klien Maklon/Ext | maklon client (external) | RBAC role for external B2B clients via portal; sees only own `client_id` data `[slide 04]` |
| Snøhund | Snøhund (proper noun) | Lukla's internal clothing brand `[slide 00]`; its orders run under the Full Package scheme `[slide 01]`; drawn as tenant "Klien A (Brand Snøhund)" of the central platform `[slide 02b]` |
| Lukla Manufacturing | Lukla Manufacturing (proper noun) | The convection factory `[slide 00]` in Ciwidey operating ±70 sewing machines `[slide 01]` |
| Menunggu QC | awaiting QC | Status that assembly output enters when recorded (FR-7.4) `[slide 06]`; printed as an edge label on the integrated data flow `[slide 04b]` (position variance recorded in register) |
| tanpa slot kaku | without rigid slots | `[inferred]`; the dynamic-line concept it paraphrased in revision 1 is FR-7.1 "Alokasi Kapasitas Dinamis" `[slide 06]` |
| Sabtu | Saturday | Day on which borongan wages are calculated from accumulated verified component output `[slide 07 — chat attachment]` |
| Ciwidey | Ciwidey (proper noun) | Factory location `[slide 01]` |

**Note:** only **ongkos potong** remains fully unsourced (no slide content at all). Payroll formula specifics are sourced from `[slide 07 — chat attachment]`; no on-disk photo of slide 07 exists yet, and the original has been requested from the user. Terms tagged `[inferred]` (WIP, tanpa slot kaku, kepala operasional's role mapping) are not stated on any slide and must not seed requirements without user confirmation.
