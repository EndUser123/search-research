"""
SEC-004 + SEC-001: State File Manager with FileLock and Session Isolation.

This module provides the state file mechanism for restoration pending state.
It combines:
- SEC-001: FileLock protection for atomic state operations
- SEC-004: Session-scoped state file naming (terminal_id + session_id)
"""

from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from typing import Any

from __lib.file_lock import FileLock

# Path to state files directory
_STATE_DIR = Path(".claude/handoff")

# Lock timeout in seconds
_LOCK_TIMEOUT = 5.0


class StateFileManager:
    """
    Manages state file operations with FileLock protection and session isolation.
    """

    def __init__(
        self,
        project_root: Path,
        terminal_id: str,
        session_id: str | None = None,
    ) -> None:
        self.project_root = Path(project_root)
        self.terminal_id = terminal_id
        self.session_id = session_id or get_session_id()
        self.state_dir = self.project_root / _STATE_DIR
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def get_state_file_path(self) -> Path:
        """Get the path to the state file."""
        return self.state_dir / f"{self.terminal_id}_{self.session_id}_restoration_pending.json"

    def get_lock_file_path(self) -> Path:
        """Get the path to the lock file alongside state file."""
        state_path = self.get_state_file_path()
        # Use name + '.lock' pattern (NOT with_suffix() which corrupts .json files)
        return state_path.parent / (state_path.name + ".lock")

    def write(self, data: dict[str, Any]) -> None:
        """
        Write state data with FileLock protection.

        Raises TimeoutError if lock cannot be acquired within 5 seconds.
        """
        state_path = self.get_state_file_path()
        lock_path = self.get_lock_file_path()

        lock = FileLock(lock_path, timeout=_LOCK_TIMEOUT)
        with lock:
            state_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def read(self) -> dict[str, Any]:
        """
        Read state data with FileLock protection.

        Raises TimeoutError if lock cannot be acquired within 5 seconds.
        Returns empty dict if state file does not exist.
        """
        state_path = self.get_state_file_path()
        lock_path = self.get_lock_file_path()

        if not state_path.exists():
            return {}

        lock = FileLock(lock_path, timeout=_LOCK_TIMEOUT)
        with lock:
            return json.loads(state_path.read_text(encoding="utf-8"))

    def atomic_increment(self, key: str) -> None:
        """
        Atomically increment a counter in state file using FileLock.

        Raises TimeoutError if lock cannot be acquired within 5 seconds.
        """
        state_path = self.get_state_file_path()
        lock_path = self.get_lock_file_path()

        lock = FileLock(lock_path, timeout=_LOCK_TIMEOUT)
        with lock:
            if state_path.exists():
                data = json.loads(state_path.read_text(encoding="utf-8"))
            else:
                data = {}
            data[key] = data.get(key, 0) + 1
            state_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def get_session_id(self) -> str:
        """Get session ID, generating UUID fallback if needed."""
        return get_session_id()


def get_session_id() -> str:
    """
    Get session ID from environment or generate UUID fallback.

    NBM-1 workaround: Writes to $CLAUDE_ENV_FILE for persistence.
    """
    # Check CLAUDE_SESSION_ID
    session_id = os.environ.get("CLAUDE_SESSION_ID")
    if session_id:
        return session_id

    # Generate UUID fallback
    generated_id = uuid.uuid4().hex[:8]

    # NBM-1 workaround: Write to CLAUDE_ENV_FILE for persistence
    env_file_path = os.environ.get("CLAUDE_ENV_FILE")
    if env_file_path:
        env_file = Path(env_file_path)
        env_file.parent.mkdir(parents=True, exist_ok=True)
        # Append session_id to existing content or create new
        existing = env_file.read_text() if env_file.exists() else ""
        if generated_id not in existing:
            env_file.write_text(f"{existing}\nCLAUDE_SESSION_ID={generated_id}", encoding="utf-8")

    return generated_id


def write_state_file(
    project_root: Path,
    terminal_id: str,
    session_id: str,
    data: dict[str, Any],
) -> None:
    """
    Write state file with FileLock.

    Raises TimeoutError if lock cannot be acquired within 5 seconds.
    """
    manager = StateFileManager(project_root, terminal_id, session_id)
    manager.write(data)


def read_state_file(
    project_root: Path,
    terminal_id: str,
    session_id: str,
) -> dict[str, Any]:
    """
    Read state file with FileLock.

    Raises TimeoutError if lock cannot be acquired within 5 seconds.
    """
    manager = StateFileManager(project_root, terminal_id, session_id)
    return manager.read()
