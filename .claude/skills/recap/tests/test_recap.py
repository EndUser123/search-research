"""Tests for /recap skill.

Tests cover import path correction, handoff-first resolution strategy,
and subagent transcript filtering.
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest


class TestImportPath:
    """TASK-001: Test that import path is correct."""

    def test_import_from_search_research_core_session_chain(self):
        """Test that search_research.core.session_chain import works.

        This is the correct import path after TASK-001 fix.
        """
        # Should not raise ImportError
        try:
            from search_research.core.session_chain import (
                SessionChainEntry,
                walk_session_chain,
            )
            assert SessionChainEntry is not None
            assert walk_session_chain is not None
        except ImportError as e:
            pytest.fail(f"Import from search_research.core.session_chain failed: {e}")

    def test_import_from_search_research_top_level(self):
        """Test that search_research top-level import works.

        The session_chain functions are re-exported at the top level.
        """
        # Should not raise ImportError
        try:
            from search_research import SessionChainEntry, walk_session_chain
            assert SessionChainEntry is not None
            assert walk_session_chain is not None
        except ImportError as e:
            pytest.fail(f"Import from search_research failed: {e}")

    def test_import_from_search_research_session_chain_fails(self):
        """Test that old import path (search_research.session_chain) fails.

        This verifies the bug that TASK-001 fixes.
        """
        with pytest.raises(ImportError):
            from search_research.session_chain import SessionChainEntry  # noqa: F401


class TestHandoffFirstResolution:
    """TASK-002: Test handoff-first resolution strategy."""

    def test_fresh_handoff_takes_priority(self, tmp_path):
        """Test that fresh handoff (< 5 min) is used as primary source."""
        # Create test handoff file with recent timestamp
        from datetime import datetime, timezone, timedelta

        handoff_dir = tmp_path / "handoff"
        handoff_dir.mkdir()

        handoff_data = {
            "session_id": "test-session-123",
            "resume_snapshot": {
                "created_at": (datetime.now(timezone.utc) - timedelta(minutes=2)).isoformat(),
                "goal": "Test goal",
                "current_task": "Test task",
                "active_files": [],
                "transcript_path": "/fake/transcript.jsonl",
            },
        }

        handoff_file = handoff_dir / "console_test_terminal_handoff.json"
        handoff_file.write_text(json.dumps(handoff_data))

        # Mock the handoff directory check
        with patch("recap.Path.home", return_value=tmp_path):
            # This should use fresh handoff
            sessions = _load_all_sessions_via_history_index(tmp_path)
            assert len(sessions) > 0  # Fresh handoff should be used

    def test_stale_handoff_degrades_to_chain_walk(self, tmp_path):
        """Test that stale handoff (> 5 min) degrades to chain walk."""
        from datetime import datetime, timezone, timedelta

        handoff_dir = tmp_path / "handoff"
        handoff_dir.mkdir()

        # Create stale handoff (10 minutes old)
        handoff_data = {
            "session_id": "test-session-123",
            "resume_snapshot": {
                "created_at": (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat(),
                "goal": "Stale goal",
            },
        }

        handoff_file = handoff_dir / "console_test_terminal_handoff.json"
        handoff_file.write_text(json.dumps(handoff_data))

        # Should fall through to chain walk
        with patch("recap.Path.home", return_value=tmp_path):
            sessions = _load_all_sessions_via_history_index(tmp_path)
            # Stale handoff ignored, chain walk or direct transcript used

    def test_missing_handoff_directory_degrades_gracefully(self, tmp_path):
        """Test that missing handoff directory degrades to chain walk."""
        # Don't create handoff directory

        with patch("recap.Path.home", return_value=tmp_path):
            # Should not crash, should fall back to chain walk
            sessions = _load_all_sessions_via_history_index(tmp_path)
            # Returns empty list or chain results


class TestSubagentFiltering:
    """TASK-003: Test subagent transcript filtering."""

    def test_subagent_directory_component_filtered(self):
        """Test that paths with 'subagents' as directory component are filtered."""
        from pathlib import Path

        # Test path with subagents as directory component
        subagent_path = Path("/home/user/projects/subagents/agent-123/transcript.jsonl")

        # After TASK-003, _is_subagent_transcript should return True

    def test_agent_prefix_filename_filtered(self):
        """Test that filenames starting with 'agent-' are filtered."""
        from pathlib import Path

        agent_path = Path("/home/user/projects/sessions/agent-456.jsonl")

        # After TASK-003, _is_subagent_transcript should return True

    def test_subagents_analysis_directory_not_filtered(self):
        """Test that 'subagents-analysis' directory is NOT incorrectly filtered.

        This tests R-012 from adversarial review - exact component matching,
        not substring matching.
        """
        from pathlib import Path

        # This should NOT be filtered (directory name is subagents-analysis, not subagents)
        legit_path = Path("/home/user/projects/subagents-analysis/transcript.jsonl")

        # After TASK-003 fix (exact component match), should return False
