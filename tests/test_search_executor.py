#!/usr/bin/env python3
"""Unit tests for search_executor module.

Tests the extracted search execution functions:
- execute_search: Execute search with Layer 1 filtering
- apply_layer1_rule_based_filtering: Apply Python rule-based filtering
- format_results_human: Format results for human display
- format_results_json: Format results as JSON
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

# Add skills/all directory to path for imports
skills_path = Path(__file__).parent.parent / "skills" / "all"
sys.path.insert(0, str(skills_path))

from search_executor import (
    apply_layer1_rule_based_filtering,
    execute_search,
    format_results_human,
    format_results_json,
)


class MockSearchResult:
    """Mock search result for testing."""

    def __init__(self, title: str, content: str, score: float, source: str = "WEB"):
        self.title = title
        self.content = content
        self.score = score
        self.source = source
        self.url = None
        self.metadata = {}


@pytest.mark.asyncio
async def test_execute_search_basic():
    """Test execute_search with basic parameters."""
    with patch("search_executor.UnifiedAsyncRouter") as MockRouter:
        # Setup mock
        mock_router = AsyncMock()
        mock_results = [MockSearchResult("Test", "Content", 0.8)]
        mock_router.search_async.return_value = mock_results
        MockRouter.return_value = mock_router

        # Execute
        results = await execute_search("test query", mode="auto", limit=10)

        # Verify
        assert len(results) == 1
        assert results[0].title == "Test"
        mock_router.search_async.assert_called_once_with("test query", limit=10)


@pytest.mark.asyncio
async def test_execute_search_with_quality_config():
    """Test execute_search passes quality config correctly."""
    with patch("search_executor.UnifiedAsyncRouter") as MockRouter:
        # Setup mock
        mock_router = AsyncMock()
        mock_router.search_async.return_value = []
        MockRouter.return_value = mock_router

        # Execute with custom quality parameters
        # Note: execute_search() accepts min_score/min_results, which are mapped to
        # QualityConfig.confidence_threshold and QualityConfig.min_backends
        results = await execute_search(
            "test query", mode="unified", limit=20, min_score=0.7, min_results=5, rrf_k=80
        )

        # Verify UnifiedAsyncRouter was called with correct config
        MockRouter.assert_called_once()
        call_kwargs = MockRouter.call_args[1]
        assert call_kwargs["mode"] == "unified"
        assert call_kwargs["rrf_k"] == 80
        # QualityConfig maps min_score → confidence_threshold, min_results → min_backends
        assert call_kwargs["quality_config"].confidence_threshold == 0.7
        assert call_kwargs["quality_config"].min_backends == 5


@pytest.mark.asyncio
async def test_execute_search_empty_results():
    """Test execute_search returns empty list when no results."""
    with patch("search_executor.UnifiedAsyncRouter") as MockRouter:
        # Setup mock
        mock_router = AsyncMock()
        mock_router.search_async.return_value = []
        MockRouter.return_value = mock_router

        # Execute
        results = await execute_search("no results query")

        # Verify
        assert results == []


def test_apply_layer1_rule_based_filtering_no_op():
    """Test apply_layer1_rule_based_filtering is a no-op (Layer 1 already applied)."""
    # Setup
    results = [
        MockSearchResult("Result 1", "Content 1", 0.9),
        MockSearchResult("Result 2", "Content 2", 0.7),
    ]

    # Execute
    filtered = apply_layer1_rule_based_filtering(results)

    # Verify (should return same list since Layer 1 is already applied by UnifiedAsyncRouter)
    assert filtered == results
    assert len(filtered) == 2


def test_format_results_human_standard_mode():
    """Test format_results_human with standard format (Layer 1 only)."""
    # Setup
    results = [
        MockSearchResult("Python async patterns", "Content about async/await", 0.9, "Code"),
        MockSearchResult("Web search result", "Content from web", 0.7, "WEB"),
    ]

    # Execute
    output = format_results_human("async patterns", results, mode="auto")

    # Verify
    assert "async patterns" in output
    assert "Mode: auto" in output
    assert "Results: 2" in output
    assert "[0.90]" in output
    assert "📚" in output  # Local source indicator
    assert "🌐" in output  # Web source indicator


def test_format_results_human_layer2_applied():
    """Test format_results_human with Layer 2 themed format."""
    # Setup
    results = []
    filtered_results = {
        "original_count": 20,
        "filtered_count": 5,
        "themes": [
            {
                "name": "Async Programming",
                "insights": [
                    {
                        "title": "Python async/await patterns",
                        "source": "Code",
                        "key_insights": ["Use async def", "Await coroutines"],
                    },
                    {
                        "title": "JavaScript promises",
                        "source": "WEB",
                        "key_insights": ["Promise chaining", "Async/await syntax"],
                    },
                ],
            }
        ],
    }

    # Execute
    output = format_results_human(
        "async", results, mode="auto", layer2_applied=True, filtered_results=filtered_results
    )

    # Verify
    assert "Layer 2 Applied" in output
    assert "20 results → 5 key insights" in output
    assert "Theme: Async Programming" in output
    assert "Python async/await patterns" in output
    assert "Use async def" in output


def test_format_results_human_empty_results():
    """Test format_results_human with empty results."""
    # Setup
    results = []

    # Execute
    output = format_results_human("test", results, mode="auto")

    # Verify
    assert "No results found" in output


def test_format_results_json():
    """Test format_results_json produces valid JSON."""
    # Setup
    results = [
        MockSearchResult("Test Title", "Test Content", 0.85, "Code"),
        MockSearchResult("Web Result", "Web Content", 0.75, "WEB"),
    ]
    results[0].url = "https://example.com/test"
    results[0].metadata = {"author": "Test"}

    # Execute
    import json

    output = format_results_json("test query", results, mode="unified")

    # Verify JSON is valid
    parsed = json.loads(output)
    assert parsed["query"] == "test query"
    assert parsed["mode"] == "unified"
    assert parsed["count"] == 2
    assert len(parsed["results"]) == 2

    # Verify first result
    first_result = parsed["results"][0]
    assert first_result["title"] == "Test Title"
    assert first_result["content"] == "Test Content"
    assert first_result["score"] == 0.85
    assert first_result["source"] == "Code"
    assert first_result["url"] == "https://example.com/test"
    assert first_result["metadata"]["author"] == "Test"

    # Verify second result
    second_result = parsed["results"][1]
    assert second_result["title"] == "Web Result"
    assert second_result["source"] == "WEB"
    assert "url" not in second_result  # No URL set


def test_format_results_json_empty_results():
    """Test format_results_json with empty results."""
    # Setup
    results = []

    # Execute
    import json

    output = format_results_json("test", results, mode="auto")

    # Verify
    parsed = json.loads(output)
    assert parsed["query"] == "test"
    assert parsed["count"] == 0
    assert parsed["results"] == []


def test_format_results_human_content_truncation():
    """Test format_results_human truncates long content."""
    # Setup
    long_content = "x" * 300  # 300 characters
    results = [MockSearchResult("Title", long_content, 0.8)]

    # Execute
    output = format_results_human("test", results, mode="auto")

    # Verify content is truncated with "..."
    assert "Content:" in output
    assert "..." in output
    # The preview should be truncated
    assert len([line for line in output.split("\n") if "Content:" in line][0]) < 400


@pytest.mark.asyncio
async def test_execute_search_jmri_parameter():
    """Test execute_search passes enable_jmri parameter correctly."""
    with patch("search_executor.UnifiedAsyncRouter") as MockRouter:
        # Setup mock
        mock_router = AsyncMock()
        mock_router.search_async.return_value = []
        MockRouter.return_value = mock_router

        # Execute with JMRI disabled
        results = await execute_search("test", enable_jmri=False)

        # Verify
        MockRouter.assert_called_once()
        call_kwargs = MockRouter.call_args[1]
        assert call_kwargs["enable_jmri"] is False
