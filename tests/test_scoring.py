"""
Tests for scoring utilities and certification logic.
Run with: pytest tests/
"""
import pytest
from app.utils.scoring import compute_peace_score, get_certification


class TestPeaceScore:
    def test_all_perfect(self):
        score = compute_peace_score(100, 100, 100, 100, 100)
        assert score == 100.0

    def test_all_zero(self):
        score = compute_peace_score(0, 0, 0, 0, 0)
        assert score == 0.0

    def test_weighted_formula(self):
        # greenery=100, rest=0 → 0.30 * 100 = 30
        score = compute_peace_score(100, 0, 0, 0, 0)
        assert score == 30.0

    def test_typical_values(self):
        score = compute_peace_score(90, 75, 80, 85, 78)
        expected = round(0.30*90 + 0.25*75 + 0.20*80 + 0.15*85 + 0.10*78, 2)
        assert score == expected


class TestCertification:
    def test_platinum(self):
        assert get_certification(100) == "Platinum Peace Zone"
        assert get_certification(85) == "Platinum Peace Zone"

    def test_green(self):
        assert get_certification(84) == "Green Certified"
        assert get_certification(70) == "Green Certified"

    def test_moderate(self):
        assert get_certification(69) == "Moderate Living"
        assert get_certification(55) == "Moderate Living"

    def test_urban_stress(self):
        assert get_certification(54) == "Urban Stress Area"
        assert get_certification(0) == "Urban Stress Area"


class TestNoiseService:
    def test_derived_formula(self):
        from app.services.noise import compute_noise_score
        score = compute_noise_score(80, 60)
        expected = round(0.70 * 80 + 0.30 * 60, 2)
        assert score == expected
