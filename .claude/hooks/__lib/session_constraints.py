#!/usr/bin/env python3
"""Lightweight session-scoped constraint storage for user corrections.

Persists user corrections ("English only", "answer directly") across turns
within a session. Loads constraints at prompt-assembly time so they apply
to subsequent turns until explicitly revoked.

Storage: one JSON file per session in .claude/state/constraints/.
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Dict, List

_STATE_DIR = Path("P:/.claude/state/constraints")
_TTL_SECONDS = 7200  # 2 hours

# Correction phrase patterns → constraint key
_CORRECTION_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\benglish\s+only\b", re.IGNORECASE), "english_only"),
    (re.compile(r"\banswer\s+(me\s+)?directly\b", re.IGNORECASE), "direct_answer"),
    (re.compile(r"\bstop\s+(?:doing|using|saying)\s+", re.IGNORECASE), "stop_directive"),
    (re.compile(r"\brespond\s+in\s+english\b", re.IGNORECASE), "english_only"),
    (re.compile(r"\buse\s+english\b", re.IGNORECASE), "english_only"),
    (re.compile(r"\bno\s+(?:non-?english|other\s+language)\b", re.IGNORECASE), "english_only"),
]

# Revocation patterns
_REVOKE_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\byou\s+can\s+use\s+\w+\s+(?:now|again)\b", re.IGNORECASE), "english_only"),
    (re.compile(r"\b(?:respond|answer)\s+in\s+any\s+language\b", re.IGNORECASE), "english_only"),
    (re.compile(r"\bnever\s+mind\s+.*(?:english|language|direct)\b", re.IGNORECASE), None),
]


def _session_file(session_id: str) -> Path:
    return _STATE_DIR / f"{session_id}.json"


def _ensure_dir() -> None:
    _STATE_DIR.mkdir(parents=True, exist_ok=True)


def detect_corrections(text: str) -> List[str]:
    """Return constraint keys detected in user text."""
    if not text:
        return []
    constraints: List[str] = []
    for pattern, key in _CORRECTION_PATTERNS:
        if pattern.search(text):
            constraints.append(key)
    return list(dict.fromkeys(constraints))  # dedupe preserving order


def detect_revocations(text: str) -> List[str]:
    """Return constraint keys to revoke, or ['*'] for full revocation."""
    if not text:
        return []
    revoked: List[str] = []
    for pattern, key in _REVOKE_PATTERNS:
        if pattern.search(text):
            if key is None:
                return ["*"]
            revoked.append(key)
    return list(dict.fromkeys(revoked))


def save_constraints(session_id: str, additions: List[str], removals: List[str]) -> Dict[str, float]:
    """Update constraints for a session. Returns the new constraint dict."""
    _ensure_dir()
    current = load_constraints(session_id)
    now = time.time()

    for key in additions:
        current[key] = now

    if "*" in removals:
        current.clear()
    else:
        for key in removals:
            current.pop(key, None)

    path = _session_file(session_id)
    if current:
        path.write_text(json.dumps(current, indent=2), encoding="utf-8")
    elif path.exists():
        path.unlink()

    return current


def load_constraints(session_id: str) -> Dict[str, float]:
    """Load active (non-stale) constraints for a session."""
    path = _session_file(session_id)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}

    now = time.time()
    return {k: ts for k, ts in data.items() if now - ts < _TTL_SECONDS}


def constraints_active(session_id: str) -> List[str]:
    """Return list of currently active constraint keys."""
    return list(load_constraints(session_id).keys())


def build_constraint_prompt(session_id: str) -> str | None:
    """Return a prompt fragment for active constraints, or None."""
    active = constraints_active(session_id)
    if not active:
        return None

    parts = []
    if "english_only" in active:
        parts.append(
            "SESSION CONSTRAINT (active until revoked): Output must be in English only. "
            "Do not use any other language in your response."
        )
    if "direct_answer" in active:
        parts.append(
            "SESSION CONSTRAINT (active until revoked): Answer concrete questions "
            "directly in the first sentence."
        )
    if "stop_directive" in active:
        parts.append(
            "SESSION CONSTRAINT (active until revoked): A 'stop doing X' directive "
            "was issued. Apply it to all subsequent turns."
        )
    return "\n".join(parts) if parts else None
