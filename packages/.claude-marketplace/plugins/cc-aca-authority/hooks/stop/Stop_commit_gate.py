#!/usr/bin/env python3
"""Stop gate: Block git commit/push without explicit /approve commit."""
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


import datetime
import json
import os
import re
import sys
import time
from pathlib import Path

from __lib.response_intent import IntentClass, is_meta_or_quoted_context, _strip_code_blocks

HOOKS_DIR = Path(__file__).resolve().parent
ARTIFACTS_BASE = Path(os.environ.get("CLAUDE_ARTIFACTS_DIR", str(HOOKS_DIR.parent / ".artifacts")))

# Git operations that require approval
_GIT_ACTION_PATTERNS = [
    re.compile(r"\b(?:git\s+(?:commit|push|rebase|merge|reset|restore))\b"),
    re.compile(r"\b(?:commit\s+(?:-m|--message))"),
]

def _terminal_id() -> str:
    tid = os.environ.get("CLAUDE_TERMINAL_ID", "").strip()
    if tid:
        return tid
    tid = os.environ.get("WT_SESSION", "").strip()
    return tid if tid else "default"

def _approval_file() -> Path:
    return ARTIFACTS_BASE / _terminal_id() / "approval.json"

def _check_commit_approval() -> tuple[bool, dict | None]:
    """Check if commit approval exists."""

    path = _approval_file()
    if not path.exists():
        return False, None
    try:
        data = json.loads(path.read_text())
        ttl_hours = data.get("ttl_hours", 24)
        ts = data.get("ts", 0)
        if ts and time.time() - ts > ttl_hours * 3600:
            try:
                path.unlink()
            except OSError:
                pass
            return False, None
        if data.get("approved") is not True:
            return False, None
        return True, data
    except (json.JSONDecodeError, OSError):
        return False, None

def run(data: dict) -> dict | None:
    response = data.get("response", "")
    if not response:
        return None

    # Gate debug/meta discussion — don't block diagnostic responses about triggers
    if is_meta_or_quoted_context(response):
        return None

    # Strip code blocks, inline code, and markdown tables so conversational
    # mentions (e.g. `git checkout HEAD`, table descriptions) don't trigger
    # the gate. Table content is always descriptive, never imperative.
    stripped = _strip_code_blocks(response)
    stripped = re.sub(r"`[^`]*`", " ", stripped)
    stripped = re.sub(r"^\|.+\|$", " ", stripped, flags=re.MULTILINE)

    # Check if any git action pattern matches the stripped text.
    # Hoist first match to avoid double iteration and to capture diagnostic context.
    first_match = None
    first_pattern = None
    for p in _GIT_ACTION_PATTERNS:
        m = p.search(stripped)
        if m:
            first_match = m
            first_pattern = p
            break

    if first_match is None:
        return None

    # ── Diagnostic capture ─────────────────────────────────────────────────────
    # Log matched text ±40 chars for post-hoc diagnosis of false positives.
    # Fires on every match regardless of whether the turn is later allowed/blocked.
    # Output goes to hook_runner_stderr.jsonl; diagnostics never alter decisions.
    try:
        start = max(0, first_match.start() - 40)
        end = min(len(stripped), first_match.end() + 40)
        snippet = stripped[start:end]
        _log_path = ARTIFACTS_BASE / _terminal_id() / "logs" / "diagnostics" / "hook_runner_stderr.jsonl"
        _log_path.parent.mkdir(parents=True, exist_ok=True)
        with _log_path.open("a", encoding="utf-8") as _fh:
            _fh.write(json.dumps({
                "ts": datetime.datetime.now().isoformat(),
                "hook": "Stop_commit_gate",
                "matched_pattern": first_pattern.pattern,
                "matched_substring": first_match.group(),
                "context": snippet,
            }) + "\n")
    except Exception:
        # Never let diagnostics alter the decision
        pass
    # ── End diagnostic capture ───────────────────────────────────────────────

    # Verify this is a real commitment, not just discussing the phrase
    intent = is_meta_or_quoted_context(response)
    if intent == IntentClass.GATE_DEBUG_META:
        return None

    approved, state = _check_commit_approval()
    if not approved:
        return {
            "decision": "block",
            "reason": (
                "GIT OPERATION WITHOUT APPROVAL\n\n"
                "Detected git commit/push without /approve commit.\n"
                "Required: Add `/approve <skill> commit` to your message.\n"
            ),
        }

    # Phase must be 'commit' or 'deploy'
    phase = (state or {}).get("phase", "")
    if phase not in ("commit", "deploy"):
        return {
            "decision": "block",
            "reason": (
                f"PHASE MISMATCH: Approval is for phase '{phase}', not 'commit'.\n"
                "Required: Add `/approve <skill> commit` to your message.\n"
            ),
        }

    return None

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