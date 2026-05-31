from __future__ import annotations
# --- plugin bootstrap ---
import sys
from pathlib import Path
_l = Path(__file__).resolve().parent.parent.parent / "__lib"
if str(_l) not in sys.path: sys.path.insert(0, str(_l))
from _bootstrap import bootstrap; _hooks_dir = bootstrap(__file__)
# --- end bootstrap ---

#!/usr/bin/env python3
"""Implementation Default Gate (PreToolUse).

PURPOSE: Block Edit/Write by default unless explicit implementation intent is present.
PROBLEM ADDRESSED: LLM defaults to implementing even when user only asked for investigation,
documentation, or findings. The blanket rule is: "do not implement unless explicitly asked."

ENFORCEMENT MECHANISM (three-signal intent detection):
- Signal 1: turn_mode classifier (control/plan -> allow, exploration/analysis/meta -> block)
- Signal 2: Structural imperative (verb-initial, <=25 words, no '?' -> allow)
- Signal 3: Inverted default (allow unless clear non-implementation signal)
- State: session+terminal-scoped JSON in CSF_STATE_DIR, per-turn reset

This is the FLIPPED default: gather-and-report is assumed unless intent detection
classifies the message as implementation-directed. "Document the approach" -> no Edit/Write.
"Implement the fix" -> Edit/Write allowed.
"""


import json
import os
import re
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Add hooks dir to path for shared utilities
_HOOKS_DIR = Path(__file__).resolve().parent
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

# Turn mode classifier for Signal 1 intent detection (global hooks __lib__)
_global_lib = _hooks_dir / "__lib"
if str(_global_lib) not in sys.path:
    sys.path.insert(0, str(_global_lib))
try:
    from turn_mode import classify
    _TURN_MODE_AVAILABLE = True
except ImportError:
    _TURN_MODE_AVAILABLE = False

# State management
try:
    from __lib.commitment_tracker import load_state, save_state
except Exception:
    load_state = None
    save_state = None

# === CONFIGURATION ===

_STATE_KEY = "implementation_default_gate"
_ALLOWED_TOOLS = {"Edit", "Write", "MultiEdit"}


# --- Signal 2: Structural imperative detection ---
# Words that typically do NOT start imperative commands in English.
# Any verb-like word NOT in this set is treated as structurally imperative.
_NON_IMPERATIVE_STARTS = frozenset({
    "a", "an", "the",
    "i", "you", "he", "she", "it", "we", "they",
    "me", "him", "us", "them",
    "my", "your", "his", "her", "its", "our", "their",
    "is", "are", "was", "were", "be", "been", "being", "am",
    "do", "does", "did", "have", "has", "had", "having",
    "will", "would", "shall", "should", "may", "might", "must", "can", "could",
    "what", "who", "where", "when", "why", "how", "which",
    "this", "that", "these", "those",
    "and", "but", "or", "nor", "so", "yet", "for",
    "in", "on", "at", "to", "of", "by", "from", "with", "about",
    "between", "through", "during", "before", "after", "above", "below",
    "under", "over", "into", "onto", "upon", "within", "without",
    "if", "unless", "because", "since", "although", "while", "whereas",
    "whether", "though", "once", "until",
    "no", "not", "never", "neither", "each", "every", "all", "some",
    "any", "both", "few", "many", "much", "more", "most", "other",
    "such", "than",
    "too", "very", "just", "also", "even", "still", "already",
    "perhaps", "maybe", "probably", "definitely", "certainly",
    "actually", "basically", "essentially", "generally", "usually",
    "however", "therefore", "moreover", "furthermore", "nevertheless",
    "otherwise", "meanwhile", "instead", "anyway",
    "thanks", "thank", "sorry", "please", "ok", "okay",
})

# --- Signal 3: Clear non-implementation markers ---
_QUESTION_MARK_RE = re.compile(r'\?')
_EXPLORATION_PHRASE_RE = re.compile(
    r'\b(?:should\s+we|what\s+if|'
    r'alternatives?\s+to|trade-?offs?|pros\s+and\s+cons|'
    r'compare\s+.*?(?:vs|versus|against))\b',
    re.IGNORECASE,
)
_STATUS_REPORT_RE = re.compile(
    r'^(?:\[STATUS\]|\[CHANGES\]|\[RESULTS\]|\[NEXT\]|status:)',
    re.IGNORECASE,
)


def _detect_implementation_intent(user_message: str) -> tuple[bool, str]:
    """Three-signal implementation intent detection.

    Signal 1: turn_mode classifier (control/plan -> allow, exploration/analysis/meta -> block)
    Signal 2: Structural imperative (verb-initial, short, no ? -> allow)
    Signal 3: Inverted default (allow unless clear non-implementation signal)

    Returns (allowed, reason_category) for telemetry.
    """
    if not user_message or not user_message.strip():
        return (True, "empty_message_fail_open")

    stripped = user_message.strip()
    lower = stripped.lower()
    words = lower.split()

    # Signal 1: turn_mode classifier
    if _TURN_MODE_AVAILABLE:
        try:
            mode = _classify_turn_mode({"user_prompt": stripped, "response": ""})
            if mode in ("control", "plan"):
                return (True, f"signal1:{mode}")
            if mode in ("exploration", "analysis", "meta", "final-answer"):
                return (False, f"signal1:{mode}")
        except Exception:
            pass

    # Signal 2: Structural imperative (verb-initial, short, no question mark)
    if words and len(words) <= 25 and "?" not in stripped:
        first = words[0].rstrip(".,!?;:")
        if first and first not in _NON_IMPERATIVE_STARTS:
            return (True, "signal2:imperative")

    # Signal 3: Inverted default -- allow unless clearly non-implementation
    if _QUESTION_MARK_RE.search(stripped):
        return (False, "signal3:question")
    if _EXPLORATION_PHRASE_RE.search(lower):
        return (False, "signal3:exploration")
    if _STATUS_REPORT_RE.match(lower):
        return (False, "signal3:status_report")

    return (True, "signal3:default_allow")


def _get_state_path() -> Path | None:
    """Get path for session state file."""
    if load_state is None or save_state is None:
        return None
    state_dir = Path(os.environ.get("CSF_STATE_DIR", str(_HOOKS_DIR / "state")))
    return state_dir / "implementation_default_gate.json"


def _set_intent_allowed(terminal_id: str, session_id: str, allowed: bool, turn_number: int) -> None:
    """Store implementation intent state for this session+terminal+turn.

    Per-turn reset: if turn_number differs from stored turn_number, the per-turn
    implementation_allowed flag is cleared and re-evaluated for the current turn.
    This prevents a single trigger word from permanently disabling the
    gather-and-report default for the remainder of the session.
    """
    if load_state is None or save_state is None:
        return
    state_path = _get_state_path()
    if state_path is None:
        return
    state = load_state(str(state_path)) if state_path.exists() else {}
    key = f"{session_id}:{terminal_id}"
    if key not in state:
        state[key] = {}
    state[key]["implementation_allowed"] = allowed
    state[key]["turn_number"] = turn_number
    state[key]["updated_at"] = str(Path(__file__).stat().st_mtime)
    save_state(str(state_path), state)


def _is_intent_allowed(terminal_id: str, session_id: str, turn_number: int) -> bool | None:
    """Retrieve implementation intent state. Returns None if no state exists or turn_number mismatched.

    Per-turn reset: if stored turn_number differs from current turn_number,
    clears implementation_allowed and returns None so the current turn's
    trigger words are re-evaluated fresh.
    """
    if load_state is None:
        return None
    state_path = _get_state_path()
    if state_path is None or not state_path.exists():
        return None
    state = load_state(str(state_path))
    key = f"{session_id}:{terminal_id}"
    entry = state.get(key, {})

    # Per-turn reset: mismatched turn number means the stored per-turn flag is stale
    if entry.get("turn_number") != turn_number:
        return None

    return entry.get("implementation_allowed", None)


def _clear_intent_state(terminal_id: str, session_id: str, turn_number: int) -> None:
    """Clear implementation intent state for this session+terminal+turn."""
    if load_state is None or save_state is None:
        return
    state_path = _get_state_path()
    if state_path is None or not state_path.exists():
        return
    state = load_state(str(state_path))
    key = f"{session_id}:{terminal_id}"
    state.pop(key, None)
    save_state(str(state_path), state)


def _get_last_user_message(input_data: dict[str, Any]) -> str:
    """Extract last user message from hook input data."""
    messages = input_data.get("messages", [])
    for msg in reversed(messages):
        if msg.get("role") == "user":
            content = msg.get("content", "")
            if isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        return part.get("text", "")
            elif isinstance(content, str):
                return content
    return input_data.get("last_prompt", "")


# === MAIN ===

# Log sink for block telemetry — appended to pretooluse_blocks.jsonl
# so hook_observability_rollup.py can ingest it.
_BLOCK_LOG = _HOOKS_DIR / "logs" / "diagnostics" / "pretooluse_blocks.jsonl"


def _log_block_event(
    session_id: str,
    terminal_id: str,
    tool_name: str,
    reason_category: str,
    latency_ms: float,
) -> None:
    """Append a structured block event to pretooluse_blocks.jsonl."""
    import datetime

    entry = {
        "ts": datetime.datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "event_kind": "block:implementation_default_gate",
        "source_hook": "PreToolUse_implementation_default_gate.py",
        "blocking_hook": "PreToolUse_implementation_default_gate.py",
        "hook_phase": "PreToolUse",
        "session_id": session_id,
        "terminal_id": terminal_id,
        "tool_name": tool_name,
        "reason_category": reason_category,
        "latency_ms": round(latency_ms, 2),
        "decision": "block",
    }
    try:
        _BLOCK_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(_BLOCK_LOG, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry) + "\n")
    except Exception:
        pass  # never fail the gate due to logging errors


def main() -> None:
    start_monotonic = time.monotonic()

    stdin_content = sys.stdin.read()
    if not stdin_content.strip():
        print("implementation_default_gate: empty stdin, allowing", file=sys.stderr)
        sys.exit(0)

    try:
        input_data = json.loads(stdin_content)
    except json.JSONDecodeError:
        print("implementation_default_gate: invalid JSON, allowing", file=sys.stderr)
        sys.exit(0)

    tool_name = input_data.get("tool_name", "")
    terminal_id = str(
        input_data.get("terminal_id")
        or input_data.get("terminalId")
        or os.environ.get("CLAUDE_TERMINAL_ID", "")
    ).strip()
    session_id = input_data.get("session_id", "default")

    # Only check mutation tools
    if tool_name not in _ALLOWED_TOOLS:
        sys.exit(0)

    # Derive turn_number from message count in the hook input payload.
    # messages array grows by one per user turn; using its length as a
    # monotonic turn counter ensures per-turn state resets when the user
    # sends a new message.
    messages = input_data.get("messages", [])
    turn_number = len(messages)

    user_message = _get_last_user_message(input_data)

    # Check if implementation intent was already established this turn
    intent_allowed = _is_intent_allowed(terminal_id, session_id, turn_number)
    if intent_allowed is True:
        sys.exit(0)  # Already confirmed

    # Three-signal intent detection
    allowed, reason_category = _detect_implementation_intent(user_message)
    if allowed:
        _set_intent_allowed(terminal_id, session_id, True, turn_number)
        sys.exit(0)  # Allow - intent detected

    # Intent not detected -- block
    latency_ms = (time.monotonic() - start_monotonic) * 1000

    _log_block_event(session_id, terminal_id, tool_name, reason_category, latency_ms)

    message = (
        "\n⛔ IMPLEMENTATION BLOCKED: User intent does not indicate implementation.\n\n"
        f"Detection signal: {reason_category}\n"
        "Your message was classified as non-implementation (question, exploration, or analysis).\n\n"
        "If you want implementation, use a direct imperative, e.g.:\n"
        '  • \"fix the bug\" → allows Edit/Write\n'
        '  • \"cleanup the file\" → allows Edit/Write\n'
        '  • \"refactor the handler\" → allows Edit/Write\n\n'
        "This gate enforces: do not implement unless explicitly asked."
    )

    print(json.dumps({"decision": "block", "reason": message, "reason_category": reason_category}))
    print(message, file=sys.stderr)
    sys.exit(2)  # Block


if __name__ == "__main__":
    main()


# ---------------------------------------------------------------------------
# Implementation notes (self-check, not executed)
# ---------------------------------------------------------------------------
# Turn number derivation:
#   turn_number = len(input_data.get("messages", []))
#   Each user message appends one entry to the messages array, so the array
#   length is a monotonic per-session turn counter already available in the
#   hook input payload. A mismatched stored turn_number triggers per-turn reset.
#
# reason_category values:
#   "trigger:<label>" — first trigger word matched (implement, build, create, …)
#   "no_trigger_found" — no trigger word in user message
#   These values are written to pretooluse_blocks.jsonl and ingested by
#   hook_observability_rollup.py's ingest_pretooluse_blocks() as the
#   reason_category column, replacing the hard-coded "other" fallback.
#
# Latency logging:
#   time.monotonic() captured at main() entry; latency_ms computed before
#   any sys.exit(2). _log_block_event() appends a JSON line to
#   logs/diagnostics/pretooluse_blocks.jsonl (the canonical block stream),
#   matching the format expected by ingest_pretooluse_blocks().
#   hook_observability_rollup.py will pick up these events on next run.
#   latency_ms is also included in the JSON stdout payload for the block response.
#
# Per-turn reset:
#   _is_intent_allowed(key, turn_number) returns None when stored
#   turn_number differs from current turn_number, causing the gate to
#   re-evaluate trigger words for the current turn instead of using a
#   stale "session-wide" implementation_allowed flag.
#   _set_intent_allowed() stores turn_number alongside implementation_allowed.
# ---------------------------------------------------------------------------
