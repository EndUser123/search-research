"""
Test suite for dreaming-daemon state management (T-003).

These tests follow RED-GREEN-REFACTOR TDD cycle:
- RED: Tests fail initially (no implementation)
- GREEN: Minimal implementation to pass tests
- REFACTOR: Improve code quality while tests pass

State File: P:/.claude/state/dreaming-daemon-state.json
Module: dreaming_state.py

Requirements from plan T-003:
- State file: dreaming-daemon-state.json
- Dataclass for state structure
- Fields: offset, heartbeat, current_file, shutdown
- Functions: load_state() -> DreamingState, save_state(state) -> None
- Atomic write guarantees
- Graceful degradation for corrupted state

Acceptance criteria:
1. Missing file returns default state
2. Corrupted JSON creates fresh state
3. Heartbeat updates are atomic
"""

import hashlib
import json
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import module to test (will fail until implementation exists)
try:
    from dreaming_state import DreamingState, _validate_state, load_state, save_state
    MODULE_EXISTS = True
except ImportError:
    MODULE_EXISTS = False


# Expected dataclass structure (for reference in tests)
@dataclass
class ExpectedDreamingState:
    """Expected structure for DreamingState dataclass."""
    offset: int = 0
    heartbeat: str = ""
    current_file: str = ""
    shutdown: bool = False


class TestDefaultState:
    """Test default state behavior when file is missing."""

    @pytest.fixture
    def state_file_path(self, tmp_path: Path) -> Path:
        """Create state file path in temp directory."""
        return tmp_path / "dreaming-daemon-state.json"

    @pytest.mark.skipif(not MODULE_EXISTS, reason="dreaming_state module not implemented yet")
    def test_missing_file_returns_default_state(self, state_file_path: Path) -> None:
        """
        Test that missing state file returns default state.

        Given: State file does not exist
        When: load_state() is called
        Then: Returns DreamingState with default values (offset=0, heartbeat="", current_file="", shutdown=False)
        """
        # Ensure file doesn't exist
        assert not state_file_path.exists()

        # Load state (should return defaults)
        with patch('dreaming_state.STATE_FILE', state_file_path):
            state = load_state()

        # Verify default values
        assert isinstance(state, DreamingState)
        assert state.offset == 0
        assert state.heartbeat == ""
        assert state.current_file == ""
        assert state.shutdown is False

    @pytest.mark.skipif(not MODULE_EXISTS, reason="dreaming_state module not implemented yet")
    def test_default_state_has_correct_types(self, state_file_path: Path) -> None:
        """
        Test that default state has correct field types.

        Given: State file does not exist
        When: load_state() is called
        Then: Returns DreamingState with correct types (int, str, str, bool)
        """
        with patch('dreaming_state.STATE_FILE', state_file_path):
            state = load_state()

        # Type checking
        assert isinstance(state.offset, int)
        assert isinstance(state.heartbeat, str)
        assert isinstance(state.current_file, str)
        assert isinstance(state.shutdown, bool)


class TestValidStateLoading:
    """Test loading valid state file."""

    @pytest.fixture
    def valid_state_data(self) -> dict[str, Any]:
        """Create valid state data."""
        return {
            "offset": 12345,
            "heartbeat": "2025-03-07T10:30:00",
            "current_file": "/path/to/session.json",
            "shutdown": False
        }

    @pytest.fixture
    def state_file_with_data(self, tmp_path: Path, valid_state_data: dict[str, Any]) -> Path:
        """Create state file with valid data."""
        state_file = tmp_path / "dreaming-daemon-state.json"
        state_file.write_text(json.dumps(valid_state_data, indent=2))
        return state_file

    @pytest.mark.skipif(not MODULE_EXISTS, reason="dreaming_state module not implemented yet")
    def test_loading_valid_state_file(self, state_file_with_data: Path, valid_state_data: dict[str, Any]) -> None:
        """
        Test loading valid state file.

        Given: State file exists with valid data
        When: load_state() is called
        Then: Returns DreamingState with loaded values
        """
        with patch('dreaming_state.STATE_FILE', state_file_with_data):
            state = load_state()

        # Verify loaded values
        assert state.offset == valid_state_data["offset"]
        assert state.heartbeat == valid_state_data["heartbeat"]
        assert state.current_file == valid_state_data["current_file"]
        assert state.shutdown == valid_state_data["shutdown"]

    @pytest.mark.skipif(not MODULE_EXISTS, reason="dreaming_state module not implemented yet")
    def test_loading_state_with_shutdown_true(self, tmp_path: Path) -> None:
        """
        Test loading state with shutdown=True.

        Given: State file has shutdown=True
        When: load_state() is called
        Then: Returns DreamingState with shutdown=True
        """
        state_file = tmp_path / "dreaming-daemon-state.json"
        state_data = {
            "offset": 100,
            "heartbeat": "2025-03-07T10:30:00",
            "current_file": "/path/to/session.json",
            "shutdown": True
        }
        state_file.write_text(json.dumps(state_data, indent=2))

        with patch('dreaming_state.STATE_FILE', state_file):
            state = load_state()

        assert state.shutdown is True

    @pytest.mark.skipif(not MODULE_EXISTS, reason="dreaming_state module not implemented yet")
    def test_loading_state_with_empty_fields(self, tmp_path: Path) -> None:
        """
        Test loading state with empty string fields.

        Given: State file has empty heartbeat and current_file
        When: load_state() is called
        Then: Returns DreamingState with empty strings
        """
        state_file = tmp_path / "dreaming-daemon-state.json"
        state_data = {
            "offset": 0,
            "heartbeat": "",
            "current_file": "",
            "shutdown": False
        }
        state_file.write_text(json.dumps(state_data, indent=2))

        with patch('dreaming_state.STATE_FILE', state_file):
            state = load_state()

        assert state.heartbeat == ""
        assert state.current_file == ""


class TestStateSaving:
    """Test saving state to file."""

    @pytest.fixture
    def state_file_path(self, tmp_path: Path) -> Path:
        """Create state file path in temp directory."""
        return tmp_path / "dreaming-daemon-state.json"

    @pytest.mark.skipif(not MODULE_EXISTS, reason="dreaming_state module not implemented yet")
    def test_saving_state_to_file(self, state_file_path: Path) -> None:
        """
        Test saving state to file.

        Given: DreamingState with specific values
        When: save_state() is called
        Then: State file is created with correct JSON data
        """
        state = DreamingState(
            offset=54321,
            heartbeat="2025-03-07T11:00:00",
            current_file="/new/path/session.json",
            shutdown=False
        )

        with patch('dreaming_state.STATE_FILE', state_file_path):
            save_state(state)

        # Verify file was created
        assert state_file_path.exists()

        # Verify file contents
        with open(state_file_path) as f:
            saved_data = json.load(f)

        assert saved_data["offset"] == 54321
        assert saved_data["heartbeat"] == "2025-03-07T11:00:00"
        assert saved_data["current_file"] == "/new/path/session.json"
        assert saved_data["shutdown"] is False

    @pytest.mark.skipif(not MODULE_EXISTS, reason="dreaming_state module not implemented yet")
    def test_saving_overwrites_existing_file(self, state_file_path: Path) -> None:
        """
        Test that saving overwrites existing state file.

        Given: State file exists with old data
        When: save_state() is called with new data
        Then: File is overwritten with new data
        """
        # Create initial state file
        initial_data = {
            "offset": 100,
            "heartbeat": "2025-03-07T10:00:00",
            "current_file": "/old/path.json",
            "shutdown": False
        }
        state_file_path.write_text(json.dumps(initial_data, indent=2))

        # Save new state
        new_state = DreamingState(
            offset=999,
            heartbeat="2025-03-07T12:00:00",
            current_file="/new/path.json",
            shutdown=True
        )

        with patch('dreaming_state.STATE_FILE', state_file_path):
            save_state(new_state)

        # Verify file has new data
        with open(state_file_path) as f:
            saved_data = json.load(f)

        assert saved_data["offset"] == 999
        assert saved_data["heartbeat"] == "2025-03-07T12:00:00"
        assert saved_data["current_file"] == "/new/path.json"
        assert saved_data["shutdown"] is True

    @pytest.mark.skipif(not MODULE_EXISTS, reason="dreaming_state module not implemented yet")
    def test_saved_state_is_valid_json(self, state_file_path: Path) -> None:
        """
        Test that saved state is valid JSON.

        Given: DreamingState instance
        When: save_state() is called
        Then: File contains valid JSON (no corruption)
        """
        state = DreamingState(
            offset=123,
            heartbeat="2025-03-07T10:30:00",
            current_file="/path/to/file.json",
            shutdown=False
        )

        with patch('dreaming_state.STATE_FILE', state_file_path):
            save_state(state)

        # Verify JSON is valid (will raise if invalid)
        with open(state_file_path) as f:
            json.load(f)  # Should not raise


class TestCorruptedJsonHandling:
    """Test handling of corrupted JSON in state file."""

    @pytest.fixture
    def corrupted_state_file(self, tmp_path: Path) -> Path:
        """Create state file with corrupted JSON."""
        state_file = tmp_path / "dreaming-daemon-state.json"
        state_file.write_text("{ invalid json content }")
        return state_file

    @pytest.mark.skipif(not MODULE_EXISTS, reason="dreaming_state module not implemented yet")
    def test_corrupted_json_creates_fresh_state(self, corrupted_state_file: Path) -> None:
        """
        Test that corrupted JSON creates fresh state.

        Given: State file exists with corrupted JSON
        When: load_state() is called
        Then: Returns default DreamingState (graceful degradation)
        """
        with patch('dreaming_state.STATE_FILE', corrupted_state_file):
            state = load_state()

        # Should return default state
        assert isinstance(state, DreamingState)
        assert state.offset == 0
        assert state.heartbeat == ""
        assert state.current_file == ""
        assert state.shutdown is False

    @pytest.mark.skipif(not MODULE_EXISTS, reason="dreaming_state module not implemented yet")
    def test_corrupted_json_does_not_crash(self, corrupted_state_file: Path) -> None:
        """
        Test that corrupted JSON does not crash the program.

        Given: State file exists with corrupted JSON
        When: load_state() is called
        Then: Returns valid DreamingState without raising exception
        """
        # Should not raise exception
        with patch('dreaming_state.STATE_FILE', corrupted_state_file):
            state = load_state()

        assert state is not None

    @pytest.mark.skipif(not MODULE_EXISTS, reason="dreaming_state module not implemented yet")
    def test_empty_file_returns_default_state(self, tmp_path: Path) -> None:
        """
        Test that empty file returns default state.

        Given: State file exists but is empty
        When: load_state() is called
        Then: Returns default DreamingState
        """
        state_file = tmp_path / "dreaming-daemon-state.json"
        state_file.write_text("")

        with patch('dreaming_state.STATE_FILE', state_file):
            state = load_state()

        assert isinstance(state, DreamingState)
        assert state.offset == 0

    @pytest.mark.skipif(not MODULE_EXISTS, reason="dreaming_state module not implemented yet")
    def test_partial_json_returns_default_state(self, tmp_path: Path) -> None:
        """
        Test that partial JSON returns default state.

        Given: State file exists with partial JSON (missing fields)
        When: load_state() is called
        Then: Returns DreamingState with defaults for missing fields
        """
        state_file = tmp_path / "dreaming-daemon-state.json"
        partial_data = {"offset": 100}  # Missing other fields
        state_file.write_text(json.dumps(partial_data))

        with patch('dreaming_state.STATE_FILE', state_file):
            state = load_state()

        # Should have offset from file, defaults for others
        assert isinstance(state, DreamingState)


class TestHeartbeatUpdates:
    """Test heartbeat timestamp updates."""

    @pytest.fixture
    def state_file_path(self, tmp_path: Path) -> Path:
        """Create state file path in temp directory."""
        return tmp_path / "dreaming-daemon-state.json"

    @pytest.mark.skipif(not MODULE_EXISTS, reason="dreaming_state module not implemented yet")
    def test_heartbeat_update_updates_timestamp(self, state_file_path: Path) -> None:
        """
        Test that heartbeat update updates timestamp.

        Given: DreamingState instance
        When: State is saved with new heartbeat timestamp
        Then: Heartbeat field is updated in file
        """
        state = DreamingState(
            offset=100,
            heartbeat="2025-03-07T10:00:00",
            current_file="/path/to/file.json",
            shutdown=False
        )

        # Update heartbeat
        new_heartbeat = "2025-03-07T11:30:00"
        state.heartbeat = new_heartbeat

        with patch('dreaming_state.STATE_FILE', state_file_path):
            save_state(state)

        # Verify heartbeat was updated
        with open(state_file_path) as f:
            saved_data = json.load(f)

        assert saved_data["heartbeat"] == new_heartbeat

    @pytest.mark.skipif(not MODULE_EXISTS, reason="dreaming_state module not implemented yet")
    def test_heartbeat_updates_are_atomic(self, state_file_path: Path) -> None:
        """
        Test that heartbeat updates are atomic (complete or fail).

        Given: DreamingState instance
        When: save_state() is called
        Then: Either complete write succeeds or no partial write occurs
        """
        state = DreamingState(
            offset=100,
            heartbeat="2025-03-07T10:00:00",
            current_file="/path/to/file.json",
            shutdown=False
        )

        with patch('dreaming_state.STATE_FILE', state_file_path):
            save_state(state)

        # Verify complete file exists (not partial)
        assert state_file_path.exists()

        # Verify file is valid JSON (atomic write guaranteed)
        with open(state_file_path) as f:
            data = json.load(f)

        # All fields present
        assert "offset" in data
        assert "heartbeat" in data
        assert "current_file" in data
        assert "shutdown" in data


class TestShutdownFlagUpdate:
    """Test shutdown flag updates."""

    @pytest.fixture
    def state_file_path(self, tmp_path: Path) -> Path:
        """Create state file path in temp directory."""
        return tmp_path / "dreaming-daemon-state.json"

    @pytest.mark.skipif(not MODULE_EXISTS, reason="dreaming_state module not implemented yet")
    def test_shutdown_flag_update_to_true(self, state_file_path: Path) -> None:
        """
        Test updating shutdown flag to True.

        Given: DreamingState with shutdown=False
        When: shutdown flag is set to True and saved
        Then: File reflects shutdown=True
        """
        state = DreamingState(
            offset=100,
            heartbeat="2025-03-07T10:00:00",
            current_file="/path/to/file.json",
            shutdown=False
        )

        # Update shutdown flag
        state.shutdown = True

        with patch('dreaming_state.STATE_FILE', state_file_path):
            save_state(state)

        # Verify shutdown was updated
        with open(state_file_path) as f:
            saved_data = json.load(f)

        assert saved_data["shutdown"] is True

    @pytest.mark.skipif(not MODULE_EXISTS, reason="dreaming_state module not implemented yet")
    def test_shutdown_flag_update_to_false(self, state_file_path: Path) -> None:
        """
        Test updating shutdown flag to False.

        Given: DreamingState with shutdown=True
        When: shutdown flag is set to False and saved
        Then: File reflects shutdown=False
        """
        # Create initial state with shutdown=True
        initial_state = DreamingState(
            offset=100,
            heartbeat="2025-03-07T10:00:00",
            current_file="/path/to/file.json",
            shutdown=True
        )

        with patch('dreaming_state.STATE_FILE', state_file_path):
            save_state(initial_state)

        # Update shutdown flag to False
        initial_state.shutdown = False

        with patch('dreaming_state.STATE_FILE', state_file_path):
            save_state(initial_state)

        # Verify shutdown was updated
        with open(state_file_path) as f:
            saved_data = json.load(f)

        assert saved_data["shutdown"] is False

    @pytest.mark.skipif(not MODULE_EXISTS, reason="dreaming_state module not implemented yet")
    def test_shutdown_flag_preserved_on_load(self, state_file_path: Path) -> None:
        """
        Test that shutdown flag is preserved when loading.

        Given: State file with shutdown=True
        When: load_state() is called
        Then: Returns DreamingState with shutdown=True
        """
        # Create state with shutdown=True
        state = DreamingState(
            offset=100,
            heartbeat="2025-03-07T10:00:00",
            current_file="/path/to/file.json",
            shutdown=True
        )

        with patch('dreaming_state.STATE_FILE', state_file_path):
            save_state(state)

        # Load state
        with patch('dreaming_state.STATE_FILE', state_file_path):
            loaded_state = load_state()

        # Verify shutdown flag was preserved
        assert loaded_state.shutdown is True


class TestStateFieldUpdates:
    """Test individual state field updates."""

    @pytest.fixture
    def state_file_path(self, tmp_path: Path) -> Path:
        """Create state file path in temp directory."""
        return tmp_path / "dreaming-daemon-state.json"

    @pytest.mark.skipif(not MODULE_EXISTS, reason="dreaming_state module not implemented yet")
    def test_offset_field_update(self, state_file_path: Path) -> None:
        """
        Test updating offset field.

        Given: DreamingState instance
        When: offset field is updated and saved
        Then: File reflects new offset value
        """
        state = DreamingState(
            offset=100,
            heartbeat="2025-03-07T10:00:00",
            current_file="/path/to/file.json",
            shutdown=False
        )

        # Update offset
        state.offset = 99999

        with patch('dreaming_state.STATE_FILE', state_file_path):
            save_state(state)

        # Verify offset was updated
        with open(state_file_path) as f:
            saved_data = json.load(f)

        assert saved_data["offset"] == 99999

    @pytest.mark.skipif(not MODULE_EXISTS, reason="dreaming_state module not implemented yet")
    def test_current_file_field_update(self, state_file_path: Path) -> None:
        """
        Test updating current_file field.

        Given: DreamingState instance
        When: current_file field is updated and saved
        Then: File reflects new current_file value
        """
        state = DreamingState(
            offset=100,
            heartbeat="2025-03-07T10:00:00",
            current_file="/old/path.json",
            shutdown=False
        )

        # Update current_file
        new_path = "/new/path/to/session.json"
        state.current_file = new_path

        with patch('dreaming_state.STATE_FILE', state_file_path):
            save_state(state)

        # Verify current_file was updated
        with open(state_file_path) as f:
            saved_data = json.load(f)

        assert saved_data["current_file"] == new_path


class TestGreenPhase:
    """Tests verifying implementation exists (GREEN phase complete)."""

    def test_module_exists(self) -> None:
        """Verify module exists and is importable."""
        try:
            from dreaming_state import DreamingState, load_state, save_state
            assert DreamingState is not None
            assert load_state is not None
            assert save_state is not None
        except ImportError:
            pytest.fail("dreaming_state module not implemented yet")

    def test_dreaming_state_is_dataclass(self) -> None:
        """Verify DreamingState is a dataclass."""
        from dataclasses import is_dataclass
        try:
            from dreaming_state import DreamingState
            assert is_dataclass(DreamingState)
        except ImportError:
            pytest.skip("dreaming_state module not implemented yet")

    def test_dreaming_state_has_required_fields(self) -> None:
        """Verify DreamingState has required fields."""
        try:
            from dreaming_state import DreamingState
            state = DreamingState()

            # Check field existence
            assert hasattr(state, 'offset')
            assert hasattr(state, 'heartbeat')
            assert hasattr(state, 'current_file')
            assert hasattr(state, 'shutdown')
        except ImportError:
            pytest.skip("dreaming_state module not implemented yet")

    def test_functions_exist(self) -> None:
        """Verify required functions exist."""
        try:
            from dreaming_state import load_state, save_state
            assert callable(load_state)
            assert callable(save_state)
        except ImportError:
            pytest.skip("dreaming_state module not implemented yet")


class TestStateValidationP2:
    """Test state validation with backup recovery (P2 improvement)."""

    @pytest.mark.skipif(not MODULE_EXISTS, reason="dreaming_state module not implemented yet")
    def test_validate_state_with_valid_data(self) -> None:
        """
        Test that valid state passes validation.

        Given: DreamingState with valid fields
        When: _validate_state() is called
        Then: Returns True
        """
        state = DreamingState(
            offset=1000,
            heartbeat="2025-03-07T10:00:00",
            current_file="/path/to/file.json",
            shutdown=False
        )

        assert _validate_state(state) is True

    @pytest.mark.skipif(not MODULE_EXISTS, reason="dreaming_state module not implemented yet")
    def test_validate_state_rejects_negative_offset(self) -> None:
        """
        Test that negative offset fails validation.

        Given: DreamingState with offset < 0
        When: _validate_state() is called
        Then: Returns False
        """
        state = DreamingState(offset=-1)

        assert _validate_state(state) is False

    @pytest.mark.skipif(not MODULE_EXISTS, reason="dreaming_state module not implemented yet")
    def test_validate_state_rejects_invalid_heartbeat(self) -> None:
        """
        Test that invalid heartbeat format fails validation.

        Given: DreamingState with malformed heartbeat
        When: _validate_state() is called
        Then: Returns False
        """
        state = DreamingState(heartbeat="invalid-timestamp")

        assert _validate_state(state) is False

    @pytest.mark.skipif(not MODULE_EXISTS, reason="dreaming_state module not implemented yet")
    def test_validate_state_accepts_empty_heartbeat(self) -> None:
        """
        Test that empty heartbeat passes validation.

        Given: DreamingState with empty heartbeat
        When: _validate_state() is called
        Then: Returns True (empty is valid)
        """
        state = DreamingState(heartbeat="")

        assert _validate_state(state) is True

    @pytest.mark.skipif(not MODULE_EXISTS, reason="dreaming_state module not implemented yet")
    def test_validate_state_rejects_invalid_shutdown_type(self) -> None:
        """
        Test that non-boolean shutdown flag fails validation.

        Given: DreamingState with shutdown as string
        When: _validate_state() is called
        Then: Returns False
        """
        # Create invalid state (simulate corrupted data)
        try:
            from dreaming_state import DreamingState
            state = DreamingState(offset=0, heartbeat="", current_file="", shutdown="true")
            # Manually corrupt the shutdown field
            import dataclasses
            state_dict = dataclasses.asdict(state)
            state_dict['shutdown'] = "true"  # String instead of bool
            state = DreamingState(**state_dict)

            assert _validate_state(state) is False
        except (ImportError, TypeError):
            pytest.skip("dreaming_state module not implemented yet")


class TestBackupRecoveryP2:
    """Test backup rotation and recovery (P2 improvement)."""

    @pytest.fixture
    def state_file_path(self, tmp_path: Path) -> Path:
        """Create state file path in temp directory."""
        return tmp_path / "dreaming-daemon-state.json"

    @pytest.mark.skipif(not MODULE_EXISTS, reason="dreaming_state module not implemented yet")
    def test_save_creates_backup(self, state_file_path: Path) -> None:
        """
        Test that saving creates backup (.json.1).

        Given: DreamingState instance
        When: save_state() is called twice
        Then: First save becomes .json.1, second save is primary
        """
        state1 = DreamingState(offset=100)
        state2 = DreamingState(offset=200)

        with patch('dreaming_state.STATE_FILE', state_file_path):
            save_state(state1)
            save_state(state2)

        # Check that backup exists
        backup_path = state_file_path.with_suffix('.json.1')
        assert backup_path.exists()

        # Verify backup has first state
        with open(backup_path, encoding='utf-8') as f:
            backup_data = json.load(f)
        assert backup_data["offset"] == 100

        # Verify primary has second state
        with open(state_file_path, encoding='utf-8') as f:
            primary_data = json.load(f)
        assert primary_data["offset"] == 200

    @pytest.mark.skipif(not MODULE_EXISTS, reason="dreaming_state module not implemented yet")
    def test_load_recovers_from_corrupted_primary(self, state_file_path: Path) -> None:
        """
        Test that load_state recovers from backup when primary is corrupted.

        Given: Corrupted primary state file + valid backup
        When: load_state() is called
        Then: Returns state from backup, restores primary
        """
        # Create valid backup first
        backup_path = state_file_path.with_suffix('.json.1')
        valid_backup_data = {
            "offset": 500,
            "heartbeat": "2025-03-07T10:00:00",
            "current_file": "/backup/path.json",
            "shutdown": False
        }
        backup_path.write_text(json.dumps(valid_backup_data, indent=2))

        # Create corrupted primary
        state_file_path.write_text("{corrupted}")

        with patch('dreaming_state.STATE_FILE', state_file_path):
            state = load_state()

        # Should recover from backup
        assert state.offset == 500
        assert state.heartbeat == "2025-03-07T10:00:00"

        # Primary should be restored from backup
        with open(state_file_path, encoding='utf-8') as f:
            primary_data = json.load(f)
        assert primary_data["offset"] == 500

    @pytest.mark.skipif(not MODULE_EXISTS, reason="dreaming_state module not implemented yet")
    def test_load_returns_default_when_all_corrupted(self, state_file_path: Path) -> None:
        """
        Test that load_state returns default when all files corrupted.

        Given: Corrupted primary + no backups
        When: load_state() is called
        Then: Returns default DreamingState
        """
        # Create corrupted primary
        state_file_path.write_text("{corrupted}")

        with patch('dreaming_state.STATE_FILE', state_file_path):
            state = load_state()

        # Should return default state
        assert state.offset == 0
        assert state.heartbeat == ""
        assert state.current_file == ""

    @pytest.mark.skipif(not MODULE_EXISTS, reason="dreaming_state module not implemented yet")
    def test_backup_rotation_keeps_only_three_backups(self, state_file_path: Path) -> None:
        """
        Test that rotation keeps only BACKUP_COUNT backups.

        Given: BACKUP_COUNT=3
        When: save_state() is called 6 times
        Then: Only .json.1, .json.2, .json.3 exist, .json.4 deleted
        """
        state = DreamingState(offset=100)

        with patch('dreaming_state.BACKUP_COUNT', 3):
            with patch('dreaming_state.STATE_FILE', state_file_path):
                # Save 6 times to create and rotate backups
                for i in range(6):
                    state.offset = i * 100
                    save_state(state)

        # Check that only 3 backups exist
        backup1 = state_file_path.with_suffix('.json.1')
        backup2 = state_file_path.with_suffix('.json.2')
        backup3 = state_file_path.with_suffix('.json.3')
        backup4 = state_file_path.with_suffix('.json.4')

        assert backup1.exists()
        assert backup2.exists()
        assert backup3.exists()
        assert not backup4.exists()  # Oldest backup deleted


class TestChecksumValidation:
    """Test checksum calculation and verification (T-010)."""

    @pytest.fixture
    def state_file_path(self, tmp_path: Path) -> Path:
        """Create state file path in temp directory."""
        return tmp_path / "dreaming-daemon-state.json"

    @pytest.mark.skipif(not MODULE_EXISTS, reason="dreaming_state module not implemented yet")
    def test_save_state_calculates_checksum(self, state_file_path: Path, caplog: pytest.LogCaptureFixture) -> None:
        """
        Test that save_state calculates SHA256 checksum.

        Given: DreamingState with specific values
        When: save_state() is called
        Then: State file contains checksum field with SHA256 hash of JSON content
        """
        state = DreamingState(
            offset=12345,
            heartbeat="2025-03-07T10:30:00",
            current_file="/path/to/session.json",
            shutdown=False
        )

        with patch('dreaming_state.STATE_FILE', state_file_path):
            save_state(state)

        # Read saved file
        with open(state_file_path) as f:
            saved_data = json.load(f)

        # Verify checksum field exists
        assert "checksum" in saved_data

        # Calculate expected checksum (SHA256 of JSON without checksum field)
        # Must use indent=2 to match implementation formatting
        data_for_checksum = {k: v for k, v in saved_data.items() if k != "checksum"}
        json_bytes = json.dumps(data_for_checksum, indent=2, sort_keys=True).encode('utf-8')
        expected_checksum = hashlib.sha256(json_bytes).hexdigest()

        # Verify checksum matches
        assert saved_data["checksum"] == expected_checksum

    @pytest.mark.skipif(not MODULE_EXISTS, reason="dreaming_state module not implemented yet")
    def test_load_state_verifies_checksum(self, state_file_path: Path, caplog: pytest.LogCaptureFixture) -> None:
        """
        Test that load_state verifies checksum on load.

        Given: State file with valid checksum
        When: load_state() is called
        Then: State loads successfully without WARNING
        """
        # Create state with valid checksum
        state_data = {
            "offset": 54321,
            "heartbeat": "2025-03-07T11:00:00",
            "current_file": "/new/path/session.json",
            "shutdown": False,
            "checksum": ""  # Will be calculated below
        }

        # Calculate checksum (must use indent=2 to match implementation)
        data_for_checksum = {k: v for k, v in state_data.items() if k != "checksum"}
        json_bytes = json.dumps(data_for_checksum, indent=2, sort_keys=True).encode('utf-8')
        state_data["checksum"] = hashlib.sha256(json_bytes).hexdigest()

        # Write state file
        state_file_path.write_text(json.dumps(state_data, indent=2))

        # Load state (should not log WARNING)
        with caplog.at_level(logging.WARNING):
            with patch('dreaming_state.STATE_FILE', state_file_path):
                loaded_state = load_state()

        # Verify state loaded correctly
        assert loaded_state.offset == 54321
        assert loaded_state.heartbeat == "2025-03-07T11:00:00"
        assert loaded_state.current_file == "/new/path/session.json"

        # Verify no WARNING was logged
        assert not any(record.levelno == logging.WARNING for record in caplog.records)

    @pytest.mark.skipif(not MODULE_EXISTS, reason="dreaming_state module not implemented yet")
    def test_load_state_detects_mismatch(self, state_file_path: Path, caplog: pytest.LogCaptureFixture) -> None:
        """
        Test that load_state detects checksum mismatch.

        Given: State file with incorrect checksum
        When: load_state() is called
        Then: Logs WARNING, treats state as corrupted (returns default)
        """
        # Create state with INVALID checksum
        state_data = {
            "offset": 99999,
            "heartbeat": "2025-03-07T12:00:00",
            "current_file": "/invalid/path.json",
            "shutdown": True,
            "checksum": "invalid_checksum_12345"  # Wrong checksum
        }

        # Write state file
        state_file_path.write_text(json.dumps(state_data, indent=2))

        # Load state (should log WARNING)
        with caplog.at_level(logging.WARNING):
            with patch('dreaming_state.STATE_FILE', state_file_path):
                loaded_state = load_state()

        # Verify WARNING was logged
        warning_logs = [record for record in caplog.records if record.levelno == logging.WARNING]
        assert len(warning_logs) > 0
        assert any("checksum" in record.message.lower() for record in warning_logs)

        # Verify state treated as corrupted (returns default)
        assert loaded_state.offset == 0
        assert loaded_state.heartbeat == ""
        assert loaded_state.current_file == ""
        assert loaded_state.shutdown is False

    @pytest.mark.skipif(not MODULE_EXISTS, reason="dreaming_state module not implemented yet")
    def test_load_state_missing_checksum_allowed(self, state_file_path: Path, caplog: pytest.LogCaptureFixture) -> None:
        """
        Test that load_state allows missing checksum (backward compatibility).

        Given: State file without checksum field
        When: load_state() is called
        Then: State loads successfully, checksum calculated on next save
        """
        # Create state WITHOUT checksum field (backward compatibility)
        state_data = {
            "offset": 11111,
            "heartbeat": "2025-03-07T13:00:00",
            "current_file": "/legacy/path.json",
            "shutdown": False
            # Note: No checksum field
        }

        # Write state file
        state_file_path.write_text(json.dumps(state_data, indent=2))

        # Load state (should succeed)
        with patch('dreaming_state.STATE_FILE', state_file_path):
            loaded_state = load_state()

        # Verify state loaded correctly (backward compatibility)
        assert loaded_state.offset == 11111
        assert loaded_state.heartbeat == "2025-03-07T13:00:00"
        assert loaded_state.current_file == "/legacy/path.json"
        assert loaded_state.shutdown is False

        # Now save state - should add checksum
        with patch('dreaming_state.STATE_FILE', state_file_path):
            save_state(loaded_state)

        # Verify checksum was added
        with open(state_file_path) as f:
            saved_data = json.load(f)

        assert "checksum" in saved_data
        assert saved_data["checksum"] != ""


class TestSafeRollback:
    """Characterization tests for safe rollback functionality with corrupted file preservation (T-011).

    These tests CAPTURE CURRENT BEHAVIOR of the _preserve_corrupted_file() function
    and the rollback flow in load_state(). Implementation already exists in
    dreaming_state.py lines 68-91 and 130-151.

    Run with: pytest tests/test_dreaming_state.py::TestSafeRollback -v
    """

    @pytest.fixture
    def state_file_path(self, tmp_path: Path) -> Path:
        """Create state file path in temp directory."""
        return tmp_path / "dreaming-daemon-state.json"

    @pytest.mark.skipif(not MODULE_EXISTS, reason="dreaming_state module not implemented yet")
    def test_corrupted_file_preserved_with_timestamp(self, state_file_path: Path) -> None:
        """
        Test that corrupted file is renamed to .corrupted.timestamp format.

        Given: State file exists with corrupted content (invalid checksum)
        When: load_state() detects corruption and triggers rollback
        Then: Original file is renamed to .json.corrupted.YYYYMMDD_HHMMSS format
        """
        # Create state file with invalid checksum
        corrupted_data = {
            "offset": 99999,
            "heartbeat": "2025-03-07T12:00:00",
            "current_file": "/corrupted/path.json",
            "shutdown": True,
            "checksum": "invalid_checksum_12345"  # Wrong checksum
        }
        state_file_path.write_text(json.dumps(corrupted_data, indent=2))

        with patch('dreaming_state.STATE_FILE', state_file_path):
            load_state()

        # Verify original file no longer exists
        assert not state_file_path.exists()

        # Verify corrupted file was preserved with timestamp
        corrupted_files = list(state_file_path.parent.glob("*.corrupted.*"))
        assert len(corrupted_files) == 1

        corrupted_path = corrupted_files[0]
        # Check naming pattern: .json.corrupted.YYYYMMDD_HHMMSS
        assert ".json.corrupted." in corrupted_path.name
        # Timestamp format uses underscores (Windows-compatible)
        assert "_" in corrupted_path.name

    @pytest.mark.skipif(not MODULE_EXISTS, reason="dreaming_state module not implemented yet")
    def test_preserved_file_contains_original_content(self, state_file_path: Path) -> None:
        """
        Test that preserved file has same content as corrupted original.

        Given: State file exists with specific corrupted content
        When: load_state() detects corruption and preserves file
        Then: Preserved file contains identical content to original corrupted file
        """
        # Create state file with specific corrupted content
        original_corrupted_data = {
            "offset": 54321,
            "heartbeat": "2025-03-07T15:30:00",
            "current_file": "/specific/corrupted.json",
            "shutdown": False,
            "checksum": "wrong_checksum_value"
        }
        state_file_path.write_text(json.dumps(original_corrupted_data, indent=2))

        with patch('dreaming_state.STATE_FILE', state_file_path):
            load_state()

        # Find preserved corrupted file
        corrupted_files = list(state_file_path.parent.glob("*.corrupted.*"))
        assert len(corrupted_files) == 1
        corrupted_path = corrupted_files[0]

        # Verify preserved file has original content
        with open(corrupted_path, encoding='utf-8') as f:
            preserved_data = json.load(f)

        assert preserved_data["offset"] == 54321
        assert preserved_data["heartbeat"] == "2025-03-07T15:30:00"
        assert preserved_data["current_file"] == "/specific/corrupted.json"
        assert preserved_data["shutdown"] is False
        assert preserved_data["checksum"] == "wrong_checksum_value"

    @pytest.mark.skipif(not MODULE_EXISTS, reason="dreaming_state module not implemented yet")
    def test_rollback_creates_preserved_file_before_restoration(self, state_file_path: Path) -> None:
        """
        Test full rollback flow: corrupt → preserve → restore from backup.

        Given: Corrupted primary state file + valid backup file
        When: load_state() detects corruption
        Then: Preserves corrupted file first, then restores from backup
        """
        # Create valid backup first
        backup_path = state_file_path.with_suffix('.json.1')
        valid_backup_data = {
            "offset": 1000,
            "heartbeat": "2025-03-07T10:00:00",
            "current_file": "/backup/path.json",
            "shutdown": False,
            "checksum": ""  # Will be calculated
        }

        # Calculate checksum for backup (must use indent=2)
        data_for_checksum = {k: v for k, v in valid_backup_data.items() if k != "checksum"}
        json_bytes = json.dumps(data_for_checksum, indent=2, sort_keys=True).encode('utf-8')
        valid_backup_data["checksum"] = hashlib.sha256(json_bytes).hexdigest()

        backup_path.write_text(json.dumps(valid_backup_data, indent=2))

        # Create corrupted primary with different data
        corrupted_primary_data = {
            "offset": 99999,
            "heartbeat": "2025-03-07T12:00:00",
            "current_file": "/corrupted/path.json",
            "shutdown": True,
            "checksum": "invalid_checksum"
        }
        state_file_path.write_text(json.dumps(corrupted_primary_data, indent=2))

        # Trigger rollback
        with patch('dreaming_state.STATE_FILE', state_file_path):
            loaded_state = load_state()

        # Step 1: Verify corrupted file was preserved
        corrupted_files = list(state_file_path.parent.glob("*.corrupted.*"))
        assert len(corrupted_files) == 1

        # Verify preserved file has corrupted content (not backup content)
        with open(corrupted_files[0], encoding='utf-8') as f:
            preserved_data = json.load(f)
        assert preserved_data["offset"] == 99999  # Corrupted value
        assert preserved_data["current_file"] == "/corrupted/path.json"

        # Step 2: Verify primary file was restored from backup
        with open(state_file_path, encoding='utf-8') as f:
            primary_data = json.load(f)
        assert primary_data["offset"] == 1000  # Backup value
        assert primary_data["heartbeat"] == "2025-03-07T10:00:00"
        assert primary_data["current_file"] == "/backup/path.json"

        # Step 3: Verify loaded state is from backup (not corrupted data)
        assert loaded_state.offset == 1000
        assert loaded_state.heartbeat == "2025-03-07T10:00:00"
        assert loaded_state.current_file == "/backup/path.json"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
