"""Task Repository Client - Client for TaskRepository integration.

Provides a thin wrapper around TaskRepository for checkpoint system integration.
Tasks are stored in CKS database (.cks/storage/cks.db) with terminal isolation.

Key features:
- Get current task (most recent in_progress task)
- Create checkpoint restore task
- Mark restore task as completed
- Terminal-aware isolation

Constitutional Requirements:
- Solo developer optimization (single source of truth for tasks)
- Multi-terminal safety (terminal_id field for isolation)
- Clean up after restoration (mark completed, not delete)
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Try importing TaskRepository (from CKS)
_TASK_REPO_AVAILABLE = False
TaskRepository = None

try:
    from ..repositories.task_repository import TaskRepository
    _TASK_REPO_AVAILABLE = True
except ImportError:
    try:
        # Fallback: try absolute import from hooks directory
        import sys
        hooks_dir = Path(__file__).resolve().parent
        sys.path.insert(0, str(hooks_dir.parent))
        from repositories.task_repository import TaskRepository
        _TASK_REPO_AVAILABLE = True
    except ImportError:
        _TASK_REPO_AVAILABLE = False
        TaskRepository = None


class TaskRepositoryClient:
    """Client for TaskRepository integration with checkpoint system.

    Provides checkpoint-specific operations on top of TaskRepository:
    - Get current active task for checkpoint capture
    - Create checkpoint restore metadata task
    - Read restore metadata for SessionStart
    - Mark restore task as completed after restoration

    All operations are terminal-aware for multi-terminal isolation.
    """

    def __init__(self, project_root: Path, terminal_id: str):
        """Initialize TaskRepository client.

        Args:
            project_root: Project root directory
            terminal_id: Terminal identifier for isolation
        """
        self.project_root = project_root
        self.terminal_id = terminal_id

        if not _TASK_REPO_AVAILABLE:
            logger.warning("[TaskRepoClient] TaskRepository not available")
            self.repo = None
            return

        db_path = project_root / ".data" / "cks" / "cks.db"
        self.repo = TaskRepository(db_path=str(db_path))

        # Initialize schema (create tables if not exist)
        try:
            self.repo.initialize_schema()
        except Exception as e:
            logger.error(f"[TaskRepoClient] Schema init failed: {e}")
            self.repo = None

    def is_available(self) -> bool:
        """Check if TaskRepository is available.

        Returns:
            True if TaskRepository is available and initialized
        """
        return self.repo is not None

    def get_current_task(self) -> dict[str, Any] | None:
        """Get current active task for checkpoint capture.

        Returns the most recently updated in_progress or blocked task.
        If no active task, returns None (caller should use fallback).

        Returns:
            Task dict with keys: id, name, status, progress_pct, description, etc.
                or None if no active task or repository unavailable
        """
        if not self.is_available():
            return None

        try:
            task = self.repo.get_current_task()
            if task:
                return {
                    "id": task.id,
                    "name": task.name,
                    "status": task.status,
                    "progress_pct": task.progress_pct,
                    "description": task.description,
                    "priority": task.priority,
                    "terminal_id": task.terminal_id,
                    "checkpoint_id": task.checkpoint_id,
                }
        except Exception as e:
            logger.error(f"[TaskRepoClient] Error getting current task: {e}")

        return None

    def create_checkpoint_restore_task(
        self,
        task_name: str,
        task_id: str,
        checkpoint_id: str,
        next_steps: list[str],
    ) -> bool:
        """Create checkpoint restore metadata task.

        This task stores the checkpoint context for session restoration.
        Named "RESTORE_CONTEXT: {terminal_id}" for unique identification.

        Args:
            task_name: The original task name being checkpointed
            task_id: The original task ID
            checkpoint_id: Checkpoint file identifier (without .json extension)
            next_steps: List of next steps for task description

        Returns:
            True if task creation succeeded, False otherwise
        """
        if not self.is_available():
            logger.warning("[TaskRepoClient] Cannot create restore task: repository unavailable")
            return False

        try:
            # Build task name for checkpoint restore
            restore_task_name = f"RESTORE_CONTEXT: {self.terminal_id}"

            # Build task description from next_steps
            if next_steps and len(next_steps) > 0:
                description = f"Checkpoint: {next_steps[0][:100]}"
            else:
                description = f"Checkpoint for task: {task_name}"

            # Build strategic context metadata
            strategic_context = {
                "type": "checkpoint_restore",
                "terminal_id": self.terminal_id,
                "pid": __import__("os").getpid(),
                "checkpoint_id": checkpoint_id,
                "original_task_id": task_id,
                "original_task_name": task_name,
                "created_at": datetime.now(UTC).isoformat(),
            }

            # Check if task already exists (update instead of create)
            existing_task = self.repo.get_by_name(restore_task_name)
            if existing_task:
                # Update existing task with new checkpoint data
                # Note: TaskRepository doesn't have update_description, so we recreate
                logger.info(f"[TaskRepoClient] Updating checkpoint restore task: {restore_task_name}")
                self.repo.delete(restore_task_name)

            # Create new checkpoint restore task
            result = self.repo.create(
                name=restore_task_name,
                description=description,
                priority="high",
                strategic_context=strategic_context,
            )

            if result.success:
                # Update terminal_id and checkpoint_id fields directly in database
                # These fields exist in the schema but aren't set by create()
                cursor = self.repo.conn.cursor()
                cursor.execute("""
                    UPDATE tasks
                    SET terminal_id = ?, checkpoint_id = ?
                    WHERE name = ?
                """, (self.terminal_id, checkpoint_id, restore_task_name))
                self.repo.conn.commit()

                logger.info(f"[TaskRepoClient] Checkpoint restore task created: {restore_task_name}")
                return True
            else:
                logger.error(f"[TaskRepoClient] Failed to create restore task: {result.error}")
                return False

        except Exception as e:
            logger.error(f"[TaskRepoClient] Error creating restore task: {e}")
            return False

    def get_checkpoint_restore_task(self) -> dict[str, Any] | None:
        """Get checkpoint restore metadata task for this terminal.

        Returns the restore task metadata for SessionStart restoration.

        Returns:
            Restore task dict with keys: checkpoint_id, task_id, task_name, strategic_context
                or None if not found or repository unavailable
        """
        if not self.is_available():
            return None

        try:
            restore_task_name = f"RESTORE_CONTEXT: {self.terminal_id}"
            task = self.repo.get_by_name(restore_task_name)

            if task:
                # Verify terminal_id matches (prevent cross-terminal bleed)
                if task.terminal_id and task.terminal_id != self.terminal_id:
                    logger.warning(
                        f"[TaskRepoClient] Terminal mismatch: {task.terminal_id} != {self.terminal_id}"
                    )
                    return None

                # Extract checkpoint context from strategic_context
                strategic_context = task.strategic_context or {}

                return {
                    "checkpoint_id": task.checkpoint_id or strategic_context.get("checkpoint_id"),
                    "task_id": strategic_context.get("original_task_id"),
                    "task_name": strategic_context.get("original_task_name"),
                    "strategic_context": strategic_context,
                }
        except Exception as e:
            logger.error(f"[TaskRepoClient] Error getting restore task: {e}")

        return None

    def mark_restore_completed(self) -> bool:
        """Mark checkpoint restore task as completed after successful restoration.

        This doesn't delete the task - marks as completed for history.
        Old completed tasks can be cleaned up by retention policy.

        Returns:
            True if task was marked completed, False if not found or error
        """
        if not self.is_available():
            return False

        try:
            restore_task_name = f"RESTORE_CONTEXT: {self.terminal_id}"
            task = self.repo.get_by_name(restore_task_name)

            if task:
                # Mark as completed
                self.repo.update_status(restore_task_name, "completed")
                logger.info(f"[TaskRepoClient] Marked restore task as completed: {restore_task_name}")
                return True
        except Exception as e:
            logger.error(f"[TaskRepoClient] Error marking restore completed: {e}")

        return False

    def cleanup_old_restore_tasks(self, max_age_hours: int = 24) -> int:
        """Clean up old completed restore tasks older than threshold.

        Args:
            max_age_hours: Maximum age in hours before cleanup (default: 24)

        Returns:
            Number of tasks cleaned up
        """
        if not self.is_available():
            return 0

        cleaned = 0
        cutoff = datetime.now(UTC).timestamp() - (max_age_hours * 3600)

        try:
            # List all completed restore tasks
            all_tasks = self.repo.list_all(status="completed")

            for task in all_tasks:
                # Check if it's a restore task (starts with "RESTORE_CONTEXT:")
                if not task.name.startswith("RESTORE_CONTEXT:"):
                    continue

                # Check age
                if task.updated_at:
                    try:
                        updated_time = datetime.fromisoformat(task.updated_at)
                        if updated_time.timestamp() < cutoff:
                            # Delete old restore task
                            self.repo.delete(task.name)
                            cleaned += 1
                            logger.debug(f"[TaskRepoClient] Cleaned up old restore task: {task.name}")
                    except (ValueError, TypeError):
                        # Invalid timestamp, skip
                        continue

        except Exception as e:
            logger.error(f"[TaskRepoClient] Error during cleanup: {e}")

        if cleaned > 0:
            logger.info(f"[TaskRepoClient] Cleanup: {cleaned} old restore task(s) deleted")

        return cleaned


if __name__ == "__main__":
    # Test the client
    import sys
    from pathlib import Path

    project_root = Path.cwd()
    terminal_id = "test_terminal"

    client = TaskRepositoryClient(project_root, terminal_id)

    print("Task Repository Client Test")
    print("=" * 50)
    print(f"Available: {client.is_available()}")

    # Test: Get current task
    current = client.get_current_task()
    print(f"Current task: {current}")

    # Test: Create restore task
    success = client.create_checkpoint_restore_task(
        task_name="test_task",
        task_id="task_test_task",
        checkpoint_id="test_task__test_terminal__v1",
        next_steps=["Step 1", "Step 2"],
    )
    print(f"Create restore task: {success}")

    # Test: Get restore task
    restore = client.get_checkpoint_restore_task()
    print(f"Restore task: {restore}")

    # Test: Mark completed
    completed = client.mark_restore_completed()
    print(f"Mark completed: {completed}")
