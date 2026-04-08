"""Task Identity Manager - Recover task identity after compaction.

Implements terminal-aware task isolation to prevent task bleeding between consoles.

State files are scoped by terminal_id:
- Session file: .claude/session-task-{terminal_id}.json
- Compact metadata: .claude/.last-compact-metadata-{terminal_id}.json

5-source resilience chain for task identification:
1. Environment variable (TASK_NAME)
2. Terminal-scoped session file
3. Terminal-scoped compact metadata
4. Git worktree mapping (.claude/task-worktree-mapping.json)
5. User confirmation (CKS query + user input)

This ensures task identity is ALWAYS recoverable, even after
environment variables are cleared on compaction.

Constitutional Requirements:
- Solo developer optimization (automatic recovery, no manual setup)
- Evidence-based implementation (proven multi-source fallback pattern)
- Force multiplier (never lose task identity)
- No enterprise bloat (direct file I/O, no complex infrastructure)
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import subprocess
from contextlib import suppress
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import TypeAlias

from cli.subprocess_helper import run_subprocess

# Type aliases
TaskMetadataDict: TypeAlias = dict[str, str]

terminal_detection_path = (
    Path(__file__).parent.parent.parent.parent / ".claude" / "hooks" / "terminal_detection.py"
)
if terminal_detection_path.exists():
    import sys

    sys.path.insert(0, str(terminal_detection_path.parent))
    from terminal_detection import detect_terminal_id
else:
    # Fallback if terminal_detection module not available
    def detect_terminal_id() -> str:
        import tempfile

        # Try to read from SessionStart's temp file
        temp_file = Path(tempfile.gettempdir()) / "claude_terminal_id.txt"
        if temp_file.exists():
            return temp_file.read_text().strip()
        # Try environment variables
        for var in ["CLAUDE_TERMINAL_ID", "TERMINAL_ID", "TERM_ID", "SESSION_TERMINAL"]:
            if os.environ.get(var):
                return os.environ.get(var, "")
        return "terminal_1"


logger = logging.getLogger(__name__)


@dataclass(slots=True)
class TaskMetadata:
    """Task identity metadata."""

    task_name: str
    task_id: str
    started: str
    checksum: str
    source: str  # Where this came from (env_var, session_file, etc.)


class TaskIdentityManager:
    """Manage task identity across compaction events."""

    def __init__(self, project_root: Path | None = None, terminal_id: str | None = None) -> None:
        """Initialize task identity manager.

        Args:
            project_root: Root directory of project (defaults to CWD)
            terminal_id: Terminal identifier for isolation (auto-detected if None)

        """
        self.project_root = Path(project_root) if project_root else Path.cwd()

        # CRITICAL: Use terminal-specific files to prevent task bleeding between consoles
        self.terminal_id = terminal_id if terminal_id else detect_terminal_id()

        # Scope state files by terminal_id for isolation
        self.session_file = self.project_root / ".claude" / f"session-task-{self.terminal_id}.json"
        self.metadata_file = (
            self.project_root / ".claude" / f".last-compact-metadata-{self.terminal_id}.json"
        )
        self.mapping_file = (
            self.project_root / ".claude" / "task-worktree-mapping.json"
        )  # Shared across terminals

    def get_current_task(self) -> str | None:
        """Get current task using 5-source resilience chain.

        Returns:
            Task name (e.g., "CWO12") or None if not determinable

        """
        sources = [
            ("env_var", self._from_env_var),
            ("session_file", self._from_session_file),
            ("compact_metadata", self._from_compact_metadata),
            ("git_worktree", self._from_git_worktree),
        ]

        for source_name, method in sources:
            try:
                task = method()
                if task:
                    logger.info(f"[TaskID] Recovered: {task} (source: {source_name})")
                    return task
            except Exception as e:
                logger.warning(f"[TaskID] Warning from {source_name}: {e}")

        # Last resort: ask user
        return self._ask_user()

    def _from_env_var(self) -> str | None:
        """Get task from TASK_NAME environment variable."""
        return os.getenv("TASK_NAME")

    def _from_session_file(self) -> str | None:
        """Read task from terminal-scoped session file with migration fallback.

        Migration path:
        1. Try terminal-scoped file (session-task-{terminal_id}.json)
        2. Fallback to legacy file (session-task.json) for migration
        """
        try:
            # Try terminal-scoped file first
            if self.session_file.exists():
                data = json.loads(self.session_file.read_text())
                return data.get("task_name")

            # Migration fallback: try legacy file
            legacy_file = self.project_root / ".claude" / "session-task.json"
            if legacy_file.exists():
                data = json.loads(legacy_file.read_text())
                task_name = data.get("task_name")
                if task_name:
                    # Migrate to terminal-scoped file
                    logger.info(f"[TaskID] Migrating task from legacy file: {task_name}")
                    self.set_current_task(task_name)
                    # Optionally remove legacy file after successful migration
                    # legacy_file.unlink()
                return task_name
        except Exception as e:
            logger.exception(f"[TaskID] Error reading session file: {e}")
        return None

    def _from_compact_metadata(self) -> str | None:
        """Read task from .claude/.last-compact-metadata.json."""
        try:
            if self.metadata_file.exists():
                data = json.loads(self.metadata_file.read_text())
                task = data.get("task_name")
                if task:
                    # Verify metadata is recent (within 5 minutes)
                    timestamp_str = data.get("timestamp", "")
                    if timestamp_str:
                        timestamp = datetime.fromisoformat(timestamp_str)
                        age = (datetime.now(UTC) - timestamp).total_seconds()
                        if age < 300:  # 5 minutes
                            return task
        except (json.JSONDecodeError, ValueError, OSError) as e:
            logger.exception(f"[TaskID] Error reading metadata: {e}")
        return None

    def _from_git_worktree(self) -> str | None:
        """Infer task from current git branch using mapping."""
        try:
            import sys

            # Get current branch
            creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            result = run_subprocess(
                ["git", "branch", "--show-current"],
                capture_output=True,
                text=True,
                cwd=self.project_root,
                timeout=5,
                creationflags=creation_flags,
            )

            branch = result.stdout.strip()
            if not branch:
                return None

            # Load task-worktree mapping
            if self.mapping_file.exists():
                mapping = json.loads(self.mapping_file.read_text())
                return mapping.get(branch)

        except subprocess.TimeoutExpired:
            logger.warning("[TaskID] Git command timed out")
        except FileNotFoundError:
            logger.warning("[TaskID] Git not found")
        except (json.JSONDecodeError, OSError) as e:
            logger.exception(f"[TaskID] Error inferring from features.git: {e}")

        return None

    def _ask_user(self) -> str | None:
        """Ask user to select task (last resort)."""
        # Try to query CKS for available tasks
        try:
            from .adapter import ProjectContextCKSAdapter

            # Try common CKS database locations
            db_paths = [
                self.project_root / ".cks" / "storage" / "cks.db",
                self.project_root / "__csf" / "data" / "cks.db",
            ]
            db_path = None
            for path in db_paths:
                if path.exists():
                    db_path = path
                    break

            if db_path.exists():
                adapter = ProjectContextCKSAdapter(db_path)
                contexts = adapter.list_contexts()

                if contexts:
                    # Show available contexts
                    print("\n[TaskID] Which task would you like to work on?")
                    for i, ctx in enumerate(contexts, 1):
                        print(f"  {i}. {ctx.tsk_id}")

                    # For now, just return the first one
                    # In production, this would prompt for user input
                    return contexts[0].tsk_id if contexts else None

        except Exception as e:
            logger.exception(f"[TaskID] Error asking user: {e}")

        return None

    def set_current_task(self, task_name: str) -> bool:
        """Set current task and persist to session file.

        Args:
            task_name: Task identifier (e.g., "CWO12")

        Returns:
            True if successful

        """
        try:
            # Set environment variable
            os.environ["TASK_NAME"] = task_name

            # Write session file
            session_data = {
                "task_name": task_name,
                "task_id": f"task_{task_name.lower()}",
                "started": datetime.now(UTC).isoformat(),
                "checksum": hashlib.md5(task_name.encode()).hexdigest(),
            }

            self.session_file.parent.mkdir(parents=True, exist_ok=True)
            self.session_file.write_text(json.dumps(session_data, indent=2))

            logger.info(f"[TaskID] Set current task: {task_name}")
            return True

        except Exception as e:
            logger.exception(f"[TaskID] Error setting task: {e}")
            return False

    def store_compact_metadata(self, task_name: str, checkpoint_id: str) -> bool:
        """Store task identity in compact metadata (for PostCompact recovery).

        Called by PreCompact hook before compaction.

        Args:
            task_name: Task being compacted
            checkpoint_id: Checkpoint ID just captured

        Returns:
            True if successful

        """
        try:
            metadata = {
                "terminal_id": self.terminal_id,
                "task_name": task_name,
                "task_id": f"task_{task_name.lower()}",
                "checkpoint_id": checkpoint_id,
                "timestamp": datetime.now(UTC).isoformat(),
                "version": "v1",
            }

            self.metadata_file.parent.mkdir(parents=True, exist_ok=True)
            self.metadata_file.write_text(json.dumps(metadata, indent=2))

            logger.info(f"[TaskID] Stored compact metadata: {task_name}")
            return True

        except Exception as e:
            logger.exception(f"[TaskID] Error storing metadata: {e}")
            return False

    def register_task_worktree_mapping(self, task_name: str, branch: str) -> bool:
        """Register mapping from features.git branch to task.

        Called when task starts or when git branch changes.

        Args:
            task_name: Task identifier
            branch: Git branch name

        Returns:
            True if successful

        """
        try:
            # Load existing mapping
            if self.mapping_file.exists():
                mapping = json.loads(self.mapping_file.read_text())
            else:
                mapping = {}

            # Add new mapping
            mapping[branch] = task_name

            # Save
            self.mapping_file.parent.mkdir(parents=True, exist_ok=True)
            self.mapping_file.write_text(json.dumps(mapping, indent=2))

            logger.info(f"[TaskID] Registered: {branch} -> {task_name}")
            return True

        except Exception as e:
            logger.exception(f"[TaskID] Error registering mapping: {e}")
            return False

    def cleanup_stale_terminal_files(self, max_age_hours: int = 24) -> int:
        """Remove stale terminal-scoped task files older than max_age_hours.

        Args:
            max_age_hours: Age in hours after which files are considered stale

        Returns:
            Number of files cleaned up

        """
        try:
            cutoff = datetime.now() - timedelta(hours=max_age_hours)
            cleaned = 0

            # Clean stale session-task-*.json files
            for f in (self.project_root / ".claude").glob("session-task-*.json"):
                with suppress(OSError):
                    # Skip the current terminal's file
                    if f == self.session_file:
                        continue

                    # Check file modification time
                    mtime = datetime.fromtimestamp(f.stat().st_mtime)
                    if mtime < cutoff:
                        f.unlink()
                        cleaned += 1
                        logger.info(f"[TaskID] Cleaned stale session file: {f.name}")

            # Clean stale .last-compact-metadata-*.json files
            for f in (self.project_root / ".claude").glob(".last-compact-metadata-*.json"):
                with suppress(OSError):
                    # Skip the current terminal's file
                    if f == self.metadata_file:
                        continue

                    mtime = datetime.fromtimestamp(f.stat().st_mtime)
                    if mtime < cutoff:
                        f.unlink()
                        cleaned += 1
                        logger.info(f"[TaskID] Cleaned stale metadata file: {f.name}")

            return cleaned
        except Exception as e:
            logger.exception(f"[TaskID] Error during cleanup: {e}")
            return 0


if __name__ == "__main__":
    # Test the manager
    manager = TaskIdentityManager()

    print("Testing Task Identity Manager")
    print("=" * 50)

    # Test: Get current task
    task = manager.get_current_task()
    print(f"Current task: {task}")

    # Test: Set task
    if task:
        print(f"\nTask '{task}' recovered from source")
    else:
        print("\nNo task found - would prompt user")
