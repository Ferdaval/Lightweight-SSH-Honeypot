"""
Entry point — runs honeypot + scheduler concurrently (US-11)
"""

import asyncio
import logging
from honeypot import start_honeypot
from scheduler import scheduler_loop

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)

async def main():
    await asyncio.gather(
        start_honeypot(),
        scheduler_loop(),
    )

if __name__ == "__main__":
    asyncio.run(main())
