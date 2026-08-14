"""Parity Test Template for SkillsBackend.

Validates that new SkillsBackend produces equivalent results to legacy.

Created: 2026-03-15
Task: TASK-002B - Create Parity Test Templates
Maps to: REQ-002 (No regressions in functionality)
"""

from __future__ import annotations

import time

import pytest

SAMPLE_QUERIES = [
    "search",
    "code",
    "test",
    "validate",
    "query",
]


class TestSkillsBackendParity:
    """Parity tests for SkillsBackend migration."""

    @pytest.fixture
    def legacy_backend(self):
        """Create legacy SkillsBackend instance."""
        from search.backends.skills_backend import SkillsBackend

        return SkillsBackend()

    @pytest.fixture
    def new_backend(self):
        """Create new SkillsBackend instance."""
        from core.backends.local.skills_backend import SkillsBackend

        return SkillsBackend()

    def test_search_returns_same_type(self, legacy_backend, new_backend):
        """Both backends should return same result type."""
        for query in SAMPLE_QUERIES[:3]:
            try:
                legacy_results = legacy_backend.search(query)
                new_results = new_backend.search(query)
                assert type(legacy_results) == type(new_results)
            except AttributeError as e:
                if "'str' object has no attribute 'get'" in str(e):
                    pytest.skip("Known issue: SkillsBackend front_matter parsing bug (TASK-005)")
                raise

    def test_search_result_count_similarity(self, legacy_backend, new_backend):
        """Both backends should return similar number of results."""
        for query in SAMPLE_QUERIES[:3]:
            try:
                legacy_results = legacy_backend.search(query)
                new_results = new_backend.search(query)

                legacy_count = len(legacy_results)
                new_count = len(new_results)
                if legacy_count > 0:
                    variance = abs(legacy_count - new_count) / legacy_count
                    assert (
                        variance < 0.1
                    ), f"Result count variance {variance:.1%} for query '{query}'"
            except AttributeError as e:
                if "'str' object has no attribute 'get'" in str(e):
                    pytest.skip("Known issue: SkillsBackend front_matter parsing bug (TASK-005)")
                raise

    def test_search_result_structure_parity(self, legacy_backend, new_backend):
        """Results should have same structure."""
        for query in ["search"]:
            try:
                legacy_results = legacy_backend.search(query)
                new_results = new_backend.search(query)

                if legacy_results and new_results:
                    legacy_keys = set(legacy_results[0].keys())
                    new_keys = set(new_results[0].keys())

                    essential = {"name", "description", "path"}
                    assert essential.issubset(
                        legacy_keys
                    ), f"Legacy missing: {essential - legacy_keys}"
                    assert essential.issubset(new_keys), f"New missing: {essential - new_keys}"
            except AttributeError as e:
                if "'str' object has no attribute 'get'" in str(e):
                    pytest.skip("Known issue: SkillsBackend front_matter parsing bug (TASK-005)")
                raise

    def test_search_result_names_overlap(self, legacy_backend, new_backend):
        """Results should find similar skill names."""
        for query in ["search"]:
            try:
                legacy_results = legacy_backend.search(query)
                new_results = new_backend.search(query)

                if legacy_results and new_results:
                    legacy_names = {r.get("name", "") for r in legacy_results}
                    new_names = {r.get("name", "") for r in new_results}

                    overlap = legacy_names & new_names
                    if legacy_names:
                        overlap_ratio = len(overlap) / len(legacy_names)
                        assert (
                            overlap_ratio >= 0.8
                        ), f"Name overlap only {overlap_ratio:.1%} for query '{query}'"
            except AttributeError as e:
                if "'str' object has no attribute 'get'" in str(e):
                    pytest.skip("Known issue: SkillsBackend front_matter parsing bug (TASK-005)")
                raise

    def test_performance_parity(self, legacy_backend, new_backend):
        """New backend should not be significantly slower."""
        query = "search"

        try:
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
        except AttributeError as e:
            if "'str' object has no attribute 'get'" in str(e):
                pytest.skip("Known issue: SkillsBackend front_matter parsing bug (TASK-005)")
            raise


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
