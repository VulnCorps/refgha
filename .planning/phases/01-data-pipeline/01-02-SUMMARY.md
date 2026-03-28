---
phase: 01-data-pipeline
plan: 02
subsystem: infra
tags: [github-actions, bash, jq, matrix, cve]

# Dependency graph
requires:
  - phase: 01-data-pipeline-01
    provides: "workflow skeleton with fetch step storing RESPONSE and CVE_ID; placeholder extraction outputs"
provides:
  - "Null-safe jq URL extraction from .containers.cna.references"
  - "Empty reference guard that exits cleanly with step summary (PIPE-04)"
  - "fromJSON-compatible matrix JSON array of {index, url} objects (PIPE-03)"
  - "has_refs/ref_count/matrix outputs wired to prepare job outputs"
affects: [01-data-pipeline, archive-job, matrix-fan-out]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "null-safe jq extraction: (.containers.cna.references // []) | .[].url"
    - "printf '%s' instead of echo for piping URLS to avoid trailing newline phantom entry"
    - "grep -c . || echo 0 for safe non-empty line counting under set -e"
    - "jq -R -s with to_entries + tojson for fromJSON-compatible matrix serialization"
    - "exit 0 inside empty-ref guard for clean job success (no archive needed)"

key-files:
  created: []
  modified:
    - .github/workflows/archive-cve.yml

key-decisions:
  - "Use printf '%s' not echo to pipe URLS into jq/grep — avoids trailing newline creating phantom empty URL"
  - "tojson at end of jq pipeline produces single-line JSON string required for GITHUB_OUTPUT echo"
  - "exit 0 in zero-reference branch — job succeeds cleanly rather than failing when no URLs exist"

patterns-established:
  - "Pattern: null-safe CVE reference extraction with // [] guard"
  - "Pattern: empty matrix guard with REF_COUNT check before any matrix output"
  - "Pattern: embedded numeric index in matrix objects (not derived from URL)"

requirements-completed: [PIPE-03, PIPE-04]

# Metrics
duration: 2min
completed: 2026-03-28
---

# Phase 01 Plan 02: URL Extraction, Empty Guard, and Matrix Construction Summary

**Null-safe jq URL extraction from CVE references field with fromJSON-compatible matrix output and clean zero-reference guard (PIPE-03, PIPE-04)**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-03-28T20:47:14Z
- **Completed:** 2026-03-28T20:49:00Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments

- Replaced placeholder extraction block with complete implementation
- Extracts reference URLs using null-safe jq path — handles reserved/rejected CVEs that lack `.containers.cna.references`
- Guards against empty matrix GHA error: REF_COUNT check exits cleanly with step summary when zero references found
- Builds fromJSON-compatible matrix JSON array of `{index, url}` objects with embedded numeric index

## Task Commits

Each task was committed atomically:

1. **Task 1: Replace placeholder with complete extraction, guard, matrix output, and summary** - `c519764` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified

- `.github/workflows/archive-cve.yml` - Replaced 7-line placeholder with 44-line complete extraction implementation

## Decisions Made

- Used `printf '%s'` rather than `echo` to pipe URLS into grep and jq — avoids a trailing newline adding a phantom empty URL that would inflate REF_COUNT
- Used `tojson` at the end of the jq pipeline to produce a single-line JSON string required for `echo "matrix=..." >> "$GITHUB_OUTPUT"` (multi-line output breaks GITHUB_OUTPUT)
- `exit 0` inside the REF_COUNT == 0 branch is deliberate — the prepare job succeeds cleanly when no URLs exist (archiving simply not needed)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- The prepare job is now fully functional for Phase 1 pipeline
- Plan 03 can wire the archive and collect jobs using `needs.prepare.outputs.has_refs` and `fromJSON(needs.prepare.outputs.matrix)`
- The matrix output format `[{"index": 0, "url": "..."}, ...]` is ready for consumption by downstream matrix jobs

---
*Phase: 01-data-pipeline*
*Completed: 2026-03-28*

## Self-Check: PASSED

- FOUND: .github/workflows/archive-cve.yml
- FOUND: .planning/phases/01-data-pipeline/01-02-SUMMARY.md
- FOUND: commit c519764
