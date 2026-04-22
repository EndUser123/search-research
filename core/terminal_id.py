"""Canonical terminal_id for multi-terminal isolation.

Provides a single, authoritative terminal_id algorithm used by all modules:
- claude_code_raw / claude_log (providers)
- critique_io (skill)
- gto_orchestrator (skill)

Algorithm:
    1. CLAUDE_TERMINAL_ID env var (explicit override)
    2. WT_SESSION env var (Windows Terminal session — stable across compactions)
    3. ConEmuServerPID env var (fallback on Windows)

This ensures:
- Unique per terminal session
- Stable across compactions within same terminal session
- No collisions between terminals in different sessions
"""

from __future__ import annotations

import os


def canonical_terminal_id() -> str:
    """Return the canonical terminal identifier for this process.

    Priority:
    1. CLAUDE_TERMINAL_ID env var (explicit override — use for testing)
    2. WT_SESSION env var (Windows Terminal session ID — stable across compactions)
    3. ConEmu session ID (fallback on Windows)

    Returns:
        A terminal identifier string prefixed with "console_" for artifact paths.
        Example: "console_081c35fc-2c20-42d8-90ee-fc271a305b8c"
    """
    # Priority 1: explicit env override
    if env_id := os.environ.get("CLAUDE_TERMINAL_ID", "").strip():
        return f"console_{env_id}"

    # Priority 2: Windows Terminal session (stable across compactions)
    if wt_sid := os.environ.get("WT_SESSION", "").strip():
        return f"console_{wt_sid}"

    # Priority 3: ConEmu session
    if conemu_sid := os.environ.get("ConEmuServerPID", "").strip():
        return f"console_{conemu_sid}"

    # Last-resort fallback — should never reach here in practice
    return "console_unknown"
