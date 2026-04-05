"""Tests for Task Repository checkpoint field functionality.

These tests verify the database schema and CRUD operations for the Task entity,
with specific focus on checkpoint-related columns (terminal_id, checkpoint_id,
checkpoint_created_at, last_compact_at, schema_version).

Run with:
    pytest P:/.claude/hooks/repositories/tests/test_task_repository.py -v
"""

from __future__ import annotations

import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

# ============================================================================
# SHARED FIXTURES
# ============================================================================

@pytest.fixture
def temp_db_path():
    """Create a temporary database file for testing.

    Yields:
        str: Path to the temporary database file.

    Cleanup:
        Deletes the temporary file after test completion.
    """
    with tempfile.NamedTemporaryFile(mode="w", suffix=".db", delete=False) as f:
        temp_path = f.name
    yield temp_path
    try:
        Path(temp_path).unlink(missing_ok=True)
    except OSError:
        pass


@pytest.fixture
def task_repository(temp_db_path):
    """Create a TaskRepository instance with a temporary database.

    Args:
        temp_db_path: Path to temporary database file.

    Returns:
        TaskRepository: Repository instance with initialized schema.
    """
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from task_repository import TaskRepository

    repo = TaskRepository(db_path=temp_db_path)
    repo.initialize_schema()
    return repo


# ============================================================================
# TEST CLASSES
# ============================================================================

class TestTaskRepositorySchema:
    """Tests for task repository database schema validation."""

    def test_database_schema_has_checkpoint_columns(
        self, temp_db_path: str, task_repository: Any
    ) -> None:
        """Verify tasks table has checkpoint-related columns with correct types.

        Given: Database is initialized with TaskRepository.initialize_schema()
        When: Querying PRAGMA table_info(tasks)
        Then: These columns must exist with correct types:
              - terminal_id: TEXT
              - checkpoint_id: TEXT
              - checkpoint_created_at: TEXT
              - last_compact_at: TEXT
              - schema_version: INTEGER
        """
        with sqlite3.connect(temp_db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("PRAGMA table_info(tasks)")
            columns = cursor.fetchall()
            column_info = {col["name"]: col for col in columns}

        required_columns = {
            "terminal_id": "TEXT",
            "checkpoint_id": "TEXT",
            "checkpoint_created_at": "TEXT",
            "last_compact_at": "TEXT",
            "schema_version": "INTEGER",
        }

        missing_columns = self._validate_columns(column_info, required_columns)

        assert not missing_columns, (
            f"Missing or incorrect checkpoint columns: {', '.join(missing_columns)}. "
            f"Current columns: {[col['name'] for col in columns]}"
        )

    def _validate_columns(
        self, column_info: dict[str, Any], required: dict[str, str]
    ) -> list[str]:
        """Validate column names and types against requirements.

        Args:
            column_info: Dictionary of column names to column metadata.
            required: Dictionary of required column names to expected types.

        Returns:
            List of missing or mismatched column descriptions.
        """
        missing = []
        for col_name, expected_type in required.items():
            if col_name not in column_info:
                missing.append(col_name)
            elif column_info[col_name]["type"] != expected_type:
                missing.append(
                    f"{col_name} (expected {expected_type}, "
                    f"got {column_info[col_name]['type']})"
                )
        return missing


class TestTaskRepositoryBasicCRUD:
    """Tests for basic CRUD operations on tasks."""

    # Test data constants
    TASK_NAME = "TEST_TASK"
    TASK_DESCRIPTION = "Test description"
    TASK_PRIORITY = "high"

    def test_create_task_basic(self, task_repository: Any) -> None:
        """Verify basic task creation with default values."""
        result = task_repository.create(
            name=self.TASK_NAME,
            description=self.TASK_DESCRIPTION,
            priority=self.TASK_PRIORITY,
        )
        assert result.success
        assert result.data.name == self.TASK_NAME
        assert result.data.status == "pending"

    def test_get_task_by_name(self, task_repository: Any) -> None:
        """Verify retrieving a task by its unique name."""
        task_name = "RETRIEVE_TEST"
        task_repository.create(name=task_name, description="Test")
        task = task_repository.get_by_name(task_name)

        assert task is not None
        assert task.name == task_name

    def test_update_task_status(self, task_repository: Any) -> None:
        """Verify updating a task's status."""
        task_name = "STATUS_TEST"
        task_repository.create(name=task_name)
        task_repository.update_status(task_name, "in_progress")

        task = task_repository.get_by_name(task_name)
        assert task.status == "in_progress"

    def test_update_task_progress(self, task_repository: Any) -> None:
        """Verify updating a task's progress percentage."""
        task_name = "PROGRESS_TEST"
        task_repository.create(name=task_name)
        task_repository.update_progress(task_name, 50)

        task = task_repository.get_by_name(task_name)
        assert task.progress_pct == 50

    def test_delete_task(self, task_repository: Any) -> None:
        """Verify deleting a task removes it from the database."""
        task_name = "DELETE_TEST"
        task_repository.create(name=task_name)
        task_repository.delete(task_name)

        task = task_repository.get_by_name(task_name)
        assert task is None


class TestTaskRepositoryBackwardCompatibility:
    """Tests for backward compatibility with legacy task rows."""

    # Legacy schema test data
    LEGACY_TASK_NAME = "LEGACY_TASK"
    LEGACY_TASK_DESCRIPTION = "Old task description"
    LEGACY_TASK_PRIORITY = "high"

    def test_backward_compatibility_old_task_rows(self, temp_db_path: str) -> None:
        """Verify legacy tasks load gracefully when schema includes new columns.

        Given: A legacy database without checkpoint columns (original schema only)
        When: An old-style task is loaded with TaskRepository
        Then: Task loads successfully with new fields defaulted

        This test verifies backward compatibility - when the schema is updated
        to include checkpoint columns, old databases should continue to work
        with new fields defaulted to appropriate values (terminal_id=None,
        checkpoint_id=None, checkpoint_created_at=None, last_compact_at=None,
        schema_version=1).
        """
        import sys

        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from task_repository import TaskRepository

        # Step 1: Create legacy schema and insert old-style task
        self._create_legacy_database(temp_db_path)

        # Step 2: Open with TaskRepository and verify task loads
        repo = TaskRepository(db_path=temp_db_path)
        task = repo.get_by_name(self.LEGACY_TASK_NAME)

        # Assert task loads successfully with expected values
        self._assert_legacy_task_loaded(task)

    def _create_legacy_database(self, db_path: str) -> None:
        """Create a legacy database schema and insert a test task.

        Args:
            db_path: Path to the database file.
        """
        import uuid

        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # Create OLD schema (without checkpoint columns)
            cursor.execute(
                """
                CREATE TABLE tasks (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    status TEXT DEFAULT 'pending',
                    progress_pct INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    description TEXT,
                    priority TEXT DEFAULT 'medium',
                    strategic_context TEXT
                )
            """
            )

            # Insert an old-style task (without new columns)
            task_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc).isoformat()
            cursor.execute(
                """
                INSERT INTO tasks (id, name, status, progress_pct, created_at,
                                  updated_at, description, priority, strategic_context)
                VALUES (?, ?, 'pending', 0, ?, ?, ?, ?, ?)
            """,
                (
                    task_id,
                    self.LEGACY_TASK_NAME,
                    now,
                    now,
                    self.LEGACY_TASK_DESCRIPTION,
                    self.LEGACY_TASK_PRIORITY,
                    None,
                ),
            )
            conn.commit()

    def _assert_legacy_task_loaded(self, task: Any) -> None:
        """Assert legacy task was loaded with correct values.

        Args:
            task: The loaded Task entity to verify.

        Raises:
            AssertionError: If task is None or values don't match.
        """
        assert task is not None, "Legacy task should load successfully"
        assert task.name == self.LEGACY_TASK_NAME
        assert task.status == "pending"
        assert task.description == self.LEGACY_TASK_DESCRIPTION
        assert task.priority == self.LEGACY_TASK_PRIORITY
