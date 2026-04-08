"""Project Context CKS Adapter.

Main adapter class integrating project context management with CKS.
Provides high-level API for project context operations.

Constitutional Requirements:
- Solo developer optimization (simple, intuitive API)
- Evidence-based implementation (proven patterns from MCP Memory Keeper)
- Force multiplier (integrates with CKS and SoloSessionBridge)
- No enterprise bloat (direct Python, no protocol overhead)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

# Try relative imports first (for package usage), then absolute (for standalone)
try:
    from .repositories.base_repository import RepositoryResult
    from .repositories.checkpoint_repository import (
        CheckpointRepository,
        ContextCheckpoint,
    )
    from .repositories.project_context_repository import (
        ProjectContext,
        ProjectContextRepository,
    )
    from .validation.validators import (
        ValidationError,
        validate_tsk_id,
        validate_worktree_path,
    )
except ImportError:
    # Standalone execution - use absolute imports
    from repositories.base_repository import RepositoryResult
    from repositories.checkpoint_repository import (
        CheckpointRepository,
        ContextCheckpoint,
    )
    from repositories.project_context_repository import (
        ProjectContext,
        ProjectContextRepository,
    )


logger = logging.getLogger(__name__)


class ProjectContextCKSAdapter:
    """Adapter integrating project context with CKS.

    This is the main entry point for project context operations,
    providing a high-level API that integrates with CKS storage.

    Usage:
        adapter = ProjectContextCKSAdapter(db_path="P:/__csf/data/cks.db")

        # Create project context
        adapter.create_context(
            tsk_id="TSK-ALT-PLATFORM-DOWNLOADING",
            worktree_path="P:/yt-fts-alt-platforms",
            description="YouTube alternative platforms"
        )

        # Set active context
        adapter.set_active_context("TSK-ALT-PLATFORM-DOWNLOADING")

        # Validate operations
        allowed, message = adapter.validate_operation("edit", "P:/yt-fts-alt-platforms/file.py")
    """

    def __init__(self, db_path: str | Path) -> None:
        """Initialize adapter with CKS database path.

        Args:
            db_path: Path to CKS SQLite database

        """
        self.db_path = str(db_path)
        self.context_repo = ProjectContextRepository(self.db_path)
        self.checkpoint_repo = CheckpointRepository(self.db_path)
        self.logger = logging.getLogger(f"{__name__}.ProjectContextCKSAdapter")

        # Initialize schema
        self.context_repo.initialize_schema()

    # Context CRUD operations

    def create_context(
        self,
        tsk_id: str,
        worktree_path: str,
        description: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> RepositoryResult:
        """Create new project context.

        Args:
            tsk_id: TSK ID (e.g., TSK-ALT-PLATFORM-DOWNLOADING)
            worktree_path: Path to git worktree
            description: Optional description
            metadata: Optional metadata dictionary

        Returns:
            RepositoryResult with created ProjectContext

        """
        return self.context_repo.create(tsk_id, worktree_path, description, metadata)

    def get_context(self, tsk_id: str) -> ProjectContext | None:
        """Get context by TSK ID."""
        try:
            return self.context_repo.get_by_tsk_id(tsk_id)
        except Exception as e:
            self.logger.exception(f"Failed to get context: {e}")
            return None

    def get_active_context(self) -> ProjectContext | None:
        """Get currently active project context."""
        try:
            return self.context_repo.get_active_context()
        except Exception as e:
            self.logger.exception(f"Failed to get active context: {e}")
            return None

    def set_active_context(self, tsk_id: str) -> RepositoryResult:
        """Set active project context."""
        result = self.context_repo.set_active_context(tsk_id)
        if result.success:
            self.logger.info(f"Active context set to: {tsk_id}")
        return result

    def list_contexts(self) -> list[ProjectContext]:
        """List all project contexts."""
        try:
            return self.context_repo.list_all()
        except Exception as e:
            self.logger.exception(f"Failed to list contexts: {e}")
            return []

    def update_context(self, tsk_id: str, **updates) -> RepositoryResult:
        """Update project context fields."""
        return self.context_repo.update(tsk_id, **updates)

    def delete_context(self, tsk_id: str) -> RepositoryResult:
        """Delete project context."""
        return self.context_repo.delete(tsk_id)

    # Operation validation

    def validate_operation(
        self,
        operation_type: str,
        operation_target: str = "",
        operation_description: str = "",
    ) -> tuple[bool, str]:
        """Validate operation against active context.

        Args:
            operation_type: Type of operation ('read', 'edit', 'write', 'task', 'bash')
            operation_target: Target of operation (file path, command, etc.)
            operation_description: Description of operation

        Returns:
            (allowed: bool, message: str)

        """
        try:
            return self.context_repo.validate_operation(
                operation_type,
                operation_target,
                operation_description,
            )
        except Exception as e:
            self.logger.exception(f"Validation error: {e}")
            return True, f"Validation bypassed due to error: {e}"

    # Checkpoint operations

    def create_checkpoint(
        self,
        checkpoint_name: str,
        description: str = "",
        tsk_id: str | None = None,
        checkpoint_data: dict[str, Any] | None = None,
    ) -> RepositoryResult:
        """Create checkpoint for current or specified context.

        Args:
            checkpoint_name: Name for the checkpoint
            description: Optional description
            tsk_id: Optional TSK ID (defaults to active context)
            checkpoint_data: Optional checkpoint data

        Returns:
            RepositoryResult with created checkpoint

        """
        try:
            # Get context
            context = self.get_context(tsk_id) if tsk_id else self.get_active_context()

            if not context:
                return RepositoryResult(
                    success=False,
                    error="No active context and no TSK ID provided",
                )

            # Get internal context ID from database
            cursor = self.context_repo.conn.cursor()
            cursor.execute(
                "SELECT rowid FROM project_contexts WHERE tsk_id = ?",
                (context.tsk_id,),
            )
            row = cursor.fetchone()
            if not row:
                return RepositoryResult(success=False, error="Context not found in database")

            context_id = row["rowid"]

            # Create checkpoint
            return self.checkpoint_repo.create(
                context_id=context_id,
                checkpoint_name=checkpoint_name,
                description=description,
                checkpoint_data=checkpoint_data,
            )

        except Exception as e:
            return RepositoryResult(success=False, error=f"Failed to create checkpoint: {e}")

    def list_checkpoints(
        self, tsk_id: str | None = None, limit: int = 100
    ) -> list[ContextCheckpoint]:
        """List checkpoints for context."""
        try:
            # Get context
            context = self.get_context(tsk_id) if tsk_id else self.get_active_context()

            if not context:
                return []

            # Get internal context ID
            cursor = self.context_repo.conn.cursor()
            cursor.execute(
                "SELECT rowid FROM project_contexts WHERE tsk_id = ?",
                (context.tsk_id,),
            )
            row = cursor.fetchone()
            if not row:
                return []

            context_id = row["rowid"]
            return self.checkpoint_repo.list_by_context(context_id, limit)

        except Exception as e:
            self.logger.exception(f"Failed to list checkpoints: {e}")
            return []

    # Utility methods

    def detect_context_from_path(self, file_path: str) -> str | None:
        """Detect project context from file path."""
        from .validation.validators import detect_context_from_path

        return detect_context_from_path(file_path)

    def detect_context_from_operation(
        self,
        operation_type: str,
        description: str,
    ) -> str | None:
        """Detect project context from operation description."""
        from .validation.validators import detect_context_from_operation

        return detect_context_from_operation(operation_type, description)

    def get_operation_log(
        self,
        tsk_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Any]:
        """Get operation log for a context."""
        try:
            return self.context_repo.get_operation_log(tsk_id, limit, offset)
        except Exception as e:
            self.logger.exception(f"Failed to get operation log: {e}")
            return []

    def close(self) -> None:
        """Close database connections."""
        self.context_repo.close()
        self.checkpoint_repo.close()
