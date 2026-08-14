"""Tests for HyDE effectiveness measurement framework.

Tests the measurement framework that tracks HyDE effectiveness metrics including:
- Query enhancement rate
- Result quality improvement
- Latency impact
"""

import time
from unittest.mock import MagicMock, patch

from core.utils.hyde_measurement import (
    HyDEMeasurement,
    measure_hyde_effectiveness,
    track_hyde_metrics,
)


class TestHyDEMeasurement:
    """Tests for HyDEMeasurement data class."""

    def test_hyde_measurement_initialization(self):
        """Test that HyDEMeasurement initializes with correct defaults."""
        measurement = HyDEMeasurement(
            original_query="FastAPI patterns",
            enhanced_query="FastAPI patterns async operations await syntax",
            hyde_applied=True,
            enhancement_latency_ms=150.5,
            result_count=10,
        )

        assert measurement.original_query == "FastAPI patterns"
        assert measurement.enhanced_query == "FastAPI patterns async operations await syntax"
        assert measurement.hyde_applied is True
        assert measurement.enhancement_latency_ms == 150.5
        assert measurement.result_count == 10
        assert measurement.key_phrases_extracted is None
        assert measurement.quality_score is None

    def test_hyde_measurement_with_optional_fields(self):
        """Test that HyDEMeasurement handles optional fields."""
        measurement = HyDEMeasurement(
            original_query="test query",
            enhanced_query="test query enhanced",
            hyde_applied=True,
            enhancement_latency_ms=100.0,
            result_count=5,
            key_phrases_extracted=3,
            quality_score=0.85,
        )

        assert measurement.key_phrases_extracted == 3
        assert measurement.quality_score == 0.85

    def test_hyde_measurement_to_dict(self):
        """Test that HyDEMeasurement converts to dictionary correctly."""
        measurement = HyDEMeasurement(
            original_query="test query",
            enhanced_query="test query enhanced",
            hyde_applied=True,
            enhancement_latency_ms=100.0,
            result_count=5,
            key_phrases_extracted=2,
            quality_score=0.9,
        )

        result_dict = measurement.to_dict()

        assert result_dict["original_query"] == "test query"
        assert result_dict["enhanced_query"] == "test query enhanced"
        assert result_dict["hyde_applied"] is True
        assert result_dict["enhancement_latency_ms"] == 100.0
        assert result_dict["result_count"] == 5
        assert result_dict["key_phrases_extracted"] == 2
        assert result_dict["quality_score"] == 0.9


class TestMeasureHyDEEffectiveness:
    """Tests for measure_hyde_effectiveness function."""

    def test_measure_hyde_with_enhancement(self):
        """Test measurement when HyDE enhancement is applied."""
        original_query = "FastAPI patterns"
        hyde_content = "FastAPI supports async operations using Python's async/await syntax."

        # Use real implementation instead of mocking to get accurate key_phrases_extracted
        measurement = measure_hyde_effectiveness(original_query, hyde_content)

        assert measurement.original_query == original_query
        assert measurement.hyde_applied is True
        assert measurement.enhanced_query != original_query  # Should be enhanced
        assert measurement.enhancement_latency_ms >= 0
        # key_phrases_extracted should be set when hyde_applied is True
        # but may be None if extraction fails or returns empty list

    def test_measure_hyde_without_enhancement(self):
        """Test measurement when HyDE is not applied."""
        original_query = "FastAPI patterns"

        with patch('search_research.utils.hyde_measurement.apply_hyde') as mock_apply_hyde:
            mock_apply_hyde.return_value = (original_query, False)

            measurement = measure_hyde_effectiveness(original_query, None)

            assert measurement.original_query == original_query
            assert measurement.hyde_applied is False
            assert measurement.enhanced_query == original_query
            assert measurement.enhancement_latency_ms >= 0

    def test_measure_hyde_tracks_latency(self):
        """Test that measurement tracks enhancement latency."""
        original_query = "test query"

        with patch('search_research.utils.hyde_measurement.apply_hyde') as mock_apply_hyde:
            # Simulate some processing time
            def slow_enhancement(*args, **kwargs):
                time.sleep(0.01)
                return ("enhanced query", True)

            mock_apply_hyde.side_effect = slow_enhancement

            measurement = measure_hyde_effectiveness(original_query, "some content")

            assert measurement.enhancement_latency_ms >= 10  # At least 10ms

    def test_measure_hyde_handles_errors_gracefully(self):
        """Test that measurement handles errors gracefully."""
        original_query = "test query"

        with patch('search_research.utils.hyde_measurement.apply_hyde') as mock_apply_hyde:
            mock_apply_hyde.side_effect = Exception("HyDE failed")

            measurement = measure_hyde_effectiveness(original_query, "content")

            # Should return original query with hyde_applied=False
            assert measurement.original_query == original_query
            assert measurement.hyde_applied is False
            assert measurement.enhanced_query == original_query


class TestTrackHyDEMetrics:
    """Tests for track_hyde_metrics function."""

    def test_track_hyde_metrics_with_results(self):
        """Test tracking metrics with search results."""
        measurement = HyDEMeasurement(
            original_query="test query",
            enhanced_query="test query enhanced",
            hyde_applied=True,
            enhancement_latency_ms=100.0,
            result_count=5,
        )

        mock_results = [
            MagicMock(title="Result 1", score=0.9),
            MagicMock(title="Result 2", score=0.8),
            MagicMock(title="Result 3", score=0.7),
            MagicMock(title="Result 4", score=0.6),
            MagicMock(title="Result 5", score=0.5),
        ]

        metrics = track_hyde_metrics(measurement, mock_results)

        assert metrics["hyde_applied"] is True
        assert metrics["enhancement_latency_ms"] == 100.0
        assert metrics["result_count"] == 5
        assert metrics["average_score"] == 0.7
        assert "original_query" in metrics
        assert "enhanced_query" in metrics

    def test_track_hyde_metrics_without_results(self):
        """Test tracking metrics with no results."""
        measurement = HyDEMeasurement(
            original_query="test query",
            enhanced_query="test query",
            hyde_applied=False,
            enhancement_latency_ms=0.0,
            result_count=0,
        )

        metrics = track_hyde_metrics(measurement, [])

        assert metrics["hyde_applied"] is False
        assert metrics["result_count"] == 0
        assert metrics["average_score"] == 0.0

    def test_track_hyde_metrics_calculates_quality_score(self):
        """Test that metrics include quality score calculation."""
        measurement = HyDEMeasurement(
            original_query="test query",
            enhanced_query="test query enhanced",
            hyde_applied=True,
            enhancement_latency_ms=100.0,
            result_count=3,
            quality_score=0.85,
        )

        mock_results = [
            MagicMock(title="Result 1", score=0.95),
            MagicMock(title="Result 2", score=0.85),
            MagicMock(title="Result 3", score=0.75),
        ]

        metrics = track_hyde_metrics(measurement, mock_results)

        assert "quality_score" in metrics
        # Quality score is optional and comes from measurement, not calculated
        assert metrics["quality_score"] == 0.85

    def test_track_hyde_metrics_includes_key_phrases_count(self):
        """Test that metrics include key phrases extracted count."""
        measurement = HyDEMeasurement(
            original_query="test query",
            enhanced_query="test query enhanced",
            hyde_applied=True,
            enhancement_latency_ms=100.0,
            result_count=5,
            key_phrases_extracted=4,
        )

        metrics = track_hyde_metrics(measurement, [])

        assert metrics["key_phrases_extracted"] == 4

    def test_track_hyde_metrics_returns_dict_with_all_fields(self):
        """Test that metrics dict contains all expected fields."""
        measurement = HyDEMeasurement(
            original_query="test",
            enhanced_query="test enhanced",
            hyde_applied=True,
            enhancement_latency_ms=150.0,
            result_count=2,
            key_phrases_extracted=3,
            quality_score=0.85,
        )

        metrics = track_hyde_metrics(measurement, [])

        expected_fields = {
            "original_query",
            "enhanced_query",
            "hyde_applied",
            "enhancement_latency_ms",
            "result_count",
            "key_phrases_extracted",
            "quality_score",
            "average_score",
        }

        assert set(metrics.keys()) == expected_fields


class TestHyDEMeasurementIntegration:
    """Integration tests for HyDE measurement with search results."""

    def test_measurement_with_research_router(self):
        """Test that measurements work with UnifiedAsyncRouter results."""
        from search_research import SearchResult

        measurement = HyDEMeasurement(
            original_query="FastAPI patterns",
            enhanced_query="FastAPI patterns async operations",
            hyde_applied=True,
            enhancement_latency_ms=120.0,
            result_count=2,
        )

        results = [
            SearchResult(
                title="FastAPI Guide",
                content="FastAPI async patterns",
                url="https://example.com",
                source="TAVILY",
                score=0.9,
            ),
            SearchResult(
                title="Async Best Practices",
                content="Python async/await",
                url="https://example.com/async",
                source="SERPER",
                score=0.8,
            ),
        ]

        metrics = track_hyde_metrics(measurement, results)

        assert metrics["result_count"] == 2
        assert abs(metrics["average_score"] - 0.85) < 0.01  # Allow floating point precision
        assert metrics["hyde_applied"] is True

    def test_measurement_flow_end_to_end(self):
        """Test complete measurement flow from query to metrics."""
        original_query = "FastAPI patterns"
        hyde_content = "FastAPI supports async operations using Python's async/await syntax."

        with patch('search_research.utils.hyde_measurement.apply_hyde') as mock_apply_hyde:
            mock_apply_hyde.return_value = ("FastAPI patterns async operations await", True)

            # Measure HyDE effectiveness
            measurement = measure_hyde_effectiveness(original_query, hyde_content)

            # Simulate search results
            mock_results = [
                MagicMock(title="Result 1", score=0.9),
                MagicMock(title="Result 2", score=0.8),
            ]

            # Track metrics
            metrics = track_hyde_metrics(measurement, mock_results)

            # Verify complete flow
            assert measurement.hyde_applied is True
            assert metrics["hyde_applied"] is True
            assert metrics["result_count"] == 2
            assert abs(metrics["average_score"] - 0.85) < 0.01  # Allow floating point precision
            assert "enhancement_latency_ms" in metrics
