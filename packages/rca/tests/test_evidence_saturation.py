"""Tests for evidence_saturation module.

Tests for evidence saturation detection and quality metrics.
"""

import pytest

from rca.evidence_saturation import (
    EvidenceSaturationChecker,
    SaturationLevel,
)


class TestSaturationLevel:
    """Test SaturationLevel enum."""

    def test_level_values(self):
        """SaturationLevel has expected values."""
        assert SaturationLevel.LOW.value == "low"
        assert SaturationLevel.MEDIUM.value == "medium"
        assert SaturationLevel.HIGH.value == "high"
        assert SaturationLevel.SATURATED.value == "saturated"


class TestEvidenceSaturationCheckerInit:
    """Test EvidenceSaturationChecker initialization."""

    def test_checker_creation(self):
        """EvidenceSaturationChecker can be created."""
        checker = EvidenceSaturationChecker()

        assert checker is not None

    def test_checker_with_thresholds(self):
        """Custom thresholds can be set."""
        checker = EvidenceSaturationChecker(
            low_threshold=5,
            medium_threshold=10,
            high_threshold=15,
        )

        assert checker.low_threshold == 5


class TestCheckSaturation:
    """Test saturation level checking."""

    def test_low_saturation(self):
        """Few evidence items results in low saturation."""
        checker = EvidenceSaturationChecker()

        level = checker.check_saturation(evidence_count=2)

        assert level == SaturationLevel.LOW

    def test_medium_saturation(self):
        """Moderate evidence results in medium saturation."""
        checker = EvidenceSaturationChecker(
            low_threshold=5,
            medium_threshold=10,
        )

        level = checker.check_saturation(evidence_count=7)

        assert level == SaturationLevel.MEDIUM

    def test_high_saturation(self):
        """Many evidence items results in high saturation."""
        checker = EvidenceSaturationChecker(
            medium_threshold=10,
            high_threshold=15,
        )

        level = checker.check_saturation(evidence_count=12)

        assert level == SaturationLevel.HIGH

    def test_saturated(self):
        """Very high evidence count results in saturated."""
        checker = EvidenceSaturationChecker(high_threshold=15)

        level = checker.check_saturation(evidence_count=20)

        assert level == SaturationLevel.SATURATED


class TestCheckSaturationWithDiversity:
    """Test saturation considering evidence diversity."""

    def test_diverse_evidence_increases_saturation(self):
        """Diverse evidence types increase saturation level."""
        checker = EvidenceSaturationChecker()

        # Same type, multiple items
        level1 = checker.check_saturation_with_diversity(
            evidence_count=5,
            unique_types=1,
        )

        # Multiple types, same count
        level2 = checker.check_saturation_with_diversity(
            evidence_count=5,
            unique_types=3,
        )

        # More diverse should be at least as saturated
        assert level2.value >= level1.value


class TestIsSaturated:
    """Test saturation boolean checks."""

    def test_is_saturated_true(self):
        """High evidence count is saturated."""
        checker = EvidenceSaturationChecker(high_threshold=10)

        assert checker.is_saturated(evidence_count=15) is True

    def test_is_saturated_false(self):
        """Low evidence count is not saturated."""
        checker = EvidenceSaturationChecker(high_threshold=10)

        assert checker.is_saturated(evidence_count=5) is False


class TestGetSaturationScore:
    """Test saturation score calculation."""

    def test_saturation_score_bounds(self):
        """Saturation score is between 0 and 1."""
        checker = EvidenceSaturationChecker()

        score1 = checker.get_saturation_score(evidence_count=0)
        score2 = checker.get_saturation_score(evidence_count=100)

        assert 0.0 <= score1 <= 1.0
        assert 0.0 <= score2 <= 1.0

    def test_saturation_score_increases(self):
        """Saturation score increases with evidence count."""
        checker = EvidenceSaturationChecker()

        score1 = checker.get_saturation_score(evidence_count=5)
        score2 = checker.get_saturation_score(evidence_count=15)

        assert score2 > score1


class TestGetRecommendation:
    """Test saturation-based recommendations."""

    def test_recommendation_for_low_saturation(self):
        """Low saturation triggers gather more evidence."""
        checker = EvidenceSaturationChecker()

        recommendation = checker.get_recommendation(evidence_count=2)

        assert "gather" in recommendation.lower() or "more" in recommendation.lower() or "evidence" in recommendation.lower()

    def test_recommendation_for_saturated(self):
        """Saturated triggers proceed to verification."""
        checker = EvidenceSaturationChecker(high_threshold=10)

        recommendation = checker.get_recommendation(evidence_count=15)

        assert "proceed" in recommendation.lower() or "verif" in recommendation.lower() or "sufficient" in recommendation.lower()


class TestEdgeCases:
    """Test edge cases."""

    def test_zero_evidence(self):
        """Zero evidence is handled."""
        checker = EvidenceSaturationChecker()

        level = checker.check_saturation(evidence_count=0)

        assert level == SaturationLevel.LOW

    def test_negative_evidence(self):
        """Negative evidence count is handled."""
        checker = EvidenceSaturationChecker()

        level = checker.check_saturation(evidence_count=-1)

        assert level == SaturationLevel.LOW

    def test_very_high_evidence(self):
        """Very high evidence count is handled."""
        checker = EvidenceSaturationChecker()

        level = checker.check_saturation(evidence_count=10000)

        assert level == SaturationLevel.SATURATED
