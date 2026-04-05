"""Centralized session and terminal detection utilities.

Consolidates duplicated logic from:
- UserPromptSubmit_router.py:_get_session_id()
- pre_tool_use.py:_get_session_id()
- Stop_router.py:get_session_id()
- PostToolUse_router.py:get_session_id()
- terminal_detection.py:detect_terminal_id()

This eliminates duplication across 4+ router files.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Import singleton for caching
_session_id_cache = None
_terminal_id_cache = None


def get_session_id() -> str:
    """Get consistent session ID for this Claude Code instance.

    Uses parent PID (Claude Code process) for consistency across hook invocations.
    All hooks spawned by the same CC instance share the parent PID.

    Returns:
        Session ID string (parent PID or CLAUDE_SESSION_ID env var)
    """
    global _session_id_cache
    if _session_id_cache:
        return _session_id_cache

    # Try environment variable first
    if env_id := os.environ.get("CLAUDE_SESSION_ID"):
        _session_id_cache = env_id
        return env_id

    # Use parent process ID (Claude Code's PID)
    try:
        import psutil
        parent = psutil.Process(os.getpid()).parent()
        if parent:
            _session_id_cache = str(parent.pid)
            return _session_id_cache
    except (ImportError, Exception):
        pass

    # Fallback to parent PID without psutil
    try:
        _session_id_cache = str(os.getppid())
        return _session_id_cache
    except Exception:
        pass

    # Last resort: current PID (less reliable)
    _session_id_cache = str(os.getpid())
    return _session_id_cache


def detect_terminal_id() -> str:
    """Detect terminal/worktree ID for session isolation.

    Uses git worktree detection or fallback to hostname.

    Returns:
        Terminal ID string for state directory isolation
    """
    global _terminal_id_cache
    if _terminal_id_cache:
        return _terminal_id_cache

    # Try git worktree detection
    try:
        import subprocess
        creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        result = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=str(Path.cwd()),
            creationflags=creation_flags
        )
        if result.returncode == 0:
            git_dir = Path(result.stdout.strip())
            # Use git common dir or worktree name
            if ".git/worktrees" in str(git_dir):
                # Extract worktree name
                parts = git_dir.parts
                if "worktrees" in parts:
                    idx = parts.index("worktrees")
                    if idx + 1 < len(parts):
                        _terminal_id_cache = f"worktree_{parts[idx + 1]}"
                        return _terminal_id_cache
    except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
        pass

    # Fallback to hostname
    try:
        import socket
        _terminal_id_cache = f"terminal_{socket.gethostname()}"
        return _terminal_id_cache
    except Exception:
        _terminal_id_cache = "terminal_unknown"
        return _terminal_id_cache


def clear_caches() -> None:
    """Clear cached session and terminal IDs.

    Useful for testing or when process state changes.
    """
    global _session_id_cache, _terminal_id_cache
    _session_id_cache = None
    _terminal_id_cache = None
