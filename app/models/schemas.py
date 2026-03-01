"""
Pydantic models for the Green Habitat Certification API.
"""

from pydantic import BaseModel, Field
from typing import Optional


class Coordinates(BaseModel):
    lat: float = Field(..., description="Latitude of the location")
    lon: float = Field(..., description="Longitude of the location")


class ParameterScores(BaseModel):
    greenery_score: float = Field(..., ge=0, le=100, description="Green cover score (0-100)")
    aqi_score: float = Field(..., ge=0, le=100, description="Air quality index score (0-100)")
    traffic_score: float = Field(..., ge=0, le=100, description="Traffic exposure score (0-100)")
    crowd_density_score: float = Field(..., ge=0, le=100, description="Crowd density score (0-100)")
    noise_score: float = Field(..., ge=0, le=100, description="Noise level score (0-100)")


class AreaRatingResponse(BaseModel):
    location: str = Field(..., description="Input location name")
    coordinates: Coordinates
    peace_score: float = Field(..., ge=0, le=100, description="Final computed peace index score")
    certification: str = Field(..., description="Certification level based on peace score")
    parameters: ParameterScores
    data_sources: Optional[dict] = Field(None, description="Indicates which data was live vs mocked")
    satellite_image_url: Optional[str] = Field(None, description="Sentinel-2A/2B or Google Maps satellite image URL")
    ndvi_value: Optional[float] = Field(None, description="NDVI value computed from Sentinel-2 Bands B4/B8. >0.6=dense green, 0.2-0.6=sparse, <0.2=urban")
    satellite_source: Optional[str] = Field(None, description="Source of satellite image: sentinel-2, google_maps_satellite, or mock")


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None