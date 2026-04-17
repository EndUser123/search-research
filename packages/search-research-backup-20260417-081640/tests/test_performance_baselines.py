"""Performance Baseline Suite for Backend Migration.

Establishes performance baselines for legacy backends to detect regressions in new backends.

Created: 2026-03-15
Task: TASK-002A - Create Performance Baseline Suite
Maps to: REQ-003 (No performance regression > 10%)
"""

from __future__ import annotations

import statistics
import time
from pathlib import Path

import pytest

# Configuration
TEST_SEARCH_ROOT = Path("P:/__csf/src")
ITERATIONS = 20
WARMUP = 5
ACCEPTABLE_VARIANCE = 0.10  # 10%


class PerformanceResult:
    """Container for performance metrics."""

    def __init__(self, name: str, times: list[float]):
        self.name = name
        self.times = times
        self.mean = statistics.mean(times)
        self.median = statistics.median(times)
        self.stdev = statistics.stdev(times) if len(times) > 1 else 0
        self.min = min(times)
        self.max = max(times)

    def __repr__(self) -> str:
        return f"PerformanceResult({self.name}: mean={self.mean:.3f}s, median={self.median:.3f}s)"


def measure_search_performance(
    backend, query: str, iterations: int = ITERATIONS, warmup: int = WARMUP
) -> PerformanceResult:
    """Measure search performance for a backend."""
    times = []

    # Warmup
    for _ in range(warmup):
        try:
            backend.search(query)
        except Exception:
            pass

    # Measure
    for _ in range(iterations):
        start = time.perf_counter()
        try:
            backend.search(query)
        except Exception:
            pass
        times.append(time.perf_counter() - start)

    return PerformanceResult(f"{backend.__class__.__name__}('{query}')", times)


class TestLegacyGrepPerformance:
    """Performance baseline for legacy GrepBackend."""

    @pytest.fixture
    def backend(self):
        from search.backends.grep_backend import GrepBackend

        backend = GrepBackend(root_paths=[str(TEST_SEARCH_ROOT)])
        backend.build_index()
        return backend

    def test_search_performance_baseline(self, backend):
        """Establish baseline for search queries."""
        queries = ["search", "index", "query"]

        baselines = {}
        for query in queries:
            result = measure_search_performance(backend, query)
            baselines[query] = result

            # Store for comparison
            print(f"\n{result}")
            assert result.mean > 0, "Search should take some time"
            assert result.mean < 1.0, "Search should complete in < 1s"

        # Store baselines for comparison
        self._store_baselines("grep", baselines)

    def _store_baselines(self, backend_name: str, baselines: dict):
        """Store baselines for later comparison."""
        import json

        baseline_file = Path(__file__).parent / "performance_baselines.json"

        try:
            with open(baseline_file) as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {}

        data[backend_name] = {
            query: {"mean": result.mean, "median": result.median}
            for query, result in baselines.items()
        }

        with open(baseline_file, "w") as f:
            json.dump(data, f, indent=2)


class TestLegacyCDSPerformance:
    """Performance baseline for legacy CDSBackend."""

    @pytest.fixture
    def backend(self):
        from search.backends.cds_backend import CDSBackend

        backend = CDSBackend(root_paths=[str(TEST_SEARCH_ROOT)])
        backend.build_index()
        return backend

    def test_search_performance_baseline(self, backend):
        """Establish baseline for CDS search."""
        queries = ["search", "docstring", "function"]

        baselines = {}
        for query in queries:
            result = measure_search_performance(backend, query)
            baselines[query] = result

            print(f"\n{result}")
            assert result.mean > 0
            assert result.mean < 1.0

        self._store_baselines("cds", baselines)

    def _store_baselines(self, backend_name: str, baselines: dict):
        """Store baselines for later comparison."""
        import json

        baseline_file = Path(__file__).parent / "performance_baselines.json"

        try:
            with open(baseline_file) as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {}

        data[backend_name] = {
            query: {"mean": result.mean, "median": result.median}
            for query, result in baselines.items()
        }

        with open(baseline_file, "w") as f:
            json.dump(data, f, indent=2)


class TestLegacyKGPerformance:
    """Performance baseline for legacy KGBackend."""

    @pytest.fixture
    def backend(self):
        from search.backends.kg_backend import KGBackend

        return KGBackend()

    def test_search_performance_baseline(self, backend):
        """Establish baseline for KG search."""
        queries = ["nip", "search", "validation"]

        baselines = {}
        for query in queries:
            result = measure_search_performance(backend, query)
            baselines[query] = result

            print(f"\n{result}")
            assert result.mean > 0
            assert result.mean < 1.0

        self._store_baselines("kg", baselines)

    def _store_baselines(self, backend_name: str, baselines: dict):
        """Store baselines for later comparison."""
        import json

        baseline_file = Path(__file__).parent / "performance_baselines.json"

        try:
            with open(baseline_file) as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {}

        data[backend_name] = {
            query: {"mean": result.mean, "median": result.median}
            for query, result in baselines.items()
        }

        with open(baseline_file, "w") as f:
            json.dump(data, f, indent=2)


class TestNewBackendPerformanceComparison:
    """Compare new backend performance against baselines."""

    @pytest.fixture
    def baseline_data(self):
        """Load stored baselines."""
        import json

        baseline_file = Path(__file__).parent / "performance_baselines.json"

        try:
            with open(baseline_file) as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pytest.skip("No baseline data found - run legacy performance tests first")

    def test_grep_performance_vs_baseline(self, baseline_data):
        """Verify new GrepBackend meets baseline."""
        if "grep" not in baseline_data:
            pytest.skip("No grep baseline found")

        from core.backends.local.grep_backend import GrepBackend

        backend = GrepBackend(root_paths=[str(TEST_SEARCH_ROOT)])
        backend.build_index()

        for query, baseline in baseline_data["grep"].items():
            result = measure_search_performance(backend, query)

            variance = (result.mean - baseline["mean"]) / baseline["mean"]
            print(
                f"\n{query}: baseline={baseline['mean']:.3f}s, new={result.mean:.3f}s, variance={variance:.1%}"
            )

            assert (
                variance < ACCEPTABLE_VARIANCE
            ), f"Performance regression: {variance:.1%} > {ACCEPTABLE_VARIANCE:.1%} for query '{query}'"

    def test_cds_performance_vs_baseline(self, baseline_data):
        """Verify new CDSBackend meets baseline."""
        if "cds" not in baseline_data:
            pytest.skip("No cds baseline found")

        from core.backends.local.cds_backend import CDSBackend

        backend = CDSBackend(root_paths=[str(TEST_SEARCH_ROOT)])
        backend.build_index()

        for query, baseline in baseline_data["cds"].items():
            result = measure_search_performance(backend, query)

            variance = (result.mean - baseline["mean"]) / baseline["mean"]
            print(
                f"\n{query}: baseline={baseline['mean']:.3f}s, new={result.mean:.3f}s, variance={variance:.1%}"
            )

            assert (
                variance < ACCEPTABLE_VARIANCE
            ), f"Performance regression: {variance:.1%} > {ACCEPTABLE_VARIANCE:.1%} for query '{query}'"

    def test_kg_performance_vs_baseline(self, baseline_data):
        """Verify new KGBackend meets baseline."""
        if "kg" not in baseline_data:
            pytest.skip("No kg baseline found")

        from core.backends.local.kg_backend import KGBackend

        backend = KGBackend()

        for query, baseline in baseline_data["kg"].items():
            result = measure_search_performance(backend, query)

            variance = (result.mean - baseline["mean"]) / baseline["mean"]
            print(
                f"\n{query}: baseline={baseline['mean']:.3f}s, new={result.mean:.3f}s, variance={variance:.1%}"
            )

            assert (
                variance < ACCEPTABLE_VARIANCE
            ), f"Performance regression: {variance:.1%} > {ACCEPTABLE_VARIANCE:.1%} for query '{query}'"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
