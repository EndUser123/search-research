#!/usr/bin/env python3
"""Stop gate: Block implementation intent without explicit /approve."""
from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
ARTIFACTS_BASE = Path(os.environ.get("CLAUDE_ARTIFACTS_DIR", str(HOOKS_DIR.parent / ".artifacts")))

_IMPLEMENT_PATTERNS = [
    re.compile(r"(?i)\b(?:implement(?:ing|s)?|execute|proceed|deploy)\b.*?(?:now|it)\b"),
    re.compile(r"(?i)\b(?:i'?ll|i am going to)\s+(?:implement|execute|deploy|build)\b"),
    re.compile(r"(?i)\bproceeding to (?:implement|execute|deploy)\b"),
    re.compile(r"(?i)\bwant me to implement\b"),
    re.compile(r"(?i)\b(?:deploy(?:ing|s)?|execute)\b"),
]


def _terminal_id() -> str:
    tid = os.environ.get("CLAUDE_TERMINAL_ID", "").strip()
    if tid:
        return tid
    tid = os.environ.get("WT_SESSION", "").strip()
    return tid if tid else "default"


def _approval_file() -> Path:
    return ARTIFACTS_BASE / _terminal_id() / "approval.json"


def _check_approval() -> bool:
    path = _approval_file()
    if not path.exists():
        return False
    try:
        data = json.loads(path.read_text())
        # TTL check: 1 hour expiry
        ts = data.get("ts", 0)
        if ts and time.time() - ts > 3600:
            try:
                path.unlink()
            except OSError:
                pass
            return False
        return data.get("approved") is True
    except (json.JSONDecodeError, OSError):
        return False


def run(data: dict) -> dict | None:
    response = data.get("response", "")
    if not response:
        return None

    if not any(p.search(response) for p in _IMPLEMENT_PATTERNS):
        return None

    if _check_approval():
        return None

    return {
        "decision": "block",
        "reason": (
            "IMPLEMENTATION WITHOUT APPROVAL\n\n"
            "Detected implementation/execute intent without /approve.\n"
            "Required: Add `/approve execute` to your message.\n"
        ),
    }


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
