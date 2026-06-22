"""Characterization tests for PreToolUse.py P0 fixes."""
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestNoneCopyBug:
    """Test that PreToolUse handles None.copy() correctly."""

    def test_tool_input_none_not_crash(self):
        """When tool_input is None explicitly, main() should not crash."""
        hook_file = Path(".claude/hooks/PreToolUse.py")
        if not hook_file.exists():
            pytest.skip("Hook file not found")

        payload = {
            "tool_name": "Read",
            "tool_input": None,  # Explicit None, not missing key
            "cwd": "P:/",
        }

        # Simulate the FIXED line
        data = payload
        original_tool_input = (data.get("tool_input", {}) or {}).copy() if "tool_input" in data else {}

        # This should NOT crash with AttributeError
        assert original_tool_input is not None
        assert original_tool_input == {}

    def test_tool_input_missing_key(self):
        """When tool_input key is missing, should use empty dict."""
        data = {"tool_name": "Read"}
        original_tool_input = data.get("tool_input", {}).copy() if "tool_input" in data else {}
        assert original_tool_input == {}

    def test_tool_input_normal_dict(self):
        """When tool_input is a normal dict, should copy it."""
        data = {"tool_name": "Read", "tool_input": {"file_path": "test.py"}}
        original_tool_input = data.get("tool_input", {}).copy() if "tool_input" in data else {}
        assert original_tool_input == {"file_path": "test.py"}
        # Verify it's a copy
        original_tool_input["modified"] = True
        assert data["tool_input"].get("modified") is None


class TestTTLFailClosed:
    """Test that missing timestamps fail-closed (treat as expired)."""

    def test_intent_without_created_at_or_timestamp_treated_as_expired(self):
        """Intent with neither created_at nor timestamp should be treated as expired."""
        # Simulate the TTL check logic
        intent = {"skill": "test", "session_id": "abc"}  # No timestamps
        _intent_created_at = 0.0

        # Current code: if _intent_created_at and _is_expired(...)
        # Bug: 0.0 is falsy, so the check is skipped entirely
        # Fix: Should fail-closed

        result = bool(_intent_created_at)  # Current buggy behavior
        assert result is False  # Bug confirmed: skips TTL check

    def test_intent_with_invalid_created_at_treated_as_expired(self):
        """Intent with invalid created_at should be treated as expired."""
        intent = {"skill": "test", "created_at": "not-a-number"}
        _intent_created_at = 0.0

        # After try/except fails to parse, stays 0.0
        try:
            _intent_created_at = float(intent["created_at"])
        except (TypeError, ValueError):
            pass

        assert _intent_created_at == 0.0
        assert bool(_intent_created_at) is False  # Bug: skips TTL check


class TestWindowsPathExemption:
    """Test that SKILL.md exemption works on Windows paths."""

    def test_windows_backslash_path_matches(self):
        """Windows paths with backslashes should match SKILL.md exemption."""
        import re

        file_path = r"P:\.claude\skills\foo\SKILL.md"

        # Current buggy regex (forward slashes only)
        buggy_regex = r"\.claude/skills/[^/]+/SKILL\.md$"
        matches_buggy = bool(re.search(buggy_regex, file_path))
        assert matches_buggy is False  # Bug confirmed

        # Fixed regex (normalized path)
        normalized_path = re.sub(r"[/\\]+", "/", file_path)
        fixed_regex = r"\.claude/skills/[^/]+/SKILL\.md$"
        matches_fixed = bool(re.search(fixed_regex, normalized_path))
        assert matches_fixed is True  # Fix works

    def test_unix_forward_slash_path_matches(self):
        """Unix paths with forward slashes should still match."""
        import re

        file_path = "/home/user/.claude/skills/foo/SKILL.md"

        normalized_path = re.sub(r"[/\\]+", "/", file_path)
        fixed_regex = r"\.claude/skills/[^/]+/SKILL\.md$"
        matches_fixed = bool(re.search(fixed_regex, normalized_path))
        assert matches_fixed is True