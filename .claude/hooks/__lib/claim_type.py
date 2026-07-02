"""Claim type reader for Stop gates.

Reads claim_type from .state/claim_type_{terminal}.json written by
UserPromptSubmit_claim_classifier.py. Used by Stop gates to short-circuit
when the gate is not relevant to the current claim type.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

_HOOKS_DIR = Path(__file__).resolve().parent.parent


def _terminal_state_path(terminal_id: str, filename: str) -> Path:
    """Resolve a terminal-scoped state path via state_paths, with legacy fallback."""
    try:
        sys.path.insert(0, str(_HOOKS_DIR / "__lib"))
        from state_paths import get_terminal_state_path  # type: ignore[import-not-found]
        return get_terminal_state_path(terminal_id, filename)
    except Exception:
        state_dir = _HOOKS_DIR / ".state"
        state_dir.mkdir(parents=True, exist_ok=True)
        return state_dir / filename


def _safe_id(value: str | None) -> str:
    """Convert terminal id to filesystem-safe fragment."""
    if not value:
        return "unknown"
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", value)


def _read_claim_type(terminal_id: str) -> str | None:
    """Read claim_type from state file, or None if not found.

    Returns: claim_type string or None
    """
    if not terminal_id:
        return None
    safe_id = _safe_id(terminal_id)
    state_path = _terminal_state_path(terminal_id, f"claim_type_{safe_id}.json")
    # Legacy fallback: pre-2026-07-02 files lived flat in hooks/.state/
    if not state_path.exists():
        legacy = _HOOKS_DIR / ".state" / f"claim_type_{safe_id}.json"
        if legacy.exists():
            state_path = legacy
    if not state_path.exists():
        return None
    try:
        with open(state_path, "r", encoding="utf-8") as f:
            state = json.load(f)
        return state.get("claim_type")
    except Exception:
        return None


def get_claim_type(terminal_id: str) -> str | None:
    """Public API: read claim_type for a terminal, or None if not available."""
    return _read_claim_type(terminal_id)