# Task Record: lukla-ops-engine-planning

**Revision:** 1
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
| 0 | Assistant | 00-deconstruction.md, 07-glossary.md | pending |

## Verification
- `openspec status --change lukla-ops-engine-planning` apply-ready
- `artifacts/verify-traceability.ps1` exit 0
- AC-1..AC-7 per plan

## Revisions
- rev 1 (2026-10-12): initial record; plan file confirmed intact after transient undo
