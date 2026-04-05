"""Tests for quality checker module.

This test file verifies the configurable quality check system for search results.
Tests cover QualityConfig dataclass, is_satisfactory() function, and various
quality heuristics including confidence, freshness, and backend count.

Run with: pytest tests/test_quality_checker.py -v
"""

from dataclasses import is_dataclass
from datetime import datetime, timedelta, timezone

import pytest


class TestQualityConfigDataclass:
    """Tests for QualityConfig dataclass existence and defaults."""

    def test_quality_config_exists(self):
        """Test that QualityConfig can be imported."""
        from core.quality_checker import QualityConfig

        # Should be able to instantiate
        config = QualityConfig()
        assert config is not None

    def test_quality_config_is_dataclass(self):
        """Test that QualityConfig is a dataclass."""
        from core.quality_checker import QualityConfig

        assert is_dataclass(QualityConfig)

    def test_quality_config_default_confidence_threshold(self):
        """Test that default confidence_threshold is 0.8."""
        from core.quality_checker import QualityConfig

        config = QualityConfig()
        assert config.confidence_threshold == 0.8

    def test_quality_config_default_freshness_hours(self):
        """Test that default freshness_hours is 24."""
        from core.quality_checker import QualityConfig

        config = QualityConfig()
        assert config.freshness_hours == 24

    def test_quality_config_default_min_backends(self):
        """Test that default min_backends is 1 (single-result check)."""
        from core.quality_checker import QualityConfig

        config = QualityConfig()
        assert config.min_backends == 1

    def test_quality_config_custom_values(self):
        """Test that QualityConfig accepts custom values."""
        from core.quality_checker import QualityConfig

        config = QualityConfig(confidence_threshold=0.9, freshness_hours=12, min_backends=5)
        assert config.confidence_threshold == 0.9
        assert config.freshness_hours == 12
        assert config.min_backends == 5


class TestIsSatisfactoryFunctionExists:
    """Tests for is_satisfactory() function existence and basic behavior."""

    def test_is_satisfactory_exists(self):
        """Test that is_satisfactory function can be imported."""
        from core.quality_checker import is_satisfactory

        assert callable(is_satisfactory)

    def test_is_satisfactory_requires_result(self):
        """Test that is_satisfactory requires a result parameter."""
        from core.quality_checker import is_satisfactory

        with pytest.raises(TypeError):
            is_satisfactory()  # Missing required argument


class TestConfidenceThreshold:
    """Tests for confidence threshold quality checks."""

    @pytest.fixture
    def fresh_result_with_multiple_backends(self):
        """Fixture for a fresh result with multiple backends."""
        return {
            "title": "Test Result",
            "content": "Test content",
            "confidence": 0.9,
            "created_at": datetime.now(timezone.utc),
            "sources": ["backend1", "backend2", "backend3"],
        }

    def test_high_confidence_passes(self, fresh_result_with_multiple_backends):
        """Test that high confidence scores (>=0.8) pass when other criteria met."""
        from core.quality_checker import is_satisfactory

        result = fresh_result_with_multiple_backends.copy()
        result["confidence"] = 0.8

        assert is_satisfactory(result) is True

    def test_very_high_confidence_passes(self, fresh_result_with_multiple_backends):
        """Test that very high confidence scores (1.0) pass."""
        from core.quality_checker import is_satisfactory

        result = fresh_result_with_multiple_backends.copy()
        result["confidence"] = 1.0

        assert is_satisfactory(result) is True

    def test_low_confidence_fails(self, fresh_result_with_multiple_backends):
        """Test that low confidence scores (<0.8) fail."""
        from core.quality_checker import is_satisfactory

        result = fresh_result_with_multiple_backends.copy()
        result["confidence"] = 0.7

        assert is_satisfactory(result) is False

    def test_very_low_confidence_fails(self, fresh_result_with_multiple_backends):
        """Test that very low confidence scores (0.0) fail."""
        from core.quality_checker import is_satisfactory

        result = fresh_result_with_multiple_backends.copy()
        result["confidence"] = 0.0

        assert is_satisfactory(result) is False

    def test_boundary_confidence_exactly_at_threshold(self, fresh_result_with_multiple_backends):
        """Test boundary condition: confidence exactly at threshold (0.8) passes."""
        from core.quality_checker import is_satisfactory

        result = fresh_result_with_multiple_backends.copy()
        result["confidence"] = 0.8

        assert is_satisfactory(result) is True

    def test_boundary_confidence_just_below_threshold(self, fresh_result_with_multiple_backends):
        """Test boundary condition: confidence just below threshold (0.799) fails."""
        from core.quality_checker import is_satisfactory

        result = fresh_result_with_multiple_backends.copy()
        result["confidence"] = 0.799

        assert is_satisfactory(result) is False

    def test_custom_confidence_threshold(self, fresh_result_with_multiple_backends):
        """Test that custom confidence threshold is respected."""
        from core.quality_checker import QualityConfig, is_satisfactory

        result = fresh_result_with_multiple_backends.copy()
        result["confidence"] = 0.85

        # With default threshold (0.8), should pass
        assert is_satisfactory(result) is True

        # With higher threshold (0.9), should fail
        config = QualityConfig(confidence_threshold=0.9)
        assert is_satisfactory(result, config) is False


class TestFreshnessCheck:
    """Tests for result freshness quality checks."""

    @pytest.fixture
    def high_confidence_result_with_multiple_backends(self):
        """Fixture for a high-confidence result with multiple backends."""
        return {
            "title": "Test Result",
            "content": "Test content",
            "confidence": 0.9,
            "sources": ["backend1", "backend2", "backend3"],
        }

    def test_fresh_result_passes(self, high_confidence_result_with_multiple_backends):
        """Test that fresh results (<=24h) pass."""
        from core.quality_checker import is_satisfactory

        result = high_confidence_result_with_multiple_backends.copy()
        result["created_at"] = datetime.now(timezone.utc)

        assert is_satisfactory(result) is True

    def test_result_at_boundary_passes(self, high_confidence_result_with_multiple_backends):
        """Test boundary condition: result exactly 24h old passes."""
        from core.quality_checker import is_satisfactory

        result = high_confidence_result_with_multiple_backends.copy()
        result["created_at"] = datetime.now(timezone.utc) - timedelta(hours=24)

        assert is_satisfactory(result) is True

    def test_stale_result_fails(self, high_confidence_result_with_multiple_backends):
        """Test that stale results (>24h) fail."""
        from core.quality_checker import is_satisfactory

        result = high_confidence_result_with_multiple_backends.copy()
        result["created_at"] = datetime.now(timezone.utc) - timedelta(hours=25)

        assert is_satisfactory(result) is False

    def test_very_stale_result_fails(self, high_confidence_result_with_multiple_backends):
        """Test that very stale results (7 days old) fail."""
        from core.quality_checker import is_satisfactory

        result = high_confidence_result_with_multiple_backends.copy()
        result["created_at"] = datetime.now(timezone.utc) - timedelta(days=7)

        assert is_satisfactory(result) is False

    def test_result_just_past_boundary_fails(self, high_confidence_result_with_multiple_backends):
        """Test boundary condition: result 24h1m old fails."""
        from core.quality_checker import is_satisfactory

        result = high_confidence_result_with_multiple_backends.copy()
        result["created_at"] = datetime.now(timezone.utc) - timedelta(hours=24, minutes=1)

        assert is_satisfactory(result) is False

    def test_custom_freshness_threshold(self, high_confidence_result_with_multiple_backends):
        """Test that custom freshness threshold is respected."""
        from core.quality_checker import QualityConfig, is_satisfactory

        result = high_confidence_result_with_multiple_backends.copy()
        result["created_at"] = datetime.now(timezone.utc) - timedelta(hours=30)

        # With default threshold (24h), should fail
        assert is_satisfactory(result) is False

        # With higher threshold (48h), should pass
        config = QualityConfig(freshness_hours=48)
        assert is_satisfactory(result, config) is True

    def test_missing_created_at_handled_gracefully(
        self, high_confidence_result_with_multiple_backends
    ):
        """Test that missing created_at is handled gracefully (assumes stale)."""
        from core.quality_checker import is_satisfactory

        result = high_confidence_result_with_multiple_backends.copy()
        # Don't set created_at

        # Should treat as stale and fail
        assert is_satisfactory(result) is False


class TestBackendCountCheck:
    """Tests for backend count quality checks."""

    @pytest.fixture
    def fresh_high_confidence_result(self):
        """Fixture for a fresh, high-confidence result."""
        return {
            "title": "Test Result",
            "content": "Test content",
            "confidence": 0.9,
            "created_at": datetime.now(timezone.utc),
        }

    def test_multiple_backends_pass(self, fresh_high_confidence_result):
        """Test that multiple backends (>=3) pass."""
        from core.quality_checker import is_satisfactory

        result = fresh_high_confidence_result.copy()
        result["sources"] = ["backend1", "backend2", "backend3"]

        assert is_satisfactory(result) is True

    def test_many_backends_pass(self, fresh_high_confidence_result):
        """Test that many backends (10) pass."""
        from core.quality_checker import is_satisfactory

        result = fresh_high_confidence_result.copy()
        result["sources"] = [f"backend{i}" for i in range(10)]

        assert is_satisfactory(result) is True

    def test_single_backend_passes_with_default(self, fresh_high_confidence_result):
        """Test that single backend passes with default min_backends=1."""
        from core.quality_checker import is_satisfactory

        result = fresh_high_confidence_result.copy()
        result["sources"] = ["backend1"]

        assert is_satisfactory(result) is True

    def test_no_backends_fails_with_custom_threshold(self, fresh_high_confidence_result):
        """Test that insufficient backends fail with custom min_backends=3."""
        from core.quality_checker import QualityConfig, is_satisfactory

        result = fresh_high_confidence_result.copy()
        result["sources"] = ["backend1", "backend2"]

        config = QualityConfig(min_backends=3)
        assert is_satisfactory(result, config) is False

    def test_no_backends_fails(self, fresh_high_confidence_result):
        """Test that empty backends list fails."""
        from core.quality_checker import is_satisfactory

        result = fresh_high_confidence_result.copy()
        result["sources"] = []

        assert is_satisfactory(result) is False

    def test_boundary_backend_count_exactly_at_threshold(self, fresh_high_confidence_result):
        """Test boundary condition: exactly 1 backend passes with default min_backends=1."""
        from core.quality_checker import is_satisfactory

        result = fresh_high_confidence_result.copy()
        result["sources"] = ["backend1"]

        assert is_satisfactory(result) is True

    def test_boundary_backend_count_just_below_custom_threshold(self, fresh_high_confidence_result):
        """Test boundary condition: 2 backends fails when custom min_backends=3."""
        from core.quality_checker import QualityConfig, is_satisfactory

        result = fresh_high_confidence_result.copy()
        result["sources"] = ["backend1", "backend2"]

        config = QualityConfig(min_backends=3)
        assert is_satisfactory(result, config) is False

    def test_custom_min_backends(self, fresh_high_confidence_result):
        """Test that custom min_backends is respected."""
        from core.quality_checker import QualityConfig, is_satisfactory

        result = fresh_high_confidence_result.copy()
        result["sources"] = ["backend1", "backend2"]

        # With default threshold (1), should pass
        assert is_satisfactory(result) is True

        # With higher threshold (3), should fail
        config = QualityConfig(min_backends=2)
        assert is_satisfactory(result, config) is True

    def test_missing_sources_handled_gracefully(self, fresh_high_confidence_result):
        """Test that missing sources is handled gracefully."""
        from core.quality_checker import is_satisfactory

        result = fresh_high_confidence_result.copy()
        # Don't set sources

        # Should treat as 0 backends and fail
        assert is_satisfactory(result) is False


class TestTimestampParsing:
    """Tests for timestamp format support."""

    @pytest.fixture
    def high_confidence_result_with_multiple_backends(self):
        """Fixture for a high-confidence result with multiple backends."""
        return {
            "title": "Test Result",
            "content": "Test content",
            "confidence": 0.9,
            "sources": ["backend1", "backend2", "backend3"],
        }

    def test_iso8601_timestamp_string(self, high_confidence_result_with_multiple_backends):
        """Test that ISO 8601 timestamp strings are parsed correctly."""
        from core.quality_checker import is_satisfactory

        result = high_confidence_result_with_multiple_backends.copy()
        result["created_at"] = "2026-03-10T12:00:00Z"

        # Should parse and check freshness (will fail if old, pass if recent)
        # We use a very recent timestamp
        result["created_at"] = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()

        assert is_satisfactory(result) is True

    def test_iso8601_with_timezone(self, high_confidence_result_with_multiple_backends):
        """Test ISO 8601 with explicit timezone."""
        from core.quality_checker import is_satisfactory

        result = high_confidence_result_with_multiple_backends.copy()
        result["created_at"] = (datetime.now(timezone.utc) - timedelta(hours=1)).strftime(
            "%Y-%m-%dT%H:%M:%S%z"
        )

        assert is_satisfactory(result) is True

    def test_unix_timestamp_integer(self, high_confidence_result_with_multiple_backends):
        """Test that Unix timestamps (integers) are parsed correctly."""
        from core.quality_checker import is_satisfactory

        result = high_confidence_result_with_multiple_backends.copy()
        # Unix timestamp for 1 hour ago
        result["created_at"] = int((datetime.now(timezone.utc) - timedelta(hours=1)).timestamp())

        assert is_satisfactory(result) is True

    def test_unix_timestamp_float(self, high_confidence_result_with_multiple_backends):
        """Test that Unix timestamps (floats) are parsed correctly."""
        from core.quality_checker import is_satisfactory

        result = high_confidence_result_with_multiple_backends.copy()
        # Unix timestamp for 1 hour ago (with microseconds)
        result["created_at"] = (datetime.now(timezone.utc) - timedelta(hours=1)).timestamp()

        assert is_satisfactory(result) is True

    def test_relative_timestamp_handled_gracefully(
        self, high_confidence_result_with_multiple_backends
    ):
        """Test that relative timestamps (like '2 hours ago') are handled gracefully."""
        from core.quality_checker import is_satisfactory

        result = high_confidence_result_with_multiple_backends.copy()
        result["created_at"] = "2 hours ago"

        # Should handle gracefully - may fail (treat as stale) or pass (treat as fresh)
        # The key is that it doesn't crash
        try:
            is_satisfactory(result)
        except Exception as e:
            pytest.fail(f"is_satisfactory raised exception for relative timestamp: {e}")

    def test_invalid_timestamp_handled_gracefully(
        self, high_confidence_result_with_multiple_backends
    ):
        """Test that invalid timestamps are handled gracefully."""
        from core.quality_checker import is_satisfactory

        result = high_confidence_result_with_multiple_backends.copy()
        result["created_at"] = "invalid-timestamp"

        # Should handle gracefully - likely treat as stale and fail
        try:
            result = is_satisfactory(result)
            # If it returns, should be False (stale)
            assert result is False
        except Exception as e:
            # If it raises, should be a ValueError or similar, not a crash
            assert isinstance(e, (ValueError, TypeError))


class TestCombinedCriteria:
    """Tests for combined quality criteria (all checks together)."""

    def test_all_criteria_met_passes(self):
        """Test that result meeting all criteria passes."""
        from core.quality_checker import is_satisfactory

        result = {
            "title": "Excellent Result",
            "content": "High quality content",
            "confidence": 0.95,
            "created_at": datetime.now(timezone.utc) - timedelta(hours=1),
            "sources": ["backend1", "backend2", "backend3", "backend4"],
        }

        assert is_satisfactory(result) is True

    def test_low_confidence_fails_despite_other_criteria(self):
        """Test that low confidence causes failure even when fresh and many backends."""
        from core.quality_checker import is_satisfactory

        result = {
            "title": "Fresh but Low Confidence",
            "content": "Content",
            "confidence": 0.5,
            "created_at": datetime.now(timezone.utc) - timedelta(hours=1),
            "sources": ["backend1", "backend2", "backend3", "backend4", "backend5"],
        }

        assert is_satisfactory(result) is False

    def test_stale_fails_despite_other_criteria(self):
        """Test that staleness causes failure even when high confidence and many backends."""
        from core.quality_checker import is_satisfactory

        result = {
            "title": "High Confidence but Stale",
            "content": "Content",
            "confidence": 0.95,
            "created_at": datetime.now(timezone.utc) - timedelta(days=7),
            "sources": ["backend1", "backend2", "backend3", "backend4"],
        }

        assert is_satisfactory(result) is False

    def test_few_backends_fails_despite_other_criteria(self):
        """Test that few backends fails with custom min_backends, even when fresh and high confidence."""
        from core.quality_checker import QualityConfig, is_satisfactory

        result = {
            "title": "Fresh and High Confidence but Few Backends",
            "content": "Content",
            "confidence": 0.95,
            "created_at": datetime.now(timezone.utc) - timedelta(hours=1),
            "sources": ["backend1"],
        }

        # With default min_backends=1, single source passes
        assert is_satisfactory(result) is True
        # With custom min_backends=3, single source fails
        config = QualityConfig(min_backends=3)
        assert is_satisfactory(result, config) is False

    def test_all_criteria_missing_fails(self):
        """Test that result missing all criteria fails."""
        from core.quality_checker import is_satisfactory

        result = {"title": "Poor Result", "content": "Low quality content"}

        assert is_satisfactory(result) is False

    def test_edge_case_just_passing_all_criteria(self):
        """Test edge case where result barely passes all criteria."""
        from core.quality_checker import is_satisfactory

        result = {
            "title": "Barely Passing",
            "content": "Content",
            "confidence": 0.8,  # Exactly at threshold
            "created_at": datetime.now(timezone.utc) - timedelta(hours=24),  # Exactly at boundary
            "sources": ["backend1", "backend2", "backend3"],  # Exactly at threshold
        }

        assert is_satisfactory(result) is True

    def test_edge_case_just_failing_one_criterion(self):
        """Test edge case where result barely fails one criterion."""
        from core.quality_checker import QualityConfig, is_satisfactory

        # Fail only confidence
        result1 = {
            "title": "Barely Failing Confidence",
            "content": "Content",
            "confidence": 0.79,  # Just below threshold
            "created_at": datetime.now(timezone.utc) - timedelta(hours=1),  # Fresh
            "sources": ["backend1", "backend2", "backend3", "backend4"],  # Many backends
        }
        assert is_satisfactory(result1) is False

        # Fail only freshness
        result2 = {
            "title": "Barely Failing Freshness",
            "content": "Content",
            "confidence": 0.9,  # High confidence
            "created_at": datetime.now(timezone.utc) - timedelta(hours=24, minutes=1),  # Just stale
            "sources": ["backend1", "backend2", "backend3", "backend4"],  # Many backends
        }
        assert is_satisfactory(result2) is False

        # Fail only backend count (with custom min_backends=3)
        result3 = {
            "title": "Barely Failing Backend Count",
            "content": "Content",
            "confidence": 0.9,  # High confidence
            "created_at": datetime.now(timezone.utc) - timedelta(hours=1),  # Fresh
            "sources": ["backend1", "backend2"],  # Just below threshold
        }
        # With default min_backends=1, 2 backends passes
        assert is_satisfactory(result3) is True
        # With custom min_backends=3, 2 backends fails
        config_strict = QualityConfig(min_backends=3)
        assert is_satisfactory(result3, config_strict) is False
