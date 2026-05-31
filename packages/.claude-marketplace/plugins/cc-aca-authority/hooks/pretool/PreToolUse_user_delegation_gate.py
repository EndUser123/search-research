#!/usr/bin/env python3
"""
PreToolUse Delegation Gate - Block ask-user-before-investigate on diagnostic turns.

Enforces that AskUserQuestion tool calls on diagnostic/investigative topics are blocked
when no prior relevant investigation exists in the ledger.

The topic-scoped investigation check is shared with lazy_closure_detector (Stop) via
__lib/anti_lazy_policy.py — both modules import from the same canonical source.
"""

from __future__ import annotations


# --- plugin bootstrap ---
import sys
from pathlib import Path

_lib = Path(__file__).resolve().parent.parent.parent / "__lib"
if str(_lib) not in sys.path:
    sys.path.insert(0, str(_lib))
from _bootstrap import bootstrap
_hooks_dir = bootstrap(__file__)
# --- end bootstrap ---


import json
import os
import re
import sys
import time
from pathlib import Path

from __lib.anti_lazy_policy import (
    check_topic_relevant_investigation,
    is_diagnostic_topic,
)

HOOKS_DIR = Path(__file__).resolve().parent

def _safe_id_str(s: str) -> str:
    """Sanitize string for use in filenames."""
    if not s or not s.strip():
        return "default"
    result = re.sub(r"[!@#<>:\"'/\\|?*]", "_", s)
    result = result.replace(" ", "_")
    return result[:64]

def _get_terminal_id() -> str:
    """Detect terminal ID for state isolation."""
    raw = os.environ.get("WT_SESSION", "")
    if raw:
        return f"console_{raw}"
    return "unknown"

# Delegation signal patterns — PreToolUse-specific (not shared with Stop)
# _is_diagnostic_topic() and check_topic_relevant_investigation() imported from
# __lib.anti_lazy_policy — canonical source shared with lazy_closure_detector.

def _has_user_delegation_signal(user_prompt: str) -> bool:
    """Return True if prompt contains user-delegation signal phrases.

    These phrases indicate the user is asking for something the model
    could obtain via local tools, not genuinely user-private info.
    """
    delegation_signals = [
        r"\bcan\s+you\s+(?:show|share|tell|explain)\s+(?:me\s+)?(?:the\s+)?(?:log|output|file|content|result|error)",
        r"\bcould\s+you\s+(?:show|share|tell|explain)\s+(?:me\s+)?(?:the\s+)?(?:log|output|file|error)",
        r"\bplease\s+(?:share|show|tell)\s+(?:the\s+)?(?:log|output|error)s?\b",
        r"\bshow\s+me\s+the\s+(?:log|output|error|result|content)s?",
        r"\bwhat(?:'s| is)\s+in\s+(?:the\s+)?(?:log|file|output|error)",
        r"\bwhat\s+does\s+(?:the\s+)?(?:log|error|output)\s+say",
        r"\bcheck\s+(?:the\s+)?(?:log|error|output|file)",
        r"\bwhat\s+error\s+(?:do you|does it)\s+show",
    ]
    for pattern in delegation_signals:
        if re.search(pattern, user_prompt, re.IGNORECASE):
            return True
    return False

def run(data: dict) -> dict | None:
    """PreToolUse gate: block ask-user delegation when investigation is insufficient.

    Blocks AskUserQuestion tool calls on diagnostic/investigative topics when
    no prior relevant investigation exists in the ledger.

    Prose delegation (model-generated text) is enforced at Stop phase via
    lazy_closure_detector — PreToolUse has no visibility into model output.

    Returns None (pass) if:
      - Not AskUserQuestion tool
      - Topic is not diagnostic/investigative
      - No user-delegation signal in prompt
      - Ledger contains relevant prior investigation for topic keywords
      - Or fail-open on errors

    Returns block dict if AskUserQuestion is used on a diagnostic topic without
    prior relevant investigation.
    """
    user_prompt = data.get("user_prompt") or data.get("prompt") or ""
    if not user_prompt:
        return None

    tool_name = data.get("tool_name", "")
    if tool_name != "AskUserQuestion":
        return None

    if not is_diagnostic_topic(user_prompt):
        return None

    if not _has_user_delegation_signal(user_prompt):
        return None

    had_relevant_investigation = check_topic_relevant_investigation(user_prompt)
    if had_relevant_investigation:
        return None

    reason = (
        f"ASK-USER-DELEGATION BLOCKED: Your question asks about diagnostic topic "
        f"but no relevant investigation has occurred yet. "
        f"Use Read/Grep/Glob/Bash to investigate the topic first, "
        f"THEN ask the user if you need clarification on genuinely private information. "
        f"Do not delegate back to the user for information that exists in repo files, "
        f"git state, hook logs, or accessible tools."
    )
    return {
        "decision": "block",
        "continue": False,
        "reason": reason,
        "blocking_hook": "PreToolUse_user_delegation_gate.py",
    }

if __name__ == "__main__":
    import sys as _sys

    # Read JSON input from Claude Code
    try:
        input_data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, OSError):
        _sys.exit(0)

    result = run(input_data)
    if result:
        print(json.dumps(result))
        _sys.exit(0)
    else:
        _sys.exit(0)