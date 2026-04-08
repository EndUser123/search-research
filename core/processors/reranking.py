"""Reranking methods for improving search result diversity and freshness."""

from datetime import datetime, timezone
from typing import Any, Callable
import math


def maximal_marginal_relevance(
    query: str,
    results: list,
    lambda_param: float = 0.5,
    limit: int | None = None,
    get_similarity_func: Callable[[Any, Any], float] | None = None,
) -> list:
    """Rerank results using Maximal Marginal Relevance (MMR).

    MMR balances relevance to query with diversity from already selected results.
    Formula: MMR = lambda * relevance - (1 - lambda) * max_similarity

    Args:
        query: The search query.
        results: List of search results to rerank.
        lambda_param: Balance between relevance (0) and diversity (1).
        limit: Maximum number of results to return.
        get_similarity_func: Optional custom similarity function.

    Returns:
        Reranked list of results.
    """
    if not results:
        return []

    if limit is not None and limit <= 0:
        return []

    # Default similarity function using content overlap
    def default_similarity(item1: Any, item2: Any) -> float:
        # Simple content-based similarity using Jaccard-like approach
        words1 = set(item1.content.lower().split())
        words2 = set(item2.content.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0

    similarity_func = get_similarity_func or default_similarity

    # Copy results to avoid modifying input
    remaining = list(results)
    selected = []

    # Select first item by highest score
    if remaining:
        # Sort by score descending for first pick
        remaining.sort(key=lambda x: x.score, reverse=True)
        selected.append(remaining.pop(0))

    # Select remaining items using MMR
    while remaining and (limit is None or len(selected) < limit):
        best_score = -float('inf')
        best_idx = 0

        for idx, item in enumerate(remaining):
            # Relevance is the item's original score
            relevance = item.score

            # Find max similarity to any selected item
            max_sim = 0.0
            for sel in selected:
                sim = similarity_func(item, sel)
                max_sim = max(max_sim, sim)

            # MMR score
            mmr_score = lambda_param * relevance - (1 - lambda_param) * max_sim

            if mmr_score > best_score:
                best_score = mmr_score
                best_idx = idx

        selected.append(remaining.pop(best_idx))

    return selected


def calculate_temporal_boost(
    entry: dict[str, Any],
    half_life_days: int = 180,
) -> float:
    """Calculate temporal boost factor based on recency and usage.

    Uses half-life decay formula: boost = 2^(-age/half_life) * usage_factor

    Args:
        entry: Dictionary with created_at, usage_count, thumbs_up, thumbs_down.
        half_life_days: Half-life in days for decay (default 180).

    Returns:
        Boost factor between 0.5 and 1.5.
    """
    now = datetime.now(timezone.utc)

    # Get creation date
    created_at_str = entry.get("created_at", "")
    if not created_at_str:
        return 1.0

    try:
        # Parse ISO format date
        if isinstance(created_at_str, str):
            created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
        else:
            created_at = created_at_str
    except (ValueError, AttributeError):
        return 1.0

    # Calculate age in days
    age = (now - created_at).total_seconds() / 86400

    # Half-life decay
    decay = math.pow(0.5, age / half_life_days)

    # Base boost from decay (0.5 to 1.0)
    base_boost = 0.5 + 0.5 * decay

    # Usage factor
    usage_count = entry.get("usage_count", 0)
    usage_factor = min(1.5, 1.0 + usage_count * 0.01)

    # Feedback factor
    thumbs_up = entry.get("thumbs_up", 0)
    thumbs_down = entry.get("thumbs_down", 0)

    if thumbs_up + thumbs_down > 0:
        success_rate = thumbs_up / (thumbs_up + thumbs_down)
        feedback_factor = 0.8 + 0.4 * success_rate  # 0.8 to 1.2
    else:
        feedback_factor = 1.0

    # Combine factors
    boost = base_boost * usage_factor * feedback_factor

    # Clamp to reasonable range
    return max(0.5, min(1.5, boost))


def apply_temporal_boosting(
    results: list,
    half_life_days: int = 180,
) -> list:
    """Apply temporal boosting to search results.

    Boosts recent and frequently accessed results.

    Args:
        results: List of search results with metadata.
        half_life_days: Half-life in days for decay (default 180).

    Returns:
        Results with adjusted scores sorted by boosted score.
    """
    if not results:
        return []

    boosted_results = []

    for result in results:
        # Create a copy to avoid modifying original
        boosted = result

        # Check for published_date in metadata
        published_date = result.metadata.get("published_date")

        if published_date:
            entry = {"created_at": published_date}
            boost = calculate_temporal_boost(entry, half_life_days)

            # Apply boost to score
            boosted_score = result.score * boost

            # Store boosted score in metadata
            boosted.metadata = boosted.metadata.copy()
            boosted.metadata["temporal_boost"] = boost
            boosted.metadata["boosted_score"] = boosted_score
            boosted.score = boosted_score

        boosted_results.append(boosted)

    # Sort by boosted score
    boosted_results.sort(key=lambda x: x.score, reverse=True)

    return boosted_results
