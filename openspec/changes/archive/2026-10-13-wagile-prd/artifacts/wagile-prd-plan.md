# Plan: Wagile PRD Restructure + Timeframe Sanitization

**Status:** APPROVED by user — in implementation (Orchestration mode).
**Change:** `wagile-prd`
**Revision:** 2 — integrated the user's shared Gemini reference ("Hybrid PRD Format for Wagile" browser tab): three-part Two-Speed blueprint (Waterfall Contract / Agile Backlog / Release Strategy). Added User Journeys, NFRs, Risks & Dependencies to the skeleton; milestones folded into the sprint plan (sequence-based, no dates). Phases 1 and 2 confirmed independent → dispatched in parallel.

## TL;DR

Create ONE new client-facing document, `PRD - Lukla Operations Engine - v2.0 - Wagile.md`, in plain Bahasa Indonesia with a two-layer "wagile" structure: **Bagian A (Kontrak)** — a fixed, sign-off-able contract layer modelled on Lenny Rachitsky's problem-crystallization block and the Confluence PRD header/assumptions/open-questions sections; **Bagian B (Backlog Agile)** — a living scrum backlog (22 FRs, 4 sprints: 3 build + 1 test/buffer, zero dates) for the dev team. The BRD v2.3.0 remains the internal source of truth and is referenced, never duplicated. Afterwards, a fenced sanitization pass strips schedule dates/timeframes from the 4 deliverable docs only, preserving audit-trail metadata.

## Efficiency Check

Veteran Engineer subagent dispatch failed 2x (upstream provider `invalid_request_error`); the simplicity ladder was run inline by the Plan agent instead. Verdict: request is valid, but the sharpest version is **restructure the existing PRD v1.3, not author a third standalone requirements doc** — confirmed by user (doc-strategy = "Restructure PRD v1.3, reference BRD").

## User Decisions (locked)

| Item | Decision | Source |
|---|---|---|
| Document strategy | Restructure PRD v1.3 into wagile two-part doc; BRD stays as referenced source of truth | [user: askQuestions `doc-strategy`] |
| Timeline | Hackathon week only: ~3 build days + 1 testing/buffer day. **No timeframes/dates in any document.** Sanitize existing docs, discrete subagent allowed | [user: askQuestions `timeline` freeText] |
| Ledger visibility | The immutable double-entry core must be genuinely present and UI-visible in the hackathon slice | [user: "Just make sure that a UI `IMMUTABLE DOUBLE-ENTRY CORE` is available"] |
| Audience | Both hackathon judges (now) and Lukla stakeholders (later) | [user: askQuestions `audience`] |
| Template | Follow a popular template: Confluence PRD and/or Lenny Rachitsky's template | [user: follow-up message] |

## Template Grounding (verified this session)

Confluence PRD template sections [doc: https://www.atlassian.com/software/confluence/templates/product-requirements]:
1. Top table (status, team, target release) — we keep the table but **omit release date** per user rule.
2. Objective + Success metrics table.
3. Assumptions.
4. Requirements/options table (requirement, user story, importance, notes).
5. Supporting documentation.
6. Open questions table.
7. Out of scope ("not doing").

Lenny Rachitsky's Product Requirements template [doc: https://www.atlassian.com/software/confluence/templates/lennys-product-requirements]:
- Description (what is it), Problem (what it solves), Why (evidence it's real), Success (how we know it's solved), Audience (who we build for), What (what it looks like in the product).

**Mapping:** Lenny's six questions + Confluence's header/assumptions/open-questions/out-of-scope form **Bagian A (fixed contract)**. Confluence's requirements table + user stories + sprint slicing + acceptance criteria form **Bagian B (living backlog)**.

## Target Files

| Action | Absolute path | What |
|---|---|---|
| CREATE | `c:\Projects\hackathon-MAIN-alkademi\openspec\changes\PRD - Lukla Operations Engine - v2.0 - Wagile.md` | The new wagile PRD (skeleton below) |
| EDIT | `c:\Projects\hackathon-MAIN-alkademi\openspec\changes\PRD Draft - Lukla Operations Engine - v1.3.md` | Add "SUPERSEDED by v2.0" banner at top; strip dates (L3 header, L138–142 sprint dates) |
| EDIT | `c:\Projects\hackathon-MAIN-alkademi\openspec\changes\BRD - Lukla Operations Engine - v2.2.1 - FINAL.md` | Strip schedule dates only (release date, revision-history dates, §12.2 sprint dates, M1–M5 milestone dates). No content rewriting |
| EDIT | `c:\Projects\hackathon-MAIN-alkademi\openspec\changes\Overall Plan Draft.md` | Strip sprint date bar (L365) |
| EDIT | `c:\Projects\hackathon-MAIN-alkademi\openspec\artifacts\lukla_operations_engine_knowledge_base.md` | Strip schedule dates (L4, L271–276 area) |

**Do-NOT-touch fence (explicit):** `task-record.md`, `worklog.md`, all `review-*.md`, `research-*.md`, `impl-*.md`, `00-deconstruction.md` provenance lines, `07-glossary.md`, `08-client-clarification-register.md`, `storage-architecture-draft.md`, everything under `DEPRECATED\`, photo filenames (`WhatsApp Image 2026-10-12 ...` — referenced by the register), and `openspec/changes/lukla-ops-engine-planning/{proposal,design,tasks}.md` unless the regex scan shows schedule dates there (verify first; proposal/design/tasks showed no hits).

**Never strip, even in the 5 target files:**
- Operational calendar facts that are business rules: "payroll setiap Sabtu", "interval 30 menit" — these are domain requirements, not schedule estimates.
- Version numbers (v2.3.0, v1.3).
- Sample data containing year-like strings (`LOT-2026-99`).
- The empty `Tanggal` column in the sign-off table (it is a fill-in-at-signing field, not an estimate).
- The BRD "Start Gate" rule itself (a governance rule, not a date).

## New PRD Skeleton (the contract for the author)

File: `PRD - Lukla Operations Engine - v2.0 - Wagile.md`. Language: plain Bahasa Indonesia; established technical terms kept (`client_id`, borongan, uang makan, rate card). Zero dates anywhere. Every fact must trace to the BRD or PRD v1.3 — no invented requirements.

```
# PRD — Lukla Operations Engine (Wagile)
Header table [Confluence top table, minus dates]:
  Status | Versi: 2.0 | Metode: Wagile (Kontrak + Backlog) | Tim Inti: Dev 1–4 |
  Dokumen Induk (source of truth): BRD v2.3.0 | Pendahulu: PRD v1.3 (superseded)

# BAGIAN A — KONTRAK / WATERFALL CONTRACT (berubah hanya lewat persetujuan ulang)
  A.1 Ringkasan Eksekutif         [Gemini Part 1.1 + Lenny: Description] — 2-3 kalimat
  A.2 Masalah yang Dipecahkan     [Lenny: Problem] — 3 pain points, bahasa awam
  A.3 Mengapa Ini Layak Dibangun  [Lenny: Why] — ringkasan BD-1..BD-4 dari BRD §4
  A.4 Tujuan Bisnis & Ukuran Keberhasilan [Gemini Part 1.2 + Lenny: Success + Confluence metrics]
      — tabel metrik, contoh: 0 insiden kontaminasi silang lolos;
        rekap payroll Sabtu < 15 menit; 4 skenario penerimaan lulus
  A.5 Untuk Siapa                 [Lenny: Audience] — pembaca dokumen + 8 peran sistem (tabel ringkas, referensi BRD §1.4)
  A.6 Batasan Ruang Lingkup       [Gemini Part 1.3 + Confluence: not doing] — In/Out, referensi BRD §3.1/§3.2
  A.7 Batasan Tetap (Non-Negotiable) — immutable ledger (append-only, koreksi via transaksi pembalik),
      anti-cross-contamination guardrail di level database, RBAC 8 peran
  A.8 Asumsi, Risiko & Ketergantungan [Confluence: Assumptions + Gemini Part 1.4] — dari BRD §13.1 + risiko
  A.9 Keputusan Terbuka           [Confluence: Open questions table]
      — 8 item UNRESOLVED dari BRD §13.3, masing-masing: pertanyaan | opsi | pemilik keputusan | status
      — PLUS konflik antar-dokumen: pembulatan bonus QC (PRD v1.3: "sisa ke cadangan pabrik"
        vs BRD §13.2/§16.1: UNRESOLVED, jangan alokasikan) — dikutip apa adanya, tidak diputuskan
  A.10 Lembar Persetujuan         — matriks 5 peran dari BRD (Owner, Head of Ops, Finance Lead,
      Lead Solution Architect, Lead Software Engineer), kolom Tanggal dibiarkan kosong

# BAGIAN B — BACKLOG AGILE (dokumen hidup untuk tim scrum)
  B.0 Cara Membaca Bagian Ini — Bagian B boleh berubah lewat sprint review; Bagian A tidak
  B.1 Persona & User Stories      [Gemini Part 2.1] — dari PRD v1.3 §2.1, diperluas ke 8 peran
  B.2 User Journeys               [Gemini Part 2.2] — alur naratif: bahan dari penerimaan → cutting →
      jahit → QC → payroll; sampel v1 → v2 → order massal
  B.3 Product Backlog (Epics & Stories) [Gemini Part 2.3 + Confluence requirements table]
      — 22 FR dari BRD §16.5 dikelompokkan per epic (6 capability area dari proposal OpenSpec)
      — tabel: FR ID | Kebutuhan (1 baris) | Prioritas | Sprint | Status
      — prioritas mengikuti BRD §7
  B.4 Kebutuhan Non-Fungsional    [Gemini Part 2.4] — NFR-01..06 dari BRD §8
  B.5 Rencana Sprint & Milestone (tanpa tanggal) [Gemini Part 3: Release Strategy]
      — Sprint 1, 2, 3 = build; Sprint 4 = testing, integrasi, buffer "preventative"
      — Milestone M1..M4 berbasis urutan (bukan tanggal)
      — Urutan mengikuti dependensi MOD-01..05 dari BRD §12.1
      — SPRINT 1 WAJIB memuat: skema double-entry ledger + RBAC + satu permukaan UI
        yang memperlihatkan jurnal ledger (interpretasi "UI IMMUTABLE DOUBLE-ENTRY CORE")
  B.6 Kriteria Penerimaan         — 4 skenario Given-When-Then dari BRD §16.4/§16.6
  B.7 Pembagian Tugas Dev 1–4     — dari PRD v1.3 §4
  B.8 Definition of Done

# LAMPIRAN
  L.1 Formula payroll & costing (BRD §16.1, apa adanya)
  L.2 Spesifikasi 6 UI Views (BRD §16.3 / PRD v1.3 §5)
  L.3 Glosarium ringkas + pointer ke BRD §14
```

## Steps

### Phase 1 — Author the wagile PRD
1. Create the new PRD file per skeleton above. Content sources: BRD v2.3.0 (§1, §3, §4, §7, §12.1, §13, §14, §16), PRD v1.3 (§2.1, §4, §5, design notes), Overall Plan Draft (architecture summary only). Reference-not-duplicate: anything long (full RBAC matrix, full FR prose, mermaid diagrams) stays in the BRD and is pointed to.
2. Self-check the draft against AC-1..AC-4 (below) before touching other files.

### Phase 2 — Supersede + sanitize (discrete subagent)
3. Add superseded banner to PRD v1.3 header.
4. Dispatch a discrete sanitization subagent with: the 5-file target list, the never-strip fence, and replacement style (dates → sequence labels: "Sprint 1..5", "Milestone M1..M5"; remove release-date lines or replace with "Tanggal Rilis: (diisi saat persetujuan)"). Stop condition: `BLOCKED: <file> | <line> | <why unsure>` if a date is ambiguous (e.g., might be operational or provenance).

### Phase 3 — Verify
5. Run the date-pattern regex scan over the 5 target files → expect zero schedule-date hits (allowed residue: version numbers, `LOT-2026-99`, "Sabtu", empty `Tanggal` columns).
6. FR traceability check: extract `FR-\d+(\.\d+)?` IDs from the new PRD Part B and set-compare against BRD §16.5's 22 IDs.
7. `git diff --stat` review confirming only the 5 target files changed.
8. Re-run the repo's existing pattern `openspec/changes/lukla-ops-engine-planning/artifacts/verify-traceability.ps1` if its scope covers these docs [code: referenced in task-record.md rev 11; read it first to confirm scope before relying on it].

## Acceptance Criteria

- **AC-1:** New PRD exists at the target path, in Bahasa Indonesia, zero date/timeframe strings (regex-verified), structured as Bagian A (A.1–A.10) + Bagian B (B.0–B.6) + Lampiran, with section comments mapping to Confluence/Lenny template sections.
- **AC-2:** All 22 FR IDs from BRD §16.5 appear in the Part B backlog table with priorities matching BRD §7; no invented FRs.
- **AC-3:** A.9 lists all 8 UNRESOLVED items from BRD §13.3 plus the bonus-rounding doc conflict, none silently resolved; A.10 contains the 5-role sign-off block with empty Tanggal column.
- **AC-4:** B.3 shows 4 sprints (3 build + 1 test/buffer), no dates, dependency-ordered per BRD §12.1, and Sprint 1 includes the double-entry ledger plus a UI surface exposing the ledger journal.
- **AC-5:** Sanitization scan over the 5 target files returns zero schedule-date hits; `git diff` shows no changes outside the 5 target files.
- **AC-6:** PRD v1.3 opens with a superseded banner pointing to v2.0.

## Non-Goals

- No rewriting or "improving" BRD content — the BRD is referenced, not duplicated.
- No resolving the 8 UNRESOLVED business decisions or the bonus-rounding conflict — they are surfaced as open decisions only.
- No touching audit/provenance artifacts, photo filenames, or the DEPRECATED folder.
- No app code, no scaffolding, no new dependencies.
- No relative-date substitutes ("minggu depan", "H+3") — sequence labels only.

## Decisions (defaults I chose — veto-able)

1. **Language:** Bahasa Indonesia, matching BRD/PRD v1.3; the client and judges are Indonesian. [default]
2. **File location:** `openspec/changes/`, matching the existing loose-doc convention. [default]
3. **Sign-off block:** reuses the BRD's existing 5-role approval matrix rather than inventing a new one. [default]
4. **Sanitization fence:** strip schedule dates from the 5 deliverable docs only; preserve provenance/audit dates in process artifacts (worklog, task-record, reviews, research, deconstruction register) because they are the traceability system this project is built on, and photo filenames are referenced by that register. [default — rationale: user's rule targets "timeframe estimates", and audit dates are not estimates]
5. **"UI IMMUTABLE DOUBLE-ENTRY CORE" interpretation:** Sprint 1 backlog must include the real ledger schema AND at least one UI surface where journal entries are visible (e.g., a journal/audit panel in the Payroll or Dashboard view) — not a mocked CRUD facade. If you meant something narrower (e.g., just a dashboard badge), say so. [default — interpretation, flagged]
6. **New PRD header carries a version number (2.0) but no dates**, per the no-timeframe rule. [default]

## Risks

- **Over-stripping by the sanitization subagent** (removing "Sabtu" payroll rules or provenance dates) → mitigated by the explicit never-strip fence, the 5-file target list, stop condition, and AC-5 git-diff review.
- **Document drift** between PRD v2.0 and BRD → mitigated by reference-not-duplicate rule; Part A header names the BRD as source of truth.
- **Template theatre** — producing a doc that *looks* like Lenny's template but buries the actual decisions → mitigated by AC-3 forcing the open-decisions table.
- **My Sprint-1 ledger-UI interpretation is wrong** → flagged as Decision 5; cheap to adjust at backlog level.

## Verification (runnable)

1. Date scan (PowerShell, repo root):
   `Get-ChildItem -Path .\openspec -Recurse -Filter *.md | Select-String -Pattern '\b20\d\d-\d{2}-\d{2}\b|\b\d{1,2}\s?(Okt|Nov|Des|Oct|Nov|Dec)[a-z]*\b|\b(Oktober|November|Desember|October|December)\b|\b2026\b'`
   → zero hits inside the 5 target files except allowed residue (version numbers, `LOT-2026-99`, "Sabtu" payroll rule, empty `Tanggal` header).
2. FR set comparison: extract `FR-\d+(\.\d+)?` from new PRD → compare against the 22 IDs in BRD §16.5 → sets must match.
3. `git diff --stat` → only the 5 target files listed under Target Files.
4. Manual read-through of new PRD against skeleton checklist (A.1–A.10, B.0–B.6, L.1–L.3 all present).

## Stop Conditions (for the implementing agent)

If anything differs from this brief — a target file is missing, the BRD section numbering has changed, a date is ambiguous between schedule/provenance/operational, or an FR ID in the BRD doesn't match §16.5 — return `BLOCKED: <what differs> | <evidence> | <question>`. Do not choose for the user and do not widen scope.
