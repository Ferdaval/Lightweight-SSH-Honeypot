#!/usr/bin/env python3
"""
Lightweight SSH Honeypot
Requirement: FR-1, FR-2, FR-5, NFR-1 to NFR-4
"""

import asyncio
import asyncssh
import json
import logging
import os
import signal
import yaml
from datetime import datetime, timezone
from collections import defaultdict
from enrichment import enrich_ip
from alerting import AlertManager

# ── Load config ──────────────────────────────────────────────────────────────
with open("config.yaml") as f:
    CFG = yaml.safe_load(f)

S_CFG   = CFG["server"]
L_CFG   = CFG["logging"]
A_CFG   = CFG["alerting"]
SEC_CFG = CFG["security"]

# ── Logging setup ─────────────────────────────────────────────────────────────
os.makedirs(L_CFG["log_dir"], exist_ok=True)
log_filename = os.path.join(
    L_CFG["log_dir"],
    f"attempts_{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.json"
)

logging.basicConfig(
    level=getattr(logging, L_CFG["log_level"]),
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("honeypot")

alert_mgr = AlertManager(A_CFG)

# ── Rate-tracking for alerting (FR-5.1) ──────────────────────────────────────
attempt_tracker: dict[str, list[float]] = defaultdict(list)


def write_log_entry(entry: dict):
    """Append a JSON log entry atomically (FR-2.1, FR-2.2)."""
    with open(log_filename, "a") as f:
        f.write(json.dumps(entry) + "\n")


async def check_alert(ip: str, username: str, password: str):
    """Fire alert if IP exceeds threshold within window (FR-5.1)."""
    now = asyncio.get_event_loop().time()
    window = A_CFG["window_seconds"]
    attempt_tracker[ip] = [t for t in attempt_tracker[ip] if now - t < window]
    attempt_tracker[ip].append(now)

    count = len(attempt_tracker[ip])
    if count == A_CFG["threshold"]:
        await alert_mgr.send(
            ip=ip,
            count=count,
            window=window,
            sample_creds={"username": username, "password": password},
        )


# ── SSH Server handler ────────────────────────────────────────────────────────
class HoneypotServer(asyncssh.SSHServer):
    """
    Emulates a vulnerable SSH server (FR-1).
    Always rejects auth; logs every attempt (FR-2).
    """

    def connection_made(self, conn):
        self._conn = conn
        self._peer_ip = conn.get_extra_info("peername")[0]
        self._client_version = conn.get_extra_info("client_version", "unknown")
        self._connect_time = datetime.now(timezone.utc).isoformat()
        logger.info(f"[+] Connection from {self._peer_ip}")

    def connection_lost(self, exc):
        logger.debug(f"[-] Connection closed from {self._peer_ip}")

    def begin_auth(self, username: str) -> bool:
        self._username = username
        return True  # always continue to password check

    def password_auth_requested(self, username: str, password: str) -> bool | asyncssh.PasswordChangeRequired:
        asyncio.get_event_loop().create_task(
            self._log_and_alert(username, password)
        )
        return False  # always deny (FR-1.3)

    def public_key_auth_requested(self, username: str, key) -> bool:
        return False  # deny key auth too

    async def _log_and_alert(self, username: str, password: str):
        geo = await enrich_ip(self._peer_ip)
        entry = {
            "timestamp":      self._connect_time,
            "src_ip":         self._peer_ip,
            "username":       username,
            "password":       password,
            "client_version": self._client_version,
            "geo":            geo,
        }
        write_log_entry(entry)
        logger.info(f"  user={username} pass={password} ip={self._peer_ip} country={geo.get('country', '?')} ")
        await check_alert(self._peer_ip, username, password)


# ── Start server ──────────────────────────────────────────────────────────────
async def start_honeypot():
    logger.info(f"Starting SSH Honeypot on {S_CFG['host']}:{S_CFG['port']}")
    server = await asyncssh.create_server(
        HoneypotServer,
        S_CFG["host"],
        S_CFG["port"],
        server_host_keys=[S_CFG["host_key"]],
        server_version=S_CFG["banner"],
    )
    async with server:
        await server.wait_closed()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, loop.stop)
    loop.run_until_complete(start_honeypot())
