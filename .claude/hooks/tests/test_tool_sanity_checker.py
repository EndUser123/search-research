"""Tests for tool_sanity_checker gate in Stop.py."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure hooks dir is on path
_HOOKS_DIR = Path(__file__).resolve().parent.parent
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))


def _run_sanity(data: dict) -> dict | None:
    """Import and call _run_tool_sanity_check from Stop.py."""
    # Force fresh module reload to get current state
    import importlib

    import Stop
    importlib.reload(Stop)
    # Reset global state before test
    Stop._turn_bash_count = 0
    Stop._turn_edit_paths.clear()
    Stop._turn_high_risk_bash.clear()
    return Stop._run_tool_sanity_check(data)


class TestBashThreshold:
    """Warn when Bash calls exceed threshold."""

    def test_no_warning_under_threshold(self):
        """3 Bash calls should not warn."""
        data = {
            "tool_events": [
                {"name": "Bash", "input": {"command": "echo 1"}},
                {"name": "Bash", "input": {"command": "echo 2"}},
                {"name": "Bash", "input": {"command": "echo 3"}},
            ]
        }
        result = _run_sanity(data)
        assert result is None, f"Expected None under threshold, got {result}"

    def test_warning_over_threshold(self):
        """4 Bash calls should warn."""
        data = {
            "tool_events": [
                {"name": "Bash", "input": {"command": "echo 1"}},
                {"name": "Bash", "input": {"command": "echo 2"}},
                {"name": "Bash", "input": {"command": "echo 3"}},
                {"name": "Bash", "input": {"command": "echo 4"}},
            ]
        }
        result = _run_sanity(data)
        assert result is not None
        assert result["decision"] == "allow"
        assert "High Bash usage" in result["systemMessage"]
        assert "4 calls" in result["systemMessage"]

    def test_warning_at_threshold_exactly(self):
        """Exactly 3 calls should not warn."""
        data = {
            "tool_events": [
                {"name": "Bash", "input": {"command": "echo 1"}},
                {"name": "Bash", "input": {"command": "echo 2"}},
                {"name": "Bash", "input": {"command": "echo 3"}},
            ]
        }
        result = _run_sanity(data)
        assert result is None


class TestRepeatedEdits:
    """Warn when same file edited multiple times."""

    def test_two_edits_same_file_no_warning(self):
        """2 edits to same file should not warn."""
        data = {
            "tool_events": [
                {"name": "Edit", "input": {"file_path": "foo.py"}},
                {"name": "Edit", "input": {"file_path": "foo.py"}},
            ]
        }
        result = _run_sanity(data)
        assert result is None

    def test_three_edits_same_file_warns(self):
        """3 edits to same file should warn."""
        data = {
            "tool_events": [
                {"name": "Edit", "input": {"file_path": "foo.py"}},
                {"name": "Edit", "input": {"file_path": "foo.py"}},
                {"name": "Edit", "input": {"file_path": "foo.py"}},
            ]
        }
        result = _run_sanity(data)
        assert result is not None
        assert result["decision"] == "allow"
        assert "Repeated edits" in result["systemMessage"]
        assert "foo.py" in result["systemMessage"]

    def test_different_files_no_warning(self):
        """Different files should not trigger repeated edit warning."""
        data = {
            "tool_events": [
                {"name": "Edit", "input": {"file_path": "foo.py"}},
                {"name": "Edit", "input": {"file_path": "bar.py"}},
                {"name": "Edit", "input": {"file_path": "baz.py"}},
            ]
        }
        result = _run_sanity(data)
        assert result is None


class TestHighRiskBash:
    """Warn on high-risk Bash commands."""

    def test_rm_rf_warns(self):
        """rm -rf should trigger warning."""
        data = {
            "tool_events": [
                {"name": "Bash", "input": {"command": "rm -rf /tmp/test"}},
            ]
        }
        result = _run_sanity(data)
        assert result is not None
        assert "High-risk Bash commands" in result["systemMessage"]
        assert "rm -rf" in result["systemMessage"]

    def test_git_reset_hard_warns(self):
        """git reset --hard should trigger warning."""
        data = {
            "tool_events": [
                {"name": "Bash", "input": {"command": "git reset --hard HEAD~1"}},
            ]
        }
        result = _run_sanity(data)
        assert result is not None
        assert "git reset --hard" in result["systemMessage"]

    def test_git_clean_fd_warns(self):
        """git clean -fd should trigger warning."""
        data = {
            "tool_events": [
                {"name": "Bash", "input": {"command": "git clean -fd"}},
            ]
        }
        result = _run_sanity(data)
        assert result is not None
        assert "git clean -fd" in result["systemMessage"]

    def test_git_restore_is_safe(self):
        """git restore is a recovery command, should NOT trigger high-risk warning."""
        data = {
            "tool_events": [
                {"name": "Bash", "input": {"command": "git restore foo.py"}},
            ]
        }
        result = _run_sanity(data)
        # git restore alone should not warn about high-risk
        if result:
            assert "rm -rf" not in result["systemMessage"]
            assert "git reset --hard" not in result["systemMessage"]

    def test_git_checkout_head_safe(self):
        """git checkout HEAD is recovery, not high-risk."""
        data = {
            "tool_events": [
                {"name": "Bash", "input": {"command": "git checkout HEAD -- foo.py"}},
            ]
        }
        result = _run_sanity(data)
        if result:
            assert "git reset --hard" not in result["systemMessage"]


class TestCombinedWarnings:
    """Multiple warning types combined."""

    def test_many_bash_and_high_risk_combined(self):
        """Both high Bash count and high-risk command should both appear."""
        data = {
            "tool_events": [
                {"name": "Bash", "input": {"command": "echo 1"}},
                {"name": "Bash", "input": {"command": "echo 2"}},
                {"name": "Bash", "input": {"command": "echo 3"}},
                {"name": "Bash", "input": {"command": "echo 4"}},
                {"name": "Bash", "input": {"command": "rm -rf /tmp/test"}},
            ]
        }
        result = _run_sanity(data)
        assert result is not None
        msg = result["systemMessage"]
        assert "High Bash usage" in msg
        assert "rm -rf" in msg


class TestEmptyOrMinimal:
    """Edge cases."""

    def test_empty_tool_events(self):
        """No tool events should produce no warning."""
        data = {"tool_events": []}
        result = _run_sanity(data)
        assert result is None

    def test_no_tool_events_key(self):
        """Missing tool_events key should not crash."""
        data = {}
        result = _run_sanity(data)
        assert result is None

    def test_read_and_grep_no_warning(self):
        """Read/Grep/Glob should not count toward any counters."""
        data = {
            "tool_events": [
                {"name": "Read", "input": {"file_path": "foo.py"}},
                {"name": "Grep", "input": {"pattern": "def foo"}},
                {"name": "Glob", "input": {"pattern": "**/*.py"}},
            ]
        }
        result = _run_sanity(data)
        assert result is None
