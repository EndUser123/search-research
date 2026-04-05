#!/usr/bin/env python3
"""
Tests for terminal-scoped state file isolation in mypy type checking hook.

Verifies Fix ARCH-001: Multi-terminal isolation for edit velocity tracking.
"""

import json

# Add hooks to path
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from PreToolUse_mypy_type_check import (
    get_edit_velocity,
    get_state_file_path,
    record_edit,
)

# Patch where the function is used (PreToolUse_mypy_type_check), not where it's defined
HOOK_MODULE = "PreToolUse_mypy_type_check"


class TestTerminalScopedStateFile:
    """Test terminal-scoped state file path generation."""

    def test_state_file_path_uses_terminal_id(self):
        """State file path includes terminal ID for isolation."""
        # Mock detect_terminal_id where it's imported/used
        with patch(f"{HOOK_MODULE}.detect_terminal_id", return_value="test-terminal-123"):
            path = get_state_file_path()

            # Should include terminal ID in filename
            assert path.name == "mypy_edit_tracker_test-terminal-123.json"
            # Should be in state directory
            assert path.parent.name == "state"

    def test_state_file_path_different_terminals(self):
        """Different terminals get different state file paths."""
        with patch(f"{HOOK_MODULE}.detect_terminal_id", return_value="terminal-A"):
            path_a = get_state_file_path()

        with patch(f"{HOOK_MODULE}.detect_terminal_id", return_value="terminal-B"):
            path_b = get_state_file_path()

        # Different terminals = different files
        assert path_a.name != path_b.name
        assert path_a.name == "mypy_edit_tracker_terminal-A.json"
        assert path_b.name == "mypy_edit_tracker_terminal-B.json"


class TestEditVelocityTracking:
    """Test edit velocity detection from terminal-scoped state."""

    def test_velocity_stable_no_edits(self, tmp_path):
        """Stable mode when no recent edits."""
        state_file = tmp_path / "test_state.json"

        with patch("PreToolUse_mypy_type_check.get_state_file_path", return_value=state_file):
            # No state file = no edits
            velocity = get_edit_velocity()
            assert velocity == "stable"

    def test_velocity_stable_few_edits(self, tmp_path):
        """Stable mode with 0-1 edits in 2 minutes."""
        state_file = tmp_path / "test_state.json"

        # Create state with 1 edit
        from datetime import datetime, timedelta

        one_minute_ago = datetime.now() - timedelta(minutes=1)
        state_file.write_text(
            json.dumps({"edits": [{"file": "test.py", "timestamp": one_minute_ago.isoformat()}]})
        )

        with patch("PreToolUse_mypy_type_check.get_state_file_path", return_value=state_file):
            velocity = get_edit_velocity()
            assert velocity == "stable"

    def test_velocity_normal(self, tmp_path):
        """Normal mode with 2-4 edits in 2 minutes."""
        state_file = tmp_path / "test_state.json"

        from datetime import datetime, timedelta

        now = datetime.now()
        edits = [
            {"file": f"test{i}.py", "timestamp": (now - timedelta(seconds=30 * i)).isoformat()}
            for i in range(3)  # 3 edits
        ]
        state_file.write_text(json.dumps({"edits": edits}))

        with patch("PreToolUse_mypy_type_check.get_state_file_path", return_value=state_file):
            velocity = get_edit_velocity()
            assert velocity == "normal"

    def test_velocity_rapid(self, tmp_path):
        """Rapid mode with >=5 edits in 2 minutes."""
        state_file = tmp_path / "test_state.json"

        from datetime import datetime, timedelta

        now = datetime.now()
        edits = [
            {"file": f"test{i}.py", "timestamp": (now - timedelta(seconds=20 * i)).isoformat()}
            for i in range(5)  # 5 edits
        ]
        state_file.write_text(json.dumps({"edits": edits}))

        with patch("PreToolUse_mypy_type_check.get_state_file_path", return_value=state_file):
            velocity = get_edit_velocity()
            assert velocity == "rapid"

    def test_velocity_ignores_old_edits(self, tmp_path):
        """Edits older than 2 minutes don't count toward velocity."""
        state_file = tmp_path / "test_state.json"

        from datetime import datetime, timedelta

        three_minutes_ago = datetime.now() - timedelta(minutes=3)
        state_file.write_text(
            json.dumps(
                {
                    "edits": [
                        {"file": "old.py", "timestamp": three_minutes_ago.isoformat()},
                        {"file": "recent.py", "timestamp": datetime.now().isoformat()},
                    ]
                }
            )
        )

        with patch("PreToolUse_mypy_type_check.get_state_file_path", return_value=state_file):
            velocity = get_edit_velocity()
            # Only 1 recent edit = stable
            assert velocity == "stable"


class TestRecordEdit:
    """Test edit recording to terminal-scoped state."""

    def test_record_edit_creates_state_file(self, tmp_path):
        """Recording an edit creates the state file."""
        state_file = tmp_path / "test_state.json"

        with patch("PreToolUse_mypy_type_check.get_state_file_path", return_value=state_file):
            record_edit("test_file.py")

            assert state_file.exists()
            data = json.loads(state_file.read_text())
            assert "edits" in data
            assert len(data["edits"]) == 1
            assert data["edits"][0]["file"] == "test_file.py"

    def test_record_edit_appends_to_existing(self, tmp_path):
        """Multiple edits are appended to state file."""
        state_file = tmp_path / "test_state.json"

        with patch("PreToolUse_mypy_type_check.get_state_file_path", return_value=state_file):
            record_edit("file1.py")
            record_edit("file2.py")
            record_edit("file3.py")

            data = json.loads(state_file.read_text())
            assert len(data["edits"]) == 3
            files = [e["file"] for e in data["edits"]]
            assert files == ["file1.py", "file2.py", "file3.py"]

    def test_record_edit_prunes_old_entries(self, tmp_path):
        """Edits older than 10 minutes are pruned."""
        state_file = tmp_path / "test_state.json"

        from datetime import datetime, timedelta

        now = datetime.now()

        # Create state with old and new edits
        fifteen_min_ago = now - timedelta(minutes=15)
        five_min_ago = now - timedelta(minutes=5)
        state_file.write_text(
            json.dumps(
                {
                    "edits": [
                        {"file": "old.py", "timestamp": fifteen_min_ago.isoformat()},
                        {"file": "recent.py", "timestamp": five_min_ago.isoformat()},
                    ]
                }
            )
        )

        with patch("PreToolUse_mypy_type_check.get_state_file_path", return_value=state_file):
            record_edit("new.py")

            data = json.loads(state_file.read_text())
            # Old edit pruned, recent and new remain
            assert len(data["edits"]) == 2
            files = [e["file"] for e in data["edits"]]
            assert "old.py" not in files
            assert "recent.py" in files
            assert "new.py" in files


class TestMultiTerminalIsolation:
    """Test that terminals don't interfere with each other."""

    def test_separate_terminals_separate_state(self, tmp_path):
        """Each terminal maintains its own edit count."""
        state_file_a = tmp_path / "mypy_edit_tracker_terminal-A.json"
        state_file_b = tmp_path / "mypy_edit_tracker_terminal-B.json"

        # Terminal A makes 3 edits
        with patch("PreToolUse_mypy_type_check.get_state_file_path", return_value=state_file_a):
            for i in range(3):
                record_edit(f"file_a_{i}.py")

        # Terminal B makes 1 edit
        with patch("PreToolUse_mypy_type_check.get_state_file_path", return_value=state_file_b):
            record_edit("file_b_1.py")

        # Terminal A velocity = normal (3 edits)
        with patch("PreToolUse_mypy_type_check.get_state_file_path", return_value=state_file_a):
            velocity_a = get_edit_velocity()

        # Terminal B velocity = stable (1 edit)
        with patch("PreToolUse_mypy_type_check.get_state_file_path", return_value=state_file_b):
            velocity_b = get_edit_velocity()

        assert velocity_a == "normal"
        assert velocity_b == "stable"

    def test_terminal_create_own_state_file(self, tmp_path):
        """Each terminal creates its own state file on first edit."""
        state_file = tmp_path / "mypy_edit_tracker_term-1.json"

        with patch("PreToolUse_mypy_type_check.get_state_file_path", return_value=state_file):
            record_edit("test.py")

        # Check terminal-1's file was created
        assert state_file.exists()
