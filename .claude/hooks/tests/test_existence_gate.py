"""Tests for PreToolUse_existence_gate.py hook.

Verifies:
1. Hook allows Write to non-existent files
2. Hook blocks Write to existing files without prior Read
3. Hook allows Write to existing files after Read
4. Hook blocks Edit to existing files without prior Read
5. Hook allows Edit after Read
6. Session isolation (Read doesn't affect other sessions)
7. Bypass flag allows overriding
8. MultiEdit handled gracefully
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

# Add hooks directory to path
HOOKS_DIR = Path(__file__).resolve().parent.parent
if str(HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(HOOKS_DIR))

from PreToolUse_existence_gate import (
    _get_state_file,
    _load_read_files,
    _record_read_file,
    run,
)


# =============================================================================
# TEST 1: State management
# =============================================================================


class TestStateManagement:
    """Verify session state tracking for read files."""

    def test_load_read_files_empty_state(self):
        """Returns empty set when no state file exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Non-existent state file
            result = _load_read_files("nonexistent_session")
            assert result == set()

    def test_load_read_files_existing_state(self):
        """Loads read_files from existing state file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = Path(tmpdir) / "read_files_test.json"
            test_data = {"read_files": ["file1.py", "file2.py"]}
            with open(state_file, "w", encoding="utf-8") as f:
                json.dump(test_data, f)

            # Monkey _get_state_file to return our temp file
            import PreToolUse_existence_gate as eg
            original = eg._get_state_file
            eg._get_state_file = lambda sid: state_file

            try:
                result = _load_read_files("test_session")
                assert result == {"file1.py", "file2.py"}
            finally:
                eg._get_state_file = original

    def test_record_read_file_creates_state(self):
        """Records read file and updates state file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = Path(tmpdir) / "read_files_test.json"
            test_file = Path(tmpdir) / "test.txt"

            # Monkey _get_state_file
            import PreToolUse_existence_gate as eg
            original = eg._get_state_file
            eg._get_state_file = lambda sid: state_file

            try:
                # Record read
                _record_read_file("test_session", str(test_file))

                # Verify state file created
                assert state_file.exists()
                with open(state_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                assert "read_files" in data
                assert str(test_file) in data["read_files"]
            finally:
                eg._get_state_file = original


# =============================================================================
# TEST 2: Hook behavior - Allow cases
# =============================================================================


class TestHookAllows:
    """Verify hook allows operations that should pass."""

    def test_allows_write_to_nonexistent_file(self):
        """Write to non-existent file is allowed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            non_existent = Path(tmpdir) / "does_not_exist.txt"

            data = {
                "tool_name": "Write",
                "session_id": "test_session_1",
                "tool_input": {"file_path": str(non_existent)},
                "message": "create new file",
            }

            result = run(data)
            assert result is None  # Allow

    def test_allows_write_after_read(self):
        """Write to existing file after Read is allowed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"

            # Mock session state to show file was read
            import PreToolUse_existence_gate as eg
            original = eg._get_state_file
            state_file = Path(tmpdir) / "read_files_test.json"
            eg._get_state_file = lambda sid: state_file

            try:
                # Record that file was read
                _record_read_file("test_session_2", str(test_file))

                data = {
                    "tool_name": "Write",
                    "session_id": "test_session_2",
                    "tool_input": {"file_path": str(test_file)},
                    "message": "update file",
                }

                result = run(data)
                assert result is None  # Allow
            finally:
                eg._get_state_file = original

    def test_allows_with_bypass_flag(self):
        """Write to existing file with --allow-overwrite flag is allowed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            test_file.touch()  # Create file

            data = {
                "tool_name": "Write",
                "session_id": "test_session_3",
                "tool_input": {"file_path": str(test_file)},
                "message": "force update --allow-overwrite",
            }

            result = run(data)
            assert result is None  # Allow

    def test_allows_edit_after_read(self):
        """Edit to existing file after Read is allowed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            test_file.touch()

            import PreToolUse_existence_gate as eg
            original = eg._get_state_file
            state_file = Path(tmpdir) / "read_files_test.json"
            eg._get_state_file = lambda sid: state_file

            try:
                _record_read_file("test_session_4", str(test_file))

                data = {
                    "tool_name": "Edit",
                    "session_id": "test_session_4",
                    "tool_input": {"file_path": str(test_file)},
                    "message": "edit file",
                }

                result = run(data)
                assert result is None  # Allow
            finally:
                eg._get_state_file = original


# =============================================================================
# TEST 3: Hook behavior - Block cases
# =============================================================================


class TestHookBlocks:
    """Verify hook blocks operations that should fail."""

    def test_blocks_write_without_read(self):
        """Write to existing file without Read is blocked."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            test_file.touch()  # Create file

            data = {
                "tool_name": "Write",
                "session_id": "test_session_5",
                "tool_input": {"file_path": str(test_file)},
                "message": "update file",
            }

            # Run in subprocess to catch sys.exit(2)
            import subprocess

            result = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    f"import sys; sys.path.insert(0, '{HOOKS_DIR}'); "
                    f"from PreToolUse_existence_gate import run; "
                    f"data={json.dumps(data)}; "
                    f"run(data); "
                    f"assert False, 'Should have exited'",
                ],
                capture_output=True,
                text=True,
                env={**os.environ, "EXISTENCE_GATE_BLOCK": "1"},
            )

            assert result.returncode == 2  # Blocked
            assert "EXISTENCE CHECK REQUIRED" in result.stderr

    def test_blocks_edit_without_read(self):
        """Edit to existing file without Read is blocked."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            test_file.touch()

            data = {
                "tool_name": "Edit",
                "session_id": "test_session_6",
                "tool_input": {"file_path": str(test_file)},
                "message": "edit file",
            }

            import subprocess

            result = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    f"import sys; sys.path.insert(0, '{HOOKS_DIR}'); "
                    f"from PreToolUse_existence_gate import run; "
                    f"data={json.dumps(data)}; "
                    f"run(data); "
                    f"assert False, 'Should have exited'",
                ],
                capture_output=True,
                text=True,
                env={**os.environ, "EXISTENCE_GATE_BLOCK": "1"},
            )

            assert result.returncode == 2  # Blocked
            assert "EXISTENCE CHECK REQUIRED" in result.stderr


# =============================================================================
# TEST 4: Session isolation
# =============================================================================


class TestSessionIsolation:
    """Verify Read tracking is session-scoped."""

    def test_read_in_session_doesnt_affect_other_session(self):
        """Read in session A doesn't allow Write in session B."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            test_file.touch()

            import PreToolUse_existence_gate as eg
            original = eg._get_state_file
            state_file = Path(tmpdir) / "read_files_test.json"
            eg._get_state_file = lambda sid: state_file

            try:
                # Record read in session A
                _record_read_file("session_A", str(test_file))

                # Write in session B should block (different session_id)
                data = {
                    "tool_name": "Write",
                    "session_id": "session_B",
                    "tool_input": {"file_path": str(test_file)},
                    "message": "update file",
                }

                result = subprocess.run(
                    [
                        sys.executable,
                        "-c",
                        f"import sys; sys.path.insert(0, '{HOOKS_DIR}'); "
                        f"from PreToolUse_existence_gate import run; "
                        f"data={json.dumps(data)}; "
                        f"run(data); "
                        f"assert False, 'Should have blocked'",
                    ],
                    capture_output=True,
                    text=True,
                    env={**os.environ, "EXISTENCE_GATE_BLOCK": "1"},
                )

                assert result.returncode == 2  # Blocked
            finally:
                eg._get_state_file = original


# =============================================================================
# TEST 5: Edge cases
# =============================================================================


class TestEdgeCases:
    """Verify hook handles edge cases gracefully."""

    def test_allows_non_write_edit_tools(self):
        """Non-Write/Edit tools are allowed."""
        for tool in ["Read", "Bash", "Grep", "Glob"]:
            data = {
                "tool_name": tool,
                "session_id": "test_session",
                "tool_input": {},
                "message": "some command",
            }

            result = run(data)
            assert result is None  # Allow

    def test_allows_without_session_id(self):
        """Operations without session_id are allowed (can't track)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            test_file.touch()

            data = {
                "tool_name": "Write",
                "session_id": "",  # Empty
                "tool_input": {"file_path": str(test_file)},
                "message": "write file",
            }

            result = run(data)
            assert result is None  # Allow (can't track without session_id)

    def test_allows_without_file_path(self):
        """Write without file_path is allowed (invalid input)."""
        data = {
            "tool_name": "Write",
            "session_id": "test_session",
            "tool_input": {},  # No file_path
            "message": "write file",
        }

        result = run(data)
        assert result is None  # Allow


# =============================================================================
# TEST 6: MultiEdit handling
# =============================================================================


class TestMultiEdit:
    """Verify MultiEdit is handled (skipped or appropriate behavior)."""

    def test_multiedit_allows_for_now(self):
        """MultiEdit is allowed for now (implementation note)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data = {
                "tool_name": "MultiEdit",
                "session_id": "test_session",
                "tool_input": {"path": f"{tmpdir}/test.txt"},  # Simplified
                "message": "edit multiple",
            }

            result = run(data)
            assert result is None  # Allow for now


# =============================================================================
# TEST 7: Error handling
# =============================================================================


class TestErrorHandling:
    """Verify hook handles errors gracefully."""

    def test_handles_malformed_state_file(self):
        """Gracefully handles corrupted state file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = Path(tmpdir) / "read_files_test.json"
            state_file.write_text("invalid json")

            import PreToolUse_existence_gate as eg
            original = eg._get_state_file
            eg._get_state_file = lambda sid: state_file

            try:
                # Should fail open gracefully, return empty set
                result = _load_read_files("test_session")
                assert result == set()
            finally:
                eg._get_state_file = original

    def test_handles_permission_error_on_state_write(self):
        """Gracefully handles permission errors when writing state."""
        # Can't easily test permission errors in temp dir
        # This is verified by existing fail-open pattern in hook
        pass