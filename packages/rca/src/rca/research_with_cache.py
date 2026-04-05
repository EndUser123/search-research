"""
Unified Research with Cache Integration

Combines auto-research triggering with library docs caching.
This is the main entry point for the /debug workflow.

Usage:
    from rca.research_with_cache import research_library_docs

    result = research_library_docs("yt-dlp AttributeError")
    if result.needs_research:
        docs = result.get_docs()  # From cache or fetch
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

# Use conditional imports for script vs module usage
try:
    from .auto_research import (
        ResearchTrigger,
        build_research_query,
        should_trigger_research,
    )
    from .library_docs_cache import get_library_cache
except ImportError:
    # Running as script
    from rca.auto_research import (
        ResearchTrigger,
        build_research_query,
        should_trigger_research,
    )
    from rca.library_docs_cache import get_library_cache

logger = logging.getLogger(__name__)


@dataclass
class ResearchResult:
    """Result of library research check and potential fetch."""

    needs_research: bool
    trigger: ResearchTrigger
    cached_doc: str | None = None
    query: str = ""

    def get_cached_content(self) -> str | None:
        """Get cached documentation if available."""
        return self.cached_doc

    def is_fresh_cached(self) -> bool:
        """Check if we have fresh cached content."""
        return self.cached_doc is not None


def research_library_docs(
    problem_description: str,
    force_research: bool = False,
    max_cache_age_hours: float = 24,
) -> ResearchResult:
    """
    Check if research is needed and return cached docs if available.

    This is the main entry point for /debug's auto-research feature.

    Args:
        problem_description: The error or problem description
        force_research: Skip cache, force research trigger
        max_cache_age_hours: Hours before considering cache stale

    Returns:
        ResearchResult with trigger info and cached docs if available

    Example usage in /debug:
        ```python
        from rca.research_with_cache import research_library_docs

        result = research_library_docs(problem_description)

        if result.needs_research:
            cached = result.get_cached_content()
            if cached:
                # Use cached docs
                research_context = f"Cached: {cached[:500]}..."
            else:
                # Need to fetch fresh docs
                query = result.query
                search_results = WebSearch(query)
                docs = WebFetch([r["url"] for r in search_results[:3]])
        ```

    """
    # Step 1: Check if research is needed
    trigger = should_trigger_research(problem_description)

    # Override if forced
    if force_research:
        trigger.should_research = True

    if not trigger.should_research:
        return ResearchResult(
            needs_research=False,
            trigger=trigger,
        )

    # Step 2: Check cache for fresh docs
    cache = get_library_cache(max_age_hours=max_cache_age_hours)

    for lib in trigger.libraries:
        cached_doc = cache.get(lib)
        if cached_doc:
            logger.info("Cache HIT for %s: %.1fh old", lib, cached_doc.age_hours)
            return ResearchResult(
                needs_research=False,  # Cached, so no immediate research needed
                trigger=trigger,
                cached_doc=cached_doc.content,
            )

    # Step 3: Build query for research
    query = build_research_query(trigger.libraries, problem_description)

    return ResearchResult(
        needs_research=True,
        trigger=trigger,
        query=query,
    )


def store_research_result(
    library: str,
    content: str,
    sources: list[str],
    version: str = "",
) -> bool:
    """
    Store research result in cache.

    Call this after fetching docs from WebSearch/WebFetch.

    Args:
        library: Library name
        content: Documentation content
        sources: Source URLs
        version: Optional version info

    Returns:
        True if stored successfully

    Example usage:
        ```python
        search_results = WebSearch(query)
        docs = WebFetch([r["url"] for r in search_results[:3]])

        # Store in cache
        store_research_result(
            library="yt-dlp",
            content=docs,
            sources=[r["url"] for r in search_results[:3]],
        )
        ```

    """
    cache = get_library_cache()
    return cache.set(library, content, sources, version)


def get_cache_stats() -> dict:
    """
    Get cache statistics for debugging.

    Returns:
        Dict with cache stats

    """
    cache = get_library_cache()
    return cache.get_stats()


def clear_stale_cache() -> int:
    """
    Remove stale entries from cache.

    Returns:
        Number of entries removed

    """
    cache = get_library_cache()
    return cache.clear_stale()


# CLI test function
def _test() -> None:
    """Run built-in tests."""

    print("Research with Cache Tests")
    print("=" * 60)

    # Test 1: No research needed (internal code)
    result = research_library_docs("my_function returns None")
    print(f"Test 1 - Internal code: {'PASS' if not result.needs_research else 'FAIL'}")

    # Test 2: Research needed (fastapi - different lib)
    result = research_library_docs("fastapi import error")
    print(f"Test 2 - Research needed: {'PASS' if result.needs_research else 'FAIL'}")
    print(f"        Query: {result.query}")

    # Test 3: Store and retrieve from cache
    # Use yt-dlp which is a known fast-moving library
    store_research_result(
        "yt-dlp",
        "Yt-dlp documentation: options and download formats",
        ["https://github.com/yt-dlp/yt-dlp"],
        version="2024.12",
    )

    result = research_library_docs("yt-dlp option not found")
    print(f"Test 3 - Cache HIT: {'PASS' if result.cached_doc else 'FAIL'}")

    # Test 4: Cache stats
    stats = get_cache_stats()
    print(f"Test 4 - Cache stats: {stats['total_entries']} entries")

    # Test 5: Clear stale
    cleared = clear_stale_cache()
    print(f"Test 5 - Clear stale: {cleared} removed")


if __name__ == "__main__":
    _test()
