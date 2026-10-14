# Raw Implementation Report — Phase 2A RBAC

## Scope and inputs

- Authorization: implement Phase 2A only, then pause before Phase 3. Read `task-record.md` **revision 9**, including its active recovery scope; `00-deconstruction.md` **revision 4 in full**, including UNRESOLVED and Contradictions/ambiguities; `07-glossary.md`; `Lukla Operations Engine - BRD v2.2.1 - FINAL.md` (**internal version 2.3.0**); and `review-004.md` (Phase 1-A approved, not Phase 2 approval).
- No subagents dispatched. No software, schema, API, test execution, OpenSpec completion artifacts, Phase 3 script, source re-transcription, cleanup, reset, stash or commit. The peer acceptance plan is being written by another worker and was not touched.

## Changes

- Created [04-rbac-matrix.md](../04-rbac-matrix.md): one eight-row capability table reproducing each slide-04 role, IZIN and PEMBATASAN; explicit UNSPECIFIED examples; source-status tags and cross-links to register, BRD, glossary and future acceptance plan. No second duplicate permission table.
- Created this report at `implementation/impl-006-rbac.md`. No existing file edited by this task.

## Acceptance checklist

| Criterion | Outcome / evidence |
|---|---|
| Exactly eight slide-04 roles, names and all IZIN/PEMBATASAN text | PASS — direct comparison of all 8 rows and four source columns (`#`, role, IZIN, PEMBATASAN) with the register rev 4 table. |
| Allowed vs explicit prohibition vs UNSPECIFIED | Documented in the matrix and its reading guide; unlisted permissions are not grants and are not adopted deny-all business rules. |
| FR-2.1 content vs ID | Slide-04 role content is observed; FR-2.1 ID remains `[assumption]` pending unavailable slide 02c. |
| FR-6.2 and role/bonus/RACI boundaries | Module ownership stays undecided; rate-card overlap stays undecided; no automatic payroll or QC privilege, ninth RBAC role, or RACI-based system grant introduced. |
| Source and peer navigation | Register, BRD and glossary targets exist. `06-acceptance-tests.md` was absent at first check, then appeared during the final recheck; this task did not create or inspect its contents. |
| Whitespace | Initial `git diff --no-index --check -- NUL <matrix>` flagged two trailing Markdown hard-break spaces; removed before final recheck. Final commands/results below. |

## Decisions and limits

- The slide-04 table is the authority for exact role wording. Some `07-glossary.md` entries still contain superseded slide-06/02b descriptions; using them instead would reintroduce errors. Register rev 4 and the reviewed BRD internal 2.3.0 take precedence for this task. `[inferred]` (source comparison).
- UNSPECIFIED examples are deliberately non-exhaustive. Resolution requires a later business decision; this report does not claim complete access policy or settled implementation behavior. The slide-04 restriction on sample mass-order approval is conditional on confirmation, not a blanket ban. `[slide 04]` (restriction); `[inferred]` (boundary).
- This is a documentation parity review, **not** a runtime authorization test. No application tests were run. Link existence does not validate rendered anchor fragments or the future peer's contents.

## Verification record

- `PowerShell Get-Content -Encoding utf8` extracted the register's slide-04 source table and the eight numbered rows from `04-rbac-matrix.md`; compared columns `#`, `Peran`, `IZIN`, `PEMBATASAN` with case-sensitive `-cne`: **PASS**, eight rows and exact wording, no mismatches.
- `Test-Path` for `00-deconstruction.md`, `07-glossary.md`, and `Lukla Operations Engine - BRD v2.2.1 - FINAL.md`: **True** for each. `Test-Path` for `06-acceptance-tests.md`: **False** at first check, **True** at final check (concurrent peer created it; no content review).
- `git diff --no-index --check -- NUL <newfile>` on **each** new file after correction: no whitespace diagnostics; exit **1** on each, the normal `--no-index` difference exit for a new file versus `NUL` (initial matrix check exited 3 with two whitespace diagnostics; both were removed).
- Final parity recheck: **8/8** rows exact for number, role, IZIN and PEMBATASAN. Link-target checks: register **True**, glossary **True**, BRD **True**; concurrent peer changed from **False** to **True** before completion. `git check-ignore -v -- <both new files>` identifies `.gitignore:121:artifacts/` for each. Both files exist on disk but are ignored by Git status; they are not committed or staged. The existing `M task-record.md` was not edited by this task.