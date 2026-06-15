"""
Automated Daily Threat Report Generator (FR-4, US-06, US-07, US-08)
Reads JSON log files and produces an HTML + PDF report.
Run standalone: python reporter.py
Or scheduled via cron: 0 0 * * * cd /opt/honeypot && python reporter.py
"""

import json
import os
import glob
import yaml
from datetime import datetime, timezone, timedelta
from collections import Counter
from pathlib import Path

try:
    import plotly.graph_objects as go
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

with open("config.yaml") as f:
    CFG = yaml.safe_load(f)

LOG_DIR    = CFG["logging"]["log_dir"]
REPORT_DIR = CFG["reporting"]["output_dir"]
os.makedirs(REPORT_DIR, exist_ok=True)


def load_logs(date_str: str) -> list[dict]:
    """Load all log entries for a given date (YYYY-MM-DD)."""
    path = os.path.join(LOG_DIR, f"attempts_{date_str}.json")
    entries = []
    if os.path.exists(path):
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    return entries


def load_previous_days(n: int = 7) -> list[dict]:
    today = datetime.now(timezone.utc).date()
    entries = []
    for i in range(1, n + 1):
        d = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        entries.extend(load_logs(d))
    return entries


def generate_report(target_date: str | None = None):
    today     = datetime.now(timezone.utc)
    date_str  = target_date or today.strftime("%Y-%m-%d")
    entries   = load_logs(date_str)
    prev_entries = load_previous_days(7)

    total_today    = len(entries)
    total_prev_avg = len(prev_entries) / 7 if prev_entries else 0
    trend          = "↑" if total_today > total_prev_avg else ("↓" if total_today < total_prev_avg else "→")

    usernames = Counter(e["username"] for e in entries)
    passwords = Counter(e["password"] for e in entries)
    ips       = Counter(e["src_ip"] for e in entries)
    countries = Counter(
        (e.get("geo") or {}).get("country", "Unknown")
        for e in entries
    )

    top_users   = usernames.most_common(10)
    top_passes  = passwords.most_common(10)
    top_ips     = ips.most_common(10)
    top_countries = countries.most_common(10)

    # ── Daily trend series (last 8 days incl. today) ───────────────────────
    trend_data = []
    for i in range(7, -1, -1):
        d = (today.date() - timedelta(days=i)).strftime("%Y-%m-%d")
        trend_data.append({"date": d, "count": len(load_logs(d))})

    # ── Build HTML ─────────────────────────────────────────────────────────
    def table_rows(data):
        rows = ""
        for rank, (val, cnt) in enumerate(data, 1):
            rows += f"<tr><td>{rank}</td><td>{val}</td><td>{cnt}</td></tr>"
        return rows

    def trend_chart_js(trend_data):
        labels  = [d["date"] for d in trend_data]
        counts  = [d["count"] for d in trend_data]
        return f"""
        <canvas id=\"trendChart\" width=\"700\" height=\"200\"></canvas>
        <script src=\"https://cdn.jsdelivr.net/npm/chart.js\"></script>
        <script>
        new Chart(document.getElementById(\'trendChart\'), {{
          type: \'line\',
          data: {{
            labels: {json.dumps(labels)},
            datasets: [{{
              label: \'Attempts per day\',
              data: {json.dumps(counts)},
              borderColor: \'#e63946\',
              backgroundColor: \'rgba(230,57,70,0.1)\',
              fill: true,
              tension: 0.3
            }}]
          }},
          options: {{ plugins: {{ legend: {{ display: false }} }} }}
        }});
        </script>
        """

    html = f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\">
  <title>SSH Honeypot Daily Report — {date_str}</title>
  <style>
    body {{ font-family: 'Segoe UI', sans-serif; background:#1a1a2e; color:#e0e0e0; padding:2rem; }}
    h1   {{ color:#e63946; }}
    h2   {{ color:#a8dadc; border-bottom:1px solid #444; padding-bottom:.3rem; }}
    .metric-grid {{ display:flex; gap:1.5rem; margin:1rem 0; flex-wrap:wrap; }}
    .metric {{ background:#16213e; padding:1rem 1.5rem; border-radius:8px; min-width:160px; }}
    .metric .val {{ font-size:2.2rem; font-weight:bold; color:#e63946; }}
    .metric .label {{ font-size:.85rem; color:#888; }}
    table {{ border-collapse:collapse; width:100%; max-width:600px; }}
    th    {{ background:#16213e; padding:.5rem 1rem; text-align:left; color:#a8dadc; }}
    td    {{ padding:.4rem 1rem; border-bottom:1px solid #2a2a4a; }}
    .trend {{ font-size:1.4rem; }}
  </style>
</head>
<body>
  <h1>🍯 SSH Honeypot Daily Report</h1>
  <p>Date: <strong>{date_str}</strong> &nbsp;|&nbsp; Generated: {today.strftime('%Y-%m-%d %H:%M UTC')}</p>

  <h2>📊 Summary</h2>
  <div class=\"metric-grid\">
    <div class=\"metric\"><div class=\"val\">{total_today}</div><div class=\"label\">Total Attempts Today</div></div>
    <div class=\"metric\"><div class=\"val\">{total_prev_avg:.0f}</div><div class=\"label\">7-Day Daily Avg</div></div>
    <div class=\"metric\"><div class=\"val trend\">{trend}</div><div class=\"label\">vs. 7-Day Avg</div></div>
    <div class=\"metric\"><div class=\"val\">{len(ips)}</div><div class=\"label\">Unique IPs</div></div>
    <div class=\"metric\"><div class=\"val\">{len(countries)}</div><div class=\"label\">Countries</div></div>
  </div>

  <h2>📈 7-Day Trend</h2>
  {trend_chart_js(trend_data)}

  <h2>👤 Top 10 Usernames</h2>
  <table><tr><th>#</th><th>Username</th><th>Attempts</th></tr>{table_rows(top_users)}</table>

  <h2>🔑 Top 10 Passwords</h2>
  <table><tr><th>#</th><th>Password</th><th>Attempts</th></tr>{table_rows(top_passes)}</table>

  <h2>🌍 Top 10 Source IPs</h2>
  <table><tr><th>#</th><th>IP Address</th><th>Attempts</th></tr>{table_rows(top_ips)}</table>

  <h2>🗺 Geographic Breakdown</h2>
  <table><tr><th>#</th><th>Country</th><th>Attempts</th></tr>{table_rows(top_countries)}</table>

</body>
</html>
"""

    out_path = os.path.join(REPORT_DIR, f"report_{date_str}.html")
    with open(out_path, "w") as f:
        f.write(html)
    print(f"[reporter] HTML report saved: {out_path}")

    # ── Optional PDF via weasyprint ────────────────────────────────────────
    try:
        from weasyprint import HTML as WHTML
        pdf_path = os.path.join(REPORT_DIR, f"report_{date_str}.pdf")
        WHTML(filename=out_path).write_pdf(pdf_path)
        print(f"[reporter] PDF report saved: {pdf_path}")
    except ImportError:
        print("[reporter] weasyprint not installed — PDF skipped. Install with: pip install weasyprint")

    return out_path


if __name__ == "__main__":
    generate_report()
