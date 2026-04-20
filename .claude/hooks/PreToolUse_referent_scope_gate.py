#!/usr/bin/env python3
"""
Referent Scope Gate - PreToolUse hook

Blocks Bash/Grep/Glob tool calls that show zero overlap with anchor terms
extracted by UserPromptSubmit_referent_anchor.py from the user's message.

Problem: LLM investigates wrong entities when user message listed specific
items in a table/list with referential language ("those", "them").

State file: .claude/state/referent_anchors_{terminal_id}.json
Written by: UserPromptSubmit_referent_anchor.py
Cleared by: Stop_referent_coverage (in Stop.py)

Three-state contract:
1. State file with anchor_terms -> gate active, enforce overlap
2. State file with status: "no_anchors" -> allow
3. No state file -> UPS never ran, allow with diagnostic
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

STATE_DIR = Path(__file__).resolve().parent / "state"
GATED_TOOLS = {"Bash", "Grep", "Glob"}
EXEMPT_TOOLS_FOR_EXPLORATION = {"Read", "Glob"}  # First Read/Glob allowed without overlap


def _get_terminal_id(data: dict) -> str:
    tid = (
        data.get("terminal_id")
        or data.get("terminalId")
        or os.environ.get("CLAUDE_TERMINAL_ID")
    )
    if tid:
        return str(tid)
    try:
        lib_path = str(Path(__file__).resolve().parent / "__lib")
        if lib_path not in sys.path:
            sys.path.insert(0, lib_path)
        from terminal_detection import detect_terminal_id
        return detect_terminal_id()
    except Exception:
        return "unknown"


def _read_state(terminal_id: str) -> dict | None:
    state_file = STATE_DIR / f"referent_anchors_{terminal_id}.json"
    if not state_file.exists():
        return None
    try:
        return json.loads(state_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _write_state(terminal_id: str, state: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    state_file = STATE_DIR / f"referent_anchors_{terminal_id}.json"
    state_file.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")


def _get_tool_text(data: dict) -> str:
    """Extract searchable text from tool input."""
    tool_input = data.get("tool_input", data.get("toolInput", {}))
    parts = []
    for key in ("command", "pattern", "query", "path", "file_path"):
        val = tool_input.get(key, "")
        if val:
            parts.append(str(val))
    return " ".join(parts).lower()


def _check_overlap(tool_text: str, anchor_terms: list[str]) -> list[str]:
    """Return list of anchor terms found in tool text.

    Matches on full term substring first, then falls back to bigram
    matching (any pair of consecutive words from the term).
    """
    matched = []
    for term in anchor_terms:
        term_lower = term.lower()
        if term_lower in tool_text:
            matched.append(term)
            continue
        # Bigram fallback: check consecutive word pairs
        words = term_lower.split()
        for i in range(len(words) - 1):
            bigram = f"{words[i]} {words[i + 1]}"
            if bigram in tool_text:
                matched.append(term)
                break
    return matched


def _build_block_message(anchor_terms: list[str], tool_text: str) -> str:
    items = "\n".join(f"  - {t}" for t in anchor_terms[:10])
    target_preview = tool_text[:120] + ("..." if len(tool_text) > 120 else "")
    return (
        f"REFERENT SCOPE MISMATCH\n\n"
        f"User message listed these items for investigation:\n{items}\n\n"
        f"Your tool call targets: {target_preview}\n\n"
        f"Zero overlap with listed items. "
        f"Re-read the user's message and investigate the listed entities."
    )


def run(data: dict) -> dict:
    """Main hook entry point. Returns {'decision': 'allow'|'block', 'reason': str}."""
    tool_name = data.get("tool_name", "")

    terminal_id = _get_terminal_id(data)
    state = _read_state(terminal_id)

    # State 3: No state file -> UPS never ran
    if state is None:
        return {"decision": "allow", "reason": "referent_scope: no state file (UPS not run)"}

    # State 2: No anchors detected
    if state.get("status") == "no_anchors":
        return {"decision": "allow", "reason": "referent_scope: no anchors in user message"}

    # Bypass: expansion language in user message
    if state.get("bypass_scope", False):
        return {"decision": "allow", "reason": "referent_scope: bypass_scope set"}

    anchor_terms = state.get("anchor_terms", [])
    if not anchor_terms:
        return {"decision": "allow", "reason": "referent_scope: empty anchor terms"}

    # Only gate investigation tools
    if tool_name not in GATED_TOOLS:
        # Allow non-gated tools unconditionally
        return {"decision": "allow", "reason": f"referent_scope: {tool_name} not gated"}

    tool_text = _get_tool_text(data)
    matched = _check_overlap(tool_text, anchor_terms)

    if matched:
        return {
            "decision": "allow",
            "reason": f"referent_scope: overlap with {matched[:3]}",
        }

    # Zero overlap -> block
    msg = _build_block_message(anchor_terms, tool_text)
    return {"decision": "block", "reason": msg, "blocking_hook": "PreToolUse_referent_scope_gate.py"}


def main() -> None:
    raw = sys.stdin.read().strip()
    if not raw:
        print(json.dumps({"decision": "allow", "reason": "referent_scope: empty input"}))
        sys.exit(0)

    try:
        data = json.loads(raw.lstrip("\ufeff"))
    except json.JSONDecodeError:
        print(json.dumps({"decision": "allow", "reason": "referent_scope: parse error"}))
        sys.exit(0)

    result = run(data)
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(2 if result.get("decision") == "block" else 0)


if __name__ == "__main__":
    main()
