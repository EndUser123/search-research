"""Cross-hook challenge marker for anti-sycophancy coordination.

Canonical location for _challenge_marker_path — owned by the epistemic plugin.
Stop hooks and UPS modules both import from here (dependency direction:
domain primitive → consumers).

Moved from UserPromptSubmit_modules/anti_sycophancy_injector to break the
reverse dependency (Stop hooks importing from UPS internals).
"""
from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path


def safe_id(value: str | None) -> str:
    if not value:
        return "unknown"
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", value)


def state_dirs() -> list[Path]:
    primary = Path("P:/.claude/hooks/state/anti_sycophancy_injector")
    fallback = Path(tempfile.gettempdir()) / "claude_hooks" / "state" / "anti_sycophancy_injector"
    if os.environ.get("PYTEST_CURRENT_TEST"):
        return [fallback]
    return [primary, fallback]


def challenge_marker_path(session_id: str, terminal_id: str) -> Path:
    """Return path for cross-hook challenge marker (read by Stop hooks)."""
    filename = f"challenge__{safe_id(session_id)}__{safe_id(terminal_id)}.json"
    for base in state_dirs():
        try:
            base.mkdir(parents=True, exist_ok=True)
            return base / filename
        except OSError:
            continue
    return (
        Path(tempfile.gettempdir())
        / "claude_hooks"
        / "state"
        / "anti_sycophancy_injector"
        / filename
    )
