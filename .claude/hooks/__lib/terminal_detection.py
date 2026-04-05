#!/usr/bin/env python3
"""
Terminal detection utilities for multi-terminal isolation.

Provides centralized terminal ID detection for all hooks and systems.
Windows-specific console handle detection and terminal environment variable handling.
"""

from __future__ import annotations

import os
from typing import Any

# Terminal ID source prefixes
SOURCE_ENV = "env"
SOURCE_CONSOLE = "console"


def detect_console_host_terminal() -> str | None:
    """
    Detect Windows Terminal ID using WT_SESSION environment variable.

    WT_SESSION is a UUID that uniquely identifies a Windows Terminal session.
    It is stable across all subprocess invocations in the same terminal window,
    making it ideal for multi-terminal isolation.

    Returns:
        Raw UUID string if successful, None otherwise.
        (Normalization happens in _normalize_terminal_id)

    Note: GetConsoleWindow() fallback removed — WT_SESSION is always available
    in Windows Terminal environments (Git Bash, MINGW64, CMD, PowerShell all set it).
    """
    wt_session = os.environ.get("WT_SESSION")
    if wt_session:
        return wt_session  # Return raw UUID, normalization adds prefix

    return None


def detect_terminal_id() -> str:
    """
    Detect and normalize terminal ID for session isolation.

    Returns WT_SESSION with console_ prefix, or empty string if unavailable.
    WT_SESSION is always available in Windows Terminal environments.

    Returns:
        Normalized terminal ID (e.g. 'console_bf0cb56b-20f0-44be-ae48-a6b4644c26fe')
    """
    raw = detect_console_host_terminal()
    if raw:
        return f"{SOURCE_CONSOLE}_{raw}"
    return ""


# Terminal ID sanitization pattern: allow only filename-safe characters
def resolve_terminal_key(terminal_id: "dict[str, Any] | str | None" = None) -> str:
    """
    Resolve and sanitize terminal ID for use in filenames.

    Validates that the terminal ID contains only safe characters, then
    applies filename-safe sanitization (replaces \\, /, : with -).

    Accepts either:
    - A dict with 'terminal_id' or 'terminalId' key (legacy interface)
    - A raw string terminal ID
    - None (auto-detect from environment)

    Args:
        terminal_id: Terminal ID to resolve (uses detect_terminal_id() if None)

    Returns:
        Sanitized terminal key string

    Raises:
        ValueError: If terminal_id is invalid or fails validation
    """
    # Handle dict input (legacy interface from skill_guard.utils.terminal_detection)
    if isinstance(terminal_id, dict):
        tid = str(terminal_id.get("terminal_id") or terminal_id.get("terminalId") or "").strip()
        if tid:
            terminal_id = tid
        else:
            terminal_id = None

    if terminal_id is None:
        terminal_id = detect_terminal_id()

    # Validate
    if not terminal_id or not terminal_id.strip():
        raise ValueError("terminal_id cannot be empty or whitespace-only")

    if "\x00" in terminal_id:
        raise ValueError(f"terminal_id cannot contain null bytes (got: {repr(terminal_id)})")

    if ".." in terminal_id or terminal_id.startswith("."):
        raise ValueError(
            f"terminal_id cannot contain path traversal sequences (got: {terminal_id})"
        )

    # Sanitize for filename use: replace path separators with dash
    safe_id = terminal_id.replace("\\", "-").replace("/", "-").replace(":", "-")
    return safe_id
