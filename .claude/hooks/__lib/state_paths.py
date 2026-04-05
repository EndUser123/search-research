#!/usr/bin/env python3
"""
State path utilities for multi-terminal isolation.

Provides centralized functions for getting terminal-scoped and session-scoped
state file paths, ensuring consistent multi-terminal isolation across all hooks.

Architecture:
- Terminal-scoped state: .claude/state/terminals/{terminal_id}/
- Session-scoped state: .claude/state/sessions/{session_id}/
- Shared state: .claude/state/shared/

Usage:
    from state_paths import get_terminal_state_dir, get_terminal_state_path
    from state_paths import get_session_state_dir, get_session_state_path

    # Terminal-scoped state (persists across sessions in same terminal)
    terminal_dir = get_terminal_state_dir(terminal_id)
    intent_file = get_terminal_state_path(terminal_id, "pending_command_intent.json")

    # Session-scoped state (unique per CC session)
    session_dir = get_session_state_dir(session_id)
    log_file = get_session_state_path(session_id, "actions.log")
"""

from __future__ import annotations

import os
from pathlib import Path

# State directory structure
STATE_DIR = Path(os.environ.get("PROJECT_ROOT", ".")) / ".claude" / "state"
TERMINALS_DIR = STATE_DIR / "terminals"
SESSIONS_DIR = STATE_DIR / "sessions"
SHARED_DIR = STATE_DIR / "shared"

# Path lookup cache for memoization
_PATH_CACHE: dict[str, Path] = {}


def _get_cached_dir(cache_key: str, dir_path: Path) -> Path:
    """
    Get directory from cache or create and cache it.

    This helper function implements memoization for path resolution,
    reducing redundant stat() and mkdir() calls during test execution.

    Args:
        cache_key: Unique key for caching (e.g., "terminal:console_123")
        dir_path: Path object to cache

    Returns:
        Cached or newly created directory path
    """
    if cache_key not in _PATH_CACHE:
        dir_path.mkdir(parents=True, exist_ok=True)
        _PATH_CACHE[cache_key] = dir_path
    return _PATH_CACHE[cache_key]


def clear_path_cache() -> None:
    """
    Clear the path lookup cache.

    This function is primarily useful for testing to ensure
    test isolation. Each test should start with a fresh cache.
    """
    _PATH_CACHE.clear()


def get_terminal_state_dir(terminal_id: str) -> Path:
    """
    Get the terminal-scoped state directory for a given terminal_id.

    Creates the directory if it doesn't exist.

    Args:
        terminal_id: Terminal ID from get_terminal_id()

    Returns:
        Path to terminal state directory: .claude/state/terminals/{terminal_id}/

    Examples:
        >>> get_terminal_state_dir("console_abc123")
        Path(".../.claude/state/terminals/console_abc123/")
    """
    if not terminal_id:
        # Fallback to global state if no terminal ID
        cache_key = "global_state"
        return _get_cached_dir(cache_key, STATE_DIR)

    terminal_dir = TERMINALS_DIR / terminal_id
    cache_key = f"terminal:{terminal_id}"
    return _get_cached_dir(cache_key, terminal_dir)


def get_terminal_state_path(terminal_id: str, filename: str) -> Path:
    """
    Get a terminal-scoped state file path.

    Args:
        terminal_id: Terminal ID from get_terminal_id()
        filename: State file name (e.g., "pending_command_intent.json")

    Returns:
        Full path to terminal-scoped state file

    Examples:
        >>> get_terminal_state_path("console_abc123", "pending_command_intent.json")
        Path(".../.claude/state/terminals/console_abc123/pending_command_intent.json")
    """
    terminal_dir = get_terminal_state_dir(terminal_id)
    return terminal_dir / filename


def get_session_state_dir(session_id: str) -> Path:
    """
    Get the session-scoped state directory for a given session_id.

    Creates the directory if it doesn't exist.

    Args:
        session_id: Session ID from get_session_id()

    Returns:
        Path to session state directory: .claude/state/sessions/{session_id}/

    Examples:
        >>> get_session_state_dir("env_session_abc123")
        Path(".../.claude/state/sessions/env_session_abc123/")
    """
    if not session_id:
        # Fallback to global state if no session ID
        cache_key = "global_state"
        return _get_cached_dir(cache_key, STATE_DIR)

    session_dir = SESSIONS_DIR / session_id
    cache_key = f"session:{session_id}"
    return _get_cached_dir(cache_key, session_dir)


def get_session_state_path(session_id: str, filename: str) -> Path:
    """
    Get a session-scoped state file path.

    Args:
        session_id: Session ID from get_session_id()
        filename: State file name (e.g., "actions.log")

    Returns:
        Full path to session-scoped state file

    Examples:
        >>> get_session_state_path("env_session_abc123", "actions.log")
        Path(".../.claude/state/sessions/env_session_abc123/actions.log")
    """
    session_dir = get_session_state_dir(session_id)
    return session_dir / filename


def get_shared_state_dir() -> Path:
    """
    Get the shared state directory (global across all terminals and sessions).

    Creates the directory if it doesn't exist.

    Returns:
        Path to shared state directory: .claude/state/shared/

    Examples:
        >>> get_shared_state_dir()
        Path(".../.claude/state/shared/")
    """
    cache_key = "shared_state"
    return _get_cached_dir(cache_key, SHARED_DIR)


def get_shared_state_path(filename: str) -> Path:
    """
    Get a shared state file path (global across all terminals and sessions).

    Args:
        filename: State file name (e.g., "hook_ledger.db")

    Returns:
        Full path to shared state file

    Examples:
        >>> get_shared_state_path("hook_ledger.db")
        Path(".../.claude/state/shared/hook_ledger.db")
    """
    shared_dir = get_shared_state_dir()
    return shared_dir / filename


def migrate_legacy_state_file(
    legacy_path: Path, terminal_id: str | None = None, session_id: str | None = None
) -> Path | None:
    """
    Migrate a legacy state file to the new terminal/session-scoped structure.

    Args:
        legacy_path: Path to legacy state file in .claude/state/
        terminal_id: Terminal ID for terminal-scoped files
        session_id: Session ID for session-scoped files

    Returns:
        New path if migration occurred, None if file doesn't exist

    Examples:
        >>> migrate_legacy_state_file(
        ...     Path(".claude/state/pending_command_intent.json"),
        ...     terminal_id="console_abc123"
        ... )
        Path(".../.claude/state/terminals/console_abc123/pending_command_intent.json")
    """
    if not legacy_path.exists():
        return None

    filename = legacy_path.name

    # Determine new location based on filename pattern
    if terminal_id and ("terminal" in filename.lower() or "intent" in filename.lower()):
        # Terminal-scoped
        new_path = get_terminal_state_path(terminal_id, filename)
    elif session_id and ("session" in filename.lower() or "execution" in filename.lower()):
        # Session-scoped
        new_path = get_session_state_path(session_id, filename)
    else:
        # Keep in shared state
        new_path = get_shared_state_path(filename)

    # Only migrate if not already at new location
    if new_path != legacy_path:
        try:
            import shutil

            new_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(legacy_path, new_path)
            return new_path
        except (OSError, shutil.Error):
            # Migration failed, return None
            return None

    return None


def cleanup_legacy_state_file(legacy_path: Path, migrated_to: Path | None = None) -> bool:
    """
    Clean up a legacy state file after successful migration.

    Args:
        legacy_path: Path to legacy state file
        migrated_to: New path if migration succeeded

    Returns:
        True if cleanup succeeded, False otherwise
    """
    if migrated_to and migrated_to.exists():
        try:
            legacy_path.unlink()
            return True
        except OSError:
            return False
    return False
