"""Project Context Repository.

Ported from MCP Memory Keeper ContextRepository pattern.
Provides CRUD operations for project context management.

Constitutional Requirements:
- Solo developer optimization (simple, direct operations)
- Evidence-based implementation (proven patterns from MCP Memory Keeper)
- Force multiplier (extensible CRUD operations)
- No enterprise bloat (direct SQLite, no ORM)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

# Conditional imports for package and standalone usage
try:
    from ..validation.validators import (
        ValidationError,
        detect_context_from_operation,
        detect_context_from_path,
        validate_description,
        validate_metadata,
        validate_tsk_id,
        validate_worktree_path,
    )
    from .base_repository import BaseRepository, RepositoryResult
except ImportError:
    from base_repository import BaseRepository, RepositoryResult
    try:
        from validation.config import get_config
    except ImportError:
        # Standalone fallback
        def get_config():
            import os
            from dataclasses import dataclass
            @dataclass
            class DummyConfig:
                blocking_mode: bool = os.getenv('CKS_BLOCKING_MODE', 'false').lower() == 'true'
            return DummyConfig()


logger = logging.getLogger(__name__)


@dataclass
class ProjectContext:
    """Project context entity."""
    id: str
    tsk_id: str
    worktree_path: str
    description: str | None = None
    active: bool = False
    metadata: dict[str, Any] | None = None
    created_at: str | None = None
    updated_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'tsk_id': self.tsk_id,
            'worktree_path': self.worktree_path,
            'description': self.description,
            'active': self.active,
            'metadata': self.metadata,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
        }


class ProjectContextRepository(BaseRepository):
    """Repository for project context CRUD operations."""

    def initialize_schema(self) -> bool:
        """Initialize project contexts table."""
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS project_contexts (
                id TEXT PRIMARY KEY,
                tsk_id TEXT NOT NULL UNIQUE,
                worktree_path TEXT NOT NULL,
                description TEXT,
                active INTEGER DEFAULT 0,
                metadata TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.logger.info("Project context schema initialized")
        return True

    def create(self, tsk_id: str, worktree_path: str, description: str = "", metadata: dict[str, Any] | None = None):
        """Create new project context."""
        from validation.validators import validate_tsk_id, validate_worktree_path
        validated_tsk_id = validate_tsk_id(tsk_id)
        validated_path = validate_worktree_path(worktree_path)

        cursor = self.conn.cursor()
        context_id = self._generate_id()
        now = self._current_timestamp()

        cursor.execute("""
            INSERT INTO project_contexts (id, tsk_id, worktree_path, description, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (context_id, validated_tsk_id, validated_path, description, now, now))

        self.conn.commit()
        self.conn.commit()

        return RepositoryResult(success=True, data=self.get_by_tsk_id(validated_tsk_id))

    def get_by_tsk_id(self, tsk_id: str) -> ProjectContext | None:
        """Get context by TSK ID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM project_contexts WHERE tsk_id = ?", (tsk_id,))
        row = cursor.fetchone()
        return self._row_to_context(row) if row else None

    def get_active_context(self) -> ProjectContext | None:
        """Get currently active project context."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM project_contexts WHERE active = 1 LIMIT 1")
        row = cursor.fetchone()
        return self._row_to_context(row) if row else None

    def set_active_context(self, tsk_id: str) -> RepositoryResult:
        """Set active project context."""
        cursor = self.conn.cursor()
        cursor.execute("UPDATE project_contexts SET active = 0")
        cursor.execute("UPDATE project_contexts SET active = 1 WHERE tsk_id = ?", (tsk_id,))
        self.conn.commit()
        return RepositoryResult(success=True)

    def list_all(self) -> list[ProjectContext]:
        """List all project contexts."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM project_contexts ORDER BY created_at DESC")
        return [self._row_to_context(row) for row in cursor.fetchall()]

    def update(self, tsk_id: str, **updates) -> RepositoryResult:
        """Update project context."""
        return RepositoryResult(success=False, error="Not implemented")

    def delete(self, tsk_id: str) -> RepositoryResult:
        """Delete project context."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM project_contexts WHERE tsk_id = ?", (tsk_id,))
        return RepositoryResult(success=True)

    def validate_operation(self, operation_type: str, operation_target: str = "", operation_description: str = "") -> tuple[bool, str]:
        """Validate operation against active context.

        Returns:
            (allowed: bool, message: str)

        In blocking mode (CKS_BLOCKING_MODE=true), operations that don't match
        the active context are blocked. In warning mode, only a warning is returned.
        """
        active_context = self.get_active_context()
        if not active_context:
            return True, "No active project context"

        # Get config for blocking mode
        try:
            config = get_config()
            blocking_mode = config.blocking_mode
        except:
            blocking_mode = False

        # Simple detection logic
        if operation_target:
            if 'platform' in operation_target.lower():
                detected = 'TSK-ALT-PLATFORM-DOWNLOADING'
            elif 'gpu' in operation_target.lower():
                detected = 'TSK-122225-GPUWorkloadIntegration-1457'
            else:
                detected = None

            if detected and detected != active_context.tsk_id:
                if blocking_mode:
                    return False, f"Operation BLOCKED: Active context is {active_context.tsk_id}, but operation suggests {detected}. Use --force to bypass or switch context with './context set {detected}'"
                else:
                    return True, f"Context warning: Active is {active_context.tsk_id}, operation suggests {detected} (blocking mode disabled, use CKS_BLOCKING_MODE=true to enable)"

        return True, "Operation allowed"

    def get_operation_log(self, tsk_id: str, limit: int = 100, offset: int = 0):
        """Get operation log."""
        return []

    def _row_to_context(self, row) -> ProjectContext | None:
        """Convert database row to ProjectContext."""
        if not row:
            return None
        return ProjectContext(
            id=row['id'],
            tsk_id=row['tsk_id'],
            worktree_path=row['worktree_path'],
            description=row['description'],
            active=bool(row['active']),
            metadata=None,
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )
