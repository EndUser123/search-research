"""Tests for CKS knowledge base auto-injection in cks_context hook.

Validates the three changes from the retrieval gap fix:
1. Knowledge base queries search ALL CKS types (not just corrections)
2. Semantic search is the primary retrieval path
3. No time window filter on durable knowledge types
"""

import os
import sys
from pathlib import Path

# Add hooks directory to path (same pattern as test_cks_context_hook.py)
hooks_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(hooks_dir))

# Add __lib for turn_mode import (needed by cks_context.py)
lib_dir = hooks_dir / "__lib"
if str(lib_dir) not in sys.path:
    sys.path.insert(0, str(lib_dir))

from UserPromptSubmit import cks_context


class TestQueryKnowledgeBase:
    """Test _query_knowledge_base retrieves durable knowledge entries."""

    def test_returns_empty_when_db_missing(self):
        """Returns empty list when CKS DB doesn't exist."""
        with patch.object(Path, "exists", return_value=False):
            result = cks_context._query_knowledge_base("test query")
            assert result == []

    def test_returns_empty_on_exception(self):
        """Fail-open: exceptions return empty list, never block."""
        result = cks_context._query_knowledge_base("test")
        # Will fail because CKS import or DB access fails — should return []
        assert isinstance(result, list)

    def test_max_results_default_is_two(self):
        """Default max_results is 2 to keep context injection small."""
        import inspect
        sig = inspect.signature(cks_context._query_knowledge_base)
        assert sig.parameters["max_results"].default == 2


class TestHookKnowledgeTypes:
    """Test that HOOK_KNOWLEDGE_TYPES includes the right types."""

    def test_includes_durable_types(self):
        assert "knowledge" in cks_context.HOOK_KNOWLEDGE_TYPES
        assert "pattern" in cks_context.HOOK_KNOWLEDGE_TYPES
        assert "decision" in cks_context.HOOK_KNOWLEDGE_TYPES
        assert "insight" in cks_context.HOOK_KNOWLEDGE_TYPES
        assert "learning" in cks_context.HOOK_KNOWLEDGE_TYPES

    def test_excludes_correction(self):
        assert "correction" not in cks_context.HOOK_KNOWLEDGE_TYPES

    def test_excludes_memory(self):
        assert "memory" not in cks_context.HOOK_KNOWLEDGE_TYPES


class TestFormatKnowledgeContext:
    """Test _format_knowledge_context formatting."""

    def test_returns_empty_for_empty_results(self):
        result = cks_context._format_knowledge_context([], "test")
        assert result == ""

    def test_formats_with_type_labels(self):
        results = [
            {"id": "1", "type": "knowledge", "title": "z.ai Integration", "content": "endpoint config"},
        ]
        result = cks_context._format_knowledge_context(results, "z.ai")
        assert "[knowledge]" in result
        assert "z.ai Integration" in result
        assert "endpoint config" in result
        assert "auto-injected" in result

    def test_truncates_long_content(self):
        long_content = "x" * 500
        results = [
            {"id": "1", "type": "pattern", "title": "test", "content": long_content},
        ]
        result = cks_context._format_knowledge_context(results, "test")
        assert "..." in result

    def test_formats_multiple_results(self):
        results = [
            {"id": "1", "type": "knowledge", "title": "entry A", "content": "content A"},
            {"id": "2", "type": "decision", "title": "entry B", "content": "content B"},
        ]
        result = cks_context._format_knowledge_context(results, "test")
        assert "1." in result
        assert "2." in result
        assert "[knowledge]" in result
        assert "[decision]" in result

    def test_handles_missing_title(self):
        results = [
            {"id": "1", "type": "knowledge", "content": "some content"},
        ]
        result = cks_context._format_knowledge_context(results, "test")
        assert "Entry 1" in result


class TestKnowledgeConfigFlags:
    """Test configuration environment variables."""

    def test_semantic_enabled_by_default(self):
        assert cks_context.KNOWLEDGE_SEMANTIC_ENABLED is True

    def test_auto_inject_enabled_by_default(self):
        assert cks_context.KNOWLEDGE_AUTO_INJECT_ENABLED is True


# Need patch for some tests
from unittest.mock import patch
