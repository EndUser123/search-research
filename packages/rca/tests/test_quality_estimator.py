"""Tests for quality_estimator module.

Tests for solution quality assessment and estimation.
"""

import pytest

from rca.quality_estimator import (
    QualityAssessment,
    QualityEstimator,
    QualityLevel,
)


class TestQualityLevel:
    """Test QualityLevel enum."""

    def test_quality_level_values(self):
        """QualityLevel has expected values."""
        assert QualityLevel.HIGH.value == "high"
        assert QualityLevel.MEDIUM.value == "medium"
        assert QualityLevel.LOW.value == "low"
        assert QualityLevel.UNKNOWN.value == "unknown"


class TestQualityAssessment:
    """Test QualityAssessment dataclass."""

    def test_assessment_creation(self):
        """QualityAssessment can be created."""
        assessment = QualityAssessment(
            level=QualityLevel.HIGH,
            confidence=0.9,
            rationale="Strong evidence and successful verification",
            completeness_score=0.95,
        )

        assert assessment.level == QualityLevel.HIGH
        assert assessment.confidence == 0.9

    def test_assessment_defaults(self):
        """QualityAssessment has defaults."""
        assessment = QualityAssessment(level=QualityLevel.UNKNOWN)

        assert assessment.level == QualityLevel.UNKNOWN
        assert assessment.confidence >= 0.0


class TestQualityEstimatorInit:
    """Test QualityEstimator initialization."""

    def test_estimator_creation(self):
        """QualityEstimator can be created."""
        estimator = QualityEstimator()

        assert estimator is not None


class TestEstimateQuality:
    """Test quality estimation."""

    def test_estimate_high_quality(self):
        """High quality solution with strong evidence."""
        estimator = QualityEstimator()

        assessment = estimator.estimate_quality(
            root_cause_identified=True,
            fix_applied=True,
            fix_verified=True,
            evidence_count=15,
            hypothesis_count=3,
            recurrence_prevented=True,
        )

        assert assessment.level == QualityLevel.HIGH
        assert assessment.confidence >= 0.7

    def test_estimate_low_quality(self):
        """Low quality solution without verification."""
        estimator = QualityEstimator()

        assessment = estimator.estimate_quality(
            root_cause_identified=False,
            fix_applied=False,
            fix_verified=False,
            evidence_count=1,
            hypothesis_count=0,
            recurrence_prevented=False,
        )

        assert assessment.level == QualityLevel.LOW
        assert assessment.confidence <= 0.5

    def test_estimate_medium_quality(self):
        """Medium quality with partial evidence."""
        estimator = QualityEstimator()

        assessment = estimator.estimate_quality(
            root_cause_identified=True,
            fix_applied=True,
            fix_verified=False,
            evidence_count=5,
            hypothesis_count=2,
            recurrence_prevented=False,
        )

        assert assessment.level in (QualityLevel.MEDIUM, QualityLevel.HIGH)

    def test_estimate_with_minimal_info(self):
        """Unknown quality with minimal information."""
        estimator = QualityEstimator()

        assessment = estimator.estimate_quality()

        assert assessment.level == QualityLevel.UNKNOWN


class TestCompletenessScore:
    """Test completeness scoring."""

    def test_completeness_with_all_elements(self):
        """Complete solution has high score."""
        estimator = QualityEstimator()

        assessment = estimator.estimate_quality(
            root_cause_identified=True,
            fix_applied=True,
            fix_verified=True,
            evidence_count=10,
            hypothesis_count=2,
            has_regression_test=True,
            has_documentation=True,
            recurrence_prevented=True,
        )

        assert assessment.completeness_score >= 0.8

    def test_completeness_with_partial_elements(self):
        """Partial solution has medium score."""
        estimator = QualityEstimator()

        assessment = estimator.estimate_quality(
            root_cause_identified=True,
            fix_applied=True,
            fix_verified=False,
            evidence_count=3,
            hypothesis_count=1,
            has_regression_test=False,
            has_documentation=False,
            recurrence_prevented=False,
        )

        assert 0.3 <= assessment.completeness_score <= 0.7


class TestRationaleGeneration:
    """Test rationale generation."""

    def test_rationale_includes_factors(self):
        """Rationale includes key assessment factors."""
        estimator = QualityEstimator()

        assessment = estimator.estimate_quality(
            root_cause_identified=True,
            fix_verified=True,
            evidence_count=10,
        )

        assert assessment.rationale is not None
        assert len(assessment.rationale) > 0

    def test_rationale_for_high_quality(self):
        """High quality rationale mentions positive factors."""
        estimator = QualityEstimator()

        assessment = estimator.estimate_quality(
            root_cause_identified=True,
            fix_applied=True,
            fix_verified=True,
            evidence_count=15,
        )

        rationale_lower = assessment.rationale.lower()

        assert "verif" in rationale_lower or "evidence" in rationale_lower or "strong" in rationale_lower


class TestEdgeCases:
    """Test edge cases."""

    def test_zero_evidence(self):
        """Zero evidence is handled."""
        estimator = QualityEstimator()

        assessment = estimator.estimate_quality(evidence_count=0)

        assert assessment.level == QualityLevel.LOW

    def test_very_high_evidence_count(self):
        """Very high evidence count is handled."""
        estimator = QualityEstimator()

        assessment = estimator.estimate_quality(
            evidence_count=1000,
            root_cause_identified=True,
            fix_verified=True,
        )

        assert assessment.level in (QualityLevel.HIGH, QualityLevel.MEDIUM)

    def test_confidence_bounds(self):
        """Confidence is always between 0 and 1."""
        estimator = QualityEstimator()

        assessment = estimator.estimate_quality(
            root_cause_identified=True,
            fix_verified=False,
        )

        assert 0.0 <= assessment.confidence <= 1.0
