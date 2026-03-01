"""
Rating Router
=============
Exposes GET /rate-area?location=<area_name>

Orchestrates all service calls concurrently and returns
the complete Green Habitat Certification JSON response
including Sentinel-2A/2B satellite image and NDVI value.
"""

import asyncio
import logging
from fastapi import APIRouter, HTTPException, Query

from app.services.services__init__ import (
    geocode_location,
    fetch_aqi_score,
    fetch_greenery_score,
    fetch_traffic_score,
    fetch_crowd_density_score,
    compute_noise_score,
    fetch_satellite_data,
)
from app.utils.scoring import compute_peace_score, get_certification
from app.models.schemas import AreaRatingResponse, Coordinates, ParameterScores

router = APIRouter(tags=["Area Rating"])
logger = logging.getLogger(__name__)


@router.get(
    "/rate-area",
    response_model=AreaRatingResponse,
    summary="Rate an area's environmental peacefulness",
    description=(
        "Accepts a location name, pincode, or city. "
        "Fetches live environmental data and Sentinel-2A/2B satellite imagery, "
        "then returns a Green Habitat Certification with NDVI score."
    ),
)
async def rate_area(
    location: str = Query(
        ...,
        min_length=2,
        max_length=200,
        description="Area name, society name, pincode, or city",
        example="Sector 62 Noida",
    )
):
    # ─── Step 1: Geocoding ────────────────────────────────────────────────────
    coords = await geocode_location(location)
    if coords is None:
        raise HTTPException(
            status_code=404,
            detail=f"Could not geocode location: '{location}'. "
                   "Try a more specific name or include the city.",
        )
    lat, lon = coords
    logger.info(f"Processing area rating for '{location}' at ({lat}, {lon})")

    # ─── Step 2: Fetch all data concurrently ──────────────────────────────────
    # AQI, greenery, traffic, crowd density, and satellite run in parallel
    aqi_task = fetch_aqi_score(lat, lon)
    greenery_task = fetch_greenery_score(lat, lon)
    traffic_task = fetch_traffic_score(lat, lon)
    crowd_task = fetch_crowd_density_score(lat, lon)
    satellite_task = fetch_satellite_data(lat, lon)

    (
        (aqi_score, aqi_source),
        (greenery_score, greenery_source),
        (traffic_score, traffic_source),
        (crowd_score, crowd_source),
        (satellite_url, ndvi_value, satellite_source),
    ) = await asyncio.gather(
        aqi_task, greenery_task, traffic_task, crowd_task, satellite_task
    )

    # ─── Step 3: Derive noise from traffic + crowd ────────────────────────────
    noise_score = compute_noise_score(traffic_score, crowd_score)

    # ─── Step 4: Compute final peace score ───────────────────────────────────
    peace_score = compute_peace_score(
        greenery_score=greenery_score,
        aqi_score=aqi_score,
        traffic_score=traffic_score,
        crowd_density_score=crowd_score,
        noise_score=noise_score,
    )

    # ─── Step 5: Assign certification tier ───────────────────────────────────
    certification = get_certification(peace_score)

    logger.info(
        f"'{location}' → peace_score={peace_score}, certification='{certification}', "
        f"ndvi={ndvi_value}, satellite_source={satellite_source}"
    )

    # ─── Step 6: Build and return response ───────────────────────────────────
    return AreaRatingResponse(
        location=location,
        coordinates=Coordinates(lat=lat, lon=lon),
        peace_score=peace_score,
        certification=certification,
        parameters=ParameterScores(
            greenery_score=greenery_score,
            aqi_score=aqi_score,
            traffic_score=traffic_score,
            crowd_density_score=crowd_score,
            noise_score=noise_score,
        ),
        data_sources={
            "greenery": greenery_source,
            "aqi": aqi_source,
            "traffic": traffic_source,
            "crowd_density": crowd_source,
            "noise": "derived",
            "satellite": satellite_source,
        },
        satellite_image_url=satellite_url,
        ndvi_value=ndvi_value,
        satellite_source=satellite_source,
    )