"""CKS Advanced Re-ranking Module.

Implements Reciprocal Rank Fusion (RRF), Maximal Marginal Relevance (MMR),
and temporal boosting for improved search result quality.
"""

import math
from datetime import UTC, datetime

# Import MMR from search-research package
try:
    from search_research.diversity import mmr_rerank

    MMR_AVAILABLE = True
except ImportError:
    # search_research.diversity not available, MMR disabled
    MMR_AVAILABLE = False


def reciprocal_rank_fusion(
    result_sets: list[list[dict]],
    k: int = 60,
    limit: int | None = None,
) -> list[dict]:
    """Combine multiple result lists using Reciprocal Rank Fusion (RRF).

    RRF Score = Σ(1 / (k + rank)) for all result lists

    Deduplicates by URL and title (separately). For duplicates, combines RRF scores
    and preserves the longest/richer content.

    Args:
        result_sets: List of result lists to combine
        k: Constant preventing rank from dominating (default: 60)
        limit: Maximum results to return

    Returns:
        Combined and sorted list of results

    """
    # Track deduplication by both URL and title
    # We maintain a mapping from any key (URL or title) to a canonical item
    scores = {}  # canonical_key -> RRF score
    items_by_key = {}  # canonical_key -> item
    key_mapping = {}  # any_key (url/title/id) -> canonical_key

    for results in result_sets:
        for rank, item in enumerate(results, 1):
            # Get identifiers
            item_url = item.get("url", "").strip().lower()
            item_title = item.get("title", "").strip().lower()
            item_id = item.get("id", item.get("entry_id"))

            # Collect all possible keys for this item
            possible_keys = []
            if item_url:
                possible_keys.append(f"url:{item_url}")
            if item_title:
                possible_keys.append(f"title:{item_title}")
            if item_id and not item_url and not item_title:
                possible_keys.append(f"id:{item_id}")

            if not possible_keys:
                continue

            # Find if any of this item's keys already exist
            canonical_key = None
            for key in possible_keys:
                if key in key_mapping:
                    # This item is a duplicate by some criterion
                    canonical_key = key_mapping[key]
                    break

            if canonical_key is None:
                # New unique item - use the first key as canonical
                canonical_key = possible_keys[0]
                # Register all keys mapping to this canonical key
                for key in possible_keys:
                    key_mapping[key] = canonical_key

            # Add to RRF score
            if canonical_key not in scores:
                scores[canonical_key] = 0
            scores[canonical_key] += 1 / (k + rank)

            # Store item data - prefer longer content
            if canonical_key not in items_by_key:
                items_by_key[canonical_key] = item
            else:
                existing = items_by_key[canonical_key]
                existing_content = existing.get("content", "")
                new_content = item.get("content", "")
                if len(new_content) > len(existing_content):
                    items_by_key[canonical_key] = item

    # Sort by RRF score (descending)
    sorted_items = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    # Build final result list
    final_results = []
    for dedupe_key, rrf_score in sorted_items[:limit] if limit else sorted_items:
        item = items_by_key[dedupe_key].copy()
        item["rrf_score"] = rrf_score
        final_results.append(item)

    return final_results


def maximal_marginal_relevance(
    query: str,
    results: list[dict],
    lambda_param: float = 0.7,
    get_similarity_func=None,
    limit: int | None = None,
) -> list[dict]:
    """Re-rank results using Maximal Marginal Relevance (MMR).

    MMR balances relevance with diversity:
    Score = (1-λ) * relevance - λ * max_similarity_to_selected

    Args:
        query: Search query (for relevance scoring)
        results: Initial results to re-rank
        lambda_param: Balance between relevance (0) and diversity (1)
        get_similarity_func: Function to compute similarity between two items
        limit: Maximum results to return

    Returns:
        Re-ranked list with improved diversity

    """
    if not results:
        return results

    if get_similarity_func is None:
        # Default: cosine similarity of embeddings or content comparison
        def default_similarity(item1: dict, item2: dict) -> float:
            # Try to use embeddings if available
            emb1 = item1.get("embedding")
            emb2 = item2.get("embedding")

            if emb1 and emb2:
                # Assume cosine similarity is pre-computed or available
                return _cosine_similarity_from_embeddings(emb1, emb2)

            # Fall back to content similarity
            content1 = item1.get("content", item1.get("answer", "")).lower()
            content2 = item2.get("content", item2.get("answer", "")).lower()

            return _jaccard_similarity(content1, content2)

        get_similarity_func = default_similarity

    selected = []
    remaining = results.copy()

    # Select first item (highest similarity/relevance)
    first_item = remaining.pop(0)
    selected.append(first_item)

    # Iteratively select items balancing relevance and diversity
    while remaining:
        best_score = -float("inf")
        best_idx = 0

        for i, item in enumerate(remaining):
            # Relevance score (use similarity or ranking score)
            relevance = item.get("similarity", item.get("score", 0))

            # Diversity penalty (max similarity to already selected items)
            max_sim_to_selected = 0
            for s in selected:
                sim = get_similarity_func(s, item)
                max_sim_to_selected = max(max_sim_to_selected, sim)

            # MMR score
            mmr_score = (1 - lambda_param) * relevance - lambda_param * max_sim_to_selected

            if mmr_score > best_score:
                best_score = mmr_score
                best_idx = i

        # Add best item to selected list
        selected.append(remaining.pop(best_idx))

    return selected[:limit] if limit is not None else selected


def _cosine_similarity_from_embeddings(emb1, emb2) -> float:
    """Compute cosine similarity between two embedding vectors."""
    try:
        import numpy as np

        vec1 = emb1 if isinstance(emb1, list) else emb1.tolist()
        vec2 = emb2 if isinstance(emb2, list) else emb2.tolist()

        # Compute cosine similarity
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0

        return dot_product / (norm1 * norm2)

    except Exception:
        return 0


def _jaccard_similarity(text1: str, text2: str) -> float:
    """Compute Jaccard similarity between two texts."""
    words1 = set(text1.split())
    words2 = set(text2.split())

    intersection = words1 & words2
    union = words1 | words2

    if len(union) == 0:
        return 0

    return len(intersection) / len(union)


def calculate_temporal_boost(
    entry: dict,
    base_boost: float = 1.0,
    decay_rates: dict[str, float] | None = None,
) -> float:
    """Calculate temporal boost with adaptive forgetting curves.

    Combines:
    - Recency (exponential decay)
    - Frequency (usage count, log scale)
    - Success rate (feedback-based)
    - Entry type adjustments

    Args:
        entry: Entry dictionary with metadata
        base_boost: Base boost factor
        decay_rates: Optional custom decay rates by entry type

    Returns:
        Temporal boost factor (0.5 to 1.5)

    """
    # Parse timestamp
    created_at = entry.get("created_at", "")
    try:
        if "Z" in created_at:
            created_time = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        elif "+" in created_at:
            created_time = datetime.fromisoformat(created_at)
        else:
            created_time = datetime.fromisoformat(created_at).replace(tzinfo=UTC)
    except Exception:
        # If parsing fails, assume recent
        created_time = datetime.now(UTC)

    # Calculate age in days
    age_days = (datetime.now(UTC) - created_time).days

    # Get entry type for adaptive decay
    entry_type = entry.get("type", "memory")

    # Determine decay rate
    if decay_rates and entry_type in decay_rates:
        decay_rate = decay_rates[entry_type]
    else:
        # Adaptive decay by entry type
        if entry_type == "pattern":
            decay_rate = 0.99  # Patterns stay relevant longer
        elif entry_type == "code":
            decay_rate = 0.95  # Code becomes obsolete faster
        else:
            decay_rate = 0.97  # Default

    # Apply exponential decay (Ebbinghaus-style)
    retention = max(0.5, decay_rate**age_days)

    # Usage frequency boost (log scale to avoid overfitting)
    usage_count = entry.get("usage_count", 0)
    frequency_boost = min(1.2, 1.0 + math.log10(usage_count + 1) * 0.1)

    # Success rate boost from feedback
    thumbs_up = entry.get("thumbs_up", 0)
    thumbs_down = entry.get("thumbs_down", 0)
    total_feedback = thumbs_up + thumbs_down

    if total_feedback > 0:
        success_rate = thumbs_up / total_feedback
        success_boost = 0.5 + success_rate  # 0.5 to 1.5 range
    else:
        success_boost = 1.0

    # Combined temporal boost
    temporal_boost = base_boost * retention * frequency_boost * success_boost

    # Clamp to reasonable range
    return max(0.5, min(1.5, temporal_boost))


def adaptive_decay_thresholds(
    query_type: str,
    entry_type: str,
    base_threshold: float = 0.50,
) -> float:
    """Calculate adaptive similarity threshold based on query and entry types.

    Args:
        query_type: Query type (technical, balanced, preference)
        entry_type: Entry type (memory, pattern, code, etc.)
        base_threshold: Base threshold to adjust

    Returns:
        Adjusted threshold (0.40 to 0.70)

    """
    threshold = base_threshold

    # Query type adjustment
    if query_type == "technical":
        threshold -= 0.05  # Higher precision needed
    elif query_type == "preference":
        threshold += 0.05  # More exploratory

    # Entry type adjustment
    if entry_type == "pattern":
        threshold -= 0.03  # Patterns should be easier to find
    elif entry_type == "code":
        threshold += 0.05  # Code requires higher precision

    # Clamp to reasonable range
    return max(0.40, min(0.70, threshold))


class SearchResultsMerger:
    """Merge and de-duplicate search results from multiple sources."""

    @staticmethod
    def merge_results(
        result_sets: list[list[dict]],
        merge_strategy: str = "rrf",
        **kwargs,
    ) -> list[dict]:
        """Merge multiple result sets using specified strategy.

        Args:
            result_sets: List of result lists to merge
            merge_strategy: Strategy to use ('rrf', 'score', 'rank')
            **kwargs: Additional arguments for strategy

        Returns:
            Merged and sorted list of unique results

        """
        if not result_sets:
            return []

        if merge_strategy == "rrf":
            return reciprocal_rank_fusion(result_sets, **kwargs)

        if merge_strategy == "score":
            return SearchResultsMerger._merge_by_score(result_sets)

        if merge_strategy == "rank":
            return SearchResultsMerger._merge_by_rank(result_sets)

        raise ValueError(f"Unknown merge strategy: {merge_strategy}")

    @staticmethod
    def _merge_by_score(result_sets: list[list[dict]]) -> list[dict]:
        """Merge by averaging scores, removing duplicates."""
        seen = {}
        merged = []

        for results in result_sets:
            for item in results:
                item_id = item.get("id", item.get("entry_id"))
                if not item_id or item_id in seen:
                    continue

                seen[item_id] = True
                merged.append(item)

        # Sort by similarity/score
        return sorted(merged, key=lambda x: x.get("similarity", 0), reverse=True)

    @staticmethod
    def _merge_by_rank(result_sets: list[list[dict]]) -> list[dict]:
        """Merge by rank position, removing duplicates."""
        seen = set()
        merged = []

        for results in result_sets:
            for item in results:
                item_id = item.get("id", item.get("entry_id"))
                if not item_id or item_id in seen:
                    continue

                seen.add(item_id)
                merged.append(item)

        return merged


# =============================================================================
# Hybrid Fusion Algorithms (Phase 2 Enhancements)
# =============================================================================


def weighted_average_fusion(
    result_sets: list[list[dict]],
    weights: list[float] | None = None,
    limit: int | None = None,
) -> list[dict]:
    """Combine results using weighted average of similarity scores."""
    if not result_sets:
        return []

    if weights is None:
        weights = [1.0] * len(result_sets)

    all_scores = {}
    all_items = {}

    for results, weight in zip(result_sets, weights, strict=False):
        for result in results:
            entry_id = result.get("id")
            if not entry_id:
                continue

            similarity = result.get("similarity", result.get("score", 0))

            if entry_id not in all_scores:
                all_scores[entry_id] = []
                all_items[entry_id] = result

            all_scores[entry_id].append((weight, similarity))

    fused_results = []
    for entry_id, score_list in all_scores.items():
        weighted_sum = sum(w * s for w, s in score_list)
        weight_sum = sum(w for w, _ in score_list)
        avg_score = weighted_sum / weight_sum if weight_sum > 0 else 0

        result = all_items[entry_id].copy()
        result["fusion_score"] = avg_score
        result["fusion_method"] = "weighted_average"
        fused_results.append(result)

    fused_results.sort(key=lambda x: x["fusion_score"], reverse=True)
    return fused_results[:limit] if limit else fused_results


def combsum_fusion(
    result_sets: list[list[dict]],
    limit: int | None = None,
) -> list[dict]:
    """Combine results by summing similarity scores (CombSUM)."""
    if not result_sets:
        return []

    summed_scores = {}
    all_items = {}

    for results in result_sets:
        for result in results:
            entry_id = result.get("id")
            if not entry_id:
                continue

            similarity = result.get("similarity", result.get("score", 0))

            if entry_id not in summed_scores:
                summed_scores[entry_id] = 0
                all_items[entry_id] = result

            summed_scores[entry_id] += similarity

    fused_results = []
    for entry_id, summed_score in summed_scores.items():
        result = all_items[entry_id].copy()
        result["fusion_score"] = summed_score
        result["fusion_method"] = "combsum"
        fused_results.append(result)

    fused_results.sort(key=lambda x: x["fusion_score"], reverse=True)
    return fused_results[:limit] if limit else fused_results


def adaptive_fusion(
    result_sets: list[list[dict]],
    query_type: str = "balanced",
    limit: int | None = None,
) -> list[dict]:
    """Automatically select best fusion method based on query type."""
    if not result_sets:
        return []

    if query_type == "specific":
        return weighted_average_fusion(result_sets, limit=limit)
    if query_type == "exploratory":
        return reciprocal_rank_fusion(result_sets, limit=limit)
    return combsum_fusion(result_sets, limit=limit)


def detect_query_type(query: str) -> str:
    """Detect query type from text characteristics."""
    query_lower = query.lower()

    if any(p in query_lower for p in ["exact", "precise", "specific"]):
        return "specific"
    if any(p in query_lower for p in ["explore", "find all", "list", "overview"]):
        return "exploratory"
    return "balanced"


# =============================================================================
# Document Length and Content Density Re-ranking (Phase 3)
# =============================================================================


def calculate_content_density(entry: dict) -> float:
    """Calculate content density score (meaningful information per character).

    Higher density = more focused, less verbose content.
    This penalizes large comprehensive docs that match many keywords.

    Args:
        entry: Entry dictionary with content/title

    Returns:
        Density score (0.0 to 1.0, higher is better)

    """
    content = entry.get("content", "")
    title = entry.get("title", "")

    # Total character length
    total_length = len(content) + len(title)

    if total_length == 0:
        return 0.0

    # Count meaningful keywords (alphanumeric sequences)
    import re

    words = re.findall(r"\b\w+\b", content + " " + title)
    unique_words = set(words)

    if not words:
        return 0.0

    # Density metrics:
    # 1. Unique word ratio (high = dense, low = repetitive)
    unique_ratio = len(unique_words) / len(words)

    # 2. Average word length (very short words = fluffy, very long = technical)
    avg_word_len = sum(len(w) for w in words) / len(words)
    # Optimal range: 4-7 characters, penalize extremes
    length_quality = 1.0 - min(0.5, abs(avg_word_len - 5.5) / 10)

    # 3. Length penalty (favor appropriate length for content type)
    # Detect content type by characteristics
    entry_type = entry.get("type", "memory")
    title_lower = title.lower()
    content_lower = content.lower()

    # Detect if this is a comprehensive guide/reference
    is_comprehensive = any(
        keyword in title_lower
        for keyword in [
            "guide",
            "reference",
            "comprehensive",
            "tutorial",
            "complete",
            "documentation",
            "overview",
            "manual",
        ]
    )

    # Detect if this is a code/config file
    is_code = (
        any(
            keyword in title_lower
            for keyword in [
                ".py",
                ".js",
                ".json",
                ".yaml",
                ".toml",
                "config",
                "settings",
            ]
        )
        or entry_type == "code"
    )

    # Length buckets based on content type
    if is_code:
        # Code/config: concise is better, but not too short
        if total_length < 50:
            length_penalty = 0.7  # Too short for code
        elif total_length < 1000:
            length_penalty = 1.0  # Optimal for code
        elif total_length < 3000:
            length_penalty = 0.9  # Longer code file, acceptable
        else:
            length_penalty = 0.6  # Very long code, might need splitting
    elif is_comprehensive:
        # Guides/reference: longer is acceptable and often necessary
        if total_length < 500:
            length_penalty = 0.8  # Too short for a guide
        elif total_length < 3000:
            length_penalty = 1.0  # Good length for focused guide
        elif total_length < 8000:
            length_penalty = 0.95  # Comprehensive guide, still good
        elif total_length < 15000:
            length_penalty = 0.8  # Very comprehensive, acceptable
        else:
            length_penalty = 0.6  # Extremely long, might be verbose
    elif entry_type == "pattern":
        # Patterns should be concise
        if total_length < 100:
            length_penalty = 0.7  # Pattern too short
        elif total_length < 1500:
            length_penalty = 1.0  # Optimal pattern length
        elif total_length < 4000:
            length_penalty = 0.85  # Longer pattern
        else:
            length_penalty = 0.6  # Very long pattern
    else:
        # General content (memories, etc.)
        if total_length < 200:
            length_penalty = 0.8  # Too short, might lack context
        elif total_length < 2000:
            length_penalty = 1.0  # Optimal range
        elif total_length < 5000:
            length_penalty = 0.85  # Getting longer but still good
        elif total_length < 10000:
            length_penalty = 0.7  # Verbose
        else:
            length_penalty = 0.5  # Very verbose

    # Combined density score
    density = unique_ratio * length_quality * length_penalty
    return max(0.0, min(1.0, density))


def apply_length_aware_reranking(
    results: list[dict],
    base_score_field: str = "rrf_score",
    density_weight: float = 0.3,
    type_boost: float = 0.15,
    query: str = "",
    enable_mmr: bool = False,
    mmr_lambda: float = 0.5,
) -> list[dict]:
    """Re-rank results accounting for document length and content density.

    This addresses the FTS5/BM25 bias where large comprehensive docs outrank
    focused specific content. By penalizing verbosity and boosting density,
    we improve relevance for specific queries.

    Args:
        results: Initial results to re-rank
        base_score_field: Field containing the base relevance score
        density_weight: How much to weight content density (0.0-1.0)
        type_boost: Boost factor for "pattern" type entries over "memory"
        query: Search query (used to make pattern boost conditional)
        enable_mmr: Enable MMR diversity reranking after density adjustment
        mmr_lambda: MMR lambda parameter (0=favor diversity, 1=favor relevance, 0.5=balanced)

    Returns:
        Re-ranked list with adjusted scores and MMR metadata if enabled

    """
    if not results:
        return results

    # Normalize query for relevance checking
    query_lower = query.lower()
    query_terms = set(query_lower.split())

    for result in results:
        # Get base score
        base_score = result.get(base_score_field, result.get("score", 0.5))

        # Calculate content density
        density = calculate_content_density(result)

        # Entry type boost (patterns > memories) - but only if relevant
        entry_type = result.get("type", "memory")
        type_multiplier = 1.0

        if entry_type == "pattern" and query:
            # Only boost patterns if they're relevant to the query
            title_lower = result.get("title", "").lower()
            content_lower = result.get("content", "").lower()

            # Check if pattern contains query terms
            pattern_text = title_lower + " " + content_lower
            has_query_terms = any(term in pattern_text for term in query_terms if len(term) > 3)

            # Boost only if pattern is relevant to query
            if has_query_terms:
                type_multiplier = 1.0 + type_boost
            else:
                # No boost for irrelevant patterns
                type_multiplier = 1.0
        elif entry_type == "code":
            type_multiplier = 1.0 + (type_boost * 0.5)

        # Combined score: base * (1 - density_weight) + density * density_weight
        # This preserves relative ordering while boosting dense content
        adjusted_score = base_score * (
            (1 - density_weight)  # Base relevance portion
            + density * density_weight * type_multiplier  # Density boost
        )

        result["density_score"] = density
        result["length_adjusted_score"] = adjusted_score

    # Re-sort by adjusted score
    results.sort(key=lambda x: x.get("length_adjusted_score", 0), reverse=True)

    # Apply MMR for diversity if enabled and available
    if enable_mmr and MMR_AVAILABLE and len(results) > 1:
        # Use length_adjusted_score as relevance input to MMR
        for r in results:
            r["score"] = r.get("length_adjusted_score", r.get(base_score_field, 0))

        results = mmr_rerank(results, lambda_param=mmr_lambda)

        # Restore original score field for reference
        for r in results:
            if "score" in r:
                r["_original_length_adjusted_score"] = r.pop("score")

    return results


def enhance_fts_with_density(
    results: list[dict],
    limit: int = 5,
) -> list[dict]:
    """Apply density-based reranking specifically for FTS5 results.

    FTS5 ranks by keyword frequency, which favors long docs with many keywords.
    This function re-ranks to favor focused, dense content.

    Args:
        results: FTS5 search results
        limit: Maximum results to return

    Returns:
        Re-ranked results with density scoring applied

    """
    if not results:
        return results

    # Calculate density for all results
    for result in results:
        result["density"] = calculate_content_density(result)

        # FTS5 doesn't always provide scores, use rank as fallback
        if "fts_score" not in result:
            fts_rank = result.get("fts_rank", 1)
            result["fts_score"] = max(1, limit * 2 - fts_rank)

    # Apply length-aware reranking
    reranked = apply_length_aware_reranking(
        results,
        base_score_field="fts_score",
        density_weight=0.4,  # Higher weight for pure FTS5
        type_boost=0.2,
    )

    return reranked[:limit]
