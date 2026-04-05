#!/usr/bin/env python3
"""
Tests for scope_inference.py module.

Tests multi-terminal safe scope inference without git or TTL.
"""

import pytest
import sys
from pathlib import Path

# Add scripts directory to path
SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from scope_inference import (
    ScopeInference,
    get_terminal_id,
    infer_from_chat_context,
    infer_from_session_ledger,
    infer_scope,
    format_prompt_for_user,
)


class TestTerminalId:
    """Test terminal ID generation."""

    def test_terminal_id_returns_string(self):
        """Terminal ID should always be a string."""
        tid = get_terminal_id()
        assert isinstance(tid, str)
        assert len(tid) > 0

    def test_terminal_id_is_consistent(self):
        """Terminal ID should be consistent within session."""
        tid1 = get_terminal_id()
        tid2 = get_terminal_id()
        assert tid1 == tid2


class TestInferFromChatContext:
    """Test chat context scope inference."""

    def test_empty_tool_calls_returns_low_confidence(self):
        """No tool calls should return low confidence inference."""
        result = infer_from_chat_context(recent_tool_calls=[])
        assert result.source == "chat_context"
        assert result.confidence == "low"
        assert result.paths == []

    def test_none_tool_calls_returns_low_confidence(self):
        """None tool calls should return low confidence inference."""
        result = infer_from_chat_context(recent_tool_calls=None)
        assert result.source == "chat_context"
        assert result.confidence == "low"
        assert result.paths == []

    def test_single_file_read_returns_medium_confidence(self):
        """Single file operation should return medium confidence."""
        tool_calls = [
            {"tool_name": "Read", "tool_input": {"path": "src/auth.py"}},
        ]
        result = infer_from_chat_context(recent_tool_calls=tool_calls)
        assert result.source == "chat_context"
        assert result.confidence == "medium"
        # Should return the parent directory
        assert any("src" in p for p in result.paths)

    def test_multiple_files_same_dir_returns_high_confidence(self):
        """Multiple files in same directory should return high confidence."""
        tool_calls = [
            {"tool_name": "Read", "tool_input": {"path": "src/auth/login.py"}},
            {"tool_name": "Edit", "tool_input": {"path": "src/auth/logout.py"}},
            {"tool_name": "Write", "tool_input": {"path": "src/auth/session.py"}},
        ]
        result = infer_from_chat_context(recent_tool_calls=tool_calls)
        assert result.source == "chat_context"
        assert result.confidence == "high"
        assert len(result.paths) == 1
        # Normalize path separators for cross-platform compatibility
        assert result.paths[0].replace("\\", "/") == "src/auth"

    def test_glob_pattern_infers_directory(self):
        """Glob patterns should extract directory."""
        tool_calls = [
            {"tool_name": "Glob", "tool_input": {"pattern": "src/**/*.py"}},
        ]
        result = infer_from_chat_context(recent_tool_calls=tool_calls)
        assert result.source == "chat_context"
        assert len(result.paths) > 0

    def test_grep_infers_directory(self):
        """Grep with path should infer directory."""
        tool_calls = [
            {"tool_name": "Grep", "tool_input": {"path": "hooks", "pattern": "test"}},
        ]
        result = infer_from_chat_context(recent_tool_calls=tool_calls)
        assert result.source == "chat_context"
        # Just check it returns something (path inference varies by platform)
        assert len(result.paths) > 0


class TestInferScope:
    """Test main infer_scope function."""

    def test_explicit_path_overrides_everything(self):
        """Explicit path should override all other inference."""
        result = infer_scope(
            explicit_path="custom/path/",
            recent_tool_calls=[
                {"tool_name": "Read", "tool_input": {"path": "other/path.py"}},
            ],
        )
        assert result.source == "explicit"
        assert result.paths == ["custom/path/"]
        assert result.confidence == "high"

    def test_explicit_path_none_falls_back_to_context(self):
        """No explicit path should fall back to context inference."""
        tool_calls = [
            {"tool_name": "Read", "tool_input": {"path": "src/test.py"}},
        ]
        result = infer_scope(explicit_path=None, recent_tool_calls=tool_calls)
        assert result.source == "chat_context"
        assert result.confidence == "medium"

    def test_no_context_returns_none(self):
        """No context available should return none source."""
        result = infer_scope(explicit_path=None, recent_tool_calls=[])
        assert result.source == "none"
        assert result.paths == []
        assert result.confidence == "low"

    def test_require_explicit_mode_ignores_context(self):
        """Require explicit mode should ignore context."""
        tool_calls = [
            {"tool_name": "Read", "tool_input": {"path": "src/test.py"}},
        ]
        result = infer_scope(
            explicit_path=None,
            recent_tool_calls=tool_calls,
            require_explicit=True,
        )
        assert result.source == "none"
        assert result.confidence == "low"


class TestFormatPrompt:
    """Test user prompt formatting."""

    def test_format_prompt_includes_inference_details(self):
        """Prompt should include inference details."""
        inference = ScopeInference(
            source="none",
            paths=[],
            confidence="low",
            reason="No files in context",
        )
        prompt = format_prompt_for_user(inference)
        assert "No clear scope" in prompt
        assert "none" in prompt
        assert "No files in context" in prompt

    def test_format_prompt_includes_options(self):
        """Prompt should include usage options."""
        inference = ScopeInference(
            source="none",
            paths=[],
            confidence="low",
            reason="test",
        )
        prompt = format_prompt_for_user(inference)
        assert "/p <path>" in prompt
        assert "/p all" in prompt
        assert "/p ." in prompt


class TestSessionLedgerIntegration:
    """Test integration with investigation-ledger."""

    def test_session_ledger_fallback(self):
        """Should fall back to session ledger when chat context is empty."""
        # This test verifies the import works and doesn't crash
        # Actual ledger testing would require setting up the ledger
        result = infer_from_session_ledger()
        # Should return something without crashing
        assert result is not None
        assert hasattr(result, "source")
        assert hasattr(result, "paths")
        assert hasattr(result, "confidence")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
