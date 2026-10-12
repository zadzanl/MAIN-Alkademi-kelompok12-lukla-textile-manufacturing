# Task Record: lukla-ops-engine-planning

**Revision:** 5
**Updated:** 2026-10-12

## Intent
Convert the Lukla Operations Engine pitch deck (13 unique slides, Indonesian) into a full formal agile planning suite of 8 English documents (with Indonesian glossary) for a dev-team build blueprint. Planning/docs only — no code, no tech stack.

## User decisions (locked)
- Deliverable shape: FULL FORMAL SUITE (8 docs in `openspec/changes/lukla-ops-engine-planning/artifacts/`)
- Language: English prose, Indonesian domain terms kept + glossary
- Audience: dev team build blueprint
- Approved plan: `artifacts/docs-conversion-plan.md` (rev approved in chat 2026-10-12)

## Constraints / authoring rules
- Every requirement tagged `[slide XX]`, `[inferred]`, or `[assumption]`
- FR-5/FR-6 (Gudang & Cutting): document only what slides state; rest `UNRESOLVED - not in source`
- Payroll: only FR-10.1-10.4; no BPJS/tax/overtime
- Bonus pool /3 fixed per slide; configurability = open question
- ~70 machines = scale context, not a system cap
- Audit/locked history = append-only `[assumption]`
- MoSCoW only; no sprints/story points
- Slides 01 & 08 exist only as chat attachments; orchestrator transcription is the source for those two; originals requested from user (non-blocking)

## Evidence
- All 11 photos in `openspec/artifacts/slide-photos/` viewed by orchestrator; deck complete (00-09 + 02b, 02c, 04b)
- openspec CLI 1.6.0; change scaffolded at `openspec/changes/lukla-ops-engine-planning/`
- Veteran Engineer verdict: HOLD MY BEER — avoid doc sprawl + Scrum theater (mitigations in plan)

## Handoffs
| Phase | Agent | Output | Verdict |
|---|---|---|---|
| 0 | Assistant | 00-deconstruction.md, 07-glossary.md | NEEDS_REVISION (review 1) |
| 0 rev1 | Assistant | corrected register + glossary | superseded by rev1b |
| 0 rev1b | Assistant | slide 07 re-anchored from chat attachment | COMPLETE (self-verified) |
| 0 review 2 | Orchestrator (direct — Review Orchestrator unavailable, provider overload x3) | reviewed rev1+rev1b | NEEDS_REVISION (critical fidelity) |
| 0 rev2 | Assistant | full verbatim re-transcription | pending (FINAL loop, cap=2) |

## Review loop policy (user instructions, 2026-10-12, verbatim)
> "for future revision, please just make sure that: 1. review-revision are capped to three times OR until no critical issue are found"

> "one slight correction: limit the review-revision to only 2."

Applied per phase: max **2** review-revision loops; stop earlier when no critical issues remain. On unresolved criticals after loop 2: escalate to user, do not attempt further fixes.

## Verification
- `openspec status --change lukla-ops-engine-planning` apply-ready
- `artifacts/verify-traceability.ps1` exit 0
- AC-1..AC-7 per plan

## Review findings (Phase 0, review 1) — blocking
- B-05: photo→slide mapping wrong (e.g. 10.40.55b = slide 03 not 02c; 10.40.56 = slide 04 not 03). Root cause: orchestrator mapping corrupted by image dedup. Fix: re-view all 11 photos fresh, read slide number printed on each slide.
- B-06: 10.40.56d = slide 08 (UI Views), not slide 07 → slide 08 IS on disk; slide 07 payroll provenance invalid.
- B-07: slide 06 FR-7.x transcription materially wrong (FR-7.1 = Alokasi Kapasitas Dinamis; FR-7.2 = Rate Card per Artikel & Klien; FR-7.3/7.4 = Output 30 Menit & Assembly → Menunggu QC).
- B-01: glossary WIP/barang jadi tagged [slide 04b] unsupported.
- B-02: glossary ±70 attached to slide 00 unsupported.
- B-03: inferred glossary content not marked [inferred]/[assumption].
- B-04: FR-6.2 module/behavior tension (cutting-phase ID vs warehouse-issuance behavior) not recorded as ambiguity.

## Revisions
- rev 1 (2026-10-12): initial record; plan file confirmed intact after transient undo
- rev 2 (2026-10-12): Phase 0 review 1 = NEEDS_REVISION (B-01..B-07); revision loop 1 dispatched with instruction to rebuild photo→slide mapping from scratch (slide numbers are printed on each slide, top-left)
- rev 3 (2026-10-12): rev1 agent closed B-01..B-07 and rebuilt mapping (verified: disk holds slides 00, 01, 02, 02b, 03, 04, 04b, 05, 06, 08, 09; missing from disk: 02c and 07). NEW ISSUE: agent marked slide 07 FR-10.1-10.4 as `[assumption]` because it did not know slide 07 EXISTS as a fully legible chat attachment (orchestrator read it: FR-10.1 Setiap Sabtu, FR-10.2 10-15%, FR-10.3 ÷3, FR-10.4 Bulanan/Σ Unit). Correction dispatched: re-anchor slide 07 with provenance `[slide 07 — chat attachment]`. Slide 02c genuinely missing from ALL sources → FR-2.1 stays `[assumption]`, originals of 02c + 07 requested from user (non-blocking). User review-cap rule recorded.
- rev 4 (2026-10-12): rev1b COMPLETE — slide 07 transcribed from orchestrator's verbatim chat-attachment reading, provenance `[slide 07 — chat attachment]`, FR-10.1-10.4 `[assumption]` downgrades removed (verified: 15 provenance tags, 0 FR-10.1/assumption hits, UNRESOLVED list size unchanged at 8, `git diff --check` clean). User tightened review cap 3 → 2. User instructed: PAUSE before starting Phase 1 (BRD). Re-review 2 of Phase 0 dispatched; BRD held until user resumes.
- rev 5 (2026-10-12): REVIEW 2 (orchestrator-direct; Review Orchestrator dispatch failed 3x — OpenAI provider overloaded; delegation rules permit direct orchestrator review of subagent work). Personally re-viewed 10/11 photos fresh. VERDICT: NEEDS_REVISION (critical). Mapping now correct (verified 54b=01, 55=02b, 55b=03, 55c=04, 56=04b, 56b=05, 56c=06, 56d=08 — review 1's claim "56=04" was itself wrong). BUT transcriptions are systematically paraphrased/invented at detail level: C-01 slide 02 (wrong label "MAIN PROBLEM" vs "PROBLEM STATEMENT"; card titles/bodies invented — register says payroll "dilakukan manual", slide says "Payroll Kompleks & Headcount Dinamis"); C-02 slide 02b (invented Modul Produksi/Gudang/Payroll decomposition + "Data Terisolasi" edge; photo shows 4 tenant boxes Klien A/B/C "Data terpisah" + Snøhund "Brand internal"; bottom-bar isolation rule missing); C-03 slide 05 (wrong label "QC & BONUS" vs "QUALITY CONTROL"; card titles paraphrased; correction note falsely claims routing text absent — FR-8.1 says "Status menentukan rute tindakan selanjutnya"; missing "dibayarkan bersama payroll mingguan", bottom bar, right panel); C-04 slide 06 (wrong label "OUTPUT TRACKING" vs "PRODUCTION TRACKING"; FR card bodies invented; FR-7.3/7.4 wrongly split into two cards — photo has ONE combined card; stat cards ±70/30 mnt/Real-time missing; "tanpa slot kaku" falsely claimed absent — it IS on the ±70 stat card; touch-friendly terminal caption missing). Slide 07 (rev1b) verified correct. REVISION LOOP 2 (final, cap=2) dispatched: full verbatim re-transcription of all sections with orchestrator's verified readings as cross-check.
