#!/usr/bin/env python3
"""
Generate docs/stats.html — interactive stats page from S3 archive data.
Run: AWS_PROFILE=vulncorps python3 scripts/generate-stats.py
"""

import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone

BUCKET = "archiver-demo-v1-public"
OUTPUT = "docs/stats.html"
TS_RE = re.compile(r"/(\d{8}-\d{6})/")


def aws(*args):
    cmd = ["aws"] + list(args)
    env = os.environ.copy()
    r = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if r.returncode != 0:
        print(f"AWS error: {r.stderr}", file=sys.stderr)
        sys.exit(1)
    return r.stdout


def load_schedule():
    print("Downloading schedule.json ...", flush=True)
    raw = aws("s3", "cp", f"s3://{BUCKET}/v2/schedule.json", "-")
    return json.loads(raw)["entries"]


def stream_s3_listing():
    """Stream 'aws s3 ls --recursive' and yield screenshot.png keys."""
    cmd = ["aws", "s3", "ls", f"s3://{BUCKET}/v2/", "--recursive"]
    env = os.environ.copy()
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True, env=env)
    count = 0
    for line in proc.stdout:
        # format: 2026-03-29 08:45:20     123456 v2/domain/path/timestamp/file
        parts = line.split(None, 3)
        if len(parts) != 4:
            continue
        key = parts[3].rstrip()
        if not key.endswith("screenshot.png"):
            continue
        yield key
        count += 1
        if count % 2000 == 0:
            print(f"  ... {count} snapshots scanned", flush=True)
    proc.wait()
    print(f"  Total snapshots: {count}", flush=True)


def parse_domain(key):
    # v2/<domain>/[path.../]<YYYYMMDD-HHMMSS>/screenshot.png
    parts = key.split("/")
    return parts[1] if len(parts) > 2 else "unknown"


def parse_date(key):
    m = TS_RE.search(key)
    if m:
        ts = m.group(1)
        return f"{ts[:4]}-{ts[4:6]}-{ts[6:8]}"
    return None


def main():
    entries = load_schedule()

    cves_per_day = defaultdict(int)
    cve_year_counts = defaultdict(int)
    interval_buckets = defaultdict(int)

    for e in entries:
        fa = e.get("first_archived", "")
        if fa:
            cves_per_day[fa[:10]] += 1
        m = re.match(r"CVE-(\d{4})-", e.get("cve_id", ""))
        if m:
            cve_year_counts[m.group(1)] += 1
        interval_buckets[len(e.get("completed_intervals", []))] += 1

    print("Streaming S3 listing ...", flush=True)
    domain_counts = defaultdict(int)
    snapshots_per_day = defaultdict(int)

    for key in stream_s3_listing():
        domain_counts[parse_domain(key)] += 1
        d = parse_date(key)
        if d:
            snapshots_per_day[d] += 1

    snap_days = sorted(snapshots_per_day)
    cve_days = sorted(cves_per_day)
    top_domains = sorted(domain_counts.items(), key=lambda x: -x[1])[:25]
    years = sorted(cve_year_counts)

    interval_labels = [
        "not yet archived",
        "initial only",
        "initial + 3-day",
        "initial + 3 + 10-day",
        "initial + 3 + 10 + 30-day",
    ]

    data = {
        "totals": {
            "cves": len(entries),
            "snapshots": sum(domain_counts.values()),
            "domains": len(domain_counts),
            "generated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        },
        "snap_days": snap_days,
        "snap_vals": [snapshots_per_day[d] for d in snap_days],
        "cve_days": cve_days,
        "cve_vals": [cves_per_day[d] for d in cve_days],
        "domain_labels": [x[0] for x in top_domains],
        "domain_vals": [x[1] for x in top_domains],
        "years": years,
        "year_vals": [cve_year_counts[y] for y in years],
        "interval_labels": interval_labels,
        "interval_vals": [interval_buckets.get(i, 0) for i in range(5)],
    }

    print(f"Writing {OUTPUT} ...", flush=True)
    write_html(data)
    print("Done.", flush=True)


def write_html(d):
    j = json.dumps(d)
    t = d["totals"]
    avg = t["snapshots"] // max(t["cves"], 1)
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CVE Archive — Stats</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"></script>
<style>
  :root {{
    --bg: #0f1117; --surface: #1a1d27; --border: #2a2d3a;
    --text: #e2e8f0; --muted: #8892a4;
    --c1: #6366f1; --c2: #22d3ee; --c3: #f59e0b; --c4: #10b981; --c5: #ef4444;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: var(--bg); color: var(--text); font-family: system-ui, sans-serif; padding: 2rem; }}
  h1 {{ font-size: 1.5rem; margin-bottom: .25rem; }}
  .meta {{ color: var(--muted); font-size: .85rem; margin-bottom: 2rem; }}
  .meta a {{ color: var(--c2); text-decoration: none; }}
  .stats-row {{ display: flex; gap: 1rem; flex-wrap: wrap; margin-bottom: 2.5rem; }}
  .stat-card {{ background: var(--surface); border: 1px solid var(--border); border-radius: 8px;
                padding: 1.25rem 1.75rem; flex: 1; min-width: 140px; }}
  .stat-card .n {{ font-size: 2rem; font-weight: 700; }}
  .stat-card .l {{ font-size: .75rem; color: var(--muted); text-transform: uppercase;
                   letter-spacing: .05em; margin-top: .2rem; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(520px, 1fr)); gap: 1.5rem; }}
  .chart-card {{ background: var(--surface); border: 1px solid var(--border); border-radius: 8px;
                 padding: 1.5rem; }}
  .chart-card h2 {{ font-size: .8rem; color: var(--muted); margin-bottom: 1.25rem;
                    text-transform: uppercase; letter-spacing: .06em; }}
  .chart-card.wide {{ grid-column: 1 / -1; }}
  canvas {{ max-height: 300px; }}
</style>
</head>
<body>
<h1>CVE Reference Archive — Stats</h1>
<p class="meta">Generated {t["generated"]} &nbsp;·&nbsp; <a href="/">← Archive</a></p>

<div class="stats-row">
  <div class="stat-card"><div class="n">{t["cves"]:,}</div><div class="l">CVEs</div></div>
  <div class="stat-card"><div class="n">{t["snapshots"]:,}</div><div class="l">Snapshots</div></div>
  <div class="stat-card"><div class="n">{t["domains"]:,}</div><div class="l">Domains</div></div>
  <div class="stat-card"><div class="n">{avg}</div><div class="l">Avg snapshots / CVE</div></div>
</div>

<div class="grid">

  <div class="chart-card wide">
    <h2>Snapshots archived per day</h2>
    <canvas id="snapTimeline"></canvas>
  </div>

  <div class="chart-card wide">
    <h2>New CVEs added per day</h2>
    <canvas id="cveTimeline"></canvas>
  </div>

  <div class="chart-card">
    <h2>Top 25 domains by snapshot count</h2>
    <canvas id="domains"></canvas>
  </div>

  <div class="chart-card">
    <h2>CVEs by publication year</h2>
    <canvas id="cveYears"></canvas>
  </div>

  <div class="chart-card">
    <h2>Re-archive interval coverage</h2>
    <canvas id="intervals"></canvas>
  </div>

</div>
<script>
const DATA = {j};
const GRID = {{ color: "rgba(255,255,255,.06)" }};
const TICK = {{ color: "#8892a4", font: {{ size: 11 }} }};
const TIP  = {{ backgroundColor: "#1a1d27", borderColor: "#2a2d3a", borderWidth: 1,
                titleColor: "#e2e8f0", bodyColor: "#8892a4" }};

new Chart(document.getElementById("snapTimeline"), {{
  type: "bar",
  data: {{
    labels: DATA.snap_days,
    datasets: [{{ label: "Snapshots", data: DATA.snap_vals,
      backgroundColor: "rgba(99,102,241,.75)", borderRadius: 2, borderSkipped: false }}]
  }},
  options: {{ responsive: true,
    plugins: {{ legend: {{ display: false }}, tooltip: TIP }},
    scales: {{ x: {{ grid: GRID, ticks: {{ ...TICK, maxTicksLimit: 14 }} }}, y: {{ grid: GRID, ticks: TICK }} }}
  }}
}});

new Chart(document.getElementById("cveTimeline"), {{
  type: "bar",
  data: {{
    labels: DATA.cve_days,
    datasets: [{{ label: "CVEs", data: DATA.cve_vals,
      backgroundColor: "rgba(34,211,238,.75)", borderRadius: 2, borderSkipped: false }}]
  }},
  options: {{ responsive: true,
    plugins: {{ legend: {{ display: false }}, tooltip: TIP }},
    scales: {{ x: {{ grid: GRID, ticks: {{ ...TICK, maxTicksLimit: 14 }} }}, y: {{ grid: GRID, ticks: TICK }} }}
  }}
}});

new Chart(document.getElementById("domains"), {{
  type: "bar",
  data: {{
    labels: DATA.domain_labels,
    datasets: [{{ label: "Snapshots", data: DATA.domain_vals,
      backgroundColor: "rgba(245,158,11,.75)", borderRadius: 3, borderSkipped: false }}]
  }},
  options: {{ indexAxis: "y", responsive: true,
    plugins: {{ legend: {{ display: false }}, tooltip: TIP }},
    scales: {{ x: {{ grid: GRID, ticks: TICK }},
               y: {{ grid: {{ display: false }}, ticks: {{ ...TICK, font: {{ size: 10 }} }} }} }}
  }}
}});

new Chart(document.getElementById("cveYears"), {{
  type: "bar",
  data: {{
    labels: DATA.years,
    datasets: [{{ label: "CVEs", data: DATA.year_vals,
      backgroundColor: "rgba(16,185,129,.75)", borderRadius: 3, borderSkipped: false }}]
  }},
  options: {{ responsive: true,
    plugins: {{ legend: {{ display: false }}, tooltip: TIP }},
    scales: {{ x: {{ grid: GRID, ticks: {{ ...TICK, maxRotation: 45 }} }}, y: {{ grid: GRID, ticks: TICK }} }}
  }}
}});

new Chart(document.getElementById("intervals"), {{
  type: "doughnut",
  data: {{
    labels: DATA.interval_labels,
    datasets: [{{ data: DATA.interval_vals,
      backgroundColor: ["rgba(99,102,241,.85)","rgba(34,211,238,.85)",
        "rgba(245,158,11,.85)","rgba(16,185,129,.85)","rgba(239,68,68,.85)"],
      borderColor: "#1a1d27", borderWidth: 2 }}]
  }},
  options: {{ responsive: true,
    plugins: {{
      legend: {{ position: "right", labels: {{ color: "#8892a4", font: {{ size: 11 }} }} }},
      tooltip: TIP
    }}
  }}
}});
</script>
</body>
</html>
"""
    with open(OUTPUT, "w") as f:
        f.write(html)


if __name__ == "__main__":
    main()
