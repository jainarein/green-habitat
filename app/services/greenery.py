"""
Greenery Service
================
Estimates green cover for an area by querying the OpenStreetMap
Overpass API for parks, forests, gardens, and green spaces within
a radius of the target coordinates.

Score heuristic:
    - Count and total area of green landuse polygons within ~1.5 km
    - Normalize against a reference "very green" area threshold
    - If Overpass is unavailable, return a seeded mock value
"""

import httpx
import logging
import hashlib
from typing import Tuple

logger = logging.getLogger(__name__)

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
SEARCH_RADIUS_M = 1500  # 1.5 km radius

# Reference count for "fully green" neighbourhood (calibrated heuristic)
GREEN_FEATURE_THRESHOLD = 20

MOCK_SOURCE = "mock"


def _mock_greenery_score(lat: float, lon: float) -> float:
    """
    Generate a deterministic mock score based on coordinates.
    Useful when Overpass is rate-limited or unreachable.
    """
    seed = int(hashlib.md5(f"{lat:.3f}{lon:.3f}".encode()).hexdigest(), 16)
    return round(50 + (seed % 50), 2)


async def fetch_greenery_score(lat: float, lon: float) -> Tuple[float, str]:
    """
    Query Overpass API for green land-use features near the location.

    Args:
        lat: Latitude
        lon: Longitude

    Returns:
        Tuple (greenery_score 0–100, source_label)
    """
    # Overpass QL query: parks, forests, gardens, nature reserves within radius
    query = f"""
    [out:json][timeout:15];
    (
      way["leisure"="park"](around:{SEARCH_RADIUS_M},{lat},{lon});
      way["landuse"="forest"](around:{SEARCH_RADIUS_M},{lat},{lon});
      way["landuse"="grass"](around:{SEARCH_RADIUS_M},{lat},{lon});
      way["leisure"="garden"](around:{SEARCH_RADIUS_M},{lat},{lon});
      way["leisure"="nature_reserve"](around:{SEARCH_RADIUS_M},{lat},{lon});
      way["landuse"="recreation_ground"](around:{SEARCH_RADIUS_M},{lat},{lon});
      node["leisure"="park"](around:{SEARCH_RADIUS_M},{lat},{lon});
    );
    out count;
    """

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(OVERPASS_URL, data={"data": query})
            response.raise_for_status()
            data = response.json()

        # "out count" returns a single element with tag "total"
        count = 0
        elements = data.get("elements", [])
        for el in elements:
            if el.get("type") == "count":
                count = int(el.get("tags", {}).get("total", 0))
                break

        if count == 0 and not elements:
            logger.warning("Overpass: empty response. Using mock greenery.")
            return _mock_greenery_score(lat, lon), MOCK_SOURCE

        # Normalize: clamp count to threshold, map to 0–100
        score = round(min(count / GREEN_FEATURE_THRESHOLD, 1.0) * 100, 2)
        # Ensure a baseline of 10 even with no green features
        score = max(score, 10.0)
        logger.info(f"Greenery: {count} features found → score={score}")
        return score, "overpass_osm"

    except httpx.HTTPError as e:
        logger.error(f"Overpass HTTP error: {e}. Using mock greenery.")
        return _mock_greenery_score(lat, lon), MOCK_SOURCE
    except Exception as e:
        logger.error(f"Greenery processing error: {e}. Using mock greenery.")
        return _mock_greenery_score(lat, lon), MOCK_SOURCE
