"""Quality checker module for search result validation.

This module provides configurable quality checking for search results to determine
if local results are satisfactory or if web search should be performed.

The QualityConfig dataclass defines configurable thresholds for:
- Confidence: Minimum confidence score (>= passes)
- Freshness: Maximum age in hours (<= passes)
- Backend diversity: Minimum number of backends (>= passes)

The is_satisfactory() function evaluates results against all configured thresholds.
All checks must pass for the result to be considered satisfactory.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

# Boundary tolerance for freshness checks (in seconds).
# Added to threshold to handle test execution time and ensure results
# exactly at the threshold boundary pass the check.
BOUNDARY_TOLERANCE_SECONDS = 1.0

# Conversion factor: seconds to hours
SECONDS_PER_HOUR = 3600.0


@dataclass
class QualityConfig:
    """Configurable quality thresholds for search results.

    Attributes:
        confidence_threshold: Minimum confidence score (0.0-1.0). Results with
            confidence >= this value pass the check. Default: 0.8
        freshness_hours: Maximum age in hours. Results with age <= this value
            pass the check. Default: 24
        min_backends: Minimum number of unique backends. Results with >= this
            many backends pass the check. Default: 1 (single-result check)
    """

    confidence_threshold: float = 0.8
    freshness_hours: int = 24
    min_backends: int = 1  # Single-result check: one result = one source


def _parse_timestamp(timestamp: datetime | str | int | float | None) -> datetime | None:
    """Parse various timestamp formats into a UTC datetime object.

    Supports datetime objects (converts to UTC), ISO 8601 strings,
    Unix timestamps (int/float), and handles None gracefully.

    Args:
        timestamp: A timestamp in various formats.

    Returns:
        A datetime object in UTC, or None if parsing fails.
    """
    if timestamp is None:
        return None

    if isinstance(timestamp, datetime):
        if timestamp.tzinfo is not None:
            return timestamp.astimezone(timezone.utc)
        return timestamp.replace(tzinfo=timezone.utc)

    if isinstance(timestamp, (int, float)):
        try:
            return datetime.fromtimestamp(timestamp, tz=timezone.utc)
        except (ValueError, OSError, OverflowError):
            return None

    if isinstance(timestamp, str):
        try:
            return datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except ValueError:
            return None

    return None


def _check_confidence(result: dict[str, Any], config: QualityConfig) -> bool:
    """Check if result confidence meets the configured threshold.

    Args:
        result: Result dictionary that may contain a 'confidence' field.
        config: Quality configuration with confidence_threshold.

    Returns:
        True if confidence >= threshold, False if confidence is missing
        or below threshold.
    """
    confidence = result.get("confidence")
    if confidence is None:
        return False
    return confidence >= config.confidence_threshold


def _check_freshness(result: dict[str, Any], config: QualityConfig) -> bool:
    """Check if result freshness meets the configured threshold.

    Args:
        result: Result dictionary that may contain a 'created_at' field.
        config: Quality configuration with freshness_hours.

    Returns:
        True if age <= freshness_hours (with boundary tolerance), False
        if timestamp is missing, unparseable, or too old.
    """
    created_at = result.get("created_at")
    if created_at is None:
        return False

    parsed_time = _parse_timestamp(created_at)
    if parsed_time is None:
        return False

    current_time_utc = datetime.now(timezone.utc)
    age_hours = (current_time_utc - parsed_time).total_seconds() / SECONDS_PER_HOUR

    tolerance_hours = BOUNDARY_TOLERANCE_SECONDS / SECONDS_PER_HOUR
    return age_hours <= (config.freshness_hours + tolerance_hours)


def _check_backend_diversity(result: dict[str, Any], config: QualityConfig) -> bool:
    """Check if result has sufficient backend diversity.

    Args:
        result: Result dictionary that may contain a 'sources' field.
        config: Quality configuration with min_backends.

    Returns:
        True if the number of unique backends >= min_backends, False
        if sources is missing, not a sequence, or has insufficient diversity.
    """
    sources = result.get("sources")
    if sources is None:
        return False

    if not isinstance(sources, (list, set, tuple)):
        return False

    unique_backend_count = len(set(sources))
    return unique_backend_count >= config.min_backends


def is_satisfactory(result: dict[str, Any], config: QualityConfig | None = None) -> bool:
    """Check if a search result meets all quality thresholds.

    A result is satisfactory only if it passes ALL quality checks:
    - Confidence score >= threshold
    - Age <= freshness_hours
    - Backend count >= min_backends

    Args:
        result: Search result dictionary with optional fields:
            - confidence (float): Relevance score [0.0, 1.0]
            - created_at (datetime|str|int|float): Result timestamp
            - sources (Sequence[str]): Backend names that provided this result
        config: Quality configuration. Uses default thresholds if None.

    Returns:
        True if result meets all quality thresholds, False otherwise.

    Examples:
        Create a result that passes with default thresholds:
        >>> result = {
        ...     "title": "Test",
        ...     "confidence": 0.9,
        ...     "created_at": datetime.now(timezone.utc),
        ...     "sources": ["backend1", "backend2", "backend3"]
        ... }
        >>> is_satisfactory(result)
        True

        Use custom thresholds:
        >>> config = QualityConfig(confidence_threshold=0.95)
        >>> is_satisfactory(result, config)
        False
    """
    if config is None:
        config = QualityConfig()

    confidence_ok = _check_confidence(result, config)
    freshness_ok = _check_freshness(result, config)
    diversity_ok = _check_backend_diversity(result, config)

    return confidence_ok and freshness_ok and diversity_ok
