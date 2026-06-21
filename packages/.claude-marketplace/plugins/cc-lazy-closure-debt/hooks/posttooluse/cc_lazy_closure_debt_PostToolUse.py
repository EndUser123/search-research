"""cc-lazy-closure-debt PostToolUse hook — closes the deferral loop.

When the model formalizes a deferral via TaskCreate(subject="Deferral: <phrase>"),
this hook appends a tombstone for that phrase's fingerprint so the deferral
stops re-surfacing on every UserPromptSubmit. Without it, the JSONL line lives
for 24h and the UserPromptSubmit directive re-fires each turn, spawning a new
duplicate task per turn (the #828/#840 duplication).

Never blocks. PostToolUse output is advisory only; this hook always returns {}.
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

from debt_store import resolve_deferral_by_phrase, _safe_id  # noqa: E402

_SUBJECT_PREFIX = "Deferral: "


def _resolve_terminal_id(data: dict) -> str:
    """Mirror the UserPromptSubmit hook's terminal resolution exactly so the
    tombstone lands in the same per-terminal JSONL the deferral was written to.
    """
    session_obj = data.get("session") or {}
    if isinstance(session_obj, dict):
        tid = session_obj.get("terminal_id") or session_obj.get("terminalId")
        if tid:
            return str(tid)
    tid = data.get("terminal_id") or data.get("terminalId")
    if tid:
        return str(tid)
    return os.environ.get("CLAUDE_TERMINAL_ID", "default")


def run(data: dict) -> dict:
    """Resolve the deferral if this is a Deferral: TaskCreate; otherwise no-op."""
    tool_name = data.get("tool_name") or data.get("toolName") or ""
    if tool_name != "TaskCreate":
        return {}

    tool_input = data.get("tool_input") or data.get("toolInput") or {}
    if not isinstance(tool_input, dict):
        return {}

    subject = str(tool_input.get("subject", "") or "")
    if not subject.startswith(_SUBJECT_PREFIX):
        return {}

    phrase = subject[len(_SUBJECT_PREFIX):].strip()
    if not phrase:
        return {}

    terminal_id = _safe_id(_resolve_terminal_id(data))
    try:
        resolve_deferral_by_phrase(terminal_id, phrase)
    except OSError:
        # Fail open — never let a state-write failure surface as a hook error.
        pass
    return {}


if __name__ == "__main__":
    raw = sys.stdin.read()
    try:
        data = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        data = {}
    run(data)
    print(json.dumps({}))
    sys.exit(0)
