"""Resolve the global hooks directory from plugin context."""
from __future__ import annotations

import os
from pathlib import Path


def get_hooks_dir() -> Path:
    # 1. Explicit env var
    env = os.environ.get("CLAUDE_HOOKS_DIR", "").strip()
    if env:
        p = Path(env)
        if p.is_dir():
            return p

    # 2. CLAUDE_PROJECT_DIR + .claude/hooks/
    proj = os.environ.get("CLAUDE_PROJECT_DIR", "").strip()
    if proj:
        p = Path(proj) / ".claude" / "hooks"
        if p.is_dir():
            return p

    # 3. Walk up from this file
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / ".claude" / "hooks"
        if candidate.is_dir():
            return candidate

    # 4. Hardcoded fallback
    return Path("P:/.claude/hooks")
