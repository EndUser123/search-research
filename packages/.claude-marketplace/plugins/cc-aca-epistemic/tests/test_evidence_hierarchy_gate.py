"""Tests for PreToolUse_evidence_hierarchy_gate hook."""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import pytest

# Setup path to find PreToolUse_evidence_hierarchy_gate.py and artifact_ledger
PLUGIN_ROOT = Path(__file__).resolve().parents[1]
pretool_path = PLUGIN_ROOT / "hooks" / "pretool"
if str(pretool_path) not in sys.path:
    sys.path.insert(0, str(pretool_path))

# Resolve global hooks __lib/ dynamically and add to sys.path
global_hooks_lib = PLUGIN_ROOT.parents[3] / ".claude" / "hooks" / "__lib"
if str(global_hooks_lib) not in sys.path:
    sys.path.insert(0, str(global_hooks_lib))

from artifact_ledger import record, load
import PreToolUse_evidence_hierarchy_gate as gate


@pytest.fixture
def mock_ledger_dir(monkeypatch):
    """Mock LEDGER_DIR for clean tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        import artifact_ledger as al
        monkeypatch.setattr(al, "LEDGER_DIR", Path(tmpdir))
        yield Path(tmpdir)


class TestEvidenceHierarchyGate:
    """Test evidence hierarchy enforcement gate."""

    def test_allow_no_session_id(self, mock_ledger_dir):
        """Gate returns None (allow) if no session_id."""
        data = {"tool_name": "WebFetch", "tool_input": {"url": "https://example.com"}}
        result = gate.run(data)
        assert result is None

    def test_allow_non_external_tool(self, mock_ledger_dir):
        """Gate returns None (allow) for non-external tools."""
        data = {
            "session_id": "sess-1",
            "tool_name": "Read",
            "tool_input": {"file_path": "file.py"},
        }
        result = gate.run(data)
        assert result is None

    def test_allow_empty_query(self, mock_ledger_dir):
        """Gate returns None (allow) if query is empty."""
        data = {
            "session_id": "sess-1",
            "tool_name": "Bash",
            "tool_input": {"command": "echo hello"},
        }
        result = gate.run(data)
        assert result is None

    def test_block_webfetch_with_local_evidence(self, mock_ledger_dir):
        """Block WebFetch when local evidence exists."""
        # Record a local finding
        record("sess-1", "sqd", "src/skill.py", 3)

        # Try to fetch same topic
        data = {
            "session_id": "sess-1",
            "tool_name": "WebFetch",
            "tool_input": {
                "url": "https://example.com/sqd",
                "query": "sqd skill",
            },
        }

        result = gate.run(data)
        assert result is not None
        assert result["decision"] == "block"
        assert "sqd" in result["reason"]

    def test_block_bash_npm_install_with_evidence(self, mock_ledger_dir):
        """Block 'npm install' when local evidence exists."""
        record("sess-1", "package", "package.json", 2)

        data = {
            "session_id": "sess-1",
            "tool_name": "Bash",
            "tool_input": {"command": "npm install @scope/package"},
        }

        result = gate.run(data)
        assert result is not None
        assert result["decision"] == "block"

    def test_allow_with_bypass_env_var(self, mock_ledger_dir, monkeypatch):
        """Env var bypass allows action despite local evidence."""
        record("sess-1", "sqd", "src/skill.py", 1)
        monkeypatch.setenv("IGNORE_LOCAL_EVIDENCE", "1")

        data = {
            "session_id": "sess-1",
            "tool_name": "WebFetch",
            "tool_input": {"url": "https://example.com/sqd"},
        }

        result = gate.run(data)
        assert result is None

    def test_allow_no_matching_evidence(self, mock_ledger_dir):
        """Allow fetch when no local evidence for topic."""
        record("sess-1", "other", "file.py", 1)

        data = {
            "session_id": "sess-1",
            "tool_name": "WebFetch",
            "tool_input": {"url": "https://example.com/unrelated"},
        }

        result = gate.run(data)
        assert result is None

    def test_extract_query_webfetch(self, mock_ledger_dir):
        """Extract query from WebFetch input."""
        query = gate._extract_query({
            "tool_name": "WebFetch",
            "tool_input": {"url": "http://example.com", "query": "search term"},
        })
        assert "example.com" in query
        assert "search term" in query

    def test_extract_query_websearch(self, mock_ledger_dir):
        """Extract query from WebSearch input."""
        query = gate._extract_query({
            "tool_name": "WebSearch",
            "tool_input": {"query": "my search"},
        })
        assert "my search" in query

    def test_extract_query_bash_curl(self, mock_ledger_dir):
        """Extract query from Bash curl command."""
        query = gate._extract_query({
            "tool_name": "Bash",
            "tool_input": {"command": "curl https://api.example.com/data"},
        })
        assert "curl https://api.example.com/data" in query

    def test_extract_query_bash_npm(self, mock_ledger_dir):
        """Extract query from Bash npm install."""
        query = gate._extract_query({
            "tool_name": "Bash",
            "tool_input": {"command": "npm install @scope/pkg"},
        })
        assert "npm install @scope/pkg" in query

    def test_extract_query_bash_pip(self, mock_ledger_dir):
        """Extract query from Bash pip install."""
        query = gate._extract_query({
            "tool_name": "Bash",
            "tool_input": {"command": "pip install package-name"},
        })
        assert "pip install package-name" in query

    def test_extract_query_bash_non_external(self, mock_ledger_dir):
        """Non-external bash commands return empty query."""
        query = gate._extract_query({
            "tool_name": "Bash",
            "tool_input": {"command": "ls -la"},
        })
        assert query == ""

    def test_get_session_id_from_data(self, mock_ledger_dir):
        """Extract session_id from hook data."""
        sid = gate._get_session_id({"session_id": "sess-abc"})
        assert sid == "sess-abc"

    def test_get_session_id_from_env(self, mock_ledger_dir, monkeypatch):
        """Fallback to env var if session_id missing."""
        monkeypatch.setenv("CLAUDE_SESSION_ID", "env-sess-123")
        sid = gate._get_session_id({})
        assert sid == "env-sess-123"

    def test_get_session_id_none(self, mock_ledger_dir):
        """Return None if session_id unavailable."""
        sid = gate._get_session_id({})
        assert sid is None

    def test_block_message_quality(self, mock_ledger_dir):
        """Block message contains required information."""
        record("sess-1", "sqd", "src/sqd_skill.py", 2)

        data = {
            "session_id": "sess-1",
            "tool_name": "WebFetch",
            "tool_input": {"url": "https://registry.com/sqd"},
        }

        result = gate.run(data)
        msg = result["reason"]
        assert "EVIDENCE HIERARCHY" in msg
        assert "sqd" in msg
        assert "src/sqd_skill.py" in msg
        assert "--ignore-local-evidence" in msg

    def test_multiple_matches_shown(self, mock_ledger_dir):
        """Show up to 3 matching entries in block message."""
        record("sess-1", "test", "file1.py", 1)
        record("sess-1", "test", "file2.py", 2)
        record("sess-1", "test", "file3.py", 3)
        record("sess-1", "test", "file4.py", 4)

        data = {
            "session_id": "sess-1",
            "tool_name": "WebFetch",
            "tool_input": {"url": "https://test.com"},
        }

        result = gate.run(data)
        msg = result["reason"]
        # Should show first 3 matches
        assert "file1.py" in msg
        assert "file2.py" in msg
        assert "file3.py" in msg
        assert "file4.py" not in msg  # 4th match not shown
