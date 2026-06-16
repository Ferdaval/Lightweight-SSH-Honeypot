
# act as Requirement engineer and write requirements and userstories for the idea i have :

Lightweight SSH Honeypot: Create a fake server designed to look vulnerable. Have it log unauthorized login attempts (recording the usernames, passwords, and origin IPs attackers try to use) and generate automated daily threat reports.

Here is a complete Requirements Engineering document for your **Lightweight SSH Honeypot** project, written with formal RE structure including stakeholder roles, functional/non-functional requirements, and Agile user stories.

***

# Lightweight SSH Honeypot — Requirements Specification

## Stakeholders \& Actors

Before defining requirements, it's essential to identify who interacts with the system:[^1]


| Actor | Role |
| :-- | :-- |
| **Security Analyst** | Reviews logs, reads threat reports, tunes alert thresholds |
| **System Administrator** | Deploys, configures, and maintains the honeypot |
| **Threat Intelligence Consumer** | Uses daily reports for strategic security decisions |
| **Attacker (External)** | Interacts with the honeypot (adversarial actor, not a user) |


***

## System Overview

The system is a **lightweight, low-interaction SSH honeypot** that emulates a vulnerable SSH server on port 22, captures unauthorized login attempts (username, password, source IP, timestamp), and produces automated daily threat intelligence reports.[^2]

***

## Functional Requirements

### FR-1: SSH Service Emulation

- **FR-1.1** — The system SHALL listen on TCP port 22 and present a realistic SSH banner (e.g., OpenSSH version string) to deceive automated scanners.[^3]
- **FR-1.2** — The system SHALL accept incoming SSH connection requests without granting real shell access.
- **FR-1.3** — The system SHALL simulate authentication failure responses after all login attempts to appear as a real but hardened server.[^4]
- **FR-1.4** — The system SHALL support configurable fake OS/version fingerprinting to evade Shodan/Nmap honeypot detection.[^5]


### FR-2: Attack Logging

- **FR-2.1** — The system SHALL log every authentication attempt with the following fields:[^6]
    - Source IP address
    - Attempted username
    - Attempted password
    - Timestamp (UTC, ISO 8601 format)
    - SSH client version/fingerprint
    - Connection duration
- **FR-2.2** — Logs SHALL be stored in a structured format (JSON or CSV) to enable downstream processing.[^5]
- **FR-2.3** — The system SHALL support log rotation to prevent unbounded disk growth.
- **FR-2.4** — The system SHALL write logs to an isolated output directory not accessible via the honeypot's simulated filesystem.[^7]


### FR-3: IP Geolocation \& Enrichment

- **FR-3.1** — The system SHALL enrich each logged IP with geolocation data (country, city, ASN) using a local or API-based GeoIP database.
- **FR-3.2** — The system SHALL flag IPs appearing on public threat intelligence blocklists (e.g., AbuseIPDB, Shodan).[^3]


### FR-4: Automated Daily Threat Reports

- **FR-4.1** — The system SHALL generate a daily report automatically at a configurable time (default: 00:00 UTC).[^3]
- **FR-4.2** — Each report SHALL include:
    - Total login attempts in the past 24 hours
    - Top 10 most-used usernames
    - Top 10 most-used passwords
    - Top 10 attacking source IPs with geolocation
    - Geographic heatmap or country frequency table
    - Trend comparison vs. the previous day
- **FR-4.3** — Reports SHALL be exportable in at least two formats: PDF and HTML.[^8]
- **FR-4.4** — The system SHALL optionally email or push-notify the Security Analyst upon report generation.


### FR-5: Real-Time Alerting

- **FR-5.1** — The system SHALL trigger an alert when a single IP exceeds a configurable connection threshold within a time window (default: 10 attempts / 60 seconds).[^2]
- **FR-5.2** — Alerts SHALL be deliverable via webhook (Slack/Discord), email, or log entry.[^8]


### FR-6: Network Isolation \& Safety

- **FR-6.1** — The honeypot SHALL be deployed in a network-isolated environment (VLAN or VM) separated from production systems.[^3]
- **FR-6.2** — The system SHALL restrict outbound traffic from the honeypot process to only logging endpoints and report delivery services.[^3]
- **FR-6.3** — The system SHALL impose CPU and memory usage caps to prevent resource abuse if the process is manipulated.[^3]

***

## Non-Functional Requirements

| ID | Category | Requirement |
| :-- | :-- | :-- |
| NFR-1 | Performance | The system SHALL handle ≥ 500 concurrent connection attempts without dropping logs [^2] |
| NFR-2 | Lightweight | Total memory footprint SHALL remain under 128 MB at idle [^4] |
| NFR-3 | Reliability | Log writes SHALL be atomic; no partial entries upon crash or SIGKILL |
| NFR-4 | Security | The honeypot process SHALL run as a non-root, unprivileged user via capability binding [^7] |
| NFR-5 | Privacy/Legal | Captured passwords SHALL be stored hashed or encrypted at rest; raw values accessible only to authorized roles [^9] |
| NFR-6 | Portability | The system SHALL run on any Linux distribution via Docker or a single Python virtualenv |
| NFR-7 | Auditability | All system configuration changes SHALL be version-controlled and logged with timestamps |


***

## User Stories

### Epic 1: Honeypot Deception Layer

**US-01**
> *As a **Security Analyst**, I want the honeypot to present a convincing SSH banner and fake OS fingerprint, so that automated attack tools and skilled attackers do not immediately recognize it as a trap.*

**Acceptance Criteria:**

- SSH banner is configurable (e.g., `SSH-2.0-OpenSSH_8.2p1 Ubuntu-4ubuntu0.5`)
- Nmap OS detection returns the configured fake OS
- No real shell is ever granted regardless of credentials used

***

**US-02**
> *As a **System Administrator**, I want to configure which port(s) the honeypot listens on, so that I can deploy it on port 22 while running my real SSH daemon on a non-standard port.*

**Acceptance Criteria:**

- Port is configurable via a `.env` or `config.yaml` file
- Honeypot starts successfully with `--port 22` without requiring root if capability binding is used
- A warning is logged if the real SSH service is detected on the same port

***

### Epic 2: Attack Capture \& Logging

**US-03**
> *As a **Security Analyst**, I want every login attempt to be logged with username, password, IP, and timestamp, so that I can analyze attacker credential patterns over time.*

**Acceptance Criteria:**

- Each attempt produces a JSON log entry with all 6 fields from FR-2.1
- Logs are flushed to disk within 500ms of the event
- Log files are rotated daily with date-stamped filenames

***

**US-04**
> *As a **Threat Intelligence Consumer**, I want source IPs to be enriched with geolocation and threat reputation data, so that I can quickly identify high-risk origins without manual lookups.*

**Acceptance Criteria:**

- Each log entry includes `country`, `city`, `ASN`, and `abuse_confidence_score`
- Enrichment occurs asynchronously and does not block connection logging
- If GeoIP lookup fails, the entry is still logged with `geo: null`

***

**US-05**
> *As a **System Administrator**, I want logs stored in an isolated, append-only directory, so that even if the honeypot process is exploited, logs cannot be tampered with.*

**Acceptance Criteria:**

- Log directory permissions are `chmod 750` owned by a dedicated `honeypot` user
- The honeypot process has write-only access to the log directory (no read or delete)
- Log integrity is verified at startup using a checksum manifest

***

### Epic 3: Automated Reporting

**US-06**
> *As a **Security Analyst**, I want a daily automated report delivered every morning, so that I can review the previous night's attack activity without manually querying logs.*

**Acceptance Criteria:**

- Report is generated automatically at the configured time via a cron job or internal scheduler
- Report includes all fields listed in FR-4.2
- Report is saved locally and optionally emailed as a PDF attachment

***

**US-07**
> *As a **Threat Intelligence Consumer**, I want the daily report to include a geographic breakdown of attacks, so that I can identify which countries or regions are most actively targeting my infrastructure.*

**Acceptance Criteria:**

- Report includes a table of top 10 attacking countries with attempt counts and percentages
- A visual heatmap or bar chart is embedded in the HTML report
- Country data is sourced from the enriched GeoIP logs

***

**US-08**
> *As a **Security Analyst**, I want day-over-day trend data in each report, so that I can detect spikes or campaigns that emerge over multiple days.*

**Acceptance Criteria:**

- Report compares today's total attempts vs. the prior 7-day average
- A trend indicator (↑ / ↓ / →) is shown next to each metric
- A time-series chart of daily attempt volume is included in HTML format

***

### Epic 4: Alerting

**US-09**
> *As a **Security Analyst**, I want to receive a real-time alert when a single IP makes more than 10 login attempts within 60 seconds, so that I can investigate active brute-force campaigns immediately.*

**Acceptance Criteria:**

- Alert fires within 5 seconds of threshold being crossed[^8]
- Alert includes: source IP, attempt count, time window, and top credentials tried
- Alert delivery method (webhook/email) is configurable without code changes

***

**US-10**
> *As a **System Administrator**, I want to configure alert thresholds via a config file, so that I can tune sensitivity based on the noise level of my deployment environment.*

**Acceptance Criteria:**

- `alert_threshold` and `alert_window_seconds` are editable in `config.yaml`
- Changes take effect on next service reload without full restart
- Invalid config values trigger a startup warning, not a silent failure

***

### Epic 5: Deployment \& Operations

**US-11**
> *As a **System Administrator**, I want to deploy the honeypot using Docker Compose with a single command, so that setup takes less than 10 minutes on any Linux host.*

**Acceptance Criteria:**

- `docker-compose up -d` brings the full system online
- A health-check endpoint confirms the SSH listener is active
- All persistent data (logs, reports) is mapped to a host volume

***

**US-12**
> *As a **System Administrator**, I want the honeypot process isolated from my production network via firewall rules, so that a compromised honeypot cannot be used as a pivot point against real systems.*

**Acceptance Criteria:**

- Outbound connections from the honeypot container are blocked except to configured logging/reporting endpoints[^3]
- Network policy is documented and validated in the deployment README
- Any unexpected outbound connection attempt is logged as a security event

***

## Constraints \& Assumptions

- The honeypot is **low-interaction** — no real shell, filesystem, or command execution is exposed.[^4]
- The system is intended for **research and threat intelligence**, not as an IDS/IPS replacement.[^10]
- Password data handling must comply with applicable data privacy regulations (e.g., GDPR in the Netherlands), particularly around storing plaintext attacker-submitted credentials.[^9]
- The operator must ensure the honeypot IP is not listed on public blocklists or Shodan as a honeypot to maintain deception effectiveness.[^5]
<span style="display:none">[^11][^12][^13][^14][^15]</span>

***

## Project Structure

The system is split into **7 focused modules**, each traceable to specific requirements :


| File | Purpose | Requirements |
| :-- | :-- | :-- |
| `main.py` | Entry point, runs all coroutines | US-11 |
| `honeypot.py` | SSH server, auth capture | FR-1, FR-2, FR-5 |
| `enrichment.py` | GeoIP + AbuseIPDB lookup | FR-3 |
| `alerting.py` | Webhook/email alerts | FR-5, US-09 |
| `reporter.py` | Daily HTML/PDF reports | FR-4, US-06–08 |
| `scheduler.py` | Cron-style async scheduler | FR-4.1 |
| `config.yaml` | All tunables in one place | US-02, US-10 |


***

## System Architecture

![SSH Honeypot System Architecture](architecture.jpg)




---

## Module Breakdown

### `honeypot.py` — Core Engine

Built on **asyncssh**, it binds to the configured port and presents a fully configurable SSH banner (FR-1.1, FR-1.4). Every `password_auth_requested` call is permanently denied (FR-1.3) and asynchronously dispatches a log + enrichment + alert pipeline so that the connection response is never delayed .[^1]

### `enrichment.py` — IP Intelligence

Uses **ip-api.com** (free, no key required) for country/city/ASN enrichment and optionally calls **AbuseIPDB** for abuse confidence scores. All lookups are async with a 3-second timeout and an in-memory cache — if a lookup fails, the log entry is still written with `"geo": null` (satisfying FR-3 acceptance criteria) .[^2]

### `alerting.py` — Real-Time Alerts

Maintains a per-IP sliding time window. When an IP exceeds the `threshold` within `window_seconds`, a formatted alert fires to the configured Slack/Discord webhook (FR-5.1, FR-5.2) . Both values are hot-configurable in `config.yaml` without code changes (US-10).[^3]

### `reporter.py` — Daily Reports

Reads JSON log files, calculates top usernames/passwords/IPs/countries, computes a 7-day trend with ↑/↓/→ indicator, and renders a self-contained dark-themed **HTML** report with an embedded Chart.js trend graph . **PDF** output is available if `weasyprint` is installed (FR-4.3).

### Docker Deployment

A single `./setup.sh` call generates the RSA host key, builds the image, and starts the container (US-11) . The compose file enforces a `128m` memory cap (NFR-2), runs as a non-root `honeypot` user (NFR-4), and maps logs/reports to host volumes so data persists across restarts .

***

## Quick Start

```bash
# Clone project & run one-command setup
chmod +x setup.sh && ./setup.sh

# Watch live attack logs
docker logs -f ssh_honeypot

# Generate a report manually anytime
docker exec ssh_honeypot python reporter.py
```

To run on real port 22, update `docker-compose.yml` ports to `"22:2222"` and move your legitimate SSH daemon to a non-standard port .

***

## Key Design Decisions

- **asyncssh over paramiko**  — fully async, handles 500+ concurrent connections without threading (NFR-1)[^1][^4]
- **JSON log format** — each line is a valid JSON object, making downstream processing with pandas, Elasticsearch, or Splunk trivial (FR-2.2)
- **No real shell ever opened** — auth is always rejected at the protocol level, not the OS level, eliminating any risk of accidental command execution (FR-1.2)
- **GDPR note** — passwords are stored as plaintext in logs for threat intelligence purposes; for production use in the EU, consider hashing with SHA-256 before writing to disk (NFR-5)[^5]
<span style="display:none">[^10][^11][^12][^13][^14][^15][^16][^17][^6][^7][^8][^9]</span>

<div align="center">⁂</div>

<div align="center">⁂</div>
