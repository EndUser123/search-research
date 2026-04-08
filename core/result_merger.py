"""Result merger with Reciprocal Rank Fusion (RRF) algorithm.

This module implements type-safe RRF fusion with performance optimization through
result capping per source. RRF is a rank aggregation method that combines ranked
lists from multiple sources by computing a fusion score based on rank position.

RRF Algorithm:
    For each result at position i in a source list:
        rrf_score += k / (k + i)

    Where k is a constant (default 60) that controls the contribution of ranks.

Performance Optimization:
    Results are capped per source (default 20) to prevent O(n*m) complexity
    when merging large result sets. This ensures linear time complexity.

Type Safety:
    All results are validated against the NormalizedResult protocol at runtime
    to ensure type safety and consistent structure across backends.

Example:
    >>> from core.result_merger import reciprocal_rank_fusion
    >>> results_list = [
    ...     [result1, result2, result3],  # Source A
    ...     [result4, result5, result6],  # Source B
    ... ]
    >>> fused = reciprocal_rank_fusion(results_list, k=60, max_per_source=20)
    >>> for result in fused:
    ...     print(f"{result.id}: {result.rrf_score:.3f} from {result.sources}")
"""

from dataclasses import dataclass, field
from typing import Any

from .result_normalizer import NormalizedResult, normalize_result

# Default RRF constant (k) - controls contribution of ranks
_DEFAULT_RRF_K: int = 60
# Default maximum results to process per source
_DEFAULT_MAX_PER_SOURCE: int = 20


@dataclass
class _AccumulatedScore:
    """Internal accumulator for RRF scores during fusion.

    Attributes:
        score: Accumulated RRF score from all sources
        sources: Set of source names that contributed to this result
    """
    score: float
    sources: set[str]


@dataclass
class FusedResult:
    """Fused result from RRF merge.

    Attributes:
        id: Unique identifier for the result
        rrf_score: Combined RRF score from all sources
        sources: List of source names that contributed this result
    """

    id: str
    rrf_score: float
    sources: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert fused result to dictionary representation.

        Returns:
            Dictionary containing id, rrf_score, and sources fields
        """
        return {
            "id": self.id,
            "rrf_score": self.rrf_score,
            "sources": self.sources,
        }


def _calculate_rrf_contribution(position: int, k: int) -> float:
    """Calculate RRF score contribution for a given position.

    The RRF formula assigns higher scores to results at lower positions
    (earlier in the ranked list).

    Args:
        position: Zero-based rank position in the source list
        k: RRF constant controlling score decay rate

    Returns:
        RRF score contribution in range (0, 1]
    """
    return k / (k + position)


def _extract_result_id_and_source(
    normalized: NormalizedResult,
) -> tuple[str, str]:
    """Extract result ID and source name from a normalized result.

    Handles both dict-like and object-based NormalizedResult implementations.

    Args:
        normalized: A NormalizedResult-compliant result (dict or object)

    Returns:
        Tuple of (result_id, source_name)
    """
    if isinstance(normalized, dict):
        result_id = normalized["id"]
        source = normalized["source"]
    else:
        result_id = normalized.id
        source = normalized.source
    return result_id, source


def _validate_fusion_inputs(
    results_list: list[list[NormalizedResult]] | None,
    k: int,
    max_per_source: int,
) -> None:
    """Validate inputs for reciprocal_rank_fusion.

    Args:
        results_list: List of result lists from different sources
        k: RRF constant
        max_per_source: Cap results per source

    Raises:
        TypeError: If results_list is None or not a list
        ValueError: If k or max_per_source are negative
    """
    if results_list is None:
        raise TypeError("results_list cannot be None")

    if not isinstance(results_list, list):
        raise TypeError(
            f"results_list must be a list, got {type(results_list).__name__}"
        )

    if k < 0:
        raise ValueError(f"k must be non-negative, got {k}")

    if max_per_source < 0:
        raise ValueError(f"max_per_source must be non-negative, got {max_per_source}")


def reciprocal_rank_fusion(
    results_list: list[list[NormalizedResult]],
    k: int = _DEFAULT_RRF_K,
    max_per_source: int = _DEFAULT_MAX_PER_SOURCE,
) -> list[FusedResult]:
    """Type-safe RRF fusion with result capping.

    Combines ranked result lists from multiple sources using Reciprocal Rank Fusion.
    Results are capped per source to ensure linear time complexity and prevent
    performance issues with large result sets.

    Args:
        results_list: List of result lists from different sources
        k: RRF constant (default 60). Higher values give more weight to lower ranks.
        max_per_source: Cap results per source (default 20). Set to 0 for unlimited.

    Returns:
        Sorted list of FusedResult by RRF score descending

    Raises:
        TypeError: If results_list is None or contains invalid results
        ValueError: If k or max_per_source are negative

    Example:
        >>> results_list = [
        ...     [result_a1, result_a2],  # Source A
        ...     [result_b1, result_b2],  # Source B
        ... ]
        >>> fused = reciprocal_rank_fusion(results_list)
        >>> len(fused)  # Number of unique results across sources
        4
    """
    _validate_fusion_inputs(results_list, k, max_per_source)

    # Handle empty input or zero cap
    if not results_list or max_per_source == 0:
        return []

    # Accumulate RRF scores by result ID
    fused_map: dict[str, _AccumulatedScore] = {}

    for source_results in results_list:
        # Skip empty sources
        if not source_results:
            continue

        # Cap results per source for performance
        capped_results = source_results[:max_per_source]

        # Process each result in this source
        for position, result in enumerate(capped_results):
            normalized = normalize_result(result)
            result_id, source = _extract_result_id_and_source(normalized)
            rrf_contribution = _calculate_rrf_contribution(position, k)

            # Initialize or update accumulated score
            if result_id not in fused_map:
                fused_map[result_id] = _AccumulatedScore(score=0.0, sources=set())

            fused_map[result_id].score += rrf_contribution
            fused_map[result_id].sources.add(source)

    # Convert to FusedResult objects
    fused_results = [
        FusedResult(
            id=result_id,
            rrf_score=accumulated.score,
            sources=sorted(accumulated.sources),  # Sort for consistent ordering
        )
        for result_id, accumulated in fused_map.items()
    ]

    # Sort by RRF score descending
    fused_results.sort(key=lambda r: r.rrf_score, reverse=True)

    return fused_results
