"""Client for the National Grid ESO Carbon Intensity API (real-time UK grid data).

Fetches live data at call time. If the network is unavailable (e.g. offline CI),
it falls back to bundled real sample responses so the code and tests still run.
Docs: https://carbon-intensity.github.io/api-definitions/
"""
from __future__ import annotations
import json
import logging
import time
from pathlib import Path

import requests

from . import config

logger = logging.getLogger(__name__)

_SESSION = requests.Session()
_SESSION.headers.update({"Accept": "application/json",
                         "User-Agent": "uk-carbon-intensity-dashboard"})
_CACHE: dict[str, tuple[float, dict]] = {}
_SOURCE: dict[str, str] = {}   # endpoint -> "live" or "sample"

# Map endpoints to their bundled real fallback fixture
_FALLBACK = {
    "/intensity": "sample_intensity.json",
    "/intensity/date": "sample_intensity_date.json",
    "/generation": "sample_generation.json",
}


def _fallback(endpoint: str) -> dict:
    """Load a bundled real sample when the API can't be reached."""
    for key in sorted(_FALLBACK, key=len, reverse=True):  # most specific first
        if endpoint.startswith(key):
            fname = _FALLBACK[key]
            path = config.DATA_DIR / fname
            logger.warning("Using bundled sample for %s (%s)", endpoint, fname)
            return json.loads(Path(path).read_text())
    raise ConnectionError(f"No live data and no fallback for {endpoint}")


def _get(endpoint: str, use_cache: bool = True, retries: int = 2) -> dict:
    """GET an API endpoint with simple TTL caching, retries, and offline fallback."""
    now = time.time()
    if use_cache and endpoint in _CACHE:
        ts, payload = _CACHE[endpoint]
        if now - ts < config.CACHE_TTL:
            return payload

    url = config.API_BASE + endpoint
    for attempt in range(retries + 1):
        try:
            resp = _SESSION.get(url, timeout=config.REQUEST_TIMEOUT)
            resp.raise_for_status()
            payload = resp.json()
            _CACHE[endpoint] = (now, payload)
            _SOURCE[endpoint] = "live"
            return payload
        except requests.RequestException as exc:
            logger.warning("Request to %s failed (attempt %d): %s", url, attempt + 1, exc)
            time.sleep(0.5 * (attempt + 1))
    # network exhausted -> bundled real sample
    _SOURCE[endpoint] = "sample"
    return _fallback(endpoint)


def last_source() -> str:
    """"live" if every endpoint used so far came from the API, else "sample"."""
    return "sample" if "sample" in _SOURCE.values() else "live"


# ---- Public endpoints ---------------------------------------------------- #
def current_intensity() -> dict:
    """Current half-hour national carbon intensity (gCO2/kWh)."""
    return _get("/intensity")


def intensity_today() -> dict:
    """Today's 48 half-hourly intensity values (forecast + actual)."""
    return _get("/intensity/date")


def generation_mix() -> dict:
    """Current electricity generation mix by fuel (%)."""
    return _get("/generation")


def intensity_range(date_from: str, date_to: str) -> dict:
    """Half-hourly intensity between two ISO timestamps (e.g. '2024-01-01T00:00Z')."""
    return _get(f"/intensity/{date_from}/{date_to}", use_cache=False)
