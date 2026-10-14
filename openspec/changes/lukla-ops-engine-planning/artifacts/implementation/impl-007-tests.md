# Implementation Report — Phase 2B acceptance-test specifications

**Change:** `lukla-ops-engine-planning`  
**Phase:** 2B only  
**Date:** 2026-10-13  
**Status:** Documentation complete; application execution not performed.

## Source and authorization confirmation

- Read `task-record.md` **revision 9**, updated 2026-10-13. Its active authorization is to create the Phase 2 RBAC matrix and acceptance-test plan, then pause before Phase 3. It prohibits reset, stash, commit, Phase 3 verification script and OpenSpec completion artifacts.
- Read `00-deconstruction.md` **revision 4**, including the source inventory, slides 04/05/06/07/09, master FR inventory, unresolved list, and contradictions/ambiguities.
- Read `Lukla Operations Engine - BRD v2.2.1 - FINAL.md`, internal version **2.3.0**, including §§7, 13.3, 16.1, 16.4–16.6. The filename/version mismatch is retained and reported; the BRD was not edited.
- Read `07-glossary.md` revision 3 for domain terminology. Where its older explanatory wording was inconsistent with register revision 4, the acceptance plan follows the register and preserves the uncertainty.
- Read `review-004.md`; it approves Phase 1-A only and explicitly says Phase 2 deliverables had not yet been assessed.
- `04-rbac-matrix.md` was read for the concurrent Phase 2A cross-link. It was not modified.

## Files created

1. `openspec/changes/lukla-ops-engine-planning/artifacts/06-acceptance-tests.md`
   - Manual English Given/When/Then specifications, not application test code.
   - IDs, source/FR mappings, prerequisites/fixtures, expected outcomes, execution states and evidence instructions.
   - Four slide-09 closing scenarios, including the valid matched-material control beside the rejection case.
   - Small +5 midweek sewer fixture with hand-calculated per-sewer Saturday wages.
   - 3,000 Pass QC units with an explicitly illustrative Rp 7 per-piece rate and hand-calculated pool and three-way split.
   - Sample v1 → v2 → Semi-CMT mass-order traceability without asserting automatic rate inheritance.
   - Same-sewer repair with no second piece-rate credit.
   - Negative checks for all eight explicit slide-04 PEMBATASAN rows, with no invented default grants.
   - Owner locked-history behavior separated from the unconfirmed append-only/reversal mechanism.
   - Nondivisible bonus quotient recorded while payout/remainder behavior is BLOCKED; no floor rounding or reserve account invented.
   - FR-9.2 and FR-10.3 identified as one shared divide-by-three rule.
   - Meal-base and FR-6.2 module ownership retained as unresolved; QC and mandor verification prerequisites retained.

2. `openspec/changes/lukla-ops-engine-planning/artifacts/implementation/impl-007-tests.md` (this report).

No existing file was edited by this phase. In particular, no BRD, register, glossary, task record, RBAC matrix, verification script, OpenSpec artifact, or unrelated artifact was changed. No subagents were dispatched, per instruction. No reset, stash, cleanup, or commit was run.

## Independent arithmetic check

Command run in PowerShell:

```powershell
$w=@(4,6,2,3,4,5,6); $rate=2000; $w | ForEach-Object { $_*$rate }; ($w | Measure-Object -Sum).Sum*$rate; 3000*7; (3000*7)/3; [decimal]100000/3
```

Observed output:

```text
8000
12000
4000
6000
8000
10000
12000
60000
21000
7000
33333,333333333333333333333333333
```

Recorded expected values:

- S1–S7: Rp 8,000; Rp 12,000; Rp 4,000; Rp 6,000; Rp 8,000; Rp 10,000; Rp 12,000.
- Total eligible units: 30 × Rp 2,000 = **Rp 60,000**.
- Bonus fixture: 3,000 × Rp 7 = **Rp 21,000**; 21,000 ÷ 3 = **Rp 7,000 each**.
- Boundary fixture: Rp 100,000 ÷ 3 = **Rp 33,333⅓ each**. Integer payout and Rp 1 remainder disposition are **BLOCKED**, not rounded or assigned.

The comma decimal separator in the PowerShell output is locale formatting; the exact mathematical value is one-third of a rupiah after Rp 33,333.

## Verification commands and actual results

### Link targets and whitespace

Command checked every Markdown link target in `06-acceptance-tests.md` against the artifact root:

```powershell
$a='openspec/changes/lukla-ops-engine-planning/artifacts'; $f=Join-Path $a '06-acceptance-tests.md'; $t=Get-Content -Raw $f; [regex]::Matches($t,'\]\(([^)#]+)(?:#[^)]+)?\)') | ForEach-Object { $p=[uri]::UnescapeDataString($_.Groups[1].Value); '{0}: {1}' -f $p,(Test-Path (Join-Path $a $p)) }
```

Result: `True` for `00-deconstruction.md`, the BRD filename, `07-glossary.md`, and `04-rbac-matrix.md` (the RBAC target appears twice). No broken link target was found.

Trailing-whitespace scan result: **0 lines** in `06-acceptance-tests.md`.

`git diff --check --no-index -- NUL <new-file>` returned exit code 1 because `--no-index` compares the new file against the Windows `NUL` device and reports a non-diff comparison status; the separate trailing-whitespace scan returned zero. This was not treated as a runtime or acceptance result.

### File and ignore-state check

`Test-Path` returned `True` for both requested files. The new acceptance file is ignored by the repository rule:

```text
.gitignore:121:artifacts/ openspec/changes/lukla-ops-engine-planning/artifacts/06-acceptance-tests.md
```

Therefore ordinary `git status --short` does not display either new artifact. This is an observation about repository ignore behavior, not evidence that the files were absent. No force-add or git index operation was performed.

### Scope observation

Before and after the work, the visible pre-existing tracked edit was:

```text
 M openspec/changes/lukla-ops-engine-planning/artifacts/task-record.md
```

It was preserved. The concurrent RBAC file existed and was not edited.

## Limits and unresolved decisions

- No application or test runner exists in this Phase 2B documentation task; all cases remain **NOT RUN**. No runtime correctness, authorization enforcement, tenant isolation, database behavior, UI wording, or payroll implementation success is claimed.
- Test fixture amounts/rates and identifiers are illustrative inferences only. They establish reproducible arithmetic, not policy.
- `FR-5` warehouse transaction detail, `FR-6` cutting detail, and FR-6.2 Gudang/Cutting/both ownership remain unresolved.
- The exact meal-allowance base/distribution remains unresolved even though the source provides the 10–15% period rule.
- QC status vocabulary varies across source slides; the plan does not silently equate Reject with scrap.
- The `Menunggu QC` placement differs between source views and is not forced into a new reconciliation rule.
- Bonus recipient configurability and nondivisible payout/remainder handling remain unresolved.
- The plan records traceable v2 history but does not claim automatic rate-card inheritance; that BRD §16.4 wording is not source-backed by register revision 4.
- The repository’s existing `04-rbac-matrix.md` contained trailing whitespace in its own Phase 2A content when inspected. It was intentionally not modified because another worker owns it.

## Phase boundary

Phase 2B is complete as documentation only. Per the user instruction, work pauses **before Phase 3**. No Phase 3 verification script, OpenSpec completion artifact, cleanup, commit, reset, or stash was performed.