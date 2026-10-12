# 07 — Domain Glossary (Indonesian ↔ English)

**Change:** `lukla-ops-engine-planning`
**Date:** 2026-10-12
**Purpose:** Working glossary for the Lukla Operations Engine document suite. Indonesian domain terms are kept untranslated in the English documents; this table is their definition of record. Definitions are scoped to *this system's* context as deconstructed in `00-deconstruction.md` — they are not general dictionary entries.

| Indonesian term | Literal English | Working definition in this system's context |
|---|---|---|
| maklon | toll manufacturing / contract manufacturing | B2B arrangement where a client outsources garment production to Lukla; every order runs under exactly one of three maklon schemes (CMT / Semi-CMT / Full Package) that fix who supplies raw material `[slide 01 — chat attachment]` |
| CMT (Cut, Make, Trim) | Cut, Make, Trim | Maklon scheme: client supplies ALL raw materials; Lukla supplies cutting, sewing, and finishing labor only `[slide 01 — chat attachment]` |
| Semi-CMT | Semi-CMT | Maklon scheme: client supplies main material; Lukla supplies supporting materials and accessories `[slide 01 — chat attachment]` |
| Full Package (CMT + Bahan) | Full Package (CMT + Materials) | Maklon scheme: Lukla supplies all raw materials and production service; also used for internal Snøhund brand orders `[slide 01 — chat attachment]` |
| konveksi | convection (garment industry sense) | Small/mid-scale garment production business — Lukla's factory type in Ciwidey, ±70 sewing machines `[slide 00]`, `[slide 01 — chat attachment]` |
| borongan | piece-rate / lump-sum piecework | Pay model where sewers are paid per verified output unit, not per hour; computed weekly from verified 30-minute outputs (FR-10.1) `[slide 07]` |
| mandor | foreman / line supervisor | Factory-floor supervisor who inputs each penjahit's output (pcs) every 30 minutes via the floor terminal (FR-7.1); 2 mandor receive QC bonus pool shares `[slide 06]`, `[slide 05]` |
| penjahit | sewer / sewing operator | Production worker whose per-30-minute piece output is tracked and paid borongan; headcount is dynamic (e.g. +5 mid-week) `[slide 06]`, `[slide 09]` |
| kepala operasional | head of operations | Senior operations role; order approval/monitoring per RBAC; 1 kepala operasional receives a QC bonus pool share (FR-9.2/FR-10.3) `[slide 04]`, `[slide 05]` |
| kepala produksi | head of production | Role managing production/line allocation per RBAC matrix `[slide 04]` |
| uang makan | meal allowance | Payroll allowance = 10–15% of ongkos jahit; percentage entered manually per payroll period (FR-10.2) `[slide 07]` |
| ongkos jahit | sewing fee / sewing piece-rate earnings | The sewing piece-rate amount that serves as the base for the uang makan percentage (FR-10.2); exact computation not defined in source `[slide 07]` |
| ongkos potong | cutting fee | Cutting-side piece rate; named in domain vocabulary but not specified on any slide — treat as UNRESOLVED if needed |
| rate card | rate card | Per-style/per-component piece-rate price list used to value borongan output; implied by borongan payroll, not shown on slides — UNRESOLVED if needed |
| time study | time study | Per-component timing of garment work using a digital stopwatch, recorded in the Sample & Time Study Tracker (view 02) `[slide 08 — chat attachment]` |
| stok opname | stock opname / physical inventory count | Periodic physical stock count; NOT specified on any slide — listed here because later docs may need the term; content is UNRESOLVED - not in source |
| titipan / bahan titipan | consigned / consignment material | Client-owned material deposited at Lukla's warehouse under CMT/Semi-CMT schemes; subject to cross-client contamination guardrail (FR-6.2) and the consignment receiving form (view 03) `[slide 02]`, `[slide 08 — chat attachment]` |
| WIP | work in progress | Goods mid-production between cutting and QC; status flow includes `Menunggu QC` `[slide 04b]` |
| barang jadi | finished goods | Completed products that have passed through production/QC `[slide 04b]` |
| lolos | pass | QC inspection status: item passed inspection (FR-8.1) `[slide 05]` |
| repair | repair | QC inspection status: item failed but is reworkable; routed to repair (FR-8.1) `[slide 05]` |
| scrap | scrap | QC inspection status: item failed and is discarded (FR-8.1) `[slide 05]` |
| defect / cacat | defect | Category of quality fault selected when an item is marked repair/scrap (FR-8.2) `[slide 05]` |
| pool bonus / bonus pool | bonus pool | QC-derived bonus fund calculated from QC-passed output (FR-9.1), split ÷3 to 2 mandor + 1 kepala operasional (FR-9.2/FR-10.3) `[slide 05]`, `[slide 07]` |
| overhead | overhead | Monthly factory operational cost allocated per unit: total overhead ÷ total units produced in the period (FR-10.4) `[slide 07]` |
| line produksi | production line | Sewing line grouping penjahit/machines; dynamically sized — "tanpa slot kaku" (no rigid slots) (FR-7.3) `[slide 06]` |
| output 30 menit | 30-minute output | Piece count per penjahit captured by the mandor every 30 minutes on the floor terminal; base data for dashboards and payroll (FR-7.1) `[slide 06]`, `[slide 08 — chat attachment]` |
| multi-tenant / multi-klien | multi-tenant / multi-client | One central platform serving many clients with data isolated per client (FR-1.1) `[slide 02b]`, `[slide 02c]` |
| kontaminasi silang | cross-contamination | Risk of Client A's consigned material being used for Client B's order; system must REJECT such issuance (FR-6.2; negative test scenario 1) `[slide 02]`, `[slide 09]` |
| B2B portal | B2B portal | Client-facing view where a maklon client sees only their own order progress (RBAC role "Klien B2B (Portal)") `[slide 04]`, `[slide 08 — chat attachment]` |
| gudang | warehouse | Phase 3 of the operational flow: multi-client material receiving and stock (FR-5 — named only, detail UNRESOLVED) `[slide 03]` |
| cutting | cutting | Phase 4: mass cutting of material (FR-6 — named only, detail UNRESOLVED; guardrail FR-6.2 applies) `[slide 03]` |
| sample | sample | Prototype garment versioned v1, v2, …; revisions tracked with spec history into mass orders (FR-4.1) `[slide 03]`, `[slide 09]` |
| order | order | Client production order, always under one maklon scheme; origin of the integrated data flow Order → Gudang → Cutting → Produksi → QC → Payroll `[slide 01 — chat attachment]`, `[slide 04b]` |
| mesin jahit | sewing machine | Factory capacity unit; ±70 machines = current scale context, NOT a system cap `[slide 01 — chat attachment]`, `[slide 06]` |
| platform sentral | central platform | The single central system serving all tenants (slide 02b architecture) `[slide 02b]` |
| audit trail | audit trail | Recorded history of actions/data; basis for sample-revision traceability (FR-3.1) `[slide 02c]` |
| RBAC | role-based access control | Access control by role; 8 roles with IZIN/PEMBATASAN columns (FR-2.1) `[slide 02c]`, `[slide 04]` |
| IZIN | permission(s) | "Allowed" column of the RBAC matrix `[slide 04]` |
| PEMBATASAN | restriction(s) | "Restricted" column of the RBAC matrix `[slide 04]` |
| Owner | owner | Top RBAC role; full access with locked-history restriction (cell wording partially legible) `[slide 04]` |
| Staff Gudang | warehouse staff | RBAC role handling material receiving/issue and stock `[slide 04]` |
| QC / Inspektor | QC inspector | RBAC role recording inspection results and defect categories `[slide 04]`, `[slide 05]` |
| Klien B2B (Portal) | B2B client (portal) | RBAC role for external maklon clients; sees own data only `[slide 04]` |
| Snøhund | Snøhund (proper noun) | Lukla's internal clothing brand; modeled as a tenant client under the Full Package scheme `[slide 00]`, `[slide 01 — chat attachment]` |
| Lukla Manufacturing | Lukla Manufacturing (proper noun) | The convection factory in Ciwidey operating ±70 sewing machines `[slide 00]`, `[slide 01 — chat attachment]` |
| Menunggu QC | awaiting QC | Order/item status between production output and QC inspection `[slide 04b]` |
| tanpa slot kaku | without rigid slots | Dynamic-line principle: line/headcount changes need no fixed slot configuration (FR-7.3) `[slide 06]` |
| Sabtu | Saturday | Weekly borongan payroll period end day (FR-10.1) `[slide 07]` |
| Ciwidey | Ciwidey (proper noun) | Factory location, West Java `[slide 01 — chat attachment]` |

**Note:** terms marked "UNRESOLVED if needed" (ongkos potong, rate card, stok opname) appear in this glossary for domain completeness but have **no defining content in the slide source** — later documents must not build requirements on them.
