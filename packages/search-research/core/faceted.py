"""Faceted search filtering for search results.

Provides filtering capabilities by source, type, date, and other dimensions.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


def filter_results(
    results: list[Any],
    sources: list[str] | None = None,
    types: list[str] | None = None,
    after: datetime | None = None,
    before: datetime | None = None,
    min_score: float | None = None,
    custom_filter: callable | None = None,
    file_paths: list[str] | None = None,
    categories: list[str] | None = None,
    skill_sources: list[str] | None = None,
) -> list[Any]:
    """Filter search results based on multiple facets.

    Args:
        results: List of SearchResult or dict results
        sources: Filter by source (CKS, CODE, CHS, etc.)
        types: Filter by type (memory, pattern, code, etc.)
        after: Filter for results after this date
        before: Filter for results before this date
        min_score: Filter by minimum score
        custom_filter: Optional custom filter function
        file_paths: Filter by file_path metadata (Per-File Learning Tracking)
        categories: Filter by category metadata (BUG, FIX, PATTERN, etc.)
        skill_sources: Filter by skill_source metadata (rca, debug, tdd, etc.)

    Returns:
        Filtered list of results
    """
    if not results:
        return results

    filtered = results

    # Filter by source
    if sources:
        filtered = _filter_by_source(filtered, sources)

    # Filter by type
    if types:
        filtered = _filter_by_type(filtered, types)

    # Filter by date range
    if after or before:
        filtered = _filter_by_date(filtered, after, before)

    # Filter by score
    if min_score is not None:
        filtered = _filter_by_score(filtered, min_score)

    # Filter by file_path metadata
    if file_paths:
        filtered = _filter_by_file_path(filtered, file_paths)

    # Filter by category metadata
    if categories:
        filtered = _filter_by_category(filtered, categories)

    # Filter by skill_source metadata
    if skill_sources:
        filtered = _filter_by_skill_source(filtered, skill_sources)

    # Custom filter
    if custom_filter:
        filtered = [r for r in filtered if custom_filter(r)]

    return filtered


def _filter_by_source(results: list[Any], sources: list[str]) -> list[Any]:
    """Filter results by source.

    Args:
        results: List of SearchResult or dict
        sources: Allowed sources

    Returns:
        Filtered results
    """
    sources_upper = [s.upper() for s in sources]

    filtered = []
    for result in results:
        # Handle both SearchResult and dict
        if hasattr(result, 'source'):
            source = result.source.upper()
        else:
            source = result.get('source', '').upper()

        if source in sources_upper:
            filtered.append(result)

    return filtered


def _filter_by_type(results: list[Any], types: list[str]) -> list[Any]:
    """Filter results by type.

    Args:
        results: List of SearchResult or dict
        types: Allowed types

    Returns:
        Filtered results
    """
    types_lower = [t.lower() for t in types]

    filtered = []
    for result in results:
        # Get type from metadata or attribute
        result_type = None

        if hasattr(result, 'metadata'):
            result_type = result.metadata.get('type')
        elif isinstance(result, dict):
            result_type = result.get('metadata', {}).get('type')

        if result_type and result_type.lower() in types_lower:
            filtered.append(result)

    return filtered


def _filter_by_date(
    results: list[Any],
    after: datetime | None = None,
    before: datetime | None = None,
) -> list[Any]:
    """Filter results by date range.

    Args:
        results: List of SearchResult or dict
        after: Include only results after this date
        before: Include only results before this date

    Returns:
        Filtered results
    """
    filtered = []

    for result in results:
        # Get date from various possible fields
        result_date = None

        if hasattr(result, 'metadata'):
            result_date = result.metadata.get('date') or result.metadata.get('created_at') or result.metadata.get('timestamp')
        elif isinstance(result, dict):
            metadata = result.get('metadata', {})
            result_date = metadata.get('date') or metadata.get('created_at') or metadata.get('timestamp')

        # Skip if no date
        if not result_date:
            continue

        # Convert string to datetime if needed
        if isinstance(result_date, str):
            try:
                result_date = datetime.fromisoformat(result_date.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                continue

        # Check date range
        if after and result_date < after:
            continue
        if before and result_date > before:
            continue

        filtered.append(result)

    return filtered


def _filter_by_score(results: list[Any], min_score: float) -> list[Any]:
    """Filter results by minimum score.

    Args:
        results: List of SearchResult or dict
        min_score: Minimum score threshold

    Returns:
        Filtered results
    """
    filtered = []

    for result in results:
        # Get score
        if hasattr(result, 'score'):
            score = result.score
        elif isinstance(result, dict):
            score = result.get('score', 0.0)
        else:
            score = 0.0

        if score >= min_score:
            filtered.append(result)

    return filtered


def _filter_by_file_path(results: list[Any], file_paths: list[str]) -> list[Any]:
    """Filter results by file_path metadata.

    Args:
        results: List of SearchResult or dict
        file_paths: Allowed file paths (supports partial matching)

    Returns:
        Filtered results matching file_path metadata
    """
    filtered = []
    file_paths_lower = [f.lower() for f in file_paths]

    for result in results:
        # Get file_path from metadata
        file_path = None
        if hasattr(result, 'metadata'):
            file_path = result.metadata.get('file_path')
        elif isinstance(result, dict):
            metadata = result.get('metadata', {})
            file_path = metadata.get('file_path')

        # Check if file_path matches any in filter list (supports partial matching)
        if file_path:
            file_path_lower = file_path.lower()
            # Exact match or partial match (e.g., "contract_api.py" matches "src/api/contract_api.py")
            if any(fp in file_path_lower or file_path_lower in fp for fp in file_paths_lower):
                filtered.append(result)

    return filtered


def _filter_by_category(results: list[Any], categories: list[str]) -> list[Any]:
    """Filter results by category metadata.

    Args:
        results: List of SearchResult or dict
        categories: Allowed categories (BUG, FIX, PATTERN, VULNERABILITY, etc.)

    Returns:
        Filtered results matching category metadata
    """
    filtered = []
    categories_upper = [c.upper() for c in categories]

    for result in results:
        # Get category from metadata
        category = None
        if hasattr(result, 'metadata'):
            category = result.metadata.get('category')
        elif isinstance(result, dict):
            metadata = result.get('metadata', {})
            category = metadata.get('category')

        # Check if category matches (case-insensitive)
        if category and category.upper() in categories_upper:
            filtered.append(result)

    return filtered


def _filter_by_skill_source(results: list[Any], skill_sources: list[str]) -> list[Any]:
    """Filter results by skill_source metadata.

    Args:
        results: List of SearchResult or dict
        skill_sources: Allowed skill sources (rca, debug, tdd, arch, security, etc.)

    Returns:
        Filtered results matching skill_source metadata
    """
    filtered = []
    skill_sources_lower = [s.lower() for s in skill_sources]

    for result in results:
        # Get skill_source from metadata
        skill_source = None
        if hasattr(result, 'metadata'):
            skill_source = result.metadata.get('skill_source')
        elif isinstance(result, dict):
            metadata = result.get('metadata', {})
            skill_source = metadata.get('skill_source')

        # Check if skill_source matches (case-insensitive)
        if skill_source and skill_source.lower() in skill_sources_lower:
            filtered.append(result)

    return filtered


def get_facets(results: list[Any]) -> dict[str, dict[str, int]]:
    """Get facet counts from results.

    Args:
        results: List of SearchResult or dict

    Returns:
        Dictionary with facet counts for sources, types, etc.
    """
    facets = {
        "sources": {},
        "types": {},
    }

    for result in results:
        # Count sources
        if hasattr(result, 'source'):
            source = result.source
        else:
            source = result.get('source', 'UNKNOWN')

        facets["sources"][source] = facets["sources"].get(source, 0) + 1

        # Count types
        result_type = None
        if hasattr(result, 'metadata'):
            result_type = result.metadata.get('type')
        elif isinstance(result, dict):
            result_type = result.get('metadata', {}).get('type')

        if result_type:
            facets["types"][result_type] = facets["types"].get(result_type, 0) + 1

    return facets
