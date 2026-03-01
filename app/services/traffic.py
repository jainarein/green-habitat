"""
Traffic Service
===============
Estimates traffic exposure by querying OpenStreetMap Overpass API
for high-traffic road types near the location.

Logic:
    - Major roads (motorways, trunk, primary) within 500 m -> high traffic penalty
    - Secondary/tertiary roads within 800 m -> moderate
    - Score inversely proportional to road density (fewer major roads = higher score)
"""

import httpx
import asyncio
import logging
import hashlib
from typing import Tuple

logger = logging.getLogger(__name__)

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Road type weights (higher weight = heavier traffic impact)
ROAD_WEIGHTS = {
    "motorway": 5,
    "trunk": 4,
    "primary": 3,
    "secondary": 2,
    "tertiary": 1,
}

# Max weighted road score that maps to score=0 (very heavy traffic)
MAX_ROAD_SCORE = 30

MOCK_SOURCE = "mock"


def _mock_traffic_score(lat: float, lon: float) -> float:
    seed = int(hashlib.md5(f"traffic{lat:.3f}{lon:.3f}".encode()).hexdigest(), 16)
    return round(40 + (seed % 55), 2)


async def fetch_traffic_score(lat: float, lon: float) -> Tuple[float, str]:
    """
    Query Overpass API for major roads near the coordinates.

    Args:
        lat: Latitude
        lon: Longitude

    Returns:
        Tuple (traffic_score 0-100, source_label)
        Higher score = lower traffic exposure = more peaceful
    """
    radius = 800  # metres

    road_filter = "|".join(ROAD_WEIGHTS.keys())
    query = f"""
    [out:json][timeout:15];
    way["highway"~"^({road_filter})$"](around:{radius},{lat},{lon});
    out tags;
    """

    # Small delay to avoid Overpass rate limiting (429 errors)
    await asyncio.sleep(1)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(OVERPASS_URL, data={"data": query})
            response.raise_for_status()
            data = response.json()

        elements = data.get("elements", [])
        weighted_sum = 0
        for way in elements:
            road_type = way.get("tags", {}).get("highway", "")
            weighted_sum += ROAD_WEIGHTS.get(road_type, 0)

        # Invert: more/heavier roads -> lower score
        penalty = min(weighted_sum / MAX_ROAD_SCORE, 1.0)
        score = round((1.0 - penalty) * 100, 2)
        score = max(score, 5.0)  # minimum floor

        logger.info(f"Traffic: {len(elements)} roads, weighted={weighted_sum} -> score={score}")
        return score, "overpass_osm"

    except httpx.HTTPError as e:
        logger.error(f"Traffic Overpass HTTP error: {e}. Using mock.")
        return _mock_traffic_score(lat, lon), MOCK_SOURCE
    except Exception as e:
        logger.error(f"Traffic processing error: {e}. Using mock.")
        return _mock_traffic_score(lat, lon), MOCK_SOURCE