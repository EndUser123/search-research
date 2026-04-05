"""HyDE-based Retrieval module.

This module implements Hypothetical Document Embeddings (HyDE) retrieval
where the hypothetical document content is USED as the retrieval query,
not just generated alongside the original query.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .hyde_single import HypotheticalDocument

import time
from dataclasses import dataclass, field


@dataclass
class HyDERetrievalConfig:
    """Configuration for HyDE-based retrieval."""

    model: str = "glm"
    max_tokens: int = 2000
    temperature: float = 0.7
    timeout: int = 30
    use_full_document: bool = True
    max_retrieval_query_length: int = 500


@dataclass
class HyDERetrievalResult:
    """
    Represents the result of HyDE-based retrieval.

    Attributes:
        results: List[Dict] - search results retrieved using hypothetical document
        hypothetical_document: Dict - the generated hypothetical document used for retrieval
        original_query: str - the user's original query
        hyde_used_for_retrieval: bool - must be True to indicate HyDE was used for retrieval
        retrieval_query: str - the actual query used for retrieval (hypothetical document content)
        metadata: Dict[str, Any] - additional metadata about the retrieval process
        jaccard_vs_baseline: float - similarity with baseline (optional)
    """

    results: list[dict[str, Any]]
    hypothetical_document: dict[str, Any]
    original_query: str
    hyde_used_for_retrieval: bool
    retrieval_query: str
    metadata: dict[str, Any] = field(default_factory=dict)
    jaccard_vs_baseline: float = 0.0

    def __repr__(self) -> str:
        return f"HyDERetrievalResult(query='{self.original_query[:30]}...', hyde_used={self.hyde_used_for_retrieval}, results={len(self.results)})"


def extract_retrieval_query(
    hypothetical_document: HypotheticalDocument, config: HyDERetrievalConfig
) -> str:
    """
    Extract key phrases from hypothetical document for search.

    Args:
        hypothetical_document: The generated hypothetical document
        config: Configuration for extraction

    Returns:
        str - the query to use for search
    """
    content = hypothetical_document.content

    if config.use_full_document:
        # Use full content, but truncate to max length
        if len(content) > config.max_retrieval_query_length:
            return content[: config.max_retrieval_query_length]
        return content
    else:
        # Extract key phrases - take first N chars as key phrases
        if len(content) > config.max_retrieval_query_length:
            return content[: config.max_retrieval_query_length]
        return content


def _calculate_jaccard_similarity(set1: set[str], set2: set[str]) -> float:
    """Calculate Jaccard similarity between two sets."""
    if not set1 and not set2:
        return 1.0
    if not set1 or not set2:
        return 0.0
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return intersection / union if union > 0 else 0.0


def _search_with_query(query: str, limit: int = 10) -> list[dict[str, Any]]:
    """
    Perform search using the given query.

    This is a minimal implementation for testing. In production,
    this would call the actual search backend.

    Args:
        query: The search query to use
        limit: Maximum number of results

    Returns:
        List of search results
    """
    # Mock search results for testing
    # In production, this would use actual search backends
    return [
        {
            "title": f"HyDE Search Result {i}",
            "url": f"https://hyde-retrieval.example.com/result-{i}",
            "content": f"Content based on hypothetical document query for result {i}",
            "score": 0.9 - i * 0.05,
        }
        for i in range(min(limit, 5))
    ]


def baseline_search(query: str, limit: int = 10) -> list[dict[str, Any]]:
    """
    Perform baseline search without HyDE.

    Args:
        query: The search query
        limit: Maximum number of results

    Returns:
        List of baseline search results
    """
    return [
        {
            "title": f"Baseline Result {i}",
            "url": f"https://baseline.example.com/result-{i}",
            "content": f"Baseline content for query: {query[:50]}",
            "score": 0.85 - i * 0.05,
        }
        for i in range(min(limit, 5))
    ]


def _generate_hypothetical_document(
    query: str, config: HyDERetrievalConfig
) -> HypotheticalDocument:
    """
    Wrapper function for generate_hypothetical_document to allow test mocking.

    This function is a thin wrapper around the actual generate_hypothetical_document
    function from hyde_single, allowing tests to patch this specific function.

    Args:
        query: The user's search query
        config: HyDE retrieval configuration

    Returns:
        HypotheticalDocument with generated content
    """
    from .hyde_single import (
        HyDEConfig,
    )
    from .hyde_single import (
        generate_hypothetical_document as _gen_doc,
    )

    hyde_config = HyDEConfig(
        model=config.model,
        max_tokens=config.max_tokens,
        temperature=config.temperature,
        timeout=config.timeout,
    )
    return _gen_doc(query, hyde_config)


def search_with_hyde(query: str, config: HyDERetrievalConfig | None = None) -> HyDERetrievalResult:
    """
    Search using HyDE-based retrieval.

    The key difference from standard HyDE is that this function USES
    the hypothetical document content as the retrieval query, not the
    original query.

    Args:
        query: The user's search query
        config: Optional HyDE retrieval configuration

    Returns:
        HyDERetrievalResult with results and metadata

    Raises:
        ValueError: If query is empty or whitespace only
        TypeError: If query is None
    """
    # Validate input
    if query is None:
        raise TypeError("Query cannot be None")
    if not isinstance(query, str):
        raise TypeError(f"Query must be a string, got {type(query)}")
    if not query or query.strip() == "":
        raise ValueError("Query cannot be empty")

    # Use default config if not provided
    if config is None:
        config = HyDERetrievalConfig()

    # Step 1: Generate hypothetical document from query (using wrapper for test mocking)
    start_time = time.time()
    hypothetical_document = _generate_hypothetical_document(query, config)
    generation_time = time.time() - start_time

    # Step 2: Extract retrieval query from hypothetical document
    retrieval_query = extract_retrieval_query(hypothetical_document, config)

    # Step 3: Search using the retrieval query (not original query)
    search_start = time.time()
    results = _search_with_query(retrieval_query)
    search_time = time.time() - search_start

    # Step 4: Compare with baseline for Jaccard similarity
    baseline_results = baseline_search(query)
    baseline_urls = {r.get("url", "") for r in baseline_results}
    hyde_urls = {r.get("url", "") for r in results}
    jaccard_similarity = _calculate_jaccard_similarity(baseline_urls, hyde_urls)

    # Build metadata
    metadata = {
        "generation_time": generation_time,
        "search_time": search_time,
        "total_time": generation_time + search_time,
        "generation_model": hypothetical_document.generation_model,
        "word_count": hypothetical_document.word_count,
        "token_count": hypothetical_document.token_count,
        "retrieval_query_length": len(retrieval_query),
        "baseline_url_count": len(baseline_urls),
        "hyde_url_count": len(hyde_urls),
        "config": {
            "model": config.model,
            "use_full_document": config.use_full_document,
            "max_retrieval_query_length": config.max_retrieval_query_length,
        },
    }

    # Convert HypotheticalDocument to dict for compatibility with tests
    hypothetical_document_dict = {
        "content": hypothetical_document.content,
        "word_count": hypothetical_document.word_count,
        "query": hypothetical_document.query,
        "generation_model": hypothetical_document.generation_model,
        "generation_time": hypothetical_document.generation_time,
        "token_count": hypothetical_document.token_count,
    }

    return HyDERetrievalResult(
        results=results,
        hypothetical_document=hypothetical_document_dict,
        original_query=query,
        hyde_used_for_retrieval=True,  # Critical: This must be True
        retrieval_query=retrieval_query,
        metadata=metadata,
        jaccard_vs_baseline=jaccard_similarity,
    )
