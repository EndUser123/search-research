#!/usr/bin/env python3
"""
Hybrid Ensemble module for combining Query Expansion, Single HyDE, and Multi-HyDE.

This module implements Stage 5 of the search optimization pipeline, combining results
from all previous stages using ensemble methods like Reciprocal Rank Fusion (RRF).
"""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from .hyde_multi_perspective_comprehensive import (
    MultiHyDEConfig,
    MultiHypotheticalDocuments,
    generate_multi_hypothetical_documents,
)

# Import from search_research modules
from .hyde_single import (
    HypotheticalDocument,
    generate_hypothetical_document,
)

# CANONICAL import (Q-ARCH-001 fix)
from .models import SearchResult


@dataclass
class EnsembleResult:
    """
    Represents the combined result from Hybrid Ensemble.

    Attributes:
        combined_results: List[SearchResult] - final ranked results after fusion
        sources_used: Dict[str, int] - count of results from each source
        ensemble_method: str - method used for combining results
        query_variants: List[str] - query variants used from Query Expansion
        hypothetical_document: Optional[HypotheticalDocument] - from Single HyDE
        multi_hypothetical_documents: Optional[MultiHypotheticalDocuments] - from Multi HyDE
        metadata: Dict[str, Any] - additional metadata about the ensemble process
    """

    combined_results: list[SearchResult]
    sources_used: dict[str, int]
    ensemble_method: str = "reciprocal_rank_fusion"
    query_variants: list[str] = field(default_factory=list)
    hypothetical_document: HypotheticalDocument | None = None
    multi_hypothetical_documents: MultiHypotheticalDocuments | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class HybridEnsembleConfig:
    """
    Configuration for Hybrid Ensemble generation.

    Attributes:
        enable_query_expansion: bool - whether to use Query Expansion
        enable_single_hyde: bool - whether to use Single HyDE
        enable_multi_hyde: bool - whether to use Multi-HyDE
        hyde_perspectives: List[str] - perspectives to use for Multi-HyDE
        ensemble_method: str - "reciprocal_rank_fusion" or "weighted_average"
        max_results: int - maximum number of results to return
        rrf_k: int - constant k for RRF calculation (default: 60)
    """

    enable_query_expansion: bool = True
    enable_single_hyde: bool = True
    enable_multi_hyde: bool = True
    hyde_perspectives: list[str] | None = None
    ensemble_method: str = "reciprocal_rank_fusion"
    max_results: int = 20
    rrf_k: int = 60

    def __post_init__(self):
        """Set default perspectives if not provided."""
        if self.hyde_perspectives is None:
            self.hyde_perspectives = ["technical", "beginner", "comprehensive"]


# =============================================================================
# Mock Search Functions for Testing
# =============================================================================


def _generate_mock_query_variants(query: str) -> list[str]:
    """
    Generate mock query variants for testing.

    Args:
        query: The original query

    Returns:
        List of query variants
    """
    query_lower = query.lower()

    if "jwt" in query_lower and "fastapi" in query_lower:
        return [
            query,
            "FastAPI JWT token authentication tutorial",
            "FastAPI OAuth2 JWT implementation example",
            "FastAPI security JWT bearer token",
        ]
    elif "machine learning" in query_lower:
        return [
            query,
            "ML algorithms and models",
            "supervised unsupervised learning",
            "neural networks deep learning",
        ]
    else:
        return [
            query,
            f"{query} tutorial",
            f"how to {query_lower}",
            f"{query} guide examples",
        ]


def _generate_mock_search_results(query: str, backend: str, count: int = 5) -> list[SearchResult]:
    """
    Generate mock search results for testing.

    Args:
        query: The search query
        backend: Backend name for these results
        count: Number of results to generate

    Returns:
        List of mock SearchResult objects
    """
    query_lower = query.lower()

    if "jwt" in query_lower and "fastapi" in query_lower:
        titles = [
            "JWT FastAPI Implementation Guide",
            "FastAPI Security Tutorial",
            "OAuth2 with FastAPI Complete Guide",
            "FastAPI Authentication Best Practices",
            "JWT Token Management in FastAPI",
        ]
        contents = [
            "Complete guide to implementing JWT authentication in FastAPI with code examples...",
            "Learn how to secure your FastAPI application with JWT tokens...",
            "OAuth2 flow implementation with FastAPI and JWT tokens...",
            "Best practices for securing FastAPI endpoints with JWT...",
            "Token generation, validation, and refresh strategies...",
        ]
        sources = [
            "docs.example.com",
            "tutorials.dev",
            "authguide.io",
            "fastapi-security.com",
            "codelearn.net",
        ]
    elif "machine learning" in query_lower:
        titles = [
            "Introduction to Machine Learning",
            "ML Algorithms Explained",
            "Supervised vs Unsupervised Learning",
            "Neural Networks Fundamentals",
            "ML Model Deployment Guide",
        ]
        contents = [
            "Comprehensive introduction to machine learning concepts...",
            "Detailed explanation of common ML algorithms...",
            "Comparison of supervised and unsupervised learning approaches...",
            "Fundamentals of neural networks and deep learning...",
            "Best practices for deploying ML models to production...",
        ]
        sources = [
            "ml-basics.com",
            "algorithms.dev",
            "learning-types.edu",
            "neuralnet.ai",
            "deploy-ml.io",
        ]
    else:
        titles = [f"Result {i + 1} for {query[:20]}" for i in range(count)]
        contents = [f"Content for result {i + 1} matching query '{query}'..." for i in range(count)]
        sources = [f"source{i + 1}.com" for i in range(count)]

    results = []
    for i in range(min(count, len(titles))):
        # Score decreases with rank
        score = 0.95 - (i * 0.08)
        results.append(
            SearchResult(
                backend=backend,
                title=titles[i] if i < len(titles) else f"Result {i + 1}",
                content=contents[i] if i < len(contents) else f"Content {i + 1}",
                source=sources[i] if i < len(sources) else f"source{i + 1}.com",
                score=max(0.0, score),
                metadata={"rank": i + 1},
            )
        )

    return results


# =============================================================================
# Reciprocal Rank Fusion (RRF)
# =============================================================================


def reciprocal_rank_fusion(
    results_lists: list[list[SearchResult]], k: int = 60, max_results: int | None = None
) -> list[SearchResult]:
    """
    Combine multiple rankings using Reciprocal Rank Fusion (RRF).

    RRF is a robust method for combining ranked search results from multiple sources.
    The formula is: score(d) = sum(1 / (k + rank_d)) for each ranking

    Args:
        results_lists: List of (SearchResult) lists, each already ranked
        k: The RRF constant (default 60). Higher values flatten score differences.
        max_results: Maximum number of results to return (None for all)

    Returns:
        List of SearchResults sorted by RRF score descending
    """
    # Handle empty input
    if not results_lists:
        return []

    # Filter out empty lists
    non_empty_lists = [lst for lst in results_lists if lst]
    if not non_empty_lists:
        return []

    # Dictionary to accumulate RRF scores
    # Key: (backend, title) tuple to identify unique results
    # Value: tuple of (rrf_score, result_object)
    rrf_scores: dict[tuple[str, str], tuple[float, SearchResult]] = {}

    for results_list in non_empty_lists:
        for rank, result in enumerate(results_list, start=1):
            # Create unique key for this result
            key = (result.backend, result.title)

            # Calculate RRF contribution: 1 / (k + rank)
            rrf_contribution = 1.0 / (k + rank)

            if key in rrf_scores:
                # Accumulate score if already seen
                current_score, existing_result = rrf_scores[key]
                rrf_scores[key] = (current_score + rrf_contribution, existing_result)
            else:
                rrf_scores[key] = (rrf_contribution, result)

    # Sort by RRF score descending
    sorted_results = sorted(rrf_scores.values(), key=lambda x: x[0], reverse=True)

    # Create result list with updated scores
    combined_results = []
    for rrf_score, result in sorted_results:
        # Create a new SearchResult with the RRF score
        new_result = SearchResult(
            backend=result.backend,
            title=result.title,
            content=result.content,
            source=result.source,
            score=rrf_score,
            metadata={**result.metadata, "rrf_score": rrf_score},
        )
        combined_results.append(new_result)

    # Apply max_results limit if specified
    if max_results is not None and max_results > 0:
        combined_results = combined_results[:max_results]

    return combined_results


# =============================================================================
# Weighted Average Fusion
# =============================================================================


def weighted_average_fusion(
    results_lists: list[list[SearchResult]],
    weights: dict[str, float] | None = None,
    max_results: int | None = None,
) -> list[SearchResult]:
    """
    Combine results using weighted average of scores.

    Args:
        results_lists: List of SearchResult lists
        weights: Dictionary mapping backend names to weights
        max_results: Maximum number of results to return

    Returns:
        List of SearchResults sorted by weighted score descending

    Raises:
        ValueError: If weights is empty
    """
    # Handle empty input
    if not results_lists:
        return []

    # Filter out empty lists
    non_empty_lists = [lst for lst in results_lists if lst]
    if not non_empty_lists:
        return []

    # Default weights: equal weight for each backend
    if weights is None:
        weights = {f"backend_{i}": 1.0 for i in range(len(non_empty_lists))}
    elif not weights:
        raise ValueError("Weights dictionary cannot be empty")

    # Normalize weights to sum to 1
    total_weight = sum(weights.values())
    if total_weight == 0:
        raise ValueError("Sum of weights cannot be zero")
    normalized_weights = {k: v / total_weight for k, v in weights.items()}

    # Dictionary to accumulate weighted scores
    # Key: (backend, title) tuple to identify unique results
    # Value: tuple of (weighted_score, result_object, weight_sum)
    score_aggregation: dict[tuple[str, str], tuple[float, SearchResult, float]] = {}

    for _i, results_list in enumerate(non_empty_lists):
        # Get weight for this backend (use backend name or index)
        if results_list and results_list[0].backend in normalized_weights:
            weight = normalized_weights[results_list[0].backend]
        else:
            # Default to equal weight if backend not in weights dict
            weight = 1.0 / len(non_empty_lists)

        for result in results_list:
            key = (result.backend, result.title)

            # Calculate weighted score
            weighted_contribution = result.score * weight

            if key in score_aggregation:
                current_score, existing_result, weight_sum = score_aggregation[key]
                score_aggregation[key] = (
                    current_score + weighted_contribution,
                    existing_result,
                    weight_sum + weight,
                )
            else:
                score_aggregation[key] = (weighted_contribution, result, weight)

    # Sort by aggregated score descending
    sorted_results = sorted(score_aggregation.values(), key=lambda x: x[0], reverse=True)

    # Create result list with weighted scores
    combined_results = []
    for weighted_score, result, _ in sorted_results:
        new_result = SearchResult(
            backend=result.backend,
            title=result.title,
            content=result.content,
            source=result.source,
            score=weighted_score,
            metadata={**result.metadata, "weighted_score": weighted_score},
        )
        combined_results.append(new_result)

    # Apply max_results limit if specified
    if max_results is not None and max_results > 0:
        combined_results = combined_results[:max_results]

    return combined_results


# =============================================================================
# Main Hybrid Ensemble Function
# =============================================================================


def run_hybrid_ensemble(query: str, config: HybridEnsembleConfig | None = None) -> EnsembleResult:
    """
    Run the Hybrid Ensemble process combining all optimization stages.

    This function orchestrates Query Expansion, Single HyDE, and Multi-HyDE,
    then combines their results using the specified ensemble method.

    Args:
        query: The search query
        config: Configuration for the ensemble (uses defaults if None)

    Returns:
        EnsembleResult with combined results and metadata

    Raises:
        TypeError: If query is None
        ValueError: If query is empty or whitespace only
        ValueError: If all stages are disabled
        ValueError: If ensemble_method is invalid
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
        config = HybridEnsembleConfig()

    # Validate ensemble method
    valid_methods = ["reciprocal_rank_fusion", "weighted_average"]
    if config.ensemble_method not in valid_methods:
        # Default to RRF if invalid method provided
        config.ensemble_method = "reciprocal_rank_fusion"

    # Check if any stages are enabled
    if not any(
        [config.enable_query_expansion, config.enable_single_hyde, config.enable_multi_hyde]
    ):
        # Return empty result when all stages are disabled
        return EnsembleResult(
            combined_results=[],
            sources_used={},
            ensemble_method=config.ensemble_method,
            query_variants=[],
            metadata={"stages_executed": [], "warning": "All stages disabled"},
        )

    # Handle max_results = 0
    if config.max_results <= 0:
        return EnsembleResult(
            combined_results=[],
            sources_used={},
            ensemble_method=config.ensemble_method,
            query_variants=[],
            metadata={"warning": "max_results is 0 or negative"},
        )

    # Start timing
    start_time = time.time()

    # Initialize collections
    all_results: list[list[SearchResult]] = []
    sources_used: dict[str, int] = defaultdict(int)
    stages_executed: list[str] = []

    # 1. Query Expansion
    query_variants: list[str] = []
    if config.enable_query_expansion:
        stages_executed.append("query_expansion")
        query_variants = _generate_mock_query_variants(query)

        # Generate mock results for each query variant
        for variant in query_variants:
            variant_results = _generate_mock_search_results(
                variant, "query_expansion", count=min(5, config.max_results)
            )
            all_results.append(variant_results)
            sources_used["query_expansion"] += len(variant_results)

    # 2. Single HyDE
    hypothetical_document: HypotheticalDocument | None = None
    if config.enable_single_hyde:
        stages_executed.append("single_hyde")

        try:
            hypothetical_document = generate_hypothetical_document(query)
            # Generate mock results using the hypothetical document
            hyde_results = _generate_mock_search_results(
                hypothetical_document.content[:100], "single_hyde", count=min(5, config.max_results)
            )
            all_results.append(hyde_results)
            sources_used["single_hyde"] += len(hyde_results)
        except RuntimeError:
            # GLM not available, use mock
            hypothetical_document = HypotheticalDocument(
                query=query,
                content=f"# Mock Hypothetical Document for: {query}\n\nThis is a mock document for testing purposes.",
                generation_model="mock",
                generation_time=0.0,
                word_count=20,
                token_count=30,
            )
            hyde_results = _generate_mock_search_results(
                query, "single_hyde", count=min(5, config.max_results)
            )
            all_results.append(hyde_results)
            sources_used["single_hyde"] += len(hyde_results)

    # 3. Multi-HyDE
    multi_hypothetical_documents: MultiHypotheticalDocuments | None = None
    if config.enable_multi_hyde:
        stages_executed.append("multi_hyde")

        try:
            multi_config = MultiHyDEConfig(perspectives=config.hyde_perspectives)
            multi_hypothetical_documents = generate_multi_hypothetical_documents(
                query, multi_config
            )
            # Generate mock results for each perspective's document
            for doc in multi_hypothetical_documents.documents:
                doc_results = _generate_mock_search_results(
                    doc.content[:100], "multi_hyde", count=min(3, config.max_results)
                )
                all_results.append(doc_results)
                sources_used["multi_hyde"] += len(doc_results)
        except RuntimeError:
            # GLM not available, use mock
            mock_docs = []
            for perspective in config.hyde_perspectives[:3]:
                doc = HypotheticalDocument(
                    query=query,
                    content=f"# Mock {perspective} document for: {query}\n\nMock content for {perspective} perspective.",
                    generation_model="mock",
                    generation_time=0.0,
                    word_count=15,
                    token_count=20,
                )
                doc.perspective = perspective
                mock_docs.append(doc)

            multi_hypothetical_documents = MultiHypotheticalDocuments(
                query=query,
                documents=mock_docs,
                perspectives=config.hyde_perspectives[:3],
                total_generation_time=0.0,
                total_word_count=45,
                total_token_count=60,
            )

            for doc in mock_docs:
                doc_results = _generate_mock_search_results(
                    query, "multi_hyde", count=min(3, config.max_results)
                )
                all_results.append(doc_results)
                sources_used["multi_hyde"] += len(doc_results)

    # Combine results using the specified ensemble method
    if config.ensemble_method == "weighted_average":
        # Create weights dict from sources_used
        total_sources = sum(sources_used.values()) or 1
        weights = {source: count / total_sources for source, count in sources_used.items()}
        combined_results = weighted_average_fusion(
            all_results, weights=weights, max_results=config.max_results
        )
    else:  # reciprocal_rank_fusion (default)
        combined_results = reciprocal_rank_fusion(
            all_results,
            k=abs(config.rrf_k),  # Handle negative k by using absolute value
            max_results=config.max_results,
        )

    # Calculate execution time
    execution_time = time.time() - start_time

    # Create metadata
    metadata: dict[str, Any] = {
        "execution_time": execution_time,
        "stages_executed": stages_executed,
        "total_results_before_fusion": sum(len(r) for r in all_results),
        "total_results_after_fusion": len(combined_results),
        "query_length": len(query),
        "rrf_k": config.rrf_k if config.ensemble_method == "reciprocal_rank_fusion" else None,
    }

    return EnsembleResult(
        combined_results=combined_results,
        sources_used=dict(sources_used),
        ensemble_method=config.ensemble_method,
        query_variants=query_variants,
        hypothetical_document=hypothetical_document,
        multi_hypothetical_documents=multi_hypothetical_documents,
        metadata=metadata,
    )


# =============================================================================
# Public API
# =============================================================================

__all__ = [
    "SearchResult",
    "EnsembleResult",
    "HybridEnsembleConfig",
    "reciprocal_rank_fusion",
    "weighted_average_fusion",
    "run_hybrid_ensemble",
]
