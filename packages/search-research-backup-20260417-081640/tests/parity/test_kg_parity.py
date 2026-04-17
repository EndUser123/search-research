"""Parity Test Template for KGBackend.

Validates that new KGBackend produces equivalent results to legacy.

Created: 2026-03-15
Task: TASK-002B - Create Parity Test Templates
Maps to: REQ-002 (No regressions in functionality)
"""

from __future__ import annotations

import time

import pytest

SAMPLE_QUERIES = [
    "nip",
    "search",
    "cwo",
    "validation",
]


class TestKGBackendParity:
    """Parity tests for KGBackend migration."""

    @pytest.fixture
    def legacy_backend(self):
        """Create legacy KGBackend instance."""
        from search.backends.kg_backend import KGBackend

        return KGBackend()

    @pytest.fixture
    def new_backend(self):
        """Create new KGBackend instance."""
        from core.backends.local.kg_backend import KGBackend

        return KGBackend()

    def test_search_returns_same_type(self, legacy_backend, new_backend):
        """Both backends should return same result type."""
        for query in SAMPLE_QUERIES[:3]:
            legacy_results = legacy_backend.search(query)
            new_results = new_backend.search(query)
            assert type(legacy_results) == type(new_results)

    def test_search_result_count_similarity(self, legacy_backend, new_backend):
        """Both backends should return similar number of results."""
        for query in SAMPLE_QUERIES[:3]:
            legacy_results = legacy_backend.search(query)
            new_results = new_backend.search(query)

            legacy_count = len(legacy_results)
            new_count = len(new_results)
            if legacy_count > 0:
                variance = abs(legacy_count - new_count) / legacy_count
                assert variance < 0.1, f"Result count variance {variance:.1%} for query '{query}'"

    def test_search_result_structure_parity(self, legacy_backend, new_backend):
        """Results should have same structure."""
        for query in ["nip"]:
            legacy_results = legacy_backend.search(query)
            new_results = new_backend.search(query)

            if legacy_results and new_results:
                legacy_keys = set(legacy_results[0].keys())
                new_keys = set(new_results[0].keys())

                essential = {"entity", "conversations"}
                assert essential.issubset(legacy_keys), f"Legacy missing: {essential - legacy_keys}"
                assert essential.issubset(new_keys), f"New missing: {essential - new_keys}"

    def test_search_result_entities_overlap(self, legacy_backend, new_backend):
        """Results should find similar entities."""
        for query in ["nip"]:
            legacy_results = legacy_backend.search(query)
            new_results = new_backend.search(query)

            if legacy_results and new_results:
                legacy_entities = {r.get("entity", "") for r in legacy_results}
                new_entities = {r.get("entity", "") for r in new_results}

                overlap = legacy_entities & new_entities
                if legacy_entities:
                    overlap_ratio = len(overlap) / len(legacy_entities)
                    assert (
                        overlap_ratio >= 0.8
                    ), f"Entity overlap only {overlap_ratio:.1%} for query '{query}'"

    def test_performance_parity(self, legacy_backend, new_backend):
        """New backend should not be significantly slower."""
        query = "nip"

        # Warm up
        legacy_backend.search(query)
        new_backend.search(query)

        # Measure
        start = time.perf_counter()
        for _ in range(10):
            legacy_backend.search(query)
        legacy_time = time.perf_counter() - start

        start = time.perf_counter()
        for _ in range(10):
            new_backend.search(query)
        new_time = time.perf_counter() - start

        if legacy_time > 0:
            slowdown = (new_time - legacy_time) / legacy_time
            assert slowdown < 0.1, f"New backend {slowdown:.1%} slower"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
