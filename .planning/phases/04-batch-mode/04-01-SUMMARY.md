---
phase: 04-batch-mode
plan: "01"
subsystem: infra
tags: [github-actions, workflow_call, reusable-workflow, matrix, batch]

# Dependency graph
requires:
  - phase: 03-full-single-cve-workflow
    provides: Complete single-CVE pipeline (prepare, archive, collect jobs) in archive-cve.yml
provides:
  - archive-cve.yml extended with workflow_call trigger for reuse
  - batch-archive.yml: multi-CVE batch entrypoint with validation and per-CVE matrix fan-out
affects: [batch-mode-02, future-scheduling]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Reusable workflow pattern: workflow_call trigger with inputs mirrors workflow_dispatch inputs"
    - "Batch fan-out via matrix: parse input list -> JSON array -> fromJSON matrix in called workflow"
    - "fail-fast: false on matrix ensures independent CVE processing"

key-files:
  created:
    - .github/workflows/batch-archive.yml
  modified:
    - .github/workflows/archive-cve.yml

key-decisions:
  - "workflow_call inputs mirror workflow_dispatch inputs exactly — inputs.cve_id works identically for both trigger types, requiring zero job-level changes"
  - "Commas treated as alternative separators alongside newlines for CSV-paste convenience"
  - "Invalid CVE ID lines silently dropped; batch job only errors if zero valid IDs remain after filtering"
  - "GITHUB_STEP_SUMMARY in batch job lists queued CVEs for run-level visibility"

patterns-established:
  - "Reusable workflow: add workflow_call block under on: with identical inputs to workflow_dispatch"
  - "Batch-to-single fan-out: parse job emits JSON array output, per-cve job consumes via fromJSON matrix and uses: local workflow path"

requirements-completed:
  - BATCH-01

# Metrics
duration: 2min
completed: 2026-03-28
---

# Phase 04 Plan 01: Batch Mode — Reusable Workflow and Batch Entrypoint Summary

**workflow_call trigger added to archive-cve.yml; batch-archive.yml created with newline-separated CVE ID input, validation, and per-CVE matrix fan-out via fail-fast: false reusable workflow call**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-03-28T22:41:15Z
- **Completed:** 2026-03-28T22:43:28Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Extended `archive-cve.yml` with `workflow_call` trigger — zero changes to any job sections, `inputs.cve_id` works identically for both trigger types
- Created `batch-archive.yml` with `workflow_dispatch` accepting a multi-line `cve_ids` input, a `batch` parse job, and a `per-cve` matrix job calling the reusable workflow
- CVE ID validation via `grep -E '^CVE-[0-9]{4}-[0-9]{4,}$'` silently drops invalid lines; `fail-fast: false` ensures one CVE's failure never blocks others

## Task Commits

Each task was committed atomically:

1. **Task 1: Add workflow_call trigger to archive-cve.yml** - `b7972e4` (feat)
2. **Task 2: Create batch-archive.yml with CVE list input and per-CVE matrix** - `4e0121c` (feat)

## Files Created/Modified

- `.github/workflows/archive-cve.yml` - Added `workflow_call` trigger block under `on:` with `inputs.cve_id` (string, required); all three jobs unchanged
- `.github/workflows/batch-archive.yml` - New batch entrypoint: parses/validates CVE list, emits JSON matrix, calls `archive-cve.yml` once per CVE

## Decisions Made

- `workflow_call` inputs are identical to `workflow_dispatch` inputs — `inputs.cve_id` works for both trigger types, so no job-level changes were needed
- Commas accepted as separator alongside newlines (CSV convenience for copy-paste from spreadsheets/lists)
- `GITHUB_STEP_SUMMARY` in batch job lists all queued CVEs so the run summary shows what was queued

## Deviations from Plan

None — plan executed exactly as written.

The worktree had only the Phase 1 version of `archive-cve.yml` (prepare job only). Resolved by writing the full Phase 3 file (from main branch) with the workflow_call trigger added, rather than patching the truncated worktree copy. Not a deviation — routine worktree initialization handling.

## Issues Encountered

- Worktree (`worktree-agent-ae09fc15` branch) contained only the Phase 1 version of `archive-cve.yml` (100 lines, prepare job only) rather than the Phase 3 version (206 lines, all three jobs). The file was rewritten from the main branch content with the workflow_call trigger added cleanly.
- `pyyaml` YAML 1.1 parses bare `on` as Python `True` — verification script used `wf[True]` instead of `wf['on']`.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Both workflow files are structurally valid YAML with correct trigger/job structure
- `archive-cve.yml` is now callable as a reusable workflow from `batch-archive.yml`
- Ready for Plan 04-02 (testing/validation of batch workflow behavior)

---
*Phase: 04-batch-mode*
*Completed: 2026-03-28*

## Self-Check: PASSED

- FOUND: `.github/workflows/archive-cve.yml`
- FOUND: `.github/workflows/batch-archive.yml`
- FOUND: `.planning/phases/04-batch-mode/04-01-SUMMARY.md`
- FOUND: commit `b7972e4` (Task 1)
- FOUND: commit `4e0121c` (Task 2)
