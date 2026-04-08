"""HyDE Integration Layer for CKS Semantic Search.

This module provides a wrapper that applies HyDE (Hypothetical Document Embeddings)
to CKS semantic search without modifying the core CKS files.

Usage:
    from .hyde_integration import hyde_search_semantic

    # Use instead of cks.search_semantic()
    results = hyde_search_semantic(cks, "how to fix permission denied", limit=10)

Based on: "Precise Zero-Shot Dense Retrieval without Relevance Labels"
by Luyu Gao et al. (2022).
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

try:
    from .hyde import HyDEQueryExpander

    HYDE_AVAILABLE = True
except ImportError:
    HYDE_AVAILABLE = False

# Global HyDE expander instance (shared across calls)
_hyde_expander: HyDEQueryExpander | None = None


def _get_hyde_expander() -> HyDEQueryExpander | None:
    """Get or create the global HyDE expander instance."""
    global _hyde_expander
    if not HYDE_AVAILABLE:
        return None
    if _hyde_expander is None:
        _hyde_expander = HyDEQueryExpander()
    return _hyde_expander


def detect_query_type(query: str) -> str:
    """Detect the type of query for HyDE hypothetical generation.

    Args:
        query: User's search query

    Returns:
        Query type: code, pattern, knowledge, or general

    """
    query_lower = query.lower()

    # Code-related queries
    code_keywords = [
        "implement",
        "code",
        "function",
        "class",
        "api",
        "syntax",
        "debug",
        "error",
        "fix",
        "bug",
        "compile",
        "test",
        "refactor",
    ]
    if any(kw in query_lower for kw in code_keywords):
        return "code"

    # Pattern/how-to queries
    pattern_keywords = [
        "how",
        "what",
        "pattern",
        "best practice",
        "approach",
        "way to",
        "method for",
    ]
    if any(kw in query_lower for kw in pattern_keywords):
        return "pattern"

    # Knowledge/concept queries
    knowledge_keywords = [
        "explain",
        "concept",
        "understand",
        "learn",
        "difference",
        "vs",
        "versus",
        "meaning",
        "definition",
    ]
    if any(kw in query_lower for kw in knowledge_keywords):
        return "knowledge"

    return "general"


def hyde_search_semantic(
    cks_instance: Any,
    query: str,
    entry_type: str | None = None,
    limit: int = 10,
    enable_hyde: bool = True,
    **kwargs,
) -> list[dict]:
    """Search CKS with HyDE query expansion for improved relevance.

    This wrapper function applies HyDE (Hypothetical Document Embeddings)
    to improve semantic search results by generating a hypothetical answer
    to the query and searching with both the query and hypothetical text.

    Args:
        cks_instance: CKS instance to search
        query: Search query text
        entry_type: Optional entry type filter
        limit: Maximum results to return
        enable_hyde: Enable HyDE expansion (default: True)
        **kwargs: Additional arguments passed to CKS search_semantic

    Returns:
        List of search results with improved relevance

    Example:
        >>> from .unified import CKS
        >>> from .hyde_integration import hyde_search_semantic
        >>> cks = CKS()
        >>> results = hyde_search_semantic(cks, "how to fix permission denied")

    """
    if not enable_hyde or not HYDE_AVAILABLE:
        # Fall back to standard semantic search
        return cks_instance.search_semantic(
            query=query,
            entry_type=entry_type,
            limit=limit,
            **kwargs,
        )

    expander = _get_hyde_expander()
    if expander is None:
        # HyDE not available, use standard search
        return cks_instance.search_semantic(
            query=query,
            entry_type=entry_type,
            limit=limit,
            **kwargs,
        )

    # Detect query type for better hypothetical generation
    query_type = detect_query_type(query)

    # Generate hypothetical document
    hypothetical = expander.generate_hypothetical(query, query_type)

    # Expand query with hypothetical document
    expanded_query = expander.expand_query(query, query_type)

    logger.debug(f"HyDE: query_type={query_type}, hypothetical_len={len(hypothetical)}")

    # Search with expanded query
    try:
        results = cks_instance.search_semantic(
            query=expanded_query,
            entry_type=entry_type,
            limit=limit,
            **kwargs,
        )

        # Add HyDE metadata to results
        for r in results:
            r["_hyde_expanded"] = True
            r["_hyde_query_type"] = query_type

        return results

    except Exception as e:
        logger.warning(f"HyDE search failed, falling back to standard search: {e}")
        return cks_instance.search_semantic(
            query=query,
            entry_type=entry_type,
            limit=limit,
            **kwargs,
        )


def hyde_search_with_boost(
    cks_instance: Any,
    query: str,
    entry_type: str | None = None,
    limit: int = 10,
    boost_factor: float = 1.1,
    **kwargs,
) -> list[dict]:
    """Search with HyDE AND separate query+hypothetical searches for boost.

    This more aggressive approach:
    1. Searches with original query
    2. Searches with hypothetical document
    3. Combines and re-ranks results

    Better for complex queries but slower (~2x search time).

    Args:
        cks_instance: CKS instance to search
        query: Search query text
        entry_type: Optional entry type filter
        limit: Maximum results to return
        boost_factor: Boost score for results from hypothetical search
        **kwargs: Additional arguments passed to CKS search_semantic

    Returns:
        Combined and re-ranked search results

    """
    if not HYDE_AVAILABLE:
        return cks_instance.search_semantic(
            query=query,
            entry_type=entry_type,
            limit=limit,
            **kwargs,
        )

    expander = _get_hyde_expander()
    if expander is None:
        return cks_instance.search_semantic(
            query=query,
            entry_type=entry_type,
            limit=limit,
            **kwargs,
        )

    query_type = detect_query_type(query)
    hypothetical = expander.generate_hypothetical(query, query_type)

    # Search with both queries
    query_results = cks_instance.search_semantic(
        query=query,
        entry_type=entry_type,
        limit=limit * 2,  # Get more for combination
        **kwargs,
    )

    hypo_results = cks_instance.search_semantic(
        query=hypothetical,
        entry_type=entry_type,
        limit=limit * 2,
        **kwargs,
    )

    # Combine results with boost
    seen_ids = {}
    combined = []

    for r in query_results:
        result_id = r.get("id", "")
        if result_id and result_id not in seen_ids:
            r["_hyde_boost"] = 1.0
            r["_combined_score"] = r.get("similarity", 0.0) * 1.0
            seen_ids[result_id] = r
            combined.append(r)

    for r in hypo_results:
        result_id = r.get("id", "")
        if result_id:
            if result_id in seen_ids:
                # Already in results, boost the score
                existing = seen_ids[result_id]
                existing["_hyde_boost"] = boost_factor
                existing["_combined_score"] = (
                    existing.get("similarity", 0.0) + r.get("similarity", 0.0) * boost_factor
                )
            else:
                # New result from hypothetical search
                r["_hyde_boost"] = boost_factor
                r["_combined_score"] = r.get("similarity", 0.0) * boost_factor
                seen_ids[result_id] = r
                combined.append(r)

    # Sort by combined score
    combined.sort(key=lambda x: x.get("_combined_score", 0), reverse=True)

    return combined[:limit]


__all__ = [
    "detect_query_type",
    "hyde_search_semantic",
    "hyde_search_with_boost",
]
