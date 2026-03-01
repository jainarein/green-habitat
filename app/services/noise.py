"""
Noise Estimation Service
========================
Estimates noise level based on:
    1. Traffic score (primary driver — road noise)
    2. Crowd density score (secondary — human activity noise)

No external API required; derived from already-fetched scores.

Formula:
    noise_score = 0.70 * traffic_score + 0.30 * crowd_density_score

This is a proxy model. Future versions can integrate real noise
map datasets (e.g., EU Environmental Noise Directive shapefiles).
"""

import logging

logger = logging.getLogger(__name__)


def compute_noise_score(traffic_score: float, crowd_density_score: float) -> float:
    """
    Estimate noise peacefulness from traffic and crowd scores.

    Args:
        traffic_score: Score where higher = less traffic (0–100)
        crowd_density_score: Score where higher = less crowded (0–100)

    Returns:
        float: noise_score (higher = quieter environment, 0–100)
    """
    score = round(0.70 * traffic_score + 0.30 * crowd_density_score, 2)
    logger.info(
        f"Noise: traffic={traffic_score}, crowd={crowd_density_score} → noise_score={score}"
    )
    return score
