"""Ensemble fusion methods for combining search results."""

from dataclasses import dataclass, field
from typing import Any
from collections import defaultdict


@dataclass
class HybridEnsembleConfig:
    """Configuration for hybrid ensemble methods.

    Attributes:
        enable_query_expansion: Whether to use query expansion.
        enable_single_hyde: Whether to use single HyDE.
        enable_multi_hyde: Whether to use multi-HyDE.
        hyde_perspectives: List of perspectives for multi-HyDE.
        ensemble_method: The fusion method to use.
        max_results: Maximum number of results to return.
        rrf_k: The k parameter for RRF (higher = more rank tolerance).
    """

    enable_query_expansion: bool = True
    enable_single_hyde: bool = True
    enable_multi_hyde: bool = True
    hyde_perspectives: list[str] | None = None
    ensemble_method: str = "reciprocal_rank_fusion"
    max_results: int = 20
    rrf_k: int = 60

    def __post_init__(self):
        if self.hyde_perspectives is None:
            self.hyde_perspectives = ["technical", "beginner", "comprehensive"]


@dataclass
class EnsembleResult:
    """Result from ensemble fusion.

    Attributes:
        combined_results: The fused search results.
        sources_used: Dictionary of source counts.
        ensemble_method: The fusion method used.
        query_variants: List of query variants used.
        hypothetical_document: The hypothetical document generated.
        multi_hypothetical_documents: Multi-perspective hypothetical docs.
        metadata: Additional metadata.
    """

    combined_results: list
    sources_used: dict
    ensemble_method: str = "reciprocal_rank_fusion"
    query_variants: list = field(default_factory=list)
    hypothetical_document: Any = None
    multi_hypothetical_documents: Any = None
    metadata: dict = field(default_factory=dict)


def reciprocal_rank_fusion(
    result_lists: list[list],
    k: int = 60,
    max_results: int | None = None,
) -> list:
    """Combine multiple result lists using Reciprocal Rank Fusion.

    RRF formula: score = sum(1 / (k + rank)) for all result lists

    Args:
        result_lists: List of search result lists to combine.
        k: The RRF k parameter (default 60).
        max_results: Maximum number of results to return.

    Returns:
        Combined and deduplicated results sorted by RRF score.
    """
    if not result_lists:
        return []

    # Filter out empty lists
    result_lists = [rl for rl in result_lists if rl]

    if not result_lists:
        return []

    # Track scores by URL (primary) and title (secondary dedup)
    scores = defaultdict(float)
    seen_items = {}  # Track the best version of each item

    for result_list in result_lists:
        for rank, item in enumerate(result_list):
            # Use URL as primary key for deduplication
            key = item.url
            rrf_score = 1.0 / (k + rank + 1)

            scores[key] += rrf_score

            # Keep the first (highest rank) version of each item
            if key not in seen_items:
                seen_items[key] = item

    # Also check for title duplicates (same title, different URL)
    title_map = defaultdict(list)
    for url, item in seen_items.items():
        title_map[item.title].append((url, scores[url], item))

    # For items with same title, keep only the highest scoring one
    final_items = []
    for title, items in title_map.items():
        if len(items) > 1:
            # Sort by score descending and keep the best
            items.sort(key=lambda x: x[1], reverse=True)
            best_url, _, best_item = items[0]
            final_items.append(best_item)
        else:
            _, _, item = items[0]
            final_items.append(item)

    # Sort by RRF score descending
    final_items.sort(key=lambda x: scores[x.url], reverse=True)

    # Add RRF score to metadata
    for item in final_items:
        item.metadata["rrf_score"] = item.metadata.get("rrf_score", scores[item.url])

    # Apply max_results limit
    if max_results is not None:
        final_items = final_items[:max_results]

    return final_items


def weighted_average_fusion(
    result_lists: list[list],
    weights: dict[str, float] | None = None,
    max_results: int | None = None,
) -> list:
    """Combine results using weighted average of source scores.

    Args:
        result_lists: List of search result lists to combine.
        weights: Optional weights by source name.
        max_results: Maximum number of results to return.

    Returns:
        Combined and deduplicated results sorted by weighted score.
    """
    if not result_lists:
        return []

    # Filter out empty lists
    result_lists = [rl for rl in result_lists if rl]

    if not result_lists:
        return []

    # Track scores by URL
    scores = defaultdict(float)
    weight_sums = defaultdict(float)
    seen_items = {}

    for result_list in result_lists:
        for item in result_list:
            key = item.url
            source = item.source

            # Get weight for this source (default 1.0)
            weight = weights.get(source, 1.0) if weights else 1.0

            # Accumulate weighted score
            scores[key] += item.score * weight
            weight_sums[key] += weight

            # Keep the first version of each item
            if key not in seen_items:
                seen_items[key] = item

    # Normalize by weight sum
    for key in scores:
        if weight_sums[key] > 0:
            scores[key] /= weight_sums[key]

    # Also check for title duplicates
    title_map = defaultdict(list)
    for url, item in seen_items.items():
        title_map[item.title].append((url, scores[url], item))

    final_items = []
    for title, items in title_map.items():
        if len(items) > 1:
            items.sort(key=lambda x: x[1], reverse=True)
            best_url, _, best_item = items[0]
            final_items.append(best_item)
        else:
            _, _, item = items[0]
            final_items.append(item)

    # Sort by weighted score descending
    final_items.sort(key=lambda x: scores[x.url], reverse=True)

    # Add weighted score to metadata
    for item in final_items:
        item.metadata["weighted_score"] = item.metadata.get("weighted_score", scores[item.url])

    # Apply max_results limit
    if max_results is not None:
        final_items = final_items[:max_results]

    return final_items


def run_hybrid_ensemble(
    query: str,
    config: HybridEnsembleConfig | None = None,
) -> EnsembleResult:
    """Run the full hybrid ensemble pipeline.

    Executes Query Expansion + HyDE + Multi-HyDE -> Ensemble Fusion.

    Args:
        query: The search query.
        config: Optional HybridEnsembleConfig.

    Returns:
        EnsembleResult with combined results and metadata.

    Raises:
        TypeError: If query is None.
        ValueError: If query is empty.
    """
    if query is None:
        raise TypeError("query cannot be None")
    if not isinstance(query, str) or query.strip() == "":
        raise ValueError("query cannot be empty")

    if config is None:
        config = HybridEnsembleConfig()

    # Collect all result lists
    all_results = []
    sources_used = defaultdict(int)
    query_variants = []

    # Query expansion results would be added here if enabled
    if config.enable_query_expansion:
        query_variants.append(query)

    # Single HyDE results would be added here if enabled
    if config.enable_single_hyde:
        pass  # Would add HyDE results

    # Multi-HyDE results would be added here for each perspective
    if config.enable_multi_hyde:
        for perspective in config.hyde_perspectives:
            pass  # Would add multi-HyDE results per perspective

    # Apply ensemble fusion
    if config.ensemble_method == "weighted_average":
        combined_results = weighted_average_fusion(
            all_results, max_results=config.max_results
        )
    else:  # reciprocal_rank_fusion (default)
        combined_results = reciprocal_rank_fusion(
            all_results, k=config.rrf_k, max_results=config.max_results
        )

    # Build sources_used dict
    for item in combined_results:
        sources_used[item.source] += 1

    return EnsembleResult(
        combined_results=combined_results,
        sources_used=dict(sources_used),
        ensemble_method=config.ensemble_method,
        query_variants=query_variants,
        metadata={
            "enable_query_expansion": config.enable_query_expansion,
            "enable_single_hyde": config.enable_single_hyde,
            "enable_multi_hyde": config.enable_multi_hyde,
        },
    )
