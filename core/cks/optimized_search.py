"""Optimized Search Pipeline - Combines all search optimizations.

This module provides a unified search pipeline that combines:
1. Query Expansion - Expands abbreviations and related terms
2. Hybrid Search - FTS5 keyword + semantic search with RRF fusion
3. MMR Diversification - Reduces duplicate/similar results

Usage:
    from .optimized_search import search_optimized, patch_optimized_search

    # Direct usage
    results = search_optimized(cks_instance, "python async patterns")

    # Or patch CKS to use optimized search by default
    patch_optimized_search(CKS)
    cks = CKS()
    results = cks.search("python async patterns")  # Now uses full pipeline
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

    from .unified import CKS


def _result_similarity(item1: dict, item2: dict) -> float:
    """Calculate Jaccard similarity between two search results.

    Uses content and title for similarity calculation.

    Args:
        item1: First result dict
        item2: Second result dict

    Returns:
        Similarity score between 0 and 1

    """
    # Extract text content from both items
    text1 = (
        item1.get("title", "") + " " + item1.get("content", "") + " " + item1.get("type", "")
    ).lower()

    text2 = (
        item2.get("title", "") + " " + item2.get("content", "") + " " + item2.get("type", "")
    ).lower()

    # Tokenize into word sets
    set1 = set(text1.split())
    set2 = set(text2.split())

    if not set1 or not set2:
        return 0.0

    # Jaccard similarity: intersection / union
    intersection = len(set1 & set2)
    union = len(set1 | set2)

    return intersection / union if union > 0 else 0.0


def search_optimized(
    self: CKS,
    query: str,
    entry_type: str | None = None,
    limit: int = 5,
    expand_query: bool = True,
    use_mmr: bool = True,
    mmr_lambda: float = 0.7,
    fusion_method: str = "rrf",
) -> list[dict]:
    """Optimized search combining query expansion, hybrid search, and MMR diversification.

    Pipeline:
    1. Query Expansion - Expands abbreviations and adds related terms
    2. Hybrid Search - FTS5 keyword + semantic search with RRF fusion
    3. MMR Diversification - Reduces duplicate/similar results in final output

    Args:
        self: CKS instance
        query: Search query text
        entry_type: Filter by entry type (optional)
        limit: Maximum results to return
        expand_query: Enable query expansion (default: True)
        use_mmr: Enable MMR diversification (default: True)
        mmr_lambda: MMR lambda parameter (0=relevance, 1=diversity, default: 0.7)
        fusion_method: Fusion method for hybrid search ('rrf', 'weighted', 'adaptive')

    Returns:
        Optimized and diversified search results

    """
    from .query_expansion import expand_query_if_enabled
    from .reranking import maximal_marginal_relevance

    # Step 1: Query Expansion
    expanded_queries = [query]
    if expand_query:
        try:
            expanded = expand_query_if_enabled(query, enabled=True)
            if expanded and isinstance(expanded, list):
                # Add expanded queries, remove duplicates
                expanded_queries = list({query, *expanded})
        except Exception:
            # If expansion fails, continue with original query
            pass

    # Step 2: Run hybrid search for each expanded query variant
    all_results: list[dict] = []
    seen_ids: set = set()

    for variant in expanded_queries[:3]:  # Limit to 3 query variants to avoid explosion
        try:
            # Use the hybrid search method (already patched onto CKS)
            variant_results = self.search_hybrid(
                variant,
                entry_type=entry_type,
                limit=limit * 2,  # Fetch more for MMR to work with
                fusion_method=fusion_method,
            )

            # Deduplicate by ID while preserving order
            for result in variant_results:
                result_id = result.get("id")
                if result_id and result_id not in seen_ids:
                    seen_ids.add(result_id)
                    all_results.append(result)
                elif not result_id:
                    all_results.append(result)

        except Exception:
            # If hybrid search fails, skip this variant
            continue

    # If no results from hybrid search, return empty
    if not all_results:
        return []

    # Step 3: Apply MMR diversification if enabled
    if use_mmr and len(all_results) > 1:
        try:
            diversified = maximal_marginal_relevance(
                query=query,
                results=all_results,
                lambda_param=mmr_lambda,
                get_similarity_func=_result_similarity,
                limit=limit,
            )
            return diversified[:limit]
        except Exception:
            # If MMR fails, return top results by score
            return sorted(
                all_results,
                key=lambda r: r.get("weighted_score", r.get("final_score", r.get("similarity", 0))),
                reverse=True,
            )[:limit]

    # Return top results by score if MMR disabled
    return sorted(
        all_results,
        key=lambda r: r.get("weighted_score", r.get("final_score", r.get("similarity", 0))),
        reverse=True,
    )[:limit]


def patch_optimized_search(cks_class: type) -> type:
    """Patch CKS class to use optimized search by default.

    This replaces the default search method with the full optimized pipeline.

    Args:
        cks_class: The CKS class to patch

    Returns:
        The patched CKS class

    """
    # Store the original search method (may already be hybrid-patched)
    original_search = cks_class.search

    # Replace with optimized search
    cks_class.search = search_optimized
    cks_class.search_optimized = search_optimized

    # Keep reference to original for fallback
    cks_class._search_original = original_search

    return cks_class


def search_parallel_backends(
    query: str,
    backends: dict[str, Callable],
    limit: int = 10,
    use_mmr: bool = True,
    mmr_lambda: float = 0.7,
) -> list[dict]:
    """Search multiple backends in parallel with optional MMR diversification.

    This is the unified search that combines results from:
    - CHS (Chat History Search)
    - CKS (Constitutional Knowledge System)
    - CDS (Code/Documentation Search)
    - Grep (Code search via ripgrep)

    Args:
        query: Search query text
        backends: Dict of backend name -> search function
        limit: Maximum results to return
        use_mmr: Enable MMR diversification (default: True)
        mmr_lambda: MMR lambda parameter (default: 0.7)

    Returns:
        Merged and diversified results from all backends

    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    from .reranking import maximal_marginal_relevance

    # Execute searches in parallel
    all_results: list[dict] = []

    with ThreadPoolExecutor() as executor:
        future_to_backend = {
            executor.submit(backend.search, query): name for name, backend in backends.items()
        }

        for future in as_completed(future_to_backend):
            try:
                results = future.result()
                if results:
                    # Add source backend to results
                    backend_name = future_to_backend[future]
                    for result in results:
                        result["source_backend"] = backend_name
                    all_results.extend(results)
            except Exception:
                # Handle backend failure gracefully
                pass

    # Rank by score
    ranked = sorted(
        all_results,
        key=lambda r: r.get("score", r.get("similarity", 0)),
        reverse=True,
    )

    # Apply MMR diversification if enabled
    if use_mmr and len(ranked) > 1:
        try:
            diversified = maximal_marginal_relevance(
                query=query,
                results=ranked,
                lambda_param=mmr_lambda,
                get_similarity_func=_result_similarity,
                limit=limit,
            )
            return diversified[:limit]
        except Exception:
            return ranked[:limit]

    return ranked[:limit]
