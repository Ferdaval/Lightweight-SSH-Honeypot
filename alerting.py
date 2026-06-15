"""
Real-Time Alerting (FR-5, US-09, US-10)
Supports: Webhook (Slack/Discord) and logging fallback.
"""

import aiohttp
import logging
import json
from datetime import datetime, timezone

logger = logging.getLogger("alerting")


class AlertManager:
    def __init__(self, config: dict):
        self.enabled     = config.get("enabled", False)
        self.webhook_url = config.get("channels", {}).get("webhook_url", "")
        self.email       = config.get("channels", {}).get("email", "")

    async def send(self, ip: str, count: int, window: int, sample_creds: dict):
        if not self.enabled:
            return

        msg = (
            f":rotating_light: *SSH Honeypot Alert*\n"
            f"IP `{ip}` made **{count}** attempts in {window}s\n"
            f"Sample creds — user: `{sample_creds['username']}` "
            f"pass: `{sample_creds['password']}` \n"
            f"Time: {datetime.now(timezone.utc).isoformat()}"
        )
        logger.warning(f"ALERT: {ip} exceeded threshold ({count} attempts / {window}s)")

        if self.webhook_url:
            await self._send_webhook(msg)

    async def _send_webhook(self, message: str):
        payload = {"text": message}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    data=json.dumps(payload),
                    headers={"Content-Type": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=5),
                ) as resp:
                    if resp.status != 200:
                        logger.error(f"Webhook failed: {resp.status}")
        except Exception as e:
            logger.error(f"Webhook error: {e}")
