"""
Test suite for TaskIdentityManager with TDD approach.

These tests follow RED-GREEN-REFACTOR TDD cycle:
- RED: Tests fail initially (no implementation)
- GREEN: Minimal implementation to pass tests
- REFACTOR: Improve code quality while tests pass

Module: __lib/task_identity_manager.py

Tests cover the 5-source resilience chain for task identification:
1. Environment variable (TASK_NAME)
2. Session file (session-task-{terminal_id}.json)
3. Compact metadata (last-compact-metadata-{terminal_id}.json)
4. Git worktree mapping (task-worktree-mapping.json)
5. User prompt fallback
"""

import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "__lib"))

# Import module to test
try:
    from task_identity_manager import TaskIdentityManager
    MODULE_EXISTS = True
except ImportError:
    MODULE_EXISTS = False

# Unique test identifiers to prevent collisions
import uuid


def get_test_id():
    return f"test_{uuid.uuid4().hex[:8]}"


@pytest.fixture(autouse=True)
def clean_state_files():
    """
    Clean up state files before each test to prevent cross-test contamination.

    TaskIdentityManager uses a hardcoded hooks_dir for state files, not the
    tmp_path passed to the constructor. This fixture cleans up those shared
    state files before each test to ensure test isolation.
    """
    # Get the state directory from TaskIdentityManager's hardcoded location
    hooks_dir = Path(__file__).resolve().parent.parent / "__lib"
    state_dir = hooks_dir / ".state" / "task-identity"

    # Clean up before test
    if state_dir.exists():
        for file in state_dir.glob("session-task-*.json"):
            file.unlink(missing_ok=True)
        for file in state_dir.glob("last-compact-metadata-*.json"):
            file.unlink(missing_ok=True)
        mapping_file = state_dir / "task-worktree-mapping.json"
        mapping_file.unlink(missing_ok=True)

    yield

    # Clean up after test
    if state_dir.exists():
        for file in state_dir.glob("session-task-*.json"):
            file.unlink(missing_ok=True)
        for file in state_dir.glob("last-compact-metadata-*.json"):
            file.unlink(missing_ok=True)
        mapping_file = state_dir / "task-worktree-mapping.json"
        mapping_file.unlink(missing_ok=True)


@pytest.mark.skipif(not MODULE_EXISTS, reason="task_identity_manager module not found")
class TestGetCurrentTaskFromEnvVar:
    """Test suite for getting task from TASK_NAME environment variable."""

    def test_get_current_task_from_env_var(self, tmp_path):
        """
        Test that TASK_NAME environment variable is read first (highest priority).

        Given: TASK_NAME environment variable is set
        When: get_current_task() is called
        Then: Task from environment variable is returned (priority 1)
        """
        # Arrange
        manager = TaskIdentityManager(project_root=tmp_path)

        # Act
        with patch.dict('os.environ', {'TASK_NAME': 'CWO12'}):
            task = manager.get_current_task()

        # Assert
        assert task == 'CWO12', f"Expected 'CWO12', got {task}"

    def test_get_current_task_env_var_overrides_session_file(self, tmp_path):
        """
        Test that TASK_NAME overrides session file (priority test).

        Given: TASK_NAME env var is set AND session file has different task
        When: get_current_task() is called
        Then: Task from environment variable is returned (higher priority)
        """
        # Arrange
        manager = TaskIdentityManager(project_root=tmp_path, terminal_id='test_terminal')

        # Create session file with different task
        session_data = {
            "task_name": "OLD_TASK",
            "task_id": "task_old_task",
            "terminal_id": "test_terminal",
            "started": datetime.now(UTC).isoformat(),
            "checksum": "abc123"
        }
        manager.session_file.parent.mkdir(parents=True, exist_ok=True)
        manager.session_file.write_text(json.dumps(session_data))

        # Act - env var should override session file
        with patch.dict('os.environ', {'TASK_NAME': 'NEW_TASK'}):
            task = manager.get_current_task()

        # Assert
        assert task == 'NEW_TASK', f"Expected 'NEW_TASK' from env, got {task}"


@pytest.mark.skipif(not MODULE_EXISTS, reason="task_identity_manager module not found")
class TestGetCurrentTaskFromSessionFile:
    """Test suite for getting task from session file."""

    def test_get_current_task_from_session_file(self, tmp_path):
        """
        Test that session file is read as fallback when env var not set.

        Given: TASK_NAME not set, session file exists with task
        When: get_current_task() is called
        Then: Task from session file is returned (priority 2)
        """
        # Arrange
        manager = TaskIdentityManager(project_root=tmp_path, terminal_id='test_terminal')

        # Create session file
        session_data = {
            "task_name": "CWO99",
            "task_id": "task_cwo99",
            "terminal_id": "test_terminal",
            "started": datetime.now(UTC).isoformat(),
            "checksum": "def456"
        }
        manager.session_file.parent.mkdir(parents=True, exist_ok=True)
        manager.session_file.write_text(json.dumps(session_data))

        # Act - ensure no env var
        with patch.dict('os.environ', {}, clear=False):
            # Remove TASK_NAME if it exists
            env_copy = dict(os.environ)
            env_copy.pop('TASK_NAME', None)
            with patch.dict('os.environ', env_copy, clear=True):
                task = manager.get_current_task()

        # Assert
        assert task == 'CWO99', f"Expected 'CWO99', got {task}"

    def test_session_file_terminal_mismatch_returns_none(self, tmp_path):
        """
        Test that session file with wrong terminal_id is rejected.

        Given: Session file exists with different terminal_id
        When: get_current_task() is called
        Then: Returns None to prevent cross-terminal bleeding
        """
        # Arrange
        manager = TaskIdentityManager(project_root=tmp_path, terminal_id='terminal_1')

        # Create session file with different terminal_id
        session_data = {
            "task_name": "CWO99",
            "task_id": "task_cwo99",
            "terminal_id": "terminal_2",  # Different terminal
            "started": datetime.now(UTC).isoformat(),
            "checksum": "def456"
        }
        manager.session_file.parent.mkdir(parents=True, exist_ok=True)
        manager.session_file.write_text(json.dumps(session_data))

        # Act
        task = manager.get_current_task()

        # Assert - should NOT return task due to terminal mismatch
        assert task is None, f"Expected None due to terminal mismatch, got {task}"


@pytest.mark.skipif(not MODULE_EXISTS, reason="task_identity_manager module not found")
class TestGetCurrentTaskFromCompactMetadata:
    """Test suite for getting task from compact metadata."""

    def test_get_current_task_from_compact_metadata(self, tmp_path):
        """
        Test that compact metadata is read as fallback.

        Given: TASK_NAME not set, session file doesn't exist, metadata file exists
        When: get_current_task() is called
        Then: Task from compact metadata is returned (priority 3)
        """
        # Arrange
        manager = TaskIdentityManager(project_root=tmp_path, terminal_id='test_terminal')

        # Create metadata file
        metadata = {
            "task_name": "CWO77",
            "task_id": "task_cwo77",
            "checkpoint_id": "ckpt_123",
            "timestamp": datetime.now(UTC).isoformat(),
            "version": "v1"
        }
        manager.metadata_file.parent.mkdir(parents=True, exist_ok=True)
        manager.metadata_file.write_text(json.dumps(metadata))

        # Act - ensure no env var and no session file
        with patch.dict('os.environ', {}, clear=False):
            env_copy = dict(os.environ)
            env_copy.pop('TASK_NAME', None)
            with patch.dict('os.environ', env_copy, clear=True):
                task = manager.get_current_task()

        # Assert
        assert task == 'CWO77', f"Expected 'CWO77', got {task}"

    def test_compact_metadata_expired_returns_none(self, tmp_path):
        """
        Test that expired compact metadata (> 5 minutes) is rejected.

        Given: Compact metadata exists but is older than 5 minutes
        When: get_current_task() is called
        Then: Returns None (metadata too old)
        """
        # Arrange
        manager = TaskIdentityManager(project_root=tmp_path, terminal_id='test_terminal')

        # Create OLD metadata file (> 5 minutes ago)
        old_timestamp = datetime.now(UTC).isoformat()
        # Manually create old metadata
        metadata = {
            "task_name": "CWO77",
            "task_id": "task_cwo77",
            "checkpoint_id": "ckpt_123",
            "timestamp": old_timestamp,
            "version": "v1"
        }
        manager.metadata_file.parent.mkdir(parents=True, exist_ok=True)
        manager.metadata_file.write_text(json.dumps(metadata))

        # Mock datetime to return a time > 5 minutes after metadata
        with patch('task_identity_manager.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2025, 1, 1, 0, 10, 0, tzinfo=UTC)
            mock_datetime.fromisoformat.return_value = datetime(2025, 1, 1, 0, 0, 0, tzinfo=UTC)

            # Act
            task = manager.get_current_task()

        # Assert - metadata is too old (> 5 minutes)
        assert task is None, f"Expected None for expired metadata, got {task}"


@pytest.mark.skipif(not MODULE_EXISTS, reason="task_identity_manager module not found")
class TestGetCurrentTaskFromGitWorktree:
    """Test suite for getting task from git worktree mapping."""

    def test_get_current_task_from_git_worktree(self, tmp_path):
        """
        Test that git branch mapping is used as fallback.

        Given: TASK_NAME not set, no session/metadata, git branch exists in mapping
        When: get_current_task() is called
        Then: Task from git worktree mapping is returned (priority 4)
        """
        # Arrange
        manager = TaskIdentityManager(project_root=tmp_path, terminal_id='test_terminal')

        # Create mapping file
        mapping_data = {
            "feature/test-branch": "CWO55"
        }
        manager.mapping_file.parent.mkdir(parents=True, exist_ok=True)
        manager.mapping_file.write_text(json.dumps(mapping_data))

        # Mock git command to return the branch
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.stdout = "feature/test-branch\n"
            mock_result.returncode = 0
            mock_run.return_value = mock_result

            # Act
            task = manager.get_current_task()

        # Assert
        assert task == 'CWO55', f"Expected 'CWO55', got {task}"

    def test_git_worktree_unknown_branch_returns_none(self, tmp_path):
        """
        Test that unknown git branch returns None.

        Given: Git branch exists but not in mapping file
        When: get_current_task() is called
        Then: Returns None (branch not mapped to task)
        """
        # Arrange
        manager = TaskIdentityManager(project_root=tmp_path, terminal_id='test_terminal')

        # Create mapping file without current branch
        mapping_data = {
            "feature/other-branch": "CWO55"
        }
        manager.mapping_file.parent.mkdir(parents=True, exist_ok=True)
        manager.mapping_file.write_text(json.dumps(mapping_data))

        # Mock git command to return different branch
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.stdout = "feature/unmapped-branch\n"
            mock_result.returncode = 0
            mock_run.return_value = mock_result

            # Act
            task = manager.get_current_task()

        # Assert
        assert task is None, f"Expected None for unmapped branch, got {task}"

    def test_git_worktree_no_repository_returns_none(self, tmp_path):
        """
        Test that missing git repository returns None.

        Given: Not in a git repository
        When: get_current_task() is called
        Then: Returns None (graceful degradation)
        """
        # Arrange
        manager = TaskIdentityManager(project_root=tmp_path, terminal_id='test_terminal')

        # Mock git command to fail
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = FileNotFoundError("Git not found")

            # Act
            task = manager.get_current_task()

        # Assert
        assert task is None, f"Expected None when git not found, got {task}"


@pytest.mark.skipif(not MODULE_EXISTS, reason="task_identity_manager module not found")
class TestGetCurrentTaskCaching:
    """Test suite for result caching behavior."""

    def test_get_current_task_caches_result(self, tmp_path):
        """
        Test that result is cached for performance.

        Given: get_current_task() returns a task
        When: Called multiple times
        Then: Should return cached result (not re-read sources)
        """
        # Arrange
        manager = TaskIdentityManager(project_root=tmp_path, terminal_id='test_terminal')

        # Act - call multiple times
        with patch.dict('os.environ', {'TASK_NAME': 'CWO12'}):
            task1 = manager.get_current_task()
            task2 = manager.get_current_task()
            task3 = manager.get_current_task()

        # Assert - all should return same result
        assert task1 == task2 == task3 == 'CWO12'
        # Verify env var was not read multiple times (implementation detail)


@pytest.mark.skipif(not MODULE_EXISTS, reason="task_identity_manager module not found")
class TestSetCurrentTask:
    """Test suite for setting current task."""

    def test_set_current_task_writes_to_session_file(self, tmp_path):
        """
        Test that set_current_task writes to session file.

        Given: A task name
        When: set_current_task() is called
        Then: Session file is created with task data and terminal_id
        """
        # Arrange
        manager = TaskIdentityManager(project_root=tmp_path, terminal_id='test_terminal')

        # Act
        result = manager.set_current_task('CWO88')

        # Assert - function returns True
        assert result is True, f"Expected True, got {result}"

        # Assert - session file was created
        assert manager.session_file.exists(), "Session file should exist"

        # Assert - session file contains correct data
        session_data = json.loads(manager.session_file.read_text())
        assert session_data['task_name'] == 'CWO88'
        assert session_data['terminal_id'] == 'test_terminal'
        assert 'started' in session_data
        assert 'checksum' in session_data

    def test_set_current_task_sets_env_var(self, tmp_path):
        """
        Test that set_current_task sets TASK_NAME environment variable.

        Given: A task name
        When: set_current_task() is called
        Then: TASK_NAME environment variable is set
        """
        # Arrange
        manager = TaskIdentityManager(project_root=tmp_path, terminal_id='test_terminal')

        # Act
        manager.set_current_task('CWO99')

        # Assert - env var should be set
        assert os.environ.get('TASK_NAME') == 'CWO99'


@pytest.mark.skipif(not MODULE_EXISTS, reason="task_identity_manager module not found")
class TestRecordActiveCommand:
    """Test suite for recording active commands."""

    def test_record_active_command_saves_command(self, tmp_path):
        """
        Test that record_active_command saves command to active_command.json.

        Given: A command name and phase
        When: record_active_command() is called
        Then: active_command.json is created with command data
        """
        # Arrange
        manager = TaskIdentityManager(project_root=tmp_path, terminal_id='test_terminal')

        # Act
        result = manager.record_active_command('duf', 'pre_mortem', {'context': 'test'})

        # Assert - function returns True
        assert result is True, f"Expected True, got {result}"

        # Assert - active_command.json was created
        active_cmd_file = tmp_path / ".claude" / "active_command.json"
        assert active_cmd_file.exists(), "active_command.json should exist"

        # Assert - file contains correct data
        command_data = json.loads(active_cmd_file.read_text())
        assert command_data['command'] == 'duf'
        assert command_data['phase'] == 'pre_mortem'
        assert command_data['terminal_id'] == 'test_terminal'
        assert command_data['metadata']['context'] == 'test'
        assert 'started_at' in command_data


@pytest.mark.skipif(not MODULE_EXISTS, reason="task_identity_manager module not found")
class TestClearActiveCommand:
    """Test suite for clearing active commands."""

    def test_clear_active_command_removes_command(self, tmp_path):
        """
        Test that clear_active_command removes active_command.json.

        Given: active_command.json exists
        When: clear_active_command() is called
        Then: active_command.json is deleted
        """
        # Arrange - create active_command.json
        manager = TaskIdentityManager(project_root=tmp_path, terminal_id='test_terminal')
        active_cmd_file = tmp_path / ".claude" / "active_command.json"
        active_cmd_file.parent.mkdir(parents=True, exist_ok=True)
        active_cmd_file.write_text('{"command": "test"}')

        # Act
        result = manager.clear_active_command()

        # Assert - function returns True
        assert result is True, f"Expected True, got {result}"

        # Assert - file was deleted
        assert not active_cmd_file.exists(), "active_command.json should be deleted"

    def test_clear_active_command_returns_false_when_no_file(self, tmp_path):
        """
        Test that clear_active_command returns False when file doesn't exist.

        Given: active_command.json does not exist
        When: clear_active_command() is called
        Then: Returns False
        """
        # Arrange
        manager = TaskIdentityManager(project_root=tmp_path, terminal_id='test_terminal')

        # Act
        result = manager.clear_active_command()

        # Assert
        assert result is False, f"Expected False when file doesn't exist, got {result}"


@pytest.mark.skipif(not MODULE_EXISTS, reason="task_identity_manager module not found")
class TestGetTransientTaskId:
    """Test suite for getting transient task ID from active command."""

    def test_get_transient_task_id_from_active_command(self, tmp_path):
        """
        Test that _get_transient_task_id returns adhoc_{command} from active_command.json.

        Given: active_command.json exists with command 'duf'
        When: _get_transient_task_id() is called
        Then: Returns 'adhoc_duf' (highest priority in get_current_task)
        """
        # Arrange
        manager = TaskIdentityManager(project_root=tmp_path, terminal_id='test_terminal')
        active_cmd_file = tmp_path / ".claude" / "active_command.json"
        active_cmd_file.parent.mkdir(parents=True, exist_ok=True)
        active_cmd_file.write_text(json.dumps({"command": "duf", "phase": "pre_mortem"}))

        # Act
        transient_task = manager._get_transient_task_id()

        # Assert
        assert transient_task == 'adhoc_duf', f"Expected 'adhoc_duf', got {transient_task}"

    def test_get_transient_task_id_returns_none_when_no_file(self, tmp_path):
        """
        Test that _get_transient_task_id returns None when no active command.

        Given: active_command.json does not exist
        When: _get_transient_task_id() is called
        Then: Returns None
        """
        # Arrange
        manager = TaskIdentityManager(project_root=tmp_path, terminal_id='test_terminal')

        # Act
        transient_task = manager._get_transient_task_id()

        # Assert
        assert transient_task is None, f"Expected None, got {transient_task}"


@pytest.mark.skipif(not MODULE_EXISTS, reason="task_identity_manager module not found")
class TestFallbackChainPriority:
    """Test suite for verifying fallback chain priority order."""

    def test_fallback_chain_priority_env_var_first(self, tmp_path):
        """
        Test that fallback chain priority: env var > session > metadata > git.

        This is an integration test verifying the complete priority order.
        """
        # Arrange
        manager = TaskIdentityManager(project_root=tmp_path, terminal_id='test_terminal')

        # Create all sources with different tasks
        # 1. Env var (should win)
        with patch.dict('os.environ', {'TASK_NAME': 'FROM_ENV'}):

            # 2. Session file
            session_data = {
                "task_name": "FROM_SESSION",
                "task_id": "task_session",
                "terminal_id": "test_terminal",
                "started": datetime.now(UTC).isoformat(),
                "checksum": "abc"
            }
            manager.session_file.parent.mkdir(parents=True, exist_ok=True)
            manager.session_file.write_text(json.dumps(session_data))

            # 3. Metadata
            metadata = {
                "task_name": "FROM_METADATA",
                "task_id": "task_metadata",
                "checkpoint_id": "ckpt",
                "timestamp": datetime.now(UTC).isoformat(),
                "version": "v1"
            }
            manager.metadata_file.write_text(json.dumps(metadata))

            # 4. Git mapping
            mapping = {"feature/branch": "FROM_GIT"}
            manager.mapping_file.write_text(json.dumps(mapping))

            with patch('subprocess.run') as mock_run:
                mock_result = MagicMock()
                mock_result.stdout = "feature/branch\n"
                mock_run.return_value = mock_result

                # Act
                task = manager.get_current_task()

        # Assert - env var should win
        assert task == 'FROM_ENV', f"Expected 'FROM_ENV' (highest priority), got {task}"

    def test_fallback_chain_priority_session_second(self, tmp_path):
        """
        Test that session file wins when env var not set.
        """
        # Arrange
        manager = TaskIdentityManager(project_root=tmp_path, terminal_id='test_terminal')

        # Create all sources except env var
        # 1. No env var
        with patch.dict('os.environ', {}, clear=False):
            env_copy = dict(os.environ)
            env_copy.pop('TASK_NAME', None)
            with patch.dict('os.environ', env_copy, clear=True):

                # 2. Session file (should win)
                session_data = {
                    "task_name": "FROM_SESSION",
                    "task_id": "task_session",
                    "terminal_id": "test_terminal",
                    "started": datetime.now(UTC).isoformat(),
                    "checksum": "abc"
                }
                manager.session_file.parent.mkdir(parents=True, exist_ok=True)
                manager.session_file.write_text(json.dumps(session_data))

                # 3. Metadata
                metadata = {
                    "task_name": "FROM_METADATA",
                    "task_id": "task_metadata",
                    "checkpoint_id": "ckpt",
                    "timestamp": datetime.now(UTC).isoformat(),
                    "version": "v1"
                }
                manager.metadata_file.write_text(json.dumps(metadata))

                # Act
                task = manager.get_current_task()

        # Assert - session should win
        assert task == 'FROM_SESSION', f"Expected 'FROM_SESSION', got {task}"

    def test_fallback_chain_returns_none_when_all_sources_empty(self, tmp_path):
        """
        Test that None is returned when all sources are empty.
        """
        # Arrange
        manager = TaskIdentityManager(project_root=tmp_path, terminal_id='test_terminal')

        # Act - no sources set up
        with patch.dict('os.environ', {}, clear=False):
            env_copy = dict(os.environ)
            env_copy.pop('TASK_NAME', None)
            with patch.dict('os.environ', env_copy, clear=True):
                task = manager.get_current_task()

        # Assert
        assert task is None, f"Expected None when no sources available, got {task}"


class TestModuleExists:
    """Tests verifying module exists (RED phase confirmation)."""

    def test_module_exists(self):
        """Verify module exists and is importable."""
        from task_identity_manager import TaskIdentityManager
        assert TaskIdentityManager is not None


# Need to import os for env var tests


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
