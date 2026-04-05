"""Task Repository - Task entity management for cross-session context preservation.

Integrates with Project Context to provide comprehensive task tracking:
- Task: Strategic context (goal, approach, success criteria)
- ProjectContext: File-level context (worktree path, active context)
- SessionCheckpoint: Progress snapshots (blockers, next steps, modified files)

Constitutional Requirements:
- Solo developer optimization (simple task management)
- Evidence-based implementation (proven patterns from MCP Memory Keeper)
- Force multiplier (multi-task workflows with checkpoint/restore)
- No enterprise bloat (direct SQLite, no ORM)
"""

from __future__ import annotations

import json
import logging
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

try:
    from ..validation.validators import ValidationError, validate_metadata
    from .base_repository import BaseRepository, RepositoryResult
except ImportError:
    from base_repository import BaseRepository, RepositoryResult


logger = logging.getLogger(__name__)

# Module constants
_DEFAULT_STALE_COMPACT_HOURS: int = 24
_DEFAULT_SCHEMA_VERSION: int = 2  # v2 adds checkpoint_data field for Tasks list storage


@dataclass
class Task:
    """Task entity with strategic context."""
    id: str
    name: str  # e.g., "CWO12", "GPU_WORKLOAD"
    status: str  # "pending", "in_progress", "blocked", "completed"
    progress_pct: int
    created_at: str | None = None
    updated_at: str | None = None
    description: str | None = None
    priority: str | None = None  # "high", "medium", "low"
    strategic_context: dict[str, Any] | None = None
    terminal_id: str | None = None
    checkpoint_id: str | None = None  # Legacy: file-based checkpoint reference
    checkpoint_created_at: str | None = None
    last_compact_at: str | None = None
    checkpoint_data: str | None = None  # Go-forward: full checkpoint JSON in Tasks list
    schema_version: int = 2  # v2 adds checkpoint_data field

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'status': self.status,
            'progress_pct': self.progress_pct,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'description': self.description,
            'priority': self.priority,
            'strategic_context': self.strategic_context,
            'terminal_id': self.terminal_id,
            'checkpoint_id': self.checkpoint_id,
            'checkpoint_created_at': self.checkpoint_created_at,
            'last_compact_at': self.last_compact_at,
            'checkpoint_data': self.checkpoint_data,
            'schema_version': self.schema_version,
        }

    def has_checkpoint(self) -> bool:
        """Check if task has an associated checkpoint.

        Returns:
            True if the task has a non-empty checkpoint_id, False otherwise.
        """
        return bool(self.checkpoint_id)

    def is_stale_compact(self, hours: int = _DEFAULT_STALE_COMPACT_HOURS) -> bool:
        """Check if task's last compact is stale (older than threshold).

        Args:
            hours: Threshold in hours. Defaults to 24.

        Returns:
            True if last_compact_at is None, invalid format, or older than threshold.
        """
        if not self.last_compact_at:
            return True

        try:
            compact_time = datetime.fromisoformat(self.last_compact_at)
        except (ValueError, TypeError):
            return True

        threshold = datetime.now(UTC) - timedelta(hours=hours)
        return compact_time < threshold


class TaskRepository(BaseRepository):
    """Repository for task CRUD operations."""

    def initialize_schema(self) -> bool:
        """Initialize tasks table."""
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                status TEXT DEFAULT 'pending',
                progress_pct INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                description TEXT,
                priority TEXT DEFAULT 'medium',
                strategic_context TEXT,
                terminal_id TEXT,
                checkpoint_id TEXT,
                checkpoint_created_at TEXT,
                last_compact_at TEXT,
                checkpoint_data TEXT,
                schema_version INTEGER DEFAULT 2
            )
        """)

        # Create index on name for fast lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_tasks_name
            ON tasks(name)
        """)

        # Create index on status for queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_tasks_status
            ON tasks(status)
        """)

        self.logger.info("Task schema initialized")
        return True

    def create(self, name: str, description: str = "", priority: str = "medium",
               strategic_context: dict[str, Any] | None = None) -> RepositoryResult:
        """Create new task."""
        task_id = self._generate_id()
        now = self._current_timestamp()

        # Serialize strategic context
        context_json = json.dumps(strategic_context) if strategic_context else None

        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO tasks (id, name, status, progress_pct, created_at, updated_at,
                              description, priority, strategic_context)
            VALUES (?, ?, 'pending', 0, ?, ?, ?, ?, ?)
        """, (task_id, name, now, now, description, priority, context_json))

        self.conn.commit()

        return RepositoryResult(success=True, data=self.get_by_name(name))

    def get_by_name(self, name: str) -> Task | None:
        """Get task by name."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE name = ?", (name,))
        row = cursor.fetchone()
        return self._row_to_task(row) if row else None

    def get_current_task(self) -> Task | None:
        """Get currently active task (most recently updated in_progress task)."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM tasks
            WHERE status IN ('in_progress', 'blocked')
            ORDER BY updated_at DESC
            LIMIT 1
        """)
        row = cursor.fetchone()
        return self._row_to_task(row) if row else None

    def get_by_terminal(self, terminal_id: str) -> Task | None:
        """Get active task by terminal_id.

        Args:
            terminal_id: Terminal identifier (from detect_terminal_id())

        Returns:
            Task with matching terminal_id and in_progress/blocked status, or None.
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM tasks
            WHERE terminal_id = ?
            AND status IN ('in_progress', 'blocked')
            ORDER BY updated_at DESC
            LIMIT 1
        """, (terminal_id,))
        row = cursor.fetchone()
        return self._row_to_task(row) if row else None

    def list_all(self, status: str | None = None) -> list[Task]:
        """List all tasks, optionally filtered by status."""
        cursor = self.conn.cursor()

        if status:
            cursor.execute("""
                SELECT * FROM tasks
                WHERE status = ?
                ORDER BY updated_at DESC
            """, (status,))
        else:
            cursor.execute("""
                SELECT * FROM tasks
                ORDER BY updated_at DESC
            """)

        return [self._row_to_task(row) for row in cursor.fetchall()]

    def update_status(self, name: str, status: str) -> RepositoryResult:
        """Update task status."""
        if status not in ['pending', 'in_progress', 'blocked', 'completed']:
            return RepositoryResult(success=False, error=f"Invalid status: {status}")

        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE tasks
            SET status = ?, updated_at = ?
            WHERE name = ?
        """, (status, self._current_timestamp(), name))

        self.conn.commit()
        return RepositoryResult(success=True)

    def update_progress(self, name: str, progress_pct: int) -> RepositoryResult:
        """Update task progress percentage."""
        if not 0 <= progress_pct <= 100:
            return RepositoryResult(success=False, error="Progress must be 0-100")

        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE tasks
            SET progress_pct = ?, updated_at = ?
            WHERE name = ?
        """, (progress_pct, self._current_timestamp(), name))

        self.conn.commit()
        return RepositoryResult(success=True)

    def delete(self, name: str) -> RepositoryResult:
        """Delete task."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE name = ?", (name,))
        self.conn.commit()
        return RepositoryResult(success=True)

    def update(self, name: str, description: str | None = None,
               strategic_context: dict[str, Any] | None = None,
               checkpoint_id: str | None = None,
               terminal_id: str | None = None) -> RepositoryResult:
        """Update task fields.

        Args:
            name: Task name (unique identifier)
            description: New description (optional)
            strategic_context: New strategic context metadata (optional)
            checkpoint_id: New checkpoint ID (optional)
            terminal_id: New terminal ID (optional)

        Returns:
            RepositoryResult with success status
        """
        updates = []
        params = []

        if description is not None:
            updates.append("description = ?")
            params.append(description)

        if strategic_context is not None:
            updates.append("strategic_context = ?")
            params.append(json.dumps(strategic_context))

        if checkpoint_id is not None:
            updates.append("checkpoint_id = ?")
            params.append(checkpoint_id)

        if terminal_id is not None:
            updates.append("terminal_id = ?")
            params.append(terminal_id)

        if not updates:
            return RepositoryResult(success=False, error="No fields to update")

        # Always update updated_at timestamp
        updates.append("updated_at = ?")
        params.append(self._current_timestamp())

        params.append(name)  # WHERE clause parameter

        cursor = self.conn.cursor()
        cursor.execute(f"""
            UPDATE tasks
            SET {', '.join(updates)}
            WHERE name = ?
        """, params)

        self.conn.commit()
        return RepositoryResult(success=True)

    def save_checkpoint(self, task_name: str, checkpoint_data: dict[str, Any]) -> RepositoryResult:
        """Save checkpoint data directly to task object (go-forward storage).

        Args:
            task_name: Name of the task to attach checkpoint to
            checkpoint_data: Full checkpoint payload as dictionary
                Includes: task_name, task_type, progress_percent, blocker,
                          next_steps, handover, active_files, transcript_path, etc.

        Returns:
            RepositoryResult with success status and updated task
        """
        # Serialize checkpoint data to JSON
        checkpoint_json = json.dumps(checkpoint_data)

        # Update task with checkpoint data
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE tasks
            SET checkpoint_data = ?,
                checkpoint_created_at = ?,
                updated_at = ?
            WHERE name = ?
        """, (checkpoint_json, self._current_timestamp(), self._current_timestamp(), task_name))

        if cursor.rowcount == 0:
            return RepositoryResult(success=False, error=f"Task '{task_name}' not found")

        self.conn.commit()
        return RepositoryResult(success=True, data=self.get_by_name(task_name))

    def load_checkpoint(self, task_name: str) -> dict[str, Any] | None:
        """Load checkpoint data from task object.

        Args:
            task_name: Name of the task with checkpoint

        Returns:
            Checkpoint data as dictionary, or None if:
            - Task not found
            - Task has no checkpoint_data
            - checkpoint_data is invalid JSON
        """
        task = self.get_by_name(task_name)
        if not task:
            return None

        if not task.checkpoint_data:
            return None

        try:
            return json.loads(task.checkpoint_data)
        except json.JSONDecodeError:
            logger.warning(f"Invalid checkpoint_data JSON for task '{task_name}'")
            return None

    def has_checkpoint_in_tasks_list(self, task_name: str) -> bool:
        """Check if task has checkpoint data in Tasks list (go-forward storage).

        Args:
            task_name: Name of the task to check

        Returns:
            True if task exists and has checkpoint_data field
        """
        task = self.get_by_name(task_name)
        return task is not None and task.checkpoint_data is not None

    def delete_checkpoint(self, task_name: str) -> RepositoryResult:
        """Remove checkpoint data from task object (task remains).

        Args:
            task_name: Name of the task to remove checkpoint from

        Returns:
            RepositoryResult with success status
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE tasks
            SET checkpoint_data = NULL,
                checkpoint_created_at = NULL,
                updated_at = ?
            WHERE name = ?
        """, (self._current_timestamp(), task_name))

        self.conn.commit()
        return RepositoryResult(success=True)

    def _row_to_task(self, row: sqlite3.Row | Any) -> Task | None:
        """Convert database row to Task.

        Args:
            row: SQLite row object with task data. Supports backward compatibility
                for legacy databases that may not have checkpoint columns.

        Returns:
            Task instance or None if row is empty.
        """
        if not row:
            return None

        strategic_context = None
        if row['strategic_context']:
            try:
                strategic_context = json.loads(row['strategic_context'])
            except json.JSONDecodeError:
                pass

        return Task(
            id=row['id'],
            name=row['name'],
            status=row['status'],
            progress_pct=row['progress_pct'],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            description=row['description'],
            priority=row['priority'],
            strategic_context=strategic_context,
            # Backward compatibility: check key existence for checkpoint fields
            terminal_id=row['terminal_id'] if 'terminal_id' in row.keys() else None,
            checkpoint_id=row['checkpoint_id'] if 'checkpoint_id' in row.keys() else None,
            checkpoint_created_at=row['checkpoint_created_at'] if 'checkpoint_created_at' in row.keys() else None,
            last_compact_at=row['last_compact_at'] if 'last_compact_at' in row.keys() else None,
            checkpoint_data=row['checkpoint_data'] if 'checkpoint_data' in row.keys() else None,
            schema_version=row['schema_version'] if 'schema_version' in row.keys() else _DEFAULT_SCHEMA_VERSION,
        )
