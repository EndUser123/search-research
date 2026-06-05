"""Resolve global hooks directory from any install location.

Used by plugin hooks to find shared __lib__ modules and state directories
regardless of whether running from source tree, plugin cache, or compat wrapper.
"""
from __future__ import annotations

import os
from pathlib import Path


def get_hooks_dir() -> Path:
    """Resolve the global hooks directory (P:/.claude/hooks/).

    Resolution order:
    1. CLAUDE_HOOKS_DIR env var (explicit override)
    2. CLAUDE_PROJECT_DIR env var + .claude/hooks/
    3. Walk up from this file looking for .claude/hooks/
    4. Hardcoded fallback P:/.claude/hooks/
    """
    # Explicit override
    env = os.environ.get("CLAUDE_HOOKS_DIR")
    if env:
        p = Path(env)
        if p.is_dir():
            return p

    # Project dir + relative path
    env = os.environ.get("CLAUDE_PROJECT_DIR")
    if env:
        p = Path(env) / ".claude" / "hooks"
        if p.is_dir():
            return p

    # Walk up from this file
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / ".claude" / "hooks"
        if candidate.is_dir():
            return candidate

    # Hardcoded fallback
    return Path("P:/.claude/hooks")


def get_plugin_lib() -> Path:
    """Resolve this plugin's lib/ directory."""
    return Path(__file__).resolve().parent
