"""Terminal-scoped state management for fact-guard."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Optional


def detect_terminal_id() -> str:
    """Detect terminal ID from Claude Code environment."""
    if env_id := os.environ.get("CLAUDE_TERMINAL_ID"):
        return env_id

    # Fallback: hash of cwd + user
    cwd = os.getcwd()
    user = os.environ.get("USER", "unknown")
    terminal_seed = f"{user}:{cwd}"
    return hashlib.md5(terminal_seed.encode()).hexdigest()[:8]


def get_state_dir(terminal_id: Optional[str] = None) -> Path:
    """Get or create state directory for this terminal."""
    if terminal_id is None:
        terminal_id = detect_terminal_id()

    state_dir = Path.home() / ".claude" / ".artifacts" / f"console_{terminal_id}" / "fact_guard"
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir


def read_state(filename: str, terminal_id: Optional[str] = None) -> dict[str, Any]:
    """Read JSON state file."""
    state_dir = get_state_dir(terminal_id)
    state_file = state_dir / filename

    if state_file.exists():
        try:
            with open(state_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def write_state(data: dict[str, Any], filename: str, terminal_id: Optional[str] = None) -> None:
    """Write JSON state file atomically."""
    state_dir = get_state_dir(terminal_id)
    state_file = state_dir / filename

    with tempfile.NamedTemporaryFile(
        mode="w", dir=state_dir, delete=False, suffix=".tmp", encoding="utf-8"
    ) as tmp:
        json.dump(data, tmp, indent=2, ensure_ascii=False)
        tmp.flush()
        os.fsync(tmp.fileno())
        tmp_path = tmp.name

    os.chmod(tmp_path, 0o600)  # Restrict to owner read/write
    os.replace(tmp_path, state_file)


def reset_session(terminal_id: Optional[str] = None) -> None:
    """Clear all state for this terminal."""
    state_dir = get_state_dir(terminal_id)
    for f in state_dir.glob("*.json"):
        try:
            f.unlink()
        except OSError:
            pass
