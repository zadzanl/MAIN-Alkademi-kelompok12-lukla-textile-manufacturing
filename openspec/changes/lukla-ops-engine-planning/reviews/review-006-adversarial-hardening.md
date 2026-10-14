# Review 006: Comprehensive Adversarial Hardening, Sensibility & 360° Multi-Stakeholder Audit

**Change:** `lukla-ops-engine-planning`  
**Date:** 2026-10-13  
**Auditor:** Adversarial Review Orchestrator & 10 Discrete Specialist Subagents  
**Audited Baseline:**
- `Lukla Operations Engine - BRD v2.2.1 - FINAL.md` (Internal v2.3.0)
- `overall-plan-draft.md` (Blueprint Draft 12/10/2026)
- Authoritative Sources: `00-deconstruction.md` (Rev 4), `04-rbac-matrix.md`, `06-acceptance-tests.md`, `storage-architecture-draft.md`

---

## 1. Executive Summary & Review Verdict

A 10-vector adversarial audit was conducted on the Lukla Operations Engine planning suite, deploying discrete specialist agents across:
1. **Veteran Engineer (Simplicity Ladder & Ambiguity Audit)**
2. **Review Orchestrator (Adversarial Hardening Coordinator)**
3. **Fact-Check Specialist (Verbatim Slide Traceability)**
4. **Manufacturing Sensibility Specialist (Ciwidey Garment Floor Realism)**
5. **Obviousness & YAGNI Specialist (Anti-Overengineering Audit)**
6. **Low-Hanging Fruits Specialist (Pragmatic Simplification Roadmap)**
7. **Factory Owner & Executive Sponsor Perspective (P&L, SAM Overhead, Snøhund Conflicts)**
8. **Head of Operations & Floor Mandors Perspective (70 Machines, Downtime, Piece-Rate Disputes)**
9. **Finance & Commercial Lead Perspective (Custodial Accounting, Cash Logistics, PPh/PPN)**
10. **External B2B Maklon Client Perspective (IP Chinese Wall, Remnant Return, Digital Sign-Off)**

### High-Level Verdict:
**APPROVED FOR ARCHITECTURAL HARDENING WITH MANDATORY RE-ALIGNMENT.**
While the multi-tenant isolation concept and piece-rate payroll vision are strategically sound, the current `overall-plan-draft.md` contains critical enterprise overengineering anti-patterns, floor workload impossibilities, and dangerous incentive misalignments that must be resolved prior to code execution.

---

## 2. Key Audit Findings by Dimension

### A. Double-Entry Accounting Core vs. Shop Floor Reality
* **The Flaw:** `overall-plan-draft.md` (§2.2) mandates synchronous double-entry general ledger journal entries (`Inventory:WIP` vs `Payroll:AccruedWagesPayable`) on high-frequency 30-minute station writes for up to 70 operators.
* **The Contradiction:** Slide 06 FR-7.4 explicitly states: *"Upah diakui setelah verifikasi QC"* (wages are recognized *only after* QC verification). Accruing wages at the 30-minute interval mark prematurely inflates payroll liabilities before units pass inspection.
* **Lock Contention Risk:** Under concurrent submissions from multiple lines on rural Ciwidey WiFi, synchronous GL debit/credit balancing triggers risk database deadlocks and latency spikes ($>500\text{ ms}$, violating NFR-03).
* **Hardening Mandate:** Decouple into a **Two-Tier Architecture**:
  - *Tier 1 (Floor MES):* Append-only operational event logging (`station_output_logs`, `bundle_movements`).
  - *Tier 2 (Finance GL):* Batched macro-milestone journal rollups (Material Issuance, QC Pass batches, and Saturday Payroll Finalization).
  - *Accounting Schema Correction:* On CMT orders, Lukla sells *manufacturing services*, not physical finished goods. Direct labor must be booked as Cost of Services / Contract Fulfillment Asset (PSAK 72), not capitalized into raw physical inventory assets.

### B. Anti-Cross Contamination (FR-6.2): Database Trigger vs. Physical Reality
* **The Flaw:** The PL/pgSQL function `validate_material_dispatch()` aborts transactions if `source_stock.client_id != target_order.client_id`.
* **The Failure Modes:**
  1. *Semi-CMT Breakdown:* Lukla internal trims (zippers, thread) have `client_id = Lukla`, which causes the trigger to crash when issued to a client order.
  2. *Scrap / Remnant Returns:* Remnant returns to warehouse have `destination_order_id = NULL`, triggering an unhandled exception.
  3. *The Physical Law:* **Software cannot uncut physically cut fabric.** If an unlabelled roll is spread on a cutting table, the catastrophe has already occurred before any database trigger runs.
* **Hardening Mandate:**
  - Add `ownership_type` (`CONSIGNED_CLIENT`, `COMPANY_SHARED_TRIM`) to bypass false positives.
  - Implement the **4-Pillar Physical-Digital Interlock**:
    1. Synthetic tear-resistant QR tags stapled to inner cardboard tube cores at Gudang intake.
    2. Physical warehouse rack zoning by client.
    3. Mandatory two-step optical scan (Scan Job Traveler + Scan Fabric Roll QR) at the cutting table before fabric unrolling is authorized.
    4. Color-coded bundle traveler cards attached to physical cut components.

### C. Sprint Phasing & Fragile Dependencies
* **The Flaw:** Sprints 1 to 4 build headless schemas and triggers, while **Sprint 5** is tasked with building all six complex UI interfaces simultaneously alongside acceptance testing.
* **Hardening Mandate:** Re-sequence into **Vertical Slices**:
  - Sprint 1: Inbound Warehouse & Cross-Contamination Guardrail + **View 03 (Warehouse Grid)**
  - Sprint 2: Sample R&D & Digital Time Study + **View 02 (Sample Tracker)**
  - Sprint 3: Floor MES & Line Allocation + **View 04 (Floor Touch Terminal)**
  - Sprint 4: QC Triage & Saturday Piece-Rate Payroll + **View 05 (QC Terminal)** & **View 06 (Payroll Workspace)**
  - Sprint 5: Executive BI Dashboard + **View 01 (Dashboard)**, Offline PWA Hardening, and E2E Audits.

### D. Shop Floor Ergonomics & Mathematical Feasibility (Ciwidey Reality)
* **The Math:** 70 machines supervised by 2 mandors = 35 machines per mandor. Walking the floor, counting pieces, and tapping tablet screens for 35 people every 30 minutes requires **17.5 minutes out of every 30 minutes** (51.4s per person). Mandors lose all needle supervision time.
* **The Environment:** Mountainous Ciwidey has humid, lint-heavy air and machine oil spray. Capacitive tablets get unresponsive.
* **Downtime Unrecorded:** Unrecorded PLN power outages, needle breakage SOPs, machine mechanical jams, and Friday prayer breaks distort 30-minute speed graphs.
* **Hardening Mandate:**
  - Adopt **Physical Bundle Traveler Cards (Kartu Bundel)** with barcode/QR stubs scanned at bundle completion, rather than polling 70 individual benches every 30 minutes.
  - Add operational downtime quick-tags (`PLN Padam`, `Jarum Patah`, `Tunggu Mekanik`, `Istirahat Resmi`) to View 04.
  - Institute a daily tally slip/sign-off before 17:00 to eliminate Saturday payday disputes.

### E. Incentive Alignment & Moral Hazard (QC Bonus Pool ÷ 3)
* **The Flaw:** FR-9.2 and FR-10.3 allocate 100% of the QC bonus pool equally to 2 Mandors and 1 Kepala Ops, while the front-line QC Inspector receives **0%**.
* **The Moral Hazard:** Mandors and the Ops Head have a direct financial incentive to pressure subordinate junior QC inspectors to mark defective garments as `PASS` so their Saturday bonus is maximized.
* **Hardening Mandate:** Restructure the bonus pool to include QC inspectors, parameterize recipient counts ($N$), and implement a client return penalty clawback clause.

### F. Multi-Stakeholder Gaps (Owner, Finance, Maklon Client)
* **Owner P&L:** Flat monthly overhead allocation (FR-10.4) severely cross-subsidizes complex Snøhund winter parkas at the expense of simple B2B CMT articles. Must adopt Standard Allowed Minutes (SAM) / Normal Capacity Costing.
* **Finance Cash Flow:** Lukla incurs hard cash drains every Saturday while B2B clients pay on Net 30/60 terms. Working capital milestone gates (DP before cutting, CBD before delivery) must be formalized.
* **B2B Maklon Trust:** To prevent IP leaks to Lukla's internal brand Snøhund, establish a digital "Chinese Wall" with access logging for client CAD/tech packs, formalize remnant return protocols, and institute digital sample sign-off gates.

---

## 3. Persisted Artifacts & Next Steps

1. **Client Clarification Register:** All 21 slide gaps and open business questions have been formally compiled into:  
   [`openspec/changes/lukla-ops-engine-planning/artifacts/08-client-clarification-register.md`](file:///c:/Projects/hackathon-MAIN-alkademi/openspec/changes/lukla-ops-engine-planning/artifacts/08-client-clarification-register.md)
2. **Implementation Plan Alignment:** Update `overall-plan-draft.md` and the OpenSpec design artifacts to reflect the approved decisions:
   - Retain Double-Entry Accounting Core with decoupled Tier 1 / Tier 2 batching.
   - Implement Physical Bundle Barcode/QR Cards (Kartu Bundel) for shop floor output tracking.
   - Escalate Domain 1–6 questions to client leadership.

*Report signed by Lead Solution Architect & Review Orchestrator.*

