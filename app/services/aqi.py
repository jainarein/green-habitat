"""
AQI Service
============
Fetches real-time Air Quality Index data using:
    1. WAQI (World Air Quality Index) API - PRIMARY (better India coverage)
    2. OpenAQ API v3 - FALLBACK
    3. Mock value - Final fallback if both APIs fail

WAQI API docs: https://aqicn.org/api/
OpenAQ API v3 docs: https://docs.openaq.org/
"""

import httpx
import logging
import os
from dotenv import load_dotenv
from typing import Tuple, Optional

# Load .env file
load_dotenv()

logger = logging.getLogger(__name__)

# API URLs
WAQI_URL = "https://api.waqi.info/feed/geo:{lat};{lon}/"
OPENAQ_URL = "https://api.openaq.org/v3/locations"

# Mock fallback AQI value (moderate air quality)
MOCK_AQI = 80
MOCK_SOURCE = "mock"


def normalize_aqi(aqi_value: float) -> float:
    """
    Convert a raw AQI value (0-500+ scale) to a cleanliness score (0-100).

    Mapping:
        0-50    -> Good             -> Score 90-100
        51-100  -> Moderate         -> Score 70-89
        101-150 -> Unhealthy (sens) -> Score 50-69
        151-200 -> Unhealthy        -> Score 30-49
        201-300 -> Very Unhealthy   -> Score 10-29
        300+    -> Hazardous        -> Score 0-9
    """
    aqi_value = max(0, aqi_value)

    if aqi_value <= 50:
        return round(90 + (50 - aqi_value) / 50 * 10, 2)
    elif aqi_value <= 100:
        return round(70 + (100 - aqi_value) / 50 * 20, 2)
    elif aqi_value <= 150:
        return round(50 + (150 - aqi_value) / 50 * 20, 2)
    elif aqi_value <= 200:
        return round(30 + (200 - aqi_value) / 50 * 20, 2)
    elif aqi_value <= 300:
        return round(10 + (300 - aqi_value) / 100 * 20, 2)
    else:
        return max(0, round(10 - (aqi_value - 300) / 100 * 10, 2))


async def fetch_waqi_score(lat: float, lon: float) -> Optional[Tuple[float, str]]:
    """
    Fetch AQI from WAQI API (better India coverage).

    Returns:
        Tuple (aqi_score, "waqi") or None if failed
    """
    waqi_token = os.getenv("WAQI_API_TOKEN", "")

    if not waqi_token:
        logger.warning("WAQI: No token found in .env. Skipping WAQI.")
        return None

    url = WAQI_URL.format(lat=lat, lon=lon)
    params = {"token": waqi_token}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        if data.get("status") != "ok":
            logger.warning(f"WAQI: Bad response status: {data.get('status')}")
            return None

        aqi_value = data.get("data", {}).get("aqi")

        if aqi_value is None or aqi_value == "-":
            logger.warning("WAQI: No AQI value in response.")
            return None

        aqi_value = float(aqi_value)
        score = normalize_aqi(aqi_value)
        logger.info(f"WAQI: AQI={aqi_value} -> score={score}")
        return score, "waqi"

    except httpx.HTTPError as e:
        logger.error(f"WAQI HTTP error: {e}")
        return None
    except Exception as e:
        logger.error(f"WAQI processing error: {e}")
        return None


async def fetch_openaq_score(lat: float, lon: float) -> Optional[Tuple[float, str]]:
    """
    Fetch AQI from OpenAQ API v3 (fallback).

    Returns:
        Tuple (aqi_score, "openaq") or None if failed
    """
    api_key = os.getenv("OPENAQ_API_KEY", "")
    headers = {}
    if api_key:
        headers["X-API-Key"] = api_key

    params = {
        "coordinates": f"{lat},{lon}",
        "radius": 10000,
        "limit": 5,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(OPENAQ_URL, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()

        results = data.get("results", [])
        if not results:
            return None

        readings = []
        for location in results:
            for sensor in location.get("sensors", []):
                param = sensor.get("parameter", {})
                if param.get("name") in ("pm25", "pm10"):
                    last_value = sensor.get("lastValue")
                    if last_value is not None:
                        readings.append(float(last_value))

        if not readings:
            return None

        avg_pm = sum(readings) / len(readings)
        aqi_approx = _pm25_to_aqi(avg_pm)
        score = normalize_aqi(aqi_approx)
        logger.info(f"OpenAQ: avg PM={avg_pm:.1f} -> AQI={aqi_approx:.0f} -> score={score}")
        return score, "openaq"

    except Exception as e:
        logger.error(f"OpenAQ error: {e}")
        return None


async def fetch_aqi_score(lat: float, lon: float) -> Tuple[float, str]:
    """
    Main AQI fetcher. Tries WAQI first, then OpenAQ, then mock.

    Args:
        lat: Latitude
        lon: Longitude

    Returns:
        Tuple (aqi_score 0-100, source_label)
    """
    # Try WAQI first (better India coverage)
    result = await fetch_waqi_score(lat, lon)
    if result is not None:
        return result

    # Try OpenAQ as fallback
    result = await fetch_openaq_score(lat, lon)
    if result is not None:
        return result

    # Final fallback: mock value
    logger.warning("AQI: Both APIs failed. Using mock value.")
    return MOCK_AQI, MOCK_SOURCE


def _pm25_to_aqi(pm25: float) -> float:
    """
    Convert PM2.5 (ug/m3) to AQI using US EPA breakpoints.
    """
    breakpoints = [
        (0.0,   12.0,  0,   50),
        (12.1,  35.4,  51,  100),
        (35.5,  55.4,  101, 150),
        (55.5,  150.4, 151, 200),
        (150.5, 250.4, 201, 300),
        (250.5, 350.4, 301, 400),
        (350.5, 500.4, 401, 500),
    ]
    pm25 = max(0, pm25)
    for c_lo, c_hi, aqi_lo, aqi_hi in breakpoints:
        if c_lo <= pm25 <= c_hi:
            aqi = ((aqi_hi - aqi_lo) / (c_hi - c_lo)) * (pm25 - c_lo) + aqi_lo
            return round(aqi, 1)
    return 500.0