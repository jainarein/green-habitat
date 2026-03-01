"""
Utility helpers: peace score calculator and certification labeler.
"""


def compute_peace_score(
    greenery_score: float,
    aqi_score: float,
    traffic_score: float,
    crowd_density_score: float,
    noise_score: float,
) -> float:
    """
    Compute weighted Peace Index score.

    Weights:
        Greenery       → 30%
        AQI            → 25%
        Traffic        → 20%
        Crowd Density  → 15%
        Noise          → 10%

    Returns:
        float: Rounded peace score between 0 and 100.
    """
    score = (
        0.30 * greenery_score
        + 0.25 * aqi_score
        + 0.20 * traffic_score
        + 0.15 * crowd_density_score
        + 0.10 * noise_score
    )
    return round(score, 2)


def get_certification(peace_score: float) -> str:
    """
    Map a peace score to a certification tier.

    Tiers:
        85–100 → Platinum Peace Zone
        70–84  → Green Certified
        55–69  → Moderate Living
        <55    → Urban Stress Area
    """
    if peace_score >= 85:
        return "Platinum Peace Zone"
    elif peace_score >= 70:
        return "Green Certified"
    elif peace_score >= 55:
        return "Moderate Living"
    else:
        return "Urban Stress Area"
