#!/usr/bin/env python3
"""Tests for SessionEnd_cleanup terminal/session scoped cleanup."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture
def session_end_module():
    import SessionEnd_cleanup

    return SessionEnd_cleanup


def test_session_end_cleanup_removes_terminal_scoped_files(session_end_module):
    """SessionEnd cleanup should remove exact terminal/session scoped state files."""
    with tempfile.TemporaryDirectory() as tmp:
        hooks_dir = Path(tmp) / "hooks"
        state_dir = hooks_dir / "state"
        session_data_dir = hooks_dir / "session_data"
        state_dir.mkdir(parents=True)
        session_data_dir.mkdir(parents=True)

        session_id = "11111111-1111-1111-1111-111111111111"
        terminal_id = "console_abc123"
        safe_session = "11111111-1111-1111-1111-111111111111"
        safe_terminal = "console_abc123"

        files_to_create = [
            state_dir / f"pending_command_intent_{safe_terminal}.json",
            state_dir / f"pending_command_intent_{safe_terminal}_{safe_session}.json",
            state_dir / f"pretool_degraded_{safe_terminal}_{safe_session}.json",
            state_dir / f"grounded_artifact_{safe_terminal}_{safe_session}.json",
            state_dir / f"grounded_artifact_{safe_session}.json",
            session_data_dir / f"last_blocked_claim_{safe_session}_{safe_terminal}.json",
        ]
        for path in files_to_create:
            path.write_text("{}", encoding="utf-8")

        stdin_payload = json.dumps(
            {"session_id": session_id, "terminal_id": terminal_id}
        )

        with patch.object(session_end_module, "HOOKS_DIR", hooks_dir):
            with patch.object(sys, "stdin") as mock_stdin:
                mock_stdin.read.return_value = stdin_payload
                with patch.object(sys, "exit") as mock_exit:
                    session_end_module.main()
                    mock_exit.assert_called()

        for path in files_to_create:
            assert not path.exists(), f"Expected cleanup to delete {path.name}"


def test_session_end_cleanup_handles_unknown_terminal_variant(session_end_module):
    """Unknown-terminal cleanup should remove unknown-scoped degraded/artifact files."""
    with tempfile.TemporaryDirectory() as tmp:
        hooks_dir = Path(tmp) / "hooks"
        state_dir = hooks_dir / "state"
        state_dir.mkdir(parents=True)

        session_id = "22222222-2222-2222-2222-222222222222"
        safe_session = session_id

        degraded = state_dir / f"pretool_degraded_unknown_{safe_session}.json"
        artifact = state_dir / f"grounded_artifact_unknown_{safe_session}.json"
        degraded.write_text("{}", encoding="utf-8")
        artifact.write_text("{}", encoding="utf-8")

        stdin_payload = json.dumps({"session_id": session_id})

        with patch.object(session_end_module, "HOOKS_DIR", hooks_dir):
            with patch.object(sys, "stdin") as mock_stdin:
                mock_stdin.read.return_value = stdin_payload
                with patch.object(sys, "exit") as mock_exit:
                    session_end_module.main()
                    mock_exit.assert_called()

        assert not degraded.exists()
        assert not artifact.exists()
