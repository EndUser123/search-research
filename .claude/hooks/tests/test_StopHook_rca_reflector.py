#!/usr/bin/env python3
"""Tests for StopHook_rca_reflector (TASK-003).

Covers:
  - Premature convergence: Root Cause present, hypothesis count < 3
  - Catch-22 spiral: same tool+error 3+ consecutive RCA turns
  - Evidence-free fix: Fix present, Evidence empty
  - Zero-plan: No Executed Path after 3+ tool calls
  - TTL cleanup on state load
  - Multi-terminal isolation
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class TestPrematureConvergence:
    """Tests for premature convergence detection."""

    def test_root_cause_with_one_hypothesis(self):
        """Root Cause + 1 hypothesis → premature convergence advisory."""
        from StopHook_rca_reflector import _detect_premature_convergence

        rc_text = "## Root Cause\nbug in auth.py"
        alt_count = 1
        result = _detect_premature_convergence(rc_text, alt_count)
        assert result is not None
        assert "hypotheses" in result.lower()

    def test_root_cause_with_three_hypotheses(self):
        """Root Cause + 3 hypotheses → no advisory."""
        from StopHook_rca_reflector import _detect_premature_convergence

        rc_text = "## Root Cause\nbug in auth.py"
        alt_count = 3
        result = _detect_premature_convergence(rc_text, alt_count)
        assert result is None

    def test_no_root_cause_no_advisory(self):
        """No Root Cause → no premature convergence advisory."""
        from StopHook_rca_reflector import _detect_premature_convergence

        rc_text = ""
        alt_count = 1
        result = _detect_premature_convergence(rc_text, alt_count)
        assert result is None


class TestCatch22Detection:
    """Tests for catch-22 spiral detection."""

    def test_three_same_tool_failures(self):
        """Same tool+error 3x → catch-22 advisory."""
        from StopHook_rca_reflector import _is_catch22_spiral

        # Simulate 3 consecutive same tool failure
        state = {
            "last_tool": "Bash",
            "last_error": "exit code 1",
            "consecutive_count": 3,
        }
        current_tool = "Bash"
        current_error = "exit code 1"
        result = _is_catch22_spiral(state, current_tool, current_error)
        assert result is True

    def test_different_tool_resets(self):
        """Different tool → reset, no catch-22."""
        from StopHook_rca_reflector import _is_catch22_spiral

        state = {
            "last_tool": "Bash",
            "last_error": "exit code 1",
            "consecutive_count": 3,
        }
        current_tool = "Read"
        current_error = "not found"
        result = _is_catch22_spiral(state, current_tool, current_error)
        assert result is False

    def test_different_error_same_tool(self):
        """Same tool different error → not catch-22."""
        from StopHook_rca_reflector import _is_catch22_spiral

        state = {
            "last_tool": "Bash",
            "last_error": "exit code 1",
            "consecutive_count": 2,
        }
        current_tool = "Bash"
        current_error = "different error"
        result = _is_catch22_spiral(state, current_tool, current_error)
        assert result is False


class TestEvidenceFreeFix:
    """Tests for evidence-free fix detection."""

    def test_fix_without_evidence(self):
        """Fix present, Evidence empty → advisory."""
        from StopHook_rca_reflector import _has_evidence_free_fix

        response = "## Fix\nupdate auth.py\n## Evidence\n"
        result = _has_evidence_free_fix(response)
        assert result is True

    def test_fix_with_evidence(self):
        """Fix present with Evidence → no advisory."""
        from StopHook_rca_reflector import _has_evidence_free_fix

        response = "## Fix\nupdate auth.py\n## Evidence\nread file.py:10"
        result = _has_evidence_free_fix(response)
        assert result is False


class TestTTLStateCleanup:
    """Tests for TTL-based state cleanup."""

    def test_stale_state_files_deleted(self):
        """State files older than 2 hours are deleted on load."""
        import tempfile
        import time

        from StopHook_rca_reflector import _cleanup_stale_state_files

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a stale state file (modified 3 hours ago)
            stale_file = Path(tmpdir) / "rca_reflector_console_abc_test.json"
            stale_file.write_text('{"consecutive_count": 1}')
            old_mtime = time.time() - (3 * 3600)
            os.utime(stale_file, (old_mtime, old_mtime))

            # Create a fresh state file
            fresh_file = Path(tmpdir) / "rca_reflector_console_xyz_test.json"
            fresh_file.write_text('{"consecutive_count": 1}')

            with patch.object(Path, "parent", Path(tmpdir)):
                with patch("StopHook_rca_reflector.STATE_DIR", Path(tmpdir)):
                    _cleanup_stale_state_files()

            # Stale file should be deleted
            assert not stale_file.exists()
            # Fresh file should still exist
            assert fresh_file.exists()


class TestStateUpdate:
    """Tests for state update logic."""

    def test_same_tool_increments_count(self):
        """Same tool+error increments consecutive count."""
        from StopHook_rca_reflector import _update_catch22_state

        state = {"last_tool": "Bash", "last_error": "exit 1", "consecutive_count": 1}
        new_state = _update_catch22_state(state, "Bash", "exit 1")
        assert new_state["consecutive_count"] == 2

    def test_different_tool_resets_count(self):
        """Different tool resets consecutive count."""
        from StopHook_rca_reflector import _update_catch22_state

        state = {"last_tool": "Bash", "last_error": "exit 1", "consecutive_count": 2}
        new_state = _update_catch22_state(state, "Read", "not found")
        assert new_state["consecutive_count"] == 1
        assert new_state["last_tool"] == "Read"
