"""
Functional tests for /all skill three-layer filtering architecture.

Tests cover:
- Layer 1: Python rule-based filtering (via AsyncSearchRouter)
- Layer 2: Context-aware filtering (trigger detection, subagent orchestration)
- Layer 3: Presentation formatting (standard vs themed output)
- Edge cases: Small result sets, context hints, flags
"""

import importlib.util
import sys
from pathlib import Path

# Load filtering module directly using importlib (all is a Python keyword)
skills_path = Path(__file__).parent.parent / "skills" / "all"
filtering_path = skills_path / "filtering.py"

spec = importlib.util.spec_from_file_location("filtering", filtering_path)
filtering = importlib.util.module_from_spec(spec)
sys.modules["filtering"] = filtering
spec.loader.exec_module(filtering)

from unittest.mock import AsyncMock, patch

import pytest

# Import filtering functions from loaded module
apply_context_filter = filtering.apply_context_filter
format_output = filtering.format_output
format_standard_results = filtering.format_standard_results
format_themed_results = filtering.format_themed_results
has_context_hints = filtering.has_context_hints
should_apply_context_filter = filtering.should_apply_context_filter

# Import from search_research package (models.py)
from core.models import SearchResult


class TestContextHintsDetection:
    """Test context hints detection for Layer 2 triggering."""

    def test_detects_discussion_hints(self):
        """Detects 'we discussed' patterns"""
        assert has_context_hints("we discussed async patterns") is True
        assert has_context_hints("We decided on this approach") is True
        assert has_context_hints("We agreed to use FastAPI") is True

    def test_detects_contextual_hints(self):
        """Detects context-specific hints"""
        assert has_context_hints("for the auth feature") is True
        assert has_context_hints("in the context of our implementation") is True
        assert has_context_hints("related to our API design") is True

    def test_detects_reference_hints(self):
        """Detects reference to previous conversation"""
        assert has_context_hints("mentioned earlier") is True
        assert has_context_hints("what did we say about this") is True

    def test_no_context_hints(self):
        """Returns False for queries without context hints"""
        assert has_context_hints("python async patterns") is False
        assert has_context_hints("fastapi vs flask") is False
        assert has_context_hints("machine learning tutorial") is False


class TestLayer2TriggerConditions:
    """Test when Layer 2 filtering should auto-enable."""

    def test_triggers_on_result_count(self):
        """Triggers when result count exceeds threshold"""
        results = [SearchResult(
            title=f"Result {i}",
            content=f"Content {i}",
            url=f"https://example.com/{i}",
            source="WEB",
            score=0.8
        ) for i in range(25)]  # 25 results > threshold of 20

        should_apply, reason = should_apply_context_filter(results, "test query")
        assert should_apply is True
        assert reason == "result_count"

    def test_triggers_on_context_hints(self):
        """Triggers on context hints even with few results"""
        results = [
            SearchResult(
                title="Async Patterns",
                content="Content",
                url="https://example.com/1",
                source="WEB",
                score=0.8
            )
        ]

        should_apply, reason = should_apply_context_filter(
            results,
            "we discussed async patterns earlier"
        )
        assert should_apply is True
        assert reason == "context_hints"

    def test_no_trigger_small_results_no_hints(self):
        """No trigger: small result set, no context hints"""
        results = [
            SearchResult(
                title=f"Result {i}",
                content=f"Content {i}",
                url=f"https://example.com/{i}",
                source="WEB",
                score=0.8
            ) for i in range(10)  # 10 results < threshold
        ]

        should_apply, reason = should_apply_context_filter(results, "python async")
        assert should_apply is False
        assert reason is None

    def test_custom_threshold(self):
        """Respects custom threshold parameter"""
        results = [
            SearchResult(
                title=f"Result {i}",
                content=f"Content {i}",
                url=f"https://example.com/{i}",
                source="WEB",
                score=0.8
            ) for i in range(15)
        ]  # 15 results

        # Default threshold (20) - should not trigger
        should_apply, _ = should_apply_context_filter(results, "test")
        assert should_apply is False

        # Custom threshold (10) - should trigger
        should_apply, _ = should_apply_context_filter(results, "test", threshold=10)
        assert should_apply is True


class TestLayer2SubagentFiltering:
    """Test Layer 2 subagent orchestration."""

    @pytest.mark.asyncio
    async def test_context_filter_returns_structure(self):
        """Returns proper structure with themes and counts"""
        results = [
            SearchResult(
                title="Python Async Guide",
                content="Learn async/await patterns",
                url="https://example.com/async",
                source="WEB",
                score=0.9
            ),
            SearchResult(
                title="FastAPI Tutorial",
                content="Build fast APIs with async",
                url="https://example.com/fastapi",
                source="WEB",
                score=0.8
            ),
        ]

        # Mock the Anthropic API call - patch the import at module level
        with patch('anthropic.Anthropic') as mock_anthropic:
            mock_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.content = [AsyncMock()]
            mock_response.content[0].text = '''
            {
                "themes": [
                    {
                        "name": "Async Programming",
                        "insights": [
                            {
                                "title": "Python Async Guide",
                                "key_insights": ["Use async/await for I/O operations"],
                                "source": "WEB"
                            }
                        ]
                    }
                ],
                "filtered_count": 1,
                "original_count": 2
            }
            '''
            mock_client.messages.create = AsyncMock(return_value=mock_response)
            mock_anthropic.return_value = mock_client

            filtered = await apply_context_filter(results, "python async")

            assert "themes" in filtered
            assert "filtered_count" in filtered
            assert "original_count" in filtered
            assert filtered["original_count"] == 2

    @pytest.mark.asyncio
    async def test_context_filter_fallback_on_error(self):
        """Returns fallback structure on error"""
        results = [
            SearchResult(
                title="Test",
                content="Content",
                url="https://example.com",
                source="WEB",
                score=0.8
            )
        ]

        # Mock API error - patch the import at module level
        with patch('anthropic.Anthropic') as mock_anthropic:
            mock_anthropic.side_effect = Exception("API Error")

            filtered = await apply_context_filter(results, "test")

            # Should return fallback with original results
            assert "themes" in filtered
            assert len(filtered["themes"]) == 1
            assert filtered["themes"][0]["name"] == "All Results"
            assert "filtering_error" in filtered


class TestLayer3Formatting:
    """Test Layer 3 presentation formatting."""

    def test_format_standard_results(self):
        """Formats results without Layer 2 filtering"""
        results = [
            SearchResult(
                title="Python Async Guide",
                content="Learn async programming patterns",
                url="https://example.com/async",
                source="WEB",
                score=0.9
            ),
            SearchResult(
                title="CKS Entry",
                content="Local knowledge about async",
                url=None,
                source="CKS",
                score=0.8
            ),
        ]

        output = format_standard_results(results, "python async")

        assert "Universal Search Results" in output
        assert "python async" in output
        assert "Python Async Guide" in output
        assert "CKS Entry" in output
        assert "🌐 WEB" in output  # Web source indicator
        assert "📚 LOCAL" in output  # Local source indicator

    def test_format_themed_results(self):
        """Formats themed results from Layer 2"""
        filtered_results = {
            "original_count": 50,
            "filtered_count": 15,
            "themes": [
                {
                    "name": "Async Patterns",
                    "insights": [
                        {
                            "title": "Python Async Guide",
                            "key_insights": ["Use async/await", "Avoid blocking calls"],
                            "source": "WEB"
                        }
                    ]
                }
            ]
        }

        output = format_themed_results(filtered_results, "python async")

        assert "Universal Search Results" in output
        assert "Layer 2 Applied" in output
        assert "50 results → 15 key insights" in output
        assert "Async Patterns" in output
        assert "Python Async Guide" in output

    def test_format_output_standard_mode(self):
        """Layer 3 routes to standard format when Layer 2 not applied"""
        results = [
            SearchResult(
                title="Test",
                content="Content",
                url="https://example.com",
                source="WEB",
                score=0.8
            )
        ]

        output = format_output(results, "test", layer2_applied=False)

        assert "Universal Search Results" in output
        # Standard format shows individual results
        assert "Test" in output

    def test_format_output_themed_mode(self):
        """Layer 3 routes to themed format when Layer 2 was applied"""
        filtered_results = {
            "original_count": 10,
            "filtered_count": 5,
            "themes": [{"name": "Theme", "insights": []}]
        }

        output = format_output(filtered_results, "test", layer2_applied=True)

        assert "Universal Search Results" in output
        assert "Layer 2 Applied" in output

    def test_format_output_json_mode(self):
        """Layer 3 supports JSON output format"""
        results = [
            SearchResult(
                title="Test",
                content="Content",
                url="https://example.com",
                source="WEB",
                score=0.8
            )
        ]

        import json
        output = format_output(results, "test", layer2_applied=False, format_type="json")
        parsed = json.loads(output)

        assert parsed["query"] == "test"
        assert "results" in parsed
        assert parsed["layer2_applied"] is False


class TestIntegration:
    """Integration tests for full filtering pipeline."""

    @pytest.mark.asyncio
    async def test_full_pipeline_small_results(self):
        """Small result set skips Layer 2, uses standard formatting"""
        results = [
            SearchResult(
                title="Result 1",
                content="Content 1",
                url="https://example.com/1",
                source="WEB",
                score=0.8
            )
        ] * 5  # 5 results, no context hints

        query = "python tutorial"

        # Layer 2 decision
        should_apply, _ = should_apply_context_filter(results, query)
        assert should_apply is False

        # Layer 3 formatting
        output = format_output(results, query, layer2_applied=False)
        assert "Universal Search Results" in output
        assert "Layer 2 Applied" not in output

    @pytest.mark.asyncio
    async def test_full_pipeline_large_results(self):
        """Large result set triggers Layer 2, uses themed formatting"""
        results = [
            SearchResult(
                title=f"Result {i}",
                content=f"Content {i}",
                url=f"https://example.com/{i}",
                source="WEB",
                score=0.8
            ) for i in range(25)
        ]  # 25 results > threshold

        query = "python async"

        # Layer 2 decision
        should_apply, reason = should_apply_context_filter(results, query)
        assert should_apply is True
        assert reason == "result_count"


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_empty_results(self):
        """Handles empty result set"""
        results = []

        should_apply, _ = should_apply_context_filter(results, "test")
        assert should_apply is False

        output = format_standard_results(results, "test")
        assert "No results found" in output

    def test_query_with_special_characters(self):
        """Handles queries with special characters"""
        query = "python async/await - what's best?"

        # Should not crash
        has_hints = has_context_hints(query)
        assert has_hints is False

    def test_mixed_sources(self):
        """Formats results from various sources correctly"""
        results = [
            SearchResult(
                title="Web Result",
                content="From web",
                url="https://example.com",
                source="WEB",
                score=0.9
            ),
            SearchResult(
                title="CKS Result",
                content="From CKS",
                url=None,
                source="CKS",
                score=0.8
            ),
            SearchResult(
                title="CHS Result",
                content="From chat",
                url=None,
                source="CHS",
                score=0.7
            ),
        ]

        output = format_standard_results(results, "test")
        assert "🌐 WEB" in output
        assert "📚 LOCAL" in output
        assert "💬 LOCAL" in output

    def test_score_threshold(self):
        """Scores below 0.5 should have been filtered by Layer 1"""
        # This test documents expectation - Layer 1 should filter
        # Results with score < 0.5 before they reach Layers 2/3
        results = [
            SearchResult(
                title="Low Quality",
                content="Poor match",
                url="https://example.com",
                source="WEB",
                score=0.3  # Should be filtered by Layer 1
            ),
            SearchResult(
                title="High Quality",
                content="Great match",
                url="https://example.com/good",
                source="WEB",
                score=0.9
            ),
        ]

        # Layer 2/3 operate on post-Layer-1 results
        # They should not see low-score results
        output = format_standard_results(results, "test")
        # Both shown because Layer 1 filtering happens earlier
        assert "Low Quality" in output
        assert "High Quality" in output
