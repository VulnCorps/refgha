# refgha — CVE Reference Archiver

Monitors [CVEProject/cvelistV5](https://github.com/CVEProject/cvelistV5) for new CVEs, archives every reference URL with ArchiveBox (PDF + screenshot + WARC), and serves a static browse/search UI.

**Browse:** [cvearchiver.com](https://cvearchiver.com) · **Stats:** [https://cvearchiver.com/stats.html](https://cvearchiver.com/stats.html)

---

## Architecture

```mermaid
flowchart TD
    CVE[(cvelistV5
 GitHub)]

    CVE -->|hourly :00| crawl

    subgraph crawl ["crawl-cves.yml"]
        C1[walk commits
 since last SHA]
        C2[filter CVEs
 with references]
        C3[cap 15/run
 spillover → .state/]
        C1 --> C2 --> C3
    end

    C3 -->|per CVE| archive

    subgraph rearchive ["rearchive.yml  (hourly :15)"]
        R1[read schedule.json]
        R2[find CVEs due
 3 · 10 · 30 · 90 days]
        R1 --> R2
    end

    R2 -->|per CVE| archive

    subgraph backfill ["backfill-cves.yml  (every 2h :45, idle-only)"]
        B1[walk cvelistV5
 newest → oldest
 from .state/ cursor]
        B2[skip already-archived
 cap 10/run]
        B1 --> B2
    end

    B2 -->|per CVE| archive

    subgraph archive ["archive-cve.yml"]
        direction LR
        P[prepare
 fetch CVE JSON
 extract URLs
 build matrix]
        A["archive  ⟨parallel matrix⟩
 ArchiveBox Docker
  (one URL each)
 PDF · PNG · WARC → S3"]
        K[collect
 bundle artifacts
 write index → S3]
        P --> A --> K
    end

    K -->|writes| S3[(S3
 v2/…)]

    S3 -->|hourly :30| site
    S3 -->|nightly 02:00| stats

    subgraph site ["generate-site.yml"]
        G1[list S3
 read CVE indexes]
        G2[write docs/data/]
        G1 --> G2
    end

    subgraph stats ["generate-stats.yml"]
        S2[stream S3 listing
 read schedule.json]
        S3b[write docs/stats.html]
        S2 --> S3b
    end

    G2 -->|git commit| Pages([GitHub Pages])
    S3b -->|git commit| Pages
```

---

## Storage

```
S3: archiver-demo-v1-public/v2/
├── <domain>/<path>/<YYYYMMDD-HHMMSS>/
│   ├── output.pdf
│   ├── screenshot.png
│   └── warc.tgz
├── index/<CVE-ID>.json     # per-CVE reference list + snapshot URLs
├── index.json              # global URL index
└── schedule.json           # re-archive ledger (first_archived, completed_intervals)

GitHub Pages: docs/
├── index.html              # SPA — browse by domain or CVE
├── stats.html              # charts (nightly, generated from S3)
└── data/
    ├── manifest.json
    ├── cves/<CVE-ID>.json
    └── domains/<domain>.json
```

---

## Workflows

| Workflow             | Trigger                  | Purpose                               |
| -------------------- | ------------------------ | ------------------------------------- |
| `archive-cve.yml`    | manual / `workflow_call` | Archive all refs for one CVE          |
| `batch-archive.yml`  | manual                   | Archive a list of CVEs                |
| `crawl-cves.yml`     | hourly `:00`             | Discover and queue new CVEs           |
| `rearchive.yml`      | hourly `:15`             | Re-archive on 3/10/30/90-day schedule |
| `backfill-cves.yml`  | every 2 h `:45`          | Backfill pre-tailing CVEs, newest first (only when pipeline is idle) |
| `generate-site.yml`  | hourly `:30`             | Rebuild static site data from S3      |
| `generate-stats.yml` | nightly `02:00`          | Rebuild stats page from S3            |

**Backfill:** Tailing began circa March 2026, so older CVEs were never archived. `backfill-cves.yml` walks cvelistV5 in reverse chronological order (CVE year/number descending) from a cursor in `.state/backfill-cursor`, skipping anything already in the `schedule.json` ledger or the crawler's spillover queue. It defers itself whenever a crawl / re-archive / archive run is active, archives at most 10 CVEs per cycle, and registers backfilled CVEs with all re-archive intervals pre-completed so historical content isn't re-snapshotted. The cursor becomes `DONE` once it reaches 1999.

**Manual trigger — single CVE:**

```
Actions → archive-cve → Run workflow → cve_id: CVE-2021-44228
```

**Manual trigger — batch:**

```
Actions → batch-archive → Run workflow → cve_ids:
CVE-2021-44228
CVE-2022-0001
```

---

## Stack

| Layer         | Tech                                        |
| ------------- | ------------------------------------------- |
| Orchestration | GitHub Actions (ubuntu-latest)              |
| CVE source    | CVEProject/cvelistV5 via GitHub raw         |
| Archiving     | ArchiveBox Docker, one-shot per URL         |
| Scripting     | Bash + `jq` + `curl`                        |
| Site gen      | Python 3 + Chart.js                         |
| Storage       | AWS S3 + GitHub Pages                       |
| Local dev     | [nektos/act](https://github.com/nektos/act) |
