#!/usr/bin/env python3
"""Stop gate: Block implementation intent without explicit /approve."""
from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

from __lib.response_intent import IntentClass, is_meta_or_quoted_context

HOOKS_DIR = Path(__file__).resolve().parent
ARTIFACTS_BASE = Path(os.environ.get("CLAUDE_ARTIFACTS_DIR", str(HOOKS_DIR.parent / ".artifacts")))

# Patterns that indicate explicit implementation intent (not general conversation)
_IMPLEMENT_PATTERNS = [
    # "proceeding to implement" - explicit statement of intent
    re.compile(r"(?i)\bproceeding to (?:implement|execute|deploy)\b"),
    # "want me to implement" - explicit request for action
    re.compile(r"(?i)\bwant me to implement\b"),
]


def _terminal_id() -> str:
    tid = os.environ.get("CLAUDE_TERMINAL_ID", "").strip()
    if tid:
        return tid
    tid = os.environ.get("WT_SESSION", "").strip()
    return tid if tid else "default"


def _approval_file() -> Path:
    return ARTIFACTS_BASE / _terminal_id() / "approval.json"


def _check_approval() -> tuple[bool, dict]:
    """Check approval state. Returns (approved, state) tuple."""
    path = _approval_file()
    if not path.exists():
        return False, {}
    try:
        data = json.loads(path.read_text())
        ts = data.get("ts", 0)
        ttl_hours = data.get("ttl_hours", 24)
        if ts and time.time() - ts > ttl_hours * 3600:
            try:
                path.unlink()
            except OSError:
                pass
            return False, {}
        return data.get("approved") is True, data
    except (json.JSONDecodeError, OSError):
        return False, {}


def _block(reason: str) -> dict:
    """Create block response."""
    return {"decision": "block", "reason": reason}


def run(data: dict) -> dict | None:
    response = data.get("response", "")
    if not response:
        return None

    # Gate debug/meta discussion — don't block diagnostic responses about triggers
    if is_meta_or_quoted_context(response):
        return None

    # Check for implement intent first
    if not any(p.search(response) for p in _IMPLEMENT_PATTERNS):
        return None

    # After confirming intent, double-check context wasn't just meta
    # (handles mixed case: quoted trigger + real commitment outside quote)
    intent = is_meta_or_quoted_context(response)
    if intent == IntentClass.GATE_DEBUG_META:
        return None

    # Check approval state (returns tuple)
    approved, state = _check_approval()
    if not approved:
        return _block("IMPLEMENTATION WITHOUT APPROVAL\n\nDetected implementation/execute intent without /approve.\nRequired: Add `/approve execute` to your message.\n")

    # Phase-aware approval check
    phase = state.get("phase", "")
    if phase not in ("execute", "deploy"):
        return _block(
            f"PHASE MISMATCH: {phase}\n\nApproval phase is '{phase}' but gate requires 'execute' or 'deploy'.\n"
            f"Fix: Use `/approve execute` to re-approve with correct phase.\n"
        )

    return None  # Approved


if __name__ == "__main__":
    raw = sys.stdin.read()
    try:
        input_data = json.loads(raw)
    except json.JSONDecodeError:
        input_data = {}
    result = run(input_data)
    if result:
        print(json.dumps(result))
        sys.exit(2)
    sys.exit(0)