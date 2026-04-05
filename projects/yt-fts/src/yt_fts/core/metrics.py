"""
Search metrics/telemetry tracking for yt-fts.

This module provides the SearchMetrics class for collecting, persisting,
and analyzing search usage data including query patterns, backend performance,
and citation rates.
"""
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class SearchMetrics:
    """Collect and manage search usage metrics and telemetry."""

    def __init__(self, metrics_path: Path | str | None = None) -> None:
        """
        Initialize SearchMetrics with a file path for persistence.

        Args:
            metrics_path: Path to metrics JSON file. If None, uses data/search_metrics.json
        """
        if metrics_path is None:
            # Default to data/search_metrics.json in project root
            self.metrics_path = Path("data/search_metrics.json")
        else:
            self.metrics_path = Path(metrics_path)

        # Initialize data structure
        self.data: dict[str, Any] = {
            "searches": [],
            "aggregations": {
                "total_searches": 0,
                "fts_searches": 0,
                "vector_searches": 0,
                "total_results": 0,
                "citations": 0,
            },
        }

        # Load existing data if file exists
        if self.metrics_path.exists():
            self.load()

    def track_search(
        self,
        query: str,
        scope: str,
        result_count: int,
        backend: str,
        duration_ms: int,
        video_id: str | None = None,
        channel_id: str | None = None,
        has_citation: bool = False,
    ) -> None:
        """
        Track a single search operation.

        Args:
            query: Search query string
            scope: Search scope (all, channel, video)
            result_count: Number of results returned
            backend: Search backend (fts, vector)
            duration_ms: Search duration in milliseconds
            video_id: Video ID if video-scoped search
            channel_id: Channel ID if channel-scoped search
            has_citation: Whether results include citations
        """
        timestamp = datetime.now(timezone.utc).isoformat()

        search_entry = {
            "timestamp": timestamp,
            "query": query,
            "scope": scope,
            "result_count": result_count,
            "backend": backend,
            "duration_ms": duration_ms,
        }

        # Add optional fields
        if video_id:
            search_entry["video_id"] = video_id
        if channel_id:
            search_entry["channel_id"] = channel_id
        if has_citation:
            search_entry["has_citation"] = True

        # Add to searches list
        self.data["searches"].append(search_entry)

        # Update aggregations
        self.data["aggregations"]["total_searches"] += 1
        self.data["aggregations"]["total_results"] += result_count

        if backend == "fts":
            self.data["aggregations"]["fts_searches"] += 1
        elif backend == "vector":
            self.data["aggregations"]["vector_searches"] += 1

        if has_citation:
            self.data["aggregations"]["citations"] += 1

    def get_query_patterns(self) -> dict[str, int]:
        """
        Analyze query patterns from all searches.

        Returns:
            Dictionary with pattern counts (wildcard, or_operator, phrase_search, etc.)
        """
        patterns = {
            "wildcard": 0,
            "or_operator": 0,
            "phrase_search": 0,
        }

        for search in self.data["searches"]:
            query = search.get("query", "")

            if "*" in query:
                patterns["wildcard"] += 1
            if " OR " in query.upper():
                patterns["or_operator"] += 1
            if query.startswith('"') and query.endswith('"'):
                patterns["phrase_search"] += 1

        return patterns

    def get_query_length_distribution(self) -> dict[str, int]:
        """
        Analyze query length distribution.

        Returns:
            Dictionary with length categories (short, medium, long)
        """
        distribution = {"short": 0, "medium": 0, "long": 0}

        for search in self.data["searches"]:
            query_length = len(search.get("query", ""))

            if query_length < 10:
                distribution["short"] += 1
            elif query_length < 30:
                distribution["medium"] += 1
            else:
                distribution["long"] += 1

        return distribution

    def get_backend_performance(self, backend: str) -> dict[str, float]:
        """
        Get performance statistics for a specific backend.

        Args:
            backend: Backend type (fts or vector)

        Returns:
            Dictionary with performance stats (count, avg_duration_ms, min/max, avg_results)
        """
        backend_searches = [
            s for s in self.data["searches"] if s.get("backend") == backend
        ]

        if not backend_searches:
            return {
                "count": 0,
                "avg_duration_ms": 0,
                "min_duration_ms": 0,
                "max_duration_ms": 0,
                "avg_results": 0,
            }

        durations = [s.get("duration_ms", 0) for s in backend_searches]
        result_counts = [s.get("result_count", 0) for s in backend_searches]

        return {
            "count": len(backend_searches),
            "avg_duration_ms": sum(durations) / len(durations),
            "min_duration_ms": min(durations),
            "max_duration_ms": max(durations),
            "avg_results": sum(result_counts) / len(result_counts),
        }

    def get_citation_rate(self) -> dict[str, Any]:
        """
        Calculate citation rate across all searches.

        Returns:
            Dictionary with citation statistics
        """
        total_searches = len(self.data["searches"])
        with_citations = sum(
            1 for s in self.data["searches"] if s.get("has_citation", False)
        )

        citation_rate = (
            with_citations / total_searches if total_searches > 0 else 0
        )

        return {
            "with_citations": with_citations,
            "total_searches": total_searches,
            "citation_rate": citation_rate,
        }

    def get_stats(self) -> dict[str, Any]:
        """
        Get overall statistics.

        Returns:
            Dictionary with overall search statistics
        """
        aggregations = self.data["aggregations"]
        total_searches = aggregations["total_searches"]

        avg_results = (
            aggregations["total_results"] / total_searches
            if total_searches > 0
            else 0
        )

        return {
            "total_searches": total_searches,
            "fts_searches": aggregations["fts_searches"],
            "vector_searches": aggregations["vector_searches"],
            "total_results": aggregations["total_results"],
            "avg_results": avg_results,
        }

    def get_top_queries(self, limit: int = 10) -> list[dict[str, Any]]:
        """
        Get most frequently used queries.

        Args:
            limit: Maximum number of queries to return

        Returns:
            List of dicts with query and count
        """
        query_counter = Counter(
            s.get("query", "") for s in self.data["searches"]
        )

        return [
            {"query": query, "count": count}
            for query, count in query_counter.most_common(limit)
        ]

    def get_scope_distribution(self) -> dict[str, int]:
        """
        Get distribution of search scopes.

        Returns:
            Dictionary with scope counts (all, channel, video)
        """
        scopes = Counter(s.get("scope", "") for s in self.data["searches"])

        return dict(scopes)

    def save(self) -> None:
        """
        Save metrics data to file.

        Creates parent directories if they don't exist.
        """
        # Ensure parent directory exists
        self.metrics_path.parent.mkdir(parents=True, exist_ok=True)

        # Write to file
        with self.metrics_path.open("w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    def load(self) -> None:
        """Load metrics data from file."""
        if not self.metrics_path.exists():
            return

        try:
            with self.metrics_path.open("r", encoding="utf-8") as f:
                loaded_data = json.load(f)

            # Merge loaded data with current structure
            self.data["searches"] = loaded_data.get("searches", [])
            self.data["aggregations"].update(
                loaded_data.get("aggregations", {})
            )
        except (OSError, json.JSONDecodeError):
            # If file is corrupted, start fresh
            self.data = {
                "searches": [],
                "aggregations": {
                    "total_searches": 0,
                    "fts_searches": 0,
                    "vector_searches": 0,
                    "total_results": 0,
                    "citations": 0,
                },
            }

    def display(self) -> str:
        """
        Generate a formatted display of metrics.

        Returns:
            Formatted string with metrics summary
        """
        stats = self.get_stats()
        patterns = self.get_query_patterns()
        fts_perf = self.get_backend_performance("fts")
        vector_perf = self.get_backend_performance("vector")
        citation_info = self.get_citation_rate()
        scope_dist = self.get_scope_distribution()

        lines = [
            "=" * 60,
            "Search Metrics Summary",
            "=" * 60,
            "",
            "Overall Statistics:",
            f"  Total Searches: {stats['total_searches']}",
            f"  FTS Searches: {stats['fts_searches']}",
            f"  Vector Searches: {stats['vector_searches']}",
            f"  Total Results: {stats['total_results']}",
            f"  Average Results: {stats['avg_results']:.2f}",
            "",
            "Query Patterns:",
            f"  Wildcard queries: {patterns['wildcard']}",
            f"  OR operator: {patterns['or_operator']}",
            f"  Phrase searches: {patterns['phrase_search']}",
            "",
            "Backend Performance:",
            f"  FTS - Avg: {fts_perf['avg_duration_ms']:.2f}ms "
            f"(min: {fts_perf['min_duration_ms']}ms, "
            f"max: {fts_perf['max_duration_ms']}ms)",
            f"  Vector - Avg: {vector_perf['avg_duration_ms']:.2f}ms "
            f"(min: {vector_perf['min_duration_ms']}ms, "
            f"max: {vector_perf['max_duration_ms']}ms)",
            "",
            "Scope Distribution:",
        ]

        for scope, count in sorted(scope_dist.items()):
            lines.append(f"  {scope}: {count}")

        lines.extend([
            "",
            "Citations:",
            f"  Searches with citations: {citation_info['with_citations']}",
            f"  Citation rate: {citation_info['citation_rate']:.2%}",
            "",
            "=" * 60,
        ])

        return "\n".join(lines)
