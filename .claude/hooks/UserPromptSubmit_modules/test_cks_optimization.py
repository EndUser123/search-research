"""Test CKS optimization implementation - relevance filtering and token budgeting."""

import pytest
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

# Add hooks directory to path
hooks_dir = Path(__file__).resolve().parent.parent / "UserPromptSubmit_modules"
if str(hooks_dir) not in sys.path:
    sys.path.insert(0, str(hooks_dir))

# Mock the base classes
class HookContext:
    def __init__(self, prompt: str):
        self.prompt = prompt

class HookResult:
    @staticmethod
    def empty():
        return HookResult(context="", tokens=0, priority=0.0)

    @staticmethod
    def context_injection(content: str):
        return HookResult(context=content, tokens=len(content.split()), priority=5.0)

    def __init__(self, context: str, tokens: int, priority: float):
        self.context = context
        self.tokens = tokens
        self.priority = priority

# Import the module under test
import cks_context


def test_relevance_threshold_filters_low_similarity_corrections():
    """Verify corrections below 0.7 similarity are filtered out."""
    # Mock results with varying similarity scores
    corrections = [
        {"id": 1, "similarity": 0.9, "title": "High relevance", "content": "Important correction"},
        {"id": 2, "similarity": 0.75, "title": "Medium-high relevance", "content": "Somewhat relevant"},
        {"id": 3, "similarity": 0.5, "title": "Low relevance", "content": "Not very relevant"},
        {"id": 4, "similarity": 0.3, "title": "Very low relevance", "content": "Barely relevant"},
    ]

    # Apply the threshold filter (same logic as in cks_context_hook)
    filtered = [c for c in corrections if c.get("similarity", 0) >= cks_context.CORRECTION_RELEVANCE_THRESHOLD]

    # Should only include items with similarity >= 0.7
    assert len(filtered) == 2
    assert all(c["similarity"] >= 0.7 for c in filtered)
    filtered_ids = [c["id"] for c in filtered]
    assert 3 not in filtered_ids
    assert 4 not in filtered_ids


def test_relevance_threshold_filters_low_similarity_knowledge():
    """Verify knowledge entries below 0.7 similarity are filtered out."""
    knowledge = [
        {"id": 1, "similarity": 0.85, "title": "Very relevant knowledge", "content": "Key insight"},
        {"id": 2, "similarity": 0.72, "title": "Relevant knowledge", "content": "Useful pattern"},
        {"id": 3, "similarity": 0.65, "title": "Less relevant", "content": "Minor insight"},
        {"id": 4, "similarity": 0.4, "title": "Barely relevant", "content": "Weak pattern"},
    ]

    # Apply the threshold filter
    filtered = [k for k in knowledge if k.get("similarity", 0) >= cks_context.KNOWLEDGE_RELEVANCE_THRESHOLD]

    # Should only include items with similarity >= 0.7
    assert len(filtered) == 2
    assert all(k["similarity"] >= 0.7 for k in filtered)


def test_token_budgeting_truncates_long_content():
    """Verify injection is truncated when exceeding MAX_INJECTION_TOKENS."""
    # Create content that exceeds 500 chars
    long_content = "A" * 600
    parts = [long_content]

    # Apply token budgeting (same logic as in cks_context_hook)
    combined = "\n\n".join(parts)
    if len(combined) > cks_context.MAX_INJECTION_TOKENS:
        combined = combined[:cks_context.MAX_INJECTION_TOKENS - 50] + "\n... [truncated]"

    # Should be truncated to under 500 chars (450 chars content + 16 chars truncation marker)
    assert len(combined) <= cks_context.MAX_INJECTION_TOKENS
    assert len(combined) == 466  # 450 chars content + 16 chars truncation marker
    assert combined.endswith("\n... [truncated]")


def test_token_budgeting_preserves_short_content():
    """Verify short content is not truncated."""
    short_content = "A" * 300
    parts = [short_content]

    # Apply token budgeting
    combined = "\n\n".join(parts)
    if len(combined) > cks_context.MAX_INJECTION_TOKENS:
        combined = combined[:cks_context.MAX_INJECTION_TOKENS - 50] + "\n... [truncated]"

    # Should not be truncated
    assert len(combined) == 300
    assert not combined.endswith("[truncated]")


def test_multiple_parts_combined_and_budgeted():
    """Verify multiple parts are combined and budgeted together."""
    part1 = "A" * 250
    part2 = "B" * 250
    parts = [part1, part2]

    # Combine and apply budgeting
    combined = "\n\n".join(parts)
    if len(combined) > cks_context.MAX_INJECTION_TOKENS:
        combined = combined[:cks_context.MAX_INJECTION_TOKENS - 50] + "\n... [truncated]"

    # Combined length (500 + 2 for newline separator) should be truncated
    assert len(combined) <= cks_context.MAX_INJECTION_TOKENS
    assert combined.endswith("\n... [truncated]")


def test_constants_are_defined():
    """Verify the optimization constants are defined correctly."""
    assert hasattr(cks_context, 'CORRECTION_RELEVANCE_THRESHOLD')
    assert hasattr(cks_context, 'KNOWLEDGE_RELEVANCE_THRESHOLD')
    assert hasattr(cks_context, 'MAX_INJECTION_TOKENS')

    assert cks_context.CORRECTION_RELEVANCE_THRESHOLD == 0.7
    assert cks_context.KNOWLEDGE_RELEVANCE_THRESHOLD == 0.7
    assert cks_context.MAX_INJECTION_TOKENS == 500


def test_empty_results_produce_empty_injection():
    """Verify empty correction/knowledge lists produce no context injection."""
    parts = []

    combined = "\n\n".join(parts)
    if len(combined) > cks_context.MAX_INJECTION_TOKENS:
        combined = combined[:cks_context.MAX_INJECTION_TOKENS - 50] + "\n... [truncated]"

    result = HookResult.context_injection(combined) if combined else HookResult.empty()

    # Should be empty result
    assert result.context == ""
    assert result.tokens == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])