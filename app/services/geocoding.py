"""
Geocoding Service
==================
Converts a location name (area, city, pincode) into (lat, lon)
using the OpenStreetMap Nominatim API.

Fallback: Returns None if geocoding fails so the caller can handle gracefully.
"""

import httpx
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
HEADERS = {
    # Nominatim requires a descriptive User-Agent per usage policy
    "User-Agent": "GreenHabitatCertificationBot/1.0 (contact@greenhabitat.dev)"
}


async def geocode_location(location: str) -> Optional[Tuple[float, float]]:
    """
    Fetch latitude and longitude for a given location string.

    Args:
        location: Human-readable place name, address, or pincode.

    Returns:
        Tuple (lat, lon) or None if geocoding fails.
    """
    params = {
        "q": location,
        "format": "json",
        "limit": 1,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(NOMINATIM_URL, params=params, headers=HEADERS)
            response.raise_for_status()
            results = response.json()

        if not results:
            logger.warning(f"Nominatim returned no results for: '{location}'")
            return None

        lat = float(results[0]["lat"])
        lon = float(results[0]["lon"])
        logger.info(f"Geocoded '{location}' → ({lat}, {lon})")
        return lat, lon

    except httpx.HTTPError as e:
        logger.error(f"Geocoding HTTP error for '{location}': {e}")
        return None
    except (KeyError, ValueError, IndexError) as e:
        logger.error(f"Geocoding parse error for '{location}': {e}")
        return None
