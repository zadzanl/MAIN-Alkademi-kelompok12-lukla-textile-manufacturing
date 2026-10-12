# Plan: Convert Lukla Operations Engine Slide Deck into Formal Agile Planning Suite

**TL;DR:** Transcribe and deconstruct the 13 unique slides (11 photos on disk in `openspec/artifacts/slide-photos/` + slides 01 and 08 seen only as chat attachments) into a traceability register, then generate 8 English-language documents (Indonesian domain glossary) forming a full formal suite: BRD, feature map, PRD with agile backlog, RBAC matrix, data-flow spec, acceptance test plan. Every requirement traces to a slide + FR ID. Deck gaps are marked `UNRESOLVED`, never invented.

**Efficiency Check:** Veteran Engineer consulted — verdict: valid request, but avoid document sprawl and Scrum theater. Mitigations adopted: single deconstruction register as the one source of truth (no copy-pasted paragraphs across docs), MoSCoW priorities instead of fabricated sprints/story points, explicit gap policy. User chose the full formal suite knowingly.

---

## Source Inventory (verified by viewing all 11 photos)

| Photo file | Slide | Content |
|---|---|---|
| `...10.40.54.jpeg` | 00 | Cover: Sistem Manajemen Produksi & Payroll Konveksi — Lukla Manufacturing x Snohund |
| `...10.40.54b.jpeg` | 02b | Arsitektur Solusi: Platform Sentral (multi-tenant, data terpisah per klien) |
| `...10.40.54c.jpeg` | 05 | Inspeksi QC & Bonus Pool 3 Arah (FR-8.1, FR-8.2, FR-9.1, FR-9.2) |
| `...10.40.55.jpeg` | 02 | Masalah Utama (kontaminasi silang FR-6.2; payroll FR-10; penelusuran revisi FR-3.1/FR-4.1) |
| `...10.40.55b.jpeg` | 02c | Solusi: Platform Operasional Terpadu (FR-1.1 multi-tenant, FR-2.1 RBAC, FR-3.1 audit trail) |
| `...10.40.55c.jpeg` | 04b | Alur Data Terintegrasi (Order -> Gudang -> Cutting -> Produksi -> QC -> Payroll) |
| `...10.40.56.jpeg` | 03 | Alur Operasional 6 Fase (FR-1..FR-10 phase mapping) |
| `...10.40.56b.jpeg` | 04 | Matriks RBAC — 8 Peran Pengguna |
| `...10.40.56c.jpeg` | 06 | Tracking Output 30 Menit & Line Dinamis (FR-7.1-7.4) |
| `...10.40.56d.jpeg` | 07 | Mesin Payroll Fleksibel (FR-10.1-10.4) |
| `...10.40.57.jpeg` | 09 | Closing: Tujuan Sistem & 4 Skenario Pengujian |
| chat attachment only | 01 | Konteks Bisnis & Skema Maklon (CMT / Semi-CMT / Full Package) |
| chat attachment only | 08 | Layar Tampilan Utama — 6 Minimum Required UI Views |

**Deck is complete (00-09 + sub-slides).** Slides 01 and 08 are legible in the chat attachments and will be transcribed from there; originals should be requested from the user for the record (non-blocking).

## Target Files (all to be created)

All deliverables live in `openspec/changes/lukla-ops-engine-planning/artifacts/`:

1. `00-deconstruction.md` — Source Deconstruction & Traceability Register. Slide-by-slide extraction: every FR ID, every business rule, every actor, every UI element, each tagged `[slide XX]`. Duplicates across re-photographed slides merged. Ends with a master FR inventory (FR-1.1 ... FR-10.4) and an `UNRESOLVED` gap list.
2. `01-brd.md` — BRD / Scope & Product Brief: business context (Lukla, Snohund internal brand, 3 maklon schemes), 3 problem statements, goals/non-goals, actor overview, 6-phase operational flow, MVP boundary, assumptions & gaps.
3. `02-feature-map.md` — Capability & Feature Map: Epics -> capabilities -> features, each mapped to FR IDs + source slides + actor + MoSCoW priority (Must/Should/Could).
4. `03-prd.md` — PRD with agile backlog: per-epic user stories (As a / I want / So that), acceptance criteria in Given/When/Then, business rules (payroll formulas, bonus pool split, 30-min output cycle), edge cases, NFRs (multi-tenant isolation, audit immutability, RBAC enforcement).
5. `04-rbac-matrix.md` — RBAC Permission Matrix: 8 roles x capabilities, with IZIN (permissions) and PEMBATASAN (restrictions) transcribed from slide 04.
6. `05-data-flow.md` — Data Flow & Integration Spec: entity/status flow Order -> Gudang -> Cutting -> Produksi -> QC -> Payroll (slide 04b), status transitions (e.g. `Menunggu QC`), multi-tenant isolation checkpoints.
7. `06-acceptance-tests.md` — Acceptance Test Plan: the 4 closing scenarios as executable test cases + negative paths (cross-client contamination rejection) + boundary cases + RBAC/audit checks.
8. `07-glossary.md` — Indonesian <-> English domain glossary (maklon, borongan, mandor, penjahit, uang makan, ongkos jahit, CMT, Semi-CMT, Full Package, ...).

OpenSpec tracking artifacts (schema-required): `proposal.md`, `design.md`, `specs/**/*.md`, `tasks.md` in the change root — these track the doc-generation work itself; `tasks.md` mirrors the phases below.

## Steps

### Phase 0 — Ingest & Deconstruct
1. Create `00-deconstruction.md` from all 13 slides. Extract every FR ID, rule, actor, number (70 machines, 30 min, 10-15%, /3, 3000 units, 5 penjahit). Tag each line `[slide XX]`. Merge duplicate photos.
2. Create `07-glossary.md` *(parallel with step 1)* from terms found during deconstruction.
3. Transcribe slides 01 and 08 from the chat-attachment versions; note in the register that originals are pending from the user.

### Phase 1 — Business Frame *(depends on Phase 0)*
4. Create `01-brd.md`. MVP boundary = the 6 minimum UI views (slide 08) + the 4 acceptance scenarios (slide 09). Non-goals: statutory payroll (BPJS/tax/overtime), accounting/GL, procurement, shipping/logistics, native mobile apps.

### Phase 2 — Structural Specs *(parallel with each other; depend on Phase 0, feature map also reads 01-brd.md)*
5. Create `02-feature-map.md` with proposed epics: E1 Tenancy & Clients, E2 Access Control & Audit, E3 Sample & Time Study, E4 Order Approval & Mass Production, E5 Warehouse & Cutting, E6 Production Tracking & Line Allocation, E7 Quality Control & Bonus Pool, E8 Payroll & Overhead, E9 Dashboards & B2B Portal.
6. Create `04-rbac-matrix.md` from slide 04 (8 roles, IZIN + PEMBATASAN).
7. Create `05-data-flow.md` from slides 04b and 03.

### Phase 3 — PRD *(depends on Phase 2)*
8. Create `03-prd.md`: user stories per epic with Given/When/Then acceptance criteria, business rules with exact formulas, NFRs.

### Phase 4 — Acceptance Tests *(depends on Phase 3)*
9. Create `06-acceptance-tests.md`: 4 scenarios from slide 09 as test cases (cross-client contamination rejection; dynamic headcount payroll with +5 penjahit mid-week; 3000-unit QC bonus pool split /3; sample v1 -> v2 revision to Semi-CMT mass order with v2 spec history) + negative/boundary/RBAC tests.

### Phase 5 — Traceability Validation
10. Create and run `artifacts/verify-traceability.ps1` (see Verification). Fix any misses.
11. Fill `proposal.md`, `design.md`, `specs/`, `tasks.md` so `openspec status` reports apply-ready.

## Authoring Rules (edge cases & gap policy)

- **Traceability:** every requirement carries `[slide XX]` + FR ID where one exists. Anything inferred is tagged `[inferred]`; anything assumed is tagged `[assumption]` and listed in the BRD assumptions section.
- **FR-5 / FR-6 (Gudang & Cutting):** named in the 6-phase flow but never specified on any slide. Document only what slides state (multi-client material receiving, mass cutting, contamination guardrail FR-6.2); mark the rest `UNRESOLVED - not in source`. Do NOT invent inventory transactions, cutting batches, or wastage rules.
- **Payroll:** only the 4 deck formulas (FR-10.1 Saturday weekly borongan from verified 30-min outputs; FR-10.2 uang makan 10-15% of ongkos jahit, manual % per period; FR-10.3 QC bonus pool /3 to 2 mandors + 1 kepala operasional; FR-10.4 monthly overhead / total units). BPJS, tax, overtime, statutory reporting = explicit non-goals.
- **Bonus pool /3:** fixed per slide 07; whether the recipient count is configurable is an open question — flag it, do not decide it.
- **~70 machines:** current factory scale context, NOT a hard system cap (slide 06 itself says "tanpa slot kaku" / no rigid slots).
- **Snohund:** internal brand, modeled as a tenant client under the Full Package scheme.
- **Audit trail / locked history (FR-3.1, Owner PEMBATASAN):** treat as append-only immutability NFR; corrections happen via reversal/adjustment entries, not edits. Tag `[assumption]`.
- **Acceptance scenarios:** these are tests (including negative paths), not feature descriptions.
- **No Scrum theater:** MoSCoW priorities only. No sprints, story points, or velocity unless the user later provides hackathon duration + team size.
- **Language:** English prose; Indonesian domain terms kept and defined in `07-glossary.md`.

## Acceptance Criteria

- AC-1: All 8 deliverable files exist at the paths above and are internally cross-linked.
- AC-2: Every FR ID observed on the slides (FR-1.1, FR-1.4, FR-2.1, FR-3.1, FR-4.1, FR-5, FR-6, FR-6.2, FR-7.1-7.4, FR-8.1, FR-8.2, FR-9.1, FR-9.2, FR-10.1-10.4) appears in `00-deconstruction.md`, `02-feature-map.md`, and `03-prd.md`.
- AC-3: All 8 RBAC roles with their IZIN and PEMBATASAN appear in `04-rbac-matrix.md`.
- AC-4: All 4 closing test scenarios appear as executable test cases in `06-acceptance-tests.md`, including the negative path (system must reject issuing Client A material for Client B order).
- AC-5: Every `UNRESOLVED` marker anywhere in the suite is consolidated in the BRD gaps section.
- AC-6: `verify-traceability.ps1` runs green (exit 0).
- AC-7: No requirement lacks a source tag (`[slide XX]`, `[inferred]`, or `[assumption]`).

## Non-Goals

- No source code, no tech-stack selection, no database schema, no API design (planning/docs only).
- No statutory payroll, tax, BPJS, overtime, or legal-compliance content.
- No invented detail for the unspecified Gudang & Cutting module.
- No sprint plans, story points, velocity, or ceremony definitions.
- No translation of documents into Indonesian (English suite + glossary only).

## Verification

1. Run `openspec status --change lukla-ops-engine-planning` — all `applyRequires` artifacts done.
2. Run `openspec/changes/lukla-ops-engine-planning/artifacts/verify-traceability.ps1`, which must:
   - assert all 8 deliverable files exist;
   - `Select-String` each FR ID (list above) across `00-deconstruction.md`, `02-feature-map.md`, `03-prd.md` and fail on any miss;
   - assert the 8 role names appear in `04-rbac-matrix.md`;
   - assert the 4 scenario keywords (kontaminasi/cross-client, headcount, bonus pool, revisi) appear in `06-acceptance-tests.md`;
   - collect all `UNRESOLVED` occurrences and assert each is echoed in `01-brd.md`;
   - exit 0 on success, 1 with a named failure list otherwise.
3. Manual spot-check: pick 3 random PRD user stories and confirm each traces back to a slide via the deconstruction register.

## Decisions

- Full formal suite (8 docs) — user-selected over the recommended lean 3-doc pack.
- English with Indonesian glossary — user-selected.
- Dev-team build blueprint orientation — user-selected; judges/stakeholders served by the BRD summary.
- Deliverables live in the change's `artifacts/` folder (repo's only established workflow is OpenSpec; user did not veto).
- MoSCoW prioritization, no sprint schedule (hackathon duration/team size unknown).

## Risks

- **Slides 01 & 08 exist only as chat attachments** — transcription from legible photos is fine, but originals may contain sharper text. Mitigation: request originals from user; register notes the provenance.
- **OCR-style misreads from angled photos** (e.g. FR-7.2 rate-card wording partially obscured). Mitigation: deconstruction register marks uncertain transcriptions `[illegible?]`; never guesses.
- **FR numbering may skip IDs** (e.g. FR-1.2/1.3, FR-8.x gaps) — the register records only observed IDs and lists skipped numbers as possibly-defined-elsewhere, not as gaps to fill.
- **Doc sprawl** (8 docs was not the recommended option). Mitigation: `00-deconstruction.md` is the single source of truth; other docs reference it instead of duplicating source transcription.

## Stop Conditions (for the implementing agent)

If anything differs from this brief — a slide contradicts another slide, an FR ID referenced in the flow has no definition anywhere, text needed for a requirement is illegible, or the user provides new source material mid-flight — return `BLOCKED: <what differs> | <evidence> | <question>`; do not choose for the user and do not widen scope.
