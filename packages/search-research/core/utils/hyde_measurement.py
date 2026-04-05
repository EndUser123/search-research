"""HyDE (Hypothetical Document Embeddings) effectiveness measurement framework.

This module provides tools to track and measure HyDE effectiveness including:
- Query enhancement rate
- Result quality improvement
- Latency impact

HYDE-M-001: Measurement Data Class
HyDEMeasurement data class stores all metrics from HyDE enhancement.

HYDE-M-002: Effectiveness Measurement
measure_hyde_effectiveness() tracks HyDE application with latency.

HYDE-M-003: Metrics Tracking
track_hyde_metrics() aggregates metrics with search results.
"""

import time
from dataclasses import dataclass
from typing import Any

from ..hyde import apply_hyde, extract_key_phrases


@dataclass
class HyDEMeasurement:
    """Measurement data for HyDE effectiveness tracking.

    Attributes:
        original_query: Original search query before enhancement
        enhanced_query: Enhanced query after HyDE processing
        hyde_applied: Whether HyDE enhancement was applied
        enhancement_latency_ms: Time taken for enhancement in milliseconds
        result_count: Number of search results returned
        key_phrases_extracted: Number of key phrases extracted (optional)
        quality_score: Quality score of results (optional)
    """

    original_query: str
    enhanced_query: str
    hyde_applied: bool
    enhancement_latency_ms: float
    result_count: int
    key_phrases_extracted: int | None = None
    quality_score: float | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert measurement to dictionary.

        Returns:
            Dictionary containing all measurement fields
        """
        return {
            "original_query": self.original_query,
            "enhanced_query": self.enhanced_query,
            "hyde_applied": self.hyde_applied,
            "enhancement_latency_ms": self.enhancement_latency_ms,
            "result_count": self.result_count,
            "key_phrases_extracted": self.key_phrases_extracted,
            "quality_score": self.quality_score,
        }


def measure_hyde_effectiveness(
    query: str, hyde_content: str | None = None
) -> HyDEMeasurement:
    """Measure HyDE effectiveness for a query.

    HYDE-M-002: Tracks HyDE enhancement with latency measurement.

    Args:
        query: Original search query
        hyde_content: Pre-generated hypothetical document content

    Returns:
        HyDEMeasurement with enhancement metrics

    Examples:
        >>> measurement = measure_hyde_effectiveness("FastAPI patterns", "Some content")
        >>> measurement.hyde_applied
        True
    """
    start_time = time.perf_counter()

    try:
        enhanced_query, hyde_applied = apply_hyde(query, hyde_content)
        key_phrases_count = None
        if hyde_applied and hyde_content:
            try:
                key_phrases = extract_key_phrases(hyde_content)
                key_phrases_count = len(key_phrases)
            except Exception:
                key_phrases_count = None
    except Exception:
        # If HyDE fails, return original query
        enhanced_query = query
        hyde_applied = False
        key_phrases_count = None

    end_time = time.perf_counter()
    latency_ms = (end_time - start_time) * 1000

    return HyDEMeasurement(
        original_query=query,
        enhanced_query=enhanced_query,
        hyde_applied=hyde_applied,
        enhancement_latency_ms=latency_ms,
        result_count=0,  # Will be updated when results are available
        key_phrases_extracted=key_phrases_count,
    )


def track_hyde_metrics(
    measurement: HyDEMeasurement, results: list[Any]
) -> dict[str, Any]:
    """Track HyDE metrics with search results.

    HYDE-M-003: Aggregates HyDE metrics with search result quality scores.

    Args:
        measurement: HyDE measurement data
        results: List of search results with score attribute

    Returns:
        Dictionary containing all tracked metrics

    Examples:
        >>> metrics = track_hyde_metrics(measurement, results)
        >>> metrics["average_score"]
        0.85
    """
    # Calculate average score from results
    average_score = 0.0
    if results:
        scores = [getattr(r, "score", 0.0) for r in results]
        average_score = sum(scores) / len(scores) if scores else 0.0

    # Build metrics dictionary
    metrics = {
        "original_query": measurement.original_query,
        "enhanced_query": measurement.enhanced_query,
        "hyde_applied": measurement.hyde_applied,
        "enhancement_latency_ms": measurement.enhancement_latency_ms,
        "result_count": len(results),
        "key_phrases_extracted": measurement.key_phrases_extracted,
        "quality_score": measurement.quality_score,
        "average_score": average_score,
    }

    return metrics
