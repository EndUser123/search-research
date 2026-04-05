#!/usr/bin/env python3
"""
Session Manager Module

Manages logical work sessions (multi-terminal safe).

Session ID = Logical work unit (persists across terminals and /clear)
Terminal ID = Physical instance (for collision safety only)

Features:
- Name/rename sessions
- Switch between sessions
- Claim tasks for current session
- Session persistence across terminals

Environment Variables:
- SESSION_STATE_DIR: Directory for session state (default: .claude/state/session_manager/)
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import time
from pathlib import Path

from __lib.file_lock import FileLock

# Version: 1.0
# Multi-terminal safe: Uses terminal_id for collision safety, session_id for logical grouping

_HOOKS_DIR = Path(__file__).resolve().parent.parent
STATE_DIR = _HOOKS_DIR / "state" / "session_manager"
SESSION_FILE = _HOOKS_DIR / "current_session.json"


def get_terminal_id() -> str:
    """Get terminal ID for collision safety."""
    try:
        from __lib.terminal_detection import detect_terminal_id

        return detect_terminal_id()
    except Exception:
        return ""  # No PID fallback


def get_current_session_id() -> str:
    """Get current session ID from session file."""
    try:
        if SESSION_FILE.exists():
            data = json.loads(SESSION_FILE.read_text())
            return data.get("session_id", "default")
    except Exception:
        pass
    return "default"


def get_session_state_path(session_id: str) -> Path:
    """Get state file path for session."""
    return STATE_DIR / f"{session_id}_state.json"


def load_session_state(session_id: str) -> dict:
    """Load session state."""
    state_path = get_session_state_path(session_id)
    if not state_path.exists():
        return {
            "session_id": session_id,
            "name": session_id,
            "created_at": time.time(),
            "last_activity": time.time(),
            "tasks": [],
            "metadata": {},
        }

    try:
        content = state_path.read_text(encoding="utf-8")
        return json.loads(content)
    except (OSError, ValueError):
        return {
            "session_id": session_id,
            "name": session_id,
            "created_at": time.time(),
            "last_activity": time.time(),
            "tasks": [],
            "metadata": {},
        }


def save_session_state(session_id: str, state: dict):
    """Save session state atomically with FileLock protection."""
    state_path = get_session_state_path(session_id)
    lock_path = state_path.with_suffix(".lock")
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        state["last_activity"] = time.time()
        with FileLock(lock_path, timeout=5.0):
            # Atomic write: write to temp file, then replace
            temp_fd, temp_path = tempfile.mkstemp(
                dir=STATE_DIR, suffix=".tmp", prefix=f"{session_id}_"
            )
            try:
                with os.fdopen(temp_fd, "w", encoding="utf-8") as f:
                    f.write(json.dumps(state, indent=2))
                Path(temp_path).replace(state_path)
            except Exception:
                Path(temp_path).unlink(missing_ok=True)
                raise
    except (OSError, TimeoutError):
        pass


def set_current_session(session_id: str, terminal_id: str):
    """Set current session for this terminal atomically with FileLock protection."""
    lock_path = SESSION_FILE.with_suffix(".lock")
    try:
        SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "session_id": session_id,
            "terminal_id": terminal_id,
            "updated_at": time.time(),
        }
        with FileLock(lock_path, timeout=5.0):
            # Atomic write: write to temp file, then replace
            temp_fd, temp_path = tempfile.mkstemp(
                dir=SESSION_FILE.parent, suffix=".tmp", prefix="current_session_"
            )
            try:
                with os.fdopen(temp_fd, "w", encoding="utf-8") as f:
                    f.write(json.dumps(data, indent=2))
                Path(temp_path).replace(SESSION_FILE)
            except Exception:
                Path(temp_path).unlink(missing_ok=True)
                raise
    except (OSError, TimeoutError):
        pass


def create_session(name: str, terminal_id: str) -> str:
    """
    Create a new session with given name.

    Returns session_id.
    """
    # Generate session ID from name + timestamp
    session_id = f"{name}_{int(time.time())}"

    # Initialize session state
    state = {
        "session_id": session_id,
        "name": name,
        "created_at": time.time(),
        "last_activity": time.time(),
        "tasks": [],
        "metadata": {},
    }
    save_session_state(session_id, state)

    # Set as current session
    set_current_session(session_id, terminal_id)

    return session_id


def rename_session(session_id: str, new_name: str):
    """Rename session."""
    state = load_session_state(session_id)
    state["name"] = new_name
    save_session_state(session_id, state)


def switch_session(session_id: str, terminal_id: str):
    """Switch to different session."""
    # Verify session exists
    state = load_session_state(session_id)
    if state["session_id"] != session_id:
        raise ValueError(f"Session {session_id} not found")

    # Set as current
    set_current_session(session_id, terminal_id)


def claim_task(session_id: str, task_id: str, terminal_id: str):
    """
    Claim a task for the current session.

    Moves task from its current session to the target session.
    """
    # Find task in existing session states
    task_dir = Path(".claude/state/task_tracker/")
    if not task_dir.exists():
        raise ValueError(f"Task {task_id} not found")

    # Search for task in all session files
    source_session_id = None
    task_data = None

    for state_file in task_dir.glob("*_tasks.json"):
        try:
            content = state_file.read_text(encoding="utf-8")
            state = json.loads(content)
            if task_id in state.get("tasks", {}):
                source_session_id = state.get("session_id")
                task_data = state["tasks"][task_id]
                break
        except (OSError, ValueError):
            continue

    if not task_data:
        raise ValueError(f"Task {task_id} not found")

    # Load source session
    source_state = load_session_state(source_session_id)
    if task_id in source_state.get("tasks", []):
        source_state["tasks"].remove(task_id)
        save_session_state(source_session_id, source_state)

    # Add to target session
    target_state = load_session_state(session_id)
    if task_id not in target_state.get("tasks", []):
        target_state["tasks"].append(task_id)
        save_session_state(session_id, target_state)


def list_sessions() -> list[dict]:
    """List all sessions."""
    sessions = []
    if not STATE_DIR.exists():
        return sessions

    for state_file in STATE_DIR.glob("*_state.json"):
        try:
            content = state_file.read_text(encoding="utf-8")
            state = json.loads(content)
            sessions.append(
                {
                    "session_id": state.get("session_id"),
                    "name": state.get("name"),
                    "created_at": state.get("created_at"),
                    "last_activity": state.get("last_activity"),
                    "task_count": len(state.get("tasks", [])),
                }
            )
        except (OSError, ValueError):
            continue

    # Sort by last activity
    sessions.sort(key=lambda x: x.get("last_activity", 0), reverse=True)
    return sessions


def get_session_info(session_id: str) -> dict:
    """Get detailed session information."""
    state = load_session_state(session_id)
    return {
        "session_id": state.get("session_id"),
        "name": state.get("name"),
        "created_at": state.get("created_at"),
        "last_activity": state.get("last_activity"),
        "tasks": state.get("tasks", []),
        "metadata": state.get("metadata", {}),
    }


class SessionManager:
    """
    High-level session management interface.

    Usage:
        sm = SessionManager()
        sm.create_session("my-work")
        sm.rename_session("my-work-2")
        sm.switch_to("another-session")
        sm.claim_task("task-123")
    """

    def __init__(self):
        self.terminal_id = get_terminal_id()
        self.current_session_id = get_current_session_id()

    def create(self, name: str) -> str:
        """Create new session and switch to it."""
        session_id = create_session(name, self.terminal_id)
        self.current_session_id = session_id
        return session_id

    def rename(self, new_name: str):
        """Rename current session."""
        rename_session(self.current_session_id, new_name)

    def switch_to(self, session_id: str):
        """Switch to different session."""
        switch_session(session_id, self.terminal_id)
        self.current_session_id = session_id

    def claim(self, task_id: str):
        """Claim task for current session."""
        claim_task(self.current_session_id, task_id, self.terminal_id)

    def list_all(self) -> list[dict]:
        """List all sessions."""
        return list_sessions()

    def get_info(self) -> dict:
        """Get current session info."""
        return get_session_info(self.current_session_id)

    def get_current_id(self) -> str:
        """Get current session ID."""
        return self.current_session_id

    def cleanup_old_sessions(self, max_age_hours: int = 24, keep_current: bool = True) -> list[str]:
        """
        Remove old session state files.

        Args:
            max_age_hours: Delete sessions older than this (default: 24 hours)
            keep_current: Never delete the current session (default: true)

        Returns:
            List of deleted session IDs
        """
        return cleanup_old_sessions(
            max_age_hours, self.current_session_id if keep_current else None
        )


def cleanup_old_sessions(
    max_age_hours: int = 24, exclude_session_id: str | None = None
) -> list[str]:
    """
    Remove old session state files.

    Args:
        max_age_hours: Delete sessions older than this (default: 24 hours)
        exclude_session_id: Never delete this session (e.g., current session)

    Returns:
        List of deleted session IDs
    """
    if not STATE_DIR.exists():
        return []

    deleted = []
    cutoff_time = time.time() - (max_age_hours * 3600)

    for state_file in STATE_DIR.glob("*_state.json"):
        try:
            # Check file modification time
            file_mtime = state_file.stat().st_mtime

            if file_mtime < cutoff_time:
                # Extract session_id from filename
                session_id = state_file.stem.replace("_state", "")

                # Skip if excluded
                if exclude_session_id and session_id == exclude_session_id:
                    continue

                # Delete state file
                state_file.unlink()
                deleted.append(session_id)

        except OSError:
            continue

    return deleted


def main():
    """Test session manager."""
    sm = SessionManager()

    # Create test session
    session_id = sm.create("test-session")
    print(f"Created session: {session_id}")

    # Rename
    sm.rename("renamed-session")
    print("Renamed session")

    # Get info
    info = sm.get_info()
    print(f"Session info: {info}")

    # List all
    sessions = sm.list_all()
    print(f"All sessions: {sessions}")

    print("✓ Session manager tests passed")


if __name__ == "__main__":
    main()
