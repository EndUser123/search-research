"""Canonical terminal_id for multi-terminal isolation.

Provides a single, authoritative terminal_id algorithm used by all modules:
- claude_code_raw / claude_log (providers)
- critique_io (skill)
- gto_orchestrator (skill)

Algorithm:
    1. CLAUDE_TERMINAL_ID env var (explicit override)
    2. hostname + cwd + pid → SHA256 → first 12 chars

This ensures:
- Unique per terminal even in same directory (different pid)
- Stable across compactions within same terminal session
- No collisions between terminals in different working directories
"""

from __future__ import annotations

import hashlib
import os
import socket
from pathlib import Path


def canonical_terminal_id() -> str:
    """Return the canonical terminal identifier for this process.

    Priority:
    1. CLAUDE_TERMINAL_ID env var (explicit override — use this for testing)
    2. hostname + cwd + pid → SHA256[:12] (deterministic, collision-resistant)

    Returns:
        A 12-character alphanumeric string matching [a-zA-Z0-9_-]{1,64}.
    """
    # Priority 1: explicit env override
    if env_id := os.environ.get("CLAUDE_TERMINAL_ID", "").strip():
        return env_id

    # Priority 2: derive from host + cwd + pid
    try:
        hostname = socket.gethostname()
        cwd = str(Path.cwd())
        pid = os.getpid()
        raw = f"{hostname}/{cwd}/{pid}"
        return hashlib.sha256(raw.encode()).hexdigest()[:12]
    except Exception:
        # Last-resort fallback — should never reach here in practice
        return "unknown"
