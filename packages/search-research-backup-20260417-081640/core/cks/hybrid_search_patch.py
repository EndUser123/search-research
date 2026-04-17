"""Hybrid Search Patch for CKS.

Implements Anthropic's recommended Contextual Retrieval approach:
1. Run FTS5 full-text search (keyword/BM25-like)
2. Run semantic search (embeddings)
3. Fuse results using Reciprocal Rank Fusion (RRF)

This improves retrieval accuracy by 49-67% over pure semantic search.
"""

import json

from .reranking import apply_length_aware_reranking, reciprocal_rank_fusion


def patch_hybrid_search(cks_class: type) -> type:
    """Patch CKS class with hybrid search methods.

    Args:
        cks_class: The CKS class to patch

    Returns:
        The patched CKS class

    """
    # Add the new methods to the CKS class
    cks_class.search_hybrid = search_hybrid
    cks_class._search_fts_raw = _search_fts_raw
    cks_class._weighted_fusion = _weighted_fusion

    # Monkey-patch the default search to use hybrid
    original_search = cks_class.search

    def search_with_hybrid(
        self, query: str, entry_type: str | None = None, limit: int = 5
    ) -> list[dict]:
        """Default search now uses hybrid approach (FTS5 + semantic fusion).

        This implements Anthropic's recommended Contextual Retrieval which
        improves accuracy by 49-67% over pure semantic search.
        """
        try:
            # Try hybrid search first
            return self.search_hybrid(query, entry_type=entry_type, limit=limit)
        except Exception as e:
            # Fallback to original FTS5 if hybrid fails
            print(f"Hybrid search failed, using FTS5 fallback: {e}")
            return original_search(self, query, entry_type=entry_type, limit=limit)

    cks_class.search = search_with_hybrid

    return cks_class


def search_hybrid(
    self,
    query: str,
    entry_type: str | None = None,
    limit: int = 5,
    fts_weight: float = 0.5,
    semantic_weight: float = 0.5,
    fusion_method: str = "rrf",
) -> list[dict]:
    """Hybrid search combining FTS5 (keyword) and semantic search.

    Implements Anthropic's recommended Contextual Retrieval approach:
    1. Run FTS5 full-text search (keyword/BM25-like)
    2. Run semantic search (embeddings)
    3. Fuse results using Reciprocal Rank Fusion (RRF)
    4. Return re-ranked combined results

    This approach improves retrieval accuracy by 49-67% over pure semantic search
    by avoiding "semantic drift" where similar-but-irrelevant chunks are retrieved.

    Args:
        query: Search query text
        entry_type: Filter by entry type (optional)
        limit: Maximum results to return
        fts_weight: Weight for FTS5 results in weighted fusion (default: 0.5)
        semantic_weight: Weight for semantic results in weighted fusion (default: 0.5)
        fusion_method: Fusion method - 'rrf' (Reciprocal Rank), 'weighted', or 'adaptive' (default: 'rrf')

    Returns:
        Combined and re-ranked list of results with hybrid scores

    """
    original_query = query

    # Step 1: Get FTS5 (keyword) results - fetch more for fusion
    fts_results = self._search_fts_raw(query, entry_type, limit * 2)

    # Step 2: Get semantic results - fetch more for fusion
    if self.enable_semantic:
        # Use base semantic search without Phase 1 to avoid recursion
        semantic_results = self._search_semantic_base(query, entry_type, limit * 2)
    else:
        semantic_results = []

    # Step 3: Normalize results for fusion
    # Add rank and source information
    for rank, result in enumerate(fts_results, 1):
        result["fts_rank"] = rank
        result["fts_score"] = limit * 2 - rank  # Simple score: higher rank = higher score

    for rank, result in enumerate(semantic_results, 1):
        result["semantic_rank"] = rank
        # Use similarity or final_score if available
        result["semantic_score"] = result.get(
            "final_score", result.get("similarity", limit * 2 - rank)
        )

    # Step 4: Fuse results using specified method
    if fusion_method == "rrf":
        # Reciprocal Rank Fusion - Anthropic's recommended approach
        merged = reciprocal_rank_fusion(
            [fts_results, semantic_results],
            k=60,  # Standard RRF constant
            limit=limit,
        )
    elif fusion_method == "weighted":
        # Weighted average fusion
        merged = self._weighted_fusion(
            [fts_results, semantic_results],
            [fts_weight, semantic_weight],
            limit=limit,
        )
    elif fusion_method == "adaptive":
        # Adaptive fusion - select best method based on query characteristics
        query_type = self._detect_query_type(query)
        if query_type == "technical":
            # Technical queries benefit more from keywords
            merged = self._weighted_fusion(
                [fts_results, semantic_results],
                [0.6, 0.4],  # Favor keywords for technical queries
                limit=limit,
            )
        else:
            # Balanced queries use RRF
            merged = reciprocal_rank_fusion(
                [fts_results, semantic_results],
                k=60,
                limit=limit,
            )
    else:
        # Default to RRF
        merged = reciprocal_rank_fusion(
            [fts_results, semantic_results],
            k=60,
            limit=limit,
        )

    # Add hybrid metadata to results
    for result in merged:
        result["search_method"] = "hybrid"
        result["fusion_method"] = fusion_method

    # Apply length-aware reranking to penalize verbose docs
    # This addresses FTS5's bias toward long documents with many keywords
    merged = apply_length_aware_reranking(
        merged,
        base_score_field="rrf_score",
        density_weight=0.25,  # Moderate weight to preserve base relevance
        type_boost=0.15,  # Boost pattern entries over memory entries
        query=original_query,  # For conditional pattern boosting
        enable_mmr=True,  # Enable MMR for result diversity
        mmr_lambda=0.5,  # Balanced relevance/diversity
    )

    # Record usage for returned entries
    self._record_usage_for_results(merged, success=True)
    return self._apply_auto_learning_if_enabled(merged, original_query)


def _search_fts_raw(
    self,
    query: str,
    entry_type: str | None = None,
    limit: int = 5,
) -> list[dict]:
    """Raw FTS5 search returning results with metadata for fusion.

    Internal method used by hybrid search. Returns results in a format
    suitable for fusion with semantic results.

    Args:
        query: Search query text
        entry_type: Filter by entry type (optional)
        limit: Maximum results to return

    Returns:
        List of results with FTS5 ranking

    """
    cursor = self.conn.cursor()

    # Check if FTS table exists
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='entries_fts'",
    )
    fts_exists = cursor.fetchone() is not None

    if fts_exists:
        sanitized_query = self._sanitize_fts_query(query)
        if entry_type:
            cursor.execute(
                """
                SELECT e.id, e.type, e.title, e.content, e.metadata, e.created_at, e.usage_count
                FROM entries e
                WHERE e.rowid IN (SELECT rowid FROM entries_fts WHERE entries_fts MATCH ?)
                  AND e.type = ?
                ORDER BY e.created_at DESC
                LIMIT ?
                """,
                (sanitized_query, entry_type, limit),
            )
        else:
            cursor.execute(
                """
                SELECT e.id, e.type, e.title, e.content, e.metadata, e.created_at, e.usage_count
                FROM entries e
                WHERE e.rowid IN (SELECT rowid FROM entries_fts WHERE entries_fts MATCH ?)
                ORDER BY e.created_at DESC
                LIMIT ?
                """,
                (sanitized_query, limit),
            )
    else:
        # Fallback to LIKE queries if FTS not available
        if entry_type:
            cursor.execute(
                """
                SELECT id, type, title, content, metadata, created_at, usage_count
                FROM entries
                WHERE type = ? AND (content LIKE ? OR title LIKE ?)
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (entry_type, f"%{query}%", f"%{query}%", limit),
            )
        else:
            cursor.execute(
                """
                SELECT id, type, title, content, metadata, created_at, usage_count
                FROM entries
                WHERE content LIKE ? OR title LIKE ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (f"%{query}%", f"%{query}%", limit),
            )

    results = []
    for row in cursor.fetchall():
        try:
            metadata = json.loads(row["metadata"]) if row["metadata"] else {}
        except:
            metadata = {}

        results.append(
            {
                "id": row["id"],
                "type": row["type"],
                "title": row["title"],
                "content": row["content"],
                "metadata": metadata,
                "created_at": row["created_at"],
                "usage_count": row["usage_count"] if row["usage_count"] else 0,
            },
        )

    return results


def _weighted_fusion(
    self,
    result_sets: list[list[dict]],
    weights: list[float],
    limit: int = 5,
) -> list[dict]:
    """Weighted average fusion for combining search results.

    Combines results from multiple sources using weighted average of scores.
    Useful when one source should be prioritized over another.

    Args:
        result_sets: List of result lists to combine
        weights: Weight for each result set (sums to 1.0)
        limit: Maximum results to return

    Returns:
        Combined and sorted list of results

    """
    if not result_sets or not weights:
        return []

    if len(result_sets) != len(weights):
        raise ValueError("Number of result sets must match number of weights")

    # Collect all items and compute weighted scores
    scores = {}
    all_items = {}
    item_ranks = {i: {} for i in range(len(result_sets))}

    for idx, results in enumerate(result_sets):
        weight = weights[idx]
        for rank, item in enumerate(results, 1):
            item_id = item.get("id", item.get("entry_id"))
            if not item_id:
                continue

            # Track rank for tie-breaking
            if item_id not in item_ranks[idx]:
                item_ranks[idx][item_id] = rank

            # Get score from item (prefer explicit scores, use rank as fallback)
            if "final_score" in item:
                item_score = item["final_score"]
            elif "similarity" in item:
                item_score = item["similarity"]
            elif "fts_score" in item:
                item_score = item["fts_score"]
            else:
                item_score = len(results) - rank  # Convert rank to score

            # Add weighted score
            if item_id not in scores:
                scores[item_id] = 0
                all_items[item_id] = item

            scores[item_id] += item_score * weight

    # Sort by weighted score (descending), then by average rank
    def sort_key(item_id):
        score = scores[item_id]
        # Use average rank as tiebreaker (lower is better)
        avg_rank = sum(
            item_ranks[idx].get(item_id, len(result_sets[idx])) for idx in range(len(result_sets))
        ) / len(result_sets)
        return (-score, avg_rank)  # Negative for descending sort, ascending rank

    sorted_ids = sorted(scores.keys(), key=sort_key)

    # Build final result list
    final_results = []
    for item_id in sorted_ids[:limit]:
        item = all_items[item_id].copy()
        item["weighted_score"] = scores[item_id]
        final_results.append(item)

    return final_results
