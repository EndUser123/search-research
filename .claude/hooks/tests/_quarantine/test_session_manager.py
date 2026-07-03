#!/usr/bin/env python3
"""
Test suite for session_manager.py module.

These tests verify session management functionality including:
- Terminal ID detection with fallback
- Session state persistence
- Session creation, renaming, and switching
- Task claiming
- Session cleanup

Run with: pytest P:\\.claude\\hooks\\tests\\test_session_manager.py -v
"""

import builtins
import json
import os
import sys
import time
from pathlib import Path

import pytest

# Add hooks directory to path for imports
hooks_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(hooks_dir))

# Import at module level to avoid Python name mangling issues inside test classes
from __lib import session_manager
from __lib.session_manager import (
    get_terminal_id,
)


class TestGetTerminalId:
    """Tests for get_terminal_id() function."""

    def test_get_terminal_id_returns_valid_string(self):
        """
        Test that get_terminal_id() always returns a valid string.

        Given: The session_manager module is imported
        When: get_terminal_id() is called
        Then: It returns a non-empty string
        """
        # Act
        result = get_terminal_id()

        # Assert
        assert isinstance(result, str), f"Expected str, got {type(result)}"
        assert len(result) > 0, "Terminal ID should not be empty"

    def test_get_terminal_id_fallback_to_pid(self, monkeypatch):
        """
        Test that get_terminal_id() falls back to PID format when detection fails.

        Given: Terminal detection module fails to import
        When: get_terminal_id() is called
        Then: It returns string in format 'term_{pid}'
        """
        # Arrange - Mock the import to fail
        original_import = builtins.__import__

        def mock_import_error(name, *args, **kwargs):
            if "terminal_detection" in name:
                raise ImportError("Mocked import failure")
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", mock_import_error)

        # Force reload of session_manager to pick up mocked import
        import importlib
        importlib.reload(session_manager)

        # Act
        result = session_manager.get_terminal_id()

        # Assert
        assert isinstance(result, str)
        assert result.startswith("term_")
        # Should contain a PID (number)
        pid_part = result.replace("term_", "")
        assert pid_part.isdigit(), f"Expected PID number, got {pid_part}"


class TestGetCurrentSessionId:
    """Tests for get_current_session_id() function."""

    def test_get_current_session_id_reads_from_file(self, tmp_path, monkeypatch):
        """
        Test that get_current_session_id() reads session ID from SESSION_FILE.

        Given: SESSION_FILE contains a valid session_id
        When: get_current_session_id() is called
        Then: It returns the session_id from the file
        """
        # Arrange
        test_session_file = tmp_path / "current_session.json"
        test_session_id = "test_session_123456"

        # Write test session file
        test_session_file.write_text(
            json.dumps({"session_id": test_session_id, "terminal_id": "term_123", "updated_at": time.time()}),
            encoding="utf-8"
        )

        # Patch SESSION_FILE in the module
        monkeypatch.setattr(session_manager, "SESSION_FILE", test_session_file)

        # Act
        result = session_manager.get_current_session_id()

        # Assert
        assert result == test_session_id, f"Expected {test_session_id}, got {result}"

    def test_get_current_session_id_defaults_when_file_missing(self, tmp_path, monkeypatch):
        """
        Test that get_current_session_id() returns 'default' when SESSION_FILE doesn't exist.

        Given: SESSION_FILE does not exist
        When: get_current_session_id() is called
        Then: It returns 'default'
        """
        # Arrange
        test_session_file = tmp_path / "nonexistent_session.json"

        monkeypatch.setattr(session_manager, "SESSION_FILE", test_session_file)

        # Act
        result = session_manager.get_current_session_id()

        # Assert
        assert result == "default"


class TestLoadSessionState:
    """Tests for load_session_state() function."""

    def test_load_session_state_returns_dict(self, tmp_path, monkeypatch):
        """
        Test that load_session_state() returns a dictionary with expected structure.

        Given: A session state file exists with valid JSON
        When: load_session_state() is called with the session_id
        Then: It returns a dict with session metadata
        """
        # Arrange
        test_state_dir = tmp_path / "session_states"
        test_state_dir.mkdir()

        monkeypatch.setattr(session_manager, "STATE_DIR", test_state_dir)

        session_id = "test_session_123"
        state_path = test_state_dir / f"{session_id}_state.json"

        test_state = {
            "session_id": session_id,
            "name": "Test Session",
            "created_at": time.time(),
            "last_activity": time.time(),
            "tasks": ["task1", "task2"],
            "metadata": {"key": "value"},
        }

        state_path.write_text(json.dumps(test_state), encoding="utf-8")

        # Act
        result = session_manager.load_session_state(session_id)

        # Assert
        assert isinstance(result, dict)
        assert result["session_id"] == session_id
        assert result["name"] == "Test Session"
        assert "tasks" in result
        assert isinstance(result["tasks"], list)

    def test_load_session_state_creates_default_for_new_session(self, tmp_path, monkeypatch):
        """
        Test that load_session_state() creates default state for non-existent session.

        Given: No session state file exists for the given session_id
        When: load_session_state() is called
        Then: It returns a new default state dict with the session_id
        """
        # Arrange
        test_state_dir = tmp_path / "session_states"
        test_state_dir.mkdir()

        monkeypatch.setattr(session_manager, "STATE_DIR", test_state_dir)

        session_id = "new_session_789"

        # Act
        result = session_manager.load_session_state(session_id)

        # Assert
        assert isinstance(result, dict)
        assert result["session_id"] == session_id
        assert result["name"] == session_id
        assert "created_at" in result
        assert "last_activity" in result
        assert isinstance(result["tasks"], list)
        assert len(result["tasks"]) == 0


class TestSaveSessionState:
    """Tests for save_session_state() function."""

    def test_save_session_state_writes_json(self, tmp_path, monkeypatch):
        """
        Test that save_session_state() writes state as JSON to the state file.

        Given: A session_id and state dict
        When: save_session_state() is called
        Then: The state is written to a JSON file in STATE_DIR
        """
        # Arrange
        test_state_dir = tmp_path / "session_states"
        test_state_dir.mkdir()

        monkeypatch.setattr(session_manager, "STATE_DIR", test_state_dir)

        session_id = "save_test_session"
        test_state = {
            "session_id": session_id,
            "name": "Save Test Session",
            "created_at": time.time(),
            "last_activity": time.time(),
            "tasks": [],
            "metadata": {},
        }

        # Act
        session_manager.save_session_state(session_id, test_state)

        # Assert - Verify file was created
        expected_path = test_state_dir / f"{session_id}_state.json"
        assert expected_path.exists(), f"State file not created at {expected_path}"

        # Verify content is valid JSON
        content = expected_path.read_text(encoding="utf-8")
        loaded_state = json.loads(content)
        assert loaded_state["session_id"] == session_id
        assert loaded_state["name"] == "Save Test Session"

    def test_save_session_state_updates_last_activity(self, tmp_path, monkeypatch):
        """
        Test that save_session_state() updates the last_activity timestamp.

        Given: A session state dict
        When: save_session_state() is called
        Then: The last_activity field is updated to current time
        """
        # Arrange
        test_state_dir = tmp_path / "session_states"
        test_state_dir.mkdir()

        monkeypatch.setattr(session_manager, "STATE_DIR", test_state_dir)

        session_id = "activity_test"
        old_time = time.time() - 3600  # 1 hour ago
        test_state = {
            "session_id": session_id,
            "name": "Activity Test",
            "created_at": old_time,
            "last_activity": old_time,
            "tasks": [],
            "metadata": {},
        }

        # Act
        time.sleep(0.01)  # Small delay to ensure time difference
        session_manager.save_session_state(session_id, test_state)

        # Assert
        state_path = test_state_dir / f"{session_id}_state.json"
        loaded_state = json.loads(state_path.read_text(encoding="utf-8"))
        assert loaded_state["last_activity"] > old_time


class TestCreateSession:
    """Tests for create_session() function."""

    def test_create_session_creates_state_file(self, tmp_path, monkeypatch):
        """
        Test that create_session() creates a new session with state file.

        Given: A session name and terminal_id
        When: create_session() is called
        Then: A new session state file is created and session_id is returned
        """
        # Arrange
        test_state_dir = tmp_path / "session_states"
        test_state_dir.mkdir()
        test_session_file = tmp_path / "current_session.json"

        monkeypatch.setattr(session_manager, "STATE_DIR", test_state_dir)
        monkeypatch.setattr(session_manager, "SESSION_FILE", test_session_file)

        session_name = "my_test_session"
        terminal_id = "term_test_123"

        # Act
        session_id = session_manager.create_session(session_name, terminal_id)

        # Assert
        assert isinstance(session_id, str)
        assert session_name in session_id  # session_id contains the name

        # Verify state file was created
        state_path = test_state_dir / f"{session_id}_state.json"
        assert state_path.exists(), "State file should be created"

        # Verify state content
        state = json.loads(state_path.read_text(encoding="utf-8"))
        assert state["name"] == session_name
        assert state["session_id"] == session_id

        # Verify current session file was updated
        assert test_session_file.exists()
        current_data = json.loads(test_session_file.read_text(encoding="utf-8"))
        assert current_data["session_id"] == session_id
        assert current_data["terminal_id"] == terminal_id


class TestRenameSession:
    """Tests for rename_session() function."""

    def test_rename_session_updates_state_file(self, tmp_path, monkeypatch):
        """
        Test that rename_session() updates the session name in the state file.

        Given: An existing session with a name
        When: rename_session() is called with a new_name
        Then: The session state file is updated with the new name
        """
        # Arrange
        test_state_dir = tmp_path / "session_states"
        test_state_dir.mkdir()

        monkeypatch.setattr(session_manager, "STATE_DIR", test_state_dir)

        session_id = "rename_test_123"
        original_name = "Original Name"

        # Create initial session state
        state_path = test_state_dir / f"{session_id}_state.json"
        initial_state = {
            "session_id": session_id,
            "name": original_name,
            "created_at": time.time(),
            "last_activity": time.time(),
            "tasks": [],
            "metadata": {},
        }
        state_path.write_text(json.dumps(initial_state), encoding="utf-8")

        # Act
        new_name = "Renamed Session"
        session_manager.rename_session(session_id, new_name)

        # Assert
        updated_state = json.loads(state_path.read_text(encoding="utf-8"))
        assert updated_state["name"] == new_name
        assert updated_state["session_id"] == session_id  # session_id unchanged

    def test_rename_session_does_not_change_session_id(self, tmp_path, monkeypatch):
        """
        Test that rename_session() only changes the name, not the session_id.

        Given: An existing session
        When: rename_session() is called
        Then: The session_id remains the same, only the name field changes
        """
        # Arrange
        test_state_dir = tmp_path / "session_states"
        test_state_dir.mkdir()

        monkeypatch.setattr(session_manager, "STATE_DIR", test_state_dir)

        session_id = "id_preservation_test"
        state_path = test_state_dir / f"{session_id}_state.json"
        initial_state = {
            "session_id": session_id,
            "name": "Old Name",
            "created_at": time.time(),
            "last_activity": time.time(),
            "tasks": [],
            "metadata": {},
        }
        state_path.write_text(json.dumps(initial_state), encoding="utf-8")

        # Act
        session_manager.rename_session(session_id, "New Name")

        # Assert
        updated_state = json.loads(state_path.read_text(encoding="utf-8"))
        assert updated_state["session_id"] == session_id
        assert updated_state["name"] == "New Name"


class TestSwitchSession:
    """Tests for switch_session() function."""

    def test_switch_session_updates_current_session(self, tmp_path, monkeypatch):
        """
        Test that switch_session() updates the current session file.

        Given: An existing session and a terminal_id
        When: switch_session() is called
        Then: SESSION_FILE is updated with the new session_id
        """
        # Arrange
        test_state_dir = tmp_path / "session_states"
        test_state_dir.mkdir()
        test_session_file = tmp_path / "current_session.json"

        monkeypatch.setattr(session_manager, "STATE_DIR", test_state_dir)
        monkeypatch.setattr(session_manager, "SESSION_FILE", test_session_file)

        # Create a session to switch to
        session_id = "target_session_456"
        state_path = test_state_dir / f"{session_id}_state.json"
        state = {
            "session_id": session_id,
            "name": "Target Session",
            "created_at": time.time(),
            "last_activity": time.time(),
            "tasks": [],
            "metadata": {},
        }
        state_path.write_text(json.dumps(state), encoding="utf-8")

        terminal_id = "term_switch_test"

        # Act
        session_manager.switch_session(session_id, terminal_id)

        # Assert
        assert test_session_file.exists()
        current_data = json.loads(test_session_file.read_text(encoding="utf-8"))
        assert current_data["session_id"] == session_id
        assert current_data["terminal_id"] == terminal_id

    def test_switch_session_creates_default_for_nonexistent_session(self, tmp_path, monkeypatch):
        """
        Test that switch_session() creates default state for non-existent session.

        Given: A session_id that doesn't exist in STATE_DIR
        When: switch_session() is called
        Then: SESSION_FILE is updated (default state is loaded via load_session_state)
        Note: Current implementation uses load_session_state which returns default dict
        """
        # Arrange
        test_state_dir = tmp_path / "session_states"
        test_session_file = tmp_path / "current_session.json"
        test_state_dir.mkdir()

        monkeypatch.setattr(session_manager, "STATE_DIR", test_state_dir)
        monkeypatch.setattr(session_manager, "SESSION_FILE", test_session_file)

        # Don't create any session files

        # Act - switch_session loads default state via load_session_state
        session_manager.switch_session("new_session", "term_123")

        # Assert - SESSION_FILE is updated
        assert test_session_file.exists()
        current_data = json.loads(test_session_file.read_text(encoding="utf-8"))
        assert current_data["session_id"] == "new_session"
        assert current_data["terminal_id"] == "term_123"


class TestClaimTask:
    """Tests for claim_task() function."""

    def test_claim_task_raises_error_when_task_tracker_missing(self, tmp_path, monkeypatch):
        """
        Test that claim_task() raises ValueError when task_tracker directory doesn't exist.

        Given: No task_tracker directory exists
        When: claim_task() is called
        Then: ValueError is raised with "not found" message
        """
        # Arrange
        test_state_dir = tmp_path / "session_states"
        test_state_dir.mkdir()

        monkeypatch.setattr(session_manager, "STATE_DIR", test_state_dir)

        # Don't create task_tracker directory

        # Act & Assert
        with pytest.raises(ValueError, match="Task .* not found"):
            session_manager.claim_task("target_session", "nonexistent_task", "term_123")

    def test_claim_task_raises_error_for_nonexistent_task(self, tmp_path, monkeypatch):
        """
        Test that claim_task() raises ValueError when task doesn't exist.

        Given: A task_id that doesn't exist in any session
        When: claim_task() is called
        Then: ValueError is raised with "not found" message
        """
        # Arrange
        test_state_dir = tmp_path / "session_states"
        test_task_dir = tmp_path / "task_tracker"
        test_state_dir.mkdir()
        test_task_dir.mkdir()

        monkeypatch.setattr(session_manager, "STATE_DIR", test_state_dir)

        # Don't create any task files

        # Act & Assert
        with pytest.raises(ValueError, match="not found"):
            session_manager.claim_task("target_session", "nonexistent_task", "term_123")


class TestListSessions:
    """Tests for list_sessions() function."""

    def test_list_sessions_returns_all_sessions(self, tmp_path, monkeypatch):
        """
        Test that list_sessions() returns a list of all sessions.

        Given: Multiple session state files exist in STATE_DIR
        When: list_sessions() is called
        Then: It returns a list of dicts with session info, sorted by last_activity
        """
        # Arrange
        test_state_dir = tmp_path / "session_states"
        test_state_dir.mkdir()

        monkeypatch.setattr(session_manager, "STATE_DIR", test_state_dir)

        # Create multiple sessions
        now = time.time()
        sessions = [
            {"session_id": "session_1", "name": "Session One", "created_at": now - 100, "last_activity": now - 50, "tasks": ["task1"], "metadata": {}},
            {"session_id": "session_2", "name": "Session Two", "created_at": now - 80, "last_activity": now, "tasks": ["task2", "task3"], "metadata": {}},
            {"session_id": "session_3", "name": "Session Three", "created_at": now - 60, "last_activity": now - 30, "tasks": [], "metadata": {}},
        ]

        for session in sessions:
            state_path = test_state_dir / f'{session["session_id"]}_state.json'
            state_path.write_text(json.dumps(session), encoding="utf-8")

        # Act
        result = session_manager.list_sessions()

        # Assert
        assert isinstance(result, list)
        assert len(result) == 3

        # Verify sorting by last_activity (most recent first)
        assert result[0]["session_id"] == "session_2"
        assert result[1]["session_id"] == "session_3"
        assert result[2]["session_id"] == "session_1"

        # Verify structure
        for session_info in result:
            assert "session_id" in session_info
            assert "name" in session_info
            assert "created_at" in session_info
            assert "last_activity" in session_info
            assert "task_count" in session_info


class TestCleanupOldSessions:
    """Tests for cleanup_old_sessions() function."""

    def test_cleanup_old_sessions_removes_expired(self, tmp_path, monkeypatch):
        """
        Test that cleanup_old_sessions() removes sessions older than max_age_hours.

        Given: Session state files with varying ages
        When: cleanup_old_sessions() is called with max_age_hours
        Then: Sessions older than max_age_hours are deleted
        """
        # Arrange
        test_state_dir = tmp_path / "session_states"
        test_state_dir.mkdir()

        monkeypatch.setattr(session_manager, "STATE_DIR", test_state_dir)

        now = time.time()

        # Create sessions with different ages
        # Old session (25 hours ago) - should be deleted
        old_session = {
            "session_id": "old_session",
            "name": "Old Session",
            "created_at": now - (25 * 3600),
            "last_activity": now - (25 * 3600),
            "tasks": [],
            "metadata": {},
        }
        old_state_path = test_state_dir / "old_session_state.json"
        old_state_path.write_text(json.dumps(old_session), encoding="utf-8")

        # Set file mtime to match session age
        os.utime(old_state_path, (now - (25 * 3600), now - (25 * 3600)))

        # Recent session (1 hour ago) - should NOT be deleted
        recent_session = {
            "session_id": "recent_session",
            "name": "Recent Session",
            "created_at": now - 3600,
            "last_activity": now - 3600,
            "tasks": [],
            "metadata": {},
        }
        recent_state_path = test_state_dir / "recent_session_state.json"
        recent_state_path.write_text(json.dumps(recent_session), encoding="utf-8")
        os.utime(recent_state_path, (now - 3600, now - 3600))

        # Act - cleanup sessions older than 24 hours
        deleted = session_manager.cleanup_old_sessions(max_age_hours=24)

        # Assert
        assert "old_session" in deleted
        assert "recent_session" not in deleted

        # Verify files
        assert not old_state_path.exists(), "Old session should be deleted"
        assert recent_state_path.exists(), "Recent session should not be deleted"

    def test_cleanup_old_sessions_preserves_excluded_session(self, tmp_path, monkeypatch):
        """
        Test that cleanup_old_sessions() preserves the excluded session.

        Given: An old session marked as excluded (current session)
        When: cleanup_old_sessions() is called with exclude_session_id
        Then: The excluded session is NOT deleted even if old
        """
        # Arrange
        test_state_dir = tmp_path / "session_states"
        test_state_dir.mkdir()

        monkeypatch.setattr(session_manager, "STATE_DIR", test_state_dir)

        now = time.time()

        # Create old session
        excluded_session_id = "current_session"
        old_session = {
            "session_id": excluded_session_id,
            "name": "Current Session",
            "created_at": now - (30 * 3600),
            "last_activity": now - (30 * 3600),
            "tasks": [],
            "metadata": {},
        }
        old_state_path = test_state_dir / f"{excluded_session_id}_state.json"
        old_state_path.write_text(json.dumps(old_session), encoding="utf-8")

        os.utime(old_state_path, (now - (30 * 3600), now - (30 * 3600)))

        # Act - cleanup but exclude the current session
        deleted = session_manager.cleanup_old_sessions(
            max_age_hours=24,
            exclude_session_id=excluded_session_id
        )

        # Assert
        assert excluded_session_id not in deleted
        assert old_state_path.exists(), "Excluded session should not be deleted"


class TestSessionManager:
    """Tests for SessionManager class."""

    def test_session_manager_create(self, tmp_path, monkeypatch):
        """
        Test that SessionManager.create() creates and switches to new session.

        Given: A SessionManager instance
        When: create() is called with a name
        Then: New session is created and becomes current
        """
        # Arrange
        test_state_dir = tmp_path / "session_states"
        test_session_file = tmp_path / "current_session.json"
        test_state_dir.mkdir()

        monkeypatch.setattr(session_manager, "STATE_DIR", test_state_dir)
        monkeypatch.setattr(session_manager, "SESSION_FILE", test_session_file)

        sm = session_manager.SessionManager()

        # Act
        session_id = sm.create("test_manager_session")

        # Assert
        assert session_id == sm.get_current_id()
        assert test_session_file.exists()
        assert (test_state_dir / f"{session_id}_state.json").exists()

    def test_session_manager_rename(self, tmp_path, monkeypatch):
        """
        Test that SessionManager.rename() renames the current session.

        Given: A SessionManager with a current session
        When: rename() is called with a new name
        Then: The current session's name is updated
        """
        # Arrange
        test_state_dir = tmp_path / "session_states"
        test_session_file = tmp_path / "current_session.json"
        test_state_dir.mkdir()

        monkeypatch.setattr(session_manager, "STATE_DIR", test_state_dir)
        monkeypatch.setattr(session_manager, "SESSION_FILE", test_session_file)

        sm = session_manager.SessionManager()
        session_id = sm.create("original_name")

        # Act
        sm.rename("renamed_session")

        # Assert
        state_path = test_state_dir / f"{session_id}_state.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        assert state["name"] == "renamed_session"

    def test_session_manager_list_all(self, tmp_path, monkeypatch):
        """
        Test that SessionManager.list_all() returns all sessions.

        Given: Multiple sessions exist
        When: list_all() is called
        Then: All sessions are returned
        """
        # Arrange
        test_state_dir = tmp_path / "session_states"
        test_session_file = tmp_path / "current_session.json"
        test_state_dir.mkdir()

        monkeypatch.setattr(session_manager, "STATE_DIR", test_state_dir)
        monkeypatch.setattr(session_manager, "SESSION_FILE", test_session_file)

        sm = session_manager.SessionManager()
        sm.create("session_one")
        sm.create("session_two")

        # Act
        sessions = sm.list_all()

        # Assert
        assert len(sessions) >= 2

    def test_session_manager_cleanup_old_sessions(self, tmp_path, monkeypatch):
        """
        Test that SessionManager.cleanup_old_sessions() removes old sessions.

        Given: Old sessions exist
        When: cleanup_old_sessions() is called
        Then: Old sessions are removed, current session is preserved
        """
        # Arrange
        test_state_dir = tmp_path / "session_states"
        test_session_file = tmp_path / "current_session.json"
        test_state_dir.mkdir()

        monkeypatch.setattr(session_manager, "STATE_DIR", test_state_dir)
        monkeypatch.setattr(session_manager, "SESSION_FILE", test_session_file)

        sm = session_manager.SessionManager()
        sm.create("current_session")

        # Create an old session file manually
        now = time.time()
        old_session_id = "old_session_123"
        old_session = {
            "session_id": old_session_id,
            "name": "Old Session",
            "created_at": now - (30 * 3600),
            "last_activity": now - (30 * 3600),
            "tasks": [],
            "metadata": {},
        }
        old_state_path = test_state_dir / f"{old_session_id}_state.json"
        old_state_path.write_text(json.dumps(old_session), encoding="utf-8")

        os.utime(old_state_path, (now - (30 * 3600), now - (30 * 3600)))

        # Act
        deleted = sm.cleanup_old_sessions(max_age_hours=24, keep_current=True)

        # Assert
        assert old_session_id in deleted
        assert not old_state_path.exists()
        # Current session should still exist
        assert (test_state_dir / f"{sm.get_current_id()}_state.json").exists()
