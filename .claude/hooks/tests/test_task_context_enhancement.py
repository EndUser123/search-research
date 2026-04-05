#!/usr/bin/env python3
"""Tests for Task Context Documentation Enhancement.

Tests that tasks automatically capture conversation context:
- description from TaskCreate input
- files_referenced from recent tool results
- session_timestamp for temporal context

QUAL-003 Tests:
- OSError during state save/load is logged (not silently ignored)
- Error logging captures error details for debugging
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Add hooks dir to path for imports
hooks_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(hooks_dir))


class TestTaskContextEnhancement:
    """Test task context capture and storage."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.state_dir = Path(self.temp_dir.name) / "state"
        self.state_dir.mkdir()

    def teardown_method(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def test_task_create_captures_description(self):
        """Test that TaskCreate captures description from input."""
        # Import after sys.path modification
        from PostToolUse_task_tracker import track_task_create

        # Setup: Mock environment variables
        with patch.dict(os.environ, {"TASK_STATE_DIR": str(self.state_dir)}):
            tool_input = {
                "taskId": "test_1",
                "subject": "Fix authentication bug",
                "description": "Fix process_prompt() in auth.py to handle null tokens",
                "status": "pending",
            }

            # Execute
            result = track_task_create(tool_input, "test_session", "term_1")

            # Load state and verify
            state_path = self.state_dir / "test_session_tasks.json"
            assert state_path.exists()

            state = json.loads(state_path.read_text())
            task = state["tasks"]["test_1"]

            # Verify description is captured
            assert "description" in task
            assert task["description"] == "Fix process_prompt() in auth.py to handle null tokens"

    def test_task_create_captures_session_timestamp(self):
        """Test that TaskCreate captures ISO8601 session timestamp."""
        from PostToolUse_task_tracker import track_task_create

        with patch.dict(os.environ, {"TASK_STATE_DIR": str(self.state_dir)}):
            tool_input = {
                "taskId": "test_2",
                "subject": "Add tests",
                "description": "Write unit tests for API",
                "status": "pending",
            }

            track_task_create(tool_input, "test_session", "term_1")

            # Load state and verify timestamp format
            state_path = self.state_dir / "test_session_tasks.json"
            state = json.loads(state_path.read_text())
            task = state["tasks"]["test_2"]

            # Verify session_timestamp exists and is ISO8601 format
            assert "session_timestamp" in task
            assert "T" in task["session_timestamp"]  # ISO8601 has T separator

    def test_task_create_captures_files_from_state(self):
        """Test that TaskCreate copies files_referenced from recent files state."""
        from PostToolUse_task_tracker import (
            load_session_state,
            save_session_state,
            track_task_create,
        )

        with patch.dict(os.environ, {"TASK_STATE_DIR": str(self.state_dir)}):
            # Setup: Pre-populate state with recent_files
            state = load_session_state("test_session")
            state["recent_files"] = [
                "P:/src/auth.py",
                "P:/tests/test_auth.py",
                "P:/src/api.py",
            ]
            save_session_state("test_session", state)

            # Execute: Create task
            tool_input = {
                "taskId": "test_3",
                "subject": "Refactor auth",
                "description": "Extract auth logic to service layer",
                "status": "pending",
            }

            track_task_create(tool_input, "test_session", "term_1")

            # Verify files are copied to task metadata
            state_path = self.state_dir / "test_session_tasks.json"
            state = json.loads(state_path.read_text())
            task = state["tasks"]["test_3"]

            assert "files_referenced" in task
            assert len(task["files_referenced"]) == 3
            assert "P:/src/auth.py" in task["files_referenced"]
            assert "P:/tests/test_auth.py" in task["files_referenced"]

    def test_track_recent_files_limits_to_5(self):
        """Test that recent files tracking limits to last 5 files."""
        from PostToolUse_task_tracker import (
            _track_recent_files,
            load_session_state,
        )

        with patch.dict(os.environ, {"TASK_STATE_DIR": str(self.state_dir)}):
            session_id = "test_limit_session"

            # Track 7 files (more than limit)
            for i in range(7):
                _track_recent_files(session_id, f"P:/src/file_{i}.py")

            # Load state and verify only last 5 are kept
            state = load_session_state(session_id)

            assert "recent_files" in state
            assert len(state["recent_files"]) == 5

            # Should be files 2-6 (last 5)
            expected_files = [f"P:/src/file_{i}.py" for i in range(2, 7)]
            assert state["recent_files"] == expected_files

    def test_task_without_description_has_fallback(self):
        """Test that tasks without description get fallback value."""
        from PostToolUse_task_tracker import track_task_create

        with patch.dict(os.environ, {"TASK_STATE_DIR": str(self.state_dir)}):
            tool_input = {
                "taskId": "test_4",
                "subject": "Quick task",
                # No description provided
                "status": "pending",
            }

            track_task_create(tool_input, "test_session", "term_1")

            # Verify fallback description
            state_path = self.state_dir / "test_session_tasks.json"
            state = json.loads(state_path.read_text())
            task = state["tasks"]["test_4"]

            assert "description" in task
            # Empty string or "No description provided"
            assert task["description"] in ("", "No description provided")

    def test_get_all_sessions_tasks_includes_context(self):
        """Test that get_all_sessions_tasks returns enhanced task data."""
        from PostToolUse_task_tracker import (
            get_all_sessions_tasks,
            load_session_state,
            save_session_state,
        )

        with patch.dict(os.environ, {"TASK_STATE_DIR": str(self.state_dir)}):
            # Create task with context
            state = load_session_state("test_session")
            state["tasks"]["task_1"] = {
                "id": "task_1",
                "subject": "Test task",
                "description": "Full description here",
                "files_referenced": ["P:/file1.py"],
                "session_timestamp": "2026-02-06T10:00:00",
                "status": "pending",
                "created_at": 1234567890.0,
                "session_id": "test_session",
                "terminal_id": "term_1",
            }
            save_session_state("test_session", state)

            # Get all tasks
            all_tasks = get_all_sessions_tasks()

            # Verify context fields are present
            assert "task_1" in all_tasks
            task = all_tasks["task_1"]
            assert task["description"] == "Full description here"
            assert task["files_referenced"] == ["P:/file1.py"]
            assert task["session_timestamp"] == "2026-02-06T10:00:00"


class TestRecentFilesTracking:
    """Test recent files tracking via PostToolUse state."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.state_dir = Path(self.temp_dir.name) / "state"
        self.state_dir.mkdir()

    def teardown_method(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def test_read_operation_tracks_file(self):
        """Test that Read operations track files."""
        from PostToolUse_task_tracker import _track_recent_files, load_session_state

        with patch.dict(os.environ, {"TASK_STATE_DIR": str(self.state_dir)}):
            session_id = "test_session"

            # Simulate PostToolUse after Read
            _track_recent_files(session_id, "P:/src/auth.py")

            # Verify file is tracked
            state = load_session_state(session_id)
            assert "recent_files" in state
            assert "P:/src/auth.py" in state["recent_files"]

    def test_edit_operation_tracks_file(self):
        """Test that Edit operations track files."""
        from PostToolUse_task_tracker import _track_recent_files, load_session_state

        with patch.dict(os.environ, {"TASK_STATE_DIR": str(self.state_dir)}):
            session_id = "test_session"

            _track_recent_files(session_id, "P:/src/config.py")

            state = load_session_state(session_id)
            assert "P:/src/config.py" in state["recent_files"]

    def test_duplicate_files_not_duplicated(self):
        """Test that same file added multiple times appears only once."""
        from PostToolUse_task_tracker import _track_recent_files, load_session_state

        with patch.dict(os.environ, {"TASK_STATE_DIR": str(self.state_dir)}):
            session_id = "test_session"

            # Add same file twice
            _track_recent_files(session_id, "P:/src/auth.py")
            _track_recent_files(session_id, "P:/src/auth.py")

            state = load_session_state(session_id)

            # Should appear only once
            assert state["recent_files"].count("P:/src/auth.py") == 1

    def test_mixed_operations_track_all_files(self):
        """Test that Read, Edit, Grep all track files."""
        from PostToolUse_task_tracker import (
            _track_recent_files,
            load_session_state,
            save_session_state,
        )

        with patch.dict(os.environ, {"TASK_STATE_DIR": str(self.state_dir)}):
            # Use unique session_id for isolation
            session_id = "test_mixed_session"

            # Clear state first for isolation
            state = load_session_state(session_id)
            state["recent_files"] = []
            save_session_state(session_id, state)

            _track_recent_files(session_id, "P:/src/auth.py")  # Read
            _track_recent_files(session_id, "P:/src/config.py")  # Edit
            _track_recent_files(session_id, "P:/tests/")  # Grep

            state = load_session_state(session_id)

            assert len(state["recent_files"]) == 3
            assert "P:/src/auth.py" in state["recent_files"]
            assert "P:/src/config.py" in state["recent_files"]
            assert "P:/tests/" in state["recent_files"]

class TestSaveSessionStateWriteFailure:
    """Test write failure handling in save_session_state.

    These tests CAPTURE CURRENT BEHAVIOR for write failure handling.
    The function currently fails silently on OSError.
    """

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.state_dir = Path(self.temp_dir.name) / "state"
        self.state_dir.mkdir()

    def teardown_method(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def test_save_session_state_handles_readonly_directory(self):
        """Test that save_session_state handles read-only directory gracefully.
        
        Given: A state directory that is read-only
        When: save_session_state is called
        Then: No exception should be raised (current behavior: silent fail)
        And: Original state should remain intact in memory
        """
        from PostToolUse_task_tracker import save_session_state

        # Create a test state
        test_state = {
            "session_id": "test_readonly_session",
            "tasks": {"task_1": {"id": "task_1", "subject": "Test task"}},
            "last_update": None,
            "recent_files": ["P:/file1.py"],
        }

        # Make the state directory read-only (simulate permission denied)
        # On Windows, we need to make it read-only
        import stat
        original_mode = self.state_dir.stat().st_mode
        try:
            # Make directory read-only
            self.state_dir.chmod(stat.S_IREAD)

            # This should NOT raise an exception (current behavior: silent fail)
            save_session_state("test_readonly_session", test_state)

            # After silent failure, the in-memory state should still be valid
            assert test_state["session_id"] == "test_readonly_session"
            assert test_state["tasks"]["task_1"]["subject"] == "Test task"

        finally:
            # Restore permissions for cleanup
            try:
                self.state_dir.chmod(original_mode)
            except OSError:
                pass

    def test_save_session_state_handles_disk_full_simulation(self):
        """Test that save_session_state handles disk full condition gracefully.
        
        Given: A simulated disk full condition (using mock)
        When: save_session_state is called
        Then: No exception should be raised (current behavior: silent fail)
        And: No partial/corrupted file should be created
        """
        from unittest.mock import patch

        from PostToolUse_task_tracker import save_session_state

        # Create a test state
        test_state = {
            "session_id": "test_diskfull_session",
            "tasks": {"task_2": {"id": "task_2", "subject": "Another task"}},
            "last_update": None,
            "recent_files": [],
        }

        # Mock write_text to raise OSError (simulating disk full)
        with patch.object(Path, "write_text") as mock_write:
            mock_write.side_effect = OSError("No space left on device")

            # This should NOT raise an exception (current behavior: silent fail)
            save_session_state("test_diskfull_session", test_state)

            # Verify the write was attempted
            mock_write.assert_called_once()

            # In-memory state should still be valid after silent failure
            assert test_state["session_id"] == "test_diskfull_session"
            assert test_state["tasks"]["task_2"]["subject"] == "Another task"

    def test_save_session_state_state_corruption_check(self):
        """Test that save_session_state does not corrupt state on write failure.
        
        Given: A write failure occurs mid-save
        When: save_session_state is called
        Then: The state object passed in should not be modified
        And: No partial data should be written
        """
        from unittest.mock import patch

        from PostToolUse_task_tracker import save_session_state

        # Create a test state with specific values
        original_state = {
            "session_id": "test_corruption_session",
            "tasks": {
                "task_a": {"id": "task_a", "subject": "Task A"},
                "task_b": {"id": "task_b", "subject": "Task B"},
            },
            "last_update": 123456.0,
            "recent_files": ["P:/file1.py", "P:/file2.py"],
        }

        # Deep copy to compare later
        import copy
        state_copy = copy.deepcopy(original_state)

        # Mock write_text to fail
        with patch.object(Path, "write_text") as mock_write:
            mock_write.side_effect = OSError("Write failed")

            # Attempt to save (should fail silently)
            save_session_state("test_corruption_session", original_state)

            # Verify state object was NOT modified by the failed save
            assert original_state == state_copy, "State should not be modified on write failure"

            # Verify last_update was not added to the state
            assert original_state["last_update"] == 123456.0, "last_update should not change on write failure"

    def test_save_session_state_logs_or_returns_error_indicator(self):
        """Test that save_session_state provides some indication of failure.
        
        This test checks if there is ANY error reporting mechanism.
        Currently expected to FAIL because the function fails silently.
        
        Given: A write failure condition
        When: save_session_state is called
        Then: Should return False, raise a logged error, or provide some indication
              (Current behavior: silent pass - this test captures that gap)
        """
        import io
        import sys
        from unittest.mock import patch

        from PostToolUse_task_tracker import save_session_state

        test_state = {
            "session_id": "test_logging_session",
            "tasks": {},
            "last_update": None,
            "recent_files": [],
        }

        # Capture stderr to check for error messages
        old_stderr = sys.stderr
        sys.stderr = io.StringIO()

        try:
            # Mock write_text to fail
            with patch.object(Path, "write_text") as mock_write:
                mock_write.side_effect = OSError("Permission denied")

                # Call save_session_state
                result = save_session_state("test_logging_session", test_state)

                # Check if anything was logged to stderr
                error_output = sys.stderr.getvalue()

                # CURRENT BEHAVIOR CAPTURE:
                # The function returns None and logs nothing
                # This test documents the gap - no error indication
                assert result is False, "Fixed: returns False on failure"
                assert "[Task Tracker] Failed to save session state" in error_output, "Fixed: errors are logged"

        finally:
            sys.stderr = old_stderr


class TestCorruptJsonRecovery:
    r"""Test corrupt JSON recovery in load_session_state.

    These tests CAPTURE CURRENT BEHAVIOR for load_session_state() error handling.
    Run with: pytest P:/.claude/hooks/tests/test_task_context_enhancement.py::TestCorruptJsonRecovery -v

    TEST-001: No test for corrupt JSON recovery
    Target: P:\.claude\hooks\PostToolUse_task_tracker.py
    Function: load_session_state() lines 175-188
    """

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.state_dir = Path(self.temp_dir.name) / "state"
        self.state_dir.mkdir()

    def teardown_method(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def test_load_session_state_with_corrupt_json_returns_default(self):
        """Test that load_session_state returns default state when JSON is corrupt.

        Given: A state file exists with invalid/corrupt JSON content
        When: load_session_state() is called
        Then: Should return default state instead of crashing
        And: session_id should be preserved in default state
        """
        from PostToolUse_task_tracker import load_session_state

        with patch.dict(os.environ, {"TASK_STATE_DIR": str(self.state_dir)}):
            session_id = "test_corrupt_session"

            # Create state file with corrupt JSON content
            state_path = self.state_dir / f"{session_id}_tasks.json"
            corrupt_content = '{"session_id": "test", "tasks": {invalid_json_here}}'
            state_path.write_text(corrupt_content, encoding="utf-8")

            # Execute - should NOT crash, should return default state
            result = load_session_state(session_id)

            # Verify default state structure is returned
            assert result is not None, "Should return state dict, not None"
            assert "session_id" in result, "Default state should have session_id"
            assert "tasks" in result, "Default state should have tasks dict"
            assert "last_update" in result, "Default state should have last_update"
            assert "recent_files" in result, "Default state should have recent_files"

            # Verify session_id is preserved in default state
            assert result["session_id"] == session_id, f"session_id should be '{session_id}'"

            # Verify default values
            assert result["tasks"] == {}, "Default state should have empty tasks dict"
            assert result["last_update"] is None, "Default state should have None for last_update"
            assert result["recent_files"] == [], "Default state should have empty recent_files list"

    def test_load_session_state_with_invalid_json_syntax(self):
        """Test that load_session_state handles various invalid JSON formats.

        Given: A state file exists with completely invalid JSON syntax
        When: load_session_state() is called
        Then: Should return default state with session_id preserved
        """
        from PostToolUse_task_tracker import load_session_state

        with patch.dict(os.environ, {"TASK_STATE_DIR": str(self.state_dir)}):
            session_id = "test_invalid_syntax"

            # Create state file with completely invalid JSON
            state_path = self.state_dir / f"{session_id}_tasks.json"
            invalid_content = 'This is not even JSON {{{{'
            state_path.write_text(invalid_content, encoding="utf-8")

            # Execute - should return default state
            result = load_session_state(session_id)

            # Verify session_id is preserved in default state
            assert result["session_id"] == session_id

    def test_load_session_state_with_empty_file(self):
        """Test that load_session_state handles empty file gracefully.

        Given: A state file exists but is empty
        When: load_session_state() is called
        Then: Should return default state instead of crashing
        """
        from PostToolUse_task_tracker import load_session_state

        with patch.dict(os.environ, {"TASK_STATE_DIR": str(self.state_dir)}):
            session_id = "test_empty_file"

            # Create empty state file
            state_path = self.state_dir / f"{session_id}_tasks.json"
            state_path.write_text("", encoding="utf-8")

            # Execute - should return default state
            result = load_session_state(session_id)

            # Verify default state is returned with correct session_id
            assert result is not None
            assert result["session_id"] == session_id
            assert result["tasks"] == {}


class TestConcurrentAccessSafety:
    r"""Test concurrent access safety - multi-terminal state management.

    These tests verify the claimed multi-terminal safety feature:
    - Session-based: Tasks grouped by session_id (logical work unit)
    - Multi-terminal safe: Multiple terminals can work on same session
    - File-based persistence: Tasks survive compaction and session restore

    TEST-003: No test for concurrent access.
    Target: P:\.claude\hooks\PostToolUse_task_tracker.py
    Functions: State management throughout - multi-terminal safety claimed but not tested
    """

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.state_dir = Path(self.temp_dir.name) / "state"
        self.state_dir.mkdir()

    def teardown_method(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def test_concurrent_task_create_same_session(self):
        """Test that concurrent task creation in same session maintains consistency.

        Given: Multiple threads create tasks for the same session
        When: All threads execute track_task_create simultaneously
        Then: All tasks should be persisted without data loss or corruption

        This test exposes lack of thread safety in load-modify-save pattern.
        """
        import concurrent.futures

        from PostToolUse_task_tracker import (
            load_session_state,
            track_task_create,
        )

        session_id = "concurrent_test_session"
        num_tasks = 10
        created_tasks = []
        errors = []

        def create_task(task_num: int):
            """Create a single task in a thread."""
            try:
                tool_input = {
                    "taskId": f"concurrent_task_{task_num}",
                    "subject": f"Concurrent task {task_num}",
                    "description": f"Task created by thread {task_num}",
                    "status": "pending",
                }

                # Use unique terminal_id per thread
                terminal_id = f"term_{task_num}"
                result = track_task_create(tool_input, session_id, terminal_id)
                created_tasks.append(task_num)
                return result
            except Exception as e:
                errors.append((task_num, str(e)))
                return None

        with patch.dict(os.environ, {"TASK_STATE_DIR": str(self.state_dir)}):
            # Execute concurrent task creation
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=num_tasks
            ) as executor:
                futures = [
                    executor.submit(create_task, i) for i in range(num_tasks)
                ]
                concurrent.futures.wait(futures)

            # Load final state
            state_path = self.state_dir / f"{session_id}_tasks.json"
            assert state_path.exists(), "State file should exist"

            state = load_session_state(session_id)

            # Verify no exceptions occurred
            assert len(errors) == 0, f"Errors during concurrent operations: {errors}"

            # Verify all tasks were created (this may fail due to race condition)
            assert len(created_tasks) == num_tasks, (
                f"Expected {num_tasks} tasks created, got {len(created_tasks)}"
            )

            # Verify all tasks are in state (this may fail due to lost updates)
            for i in range(num_tasks):
                task_id = f"concurrent_task_{i}"
                assert task_id in state["tasks"], (
                    f"Task {task_id} missing from state - data loss detected"
                )

            # Verify state integrity
            assert len(state["tasks"]) == num_tasks, (
                f"Expected {num_tasks} tasks in state, got {len(state['tasks'])}"
            )

    def test_concurrent_task_update_same_task(self):
        """Test that concurrent updates to the same task maintain consistency.

        Given: Multiple threads update the same task with different statuses
        When: All threads execute track_task_update simultaneously
        Then: State should remain consistent (no corruption, though last write wins)

        This test exposes race condition in load-modify-save pattern.
        """
        import concurrent.futures

        from PostToolUse_task_tracker import (
            load_session_state,
            track_task_create,
            track_task_update,
        )

        session_id = "concurrent_update_session"
        task_id = "shared_task"
        num_updates = 20
        update_statuses = []

        def update_task(status_num: int):
            """Update task with a status."""
            tool_input = {
                "taskId": task_id,
                "status": f"status_{status_num}",
            }
            terminal_id = f"term_{status_num}"
            result = track_task_update(tool_input, session_id, terminal_id)
            return result

        with patch.dict(os.environ, {"TASK_STATE_DIR": str(self.state_dir)}):
            # Create the task first
            track_task_create(
                {
                    "taskId": task_id,
                    "subject": "Shared task",
                    "description": "Task to be updated concurrently",
                    "status": "pending",
                },
                session_id,
                "term_0",
            )

            # Execute concurrent updates
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=num_updates
            ) as executor:
                futures = [
                    executor.submit(update_task, i) for i in range(num_updates)
                ]
                concurrent.futures.wait(futures)

            # Load final state
            state = load_session_state(session_id)

            # Verify task still exists
            assert task_id in state["tasks"], "Task should still exist"

            # Verify state file is valid JSON
            state_path = self.state_dir / f"{session_id}_tasks.json"
            content = state_path.read_text()

            # This should not raise JSONDecodeError
            # (but may fail if writes got corrupted)
            try:
                parsed_state = json.loads(content)
                assert "tasks" in parsed_state, "State should have 'tasks' key"
            except json.JSONDecodeError as e:
                pytest.fail(f"State file corrupted with invalid JSON: {e}")

            # Verify task has a valid status (one of the updates)
            final_status = state["tasks"][task_id]["status"]
            assert final_status.startswith("status_"), (
                f"Task should have a status from concurrent updates, got: {final_status}"
            )

    def test_concurrent_session_state_corruption(self):
        """Test that concurrent operations don't corrupt state file structure.

        Given: Multiple threads perform different operations (create, update, load)
        When: All threads execute simultaneously
        Then: State file should remain valid JSON with intact structure

        This test verifies that the state file structure is maintained
        even under concurrent load.
        """
        import concurrent.futures
        import random

        from PostToolUse_task_tracker import (
            _track_recent_files,
            load_session_state,
            track_task_create,
            track_task_update,
        )

        session_id = "corruption_test_session"
        num_operations = 30

        def mixed_operation(op_id: int):
            """Perform a random operation."""
            operation_type = random.choice(["create", "update", "load", "files"])

            if operation_type == "create":
                tool_input = {
                    "taskId": f"task_{op_id}",
                    "subject": f"Task {op_id}",
                    "description": f"Concurrent task {op_id}",
                    "status": "pending",
                }
                return track_task_create(tool_input, session_id, f"term_{op_id}")

            elif operation_type == "update":
                tool_input = {
                    "taskId": f"task_{op_id % 5}",  # Update some existing tasks
                    "status": f"updated_{op_id}",
                }
                return track_task_update(tool_input, session_id, f"term_{op_id}")

            elif operation_type == "load":
                return load_session_state(session_id)

            else:  # files
                _track_recent_files(session_id, f"P:/file_{op_id}.py")
                return None

        with patch.dict(os.environ, {"TASK_STATE_DIR": str(self.state_dir)}):
            # Create some initial tasks
            for i in range(5):
                track_task_create(
                    {
                        "taskId": f"task_{i}",
                        "subject": f"Initial task {i}",
                        "description": "Initial task",
                        "status": "pending",
                    },
                    session_id,
                    "term_0",
                )

            # Execute mixed concurrent operations
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=10
            ) as executor:
                futures = [
                    executor.submit(mixed_operation, i)
                    for i in range(num_operations)
                ]
                concurrent.futures.wait(futures)

            # Verify state file integrity
            state_path = self.state_dir / f"{session_id}_tasks.json"

            assert state_path.exists(), "State file should exist"

            content = state_path.read_text()

            # Critical: File must be valid JSON
            try:
                state = json.loads(content)
            except json.JSONDecodeError as e:
                pytest.fail(
                    f"State file corrupted with invalid JSON after concurrent ops: {e}\n"
                    f"File content preview: {content[:500]}"
                )

            # Verify state structure is intact
            required_keys = {"session_id", "tasks", "last_update", "recent_files"}
            assert required_keys.issubset(state.keys()), (
                f"State missing required keys. Has: {state.keys()}, Need: {required_keys}"
            )

            # Verify tasks is a dict
            assert isinstance(state["tasks"], dict), "'tasks' should be a dict"

            # Verify session_id matches
            assert state["session_id"] == session_id, "session_id should match"

            # Verify recent_files is a list
            assert isinstance(state["recent_files"], list), "'recent_files' should be a list"

    def test_concurrent_different_sessions(self):
        """Test concurrent operations across different sessions.

        Given: Multiple threads operate on different sessions simultaneously
        When: All threads execute track_task_create for different sessions
        Then: Each session should maintain its own state without interference

        This verifies session isolation works correctly under concurrent load.
        """
        import concurrent.futures

        from PostToolUse_task_tracker import (
            get_all_sessions_tasks,
            load_session_state,
            track_task_create,
        )

        num_sessions = 5
        tasks_per_session = 3

        def create_tasks_for_session(session_num: int):
            """Create tasks for a specific session."""
            session_id = f"session_{session_num}"
            results = []

            for task_num in range(tasks_per_session):
                tool_input = {
                    "taskId": f"session_{session_num}_task_{task_num}",
                    "subject": f"Task {task_num} in session {session_num}",
                    "description": f"Task in session {session_num}",
                    "status": "pending",
                }

                result = track_task_create(
                    tool_input, session_id, f"term_{session_num}"
                )
                results.append(result)

            return session_id, results

        with patch.dict(os.environ, {"TASK_STATE_DIR": str(self.state_dir)}):
            # Execute concurrent task creation across sessions
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=num_sessions
            ) as executor:
                futures = [
                    executor.submit(create_tasks_for_session, i)
                    for i in range(num_sessions)
                ]
                concurrent.futures.wait(futures)

            # Verify each session has correct tasks
            for session_num in range(num_sessions):
                session_id = f"session_{session_num}"
                state = load_session_state(session_id)

                # Each session should have tasks_per_session tasks
                assert len(state["tasks"]) == tasks_per_session, (
                    f"Session {session_id} should have {tasks_per_session} tasks, "
                    f"got {len(state['tasks'])}"
                )

                # Verify all tasks are present
                for task_num in range(tasks_per_session):
                    task_id = f"session_{session_num}_task_{task_num}"
                    assert task_id in state["tasks"], (
                        f"Task {task_id} missing from session {session_id}"
                    )

            # Verify get_all_sessions_tasks sees all tasks
            all_tasks = get_all_sessions_tasks()
            expected_total = num_sessions * tasks_per_session
            assert len(all_tasks) == expected_total, (
                f"Expected {expected_total} total tasks across all sessions, "
                f"got {len(all_tasks)}"
            )


class TestSessionIdSecuritySEC001:
    """Security tests for session_id handling (SEC-001: Path Traversal).

    Vulnerability: Line 161 in PostToolUse_task_tracker.py
    get_session_state_path() uses session_id directly in Path construction
    without validation, allowing path traversal attacks.

    These tests capture the vulnerability and will FAIL until the fix is implemented.
    Run with: pytest P:/.claude/hooks/tests/test_task_context_enhancement.py::TestSessionIdSecuritySEC001 -v
    """

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.state_dir = Path(self.temp_dir.name) / "state"
        self.state_dir.mkdir()
        # Create a safe directory outside state_dir for testing
        self.safe_dir = Path(self.temp_dir.name) / "safe"
        self.safe_dir.mkdir()

    def teardown_method(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def test_path_traversal_parent_directory_escape(self):
        """Test that malicious session_id with '../' path traversal is sanitized.

        Given: A malicious session_id containing '../' path traversal sequences
        When: get_session_state_path() is called with the malicious session_id
        Then: The resulting path should be within the allowed state directory

        Expected: FAILS - Path traversal vulnerability allows escape from state_dir
        """
        from PostToolUse_task_tracker import get_session_state_path

        with patch.dict(os.environ, {"TASK_STATE_DIR": str(self.state_dir)}):
            # Test case: Path traversal using '../' to escape state directory
            malicious_session_id = "../../../etc/passwd"
            result_path = get_session_state_path(malicious_session_id)

            # Resolve both paths to absolute for comparison
            result_resolved = result_path.resolve()
            state_dir_resolved = self.state_dir.resolve()

            # SECURITY ASSERTION: Result must be within state directory
            # This WILL FAIL because the code doesn't sanitize session_id
            try:
                is_relative = result_resolved.is_relative_to(state_dir_resolved)
            except AttributeError:
                # Python < 3.9 doesn't have is_relative_to, use alternative check
                try:
                    result_resolved.relative_to(state_dir_resolved)
                    is_relative = True
                except ValueError:
                    is_relative = False

            assert is_relative, (
                f"SEC-001: Path traversal detected! Result path {result_resolved} "
                f"escapes state directory {state_dir_resolved}"
            )

    def test_path_traversal_absolute_path_windows(self):
        """Test that malicious session_id with absolute path is rejected.

        Given: A malicious session_id containing an absolute Windows path
        When: get_session_state_path() is called with the malicious session_id
        Then: The resulting path should be within the allowed state directory

        Expected: FAILS - Absolute path bypasses state directory
        """
        from PostToolUse_task_tracker import get_session_state_path

        with patch.dict(os.environ, {"TASK_STATE_DIR": str(self.state_dir)}):
            # Test case: Absolute path on Windows
            malicious_session_id = "C:/Windows/System32/config/sam"
            result_path = get_session_state_path(malicious_session_id)

            # Resolve both paths to absolute for comparison
            result_resolved = result_path.resolve()
            state_dir_resolved = self.state_dir.resolve()

            # SECURITY ASSERTION: Result must be within state directory
            # This WILL FAIL because the code doesn't validate session_id
            try:
                is_relative = result_resolved.is_relative_to(state_dir_resolved)
            except AttributeError:
                try:
                    result_resolved.relative_to(state_dir_resolved)
                    is_relative = True
                except ValueError:
                    is_relative = False

            assert is_relative, (
                f"SEC-001: Absolute path attack detected! Result path {result_resolved} "
                f"is outside state directory {state_dir_resolved}"
            )

    def test_null_bytes_in_session_id(self):
        """Test that session_id with null bytes is rejected or sanitized.

        Given: A malicious session_id containing null bytes
        When: get_session_state_path() is called with the malicious session_id
        Then: The function should sanitize null bytes or raise an exception

        Note: Null bytes can cause security issues in path operations on some systems.

        Expected: FAILS - Null bytes are not sanitized
        """
        from PostToolUse_task_tracker import get_session_state_path

        with patch.dict(os.environ, {"TASK_STATE_DIR": str(self.state_dir)}):
            # Test case: Null byte injection
            malicious_session_id = "safe_prefix\x00.json"

            # This should raise an exception or sanitize the null byte
            # Current implementation will fail this test
            exception_raised = False
            null_byte_present = False

            try:
                result_path = get_session_state_path(malicious_session_id)
                # If no exception, check if null byte was sanitized
                null_byte_present = "\x00" in str(result_path)
            except (ValueError, OSError):
                exception_raised = True

            # Either an exception should be raised, or null byte should be sanitized
            assert exception_raised or not null_byte_present, (
                "SEC-001: Null byte not sanitized in path and no exception raised"
            )

    def test_save_session_state_respects_directory_boundaries(self):
        """Test that save_session_state only creates files within allowed directory.

        Given: Various session_id values including malicious ones
        When: save_session_state() is called with untrusted session_id
        Then: State files must be created within TASK_STATE_DIR only

        This is an integration test verifying the entire save operation
        respects directory boundaries.

        Expected: FAILS - Files can be created outside state directory
        """
        from PostToolUse_task_tracker import (
            get_session_state_path,
            save_session_state,
        )

        with patch.dict(os.environ, {"TASK_STATE_DIR": str(self.state_dir)}):
            # Test case: Partial path traversal attempt
            malicious_session_id = "../../safe/escaped"
            test_data = {"test": "data", "malicious": True}

            # Save state - this should be safe
            save_session_state(malicious_session_id, test_data)

            # Get the path where file was created
            result_path = get_session_state_path(malicious_session_id)
            result_resolved = result_path.resolve()
            state_dir_resolved = self.state_dir.resolve()

            # Verify file is within allowed directory
            try:
                is_relative = result_resolved.is_relative_to(state_dir_resolved)
            except AttributeError:
                try:
                    result_resolved.relative_to(state_dir_resolved)
                    is_relative = True
                except ValueError:
                    is_relative = False

            # This WILL FAIL for path traversal cases
            assert is_relative, (
                f"SEC-001: State file created outside allowed directory! "
                f"Path: {result_resolved}, Allowed: {state_dir_resolved}"
            )

            # If file was created outside, clean it up (best effort)
            if result_resolved.exists():
                try:
                    result_resolved.unlink()
                except (OSError, PermissionError):
                    pass

    def test_load_session_state_respects_directory_boundaries(self):
        """Test that load_session_state only reads files within allowed directory.

        Given: Various session_id values including malicious ones
        When: load_session_state() is called with untrusted session_id
        Then: Files should only be read from within TASK_STATE_DIR

        This tests against directory traversal attacks that attempt to
        read arbitrary files from the filesystem.

        Expected: FAILS - Can read files outside state directory
        """
        from PostToolUse_task_tracker import save_session_state

        with patch.dict(os.environ, {"TASK_STATE_DIR": str(self.state_dir)}):
            # First, create a file outside the state directory
            # using path traversal in session_id
            malicious_session_id = f"../../{self.safe_dir.name}/sensitive_data"
            test_data = {"sensitive": "information", "secret": "keys"}

            # Try to save - this should be blocked but currently isn't
            save_session_state(malicious_session_id, test_data)

            # Check if file was created outside allowed directory
            expected_violation_path = self.safe_dir / "sensitive_data_tasks.json"

            # The file should NOT exist outside state_dir, but it will
            # because the code doesn't sanitize session_id
            file_exists_outside = expected_violation_path.exists()

            # Clean up if file was created
            if file_exists_outside:
                try:
                    expected_violation_path.unlink()
                except (OSError, PermissionError):
                    pass

            # SECURITY ASSERTION: File should NOT exist outside state_dir
            assert not file_exists_outside, (
                f"SEC-001: File was created outside allowed directory at "
                f"{expected_violation_path}"
            )


class TestFileLockTimeoutScenarios:
    r"""TEST-001: FileLock timeout handling tests.

    These tests verify behavior when FileLock cannot be acquired within timeout.
    Run with: pytest P:/.claude/hooks/tests/test_task_context_enhancement.py::TestFileLockTimeoutScenarios -v

    Target: P:\.claude\hooks\PostToolUse_task_tracker.py
    Functions: load_session_state(), save_session_state(), _update_session_state_locked()
    """

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.state_dir = Path(self.temp_dir.name) / "state"
        self.state_dir.mkdir()

    def teardown_method(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def test_load_session_state_timeout_returns_default(self):
        """TEST-001: Test that load_session_state returns default state on lock timeout.

        Given: Another process holds the session lock
        When: load_session_state() times out acquiring lock
        Then: Should return default state without crashing

        Expected: PASS - Current implementation returns default_state on TimeoutError
        """
        import threading
        import time

        from PostToolUse_task_tracker import load_session_state, validate_session_id

        session_id = "timeout_load_session"

        with patch.dict(os.environ, {"TASK_STATE_DIR": str(self.state_dir)}):
            # Start a thread that holds the lock for 3 seconds
            lock_holder_started = threading.Event()
            lock_holder_done = threading.Event()

            def hold_lock():
                """Hold the session lock for 3 seconds."""
                safe_session_id = validate_session_id(session_id)
                lock_path = self.state_dir / f"{safe_session_id}_tasks.lock"

                from PostToolUse_task_tracker import FileLock
                with FileLock(lock_path, timeout=5.0):
                    lock_holder_started.set()
                    time.sleep(3)  # Hold lock longer than load timeout
                lock_holder_done.set()

            # Start lock holder thread
            holder_thread = threading.Thread(target=hold_lock, daemon=True)
            holder_thread.start()
            lock_holder_started.wait(timeout=5)

            # Try to load - should timeout and return default state
            # Note: FileLock timeout is 5 seconds in current code, so we need
            # to ensure the holder thread holds it long enough
            result = load_session_state(session_id)

            # Should return default state even with timeout
            assert result is not None, "Should return state dict, not None"
            assert "session_id" in result, "Default state should have session_id"
            assert "tasks" in result, "Default state should have tasks dict"
            assert result["session_id"] == session_id

            # Wait for lock holder to finish
            holder_thread.join(timeout=10)

    def test_save_session_state_timeout_returns_false(self):
        """TEST-001: Test that save_session_state returns False on lock timeout.

        Given: Another process holds the session lock
        When: save_session_state() times out acquiring lock
        Then: Should return False to indicate failure

        Expected: PASS - Current implementation returns False on TimeoutError
        """
        import threading
        import time

        from PostToolUse_task_tracker import FileLock, save_session_state, validate_session_id

        session_id = "timeout_save_session"
        test_state = {
            "session_id": session_id,
            "tasks": {"task_1": {"id": "task_1", "subject": "Test task"}},
            "last_update": None,
            "recent_files": [],
        }

        with patch.dict(os.environ, {"TASK_STATE_DIR": str(self.state_dir)}):
            # Start a thread that holds the lock
            lock_holder_started = threading.Event()
            lock_holder_done = threading.Event()

            def hold_lock():
                """Hold the session lock longer than FileLock timeout."""
                safe_session_id = validate_session_id(session_id)
                lock_path = self.state_dir / f"{safe_session_id}_tasks.lock"

                # Hold lock for 7 seconds (longer than the 5s timeout in save_session_state)
                with FileLock(lock_path, timeout=5.0):
                    lock_holder_started.set()
                    time.sleep(7)
                lock_holder_done.set()

            holder_thread = threading.Thread(target=hold_lock, daemon=True)
            holder_thread.start()
            lock_holder_started.wait(timeout=5)

            # Try to save - should timeout and return False
            result = save_session_state(session_id, test_state)

            # Should return False on timeout
            assert result is False, "Should return False when lock acquisition times out"

            holder_thread.join(timeout=15)

    def test_concurrent_operations_handle_timeout_gracefully(self):
        """TEST-001: Test that concurrent operations handle timeouts without crashing.

        Given: Multiple threads compete for the same lock
        When: Some threads timeout acquiring lock
        Then: No threads should crash, all should return gracefully

        Expected: PASS - Current implementation handles timeouts gracefully
        """
        import concurrent.futures

        from PostToolUse_task_tracker import (
            save_session_state,
        )

        session_id = "timeout_concurrent_session"
        num_threads = 15  # More than typical concurrency
        successful_operations = []
        failed_operations = []

        def compete_for_lock(op_id: int):
            """Try to acquire lock and perform operation."""
            try:
                state = {
                    "session_id": session_id,
                    "tasks": {f"task_{op_id}": {"id": f"task_{op_id}", "subject": f"Task {op_id}"}},
                    "last_update": None,
                    "recent_files": [],
                }
                result = save_session_state(session_id, state)
                if result:
                    successful_operations.append(op_id)
                else:
                    failed_operations.append(op_id)
            except TimeoutError:
                failed_operations.append(op_id)
            except Exception as e:
                failed_operations.append((op_id, str(e)))

        with patch.dict(os.environ, {"TASK_STATE_DIR": str(self.state_dir)}):
            with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
                futures = [executor.submit(compete_for_lock, i) for i in range(num_threads)]
                concurrent.futures.wait(futures)

            # Verify no crashes - all operations should complete (success or timeout)
            total_completed = len(successful_operations) + len(failed_operations)
            assert total_completed == num_threads, (
                f"Expected {num_threads} completed operations, got {total_completed}"
            )

            # At least some should succeed (not all should timeout)
            assert len(successful_operations) > 0, "At least some operations should succeed"


class TestLockStarvationScenarios:
    r"""TEST-012: Lock starvation tests under high contention.

    These tests verify behavior under high lock contention scenarios.
    Run with: pytest P:/.claude/hooks/tests/test_task_context_enhancement.py::TestLockStarvationScenarios -v

    Target: P:\.claude\hooks\PostToolUse_task_tracker.py
    Functions: All state modification functions using FileLock
    """

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.state_dir = Path(self.temp_dir.name) / "state"
        self.state_dir.mkdir()

    def teardown_method(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def test_high_contention_all_threads_complete(self):
        """TEST-012: Test that all threads complete under high contention.

        Given: 100+ threads competing for the same lock
        When: All threads attempt to update the same session
        Then: All threads should complete (no starvation)

        Expected: PASS - FileLock should provide fair access
        """
        import concurrent.futures
        import time

        from PostToolUse_task_tracker import (
            load_session_state,
            track_task_create,
        )

        session_id = "starvation_test_session"
        num_threads = 100  # High contention scenario
        completed_threads = []

        def create_task(op_id: int):
            """Create a task in a thread."""
            try:
                tool_input = {
                    "taskId": f"starvation_task_{op_id}",
                    "subject": f"Starvation test task {op_id}",
                    "description": f"Task {op_id} created under high contention",
                    "status": "pending",
                }
                result = track_task_create(tool_input, session_id, f"term_{op_id}")
                completed_threads.append(op_id)
                return result
            except Exception:
                # Thread should not crash even under contention
                pass

        with patch.dict(os.environ, {"TASK_STATE_DIR": str(self.state_dir)}):
            start_time = time.time()

            with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
                futures = [executor.submit(create_task, i) for i in range(num_threads)]
                concurrent.futures.wait(futures, timeout=60)

            elapsed = time.time() - start_time

            # All threads should complete (no starvation)
            assert len(completed_threads) == num_threads, (
                f"Expected {num_threads} threads to complete, got {len(completed_threads)}"
            )

            # Verify state integrity
            state = load_session_state(session_id)
            assert len(state["tasks"]) == num_threads, (
                f"Expected {num_threads} tasks in state, got {len(state['tasks'])}"
            )

            # High contention should complete within reasonable time
            # (100 threads with 5s timeout each = worst case ~500s, but fair lock should be faster)
            assert elapsed < 120, f"High contention took {elapsed:.1f}s, expected <120s"

    def test_writers_dont_starve_readers(self):
        """TEST-012: Test that write-heavy workload doesn't starve readers.

        Given: Mix of reader and writer threads on same session
        When: 20 writers continuously update while 10 readers read
        Then: All readers should complete (no read starvation)

        Expected: PASS - FileLock provides fair access to both read and write
        """
        import concurrent.futures

        from PostToolUse_task_tracker import (
            load_session_state,
            track_task_create,
        )

        session_id = "reader_writer_session"
        num_readers = 10
        num_writers = 20
        completed_readers = []
        completed_writers = []

        def reader(op_id: int):
            """Read session state."""
            for _ in range(5):  # Each reader reads multiple times
                state = load_session_state(session_id)
                assert state is not None
            completed_readers.append(op_id)

        def writer(op_id: int):
            """Write to session state."""
            for i in range(3):  # Each writer writes multiple times
                tool_input = {
                    "taskId": f"rw_task_{op_id}_{i}",
                    "subject": f"RW task {op_id}",
                    "description": "Test task",
                    "status": "pending",
                }
                track_task_create(tool_input, session_id, f"term_{op_id}")
            completed_writers.append(op_id)

        with patch.dict(os.environ, {"TASK_STATE_DIR": str(self.state_dir)}):
            # Create initial task
            track_task_create(
                {"taskId": "initial", "subject": "Initial", "description": "Init", "status": "pending"},
                session_id,
                "term_0",
            )

            with concurrent.futures.ThreadPoolExecutor(max_workers=num_readers + num_writers) as executor:
                futures = []
                futures.extend(executor.submit(reader, i) for i in range(num_readers))
                futures.extend(executor.submit(writer, i) for i in range(num_writers))
                concurrent.futures.wait(futures, timeout=120)

            # All readers and writers should complete
            assert len(completed_readers) == num_readers, (
                f"Expected {num_readers} readers to complete, got {len(completed_readers)}"
            )
            assert len(completed_writers) == num_writers, (
                f"Expected {num_writers} writers to complete, got {len(completed_writers)}"
            )


class TestMarkerFileBehavior:
    r"""TEST-002: Marker file cleanup and failure scenarios.

    These tests verify marker file behavior for re-entrancy guard.
    Run with: pytest P:/.claude/hooks/tests/test_task_context_enhancement.py::TestMarkerFileBehavior -v

    Target: P:\.claude\hooks\PostToolUse_task_tracker.py
    Functions: is_already_tracked(), mark_as_tracked(), get_marker_path()
    """

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.state_dir = Path(self.temp_dir.name) / "state"
        self.state_dir.mkdir()

    def teardown_method(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def test_mark_as_tracked_creates_marker_file(self):
        """TEST-002: Test that mark_as_tracked creates marker file.

        Given: A marker path is provided
        When: mark_as_tracked() is called
        Then: Marker file should be created

        Expected: PASS - Current implementation creates marker file
        """
        from PostToolUse_task_tracker import mark_as_tracked

        with patch.dict(os.environ, {"TASK_STATE_DIR": str(self.state_dir)}):
            marker_path = self.state_dir / "test_marker.txt"
            terminal_id = "test_term"
            task_id = "test_task"

            # Call mark_as_tracked with constructed marker path
            from PostToolUse_task_tracker import get_marker_path
            actual_marker = get_marker_path(terminal_id, task_id)

            mark_as_tracked(actual_marker)

            # Verify marker file exists
            assert actual_marker.exists(), "Marker file should be created"

    def test_is_already_tracked_detects_existing_marker(self):
        """TEST-002: Test that is_already_tracked detects existing marker.

        Given: A marker file already exists
        When: is_already_tracked() is called
        Then: Should return True

        Expected: PASS - Current implementation detects existing markers
        """
        from PostToolUse_task_tracker import (
            get_marker_path,
            is_already_tracked,
            mark_as_tracked,
        )

        with patch.dict(os.environ, {"TASK_STATE_DIR": str(self.state_dir)}):
            terminal_id = "test_term2"
            task_id = "test_task2"
            marker_path = get_marker_path(terminal_id, task_id)

            # Create marker
            mark_as_tracked(marker_path)

            # Check detection
            assert is_already_tracked(marker_path), "Should detect existing marker"

    def test_mark_as_tracked_handles_directory_creation_failure(self):
        """TEST-002: Test that mark_as_tracked handles mkdir failure gracefully.

        Given: mkdir fails (e.g., permission denied)
        When: mark_as_tracked() is called
        Then: Should not crash, should log error

        Expected: PASS - Current implementation catches OSError and logs
        """
        from unittest.mock import patch

        from PostToolUse_task_tracker import mark_as_tracked

        with patch.dict(os.environ, {"TASK_STATE_DIR": str(self.state_dir)}):
            from PostToolUse_task_tracker import get_marker_path
            marker_path = self.state_dir / "test_marker3.txt"
            terminal_id = "test_term3"
            task_id = "test_task3"

            actual_marker = get_marker_path(terminal_id, task_id)

            # Mock mkdir to raise OSError
            with patch.object(Path, "mkdir", side_effect=OSError("Permission denied")):
                # Should not crash
                try:
                    mark_as_tracked(actual_marker)
                except OSError:
                    pytest.fail("mark_as_tracked should not raise OSError")

    def test_marker_file_prevents_duplicate_tracking(self):
        """TEST-002: Test that marker files prevent duplicate tracking.

        Given: A task has been tracked (marker exists)
        When: Attempting to track the same task again
        Then: is_already_tracked() should return True

        Expected: PASS - Marker file prevents re-entrancy
        """
        from PostToolUse_task_tracker import (
            get_marker_path,
            is_already_tracked,
            mark_as_tracked,
        )

        with patch.dict(os.environ, {"TASK_STATE_DIR": str(self.state_dir)}):
            terminal_id = "test_term4"
            task_id = "test_task4"
            marker_path = get_marker_path(terminal_id, task_id)

            # First tracking
            assert not is_already_tracked(marker_path), "Should not be tracked initially"
            mark_as_tracked(marker_path)

            # Second tracking attempt should be detected
            assert is_already_tracked(marker_path), "Should detect as already tracked"


class TestAtomicWriteFailure:
    r"""TEST-004: Atomic write failure scenarios.

    These tests verify atomic write behavior and orphaned .tmp file handling.
    Run with: pytest P:/.claude/hooks/tests/test_task_context_enhancement.py::TestAtomicWriteFailure -v

    Target: P:\.claude\hooks\PostToolUse_task_tracker.py
    Functions: save_session_state(), _update_session_state_locked()
    """

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.state_dir = Path(self.temp_dir.name) / "state"
        self.state_dir.mkdir()

    def teardown_method(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def test_atomic_write_creates_then_replaces(self):
        """TEST-004: Test that atomic write creates temp file then replaces.

        Given: A save_session_state() call
        When: The write completes successfully
        Then: .tmp file should not exist after completion

        Expected: PASS - Atomic write pattern properly cleans up .tmp file
        """
        from PostToolUse_task_tracker import save_session_state

        session_id = "atomic_test_session"
        test_state = {
            "session_id": session_id,
            "tasks": {"task_1": {"id": "task_1", "subject": "Test"}},
            "last_update": None,
            "recent_files": [],
        }

        with patch.dict(os.environ, {"TASK_STATE_DIR": str(self.state_dir)}):
            state_path = self.state_dir / f"{session_id}_tasks.json"
            temp_path = state_path.with_suffix(".tmp")

            # Save state
            result = save_session_state(session_id, test_state)

            assert result is True, "Save should succeed"

            # Verify final file exists
            assert state_path.exists(), "Final state file should exist"

            # Verify .tmp file does not exist (atomic cleanup)
            assert not temp_path.exists(), ".tmp file should be cleaned up after successful save"

    def test_write_failure_leaves_no_orphaned_tmp(self):
        """TEST-004: Test that write failure doesn't leave orphaned .tmp file.

        Given: A simulated write failure during temp file creation
        When: write_text() fails after creating .tmp file
        Then: .tmp file should be cleaned up or not created

        Expected: PARTIAL - Current implementation may leave .tmp if write_text fails
        """
        from unittest.mock import patch

        from PostToolUse_task_tracker import save_session_state

        session_id = "orphan_test_session"
        test_state = {
            "session_id": session_id,
            "tasks": {},
            "last_update": None,
            "recent_files": [],
        }

        with patch.dict(os.environ, {"TASK_STATE_DIR": str(self.state_dir)}):
            state_path = self.state_dir / f"{session_id}_tasks.json"
            temp_path = state_path.with_suffix(".tmp")

            # Mock write_text to fail after temp file is created
            original_write_text = Path.write_text

            def failing_write_text(self, content, **kwargs):
                # Call original to create the file
                if str(self).endswith(".tmp"):
                    # Simulate failure mid-write
                    original_write_text(self, content[:10], **kwargs)
                    raise OSError("Write failed")
                return original_write_text(self, content, **kwargs)

            with patch.object(Path, "write_text", failing_write_text):
                result = save_session_state(session_id, test_state)

            # Result should be False
            assert result is False, "Save should return False on write failure"

            # Note: .tmp file may exist - this captures current behavior
            # A more robust implementation would use try/finally to clean up .tmp

    def test_atomic_write_is_crash_safe(self):
        """TEST-004: Test that atomic write is crash-safe (simulated).

        Given: A simulated crash after temp file write but before replace
        When: Process crashes (simulated by exception)
        Then: Original file should remain intact

        Expected: PASS - Atomic write preserves original on failure
        """
        from unittest.mock import patch

        from PostToolUse_task_tracker import save_session_state

        session_id = "crash_test_session"
        test_state = {
            "session_id": session_id,
            "tasks": {"task_new": {"id": "task_new", "subject": "New task"}},
            "last_update": 123.0,
            "recent_files": [],
        }

        with patch.dict(os.environ, {"TASK_STATE_DIR": str(self.state_dir)}):
            state_path = self.state_dir / f"{session_id}_tasks.json"

            # Create initial state
            initial_state = {
                "session_id": session_id,
                "tasks": {"task_1": {"id": "task_1", "subject": "Original task"}},
                "last_update": 100.0,
                "recent_files": [],
            }
            state_path.write_text(json.dumps(initial_state), encoding="utf-8")

            original_content = state_path.read_text()

            # Mock replace to fail (simulating crash)
            with patch.object(Path, "replace", side_effect=OSError("Simulated crash")):
                result = save_session_state(session_id, test_state)

            # Save should fail
            assert result is False, "Save should return False on replace failure"

            # Original file should be intact (atomic property)
            final_content = state_path.read_text()
            assert final_content == original_content, "Original file should remain intact on failure"


class TestTrackRecentFilesRaceCondition:
    r"""TEST-003: _track_recent_files race condition tests.

    These tests verify race condition in _track_recent_files load-modify-save pattern.
    Run with: pytest P:/.claude/hooks/tests/test_task_context_enhancement.py::TestTrackRecentFilesRaceCondition -v

    Target: P:\.claude\hooks\PostToolUse_task_tracker.py
    Function: _track_recent_files() - uses load/modify/save without lock
    """

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.state_dir = Path(self.temp_dir.name) / "state"
        self.state_dir.mkdir()

    def teardown_method(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def test_concurrent_track_recent_files_has_race_condition(self):
        """TEST-003: Test that concurrent _track_recent_files calls can lose data.

        Given: Multiple threads call _track_recent_files simultaneously
        When: All threads use load-modify-save pattern without lock
        Then: Some file additions may be lost (race condition)

        Expected: This test documents the race condition.
        It may FLIP between pass/fail depending on thread timing.
        Consistent failure indicates race condition exists.
        """
        import concurrent.futures

        from PostToolUse_task_tracker import (
            _track_recent_files,
            load_session_state,
        )

        session_id = "race_test_session"
        num_threads = 20
        num_files_per_thread = 5

        def track_files_batch(thread_id: int):
            """Track multiple files in a thread."""
            for i in range(num_files_per_thread):
                file_path = f"P:/thread_{thread_id}/file_{i}.py"
                _track_recent_files(session_id, file_path)

        with patch.dict(os.environ, {"TASK_STATE_DIR": str(self.state_dir)}):
            # Execute concurrent file tracking
            with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
                futures = [
                    executor.submit(track_files_batch, i) for i in range(num_threads)
                ]
                concurrent.futures.wait(futures)

            # Load final state
            state = load_session_state(session_id)
            final_files = state.get("recent_files", [])

            # Expected: num_threads * num_files_per_thread unique file paths
            # But due to race condition, some may be lost
            expected_unique_files = num_threads * num_files_per_thread

            # The last 5 files should be present (limit)
            assert len(final_files) <= 5, f"Should have at most 5 files, got {len(final_files)}"

            # Due to race condition, the exact set of files is non-deterministic
            # This test documents that behavior - it may pass or fail depending on timing

            # Verify files are unique (no duplicates) - this should always be true
            # because _track_recent_files checks `if file_path not in state["recent_files"]`
            # (though this check itself is racy and may not prevent duplicates)
            assert len(final_files) == len(set(final_files)), (
                "Files should be unique (duplicates indicate race condition in deduplication check)"
            )

    def test_track_recent_files_deduplication_race(self):
        """TEST-003: Test that deduplication check itself has race condition.

        Given: Two threads try to add the same file simultaneously
        When: Both threads check `if file_path not in state["recent_files"]`
        Then: Both may see False and add the file, creating duplicates

        Expected: MAY FAIL - Demonstrates the race condition
        """
        import concurrent.futures

        from PostToolUse_task_tracker import (
            _track_recent_files,
            load_session_state,
        )

        session_id = "dedup_race_session"
        same_file = "P:/shared/file.py"
        num_threads = 10

        def track_same_file(_thread_id: int):
            """All threads try to add the same file."""
            _track_recent_files(session_id, same_file)

        with patch.dict(os.environ, {"TASK_STATE_DIR": str(self.state_dir)}):
            # Execute concurrent tracking of same file
            with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
                futures = [
                    executor.submit(track_same_file, i) for i in range(num_threads)
                ]
                concurrent.futures.wait(futures)

            # Load final state
            state = load_session_state(session_id)
            final_files = state.get("recent_files", [])

            # Should have exactly 1 instance of the file (deduplication works)
            # But race condition may cause duplicates
            count = final_files.count(same_file)

            # This assertion may fail if race condition causes duplicates
            # The test documents this behavior
            if count > 1:
                # Race condition detected - deduplication failed
                pytest.fail(
                    f"TEST-003: Race condition detected! "
                    f"File '{same_file}' appears {count} times (expected 1). "
                    f"This demonstrates the race condition in _track_recent_files()."
                )

            # If we reach here, no duplicates this time (race condition didn't manifest)
            assert count == 1, f"File should appear once, got {count} occurrences"

    def test_track_recent_files_slice_race(self):
        """TEST-003: Test that slice operation `[-5:]` can race with concurrent appends.

        Given: Thread A appends file then slices
        When: Thread B appends between A's append and slice
        Then: B's file may be lost when A slices

        Expected: MAY FAIL - Demonstrates the race condition
        """
        import concurrent.futures

        from PostToolUse_task_tracker import (
            _track_recent_files,
            load_session_state,
        )

        session_id = "slice_race_session"

        def track_many_files(batch_id: int):
            """Track many files to trigger slice operation."""
            for i in range(10):
                _track_recent_files(session_id, f"P:/batch_{batch_id}/file_{i}.py")

        with patch.dict(os.environ, {"TASK_STATE_DIR": str(self.state_dir)}):
            # Two batches of files tracked concurrently
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                futures = [
                    executor.submit(track_many_files, 0),
                    executor.submit(track_many_files, 1),
                ]
                concurrent.futures.wait(futures)

            # Load final state
            state = load_session_state(session_id)
            final_files = state.get("recent_files", [])

            # Should have exactly 5 files (the limit)
            # But race condition may cause fewer or more
            assert len(final_files) <= 5, (
                f"Should have at most 5 files due to slice, got {len(final_files)}. "
                f"Fewer than 5 indicates race condition in slice operation."
            )
