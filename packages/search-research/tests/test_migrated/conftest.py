"""
Shared fixtures and test utilities for migrated research components.

This module provides common test data, fixtures, and utilities used across
all test files for the migrated research functionality.
"""

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

from pytest import fixture

# Add core to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "core"))

from core.analysis.contradiction_detector import ResearchResult

# Import classes under test
from core.analysis.gap_analyzer import CoverageGap, GapType
from core.analysis.topic_clusterer import CoverageState, TopicSignature
from core.enhancement.enhanced_dependency_analyzer import (
    QueryDependencies,
    ResearchDepth,
)
from core.enhancement.mode_relationship_mapper import ModeCombination, ResearchMode
from core.processing.result_normalizer import NormalizedResult, SourceType


@fixture
def sample_raw_results() -> list[dict[str, Any]]:
    """Sample raw search results from multiple providers."""
    return [
        {
            "url": "https://docs.python.org/3/library/asyncio.html",
            "title": "asyncio — Asynchronous I/O",
            "content": "Python's asyncio library provides infrastructure for writing single-threaded concurrent code.",
            "score": 0.95
        },
        {
            "url": "https://github.com/python/cpython",
            "title": "python/cpython: The Python programming language",
            "content": "The CPython reference implementation.",
            "snippet": "Main Python implementation"
        },
        {
            "url": "https://stackoverflow.com/questions/12345",
            "title": "How to use asyncio in Python?",
            "content": "You can use asyncio.run() to execute async code.",
            "snippet": "asyncio tutorial"
        },
        {
            "url": "https://arxiv.org/abs/2301.00000",
            "title": "Recent Advances in Asynchronous Programming",
            "content": "This paper surveys async programming patterns.",
            "snippet": "academic paper on async",
            "date": "2023-01-01"
        },
        {
            "url": "https://medium.com/tutorial/async-python",
            "title": "Understanding Async Python",
            "content": "A beginner-friendly guide to async/await.",
            "snippet": "async tutorial blog"
        }
    ]


@fixture
def sample_normalized_results() -> list[NormalizedResult]:
    """Sample normalized results for testing."""
    return [
        NormalizedResult(
            title="Python Asyncio Documentation",
            snippet="Python's asyncio library provides infrastructure for writing single-threaded concurrent code.",
            url="https://docs.python.org/3/library/asyncio.html",
            domain="docs.python.org",
            source_type=SourceType.DOCS,
            provider="tavily",
            metadata={"trust_score": 0.95, "original_score": 0.95}
        ),
        NormalizedResult(
            title="Python GitHub Repository",
            snippet="The CPython reference implementation.",
            url="https://github.com/python/cpython",
            domain="github.com",
            source_type=SourceType.COMMUNITY,
            provider="serper",
            metadata={"trust_score": 0.80, "original_score": 0.88}
        ),
        NormalizedResult(
            title="Stack Overflow Async Question",
            snippet="You can use asyncio.run() to execute async code.",
            url="https://stackoverflow.com/questions/12345",
            domain="stackoverflow.com",
            source_type=SourceType.COMMUNITY,
            provider="brave",
            metadata={"trust_score": 0.75, "original_score": 0.82}
        ),
        NormalizedResult(
            title="Recent Advances in Async Programming",
            snippet="This paper surveys async programming patterns.",
            url="https://arxiv.org/abs/2301.00000",
            domain="arxiv.org",
            source_type=SourceType.ACADEMIC,
            provider="exa",
            metadata={"trust_score": 0.90, "original_score": 0.85}
        ),
    ]


@fixture
def sample_research_results() -> list[ResearchResult]:
    """Sample research results for contradiction detection."""
    return [
        ResearchResult(
            title="Python supports async/await",
            url="https://docs.python.org/asyncio",
            content="Python supports async and await syntax for asynchronous programming.",
            source="official_docs"
        ),
        ResearchResult(
            title="Python async limitation",
            url="https://old-blog.com/python-async",
            content="Python does not support async natively, requires external libraries.",
            source="blog"
        ),
        ResearchResult(
            title="GitHub supports webhooks",
            url="https://docs.github.com/webhooks",
            content="GitHub supports both webhooks and actions for automation.",
            source="official_docs"
        ),
        ResearchResult(
            title="GitHub webhook options",
            url="https://tutorial.github.com/integration",
            content="GitHub only supports webhooks for integration, actions are separate.",
            source="tutorial"
        ),
    ]


@fixture
def sample_coverage_state() -> CoverageState:
    """Sample coverage state for novelty tracking."""
    return CoverageState(
        topics={"topic_async", "topic_python", "topic_programming"},
        source_types={"docs", "community", "academic"},
        domains={"docs.python.org", "github.com", "stackoverflow.com"},
        claim_terms={"async", "await", "concurrent", "coroutine"}
    )


@fixture
def sample_query_dependencies() -> QueryDependencies:
    """Sample query dependencies for testing."""
    return QueryDependencies(
        requires_code=True,
        requires_github=True,
        requires_documentation=True,
        requires_academic=False,
        requires_ai_perspectives=False,
        requires_tutorials=True,
        complexity_score=0.6,
        research_depth=ResearchDepth.INTERMEDIATE,
        confidence=0.85,
        primary_indicators=["code:async", "github:repo", "documentation:docs"]
    )


@fixture
def sample_mode_combination() -> ModeCombination:
    """Sample mode combination for testing."""
    return ModeCombination(
        modes=[ResearchMode.OCTOCODE, ResearchMode.WEB],
        predicted_quality=0.88,
        estimated_cost=2.5,
        redundancy_score=0.3,
        coverage_score=0.92
    )


@fixture
def sample_topic_clusters() -> dict[str, TopicSignature]:
    """Sample topic clusters for testing."""
    return {
        "topic_a1b2": TopicSignature(
            topic_id="topic_a1b2",
            keyword_hash=0xa1b2,
            keywords={"python", "async", "await"},
            result_ids={"url1", "url2"}
        ),
        "topic_c3d4": TopicSignature(
            topic_id="topic_c3d4",
            keyword_hash=0xc3d4,
            keywords={"github", "repository", "code"},
            result_ids={"url3", "url4"}
        ),
    }


@fixture
def sample_coverage_gaps() -> list[CoverageGap]:
    """Sample coverage gaps for testing."""
    return [
        CoverageGap(
            gap_type=GapType.MISSING_SOURCE_TYPE,
            description="Missing video sources",
            severity=0.7,
            metadata={"missing_type": "video"}
        ),
        CoverageGap(
            gap_type=GapType.LOW_DOMAIN_DIVERSITY,
            description="Low domain diversity (2 domains)",
            severity=0.6,
            metadata={"domain_count": 2, "domains": ["github.com", "stackoverflow.com"]}
        ),
    ]


@fixture
def mock_search_provider():
    """Mock search provider for testing orchestration."""
    provider = MagicMock()
    provider.name = "mock_provider"

    # Create async mock for search method
    async def mock_search(query: str, **kwargs):
        return [
            {
                "url": f"https://example.com/result{i}",
                "title": f"Result {i} for {query}",
                "snippet": f"Content snippet {i}",
                "score": 0.9 - (i * 0.1)
            }
            for i in range(1, 6)
        ]

    provider.search = mock_search
    return provider


@fixture
def sample_feedback_data() -> list[dict[str, Any]]:
    """Sample feedback data for learning system tests."""
    return [
        {
            "research_id": "test_001",
            "query": "react hooks implementation",
            "modes_used": ["octocode", "web"],
            "predicted_quality": 0.85,
            "actual_quality_rating": 4.2,
            "helpful_aspects": ["code examples", "github repos"],
            "improvement_suggestions": ["more documentation"],
            "sources_helpful": ["github", "stackoverflow"],
            "sources_missing": ["official docs"],
            "timestamp": "2024-01-15T10:30:00",
            "session_duration": 120.5,
            "user_expertise_level": "intermediate",
            "research_domain": "technical"
        },
        {
            "research_id": "test_002",
            "query": "machine learning research papers",
            "modes_used": ["web"],
            "predicted_quality": 0.75,
            "actual_quality_rating": 3.8,
            "helpful_aspects": ["paper links"],
            "improvement_suggestions": ["more recent papers"],
            "sources_helpful": ["arxiv"],
            "sources_missing": ["ieee", "acm"],
            "timestamp": "2024-01-16T14:20:00",
            "session_duration": 180.0,
            "user_expertise_level": "expert",
            "research_domain": "academic"
        },
    ]


@fixture
def temp_feedback_file(tmp_path) -> str:
    """Create a temporary feedback file for testing."""
    feedback_file = tmp_path / "test_feedback.json"
    return str(feedback_file)


@fixture
def sample_research_queries() -> list[str]:
    """Sample research queries for testing."""
    return [
        "react hooks implementation example",
        "github repository microservices architecture",
        "machine learning research papers comparison",
        "docker production deployment security",
        "python asyncio best practices",
    ]


@dataclass
class MockSearchResult:
    """Mock search result for testing."""
    title: str
    url: str
    snippet: str
    score: float = 0.8
    source_type: str = "unknown"
    domain: str = ""


@fixture
def mock_search_results() -> list[MockSearchResult]:
    """Mock search results with domain and source type."""
    return [
        MockSearchResult(
            title="Python Asyncio Guide",
            url="https://docs.python.org/3/library/asyncio.html",
            snippet="Comprehensive asyncio documentation",
            score=0.95,
            source_type="docs",
            domain="docs.python.org"
        ),
        MockSearchResult(
            title="GitHub Async Projects",
            url="https://github.com/topics/async",
            snippet="Curated list of async projects",
            score=0.88,
            source_type="community",
            domain="github.com"
        ),
        MockSearchResult(
            title="Async Programming Tutorial",
            url="https://example.com/async-tutorial",
            snippet="Learn async programming patterns",
            score=0.82,
            source_type="blog",
            domain="example.com"
        ),
    ]


# Test helper functions

def create_mock_result(
    title: str = "Test Result",
    url: str = "https://example.com",
    content: str = "Test content",
    source: str = "test"
) -> ResearchResult:
    """Helper to create mock ResearchResult objects."""
    return ResearchResult(
        title=title,
        url=url,
        content=content,
        source=source
    )


def create_normalized_result(
    title: str = "Test Result",
    snippet: str = "Test snippet",
    url: str = "https://example.com",
    domain: str = "example.com",
    source_type: SourceType = SourceType.UNKNOWN,
    provider: str = "test"
) -> NormalizedResult:
    """Helper to create mock NormalizedResult objects."""
    return NormalizedResult(
        title=title,
        snippet=snippet,
        url=url,
        domain=domain,
        source_type=source_type,
        provider=provider
    )


def assert_coverage_gap(
    gap: CoverageGap,
    expected_type: GapType,
    min_severity: float = 0.0
) -> None:
    """Helper to assert coverage gap properties."""
    assert gap.gap_type == expected_type
    assert gap.severity >= min_severity
    assert len(gap.description) > 0
    assert isinstance(gap.metadata, dict)


def assert_normalized_result(
    result: NormalizedResult,
    has_url: bool = True,
    has_title: bool = True
) -> None:
    """Helper to assert normalized result properties."""
    if has_url:
        assert len(result.url) > 0
        assert isinstance(result.domain, str)
    if has_title:
        assert len(result.title) > 0
    assert isinstance(result.source_type, SourceType)
    assert isinstance(result.provider, str)
    assert isinstance(result.metadata, dict)


# Async test utilities

async def async_none() -> None:
    """Helper for async functions that return None."""
    return None


class AsyncContextManager:
    """Helper for async context manager testing."""

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return None
