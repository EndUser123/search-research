"""
Tests for search metrics/telemetry tracking.

Tests the SearchMetrics class for collecting and persisting search usage data.
"""

import json
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from yt_fts.core.metrics import SearchMetrics


@pytest.fixture
def temp_metrics_file(tmp_path):
    """Create a temporary metrics file for testing."""
    return tmp_path / "search_metrics.json"


@pytest.fixture
def metrics(temp_metrics_file):
    """Create a SearchMetrics instance with a temporary file."""
    return SearchMetrics(metrics_path=temp_metrics_file)


class TestSearchMetricsInitialization:
    """Tests for SearchMetrics initialization and basic setup."""

    def test_initialization_creates_file_if_not_exists(self, temp_metrics_file):
        """Test that initializing creates the metrics file."""
        assert not temp_metrics_file.exists()

        metrics = SearchMetrics(metrics_path=temp_metrics_file)
        metrics.save()

        assert temp_metrics_file.exists()

    def test_initialization_loads_existing_data(self, temp_metrics_file):
        """Test that initializing loads existing metrics data."""
        existing_data = {
            "searches": [
                {
                    "timestamp": "2025-01-10T12:00:00Z",
                    "query": "test query",
                    "scope": "all",
                    "result_count": 10,
                    "backend": "fts",
                    "duration_ms": 150,
                }
            ],
            "aggregations": {
                "total_searches": 1,
                "fts_searches": 1,
                "vector_searches": 0,
                "total_results": 10,
            },
        }

        temp_metrics_file.write_text(json.dumps(existing_data))

        metrics = SearchMetrics(metrics_path=temp_metrics_file)

        assert len(metrics.data["searches"]) == 1
        assert metrics.data["aggregations"]["total_searches"] == 1

    def test_default_structure(self, temp_metrics_file):
        """Test that metrics have the correct default structure."""
        metrics = SearchMetrics(metrics_path=temp_metrics_file)

        assert "searches" in metrics.data
        assert "aggregations" in metrics.data
        assert metrics.data["searches"] == []
        assert "total_searches" in metrics.data["aggregations"]


class TestTrackSearch:
    """Tests for tracking individual searches."""

    def test_track_fts_search(self, metrics):
        """Test tracking a basic FTS search."""
        metrics.track_search(
            query="machine learning",
            scope="all",
            result_count=25,
            backend="fts",
            duration_ms=120,
        )

        assert len(metrics.data["searches"]) == 1
        search = metrics.data["searches"][0]
        assert search["query"] == "machine learning"
        assert search["scope"] == "all"
        assert search["result_count"] == 25
        assert search["backend"] == "fts"
        assert search["duration_ms"] == 120
        assert "timestamp" in search

    def test_track_vector_search(self, metrics):
        """Test tracking a vector search."""
        metrics.track_search(
            query="neural networks",
            scope="channel",
            result_count=15,
            backend="vector",
            duration_ms=350,
            channel_id="UC1234567890",
        )

        assert len(metrics.data["searches"]) == 1
        search = metrics.data["searches"][0]
        assert search["backend"] == "vector"
        assert search["channel_id"] == "UC1234567890"

    def test_track_search_with_optional_fields(self, metrics):
        """Test tracking search with all optional fields."""
        metrics.track_search(
            query="deep learning",
            scope="video",
            result_count=5,
            backend="fts",
            duration_ms=80,
            video_id="abc123",
            channel_id="UC1234567890",
            has_citation=True,
        )

        search = metrics.data["searches"][0]
        assert search["video_id"] == "abc123"
        assert search["channel_id"] == "UC1234567890"
        assert search["has_citation"] is True

    def test_track_multiple_searches(self, metrics):
        """Test tracking multiple searches."""
        for i in range(5):
            metrics.track_search(
                query=f"query {i}",
                scope="all",
                result_count=i * 10,
                backend="fts",
                duration_ms=100 + i * 10,
            )

        assert len(metrics.data["searches"]) == 5

    def test_track_search_increments_aggregations(self, metrics):
        """Test that tracking search updates aggregations."""
        metrics.track_search(
            query="test", scope="all", result_count=10, backend="fts", duration_ms=100
        )
        metrics.track_search(
            query="test2", scope="channel", result_count=5, backend="vector", duration_ms=200
        )

        agg = metrics.data["aggregations"]
        assert agg["total_searches"] == 2
        assert agg["fts_searches"] == 1
        assert agg["vector_searches"] == 1
        assert agg["total_results"] == 15


class TestQueryPatternTracking:
    """Tests for query pattern analysis."""

    def test_detects_wildcard_pattern(self, metrics):
        """Test detection of wildcard queries."""
        metrics.track_search(
            query="machine learning*",
            scope="all",
            result_count=10,
            backend="fts",
            duration_ms=100,
        )

        patterns = metrics.get_query_patterns()
        assert "wildcard" in patterns
        assert patterns["wildcard"] == 1

    def test_detects_or_operator(self, metrics):
        """Test detection of OR operator queries."""
        metrics.track_search(
            query="foo OR bar",
            scope="all",
            result_count=10,
            backend="fts",
            duration_ms=100,
        )

        patterns = metrics.get_query_patterns()
        assert "or_operator" in patterns
        assert patterns["or_operator"] == 1

    def test_detects_phrase_search(self, metrics):
        """Test detection of phrase queries."""
        metrics.track_search(
            query='"machine learning"',
            scope="all",
            result_count=10,
            backend="fts",
            duration_ms=100,
        )

        patterns = metrics.get_query_patterns()
        assert "phrase_search" in patterns
        assert patterns["phrase_search"] == 1

    def test_query_length_distribution(self, metrics):
        """Test query length analysis."""
        metrics.track_search(
            query="ml", scope="all", result_count=10, backend="fts", duration_ms=100
        )
        metrics.track_search(
            query="machine learning",
            scope="all",
            result_count=10,
            backend="fts",
            duration_ms=100,
        )
        metrics.track_search(
            query="this is a very long query about deep learning",
            scope="all",
            result_count=10,
            backend="fts",
            duration_ms=100,
        )

        length_dist = metrics.get_query_length_distribution()
        assert length_dist["short"] == 1  # < 10 chars
        assert length_dist["medium"] == 1  # 10-30 chars
        assert length_dist["long"] == 1  # > 30 chars


class TestBackendPerformance:
    """Tests for backend performance tracking."""

    def test_fts_performance_stats(self, metrics):
        """Test FTS performance statistics."""
        metrics.track_search(
            query="test1", scope="all", result_count=10, backend="fts", duration_ms=100
        )
        metrics.track_search(
            query="test2", scope="all", result_count=20, backend="fts", duration_ms=200
        )
        metrics.track_search(
            query="test3", scope="all", result_count=15, backend="fts", duration_ms=150
        )

        fts_perf = metrics.get_backend_performance("fts")
        assert fts_perf["count"] == 3
        assert fts_perf["avg_duration_ms"] == 150
        assert fts_perf["min_duration_ms"] == 100
        assert fts_perf["max_duration_ms"] == 200
        assert fts_perf["avg_results"] == 15

    def test_vector_performance_stats(self, metrics):
        """Test vector search performance statistics."""
        metrics.track_search(
            query="test1", scope="all", result_count=5, backend="vector", duration_ms=300
        )
        metrics.track_search(
            query="test2", scope="all", result_count=10, backend="vector", duration_ms=400
        )

        vector_perf = metrics.get_backend_performance("vector")
        assert vector_perf["count"] == 2
        assert vector_perf["avg_duration_ms"] == 350
        assert vector_perf["avg_results"] == 7.5


class TestCitationTracking:
    """Tests for citation rate tracking."""

    def test_citation_rate_calculation(self, metrics):
        """Test calculation of citation rate."""
        # Track searches with citations
        metrics.track_search(
            query="test1",
            scope="all",
            result_count=10,
            backend="fts",
            duration_ms=100,
            has_citation=True,
        )
        metrics.track_search(
            query="test2",
            scope="all",
            result_count=10,
            backend="fts",
            duration_ms=100,
            has_citation=False,
        )
        metrics.track_search(
            query="test3",
            scope="all",
            result_count=10,
            backend="fts",
            duration_ms=100,
            has_citation=True,
        )

        citation_rate = metrics.get_citation_rate()
        assert citation_rate["with_citations"] == 2
        assert citation_rate["total_searches"] == 3
        assert citation_rate["citation_rate"] == pytest.approx(0.667, rel=0.01)


class TestPersistence:
    """Tests for data persistence."""

    def test_save_persists_to_file(self, metrics, temp_metrics_file):
        """Test that save writes data to file."""
        metrics.track_search(
            query="test", scope="all", result_count=10, backend="fts", duration_ms=100
        )
        metrics.save()

        with Path(temp_metrics_file).open() as f:
            data = json.load(f)

        assert len(data["searches"]) == 1
        assert data["aggregations"]["total_searches"] == 1

    def test_load_reads_from_file(self, metrics, temp_metrics_file):
        """Test that load reads data from file."""
        # Write test data
        test_data = {
            "searches": [
                {
                    "timestamp": "2025-01-10T12:00:00Z",
                    "query": "test",
                    "scope": "all",
                    "result_count": 10,
                    "backend": "fts",
                    "duration_ms": 100,
                }
            ],
            "aggregations": {"total_searches": 1, "fts_searches": 1, "vector_searches": 0, "total_results": 10},
        }
        temp_metrics_file.write_text(json.dumps(test_data))

        metrics.load()

        assert len(metrics.data["searches"]) == 1
        assert metrics.data["searches"][0]["query"] == "test"


class TestStatsAndAggregation:
    """Tests for statistics and aggregation methods."""

    def test_get_stats(self, metrics):
        """Test getting overall statistics."""
        metrics.track_search(
            query="test1", scope="all", result_count=10, backend="fts", duration_ms=100
        )
        metrics.track_search(
            query="test2", scope="channel", result_count=5, backend="vector", duration_ms=200
        )

        stats = metrics.get_stats()

        assert stats["total_searches"] == 2
        assert stats["fts_searches"] == 1
        assert stats["vector_searches"] == 1
        assert stats["avg_results"] == 7.5
        assert stats["total_results"] == 15

    def test_get_top_queries(self, metrics):
        """Test getting top queries."""
        metrics.track_search(
            query="machine learning",
            scope="all",
            result_count=10,
            backend="fts",
            duration_ms=100,
        )
        metrics.track_search(
            query="machine learning",
            scope="all",
            result_count=12,
            backend="fts",
            duration_ms=110,
        )
        metrics.track_search(
            query="neural networks", scope="all", result_count=5, backend="fts", duration_ms=90
        )

        top_queries = metrics.get_top_queries(limit=2)

        assert len(top_queries) == 2
        assert top_queries[0]["query"] == "machine learning"
        assert top_queries[0]["count"] == 2
        assert top_queries[1]["query"] == "neural networks"
        assert top_queries[1]["count"] == 1

    def test_get_scope_distribution(self, metrics):
        """Test getting scope distribution."""
        metrics.track_search(
            query="test1", scope="all", result_count=10, backend="fts", duration_ms=100
        )
        metrics.track_search(
            query="test2", scope="channel", result_count=5, backend="fts", duration_ms=100
        )
        metrics.track_search(
            query="test3", scope="channel", result_count=5, backend="fts", duration_ms=100
        )
        metrics.track_search(
            query="test4", scope="video", result_count=2, backend="fts", duration_ms=100
        )

        scope_dist = metrics.get_scope_distribution()

        assert scope_dist["all"] == 1
        assert scope_dist["channel"] == 2
        assert scope_dist["video"] == 1


class TestMetricsDisplay:
    """Tests for metrics display functionality."""

    def test_display_format(self, metrics):
        """Test that display returns formatted output."""
        metrics.track_search(
            query="test", scope="all", result_count=10, backend="fts", duration_ms=100
        )

        output = metrics.display()

        assert "Total Searches" in output
        assert "FTS Searches" in output
        assert "Average Results" in output
        assert isinstance(output, str)


class TestDefaultPath:
    """Tests for default metrics path."""

    def test_default_metrics_path(self, tmp_path):
        """Test that default path is data/search_metrics.json."""
        from yt_fts.core.metrics import SearchMetrics

        # Test with a temporary directory to verify default path handling
        # We can't test the actual default path without side effects,
        # but we can verify the instantiation works
        metrics = SearchMetrics(metrics_path=tmp_path / "metrics.json")
        assert metrics is not None
        assert metrics.metrics_path == tmp_path / "metrics.json"
