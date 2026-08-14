"""Intelligent Default Detection for Search Features.

This module provides automatic activation logic for search features
based on query complexity, execution context, and result characteristics.

Features:
- --explain: Auto-shows for complex or slow queries
- --session: Auto-enables in terminal mode (WT_SESSION detected)
- --cluster: Auto-triggers at 10+ diverse results
"""

from __future__ import annotations

import os
import re
from typing import Any


def should_explain(
    query: str,
    execution_time_ms: float = 0,
    backend_count: int = 1,
    result_count: int | None = None,
) -> bool:
    """Determine if query explanation should be shown.

    Auto-explain triggers for:
    - Long queries (>100 chars)
    - Multi-part queries (OR, AND with complex structure)
    - Slow execution (>2 seconds)
    - Multiple backends selected
    - Low result count (possible failed search)

    Args:
        query: The search query text
        execution_time_ms: Query execution time in milliseconds
        backend_count: Number of backends used
        result_count: Number of results returned (None to skip this check)

    Returns:
        True if explanation should be shown
    """
    complexity_indicators = [
        len(query) > 100,
        " OR " in query.upper(),
        " AND " in query.upper() and len(query.split()) > 5,
        query.count("?") > 1,
        len(re.findall("\\([^)]+\\)", query)) > 1,
    ]
    execution_indicators = [execution_time_ms > 2000, backend_count > 2]
    if result_count is not None:
        execution_indicators.append(result_count == 0)
    return any(complexity_indicators) or any(execution_indicators)


def should_enable_session() -> bool:
    """Determine if session context should be enabled.

    Auto-enables in terminal mode (WT_SESSION detected).
    Disables for script/programmatic usage.

    Returns:
        True if session should be enabled
    """
    return bool(os.getenv("WT_SESSION"))


def should_cluster(
    results: list[dict[str, Any]], min_results: int = 10, min_source_diversity: int = 2
) -> bool:
    """Determine if results should be clustered.

    Auto-clusters when:
    - Enough results (>= min_results)
    - Diverse sources (>= min_source_diversity different sources)

    Args:
        results: List of search result dictionaries
        min_results: Minimum results for clustering
        min_source_diversity: Minimum different sources required

    Returns:
        True if clustering should be applied
    """
    if len(results) < min_results:
        return False
    sources = set()
    for result in results:
        if source := result.get("source"):
            sources.add(source)
    return len(sources) >= min_source_diversity


def get_feature_config(
    query: str = "",
    execution_time_ms: float = 0,
    backend_count: int = 1,
    result_count: int | None = None,
    results: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Get intelligent feature configuration for a search operation.

    Args:
        query: The search query text
        execution_time_ms: Query execution time in milliseconds
        backend_count: Number of backends used
        result_count: Number of results returned
        results: List of search results (for clustering decision)

    Returns:
        Dict with feature activation flags and reasons
    """
    results = results or []
    explain = should_explain(query, execution_time_ms, backend_count, result_count)
    session = should_enable_session()
    cluster = should_cluster(results)
    reasons = {
        "explain": _explain_reason(query, execution_time_ms, backend_count, result_count)
        if explain
        else "Simple query (no explanation needed)",
        "session": _session_reason(),
        "cluster": _cluster_reason(results) if cluster else "Not enough diverse results",
    }
    return {"explain": explain, "session": session, "cluster": cluster, "reasons": reasons}


def _explain_reason(
    query: str, execution_time_ms: float, backend_count: int, result_count: int | None
) -> str:
    """Generate human-readable reason for explain decision."""
    if execution_time_ms > 2000:
        return f"Slow query ({execution_time_ms:.0f}ms)"
    if len(query) > 100:
        return f"Complex query ({len(query)} chars)"
    if " OR " in query.upper():
        return "Multi-part query (OR)"
    if backend_count > 2:
        return f"Multiple backends ({backend_count})"
    if result_count == 0:
        return "No results (explanation helpful)"
    return "Query complexity detected"


def _session_reason() -> str:
    """Generate human-readable reason for session decision."""
    if wt_session := os.getenv("WT_SESSION"):
        return f"Terminal mode (WT_SESSION: {wt_session[:8]}...)"
    return "Script/programmatic mode"


def _cluster_reason(results: list[dict[str, Any]]) -> str:
    """Generate human-readable reason for cluster decision."""
    if len(results) < 10:
        return f"Too few results ({len(results)} < 10)"
    sources = {r.get("source", "unknown") for r in results}
    if len(sources) < 2:
        return f"Low source diversity ({len(sources)} source)"
    return f"Diverse results ({len(results)} items, {len(sources)} sources)"


class IntelligentDefaults:
    """Configuration manager for intelligent defaults.

    Usage:
        config = IntelligentDefaults()
        if config.should_explain_query("my query"):
            # Show explanation
        if config.should_use_session():
            # Enable session context
    """

    def __init__(
        self,
        explain_threshold_ms: float = 2000,
        explain_query_length: int = 100,
        cluster_min_results: int = 10,
        cluster_min_sources: int = 2,
    ) -> None:
        """Initialize intelligent defaults configuration.

        Args:
            explain_threshold_ms: Execution time threshold for auto-explain
            explain_query_length: Query length threshold for auto-explain
            cluster_min_results: Minimum results for auto-clustering
            cluster_min_sources: Minimum sources for auto-clustering
        """
        self.explain_threshold_ms = explain_threshold_ms
        self.explain_query_length = explain_query_length
        self.cluster_min_results = cluster_min_results
        self.cluster_min_sources = cluster_min_sources

    def should_explain(
        self,
        query: str,
        execution_time_ms: float = 0,
        backend_count: int = 1,
        result_count: int | None = None,
    ) -> bool:
        """Check if explanation should be shown using custom thresholds."""
        complexity_indicators = [
            len(query) > self.explain_query_length,
            " OR " in query.upper(),
            " AND " in query.upper() and len(query.split()) > 5,
            query.count("?") > 1,
        ]
        execution_indicators = [execution_time_ms > self.explain_threshold_ms, backend_count > 2]
        if result_count is not None:
            execution_indicators.append(result_count == 0)
        return any(complexity_indicators) or any(execution_indicators)

    def should_use_session(self) -> bool:
        """Check if session context should be enabled."""
        return should_enable_session()

    def should_cluster(self, results: list[dict[str, Any]]) -> bool:
        """Check if results should be clustered."""
        return should_cluster(
            results,
            min_results=self.cluster_min_results,
            min_source_diversity=self.cluster_min_sources,
        )

    def get_config(
        self,
        query: str = "",
        execution_time_ms: float = 0,
        backend_count: int = 1,
        result_count: int = 0,
        results: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Get full feature configuration."""
        return get_feature_config(query, execution_time_ms, backend_count, result_count, results)
