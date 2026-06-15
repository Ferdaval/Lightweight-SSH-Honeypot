# 🍯 Lightweight SSH Honeypot

A production-ready SSH honeypot built in Python that captures attacker credentials,
enriches with geolocation/reputation data, fires real-time alerts, and generates
automated daily HTML/PDF threat reports.

---

## Architecture

```
┌─────────────────────────────────────────────┐
│              SSH Honeypot System             │
│                                              │
│  ┌──────────┐   ┌────────────┐  ┌─────────┐ │
│  │honeypot  │──▶│enrichment  │  │alerting │ │
│  │.py       │   │.py         │  │.py      │ │
│  │(FR-1,FR-2│   │(FR-3)      │  │(FR-5)   │ │
│  └──────────┘   └────────────┘  └─────────┘ │
│       │                              │       │
│       ▼                              ▼       │
│  ┌──────────┐                 ┌──────────┐  │
│  │logs/     │                 │Webhook / │  │
│  │YYYY-MM-DD│                 │Email     │  │
│  │.json     │                 └──────────┘  │
│  └────┬─────┘                               │
│       │                                     │
│       ▼                                     │
│  ┌──────────┐                               │
│  │reporter  │──▶ reports/report_YYYY.html   │
│  │.py (FR-4)│──▶ reports/report_YYYY.pdf    │
│  └──────────┘                               │
└─────────────────────────────────────────────┘
```

---

## Quick Start (Docker)

```bash
# 1. Clone / copy project files
git clone <your-repo> ssh-honeypot && cd ssh-honeypot

# 2. One-command setup
chmod +x setup.sh && ./setup.sh

# 3. Watch logs in real time
docker logs -f ssh_honeypot
```

---

## Manual Setup (virtualenv)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Generate RSA host key
ssh-keygen -t rsa -b 4096 -f keys/server.key -N ""

# Start
python main.py
```

---

## Configuration (`config.yaml`)

| Key | Default | Description |
|-----|---------|-------------|
| `server.port` | `2222` | Listening port (use 22 in prod) |
| `server.banner` | OpenSSH 8.2 | Fake SSH banner |
| `alerting.threshold` | `10` | Attempts before alert |
| `alerting.window_seconds` | `60` | Alert time window |
| `reporting.schedule` | `"00:00"` | Daily report time (UTC) |
| `geo_enrichment.abuseipdb_api_key` | `""` | Optional AbuseIPDB key |

---

## Log Format (JSON — FR-2.1)

```json
{
  "timestamp":      "2026-06-15T20:00:00+00:00",
  "src_ip":         "198.51.100.42",
  "username":       "root",
  "password":       "admin123",
  "client_version": "SSH-2.0-libssh2_1.10.0",
  "geo": {
    "country":     "China",
    "city":        "Beijing",
    "asn":         "AS4134 Chinanet",
    "abuse_score": 87
  }
}
```

---

## Generate Report Manually

```bash
python reporter.py
# Output: reports/report_YYYY-MM-DD.html
#         reports/report_YYYY-MM-DD.pdf  (requires weasyprint)
```

---

## Production Deployment Notes

- Change `ports` to `"22:2222"` in `docker-compose.yml` to capture real port 22 traffic
- Move real SSH daemon to a non-standard port (e.g., 2222 → 22222)
- Set `CAP_NET_BIND_SERVICE` if running without Docker on port 22:
  `sudo setcap cap_net_bind_service=+ep $(which python3)`
- Ensure the honeypot container has **no access** to production network (NFR-5, US-12)
- Store AbuseIPDB key in a `.env` file, never in `config.yaml` committed to git

---

## Legal & Ethical Notice

This tool is intended for **research, education, and threat intelligence** on
infrastructure you own or have explicit permission to monitor. Do not deploy
on networks you do not own. Captured credential data may be subject to GDPR
(Art. 5 & 32) — ensure appropriate data minimization and access controls.

---

## Requirements Traceability

| File | Requirements Covered |
|------|----------------------|
| `honeypot.py` | FR-1, FR-2, FR-5, NFR-1, NFR-2, NFR-4 |
| `enrichment.py` | FR-3 |
| `alerting.py` | FR-5, US-09, US-10 |
| `reporter.py` | FR-4, US-06, US-07, US-08 |
| `scheduler.py` | FR-4.1, US-06 |
| `config.yaml` | FR-1.4, FR-5.1, US-02, US-10 |
| `Dockerfile` | NFR-4, NFR-6, US-11, US-12 |
| `docker-compose.yml` | FR-6, NFR-2, US-11, US-12 |
