---
phase: 01-data-pipeline
plan: "01"
subsystem: infra
tags: [github-actions, workflow_dispatch, bash, curl, cveproject]

requires: []

provides:
  - GitHub Actions workflow file with workflow_dispatch trigger accepting a CVE ID input
  - prepare job scaffold with job-level outputs block (matrix, has_refs, ref_count)
  - CVE ID format validation via regex before any network call
  - GitHub raw content URL construction with 1000-block numXXX path segment
  - curl fetch with --fail-with-body for clean HTTP error handling
  - GITHUB_STEP_SUMMARY output confirming fetch

affects: [01-02, 01-03]

tech-stack:
  added: [github-actions, bash, curl]
  patterns:
    - "workflow_dispatch with required string input for manual CVE triggering"
    - "Job-level outputs block declaring step outputs for downstream jobs"
    - "set -euo pipefail at top of every run step"
    - "GITHUB_OUTPUT env file syntax (not deprecated ::set-output::)"
    - "curl --fail-with-body for clean 4xx/5xx error propagation"
    - "numXXX 1000-block: integer-divide CVE number by 1000, append 'xxx'"

key-files:
  created:
    - .github/workflows/archive-cve.yml
  modified: []

key-decisions:
  - "Use inputs.cve_id (not github.event.inputs.cve_id) per modern GHA pattern"
  - "Placeholder extraction outputs in this plan; replaced by plan 02"
  - "sed-based leading-zero strip for NUM_INT per plan spec (produces 0 for all-zero input)"

patterns-established:
  - "Workflow file: single archive-cve.yml for all phases (prepare, archive, collect added incrementally)"
  - "CVE URL construction: YEAR from field 2, NUM from field 3 of CVE-YYYY-NNNN, BLOCK=NUM/1000, path={YEAR}/{BLOCK}xxx/CVE-{YEAR}-{NUM}.json"

requirements-completed: [PIPE-01, PIPE-02]

duration: 2min
completed: 2026-03-28
---

# Phase 01 Plan 01: Data Pipeline Trigger and Fetch Summary

**GitHub Actions workflow with workflow_dispatch CVE ID input, format validation, and GitHub raw content fetch using 1000-block URL construction**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-03-28T20:44:22Z
- **Completed:** 2026-03-28T20:46:00Z
- **Tasks:** 1 of 1
- **Files modified:** 1

## Accomplishments

- Created `.github/workflows/archive-cve.yml` with `workflow_dispatch` trigger accepting `cve_id` input
- Added CVE ID format validation (`^CVE-[0-9]{4}-[0-9]{4,}$`) before any network call with `::error::` annotation
- Implemented GitHub raw content URL construction: year + numXXX (1000-block via integer division) + CVE-{YEAR}-{NUM}.json
- Fetch via `curl --fail-with-body --silent --show-error` — exits non-zero on HTTP 4xx/5xx
- Placeholder extraction outputs (has_refs, matrix, ref_count) scaffolded for plan 02 to replace
- Job-level `outputs:` block with `steps.extract.outputs.*` references for downstream jobs

## Task Commits

1. **Task 1: Create workflow file with workflow_dispatch trigger and prepare job scaffold** - `e905ae2` (feat)

**Plan metadata:** (pending final commit)

## Files Created/Modified

- `.github/workflows/archive-cve.yml` - Complete workflow definition: trigger, prepare job scaffold, CVE validation, URL construction, fetch, placeholder outputs, step summary

## Decisions Made

- Followed plan spec exactly for NUM_INT stripping: `sed 's/^0*//'` + `grep -E '^[0-9]+$' || echo "0"` — handles all-zeros edge case (CVE-YYYY-0000 → BLOCK=0 → 0xxx)
- Placeholder extraction section intentionally left incomplete — plan 02 Task 1 replaces it with real jq extraction + empty-reference guard

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 01-01 provides the workflow trigger and fetch foundation
- Plan 01-02 (extraction + matrix output) can now build on the fetch step by replacing placeholder outputs with real jq extraction logic
- No blockers for plan 01-02

---
*Phase: 01-data-pipeline*
*Completed: 2026-03-28*

## Self-Check: PASSED

- FOUND: `.github/workflows/archive-cve.yml`
- FOUND: `.planning/phases/01-data-pipeline/01-01-SUMMARY.md`
- FOUND: commit `e905ae2`
