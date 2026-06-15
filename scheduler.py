"""
Report Scheduler (FR-4.1, US-06)
Runs as a background daemon. Triggers reporter.py at configured time daily.
Can also be replaced by a system cron job:
  0 0 * * * cd /opt/honeypot && python reporter.py >> logs/scheduler.log 2>&1
"""

import asyncio
import yaml
import logging
from datetime import datetime, timezone
from reporter import generate_report

logger = logging.getLogger("scheduler")

with open("config.yaml") as f:
    CFG = yaml.safe_load(f)

SCHEDULE_TIME = CFG["reporting"]["schedule"]  # "HH:MM"


async def scheduler_loop():
    logger.info(f"Scheduler started — reports will run daily at {SCHEDULE_TIME} UTC")
    while True:
        now      = datetime.now(timezone.utc)
        h, m     = map(int, SCHEDULE_TIME.split(":"))
        next_run = now.replace(hour=h, minute=m, second=0, microsecond=0)
        if next_run <= now:
            next_run = next_run.replace(day=next_run.day + 1)
        wait_sec = (next_run - now).total_seconds()
        logger.info(f"Next report in {wait_sec:.0f}s ({next_run.isoformat()})")
        await asyncio.sleep(wait_sec)
        try:
            generate_report()
        except Exception as e:
            logger.error(f"Report generation failed: {e}")


if __name__ == "__main__":
    asyncio.run(scheduler_loop())
