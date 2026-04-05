"""Tests for Verification Tracker - files_touched extension.

These tests verify the VerificationTracker class extension that tracks:
- Files touched during session (Write, Edit tools)
- Timestamps for all tracked entries
- Persistence across state save/load cycles

Run with:
    pytest P:/.claude/hooks/repositories/tests/test_verification_tracker_integration.py -v
"""

from __future__ import annotations

import json
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

# Import VerificationTracker for module-level access in tests
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "posttooluse"))
from verification_tracker import VerificationTracker

# ============================================================================
# SHARED FIXTURES
# ============================================================================

@pytest.fixture
def temp_state_dir():
    """Create a temporary directory for state files.

    Yields:
        Path: Path to the temporary state directory.

    Cleanup:
        Deletes the temporary directory after test completion.
    """
    with tempfile.TemporaryDirectory(prefix="vt_test_") as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def mock_terminal_id():
    """Return a predictable terminal ID for testing.

    Returns:
        str: Mock terminal ID.
    """
    return "test_term_12"


@pytest.fixture
def verification_tracker(temp_state_dir: Path, mock_terminal_id: str):
    """Create a VerificationTracker instance with mocked terminal detection.

    Args:
        temp_state_dir: Path to temporary state directory.
        mock_terminal_id: Mock terminal ID to return.

    Returns:
        VerificationTracker: Tracker instance with mocked dependencies.
    """
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "posttooluse"))
    from verification_tracker import VerificationTracker

    # Mock terminal_detection to return predictable ID
    with patch("verification_tracker._get_terminal_id", return_value=mock_terminal_id):
        # Mock STATE_DIR to use temp directory
        with patch("verification_tracker.STATE_DIR", temp_state_dir):
            tracker = VerificationTracker()
            return tracker


# ============================================================================
# TEST CLASSES
# ============================================================================

class TestWriteOperationAddsToFilesTouched:
    """Tests for Write tool tracking in files_touched."""

    def test_write_operation_adds_to_files_touched(
        self, verification_tracker: Any, temp_state_dir: Path, mock_terminal_id: str
    ) -> None:
        """Verify Write tool adds entry with path and timestamp.

        Given: VerificationTracker is initialized
        When: process() is called with Write tool
        Then: The file is added to files_touched with path and timestamp
        """
        file_path = "P:/test/file.py"
        timestamp_before = datetime.now(UTC).isoformat()

        # Process Write tool
        verification_tracker.process(
            tool_name="Write",
            tool_input={"file_path": file_path},
            tool_response={"success": True}
        )

        timestamp_after = datetime.now(UTC).isoformat()

        # Verify state file was created
        state_file = temp_state_dir / f"verification_state_{mock_terminal_id}.json"
        assert state_file.exists(), "State file should be created after Write operation"

        # Load and verify state
        with open(state_file) as f:
            state = json.load(f)

        # Assert files_touched exists and has the entry
        assert "files_touched" in state, "State should have files_touched key"
        assert len(state["files_touched"]) == 1, "Should have exactly one file touched"

        entry = state["files_touched"][0]
        assert entry["path"] == file_path, f"Path should be {file_path}"
        assert entry["operation"] == "write", "Operation should be 'write'"

        # Verify timestamp is valid ISO format and within expected range
        assert "timestamp" in entry, "Entry should have timestamp"
        entry_timestamp = entry["timestamp"]
        parsed_timestamp = datetime.fromisoformat(entry_timestamp)

        # Check timestamp is reasonable (within last few seconds)
        timestamp_before_dt = datetime.fromisoformat(timestamp_before)
        timestamp_after_dt = datetime.fromisoformat(timestamp_after)
        assert timestamp_before_dt <= parsed_timestamp <= timestamp_after_dt, \
            "Timestamp should be between before and after"


class TestEditOperationAddsToFilesTouched:
    """Tests for Edit tool tracking in files_touched."""

    def test_edit_operation_adds_to_files_touched(
        self, verification_tracker: Any, temp_state_dir: Path, mock_terminal_id: str
    ) -> None:
        """Verify Edit tool adds entry with path and timestamp.

        Given: VerificationTracker is initialized
        When: process() is called with Edit tool
        Then: The file is added to files_touched with path and timestamp
        """
        file_path = "P:/test/another_file.py"
        timestamp_before = datetime.now(UTC).isoformat()

        # Process Edit tool
        verification_tracker.process(
            tool_name="Edit",
            tool_input={"file_path": file_path, "old_string": "old", "new_string": "new"},
            tool_response={"success": True}
        )

        timestamp_after = datetime.now(UTC).isoformat()

        # Verify state file was created
        state_file = temp_state_dir / f"verification_state_{mock_terminal_id}.json"
        assert state_file.exists(), "State file should be created after Edit operation"

        # Load and verify state
        with open(state_file) as f:
            state = json.load(f)

        # Assert files_touched exists and has the entry
        assert "files_touched" in state, "State should have files_touched key"
        assert len(state["files_touched"]) == 1, "Should have exactly one file touched"

        entry = state["files_touched"][0]
        assert entry["path"] == file_path, f"Path should be {file_path}"
        assert entry["operation"] == "edit", "Operation should be 'edit'"

        # Verify timestamp is valid ISO format
        assert "timestamp" in entry, "Entry should have timestamp"
        entry_timestamp = entry["timestamp"]
        parsed_timestamp = datetime.fromisoformat(entry_timestamp)

        # Check timestamp is reasonable
        timestamp_before_dt = datetime.fromisoformat(timestamp_before)
        timestamp_after_dt = datetime.fromisoformat(timestamp_after)
        assert timestamp_before_dt <= parsed_timestamp <= timestamp_after_dt, \
            "Timestamp should be between before and after"


class TestFilesTouchedHasTimestampFormat:
    """Tests for ISO timestamp format in files_touched entries."""

    def test_files_touched_has_timestamp_format(
        self, verification_tracker: Any, temp_state_dir: Path, mock_terminal_id: str
    ) -> None:
        """Verify each entry has ISO timestamp.

        Given: VerificationTracker is initialized
        When: Multiple operations are tracked
        Then: Each entry has a valid ISO 8601 timestamp
        """
        # Track multiple operations
        operations = [
            ("Write", {"file_path": "P:/test/file1.py"}),
            ("Edit", {"file_path": "P:/test/file2.py", "old_string": "a", "new_string": "b"}),
            ("Write", {"file_path": "P:/test/file3.py"}),
        ]

        for tool_name, tool_input in operations:
            verification_tracker.process(
                tool_name=tool_name,
                tool_input=tool_input,
                tool_response={"success": True}
            )

        # Load state
        state_file = temp_state_dir / f"verification_state_{mock_terminal_id}.json"
        with open(state_file) as f:
            state = json.load(f)

        # Assert all entries have valid ISO timestamps
        assert "files_touched" in state, "State should have files_touched key"
        assert len(state["files_touched"]) == 3, "Should have three files touched"

        for entry in state["files_touched"]:
            assert "timestamp" in entry, f"Entry {entry} should have timestamp"
            assert entry["timestamp"] is not None, "Timestamp should not be None"

            # Verify it's a valid ISO format by attempting to parse
            try:
                datetime.fromisoformat(entry["timestamp"])
            except ValueError as e:
                pytest.fail(f"Invalid ISO timestamp format: {entry['timestamp']}. Error: {e}")


class TestFilesTouchedPersistentAcrossLoads:
    """Tests for persistence across state save/load cycles."""

    def test_files_touched_persistent_across_loads(
        self, verification_tracker: Any, temp_state_dir: Path, mock_terminal_id: str
    ) -> None:
        """Verify files_touched survives state save/load cycle.

        Given: VerificationTracker is initialized and tracks operations
        When: State is saved and loaded again
        Then: files_touched entries are preserved correctly
        """
        # Track some operations
        operations = [
            ("Write", {"file_path": "P:/test/persistent1.py"}),
            ("Edit", {"file_path": "P:/test/persistent2.py", "old_string": "x", "new_string": "y"}),
        ]

        for tool_name, tool_input in operations:
            verification_tracker.process(
                tool_name=tool_name,
                tool_input=tool_input,
                tool_response={"success": True}
            )

        # Get state file path
        state_file = temp_state_dir / f"verification_state_{mock_terminal_id}.json"

        # Load state directly to verify persistence
        with open(state_file) as f:
            saved_state = json.load(f)

        # Verify files_touched was saved
        assert "files_touched" in saved_state, "Saved state should have files_touched"
        assert len(saved_state["files_touched"]) == 2, "Should have two entries"

        # Create new tracker instance to simulate reload
        with patch("verification_tracker._get_terminal_id", return_value=mock_terminal_id):
            with patch("verification_tracker.STATE_DIR", temp_state_dir):
                new_tracker = VerificationTracker()

        # Load state through new tracker
        loaded_state = new_tracker._load_state()

        # Verify files_touched persisted correctly
        assert "files_touched" in loaded_state, "Loaded state should have files_touched"
        assert len(loaded_state["files_touched"]) == 2, "Should have two entries after reload"

        # Verify entries match
        for i, entry in enumerate(loaded_state["files_touched"]):
            assert entry["path"] == saved_state["files_touched"][i]["path"]
            assert entry["operation"] == saved_state["files_touched"][i]["operation"]
            assert entry["timestamp"] == saved_state["files_touched"][i]["timestamp"]

        # Verify timestamps are still valid ISO format after reload
        for entry in loaded_state["files_touched"]:
            try:
                datetime.fromisoformat(entry["timestamp"])
            except ValueError as e:
                pytest.fail(f"Invalid ISO timestamp after reload: {entry['timestamp']}. Error: {e}")
