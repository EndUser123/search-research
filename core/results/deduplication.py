"""Deduplication processor for search results.

Migrated from research_skill.processors.deduplication (2025-03-08).
"""

from collections import defaultdict


def _jaccard_similarity(text1: str, text2: str) -> float:
    """Calculate Jaccard similarity between two texts.

    Args:
        text1: First text string.
        text2: Second text string.

    Returns:
        Similarity score between 0 and 1.
    """
    if not text1 or not text2:
        return 0.0

    # Tokenize by words
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())

    if not words1 or not words2:
        return 0.0

    intersection = len(words1 & words2)
    union = len(words1 | words2)

    return intersection / union if union > 0 else 0.0


def _normalize_url(url: str) -> str:
    """Normalize URL for comparison.

    Handles case-insensitivity and trailing slashes.

    Args:
        url: URL to normalize.

    Returns:
        Normalized URL string.
    """
    if not url:
        return ""
    # Convert to lowercase
    url = url.lower()
    # Remove trailing slash
    url = url.rstrip("/")
    return url


class DeduplicationProcessor:
    """Processor for deduplicating search results.

    Removes duplicate results based on URL, title, and content similarity.
    """

    def __init__(
        self,
        similarity_threshold: float = 0.6,
        normalize_urls: bool = True,
    ):
        """Initialize the deduplication processor.

        Args:
            similarity_threshold: Jaccard similarity threshold for content dedup (0-1).
            normalize_urls: Whether to normalize URLs for comparison.
        """
        self.similarity_threshold = similarity_threshold
        self.normalize_urls = normalize_urls

    def deduplicate_by_url(
        self,
        results: list,
        aggregate_sources: bool = False,
    ) -> list:
        """Deduplicate results by URL.

        Keeps the result with the highest score for each URL.

        Args:
            results: List of search results.
            aggregate_sources: Whether to aggregate sources from duplicates.

        Returns:
            Deduplicated list of results.
        """
        if not results:
            return []

        # Group by URL
        url_groups = defaultdict(list)
        for result in results:
            url = _normalize_url(result.url) if self.normalize_urls else result.url
            url_groups[url].append(result)

        # Keep the best result for each URL
        deduped = []
        for group in url_groups.values():
            # Sort by score descending
            group.sort(key=lambda x: x.score, reverse=True)
            best = group[0]

            # Aggregate sources if requested
            if aggregate_sources and len(group) > 1:
                # Create a copy to avoid modifying original
                if not hasattr(best, '_metadata_copy'):
                    best.metadata = best.metadata.copy()
                sources = best.metadata.get("sources", [])
                if isinstance(sources, list):
                    for other in group[1:]:
                        other_source = other.source
                        if other_source not in sources:
                            sources.append(other_source)
                    best.metadata["sources"] = sources

            deduped.append(best)

        return deduped

    def deduplicate_by_title(self, results: list) -> list:
        """Deduplicate results by title.

        Keeps the result with the highest score for each title.

        Args:
            results: List of search results.

        Returns:
            Deduplicated list of results.
        """
        if not results:
            return []

        # Group by title
        title_groups = defaultdict(list)
        for result in results:
            title = result.title
            title_groups[title].append(result)

        # Keep the best result for each title
        deduped = []
        for group in title_groups.values():
            group.sort(key=lambda x: x.score, reverse=True)
            deduped.append(group[0])

        return deduped

    def deduplicate_by_content(self, results: list) -> list:
        """Deduplicate results by content similarity.

        Uses Jaccard similarity to find and remove similar content.

        Args:
            results: List of search results.

        Returns:
            Deduplicated list of results.
        """
        if not results:
            return []

        # Sort by score descending first
        sorted_results = sorted(results, key=lambda x: x.score, reverse=True)

        deduped = []
        for result in sorted_results:
            is_duplicate = False

            # Check against already selected results
            for kept in deduped:
                similarity = _jaccard_similarity(result.content, kept.content)
                if similarity >= self.similarity_threshold:
                    is_duplicate = True
                    break

            if not is_duplicate:
                deduped.append(result)

        return deduped

    def deduplicate(self, results: list) -> list:
        """Deduplicate using all strategies.

        Applies URL, title, and content deduplication in sequence.

        Args:
            results: List of search results.

        Returns:
            Deduplicated list of results.
        """
        if not results:
            return []

        # Step 1: Deduplicate by URL (most specific)
        result = self.deduplicate_by_url(results)

        # Step 2: Deduplicate by title
        result = self.deduplicate_by_title(result)

        # Step 3: Deduplicate by content similarity
        result = self.deduplicate_by_content(result)

        return result
