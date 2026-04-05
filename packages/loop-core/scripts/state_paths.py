"""State path utilities for loop-core package.

This module provides terminal-scoped and session-scoped state file paths,
copied from hooks infrastructure to make loop-core standalone.
"""

from __future__ import annotations

import os
from pathlib import Path

# State directory structure
STATE_DIR = Path(os.environ.get("PROJECT_ROOT", ".")) / ".claude" / "state"
TERMINALS_DIR = STATE_DIR / "terminals"
SESSIONS_DIR = STATE_DIR / "sessions"
SHARED_DIR = STATE_DIR / "shared"


def get_terminal_state_dir(terminal_id: str) -> Path:
    """
    Get the terminal-scoped state directory for a given terminal_id.

    Creates the directory if it doesn't exist.

    Args:
        terminal_id: Terminal ID from get_terminal_id()

    Returns:
        Path to terminal state directory: .claude/state/terminals/{terminal_id}/
    """
    if not terminal_id:
        # Fallback to global state if no terminal ID
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        return STATE_DIR

    terminal_dir = TERMINALS_DIR / terminal_id
    terminal_dir.mkdir(parents=True, exist_ok=True)
    return terminal_dir


def get_terminal_state_path(terminal_id: str, filename: str) -> Path:
    """
    Get a terminal-scoped state file path.

    Args:
        terminal_id: Terminal ID from get_terminal_id()
        filename: State file name (e.g., "pending_command_intent.json")

    Returns:
        Full path to terminal-scoped state file
    """
    terminal_dir = get_terminal_state_dir(terminal_id)
    return terminal_dir / filename


def get_terminal_log_dir(terminal_id: str) -> Path:
    """
    Get the terminal-scoped log directory for a given terminal_id.

    Creates the directory if it doesn't exist.

    Args:
        terminal_id: Terminal ID from get_terminal_id()

    Returns:
        Path to terminal log directory: .claude/state/terminals/{terminal_id}/logs/
    """
    if not terminal_id:
        # Fallback to shared logs if no terminal ID
        log_dir = STATE_DIR / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir

    terminal_dir = TERMINALS_DIR / terminal_id
    log_dir = terminal_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def get_terminals_dir() -> Path:
    """
    Get the terminals directory path.

    Returns:
        Path to terminals directory: .claude/state/terminals/
    """
    TERMINALS_DIR.mkdir(parents=True, exist_ok=True)
    return TERMINALS_DIR
