# Plan: Resume and Complete Lukla Operations Engine Planning Suite

> **Change Root:** `openspec/changes/lukla-ops-engine-planning/`  
> **Authoritative Baseline:** `00-deconstruction.md` revision 4, `Lukla Operations Engine - BRD v2.2.1 - FINAL.md` (internal version 2.3.0)  

---

## 1. Goal Description
The previous sessions established a rigorous source deconstruction register (`00-deconstruction.md` rev 4, approved in `review-001.md`) and audited the comprehensive Indonesian BRD (`Lukla Operations Engine - BRD v2.2.1 - FINAL.md` internal v2.3.0, approved in `review-004.md`). 

In Phase 2, the team authored the missing structural specifications:
- `04-rbac-matrix.md` (8 roles, IZIN & PEMBATASAN)
- `06-acceptance-tests.md` (4 closing scenarios expanded to AT-01..AT-10 and AT-R01..AT-R08)

However, the session was interrupted by LLM provider overloads when dispatching the Review Orchestrator for Phase 2. Consequently:
1. `04-rbac-matrix.md` and `06-acceptance-tests.md` exist on disk but **have not received review approval** (`review-005-phase2.md` was never generated).
2. Phase 3 (traceability verification script and OpenSpec apply-ready status) is **unstarted**.

This plan outlines the exact progression to complete the Phase 2 review and finalize Phase 3.

---

## 2. Forensic Audit: What the Previous Agents Completed vs. Where Work Paused

| Phase | Original v1 Step | Actual Deliverable / Action Taken | Review / Verification Status | Pickup Action |
|---|---|---|---|---|
| **Phase 0** | `00-deconstruction.md` & `07-glossary.md` | Verbatim re-transcription from high-resolution PDF renders (`page-0003.jpg`, `page-0004.jpg`, `page-0008.jpg`, `page-0009.jpg`). Closed critical defects C-01..C-04. | **APPROVED** (`review-001.md`, rev 4) | **DONE.** Source register is authoritative. Do not reopen. |
| **Phase 1** | `01-brd.md` (Scope & Business Brief) | Consolidated into mega-BRD (`Lukla Operations Engine - BRD v2.2.1 - FINAL.md` internal v2.3.0). User approved adopting mega-BRD as reference. Cleaned up invented rounding, restored distinct FR-9.1/9.2, reconciled 20 observed FRs. | **APPROVED** (`review-004.md`) | **DONE.** Adopted BRD v2.3.0 is approved baseline. Do not alter text unless cross-linking. |
| **Phase 2 (Specs)** | `02-feature-map.md`, `03-prd.md`, `05-data-flow.md` | Absorbed directly into the mega-BRD (§7, §8, §16.5, §4–6, and `BRD-diagram.md`). | **APPROVED** within BRD v2.3.0 | **DONE.** Maintained as unified spec. |
| **Phase 2 (RBAC)** | `04-rbac-matrix.md` (8 roles, IZIN/PEMBATASAN) | Authored on disk (7,073 bytes) mapping slide 04 and cross-linked to BRD §3.1/§11.1 (`impl-006-rbac.md`). | **AWAITING REVIEW** | **PICKUP STEP 1:** Review against slide 04 and register rev 4. |
| **Phase 2 (Tests)** | `06-acceptance-tests.md` (4 closing scenarios) | Authored on disk (18,656 bytes) covering AT-01..AT-10, AT-R01..AT-R08 negative checks, and BLOCKED items (`impl-007-tests.md`). | **AWAITING REVIEW** (Review failed 3x with provider overload) | **PICKUP STEP 1:** Review against slide 09 and register rev 4. |
| **Phase 3 (Verify)** | `verify-traceability.ps1` & OpenSpec Apply-Ready | Not created. `openspec status` reports 0/4 complete. | **NOT STARTED** | **PICKUP STEP 2 & 3:** Write script, execute check, scaffold OpenSpec files. |

---

## 3. Step-by-Step Pickup Execution Plan

### Step 1: Formal Phase 2 Review & Verdict (`review-005-phase2.md`)
- **Action:** Conduct the independent review of `04-rbac-matrix.md` and `06-acceptance-tests.md` against `00-deconstruction.md` rev 4, BRD v2.3.0, and slide photos.
- **Specific Scrutiny Targets:**
  1. Inspect AT-04 component-to-finished-unit linkage consistency.
  2. Inspect AT-09 confirmation dependency prerequisite.
  3. Verify all 8 roles match slide 04 IZIN and PEMBATASAN.
  4. Verify all 4 scenarios from slide 09 (cross-client contamination, midweek +5 sewers, 3,000 units QC bonus pool ÷3, sample v1→v2 revision) are fully represented as executable test specifications.
- **Output:** Generate `openspec/changes/lukla-ops-engine-planning/artifacts/review/review-005-phase2.md` and update `task-record.md` (bumping to revision 10) and `worklog.md`.

### Step 2: Implement and Execute Traceability Script (`verify-traceability.ps1`)
- **Action:** Create `openspec/changes/lukla-ops-engine-planning/artifacts/verify-traceability.ps1`.
- **Automated Assertions:**
  - Verify physical existence of all core planning artifacts (`00-deconstruction.md`, `04-rbac-matrix.md`, `06-acceptance-tests.md`, `07-glossary.md`, `Lukla Operations Engine - BRD v2.2.1 - FINAL.md`).
  - Scan for all 20 observed FR IDs (`FR-1.1`, `FR-1.4`, `FR-2.1`, `FR-3.1`, `FR-4.1`, `FR-5`, `FR-6`, `FR-6.2`, `FR-7.1`, `FR-7.2`, `FR-7.3`, `FR-7.4`, `FR-8.1`, `FR-8.2`, `FR-9.1`, `FR-9.2`, `FR-10.1`, `FR-10.2`, `FR-10.3`, `FR-10.4`) across register, BRD backlog, and acceptance tests.
  - Verify the 8 role names in `04-rbac-matrix.md`.
  - Verify scenario keywords (`kontaminasi`, `headcount`, `bonus pool` / `3 Arah`, `revisi`) in `06-acceptance-tests.md`.
  - Validate that every `UNRESOLVED` marker is consolidated in BRD §13.3.
  - Exit with return code 0 on success, or non-zero with failure diagnostic details.
- **Verification:** Execute `pwsh verify-traceability.ps1` and confirm exit code 0.

### Step 3: Populate OpenSpec Spec-Driven Artifacts
- **Action:** Scaffold and write the required schema artifacts in `openspec/changes/lukla-ops-engine-planning/`:
  - `proposal.md`: Summary of problem statement, context, and planning suite scope.
  - `design.md`: Technical and architectural design referencing BRD v2.3.0, storage spike, and database structure.
  - `specs/**/*.md`: Capability and functional specifications referencing the approved documents.
  - `tasks.md`: Detailed work breakdown tracking the planning deliverables and implementation handoff.
- **Verification:** Run `openspec status --change lukla-ops-engine-planning` and assert progress is 4/4 complete (apply-ready).

---

## 4. Acceptance Criteria
- **AC-1:** `04-rbac-matrix.md` and `06-acceptance-tests.md` pass formal review in `review-005-phase2.md`.
- **AC-2:** Every observed FR ID (FR-1.1 through FR-10.4) is verified across register, BRD §16.5, and acceptance tests.
- **AC-3:** `verify-traceability.ps1` runs clean and exits with code 0.
- **AC-4:** `openspec status --change lukla-ops-engine-planning` transitions from 0/4 to 4/4 complete (apply-ready).
- **AC-5:** `task-record.md` and `worklog.md` accurately record the recovery, Phase 2 review closure, and Phase 3 completion.

---

## 5. Non-Goals
- No modification of source code or application programming (planning and documentation only).
- No reopening of Phase 0-R (register rev 4 is frozen and approved).
- No re-fragmenting of the Indonesian Mega-BRD into 8 separate files (respecting the prior user decision).
- No invention of unstated Gudang/Cutting details beyond deck evidence.

