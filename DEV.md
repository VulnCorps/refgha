# Local Development

## Prerequisites

```bash
brew install act
```

## What works locally

The `prepare` job (fetch CVE JSON + extract URLs + build matrix) runs fine:

```bash
act workflow_dispatch \
  -W .github/workflows/archive-cve.yml \
  --input cve_id=CVE-2025-29002 \
  -j prepare
```

Batch input:
```bash
act workflow_dispatch \
  -W .github/workflows/batch-archive.yml \
  --input cve_ids="CVE-2025-29002
CVE-2024-3094"
```

## What doesn't work locally

The `archive` and `collect` jobs require Docker-in-Docker (ArchiveBox runs inside a container on the runner). This doesn't work on macOS with act. Test those on real GHA runners.

## Stats page

Requires AWS credentials with read access to `archiver-demo-v1-public`:

```bash
AWS_PROFILE=vulncorps python3 scripts/generate-stats.py
# writes docs/stats.html
```
