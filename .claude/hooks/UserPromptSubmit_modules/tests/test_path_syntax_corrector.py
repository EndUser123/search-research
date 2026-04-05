"""Tests for path_syntax_corrector hook."""

import sys
from pathlib import Path

import pytest

# Add hooks directory to path
hooks_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(hooks_dir))

from UserPromptSubmit.base import HookContext  # noqa: E402
from UserPromptSubmit.path_syntax_corrector import (  # noqa: E402
    path_syntax_corrector,
)


class TestPathSyntaxCorrector:
    """Test path syntax detection and correction."""

    def test_no_path_errors_returns_empty(self):
        """Test that prompts without path errors return empty result."""
        context = HookContext(
            prompt="ls -la", data={"session_id": "test-session", "terminal_id": "test-terminal"}
        )
        result = path_syntax_corrector(context)
        assert result.is_empty()

    def test_windows_path_with_missing_backslashes_detected(self):
        """Test detection of Windows path missing backslashes (high confidence = auto-correct)."""
        context = HookContext(
            prompt="ls P:.claudehooksscannersmy_scanner.py",
            data={"session_id": "test-session", "terminal_id": "test-terminal"},
        )
        result = path_syntax_corrector(context)

        # Should NOT return empty (path error detected)
        assert not result.is_empty()
        assert isinstance(result.context, dict)
        # Should replace with corrected prompt (not just True)
        assert isinstance(result.context.get("replacePrompt"), str)
        assert "P:\\.claude\\hooks\\scanners" in result.context.get("replacePrompt", "")
        # High confidence path should auto-correct (not show choice UI)
        assert "Auto-corrected path" in result.context.get("additionalContext", "")

    def test_multiple_paths_detected(self):
        """Test detection of multiple malformed paths (high confidence = auto-correct)."""
        context = HookContext(
            prompt="ls P:.claudehooksscanner.py P:.claudehookstest.py",
            data={"session_id": "test-session", "terminal_id": "test-terminal"},
        )
        result = path_syntax_corrector(context)

        assert not result.is_empty()
        # High confidence paths should auto-correct with count
        assert "Auto-corrected" in result.context.get("additionalContext", "")

    def test_choice_response_zero_uses_corrected_path(self):
        """Test that choice '0' applies corrected path (low confidence = shows choice UI)."""
        # Use low-confidence path (no known dirs) to trigger choice UI
        context1 = HookContext(
            prompt="ls C:script.bat",
            data={"session_id": "test-session", "terminal_id": "test-terminal"},
        )
        result1 = path_syntax_corrector(context1)
        assert not result1.is_empty()
        # Low confidence should show choice UI
        assert "Action Required" in result1.context.get("additionalContext", "")

        # Then, simulate Turn 2 with choice "0"
        context2 = HookContext(
            prompt="0", data={"session_id": "test-session", "terminal_id": "test-terminal"}
        )
        result2 = path_syntax_corrector(context2)

        assert not result2.is_empty()
        assert isinstance(result2.context, dict)
        corrected_prompt = result2.context.get("additionalContext", "")
        # Should contain corrected path with backslash
        assert "C:\\script.bat" in corrected_prompt

    def test_choice_response_one_uses_original_path(self):
        """Test that choice '1' uses original (malformed) path (low confidence = shows choice UI)."""
        # Use low-confidence path (no known dirs) to trigger choice UI
        context1 = HookContext(
            prompt="ls C:script.bat",
            data={"session_id": "test-session-2", "terminal_id": "test-terminal-2"},
        )
        result1 = path_syntax_corrector(context1)
        assert not result1.is_empty()
        # Low confidence should show choice UI
        assert "Action Required" in result1.context.get("additionalContext", "")

        # Then, simulate Turn 2 with choice "1"
        context2 = HookContext(
            prompt="1", data={"session_id": "test-session-2", "terminal_id": "test-terminal-2"}
        )
        result2 = path_syntax_corrector(context2)

        assert not result2.is_empty()
        original_prompt = result2.context.get("additionalContext", "")
        # Should contain original malformed path
        assert "C:script.bat" in original_prompt

    def test_normalized_path_returns_empty(self):
        """Test that already-normalized paths return empty."""
        context = HookContext(
            prompt="ls P:\\.claude\\hooks\\test.py",
            data={"session_id": "test-session", "terminal_id": "test-terminal"},
        )
        result = path_syntax_corrector(context)
        # Path is already normalized (has backslashes)
        # normalize_path() should return same path, so no correction needed
        assert result.is_empty()

    def test_unix_paths_not_affected(self):
        """Test that Unix-style paths are not affected."""
        context = HookContext(
            prompt="ls /usr/local/bin/test",
            data={"session_id": "test-session", "terminal_id": "test-terminal"},
        )
        result = path_syntax_corrector(context)
        # Unix paths don't match Windows path pattern
        assert result.is_empty()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
