#!/usr/bin/env python3
from __future__ import annotations

# Import auto-logging decorator
from __lib.hook_base import get_terminal_id, hook_main

r"""
SessionStart hook: Authoritative source for terminal_id and session_id.

ARCHITECTURE v3.0 (2026-03-14):
- This hook is the AUTHORITATIVE source of terminal_id for all systems
- Uses centralized get_terminal_id() from hook_base.py
- Writes terminal_id to {PROJECT_ROOT}/.claude/state/terminal_id.json (authoritative)
- Writes terminal_id to %TEMP%/claude_terminal_id.txt for statusline.ps1 compat
- Other systems (skill-guard, handoff) read from the shared state file

IMPORTANT: This hook now uses the centralized get_terminal_id() from hook_base.py
which provides consistent terminal ID derivation across all hooks.

v3.0: Refactored to use centralized get_terminal_id() from hook_base.py
v2.3: Writes to .claude/state/terminal_id.json as authoritative source
v2.2: Removed PID/numeric fallbacks — empty string when detection fails
v2.1: Uses normalized format from terminal_detection.py
v2.0: Environment variables instead of temp files
"""
import os
import tempfile
import uuid
from pathlib import Path

# Terminal ID source prefixes (must match skill-guard format for compatibility)
SOURCE_ENV = "env"
SOURCE_CONSOLE = "console"


def _normalize_id(raw_id: str, source: str) -> str:
    """
    Normalize terminal ID to consistent format: {source}_{id}.

    This function MUST match the implementation in hook_base.py's _normalize_terminal_id
    to ensure all systems use the same format.

    If ID already has a known prefix, preserve it (idempotent).
    """
    known_prefixes = (f"{SOURCE_ENV}_", f"{SOURCE_CONSOLE}_")

    if raw_id.startswith(known_prefixes):
        return raw_id

    # Legacy format: ConsoleHost_XXXX -> console source
    if raw_id.startswith("ConsoleHost_"):
        return f"{SOURCE_CONSOLE}_{raw_id[12:]}"

    # Legacy format: session_XXXX -> env source (came from SessionStart)
    if raw_id.startswith("session_"):
        return f"{SOURCE_ENV}_{raw_id[8:]}"

    return f"{source}_{raw_id}"


def get_session_id() -> str:
    """
    Get session ID (unique per CC invocation).

    Priority:
    1. CLAUDE_SESSION_ID env var (user override)
    2. Generate fresh UUID (normalized as env_session_{uuid})
    3. "" — uuid4 failure is extremely unlikely; no PID fallback

    Returns:
        Session ID string in normalized format.
    """
    # Priority 1: CLAUDE_SESSION_ID env var (user override)
    session_id = os.environ.get('CLAUDE_SESSION_ID')
    if session_id:
        return _normalize_id(session_id, SOURCE_ENV)

    # Priority 2: Generate session-unique UUID
    try:
        raw_uuid = uuid.uuid4().hex
        return _normalize_id(f"session_{raw_uuid}", SOURCE_ENV)
    except Exception:
        pass

    # No PID fallback — uuid4 failure is extremely unlikely; if it happens, return ""
    return ""

def write_terminal_id_to_shared_file(terminal_id: str) -> bool:
    """
    Write terminal_id to the shared file using atomic write.

    Args:
        terminal_id: The terminal ID to write.

    Returns:
        True if write succeeded, False otherwise.
    """
    try:
        shared_file = Path(tempfile.gettempdir()) / "claude_terminal_id.txt"
        shared_file.parent.mkdir(parents=True, exist_ok=True)

        # Atomic write: write to temp file, then rename
        temp_file = shared_file.with_suffix('.tmp')
        temp_file.write_text(terminal_id, encoding='utf-8')
        temp_file.replace(shared_file)

        return True
    except Exception:
        return False


def write_session_start_file(terminal_id: str) -> bool:
    """
    Write session start time file for this terminal.

    Creates or resets the session tracking file with the current time
    as the session start time. This should be called on CC startup.

    Args:
        terminal_id: The terminal ID for this session.

    Returns:
        True if write succeeded, False otherwise.
    """
    try:
        import time

        session_file = Path(tempfile.gettempdir()) / f"cc_settings_mtime_{terminal_id}.json"
        session_file.parent.mkdir(parents=True, exist_ok=True)

        now = int(time.time())
        session_data = {
            "start_time": now,
            "last_seen": now
        }

        import json
        session_file.write_text(json.dumps(session_data, separators=(',', ':')), encoding='utf-8')

        return True
    except Exception:
        return False


def persist_terminal_id_to_project(terminal_id: str, console_handle: str) -> bool:
    """
    Persist terminal_id to terminal-specific state file.

    MULTI-TERMINAL ISOLATION: Each terminal gets its own state file.
    Filename format: terminal_{hex_handle}.json (uses raw HWND, not normalized ID)

    This prevents terminals from overwriting each other's state when
    running 5+ concurrent terminals.

    Args:
        terminal_id: The normalized terminal ID to persist.
        console_handle: Raw hex console handle (from GetConsoleWindow).

    Returns:
        True if write succeeded, False otherwise.
    """
    try:
        import json
        import time

        project_root = os.environ.get("PROJECT_ROOT")
        if not project_root:
            return False

        # Terminal-specific state file: uses raw console handle in filename
        # This ensures each terminal gets its own file (multi-terminal isolation)
        state_file = Path(project_root) / ".claude" / "state" / f"terminal_{console_handle}.json"
        state_file.parent.mkdir(parents=True, exist_ok=True)

        state_data = {
            "terminal_id": terminal_id,
            "console_handle": console_handle,
            "pid": os.getpid(),
            "timestamp": time.time()
        }

        # Add parent_pid for session continuity (same terminal, different process)
        if hasattr(os, 'getppid'):
            try:
                state_data["parent_pid"] = os.getppid()
            except (OSError, AttributeError):
                # getppid() not available or failed - continue without parent_pid
                pass

        # Atomic write: write to temp file, then rename
        temp_file = state_file.with_suffix('.tmp')
        temp_file.write_text(json.dumps(state_data, separators=(',', ':')), encoding='utf-8')
        temp_file.replace(state_file)

        return True
    except Exception:
        return False


def cleanup_stale_terminal_state(project_root: str, max_age_hours: float = 24.0) -> int:
    """
    Clean up stale terminal-specific state files.

    Removes terminal state files older than max_age_hours. This prevents
    accumulation of stale data from closed terminals.

    Args:
        project_root: Project root directory path.
        max_age_hours: Maximum age in hours before a file is considered stale.

    Returns:
        Number of files cleaned up.
    """
    try:
        import time

        state_dir = Path(project_root) / ".claude" / "state"
        if not state_dir.exists():
            return 0

        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        cleaned_count = 0

        # Clean up terminal_*.json files older than max_age_hours
        for state_file in state_dir.glob("terminal_*.json"):
            try:
                file_age = current_time - state_file.stat().st_mtime
                if file_age > max_age_seconds:
                    state_file.unlink()
                    cleaned_count += 1
            except Exception:
                # Skip files that can't be read/deleted
                pass

        return cleaned_count
    except Exception:
        return 0


@hook_main
def main():
    """
    Main hook entry point.

    Detects terminal and session IDs, then writes to terminal-specific state files.
    This is the AUTHORITATIVE source of terminal_id for all systems.

    MULTI-TERMINAL ISOLATION: Each terminal gets its own state file:
    - {PROJECT_ROOT}/.claude/state/terminal_{hex_handle}.json

    Other systems (skill-guard, handoff) should read from these terminal-specific
    files or detect independently using compatible logic.

    Env vars are set for this subprocess only (sibling hooks do NOT inherit these).
    """
    # Get console handle first (needed for terminal-specific filename)
    # Try to extract from terminal_id if it's console_* format
    terminal_id = get_terminal_id()
    console_handle = None

    if terminal_id and terminal_id.startswith("console_"):
        console_handle = terminal_id[8:]  # Extract hex handle after "console_" prefix

    # Get session ID
    session_id = get_session_id()

    # Set env vars for this subprocess only (sibling hooks use their own detection)
    os.environ["CLAUDE_TERMINAL_ID"] = terminal_id
    os.environ["CLAUDE_SESSION_ID"] = session_id

    # Write to terminal-specific state file (multi-terminal isolated)
    if terminal_id and console_handle:  # Only persist if we detected valid IDs
        project_root = os.environ.get("PROJECT_ROOT", "")
        persist_terminal_id_to_project(terminal_id, console_handle)

        # Clean up stale terminal state files from other terminals
        if project_root:
            cleanup_stale_terminal_state(project_root)

    # Write to temp files for backward compat (statusline.ps1, etc.)
    write_terminal_id_to_shared_file(terminal_id)
    write_session_start_file(terminal_id)

if __name__ == "__main__":
    main()
