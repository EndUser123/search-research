"""Shared state path constants for cc-aca-session hooks.

All paths resolve relative to the global hooks directory or user home,
never relative to the plugin install location (which changes between
source at P:/packages/ and cache at C:/Users/.../cache/local/.../).
"""

from __future__ import annotations

import os
import re
from pathlib import Path


def _resolve_project_root() -> Path:
    """Find the project root by looking for .claude/hooks/.

    Walks up from CWD, then falls back to CLAUDE_PROJECT_DIR env var,
    then to P:/ as a last resort.
    """
    # Try CWD upward
    cwd = Path.cwd()
    for parent in [cwd, *cwd.parents]:
        if (parent / ".claude" / "hooks").is_dir():
            return parent

    # Try env var
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")
    if project_dir and Path(project_dir, ".claude", "hooks").is_dir():
        return Path(project_dir)

    # Fallback
    return Path("P:/")


def get_hooks_dir() -> Path:
    """Resolve the global hooks directory."""
    return _resolve_project_root() / ".claude" / "hooks"


def get_state_dir() -> Path:
    """Global hooks state directory."""
    return get_hooks_dir() / "state"


def get_evidence_dir() -> Path:
    """Global hooks evidence directory."""
    return get_hooks_dir() / "evidence"


def get_plan_dir() -> Path:
    """User's home .claude/plans directory."""
    return Path.home() / ".claude" / "plans"


def get_tdd_state_dir(terminal_id: str) -> Path:
    """Terminal-isolated TDD state directory."""
    return Path.home() / ".claude" / ".state" / "tdd" / terminal_id


def get_session_data_dir() -> Path:
    """Session-scoped data directory."""
    return get_hooks_dir() / "session_data"


def safe_id(value: str | None) -> str:
    """Sanitize a value for use in filenames."""
    if not value:
        return "unknown"
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", value)


def get_discovery_state_path(session_id: str) -> Path:
    """Discovery state file for a given session."""
    return Path.home() / ".claude" / f"discovery_state_{safe_id(session_id)}.json"


def get_plugin_lib_dir() -> Path:
    """Resolve this plugin's lib/ directory from any install location."""
    return Path(__file__).resolve().parent
