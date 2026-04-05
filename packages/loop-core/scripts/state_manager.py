"""Terminal-local state management for autonomous loops.

Canonical Schema for loop_state.json
=====================================

The loop_state.json file stores the current execution state of an autonomous
loop. All fields are required unless otherwise noted.

Top-level Fields:
-----------------
- current_task_id: str
    The ID of the task currently being executed (e.g., "TASK-001")

- completed_tasks: list[str]
    List of task IDs that have been successfully completed

- failed_tasks: list[str]
    List of task IDs that have failed (may be retried later)

- completion_indicators: int
    Heuristic counter tracking completion signals (default: 0)
    Used for dual-condition exit detection with EXIT_SIGNAL

- loop_metadata: dict
    Nested dictionary containing loop execution metadata

Loop Metadata Fields:
---------------------
- plan_path: str
    Absolute path to the plan file being executed

- started_at: str
    ISO 8601 timestamp when the loop started (e.g., "2026-03-14T10:00:00")

- last_update: str
    ISO 8601 timestamp of the last state update (e.g., "2026-03-14T10:15:00")

- iterations: int
    Number of loop iterations completed (starts at 1)

Example:
--------
{
    "current_task_id": "TASK-003",
    "completed_tasks": ["TASK-001", "TASK-002"],
    "failed_tasks": ["TASK-004"],
    "completion_indicators": 2,
    "loop_metadata": {
        "plan_path": "/path/to/plan.md",
        "started_at": "2026-03-14T10:00:00",
        "last_update": "2026-03-14T10:15:00",
        "iterations": 3
    }
}

Type Validation:
----------------
- All timestamp fields MUST be ISO 8601 formatted strings
- Task ID lists MUST contain only string values
- Counter fields (completion_indicators, iterations) MUST be integers
- Path fields MUST be strings

State Management:
-----------------
- State is stored per-terminal in .claude/loop/state/terminals/{terminal_id}/
- Atomic writes use temp file + rename pattern
- File-based locking prevents concurrent access issues
"""

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

from scripts.state_paths import get_terminal_state_dir
from scripts.terminal_detection import get_terminal_id


class LoopStateError(Exception):
    """Base exception for loop state errors."""


class LoopPlanError(LoopStateError):
    """Exception raised when plan file is not found or invalid."""


class LoopStateValidationError(LoopStateError):
    """Exception raised when loop_state.json schema validation fails."""


def validate_loop_state_schema(state: dict[str, Any]) -> None:
    """Validate loop_state.json against canonical schema.

    Args:
        state: Dictionary containing loop state

    Raises:
        LoopStateValidationError: If state doesn't match required schema

    Canonical Schema:
        - current_task_id: str (required)
        - completed_tasks: list[str] (required)
        - failed_tasks: list[str] (required)
        - completion_indicators: int (required)
        - loop_metadata: dict (required)
            - plan_path: str (required)
            - started_at: str (required, ISO 8601 timestamp)
            - last_update: str (required, ISO 8601 timestamp)
            - iterations: int (required)
    """
    # Validate top-level required fields
    required_fields = {
        "current_task_id": str,
        "completed_tasks": list,
        "failed_tasks": list,
        "completion_indicators": int,
        "loop_metadata": dict,
    }

    for field, expected_type in required_fields.items():
        if field not in state:
            raise LoopStateValidationError(f"Missing required field: {field}")

        if not isinstance(state[field], expected_type):
            raise LoopStateValidationError(
                f"Field '{field}' has wrong type: expected {expected_type.__name__}, got {type(state[field]).__name__}"
            )

    # Validate task lists contain only strings
    for i, task_id in enumerate(state["completed_tasks"]):
        if not isinstance(task_id, str):
            raise LoopStateValidationError(
                f"completed_tasks[{i}] has wrong type: expected str, got {type(task_id).__name__}"
            )

    for i, task_id in enumerate(state["failed_tasks"]):
        if not isinstance(task_id, str):
            raise LoopStateValidationError(
                f"failed_tasks[{i}] has wrong type: expected str, got {type(task_id).__name__}"
            )

    # Validate loop_metadata required fields
    metadata = state["loop_metadata"]
    metadata_fields = {
        "plan_path": str,
        "started_at": str,
        "last_update": str,
        "iterations": int,
    }

    for field, expected_type in metadata_fields.items():
        if field not in metadata:
            raise LoopStateValidationError(f"Missing required loop_metadata field: {field}")

        if not isinstance(metadata[field], expected_type):
            raise LoopStateValidationError(
                f"loop_metadata.{field} has wrong type: expected {expected_type.__name__}, got {type(metadata[field]).__name__}"
            )

    # Validate ISO 8601 timestamps (basic check)
    for timestamp_field in ["started_at", "last_update"]:
        timestamp = metadata[timestamp_field]
        try:
            # Attempt to parse as ISO timestamp
            datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except (ValueError, AttributeError) as e:
            raise LoopStateValidationError(
                f"loop_metadata.{timestamp_field} is not a valid ISO 8601 timestamp: {timestamp}"
            ) from e


class TerminalStateManager:
    """Manages terminal-local state for autonomous loops.

    Provides atomic state operations with file-based locking to ensure
    multi-terminal isolation and prevent race conditions.

    Attributes:
        terminal_id: Terminal identifier (format: {source}_{id})
        state_dir: Terminal-scoped state directory path
    """

    def __init__(self, terminal_id: str | None = None) -> None:
        """Initialize state manager for terminal-local state.

        Args:
            terminal_id: Terminal identifier. If None, auto-detected.
        """
        self.terminal_id = terminal_id or get_terminal_id()
        self.state_dir = get_terminal_state_dir(self.terminal_id)

    def read_state(self, key: str) -> dict[str, Any] | None:
        """Read state value from file.

        Args:
            key: State key (filename without .json extension)

        Returns:
            State dictionary, or None if file doesn't exist

        Raises:
            LoopStateError: If file exists but is corrupted
        """
        state_file = self.state_dir / f"{key}.json"

        if not state_file.exists():
            return None

        try:
            data = json.loads(state_file.read_text())
            return data if isinstance(data, dict) else {"data": data}
        except json.JSONDecodeError as e:
            raise LoopStateError(
                f"Corrupted state file {state_file}: {e}"
            ) from e

    def write_state(self, key: str, value: dict[str, Any], validate_schema: bool = False) -> None:
        """Write state value with atomic write operation.

        Uses temp file + rename pattern for atomicity.

        Args:
            key: State key (filename without .json extension)
            value: State dictionary to write
            validate_schema: If True and key is "loop_state", validates against canonical schema

        Raises:
            LoopStateError: If write fails after retries
            LoopStateValidationError: If schema validation fails
        """
        # Validate loop_state schema if requested
        if validate_schema and key == "loop_state":
            validate_loop_state_schema(value)

        state_file = self.state_dir / f"{key}.json"

        # Atomic write pattern: temp file + rename
        try:
            # Create temp file in same directory for atomic rename
            with tempfile.NamedTemporaryFile(
                mode="w",
                dir=self.state_dir,
                prefix=f".{key}_",
                suffix=".tmp",
                delete=False,
            ) as tmp:
                json.dump(value, tmp, indent=2)
                tmp_path = Path(tmp.name)

            # Atomic rename (overwrites target if exists)
            tmp_path.replace(state_file)

        except OSError as e:
            raise LoopStateError(
                f"Failed to write state file {state_file}: {e}"
            ) from e

    def acquire_lock(self, lock_name: str, timeout_sec: float = 30.0) -> bool:
        """Acquire lock file with PID-based ownership.

        Args:
            lock_name: Lock name (filename without .lock extension)
            timeout_sec: Maximum time to wait for lock (default 30s)

        Returns:
            True if lock acquired, False if timeout exceeded

        Raises:
            LoopStateError: If lock acquisition fails for other reasons
        """
        lock_file = self.state_dir / f"{lock_name}.lock"
        pid = os.getpid()

        # Check for stale lock (PID no longer running)
        if lock_file.exists():
            try:
                lock_pid = int(lock_file.read_text().strip())
                if not self._is_pid_running(lock_pid):
                    # Stale lock - clean it up
                    lock_file.unlink()
                else:
                    # Valid lock held by another process
                    return False
            except (ValueError, OSError):
                # Corrupted lock file - clean it up
                try:
                    lock_file.unlink()
                except OSError:
                    # If cleanup fails, treat as locked
                    return False

        # Try to create lock file (atomic if O_CREAT | O_EXCL)
        try:
            # Use os.open with O_CREAT | O_EXCL for atomic creation
            fd = os.open(lock_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(pid).encode())
            os.close(fd)
            return True
        except FileExistsError:
            # Lock held by another process
            return False
        except OSError as e:
            raise LoopStateError(
                f"Failed to acquire lock {lock_name}: {e}"
            ) from e

    def release_lock(self, lock_name: str) -> None:
        """Release lock file.

        Args:
            lock_name: Lock name (filename without .lock extension)

        Raises:
            LoopStateError: If lock release fails
        """
        lock_file = self.state_dir / f"{lock_name}.lock"

        try:
            lock_file.unlink(missing_ok=True)
        except OSError as e:
            raise LoopStateError(
                f"Failed to release lock {lock_name}: {e}"
            ) from e

    def _is_pid_running(self, pid: int) -> bool:
        """Check if process with given PID is running.

        Args:
            pid: Process ID to check

        Returns:
            True if process is running, False otherwise
        """
        if pid <= 0:
            return False

        try:
            # Send signal 0 to check if process exists
            os.kill(pid, 0)
            return True
        except OSError:
            return False
