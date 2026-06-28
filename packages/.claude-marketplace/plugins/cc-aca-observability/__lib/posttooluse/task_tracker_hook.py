#!/usr/bin/env python3
"""
PostToolUse Hook - Task Tracker (In-Process)

Tracks TaskCreate/TaskUpdate/TaskList calls for session-based task coordination.

This is the in-process version of PostToolUse_task_tracker.py.
Wraps the core logic in a PostToolUseHook class for zero-latency execution.

Session-based: Tasks grouped by session_id (logical work unit).
Multi-terminal safe: Multiple terminals can work on same session.
Re-entrancy guard: Prevents infinite loops via marker file.
File-based persistence: Tasks survive compaction and session restore.

Environment Variables:
- TASK_TRACKER_ENABLED: Enable/disable hook (default: true)
- TASK_STATE_DIR: Directory for task state (default: .claude/state/task_tracker/)
"""

from __future__ import annotations

import hashlib
import json
import logging as _li
import os
import re
import sys

# Import self-documentation validator
import time
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

_HOOKS_DIR = Path(__file__).resolve().parent
_LOG_DIR = _HOOKS_DIR / "logs" / "diagnostics"
_LOG_DIR.mkdir(parents=True, exist_ok=True)
_logger = _li.getLogger(__name__)
_handler = _li.FileHandler(_LOG_DIR / "hook_stderr.log", encoding="utf-8")
_handler.setFormatter(_li.Formatter("%(asctime)s %(levelname)s %(message)s"))
_logger.addHandler(_handler)
_logger.setLevel(_li.WARNING)
from typing import Any

# Import base class
from posttooluse.base import PostToolUseHook

hooks_root = Path(__file__).resolve().parent.parent
if str(hooks_root) not in sys.path:
    sys.path.insert(0, str(hooks_root))

hooks_lib = hooks_root / "__lib"
if str(hooks_lib) not in sys.path:
    sys.path.insert(0, str(hooks_lib))

# Import file locking for concurrent access safety.
# Support both package-style (__lib.file_lock) and bare-module (file_lock)
# resolution because hooks run under mixed entrypoints.
try:
    from __lib.file_lock import FileLock
except ImportError:
    from file_lock import FileLock  # type: ignore[no-redef]

from task_self_doc_validator import self_documentation_check

# Import delegation state clearer for cross-hook coordination
_DELEGATION_STATE_DIR: Path | None = None


def _get_delegation_state_dir() -> Path:
    """Get delegation state directory (terminal-scoped).

    Uses WT_SESSION env var (set in Windows Terminal), falls back to
    CLAUDE_TERMINAL_ID, then to hash(PID+cwd) for process isolation.
    Matches the terminal ID detection in PreToolUse_delegation_gate.py.
    """
    global _DELEGATION_STATE_DIR
    if _DELEGATION_STATE_DIR is None:
        import os as _os
        import hashlib as _hashlib

        claude_root = Path("P:/") / ".claude"

        # Primary: WT_SESSION
        raw = _os.environ.get("WT_SESSION", "")
        if raw:
            terminal_id = f"console_{raw}"
        else:
            # Fallback: CLAUDE_TERMINAL_ID
            fallback = _os.environ.get("CLAUDE_TERMINAL_ID", "")
            if fallback:
                terminal_id = f"console_{fallback}"
            else:
                # Fallback: hash of PID + cwd for process isolation
                pid = _os.getpid()
                cwd = _os.getcwd()
                hash_input = f"{pid}:{cwd}"
                terminal_hash = _hashlib.md5(hash_input.encode()).hexdigest()[:12]
                terminal_id = f"unknown_{terminal_hash}"

        _DELEGATION_STATE_DIR = claude_root / ".artifacts" / terminal_id / "hook_state"
    return _DELEGATION_STATE_DIR


def _clear_delegation_state() -> None:
    """Clear delegation_expected state after Task invocation (terminal-scoped)."""
    state_file = _get_delegation_state_dir() / "delegation_expected.json"
    try:
        state_file.unlink(missing_ok=True)
    except OSError:
        pass

# Version: 2.0 (in-process version)
# Derived from: PostToolUse_task_tracker.py v1.3
# Changes: Wrapped in PostToolUseHook class, eliminated subprocess overhead

SESSION_ID = None
TERMINAL_ID = None


def get_state_dir() -> Path:
    """Get state directory dynamically from environment. Uses absolute path to avoid CWD issues.

    Note: Uses os.environ as this is hook infrastructure (configured via settings.json),
    not a standalone package with pydantic-settings.
    """
    env_dir = os.environ.get("TASK_STATE_DIR")
    if env_dir:
        return Path(env_dir)
    # Default: P:/.claude/state/task_tracker/
    # Resolve from this file's location: hooks/posttooluse/task_tracker_hook.py
    # Go up THREE levels to reach .claude root, then into state/task_tracker
    hook_file = Path(__file__).resolve()
    # P:/.claude/hooks/posttooluse/task_tracker_hook.py
    # -> P:/.claude/hooks/posttooluse
    # -> P:/.claude/hooks
    # -> P:/.claude (this is what we want)
    # Go up THREE levels: hooks/posttooluse/task_tracker_hook.py -> hooks/posttooluse -> hooks -> .claude
    from _bootstrap import state_root
    return state_root() / "task_tracker"


def log(msg: str) -> None:
    """Debug logging (disabled by default to avoid noisy hook errors)."""
    if os.environ.get("TASK_TRACKER_DEBUG", "0") == "1":
        _logger.debug(msg)


def validate_session_id(session_id: str) -> str:
    """
    Validate and sanitize session_id to prevent path traversal attacks (SEC-001).
    """
    if not session_id:
        raise ValueError("session_id cannot be empty")

    if "\x00" in session_id:
        raise ValueError("session_id contains null bytes")

    safe_session_id = session_id
    safe_session_id = safe_session_id.replace("..", "_")
    safe_session_id = safe_session_id.replace("/", "_")
    safe_session_id = safe_session_id.replace("\\", "_")
    safe_session_id = safe_session_id.replace(":", "_")
    safe_session_id = re.sub(r"[^A-Za-z0-9_-]", "_", safe_session_id)

    if not safe_session_id:
        safe_session_id = "invalid_session"

    return safe_session_id


def get_session_id() -> str:
    """Get session ID for logical task grouping."""
    global SESSION_ID
    if SESSION_ID is not None:
        return SESSION_ID  # type: ignore[unreachable]

    try:
        hooks_dir = Path(__file__).resolve().parent.parent.parent
        session_file = hooks_dir / "current_session.json"
        if session_file.exists():
            data: dict[str, Any] = json.loads(session_file.read_text())
            SESSION_ID = data.get("session_id", "default")
            if SESSION_ID is None:
                SESSION_ID = "default"
            return SESSION_ID
    except (OSError, json.JSONDecodeError, ValueError) as e:
        log(f"[Task Tracker] get_session_id failed: {e}")

    SESSION_ID = f"session_{int(time.time())}"
    return SESSION_ID


def ensure_session_exists(terminal_id: str) -> str:
    """Auto-create a session if none exists (default session)."""
    hooks_dir = Path(__file__).resolve().parent.parent.parent
    session_file = hooks_dir / "current_session.json"

    try:
        if session_file.exists():
            data: dict[str, Any] = json.loads(session_file.read_text())
            session_id: str = data.get("session_id", "default")
            if session_id != "default":
                return session_id
    except (OSError, json.JSONDecodeError, ValueError):
        # Session file unreadable, will use fallback
        pass

    fallback_id = f"auto_session_{int(time.time())}"
    log(f"[Task Tracker] Using fallback session: {fallback_id}")
    return fallback_id


def get_terminal_id() -> str:
    """Get terminal ID for collision safety."""
    global TERMINAL_ID
    if TERMINAL_ID is not None:
        return TERMINAL_ID  # type: ignore[unreachable]

    try:
        # terminal_detection is a peer module in hooks/
        # The hook runner adds hooks/ to sys.path before execution
        from __lib.terminal_detection import detect_terminal_id

        TERMINAL_ID = detect_terminal_id()
        return TERMINAL_ID
    except (ImportError, AttributeError, OSError):
        TERMINAL_ID = ""  # No PID fallback
        return TERMINAL_ID


def get_marker_path(terminal_id: str, task_id: str) -> Path:
    """Generate marker file path for re-entrancy guard."""
    marker_name = f"task_tracker_{terminal_id}_{hashlib.md5(task_id.encode()).hexdigest()[:16]}"
    return get_state_dir() / marker_name


def is_already_tracked(marker_path: Path) -> bool:
    """Check if task was already tracked in this operation (re-entrancy guard)."""
    return marker_path.exists()


def mark_as_tracked(marker_path: Path) -> None:
    """Create marker file to prevent re-entrancy."""
    try:
        get_state_dir().mkdir(parents=True, exist_ok=True)
        marker_path.touch(exist_ok=True)
    except OSError as e:
        log(f"[Task Tracker] mark_as_tracked failed: {e}")


def get_terminal_state_path(terminal_id: str) -> Path:
    """Get state file path for terminal (stable across compactions).

    Uses terminal_id instead of session_id because:
    - session_id changes on compaction (session continuity breaks)
    - terminal_id stays stable across compactions (better continuity)

    Args:
        terminal_id: The terminal identifier (stable across compactions)

    Returns:
        Path to the terminal's task state file
    """
    safe_terminal_id = validate_session_id(terminal_id)  # reuse validation
    return get_state_dir() / f"{safe_terminal_id}_tasks.json"


# Backward compatibility alias (deprecated)
def get_session_state_path(session_id: str) -> Path:
    """Get state file path for session (deprecated: use terminal-based naming).

    Note: This function is kept for backward compatibility but uses terminal_id
    internally to ensure task continuity across compactions.
    """
    terminal_id = get_terminal_id()
    return get_terminal_state_path(terminal_id)


def _update_terminal_state_locked(
    terminal_id: str, update_func: Callable[[dict[str, Any]], dict[str, Any]]
) -> bool:
    """Update terminal state with a function under file lock to prevent race conditions."""
    state_path = get_terminal_state_path(terminal_id)
    safe_terminal_id = validate_session_id(terminal_id)
    lock_path = get_state_dir() / f"{safe_terminal_id}_tasks.lock"

    default_state: dict[str, Any] = {
        "terminal_id": terminal_id,
        "tasks": {},
        # Removed last_update - task tracker should not use TTL (design requirement)
        "recent_files": [],
        "changed_files": [],
        "changed_files_by_session": {},  # Track by session for continuity
    }

    try:
        get_state_dir().mkdir(parents=True, exist_ok=True)

        with FileLock(lock_path, timeout=5.0):
            if state_path.exists():
                try:
                    content = state_path.read_text(encoding="utf-8")
                    state = json.loads(content)
                    if "recent_files" not in state:
                        state["recent_files"] = []
                    if "changed_files" not in state:
                        state["changed_files"] = []
                    if "changed_files_by_terminal" not in state or not isinstance(
                        state.get("changed_files_by_terminal"), dict
                    ):
                        state["changed_files_by_terminal"] = {}
                except (OSError, ValueError):
                    state = default_state.copy()
            else:
                state = default_state.copy()

            updated_state = update_func(state)
            # Removed last_update - task tracker should not use TTL (design requirement)

            temp_suffix = f".{uuid.uuid4().hex[:8]}.tmp"
            temp_path = state_path.with_suffix(temp_suffix)
            temp_path.write_text(json.dumps(updated_state, indent=2), encoding="utf-8")
            temp_path.replace(state_path)

        return True
    except (OSError, ValueError, TimeoutError) as e:
        log(f"[Task Tracker] Failed to update session state: {e}")
        return False


def _update_session_state_locked(
    session_id: str, update_func: Callable[[dict[str, Any]], dict[str, Any]]
) -> bool:
    """Update session state with a function under file lock (deprecated: use terminal version).

    Note: This function is kept for backward compatibility but routes to
    _update_terminal_state_locked internally for task continuity.
    """
    terminal_id = get_terminal_id()
    return _update_terminal_state_locked(terminal_id, update_func)


def _track_recent_files(terminal_id: str, file_path: str) -> None:
    """Track recent files for task context (terminal-based)."""
    if not file_path:
        return

    def update_state(state: dict[str, Any]) -> dict[str, Any]:
        if "recent_files" not in state:
            state["recent_files"] = []

        if file_path not in state["recent_files"]:
            state["recent_files"].append(file_path)

        state["recent_files"] = state["recent_files"][-5:]
        return state

    _update_terminal_state_locked(terminal_id, update_state)


# Backward compatibility alias (deprecated)
def _track_recent_files_session(session_id: str, file_path: str) -> None:
    """Track recent files for task context (deprecated session-based version)."""
    terminal_id = get_terminal_id()
    _track_recent_files(terminal_id, file_path)


def _track_changed_file(terminal_id: str, session_id: str, file_path: str) -> None:
    """Track edited/written files for session-scoped build verification."""
    if not file_path:
        return

    def update_state(state: dict[str, Any]) -> dict[str, Any]:
        if "changed_files" not in state:
            state["changed_files"] = []
        # Track by session now (changed_files_by_session for continuity)
        if "changed_files_by_session" not in state or not isinstance(
            state.get("changed_files_by_session"), dict
        ):
            state["changed_files_by_session"] = {}

        if file_path not in state["changed_files"]:
            state["changed_files"].append(file_path)
        state["changed_files"] = state["changed_files"][-400:]

        per_session = state["changed_files_by_session"].get(session_id)
        if not isinstance(per_session, list):
            per_session = []
        if file_path not in per_session:
            per_session.append(file_path)
        state["changed_files_by_session"][session_id] = per_session[-200:]
        return state

    _update_terminal_state_locked(terminal_id, update_state)


# Backward compatibility alias (deprecated)
def _track_changed_file_legacy(session_id: str, terminal_id: str, file_path: str) -> None:
    """Track edited/written files (deprecated signature)."""
    _track_changed_file(terminal_id, session_id, file_path)


def track_task_create(tool_input: dict, session_id: str, terminal_id: str) -> str | None:
    """Track TaskCreate call with enhanced context capture and concurrent access safety.

    Uses terminal-based state for continuity across compactions.
    """
    task_id = tool_input.get("taskId") or tool_input.get("task_id")
    subject = tool_input.get("subject", "")
    status = tool_input.get("status", "pending")
    description = tool_input.get("description", "")

    if not task_id:
        return None

    session_timestamp = datetime.now(UTC).isoformat()

    def update_state(state: dict[str, Any]) -> dict[str, Any]:
        files_referenced = state.get("recent_files", []).copy()

        state["tasks"][task_id] = {
            "id": task_id,
            "subject": subject,
            "status": status,
            "description": description or "No description provided",
            "files_referenced": files_referenced,
            "session_timestamp": session_timestamp,
            "created_at": state["tasks"].get(task_id, {}).get("created_at"),
            "session_id": session_id,  # Track session for context
            "terminal_id": terminal_id,  # File is terminal-based
        }

        if not state["tasks"][task_id]["created_at"]:
            state["tasks"][task_id]["created_at"] = time.time()

        return state

    # Use terminal-based state for continuity
    _update_terminal_state_locked(terminal_id, update_state)
    return f"[Task Tracker] Tracked TaskCreate: #{task_id} - {subject}"


def track_task_update(tool_input: dict, session_id: str, terminal_id: str) -> str | None:
    """Track TaskUpdate call with concurrent access safety.

    Uses terminal-based state for continuity across compactions.
    """
    task_id = tool_input.get("taskId") or tool_input.get("task_id")
    status = tool_input.get("status")
    owner = tool_input.get("owner")

    if not task_id:
        return None

    def update_state(state: dict[str, Any]) -> dict[str, Any]:
        if task_id not in state["tasks"]:
            state["tasks"][task_id] = {
                "id": task_id,
                "subject": "External task",
                "status": status or "pending",
                "created_at": None,
                "session_id": session_id,
                "terminal_id": terminal_id,
            }

        if status:
            state["tasks"][task_id]["status"] = status
        if owner:
            state["tasks"][task_id]["owner"] = owner

        return state

    # Use terminal-based state for continuity
    _update_terminal_state_locked(terminal_id, update_state)
    return f"[Task Tracker] Tracked TaskUpdate: #{task_id} â†’ {status or owner}"


def get_all_sessions_tasks() -> dict[str, Any]:
    """Get tasks from all terminal state files.

    Reads from *_tasks.json files which are now named by terminal_id
    for continuity across compactions.
    """
    all_tasks: dict[str, Any] = {}
    if not get_state_dir().exists():
        return all_tasks

    for state_file in get_state_dir().glob("*_tasks.json"):
        try:
            content = state_file.read_text(encoding="utf-8")
            state = json.loads(content)
            # Track both terminal and session context
            terminal_id = state.get("terminal_id", "unknown")
            for task_id, task_data in state.get("tasks", {}).items():
                task_data["terminal"] = terminal_id
                all_tasks[task_id] = task_data
        except (OSError, ValueError) as e:
            log(f"[Task Tracker] get_all_sessions_tasks failed for {state_file.name}: {e}")
            continue

    return all_tasks


# ============================================================================
# Checkpoint Metadata Support (Task-based Checkpoint Storage)
# ============================================================================


def recover_task_metadata(task_file_path: Path) -> dict[str, Any] | None:
    """Recover task metadata from corrupted or missing task file.

    Recovery sources (tried in order):
        1. Backup file: {task_file_path}.backup
        2. Checkpoint JSON archive: .claude/checkpoints.deprecated/{terminal_id}_*.json
        3. Create empty task structure as last resort

    Args:
        task_file_path: Path to the corrupted task file

    Returns:
        Recovered task data dict or None if all recovery fails

    Note:
        This is part of PR-006: Task File Corruption Recovery
        Used during transition period when checkpoint JSON files may still exist
    """
    # Try backup file
    backup_path = task_file_path.with_suffix(".json.backup")
    if backup_path.exists():
        try:
            return json.loads(backup_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass  # Try next recovery method

    # Try checkpoint archive (fallback during transition period)
    checkpoint_archive = get_state_dir().parent.parent / "checkpoints.deprecated"
    if checkpoint_archive.exists():
        # Find latest checkpoint for this terminal
        terminal_id = task_file_path.stem.replace("_tasks", "")
        checkpoints = list(checkpoint_archive.glob(f"*__{terminal_id}__*.json"))
        if checkpoints:
            # Sort by modification time, use latest
            latest = max(checkpoints, key=lambda p: p.stat().st_mtime)
            try:
                checkpoint_data = json.loads(latest.read_text(encoding="utf-8"))
                # Convert checkpoint to minimal task structure
                return {
                    "terminal_id": terminal_id,
                    "tasks": {
                        "active_session": {
                            "id": "active_session",
                            "subject": f"Recovered: {checkpoint_data.get('task_name', 'unknown')}",
                            "status": "pending",
                            "terminal": terminal_id,
                            "metadata": {
                                "checkpoint": checkpoint_data,
                                "recovered_from": str(latest.name),
                                "restore_pending": True,
                            },
                        }
                    },
                    # Removed last_update - task tracker should not use TTL (design requirement)
                    "recovered": True,
                }
            except (json.JSONDecodeError, OSError):
                pass

    # Last resort: create empty task structure
    terminal_id = task_file_path.stem.replace("_tasks", "")
    log(f"[Task Tracker] Creating empty task structure for {terminal_id} (all recovery failed)")
    return {
        "terminal_id": terminal_id,
        "tasks": {},
        # Removed last_update - task tracker should not use TTL (design requirement)
        "created_empty": True,
    }


def load_task_data_with_recovery(task_file_path: Path) -> dict[str, Any]:
    """Load task data with automatic recovery on corruption.

    Args:
        task_file_path: Path to the task file

    Returns:
        Task data dict, either loaded successfully or recovered

    Note:
        - Attempts to load task file normally first
        - If corruption detected, attempts recovery via recover_task_metadata()
        - Saves recovered data to disk for next time
        - Always returns a valid dict (never None)
    """
    try:
        content = task_file_path.read_text(encoding="utf-8")
        return json.loads(content)
    except (json.JSONDecodeError, OSError) as e:
        log(f"[Task Tracker] Task file corruption detected: {task_file_path.name} - {e}")
        recovered = recover_task_metadata(task_file_path)
        if recovered:
            # Save recovered data
            try:
                task_file_path.write_text(json.dumps(recovered, indent=2), encoding="utf-8")
                log(f"[Task Tracker] Recovered task data for {task_file_path.name}")
            except OSError:
                log(f"[Task Tracker] Failed to save recovered data for {task_file_path.name}")
        return recovered or {
            "terminal_id": "unknown",
            "tasks": {},
            # Removed last_update - task tracker should not use TTL (design requirement)
        }


def validate_checkpoint_metadata(metadata: dict[str, Any]) -> bool:
    """Validate checkpoint metadata structure and size.

    Args:
        metadata: Task metadata dict that may contain checkpoint data

    Returns:
        True if checkpoint metadata is valid, False otherwise

    Note:
        - Checks for required checkpoint fields
        - Validates metadata size is under 500 KB limit
        - Returns True for non-checkpoint metadata (backward compatibility)
    """
    # If no checkpoint field, this is legacy metadata (valid)
    if "checkpoint" not in metadata:
        return True

    checkpoint = metadata["checkpoint"]
    if not isinstance(checkpoint, dict):
        return False

    # Check required fields
    required_fields = ["task_name", "saved_at", "version"]
    for field in required_fields:
        if field not in checkpoint:
            log(f"[Task Tracker] Checkpoint metadata missing required field: {field}")
            return False

    # Check size limit (500 KB)
    import json

    estimated_size = len(json.dumps(checkpoint).encode("utf-8"))
    if estimated_size > 500_000:
        log(f"[Task Tracker] Checkpoint metadata exceeds 500 KB: {estimated_size} bytes")
        return False

    return True


class TaskTrackerHook(PostToolUseHook):
    """
    In-process PostToolUse hook for task tracking.

    Replaces subprocess-based PostToolUse_task_tracker.py.
    Zero-latency execution by running in the same process.
    """

    env_var = "TASK_TRACKER_ENABLED"
    default_enabled = True
    tool_matcher = {
        "TaskCreate",
        "TaskUpdate",
        "TaskList",
        "Read",
        "Edit",
        "Write",
        "MultiEdit",
        "Grep",
    }

    def process(
        self, tool_name: str, tool_input: dict[str, Any], tool_response: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Process the tool result for task tracking.

        Tracks TaskCreate/TaskUpdate/TaskList operations and recent files.
        """
        terminal_id = get_terminal_id()
        session_id = get_session_id()

        # Track recent files from observation/edit operations.
        # Uses terminal_id for state file naming (stable across compactions)
        if tool_name in ("Read", "Edit", "Write", "MultiEdit", "Grep"):
            file_path = None
            if tool_name == "Read":
                file_path = tool_input.get("file_path")
            elif tool_name == "Edit":
                file_path = tool_input.get("file_path")
            elif tool_name == "Write":
                file_path = tool_input.get("file_path")
            elif tool_name == "MultiEdit":
                file_path = tool_input.get("file_path")
            elif tool_name == "Grep":
                file_path = tool_input.get("path")

            if file_path:
                # Track in terminal-based state (stable across compactions)
                _track_recent_files(terminal_id, str(file_path))
                if tool_name in ("Edit", "Write", "MultiEdit"):
                    _track_changed_file(terminal_id, session_id, str(file_path))

        # Only track TaskCreate, TaskUpdate, TaskList for message output
        if tool_name not in ("TaskCreate", "TaskUpdate", "TaskList"):
            return {}

        # Auto-create session on TaskCreate if using default session
        if tool_name == "TaskCreate":
            session_id = ensure_session_exists(terminal_id)

        # Re-entrancy guard
        task_id = tool_input.get("taskId") or tool_input.get("task_id") or "list"
        marker_path = get_marker_path(terminal_id, task_id)

        if is_already_tracked(marker_path):
            return {}

        mark_as_tracked(marker_path)

        # Track the operation
        message = None
        if tool_name == "TaskCreate":
            message = track_task_create(tool_input, session_id, terminal_id)

            # Clear delegation_expected state when Task is used (delegation occurred)
            _clear_delegation_state()

            # Self-documentation advisory for vague tasks
            subject = tool_input.get("subject", "")
            description = tool_input.get("description", "")
            result = self_documentation_check(subject, description)

            if (
                not result.is_valid
                and os.environ.get("TASK_SELF_DOC_ENABLED", "true").lower() == "true"
            ):
                task_id_display = tool_input.get("taskId") or tool_input.get("task_id") or "?"
                advisory = (
                    f"\n\nâš ï¸ TASK SELF-DOCUMENTATION ADVISORY\n\n"
                    f"Task #{task_id_display} - {subject or '(no subject)'}' lacks self-documentation.\n\n"
                    f"Add to description:\n"
                    f"  â€¢ Problem: what issue is this fixing?\n"
                    f"  â€¢ Situation: when/where does it occur?\n"
                    f"  â€¢ Symptom: what observable behavior?\n\n"
                    f"You can still complete the task, but documentation will be required before marking as completed."
                )
                message = (message or "") + advisory
        elif tool_name == "TaskUpdate":
            message = track_task_update(tool_input, session_id, terminal_id)
        elif tool_name == "TaskList":
            all_tasks = get_all_sessions_tasks()
            message = f"[Task Tracker] Synced {len(all_tasks)} tasks across all sessions"

        if message:
            return {"injection": message}

        return {}


