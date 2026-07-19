"""Tests for artifact_access_tracker (standalone, no Claude Code runtime).

These tests import the module directly via sys.path insertion and run
without any hook execution environment.  They verify that:
  - _extract_file_paths correctly parses tool inputs
  - track_tool_use writes correct JSONL entries
  - track_tool_use silently skips tools that access no files
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

# Add plugin __lib/ to path so that posttooluse.* modules resolve
PLUGIN_LIB = (
    Path(__file__).resolve().parent.parent / "__lib"
)
sys.path.insert(0, str(PLUGIN_LIB))

# Route hooks dir to a temp location so the module's STATE_DIR resolves
# under it (hooks_resolver.get_hooks_dir() -> CLAUDE_HOOKS_DIR -> /tmp/...).
_temp_hooks_dir = Path(tempfile.mkdtemp())
os.environ["CLAUDE_HOOKS_DIR"] = str(_temp_hooks_dir)
# Create .state/ dir because STATE_DIR is get_hooks_dir() / ".state"
_state_sub = _temp_hooks_dir / ".state"
_state_sub.mkdir(parents=True, exist_ok=True)

from posttooluse.artifact_access_tracker import (
    STATE_DIR,
    _extract_file_paths,
    track_tool_use,
)


# ---------------------------------------------------------------------------
# _extract_file_paths  (pure function, no side effects)
# ---------------------------------------------------------------------------

class TestExtractFilePaths:
    def test_read(self):
        result = _extract_file_paths("Read", {"file_path": "/a/b.py"})
        assert result == ["/a/b.py"]

        result = _extract_file_paths("Read", {})
        assert result == []

    def test_read_alternate_key(self):
        result = _extract_file_paths("read_file", {"path": "/x/y.txt"})
        assert result == ["/x/y.txt"]

    def test_grep(self):
        result = _extract_file_paths("Grep", {"path": "/search/root", "glob": "*.py"})
        assert "/search/root" in result
        assert "glob:*.py" in result

    def test_glob(self):
        result = _extract_file_paths("Glob", {"DirectoryPath": "/src", "pattern": "**/*.ts"})
        assert "/src" in result
        assert "pattern:**/*.ts" in result

    def test_bash_with_file_command(self):
        result = _extract_file_paths("Bash", {"command": "cat /etc/hostname"})
        assert any("/etc/hostname" in p for p in result)

    def test_bash_no_path(self):
        result = _extract_file_paths("Bash", {"command": "echo hello"})
        assert result == []

    def test_unknown_tool(self):
        result = _extract_file_paths("Skill", {})
        assert result == []


# ---------------------------------------------------------------------------
# track_tool_use  (integration-lite: writes JSONL to state dir)
# ---------------------------------------------------------------------------

class TestTrackToolUse:
    def _log_files(self) -> list[Path]:
        return sorted(STATE_DIR.glob("tool_use_log_*.jsonl"))

    def test_writes_log_entry(self):
        count_before = len(self._log_files())

        track_tool_use("sess-abc", "term-xyz", "Read", {"file_path": "/f.py"})

        logs = self._log_files()
        assert len(logs) == count_before + 1

        entry = json.loads(logs[-1].read_text(encoding="utf-8"))
        assert entry["session_id"] == "sess-abc"
        assert entry["terminal_id"] == "term-xyz"
        assert entry["tool"] == "Read"
        assert "/f.py" in entry["accessed"]

    def test_skips_tools_with_no_accessed_files(self):
        count_before = len(self._log_files())

        track_tool_use("sess-1", "term-1", "Bash", {"command": "echo no-op"})
        track_tool_use("sess-1", "term-1", "Skill", {})
        track_tool_use("sess-1", "term-1", "Read", {})

        assert len(self._log_files()) == count_before  # no new files

    def test_safe_terminal_id_log_path(self):
        track_tool_use("sess-x", "bad/ chars!", "Read", {"file_path": "/a.py"})

        logs = self._log_files()
        assert any("bad_chars_" in f.name for f in logs)

    def test_appends_to_existing_log(self):
        track_tool_use("s1", "t1", "Read", {"file_path": "/a.py"})
        track_tool_use("s1", "t1", "Read", {"file_path": "/b.py"})

        # Both entries should be in the same file
        term_logs = [f for f in self._log_files() if "t1" in f.name]
        assert len(term_logs) == 1

        lines = term_logs[0].read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) >= 2
