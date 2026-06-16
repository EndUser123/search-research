"""Tests for domain tool router hook."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add hooks to path for testing
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class TestDomainToolRouter:
    """Tests for PreToolUse_domain_tool_router.py hook."""

    @pytest.fixture
    def hook_module(self):
        """Import the hook module."""
        import PreToolUse_domain_tool_router as hook

        return hook

    def test_chat_history_detection(self, hook_module):
        """Test chat history query detection."""
        # Chat history patterns
        chat_queries = [
            "we discussed authentication earlier",
            "what did we say about CHS",
            "you mentioned something about FAISS",
            "recent changes to search skill",
        ]
        for query in chat_queries:
            result = hook_module.classify_query(query)
            assert result == "chat", f"Query should be classified as 'chat': {query}"

    def test_web_source_detection(self, hook_module):
        """Test web source/documentation query detection."""
        web_queries = [
            "how does FAISS work",
            "python async patterns documentation",
            "the search skill documentation",
        ]
        for query in web_queries:
            result = hook_module.classify_query(query)
            assert result == "web", f"Query should be classified as 'web': {query}"

    def test_knowledge_detection(self, hook_module):
        """Test knowledge base query detection."""
        knowledge_queries = [
            "best practice for caching",
            "design pattern for authentication",
            "rationale behind this decision",
        ]
        for query in knowledge_queries:
            result = hook_module.classify_query(query)
            assert result == "knowledge", f"Query should be classified as 'knowledge': {query}"

    def test_combined_search_detection(self, hook_module):
        """Test combined multi-source query detection."""
        # The combined pattern requires "versus/compare" or "evolved over"
        combined_queries = [
            "compare FAISS vs chroma",
            "FAISS versus chroma",
            "how our approach evolved over time",
            "verify documentation against implementation",
        ]
        for query in combined_queries:
            result = hook_module.classify_query(query)
            assert result == "combined", f"Query should be classified as 'combined': {query}"

    def test_no_classification(self, hook_module):
        """Test queries that don't match any pattern."""
        neutral_queries = [
            "hello world",
            "test command",
            "list files",
        ]
        for query in neutral_queries:
            result = hook_module.classify_query(query)
            assert result is None, f"Query should not be classified: {query}"

    def test_extract_query_from_bash(self, hook_module):
        """Test query extraction from Bash tool input."""
        tool_input = {"command": "grep -r 'pattern' src/"}
        query = hook_module.extract_query("Bash", tool_input)
        assert "grep" in query or "pattern" in query

    def test_extract_query_from_grep(self, hook_module):
        """Test query extraction from Grep tool input."""
        tool_input = {"pattern": "async def"}
        query = hook_module.extract_query("Grep", tool_input)
        assert query == "async def"

    def test_build_suggestion(self, hook_module):
        """Test suggestion message building."""
        suggestion = hook_module.build_suggestion("chat", "we discussed auth")
        assert "/search" in suggestion
        assert "--source chat" in suggestion
        assert "auth" in suggestion

    def test_hook_allows_without_suggestion(self, hook_module):
        """Test hook allows tools without suggestion for neutral queries."""
        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": "ls -la"},
        }
        # Test the classification logic directly
        query = hook_module.extract_query("Bash", input_data)
        classification = hook_module.classify_query(query)
        assert classification is None  # No suggestion for neutral queries

    def test_hook_advisory_for_chat_query(self, hook_module):
        """Test hook provides advisory for chat history query."""
        tool_name = "Bash"
        tool_input = {"command": "grep 'we discussed' file.txt"}
        # Test the classification logic directly
        query = hook_module.extract_query(tool_name, tool_input)
        classification = hook_module.classify_query(query)
        assert classification == "chat"  # Should detect chat history intent
        suggestion = hook_module.build_suggestion(classification, query)
        assert "/search" in suggestion
        assert "--source chat" in suggestion
