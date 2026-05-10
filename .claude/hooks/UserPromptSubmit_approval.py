#!/usr/bin/env python3
"""UserPromptSubmit hook: Handle /approve command, write approval state."""
from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
ARTIFACTS_BASE = Path(os.environ.get("CLAUDE_ARTIFACTS_DIR", str(HOOKS_DIR.parent / ".artifacts")))
TERMINAL_ID = os.environ.get("CLAUDE_TERMINAL_ID", os.environ.get("WT_SESSION", "default"))


def _approval_file() -> Path:
    return ARTIFACTS_BASE / TERMINAL_ID / "approval.json"


def _register_hooks():
    """Self-register hook for registry loading."""
    from UserPromptSubmit_modules.registry import register_hook

    register_hook("approval", priority=9.0)


def process_prompt(data: dict) -> dict | None:
    prompt = data.get("prompt", "")
    if not prompt:
        return None

    # Match /approve <phase> [skill]
    m = re.match(r"^/approve\s+(\w+)(?:\s+(\w+))?", prompt, re.I)
    if not m:
        return None

    phase = m.group(1)
    skill = m.group(2) or "design"

    approval_file = _approval_file()
    approval_file.parent.mkdir(parents=True, exist_ok=True)
    approval_file.write_text(json.dumps({
        "skill": skill,
        "phase": phase,
        "approved": True,
        "ts": time.time(),
    }))

    return None  # Silent pass-through


if __name__ == "__main__":
    raw = sys.stdin.read()
    try:
        input_data = json.loads(raw)
    except json.JSONDecodeError:
        input_data = {}
    result = process_prompt(input_data)
    print(json.dumps(result or {}))
    sys.exit(0)


# Auto-register hook on module import
_register_hooks()
