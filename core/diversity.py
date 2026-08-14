"""MMR (Maximal Marginal Relevance) diversity ranking for search results.

Reduces redundancy by balancing relevance to query with diversity
from already-selected results.

Formula:
    MMR_score = lambda * relevance_score - (1 - lambda) * max_similarity

Where:
- lambda: Balance parameter (0=pure diversity, 1=pure relevance)
- relevance_score: Original search result score
- max_similarity: Maximum similarity to any already-selected result
"""
from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class DiversityConfig:
    """Configuration for MMR diversity ranking."""
    lambda_param: float = 0.7  # Balance: 0=pure diversity, 1=pure relevance
    content_field: str = "content"  # Field to use for similarity computation
    similarity_threshold: float = 0.8  # Results above this are considered redundant
    add_metadata: bool = True  # Add diversity metadata to results


def compute_similarity(
    result1: dict[str, Any],
    result2: dict[str, Any],
    content_field: str = "content",
) -> float:
    """Compute similarity between two search results.

    Uses simple token overlap Jaccard similarity.
    For production, consider using embeddings for semantic similarity.

    Args:
        result1: First result
        result2: Second result
        content_field: Field to compare (default: "content")

    Returns:
        Similarity score between 0 and 1
    """
    content1 = result1.get(content_field, "")
    content2 = result2.get(content_field, "")

    if not content1 or not content2:
        return 0.0

    # Tokenize by words
    tokens1 = set(content1.lower().split())
    tokens2 = set(content2.lower().split())

    if not tokens1 or not tokens2:
        return 0.0

    # Jaccard similarity
    intersection = tokens1 & tokens2
    union = tokens1 | tokens2

    return len(intersection) / len(union) if union else 0.0


def mmr_rerank(
    results: list[dict[str, Any]],
    lambda_param: float = 0.7,
    content_field: str = "content",
    similarity_fn: Callable[[dict[str, Any], dict[str, Any]], float] | None = None,
    add_metadata: bool = False,
) -> list[dict[str, Any]]:
    """Re-rank results using Maximal Marginal Relevance (MMR).

    Selects results iteratively, balancing:
    - Relevance to the query (original score)
    - Diversity from already-selected results

    Args:
        results: List of search results (dict with 'score' and content field)
        lambda_param: Balance between relevance (1) and diversity (0)
        content_field: Field to use for similarity computation
        similarity_fn: Optional custom similarity function
        add_metadata: Whether to add diversity metadata to results

    Returns:
        Re-ranked list of results
    """
    if not results:
        return results

    # Use default similarity if not provided
    if similarity_fn is None:
        def similarity_fn(r1, r2):
            return compute_similarity(r1, r2, content_field)

    # Create copies to avoid modifying originals
    remaining = list(results)
    selected: list[dict[str, Any]] = []

    while remaining:
        best_score = -float('inf')
        best_idx = 0
        best_result = None

        for i, candidate in enumerate(remaining):
            # Get original relevance score
            relevance = candidate.get("score", 0.0)

            # Compute max similarity to already-selected results
            if selected:
                max_similarity = max(
                    similarity_fn(candidate, sel) for sel in selected
                )
            else:
                max_similarity = 0.0

            # MMR score: balance relevance and diversity
            mmr_score = lambda_param * relevance - (1 - lambda_param) * max_similarity

            if mmr_score > best_score:
                best_score = mmr_score
                best_idx = i
                best_result = candidate

        # Add diversity metadata if requested
        if add_metadata and best_result:
            best_result = dict(best_result)  # Copy
            best_result["mmr_score"] = round(best_score, 3)
            if selected:
                best_result["max_similarity"] = round(
                    max(similarity_fn(best_result, sel) for sel in selected), 3
                )
            else:
                best_result["max_similarity"] = 0.0

        # Move best result from remaining to selected
        if best_result:
            selected.append(best_result)
            remaining.pop(best_idx)
        else:
            break

    return selected


def filter_redundant(
    results: list[dict[str, Any]],
    threshold: float = 0.9,
    content_field: str = "content",
) -> list[dict[str, Any]]:
    """Filter out highly redundant results.

    Removes results that are too similar to higher-ranked results.

    Args:
        results: List of search results
        threshold: Similarity threshold above which results are filtered
        content_field: Field to use for similarity computation

    Returns:
        Filtered list with redundant results removed
    """
    if not results:
        return results

    filtered = []
    for result in results:
        # Check similarity to all already-selected results
        is_redundant = False
        for selected in filtered:
            sim = compute_similarity(result, selected, content_field)
            if sim >= threshold:
                is_redundant = True
                # Mark as redundant
                result.get("metadata", {})["_redundant"] = True
                result.get("metadata", {})["_similar_to"] = selected.get("id")
                break

        if not is_redundant:
            filtered.append(result)

    return filtered


def get_diverse_subset(
    results: list[dict[str, Any]],
    n: int,
    lambda_param: float = 0.5,
    content_field: str = "content",
) -> list[dict[str, Any]]:
    """Get a diverse subset of results using MMR.

    Useful for limiting token usage while maintaining diversity.

    Args:
        results: List of search results
        n: Maximum number of results to return
        lambda_param: MMR balance parameter
        content_field: Field for similarity computation

    Returns:
        Diverse subset of results (max n items)
    """
    if not results or n <= 0:
        return []

    # Apply MMR and take top n
    reranked = mmr_rerank(results, lambda_param=lambda_param, content_field=content_field)
    return reranked[:n]
