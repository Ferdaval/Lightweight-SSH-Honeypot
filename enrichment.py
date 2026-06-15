"""
IP Geolocation & Threat Enrichment (FR-3)
Uses ip-api.com (free, no key needed) with optional AbuseIPDB overlay.
"""

import asyncio
import aiohttp
import yaml
import logging

logger = logging.getLogger("enrichment")

with open("config.yaml") as f:
    GEO_CFG = yaml.safe_load(f)["geo_enrichment"]

_cache: dict[str, dict] = {}   # Simple in-memory cache to avoid hammering APIs


async def enrich_ip(ip: str) -> dict:
    """Return geo + reputation data for an IP. Falls back to null on failure."""
    if ip in _cache:
        return _cache[ip]

    result = {"country": None, "city": None, "asn": None, "abuse_score": None}

    # ── ip-api.com (free, no key) ──────────────────────────────────────────
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"http://ip-api.com/json/{ip}?fields=status,country,city,org,as",
                timeout=aiohttp.ClientTimeout(total=3),
            ) as resp:
                data = await resp.json(content_type=None)
                if data.get("status") == "success":
                    result["country"] = data.get("country")
                    result["city"]    = data.get("city")
                    result["asn"]     = data.get("as")
    except Exception as e:
        logger.warning(f"GeoIP lookup failed for {ip}: {e}")

    # ── AbuseIPDB (if key configured) ─────────────────────────────────────
    api_key = GEO_CFG.get("abuseipdb_api_key", "")
    if GEO_CFG.get("enabled") and api_key and api_key != "YOUR_KEY_HERE":
        try:
            headers = {"Key": api_key, "Accept": "application/json"}
            params  = {"ipAddress": ip, "maxAgeInDays": 90}
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://api.abuseipdb.com/api/v2/check",
                    headers=headers,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=3),
                ) as resp:
                    abuse_data = await resp.json()
                    result["abuse_score"] = abuse_data["data"]["abuseConfidenceScore"]
        except Exception as e:
            logger.warning(f"AbuseIPDB lookup failed for {ip}: {e}")

    _cache[ip] = result
    return result
