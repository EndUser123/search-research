"""
Tests for proactive search injection functionality.

Tests follow TDD approach:
1. Define expected behavior
2. Write test cases
3. Implement functionality to make tests pass
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from yt_fts.lib.search.proactive_injection import (
    ProactiveSearchInjection,
    QueryIntentDetector,
)


class TestQueryIntentDetector:
    """Test suite for QueryIntentDetector class."""

    def test_detect_search_intent_with_question_words(self):
        """Test that questions starting with what/how/why are detected as search intent."""
        detector = QueryIntentDetector()

        # Question words should trigger search intent
        assert detector.detect("What is machine learning?") == "search"
        assert detector.detect("How does neural network work?") == "search"
        assert detector.detect("Why do we use transformers?") == "search"
        assert detector.detect("When was attention mechanism introduced?") == "search"
        assert detector.detect("Where can I find tutorials?") == "search"
        assert detector.detect("Who created backpropagation?") == "search"

    def test_detect_search_intent_with_search_keywords(self):
        """Test that queries containing search keywords are detected as search intent."""
        detector = QueryIntentDetector()

        # Explicit search keywords
        assert detector.detect("search for convolutional neural networks") == "search"
        assert detector.detect("find information about GPT") == "search"
        assert detector.detect("look up batch normalization") == "search"
        assert detector.detect("explain gradient descent") == "search"

    def test_detect_search_intent_with_topic_specific_terms(self):
        """Test that queries with specific technical topics are detected as search intent."""
        detector = QueryIntentDetector()

        # Technical/conceptual queries
        assert detector.detect("machine learning algorithms") == "search"
        assert detector.detect("deep learning architectures") == "search"
        assert detector.detect("computer vision techniques") == "search"
        assert detector.detect("natural language processing") == "search"

    def test_detect_conversational_intent(self):
        """Test that conversational queries are detected as chat intent."""
        detector = QueryIntentDetector()

        # Conversational patterns
        assert detector.detect("hello") == "chat"
        assert detector.detect("hi there") == "chat"
        assert detector.detect("thanks") == "chat"
        assert detector.detect("goodbye") == "chat"
        assert detector.detect("how are you?") == "chat"

    def test_detect_unknown_intent(self):
        """Test that unclear queries return unknown intent."""
        detector = QueryIntentDetector()

        # Ambiguous or very short queries
        assert detector.detect("") == "unknown"
        assert detector.detect("ok") == "unknown"
        assert detector.detect("maybe") == "unknown"


class TestProactiveSearchInjection:
    """Test suite for ProactiveSearchInjection class."""

    @pytest.fixture
    def mock_search_handler(self):
        """Create a mock search handler."""
        handler = Mock()
        handler.res = [
            {
                "video_id": "test123",
                "start_time": "00:01:23",
                "text": "Machine learning is a subset of artificial intelligence.",
                "channel_name": "TestChannel",
                "video_title": "Introduction to ML",
                "link": "https://youtu.be/test123?t=83",
            }
        ]
        return handler

    def test_should_inject_search_with_search_intent(self):
        """Test that search is injected when intent is 'search'."""
        injector = ProactiveSearchInjection()

        # Should inject when intent is search
        assert injector.should_inject("What is machine learning?") is True
        assert injector.should_inject("How do neural networks learn?") is True

    def test_should_not_inject_search_with_chat_intent(self):
        """Test that search is not injected when intent is 'chat'."""
        injector = ProactiveSearchInjection()

        # Should not inject for conversational queries
        assert injector.should_inject("hello") is False
        assert injector.should_inject("thanks for your help") is False

    def test_should_not_inject_search_with_unknown_intent(self):
        """Test that search is not injected when intent is 'unknown'."""
        injector = ProactiveSearchInjection()

        # Should not inject for ambiguous queries
        assert injector.should_inject("") is False
        assert injector.should_inject("ok") is False

    def test_execute_proactive_search_success(self, mock_search_handler):
        """Test successful execution of proactive search."""
        injector = ProactiveSearchInjection()

        with patch(
            "yt_fts.core.search.SearchHandler",
            return_value=mock_search_handler,
        ):
            result = injector.execute_search(
                "machine learning", scope="all", limit=5
            )

            assert result["success"] is True
            assert len(result["results"]) == 1
            assert result["query"] == "machine learning"
            assert result["results"][0]["video_id"] == "test123"

    def test_execute_proactive_search_no_results(self):
        """Test proactive search when no results are found."""
        injector = ProactiveSearchInjection()

        mock_handler = Mock()
        mock_handler.res = []

        with patch(
            "yt_fts.core.search.SearchHandler",
            return_value=mock_handler,
        ):
            result = injector.execute_search(
                "nonexistent topic xyz", scope="all", limit=5
            )

            assert result["success"] is True
            assert len(result["results"]) == 0
            assert result["query"] == "nonexistent topic xyz"

    def test_execute_proactive_search_with_error(self):
        """Test proactive search when an error occurs."""
        injector = ProactiveSearchInjection()

        with patch(
            "yt_fts.core.search.SearchHandler",
            side_effect=Exception("Database error"),
        ):
            result = injector.execute_search("test query", scope="all", limit=5)

            assert result["success"] is False
            assert "error" in result
            assert "Database error" in result["error"]

    def test_format_results_for_llm(self, mock_search_handler):
        """Test formatting search results for LLM consumption."""
        injector = ProactiveSearchInjection()

        formatted = injector.format_for_llm(mock_search_handler.res)

        assert isinstance(formatted, str)
        assert "machine learning" in formatted.lower()
        assert "TestChannel" in formatted
        assert "00:01:23" in formatted
        assert "test123" in formatted

    def test_format_empty_results_for_llm(self):
        """Test formatting empty results for LLM consumption."""
        injector = ProactiveSearchInjection()

        formatted = injector.format_for_llm([])

        assert isinstance(formatted, str)
        # Should handle empty list with a message
        assert len(formatted) > 0

    def test_get_injection_context_with_results(self, mock_search_handler):
        """Test getting complete injection context with results."""
        injector = ProactiveSearchInjection()

        with patch(
            "yt_fts.core.search.SearchHandler",
            return_value=mock_search_handler,
        ):
            context = injector.get_injection_context("machine learning", scope="all")

            assert context["should_inject"] is True
            assert context["intent"] == "search"
            assert context["results"] is not None
            assert len(context["results"]) > 0
            assert context["formatted_for_llm"] is not None

    def test_get_injection_context_without_results(self):
        """Test getting injection context when search returns no results."""
        injector = ProactiveSearchInjection()

        mock_handler = Mock()
        mock_handler.res = []

        with patch(
            "yt_fts.core.search.SearchHandler",
            return_value=mock_handler,
        ):
            context = injector.get_injection_context("obscure topic xyz", scope="all")

            assert context["should_inject"] is True
            assert context["intent"] == "search"
            assert context["results"] == []
            # Should have formatted output even if empty
            assert context["formatted_for_llm"] is not None

    def test_get_injection_context_no_injection_needed(self):
        """Test getting injection context when search should not be injected."""
        injector = ProactiveSearchInjection()

        context = injector.get_injection_context("hello there", scope="all")

        assert context["should_inject"] is False
        assert context["intent"] == "chat"
        assert context["results"] is None
        assert context["formatted_for_llm"] is None

    def test_format_results_with_limit(self, mock_search_handler):
        """Test that formatted results respect the limit parameter."""
        injector = ProactiveSearchInjection()

        # Add more results to test limiting
        mock_search_handler.res = [
            {
                "video_id": f"video{i}",
                "start_time": f"00:0{i}:23",
                "text": f"Text content {i}",
                "channel_name": "TestChannel",
                "video_title": f"Video {i}",
                "link": f"https://youtu.be/video{i}",
            }
            for i in range(10)
        ]

        formatted = injector.format_for_llm(mock_search_handler.res, max_results=5)

        # Should only include top 5 results
        assert "video0" in formatted
        assert "video4" in formatted
        assert "video5" not in formatted


@pytest.mark.integration
class TestProactiveSearchIntegration:
    """Integration tests for proactive search with actual database."""

    def test_proactive_search_integration(self):
        """Test end-to-end proactive search flow."""
        injector = ProactiveSearchInjection()

        # Detect intent
        query = "What is machine learning?"
        intent = injector.detect_intent(query)
        assert intent == "search"

        # Check if should inject
        should_inject = injector.should_inject(query)
        assert should_inject is True

        # Note: Actual search execution requires test database
        # This is tested separately in database integration tests

    def test_conversational_query_no_injection(self):
        """Test that conversational queries don't trigger search."""
        injector = ProactiveSearchInjection()

        query = "hello, how are you?"
        intent = injector.detect_intent(query)
        assert intent == "chat"

        should_inject = injector.should_inject(query)
        assert should_inject is False
