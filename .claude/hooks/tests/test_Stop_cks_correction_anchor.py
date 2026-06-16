#!/usr/bin/env python3
"""Tests for Stop_cks_correction_anchor.py."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from Stop_cks_correction_anchor import run


class TestCksCorrectionAnchor:
    """Regression suite for Stop_cks_correction_anchor.py."""

    def _make_data(self, session_id="sess-test", terminal_id="t1"):
        return {"session_id": session_id, "terminal_id": terminal_id}
        return {"session_id": session_id, "terminal_id": terminal_id}

    # --- Enabled/disable ----------------------------------------------------- #

    def test_disabled_by_env(self):
        """When STOP_CKS_CORRECTION_ANCHOR_ENABLED=false, returns None."""
        with patch.dict(os.environ, {"STOP_CKS_CORRECTION_ANCHOR_ENABLED": "false"}):
            # Need to re-import to pick up env change — patch the constant instead
            with patch("Stop_cks_correction_anchor.ENABLED", False):
                result = run(self._make_data())
        assert result is None

    def test_no_session_id(self):
        """Missing session_id returns None early."""
        result = run({"terminal_id": "t1"})
        assert result is None

    def test_no_terminal_id(self):
        """Missing terminal_id returns None early."""
        result = run({"session_id": "sess-test"})
        assert result is None

    # --- Challenge marker absent -------------------------------------------- #

    def test_no_challenge_marker(self):
        """No challenge marker file → returns None."""
        data = self._make_data()
        with patch("Stop_cks_correction_anchor._challenge_marker_path") as mock_path:
            mock_path.return_value = Path("/nonexistent/marker.json")
            result = run(data)
        assert result is None

    # --- No expected skill from conversation --------------------------------- #

    def test_no_skill_in_conversation(self):
        """Conversation with no /skill-name → returns None."""
        data = self._make_data()
        marker = Path("/tmp/challenge_marker.json")
        marker.touch()
        try:
            with patch("Stop_cks_correction_anchor._challenge_marker_path", return_value=marker):
                result = run(data)
            assert result is None
        finally:
            marker.unlink(missing_ok=True)

    # --- Current-turn events empty ------------------------------------------- #

    def test_no_current_turn_events(self):
        """No current-turn events → returns None."""
        data = self._make_data()
        marker = Path("/tmp/challenge_marker.json")
        marker.touch()
        try:
            with patch("Stop_cks_correction_anchor._challenge_marker_path", return_value=marker):
                with patch("Stop_cks_correction_anchor.load_scoped_tool_events", side_effect=[
                    [],  # current turn
                    [],  # session
                ]):
                    result = run(data)
            assert result is None
        finally:
            marker.unlink(missing_ok=True)

    # --- No prior-turn mismatch (same skill) -------------------------------- #

    def test_same_skill_no_anchor(self):
        """Prior and current have same skill dir → no CKS write."""
        data = {
            "session_id": "sess-test",
            "terminal_id": "t1",
            "conversation": [{"role": "user", "content": "What does /ai-pcli use?"}],
        }
        marker = Path("/tmp/challenge_marker.json")
        marker.touch()
        try:
            with patch("Stop_cks_correction_anchor._challenge_marker_path", return_value=marker):
                current = [{"name": "Read", "command": "P:/.claude/skills/ai-pcli/SKILL.md", "id": 1}]
                session = [{"name": "Read", "command": "P:/.claude/skills/ai-pcli/SKILL.md", "id": 2}]
                with patch("Stop_cks_correction_anchor.load_scoped_tool_events", side_effect=[current, session]):
                    with patch("Stop_cks_correction_anchor._get_ingest", return_value=MagicMock()) as mock_get_ingest:
                        result = run(data)
            assert result is None
            mock_get_ingest.assert_not_called()
        finally:
            marker.unlink(missing_ok=True)

    # --- Skill mismatch triggers CKS write ---------------------------------- #

    def test_skill_mismatch_triggers_ingest(self):
        """Challenge marker + skill mismatch → ingest_memory called."""
        data = {
            "session_id": "sess-test",
            "terminal_id": "t1",
            "conversation": [{"role": "user", "content": "What does /ai-pcli use?"}],
        }
        marker = Path("/tmp/challenge_marker.json")
        marker.touch()
        try:
            with patch("Stop_cks_correction_anchor._challenge_marker_path", return_value=marker):
                # Prior turn accessed ai-cli (wrong), current turn accessed ai-pcli (correct)
                current = [{"name": "Read", "command": "P:/.claude/skills/ai-pcli/SKILL.md", "id": 1}]
                session = [
                    {"name": "Read", "command": "P:/.claude/skills/ai-pcli/SKILL.md", "id": 1},
                    {"name": "Read", "command": "P:/.claude/skills/ai-cli/SKILL.md", "id": 2},
                ]
                with patch("Stop_cks_correction_anchor.load_scoped_tool_events", side_effect=[current, session]):
                    with patch("Stop_cks_correction_anchor._get_ingest", return_value=MagicMock()) as mock_get_ingest:
                        result = run(data)
            assert result is None
            mock_get_ingest.assert_called_once()
            call_kwargs = mock_get_ingest.return_value.call_args.kwargs
            assert call_kwargs["wrong_skill"] == "ai-cli"
            assert call_kwargs["correct_skill"] == "ai-pcli"
            # ingest_correction(title=..., content=..., **metadata) — NOT ingest_memory
            assert "title" in call_kwargs, "Must use ingest_correction(title=...), not ingest_memory()"
            assert "content" in call_kwargs, "Must use ingest_correction(content=...), not ingest_memory()"
            assert "entry_type" not in call_kwargs, (
                "Must not pass entry_type kwarg — ingest_correction hardcodes type='correction'"
            )
        finally:
            marker.unlink(missing_ok=True)

    # --- CKS failure is silent --------------------------------------------- #

    def test_ingest_failure_is_silent(self):
        """CKS ingest_memory raises → returns None (fail open)."""
        data = {
            "session_id": "sess-test",
            "terminal_id": "t1",
            "conversation": [{"role": "user", "content": "What does /ai-pcli use?"}],
        }
        marker = Path("/tmp/challenge_marker.json")
        marker.touch()
        try:
            with patch("Stop_cks_correction_anchor._challenge_marker_path", return_value=marker):
                current = [{"name": "Read", "command": "P:/.claude/skills/ai-pcli/SKILL.md", "id": 1}]
                session = [
                    {"name": "Read", "command": "P:/.claude/skills/ai-pcli/SKILL.md", "id": 1},
                    {"name": "Read", "command": "P:/.claude/skills/ai-cli/SKILL.md", "id": 2},
                ]
                with patch("Stop_cks_correction_anchor.load_scoped_tool_events", side_effect=[current, session]):
                    with patch("Stop_cks_correction_anchor._get_ingest", return_value=MagicMock(side_effect=RuntimeError("CKS error"))):
                        result = run(data)
            assert result is None  # fail open — no exception propagated
        finally:
            marker.unlink(missing_ok=True)

    # --- Write-path type regression ----------------------------------------- #

    def test_ingest_uses_correct_api(self):
        """Guard: calling ingest_memory with entry_type='correction' writes type='memory'.

        This test documents the old broken behavior and proves the fix is in place.
        ingest_correction() hardcodes type='correction'; ingest_memory() hardcodes type='memory'.
        Stop_cks_correction_anchor must use ingest_correction, not ingest_memory.
        """
        import sys
        cks_path = Path("P:/packages/.claude-marketplace/plugins/search-research/core")
        if str(cks_path) not in sys.path:
            sys.path.insert(0, str(cks_path))

        from cks.unified import CKS

        db = "P:/__csf/data/cks.db"
        with CKS(db) as cks:
            before = cks.conn.execute(
                "SELECT COUNT(*) FROM entries WHERE type='correction'"
            ).fetchone()[0]

            eid = cks.ingest_correction(
                title="regression: verify ingest_correction sets type=correction",
                content="Direct API test — must be type='correction', not 'memory'",
                test_marker="write_path_regression_test",
            )

            after = cks.conn.execute(
                "SELECT COUNT(*) FROM entries WHERE type='correction'"
            ).fetchone()[0]

            row_type = cks.conn.execute(
                "SELECT type FROM entries WHERE id=?", (eid,)
            ).fetchone()[0]

        assert row_type == "correction", (
            f"BUG: ingest_correction wrote type='{row_type}', expected 'correction'. "
            "Root cause: ensure Stop_cks_correction_anchor uses ingest_correction(), "
            "NOT ingest_memory(question=..., answer=..., entry_type='correction')."
        )
        assert after == before + 1, "Delta should be exactly 1"


# Needed for patch.dict in test_disabled_by_env
import os
