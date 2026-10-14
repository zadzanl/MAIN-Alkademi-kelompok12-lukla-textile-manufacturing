# Phase 1-A Recovery Correction — Raw Implementation Report

## Status

**COMPLETE for the bounded Phase 1-A BRD correction.** The BRD now has an explicit, readable observed FR backlog and the independently audited defects listed in the user brief were repaired. Phase 2 was not started.

No subagents were dispatched, per instruction.

## Context loaded

- `task-record.md` Revision 8, including the 2026-10-13 orchestration-recovery entry.
- Approved recovery plan: `openspec/changes/lukla-ops-engine-planning/artifacts/docs-conversion-plan-v2-pickup.md`.
- Independent audit reports: `research-001.md` and `research-002.md`.
- Authoritative comparison source: `00-deconstruction.md`, register revision 4.
- Environment: Windows PowerShell (`pwsh`), repository root `c:\Projects\hackathon-MAIN-alkademi`, OpenSpec CLI 1.6.0, date 2026-10-13.

OpenSpec status was checked. The change is `spec-driven` but currently blocked because its proposal/design/specs/tasks artifacts are absent. This bounded repair was explicitly authorized by the user and did not modify those missing artifacts.

## Objective

Repair the Phase 1-A BRD defects found by independent audits so Phase 2 documents can rely on an explicit, observable FR backlog while preserving register source fidelity and avoiding new business decisions.

## Files changed by this phase

- `openspec/changes/lukla-ops-engine-planning/artifacts/Lukla Operations Engine - BRD v2.2.1 - FINAL.md`
- `openspec/changes/lukla-ops-engine-planning/artifacts/worklog.md`
- `openspec/changes/lukla-ops-engine-planning/artifacts/impl-003.md`

Protected files were not modified: `00-deconstruction.md`, `research-001.md`, `research-002.md`, and historical review reports. The working tree also contains pre-existing Phase 0-R/recovery changes outside this phase.

## Edits made

1. Kept document version `2.3.0` and removed the accidental duplicate identical v2.3.0 revision-history entry.
2. Replaced `<IMAGE_OMITTED_DUE_TO_SIZE>` in §16.5 with a readable Markdown table containing exactly the 20 observed register IDs and a `Sumber` column. FR-2.1 remains marked `[assumption]` because slide 02c is missing.
3. Added the requested §7 source tags:
   - FR-4.1: `[slide 02; slide 03]`.
   - FR-7.1 through FR-7.4: `[slide 06]`.
   - FR-8.1: `[slide 05]`.
4. Added distinct observed source-backed §7 rows for FR-9.1 and FR-9.2 with meanings from register revision 4.
5. Removed invented rounding-direction wording from the FR-10.3 row, payroll formula, and acceptance scenario. Retained `UNRESOLVED - not in source` for remainder handling and assigned no remainder to an account or recipient.
6. Removed the duplicate FR-8.2 from Sprint 4.
7. Removed trailing whitespace exposed on changed BRD lines and the extra final blank line.
8. Appended the dated worklog entry describing the edits and verification.

## Verification commands and actual output

### OpenSpec context

Command:

```powershell
openspec status --change "lukla-ops-engine-planning" --json
```

Actual result: `schemaName` = `spec-driven`; `isComplete` = `false`; apply is blocked because `tasks` is missing. The status also reports proposal/design/specs/tasks as absent or blocked. No OpenSpec artifact was created because it was outside the allowed file list.

### All 20 observed IDs

Command checked the exact list: FR-1.1, FR-1.4, FR-2.1, FR-3.1, FR-4.1, FR-5, FR-6, FR-6.2, FR-7.1, FR-7.2, FR-7.3, FR-7.4, FR-8.1, FR-8.2, FR-9.1, FR-9.2, FR-10.1, FR-10.2, FR-10.3, FR-10.4.

Actual output:

```text
PASS all 20 observed FR IDs present
```

### §16.5 exact inventory and FR-9 rows

Actual output:

```text
FR-9.1/FR-9.2 §7 row matches: 2 (expected 2)
FR-9.1/FR-9.2 §16.5 row matches: 2 (expected 2)
§16.5 exact observed row count: 20 (expected 20)
```

### Required negative checks

Actual output:

```text
<IMAGE_OMITTED_DUE_TO_SIZE> matches: 0
pembulatan ke bawah matches: 0
rekening cadangan matches: 0
Versi 2.3.0 history matches: 1
```

The inspected Sprint 4 scope line was:

```text
... (FR-8.1, FR-8.2, FR-10.1, FR-10.2, FR-10.3, FR-10.4).
```

This contains one FR-8.2 occurrence.

### Required whitespace check

Command:

```powershell
git diff --check -- 'openspec/changes/lukla-ops-engine-planning/artifacts/Lukla Operations Engine - BRD v2.2.1 - FINAL.md' 'openspec/changes/lukla-ops-engine-planning/artifacts/worklog.md'
```

Actual result: exit code 0 and no `git diff --check` errors. Git emitted only this line-ending warning for the worklog:

```text
warning: in the working copy of 'openspec/changes/lukla-ops-engine-planning/artifacts/worklog.md', LF will be replaced by CRLF the next time Git touches it
```

## Acceptance criteria

- **Duplicate v2.3.0 entry removed:** PASS; one `Versi 2.3.0` match remains.
- **Readable §16.5 observed inventory:** PASS; exactly 20 register IDs and a `Sumber` column are present.
- **FR-2.1 preserved as `[assumption]`:** PASS; the missing slide 02c is not guessed around.
- **Requested §7 source tags:** PASS for FR-4.1, FR-7.1–FR-7.4, and FR-8.1.
- **FR-9.1 and FR-9.2 distinct in §7 and §16.5:** PASS.
- **Rounding direction and reserve-account rule removed:** PASS; both requested forbidden strings return zero matches, with remainder handling still unresolved.
- **Sprint 4 duplicate FR-8.2 removed:** PASS.
- **`git diff --check` run:** PASS, exit code 0.
- **Dated worklog entry appended:** PASS.

## Decisions

- The register revision 4 remains authoritative. The §16.5 table uses its observed inventory only; skipped IDs and BRD-only inferred IDs were not added to that table.
- FR-2.1 remains `[assumption]`; the 8-role concept is separately corroborated by slide 04, but slide 02c is unavailable.
- The bonus formula states only division by three. Remainder/rounding behavior remains `UNRESOLVED - not in source`.
- Existing adopted inferred planning sections were preserved. No new business decision, RBAC interpretation, module ownership decision, or payroll-base decision was added.

## Failures / recovery

The first CRLF-insensitive whitespace cleanup attempt did not remove the reported trailing spaces. I corrected the cleanup with a CRLF-aware expression, reran `git diff --check`, and obtained exit code 0. The helper used for one initial §7 range count selected the wrong boundary and returned 0; I did not treat that as a content result. A corrected fixed-range check returned two §7 FR-9 rows and two §16.5 FR-9 rows.

OpenSpec remains blocked on missing proposal/design/specs/tasks artifacts. This was recorded rather than bypassed or fabricated.

## Risks / notes

- The BRD filename still contains `v2.2.1`, while its internal document version is `2.3.0`; changing the filename was not requested and was not done.
- The full repository working tree includes pre-existing Phase 0-R/recovery modifications. This report claims only the three files listed above for this bounded phase.
- This report does not claim Phase 2 deliverables or overall planning-suite completion.
