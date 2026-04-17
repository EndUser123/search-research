"""Parity Test Template for GrepBackend.

Validates that new GrepBackend produces equivalent results to legacy.

Created: 2026-03-15
Task: TASK-002B - Create Parity Test Templates
Maps to: REQ-002 (No regressions in functionality)
"""

from __future__ import annotations

import time
from pathlib import Path

import pytest

# Test configuration
TEST_SEARCH_ROOT = Path("P:/__csf/src")
SAMPLE_QUERIES = [
    "search",
    "index",
    "query",
    "result",
    "build",
    "init",
    "config",
    "process",
    "handle",
    "validate",
]


class TestGrepBackendParity:
    """Parity tests for GrepBackend migration."""

    @pytest.fixture
    def legacy_backend(self):
        """Create legacy GrepBackend instance."""
        from search.backends.grep_backend import GrepBackend

        backend = GrepBackend(root_paths=[str(TEST_SEARCH_ROOT)])
        backend.build_index()
        return backend

    @pytest.fixture
    def new_backend(self):
        """Create new GrepBackend instance."""
        from core.backends.local.grep_backend import GrepBackend

        backend = GrepBackend(root_paths=[str(TEST_SEARCH_ROOT)])
        backend.build_index()
        return backend

    def test_search_returns_same_type(self, legacy_backend, new_backend):
        """Both backends should return same result type."""
        for query in SAMPLE_QUERIES[:3]:
            legacy_results = legacy_backend.search(query)
            new_results = new_backend.search(query)
            assert type(legacy_results) == type(
                new_results
            ), f"Result type mismatch for query '{query}'"

    def test_search_result_count_similarity(self, legacy_backend, new_backend):
        """Both backends should return similar number of results."""
        for query in SAMPLE_QUERIES[:3]:
            legacy_results = legacy_backend.search(query)
            new_results = new_backend.search(query)

            # Allow 10% variance in result count
            legacy_count = len(legacy_results)
            new_count = len(new_results)
            if legacy_count > 0:
                variance = abs(legacy_count - new_count) / legacy_count
                assert variance < 0.1, f"Result count variance {variance:.1%} for query '{query}'"

    def test_search_result_structure_parity(self, legacy_backend, new_backend):
        """Results should have same structure."""
        for query in ["search"]:
            legacy_results = legacy_backend.search(query)
            new_results = new_backend.search(query)

            if legacy_results and new_results:
                legacy_keys = set(legacy_results[0].keys())
                new_keys = set(new_results[0].keys())

                # Essential keys must match
                essential = {"name", "file", "line"}
                assert essential.issubset(
                    legacy_keys
                ), f"Legacy missing essential keys: {essential - legacy_keys}"
                assert essential.issubset(
                    new_keys
                ), f"New missing essential keys: {essential - new_keys}"

    def test_search_result_names_overlap(self, legacy_backend, new_backend):
        """Results should find similar function/class names."""
        for query in ["search"]:
            legacy_results = legacy_backend.search(query)
            new_results = new_backend.search(query)

            if legacy_results and new_results:
                legacy_names = {r.get("name", "") for r in legacy_results}
                new_names = {r.get("name", "") for r in new_results}

                # At least 80% overlap in names found
                overlap = legacy_names & new_names
                if legacy_names:
                    overlap_ratio = len(overlap) / len(legacy_names)
                    assert (
                        overlap_ratio >= 0.8
                    ), f"Name overlap only {overlap_ratio:.1%} for query '{query}'"

    def test_performance_parity(self, legacy_backend, new_backend):
        """New backend should not be significantly slower."""
        query = "search"

        # Warm up
        legacy_backend.search(query)
        new_backend.search(query)

        # Measure legacy
        start = time.perf_counter()
        for _ in range(10):
            legacy_backend.search(query)
        legacy_time = time.perf_counter() - start

        # Measure new
        start = time.perf_counter()
        for _ in range(10):
            new_backend.search(query)
        new_time = time.perf_counter() - start

        # New backend should not be > 10% slower
        if legacy_time > 0:
            slowdown = (new_time - legacy_time) / legacy_time
            assert (
                slowdown < 0.1
            ), f"New backend {slowdown:.1%} slower (legacy: {legacy_time:.3f}s, new: {new_time:.3f}s)"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
