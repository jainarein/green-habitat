"""
Crowd Density Service
=====================
Estimates crowd density by counting Points of Interest (POIs)
near the location via the Overpass API.

Rationale:
    More POIs (shops, offices, restaurants, etc.) → denser urban area → lower peacefulness.
    We invert this count into a 0–100 comfort score.
"""

import httpx
import logging
import hashlib
from typing import Tuple

logger = logging.getLogger(__name__)

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
SEARCH_RADIUS_M = 1000  # 1 km

# POI count that maps to score ≈ 0 (extremely dense)
MAX_POI_COUNT = 200

MOCK_SOURCE = "mock"


def _mock_crowd_score(lat: float, lon: float) -> float:
    seed = int(hashlib.md5(f"crowd{lat:.3f}{lon:.3f}".encode()).hexdigest(), 16)
    return round(45 + (seed % 50), 2)


async def fetch_crowd_density_score(lat: float, lon: float) -> Tuple[float, str]:
    """
    Count nearby POIs from Overpass and invert to a peacefulness score.

    Args:
        lat: Latitude
        lon: Longitude

    Returns:
        Tuple (crowd_density_score 0–100, source_label)
        Higher = less crowded = more peaceful
    """
    # Query nodes with amenity/shop/office tags (common POI indicators)
    query = f"""
    [out:json][timeout:15];
    (
      node["amenity"](around:{SEARCH_RADIUS_M},{lat},{lon});
      node["shop"](around:{SEARCH_RADIUS_M},{lat},{lon});
      node["office"](around:{SEARCH_RADIUS_M},{lat},{lon});
    );
    out count;
    """

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(OVERPASS_URL, data={"data": query})
            response.raise_for_status()
            data = response.json()

        count = 0
        for el in data.get("elements", []):
            if el.get("type") == "count":
                count = int(el.get("tags", {}).get("total", 0))
                break

        # Invert: more POIs → lower comfort
        density_ratio = min(count / MAX_POI_COUNT, 1.0)
        score = round((1.0 - density_ratio) * 100, 2)
        score = max(score, 5.0)

        logger.info(f"Crowd: {count} POIs → score={score}")
        return score, "overpass_osm"

    except httpx.HTTPError as e:
        logger.error(f"Crowd density Overpass HTTP error: {e}. Using mock.")
        return _mock_crowd_score(lat, lon), MOCK_SOURCE
    except Exception as e:
        logger.error(f"Crowd density processing error: {e}. Using mock.")
        return _mock_crowd_score(lat, lon), MOCK_SOURCE
