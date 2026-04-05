"""Tests for result merger with RRF fusion and result capping.

These tests verify the reciprocal_rank_fusion() function and FusedResult dataclass
provide type-safe result merging with performance optimization through max_per_source capping.

Test Requirements:
1. FusedResult dataclass exists with required fields (id, rrf_score, sources, to_dict())
2. reciprocal_rank_fusion() function exists
3. Empty results_list returns empty list
4. Single source returns results in original order
5. Multiple sources merged correctly
6. RRF scoring formula: score = k / (k + position)
7. Results capped per source (max 20 default)
8. Duplicate IDs from different sources have scores summed
9. Results sorted by RRF score descending
10. Handles None/empty results gracefully
11. Returns FusedResult objects with correct metadata
12. Type-safe with NormalizedResult protocol
"""

from typing import Any

import pytest

from core.models import SearchResult


class MockNormalizedResult:
    """Mock NormalizedResult for testing."""

    def __init__(
        self,
        id: str,
        score: float,
        source: str,
        title: str = "Test Title",
        url: str = "https://example.com",
    ):
        self.id = id
        self.score = score
        self.source = source
        self.title = title
        self.url = url

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary representation."""
        return {
            "id": self.id,
            "score": self.score,
            "source": self.source,
            "title": self.title,
            "url": self.url,
        }


class TestFusedResultDataclass:
    """Tests for FusedResult dataclass definition."""

    def test_fused_result_exists(self):
        """Test that FusedResult dataclass is defined."""
        from core.result_merger import FusedResult

        # Verify it's a dataclass
        assert hasattr(FusedResult, "__dataclass_fields__")

    def test_fused_result_has_id_field(self):
        """Test that FusedResult has 'id' field."""
        from core.result_merger import FusedResult

        assert "id" in FusedResult.__dataclass_fields__

    def test_fused_result_has_rrf_score_field(self):
        """Test that FusedResult has 'rrf_score' field."""
        from core.result_merger import FusedResult

        assert "rrf_score" in FusedResult.__dataclass_fields__

    def test_fused_result_has_sources_field(self):
        """Test that FusedResult has 'sources' field."""
        from core.result_merger import FusedResult

        assert "sources" in FusedResult.__dataclass_fields__

    def test_fused_result_has_to_dict_method(self):
        """Test that FusedResult has to_dict() method."""
        from core.result_merger import FusedResult

        # Create instance to test method
        result = FusedResult(
            id="test-id",
            rrf_score=0.8,
            sources=["source1", "source2"],
        )
        assert hasattr(result, "to_dict")
        assert callable(result.to_dict)

    def test_fused_result_to_dict_returns_dict(self):
        """Test that FusedResult.to_dict() returns a dictionary."""
        from core.result_merger import FusedResult

        result = FusedResult(
            id="test-id",
            rrf_score=0.8,
            sources=["source1", "source2"],
        )

        result_dict = result.to_dict()
        assert isinstance(result_dict, dict)

    def test_fused_result_to_dict_contains_required_fields(self):
        """Test that FusedResult.to_dict() contains required fields."""
        from core.result_merger import FusedResult

        result = FusedResult(
            id="test-id",
            rrf_score=0.8,
            sources=["source1", "source2"],
        )

        result_dict = result.to_dict()

        # Must contain all required fields
        assert "id" in result_dict
        assert "rrf_score" in result_dict
        assert "sources" in result_dict


class TestReciprocalRankFusionFunction:
    """Tests for reciprocal_rank_fusion() function."""

    def test_function_exists(self):
        """Test that reciprocal_rank_fusion() function is defined."""
        from core.result_merger import reciprocal_rank_fusion

        assert callable(reciprocal_rank_fusion)

    def test_function_accepts_results_list(self):
        """Test that reciprocal_rank_fusion() accepts results_list parameter."""
        from core.result_merger import reciprocal_rank_fusion

        results_list = [
            [MockNormalizedResult(id="1", score=0.8, source="source1")]
        ]

        # Should not raise
        result = reciprocal_rank_fusion(results_list)
        assert result is not None

    def test_function_accepts_k_parameter(self):
        """Test that reciprocal_rank_fusion() accepts k parameter."""
        from core.result_merger import reciprocal_rank_fusion

        results_list = [
            [MockNormalizedResult(id="1", score=0.8, source="source1")]
        ]

        # Should not raise
        result = reciprocal_rank_fusion(results_list, k=60)
        assert result is not None

    def test_function_accepts_max_per_source_parameter(self):
        """Test that reciprocal_rank_fusion() accepts max_per_source parameter."""
        from core.result_merger import reciprocal_rank_fusion

        results_list = [
            [MockNormalizedResult(id="1", score=0.8, source="source1")]
        ]

        # Should not raise
        result = reciprocal_rank_fusion(results_list, max_per_source=20)
        assert result is not None


class TestEmptyInputs:
    """Tests for empty and None input handling."""

    def test_empty_results_list_returns_empty_list(self):
        """Test that empty results_list returns empty list."""
        from core.result_merger import reciprocal_rank_fusion

        result = reciprocal_rank_fusion([])

        assert result == []

    def test_none_results_list_raises_error(self):
        """Test that None results_list raises TypeError."""
        from core.result_merger import reciprocal_rank_fusion

        with pytest.raises(TypeError):
            reciprocal_rank_fusion(None)

    def test_empty_source_lists_returns_empty_list(self):
        """Test that results_list with only empty sources returns empty list."""
        from core.result_merger import reciprocal_rank_fusion

        result = reciprocal_rank_fusion([[], [], []])

        assert result == []

    def test_handles_mixed_empty_and_nonempty_sources(self):
        """Test that mixed empty and non-empty sources are handled correctly."""
        from core.result_merger import reciprocal_rank_fusion

        results_list = [
            [],  # Empty source
            [MockNormalizedResult(id="1", score=0.8, source="source2")],
            [],  # Empty source
        ]

        result = reciprocal_rank_fusion(results_list)

        assert len(result) == 1
        assert result[0].id == "1"


class TestSingleSourceResults:
    """Tests for single source result merging."""

    def test_single_source_returns_results_in_order(self):
        """Test that single source returns results in original order."""
        from core.result_merger import reciprocal_rank_fusion

        results_list = [
            [
                MockNormalizedResult(id="1", score=0.9, source="source1"),
                MockNormalizedResult(id="2", score=0.8, source="source1"),
                MockNormalizedResult(id="3", score=0.7, source="source1"),
            ]
        ]

        result = reciprocal_rank_fusion(results_list, k=60)

        assert len(result) == 3
        assert result[0].id == "1"
        assert result[1].id == "2"
        assert result[2].id == "3"

    def test_single_source_rrf_scoring(self):
        """Test that RRF scoring formula is applied correctly for single source."""
        from core.result_merger import reciprocal_rank_fusion

        k = 60
        results_list = [
            [
                MockNormalizedResult(id="1", score=0.9, source="source1"),  # position 0
                MockNormalizedResult(id="2", score=0.8, source="source1"),  # position 1
                MockNormalizedResult(id="3", score=0.7, source="source1"),  # position 2
            ]
        ]

        result = reciprocal_rank_fusion(results_list, k=k)

        # RRF formula: score = k / (k + position)
        # position 0: 60 / (60 + 0) = 1.0
        # position 1: 60 / (60 + 1) ≈ 0.9836
        # position 2: 60 / (60 + 2) ≈ 0.9677
        assert result[0].rrf_score == pytest.approx(1.0)
        assert result[1].rrf_score == pytest.approx(60 / 61)
        assert result[2].rrf_score == pytest.approx(60 / 62)

    def test_single_source_metadata_preserved(self):
        """Test that source metadata is preserved in FusedResult."""
        from core.result_merger import reciprocal_rank_fusion

        results_list = [
            [
                MockNormalizedResult(id="1", score=0.9, source="source1"),
            ]
        ]

        result = reciprocal_rank_fusion(results_list)

        assert len(result) == 1
        assert result[0].id == "1"
        assert "source1" in result[0].sources


class TestMultipleSourceResults:
    """Tests for multiple source result merging."""

    def test_multiple_sources_merged_correctly(self):
        """Test that multiple sources are merged correctly."""
        from core.result_merger import reciprocal_rank_fusion

        results_list = [
            [  # Source 1
                MockNormalizedResult(id="1", score=0.9, source="source1"),
                MockNormalizedResult(id="2", score=0.8, source="source1"),
            ],
            [  # Source 2
                MockNormalizedResult(id="3", score=0.9, source="source2"),
                MockNormalizedResult(id="4", score=0.8, source="source2"),
            ],
        ]

        result = reciprocal_rank_fusion(results_list, k=60)

        # Should have 4 unique results
        assert len(result) == 4

        # All results should be FusedResult instances
        from core.result_merger import FusedResult
        assert all(isinstance(r, FusedResult) for r in result)

    def test_duplicate_ids_from_different_sources_summed(self):
        """Test that duplicate IDs from different sources have scores summed."""
        from core.result_merger import reciprocal_rank_fusion

        k = 60
        results_list = [
            [  # Source 1
                MockNormalizedResult(id="1", score=0.9, source="source1"),  # position 0
                MockNormalizedResult(id="2", score=0.8, source="source1"),  # position 1
            ],
            [  # Source 2
                MockNormalizedResult(id="1", score=0.9, source="source2"),  # position 0
                MockNormalizedResult(id="3", score=0.8, source="source2"),  # position 1
            ],
        ]

        result = reciprocal_rank_fusion(results_list, k=k)

        # Find the duplicate result
        duplicate = next(r for r in result if r.id == "1")

        # RRF scores should be summed: 1.0 + 1.0 = 2.0
        assert duplicate.rrf_score == pytest.approx(2.0)
        assert len(duplicate.sources) == 2
        assert "source1" in duplicate.sources
        assert "source2" in duplicate.sources

    def test_results_sorted_by_rrf_score_descending(self):
        """Test that results are sorted by RRF score in descending order."""
        from core.result_merger import reciprocal_rank_fusion

        results_list = [
            [  # Source 1
                MockNormalizedResult(id="low", score=0.5, source="source1"),
                MockNormalizedResult(id="high", score=0.9, source="source1"),
            ],
            [  # Source 2
                MockNormalizedResult(id="mid", score=0.7, source="source2"),
                MockNormalizedResult(id="high", score=0.9, source="source2"),  # Duplicate
            ],
        ]

        result = reciprocal_rank_fusion(results_list, k=60)

        # "high" appears in both sources (positions 1 and 1)
        # RRF: (60/61) + (60/61) ≈ 1.967
        # "low" appears in source1 position 0: RRF: 1.0
        # "mid" appears in source2 position 0: RRF: 1.0

        # "high" should be first (highest summed score)
        assert result[0].id == "high"

        # Remaining should be sorted by score
        scores = [r.rrf_score for r in result]
        assert scores == sorted(scores, reverse=True)

    def test_sources_list_tracks_all_contributors(self):
        """Test that sources list tracks all contributing sources."""
        from core.result_merger import reciprocal_rank_fusion

        results_list = [
            [  # Source 1
                MockNormalizedResult(id="1", score=0.9, source="source1"),
                MockNormalizedResult(id="2", score=0.8, source="source1"),
            ],
            [  # Source 2
                MockNormalizedResult(id="2", score=0.9, source="source2"),  # Duplicate
                MockNormalizedResult(id="3", score=0.8, source="source2"),
            ],
            [  # Source 3
                MockNormalizedResult(id="2", score=0.9, source="source3"),  # Duplicate
            ],
        ]

        result = reciprocal_rank_fusion(results_list)

        # Find result that appears in all 3 sources
        duplicate = next(r for r in result if r.id == "2")

        assert len(duplicate.sources) == 3
        assert "source1" in duplicate.sources
        assert "source2" in duplicate.sources
        assert "source3" in duplicate.sources


class TestResultCapping:
    """Tests for max_per_source performance optimization."""

    def test_results_capped_per_source_default(self):
        """Test that results are capped at 20 per source by default."""
        from core.result_merger import reciprocal_rank_fusion

        # Create source with 25 results
        results_list = [
            [
                MockNormalizedResult(
                    id=f"result-{i}",
                    score=0.9 - (i * 0.01),
                    source="source1"
                )
                for i in range(25)
            ]
        ]

        result = reciprocal_rank_fusion(results_list)

        # Should only return top 20
        assert len(result) == 20

        # Should be first 20 results
        assert result[0].id == "result-0"
        assert result[19].id == "result-19"

    def test_results_capped_per_source_custom_limit(self):
        """Test that results respect custom max_per_source limit."""
        from core.result_merger import reciprocal_rank_fusion

        # Create source with 15 results, cap at 5
        results_list = [
            [
                MockNormalizedResult(
                    id=f"result-{i}",
                    score=0.9 - (i * 0.01),
                    source="source1"
                )
                for i in range(15)
            ]
        ]

        result = reciprocal_rank_fusion(results_list, max_per_source=5)

        # Should only return top 5
        assert len(result) == 5

        # Should be first 5 results
        assert result[0].id == "result-0"
        assert result[4].id == "result-4"

    def test_capping_applied_per_source_independently(self):
        """Test that capping is applied per source, not globally."""
        from core.result_merger import reciprocal_rank_fusion

        # Create 3 sources with 25 results each
        results_list = []
        for source_idx in range(3):
            source_name = f"source{source_idx + 1}"
            results = [
                MockNormalizedResult(
                    id=f"{source_name}-result-{i}",
                    score=0.9 - (i * 0.01),
                    source=source_name
                )
                for i in range(25)
            ]
            results_list.append(results)

        result = reciprocal_rank_fusion(results_list, max_per_source=10)

        # Should have 30 results (10 from each of 3 sources)
        assert len(result) == 30

        # Each source should have exactly 10 results
        source_counts = {}
        for r in result:
            for source in r.sources:
                source_counts[source] = source_counts.get(source, 0) + 1

        # Each source should appear exactly 10 times
        assert source_counts["source1"] == 10
        assert source_counts["source2"] == 10
        assert source_counts["source3"] == 10

    def test_no_capping_when_source_below_limit(self):
        """Test that no capping occurs when source is below limit."""
        from core.result_merger import reciprocal_rank_fusion

        # Create source with 5 results, cap at 20
        results_list = [
            [
                MockNormalizedResult(
                    id=f"result-{i}",
                    score=0.9 - (i * 0.01),
                    source="source1"
                )
                for i in range(5)
            ]
        ]

        result = reciprocal_rank_fusion(results_list, max_per_source=20)

        # Should return all 5 results
        assert len(result) == 5


class TestRRFScoringFormula:
    """Tests for RRF scoring formula implementation."""

    def test_rrf_formula_with_k_60(self):
        """Test RRF formula with k=60 (default)."""
        from core.result_merger import reciprocal_rank_fusion

        k = 60
        results_list = [
            [
                MockNormalizedResult(id="1", score=0.9, source="source1"),  # position 0
                MockNormalizedResult(id="2", score=0.8, source="source1"),  # position 1
                MockNormalizedResult(id="3", score=0.7, source="source1"),  # position 2
            ]
        ]

        result = reciprocal_rank_fusion(results_list, k=k)

        # position 0: 60 / (60 + 0) = 1.0
        assert result[0].rrf_score == pytest.approx(1.0)

        # position 1: 60 / (60 + 1) ≈ 0.9836
        assert result[1].rrf_score == pytest.approx(60 / 61)

        # position 2: 60 / (60 + 2) ≈ 0.9677
        assert result[2].rrf_score == pytest.approx(60 / 62)

    def test_rrf_formula_with_custom_k(self):
        """Test RRF formula with custom k value."""
        from core.result_merger import reciprocal_rank_fusion

        k = 100
        results_list = [
            [
                MockNormalizedResult(id="1", score=0.9, source="source1"),  # position 0
                MockNormalizedResult(id="2", score=0.8, source="source1"),  # position 1
            ]
        ]

        result = reciprocal_rank_fusion(results_list, k=k)

        # position 0: 100 / (100 + 0) = 1.0
        assert result[0].rrf_score == pytest.approx(1.0)

        # position 1: 100 / (100 + 1) ≈ 0.9901
        assert result[1].rrf_score == pytest.approx(100 / 101)

    def test_rrf_scores_summed_for_duplicates(self):
        """Test that RRF scores are summed for duplicate IDs."""
        from core.result_merger import reciprocal_rank_fusion

        k = 60
        results_list = [
            [  # Source 1: "dup" at position 0
                MockNormalizedResult(id="dup", score=0.9, source="source1"),
            ],
            [  # Source 2: "dup" at position 1
                MockNormalizedResult(id="other", score=0.9, source="source2"),
                MockNormalizedResult(id="dup", score=0.8, source="source2"),
            ],
            [  # Source 3: "dup" at position 0
                MockNormalizedResult(id="dup", score=0.9, source="source3"),
            ],
        ]

        result = reciprocal_rank_fusion(results_list, k=k)

        duplicate = next(r for r in result if r.id == "dup")

        # position 0 from source1: 60/60 = 1.0
        # position 1 from source2: 60/61 ≈ 0.9836
        # position 0 from source3: 60/60 = 1.0
        # Total: 1.0 + 0.9836 + 1.0 ≈ 2.9836
        expected_score = 1.0 + (60 / 61) + 1.0
        assert duplicate.rrf_score == pytest.approx(expected_score)


class TestTypeSafety:
    """Tests for type safety with NormalizedResult protocol."""

    def test_accepts_search_result_objects(self):
        """Test that SearchResult objects are accepted."""
        from core.result_merger import reciprocal_rank_fusion

        results_list = [
            [
                SearchResult(
                    url="https://example.com/1",
                    title="Result 1",
                    content="Content 1",
                    source="source1",
                    score=0.9
                ),
                SearchResult(
                    url="https://example.com/2",
                    title="Result 2",
                    content="Content 2",
                    source="source1",
                    score=0.8
                ),
            ]
        ]

        result = reciprocal_rank_fusion(results_list)

        assert len(result) == 2
        assert result[0].id == "https://example.com/1"
        assert result[1].id == "https://example.com/2"

    def test_accepts_dict_results(self):
        """Test that dict results satisfying protocol are accepted."""
        from core.result_merger import reciprocal_rank_fusion

        results_list = [
            [
                {
                    "id": "result-1",
                    "score": 0.9,
                    "source": "source1",
                    "to_dict": lambda: {"id": "result-1", "score": 0.9, "source": "source1"}
                },
                {
                    "id": "result-2",
                    "score": 0.8,
                    "source": "source1",
                    "to_dict": lambda: {"id": "result-2", "score": 0.8, "source": "source1"}
                },
            ]
        ]

        result = reciprocal_rank_fusion(results_list)

        assert len(result) == 2
        assert result[0].id == "result-1"
        assert result[1].id == "result-2"

    def test_rejects_invalid_results(self):
        """Test that invalid results are rejected."""
        from core.result_merger import reciprocal_rank_fusion

        # Invalid: missing required fields
        results_list = [
            [
                {"id": "invalid"}  # Missing score, source, to_dict
            ]
        ]

        with pytest.raises(TypeError):
            reciprocal_rank_fusion(results_list)


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_very_large_k_value(self):
        """Test behavior with very large k value."""
        from core.result_merger import reciprocal_rank_fusion

        results_list = [
            [
                MockNormalizedResult(id="1", score=0.9, source="source1"),
            ]
        ]

        result = reciprocal_rank_fusion(results_list, k=10000)

        # With very large k, all scores should be very close to 1.0
        assert result[0].rrf_score > 0.99

    def test_very_small_k_value(self):
        """Test behavior with very small k value."""
        from core.result_merger import reciprocal_rank_fusion

        results_list = [
            [
                MockNormalizedResult(id="1", score=0.9, source="source1"),
                MockNormalizedResult(id="2", score=0.8, source="source1"),
            ]
        ]

        result = reciprocal_rank_fusion(results_list, k=1)

        # With k=1, scores should drop quickly
        # position 0: 1/1 = 1.0
        # position 1: 1/2 = 0.5
        assert result[0].rrf_score == pytest.approx(1.0)
        assert result[1].rrf_score == pytest.approx(0.5)

    def test_zero_max_per_source(self):
        """Test that max_per_source=0 returns no results."""
        from core.result_merger import reciprocal_rank_fusion

        results_list = [
            [
                MockNormalizedResult(id="1", score=0.9, source="source1"),
            ]
        ]

        result = reciprocal_rank_fusion(results_list, max_per_source=0)

        assert len(result) == 0

    def test_single_result_per_source(self):
        """Test with exactly one result per source."""
        from core.result_merger import reciprocal_rank_fusion

        results_list = [
            [MockNormalizedResult(id="1", score=0.9, source="source1")],
            [MockNormalizedResult(id="2", score=0.8, source="source2")],
            [MockNormalizedResult(id="3", score=0.7, source="source3")],
        ]

        result = reciprocal_rank_fusion(results_list)

        assert len(result) == 3
        # All should have RRF score of 1.0 (position 0)
        assert all(r.rrf_score == pytest.approx(1.0) for r in result)

    def test_all_duplicates_across_sources(self):
        """Test when all sources return the same result ID."""
        from core.result_merger import reciprocal_rank_fusion

        results_list = [
            [MockNormalizedResult(id="same", score=0.9, source="source1")],
            [MockNormalizedResult(id="same", score=0.8, source="source2")],
            [MockNormalizedResult(id="same", score=0.7, source="source3")],
        ]

        result = reciprocal_rank_fusion(results_list, k=60)

        # Should have 1 result with summed scores
        assert len(result) == 1
        assert result[0].id == "same"
        assert result[0].rrf_score == pytest.approx(3.0)  # 1.0 + 1.0 + 1.0
        assert len(result[0].sources) == 3
