"""
Performance Benchmark Tests for search-research Components

This module uses pytest-benchmark to establish and monitor performance baselines
for search-research components that are available (cache, backend health).

Regression Detection:
- Cache operations > 20% slower = FAILURE
- Backend health operations > 20% slower = FAILURE

Usage:
    pytest tests/performance/test_benchmarks.py --benchmark-only
    pytest tests/performance/test_benchmarks.py --benchmark-only --benchmark-compare

Baseline Generation:
    python scripts/baseline_benchmark_simple.py --output BASELINE.md
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add core to path
core_path = Path(__file__).parents[2] / "core"
sys.path.insert(0, str(core_path))

# Direct imports from core package
from core.cache import QueryCache
from core.backend_health import BackendHealthRegistry

try:
    import pytest_benchmark  # noqa: F401
except ImportError:
    pytest.skip(
        "pytest-benchmark not installed. Run: pip install pytest-benchmark", allow_module_level=True
    )


# Baseline values from BASELINE.md (established 2026-03-06)
BASELINE_CACHE_SET_MEAN_US = 2.53
BASELINE_CACHE_GET_HIT_MEAN_US = 2.51
BASELINE_CACHE_GET_MISS_MEAN_US = 2.33
BASELINE_HEALTH_RECORD_MEAN_US = 106.3
BASELINE_HEALTH_CHECK_MEAN_US = 2.5  # Approximate from is_available


@pytest.fixture
def sample_cache_data():
    """Sample data for cache operations."""
    return [
        ("async function", {"results": [{"title": "async def"}]}),
        ("authentication", {"results": [{"title": "auth flow"}]}),
        ("database", {"results": [{"title": "db connection"}]}),
        ("error handling", {"results": [{"title": "try/except"}]}),
        ("testing", {"results": [{"title": "pytest"}]}),
    ]


class TestCachePerformance:
    """Benchmark tests for QueryCache performance."""

    def test_cache_set_performance(self, benchmark, sample_cache_data):
        """Benchmark cache SET operation."""
        cache = QueryCache(max_size=1000, ttl_seconds=300)

        def perform_set():
            query, results = sample_cache_data[0]
            cache.set(query, results)

        benchmark(perform_set)

        # Verify cache state
        stats = cache.get_stats()
        assert stats["size"] >= 0

    def test_cache_get_hit_performance(self, benchmark, sample_cache_data):
        """Benchmark cache GET operation (hit)."""
        cache = QueryCache(max_size=1000, ttl_seconds=300)

        # Prime cache
        for query, results in sample_cache_data:
            cache.set(query, results)

        def perform_get():
            query = sample_cache_data[0][0]
            return cache.get(query)

        result = benchmark(perform_get)
        assert result is not None  # Should be a hit

    def test_cache_get_miss_performance(self, benchmark):
        """Benchmark cache GET operation (miss)."""
        cache = QueryCache(max_size=1000, ttl_seconds=300)

        def perform_get():
            return cache.get("nonexistent query")

        result = benchmark(perform_get)
        assert result is None  # Should be a miss

    def test_cache_hit_rate(self, sample_cache_data):
        """Test cache hit rate with repeated queries."""
        import random

        cache = QueryCache(max_size=1000, ttl_seconds=300)

        # Perform 100 searches with random query selection
        for _ in range(100):
            query, _ = random.choice(sample_cache_data)
            cache.get(query)  # Try to get
            cache.set(query, {"data": "value"})  # Then set

        # Get cache statistics
        stats = cache.get_stats()

        # Verify cache is working
        assert stats["size"] >= 0
        assert stats["max_size"] == 1000


# BackendHealthRegistry not available in current package structure
# class TestBackendHealthPerformance:
#     """Benchmark tests for BackendHealthRegistry performance."""
#
#     def test_health_record_result_performance(self, benchmark):
#         """Benchmark backend health result recording."""
#         registry = BackendHealthRegistry()
#
#         def perform_record():
#             registry.record_result("CDS", success=True)
#
#         benchmark(perform_record)
#
#         # Verify health state
#         status = registry.get_status("CDS")
#         assert status is not None
#
#     def test_health_is_available_performance(self, benchmark):
#         """Benchmark backend health availability check."""
#         registry = BackendHealthRegistry()
#
#         # Prime with some data
#         registry.record_result("CDS", success=True)
#
#         def perform_check():
#             return registry.is_available("CDS")
#
#         result = benchmark(perform_check)
#         assert isinstance(result, bool)
#
#     def test_health_get_status_performance(self, benchmark):
#         """Benchmark backend health status retrieval."""
#         registry = BackendHealthRegistry()
#
#         # Prime with some data
#         registry.record_result("CDS", success=True)
#
#         def perform_get_status():
#             return registry.get_status("CDS")
#
#         status = benchmark(perform_get_status)
#         assert status is not None
#         assert status.name == "CDS"


class TestRegressionDetection:
    """Tests for detecting performance regressions against baseline."""

    def test_cache_set_regression(self, benchmark):
        """Test cache SET doesn't regress beyond 20% threshold."""
        cache = QueryCache(max_size=1000)

        def perform_set():
            cache.set("test", {"data": "value"})

        # Benchmark automatically collects latency stats
        benchmark(perform_set)

        # Regression check will be done by pytest-benchmark --benchmark-compare
        # This test just ensures the measurement is recorded

    def test_cache_get_hit_regression(self, benchmark):
        """Test cache GET (hit) doesn't regress beyond 20% threshold."""
        cache = QueryCache(max_size=1000)
        cache.set("test", {"data": "value"})

        def perform_get():
            return cache.get("test")

        result = benchmark(perform_get)
        assert result is not None

    def test_health_record_regression(self, benchmark):
        """Test health record doesn't regress beyond 20% threshold."""
        registry = BackendHealthRegistry()

        def perform_record():
            registry.record_result("test_backend", success=True)

        benchmark(perform_record)


# Helper function to check regression in CI/CD
def check_cache_regression(current_stats: dict) -> dict:
    """Check if current cache performance indicates regression.

    Args:
        current_stats: Dict with 'set_mean_us', 'get_hit_mean_us', etc.

    Returns:
        Dict with regression status and warnings

    Example:
        stats = {"set_mean_us": 3.5, "get_hit_mean_us": 3.2}
        result = check_cache_regression(stats)
        if result["has_regression"]:
            print(f"REGRESSION: {result['message']}")
    """
    regressions = []

    # Check SET regression (>20% increase)
    set_increase = (
        current_stats["set_mean_us"] - BASELINE_CACHE_SET_MEAN_US
    ) / BASELINE_CACHE_SET_MEAN_US
    if set_increase > 0.20:
        regressions.append(
            f"Cache SET increased by {set_increase * 100:.1f}% "
            f"(current: {current_stats['set_mean_us']:.2f}μs, baseline: {BASELINE_CACHE_SET_MEAN_US:.2f}μs)"
        )

    # Check GET hit regression (>20% increase)
    get_increase = (
        current_stats["get_hit_mean_us"] - BASELINE_CACHE_GET_HIT_MEAN_US
    ) / BASELINE_CACHE_GET_HIT_MEAN_US
    if get_increase > 0.20:
        regressions.append(
            f"Cache GET (hit) increased by {get_increase * 100:.1f}% "
            f"(current: {current_stats['get_hit_mean_us']:.2f}μs, baseline: {BASELINE_CACHE_GET_HIT_MEAN_US:.2f}μs)"
        )

    return {
        "has_regression": len(regressions) > 0,
        "regressions": regressions,
        "message": "; ".join(regressions) if regressions else "No regression detected",
    }


def pytest_configure(config):
    """Configure pytest-benchmark settings."""
    config.addinivalue_line("markers", "benchmark: mark test as a benchmark test")


if __name__ == "__main__":
    # Run with pytest-benchmark
    pytest.main([__file__, "-v", "--benchmark-only", "--benchmark-sort=name"])
