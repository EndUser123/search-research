#!/usr/bin/env python3
"""
PreToolUse_recent_evidence_gate.py - Verify-before-claim enforcement v1.0
=========================================================================

Blocks Edit/Write/MultiEdit/NotebookEdit when no evidence-gathering tool
(Read, Bash, Grep, Glob, WebFetch, WebSearch) has fired within the
configured freshness window. The companion PostToolUse hook
(PostToolUse_recent_evidence_tracker.py) records evidence timestamps.

WHY THIS EXISTS:
  CLAUDE.md mandates: "Before any claim starting with 'Root Cause:',
  'Fixed.', 'Verified.', 'This works because:', list the tool calls from
  the last 3 turns that justify the claim." 17 of 25 bad-thinking cases
  this month broke this rule. The companion gate enforces it at edit
  time so the model can't ship a "verified" verdict whose verifying tool
  call is missing from recent context.

FAILURE MODE CAUGHT:
  Pattern: model emits "Root Cause: X" with confident language but no
  Read/Bash/Grep in the last few turns. The fix looks correct in
  isolation but is untested.

NOT CAUGHT (out of scope, by design):
  - Reads that returned stale data (caller's job to interpret)
  - Single-Bash tool call whose exit code was never checked
  - Subagent delegation with unverifiable subagent claims
  - Documentation-only edits (DOC-001 fires for those via separate gate)

LIFECYCLE: PreToolUse (blocking gate -- exits with code 2 to block)

Configuration:
  RECENT_EVIDENCE_GATE_ENABLED=false to disable (default: true -- on by default)
  RECENT_EVIDENCE_WINDOW_SEC=600 to set freshness window (default: 600s = 10min)
  RECENT_EVIDENCE_MODE=bypass to bypass checks (default: block)
  RECENT_EVIDENCE_BYPASS=1 in tool args or env bypasses one call

State Management:
  Uses terminal_detection.detect_terminal_id() for session isolation.
  State file: recent_evidence_{terminal_id}.json (written by companion
  PostToolUse hook).
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
import logging
import os
import sys
import time
from pathlib import Path

# Import terminal_detection for session isolation
_marketplace_plugins = _hooks_dir.parent.parent.parent
_skill_guard_path = _marketplace_plugins / "skill-guard" / "src"
if _skill_guard_path.exists():
    sys.path.insert(0, str(_skill_guard_path))
else:
    _skill_guard_path = _marketplace_plugins.parent / "skill-guard" / "src"
    if _skill_guard_path.exists():
        sys.path.insert(0, str(_skill_guard_path))
from __lib.terminal_detection import detect_terminal_id

# Logging
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

# Configuration
ENABLED = os.environ.get("RECENT_EVIDENCE_GATE_ENABLED", "true").lower() != "false"
WINDOW_SEC = int(os.environ.get("RECENT_EVIDENCE_WINDOW_SEC", "600"))
MODE = os.environ.get("RECENT_EVIDENCE_MODE", "block").lower()
ENV_BYPASS = os.environ.get("RECENT_EVIDENCE_BYPASS", "").lower() in ("1", "true", "yes")

# Tools that modify files (the gate's blocking targets)
WRITE_TOOLS = frozenset({
    "Edit",
    "Write",
    "MultiEdit",
    "NotebookEdit",
})

# State directory - mirrors dependency_verification_gate layout. MUST match
# the companion PostToolUse hook's STATE_DIR so the two halves of the gate
# share the same per-terminal state file.
HOOK_DIR = Path(__file__).resolve().parent
# PostToolUse hook lives at ../posttool/PostToolUse_recent_evidence_tracker.py
# and writes to ../posttool/state/. Read from there so writes and reads hit
# the same JSON file.
SHARED_STATE_DIR = Path(os.environ.get("CSF_STATE_DIR") or str(Path("P:/") / ".claude" / "state")) / "cc-aca-epistemic"
SHARED_STATE_DIR.mkdir(exist_ok=True)


def parse_stdin() -> dict:
    """Parse stdin JSON; return {} on parse failure (this hook never blocks
    when stdin is malformed — we fail open to avoid breaking the harness)."""
    try:
        return json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError, OSError):
        return {}


def get_terminal_id(tool_input: dict) -> str:
    """Resolve terminal ID with the priority chain used by sibling gates."""
    explicit_terminal = str(
        tool_input.get("terminal_id")
        or tool_input.get("terminalId")
        or os.environ.get("CLAUDE_TERMINAL_ID", "")
    ).strip()
    if explicit_terminal:
        return explicit_terminal

    if "detect_terminal_id" in globals():
        return (detect_terminal_id() or "").strip()
    try:
        from __lib.terminal_detection import detect_terminal_id as _dt
        return (_dt() or "").strip()
    except ImportError:
        return ""


def get_state_path(terminal_id: str) -> Path:
    return SHARED_STATE_DIR / f"recent_evidence_{terminal_id}.json"


def load_state(terminal_id: str) -> dict:
    state_path = get_state_path(terminal_id)
    if not state_path.exists():
        return {"last_evidence_ts": 0.0, "last_tool": ""}
    try:
        with state_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {"last_evidence_ts": 0.0, "last_tool": ""}


def evidence_age_seconds(state: dict) -> float | None:
    """Return age of last evidence call in seconds, or None if never recorded."""
    ts = state.get("last_evidence_ts", 0.0)
    if not ts:
        return None
    return time.time() - float(ts)


def is_arg_bypass(tool_input: dict) -> bool:
    """Per-call bypass: 'RECENT_EVIDENCE_BYPASS: 1' in tool args."""
    if not isinstance(tool_input, dict):
        return False
    flag = tool_input.get("RECENT_EVIDENCE_BYPASS")
    return str(flag).lower() in ("1", "true", "yes")


def create_block_payload(tool_name: str, state: dict) -> dict:
    """Compose the block payload with recovery guidance."""
    last_tool = state.get("last_tool") or "(none)"
    age = evidence_age_seconds(state)
    age_str = "no evidence recorded this session" if age is None else (
        f"{age:.0f}s ago ({age / 60:.1f} min)"
    )

    file_path = ""
    if isinstance(state, dict):
        pass
    lines = [
        "Edit blocked: no recent evidence-gathering tool call.",
        f"Tool: {tool_name}",
        f"Last evidence call: {last_tool}, {age_str}",
        f"Window: {WINDOW_SEC}s ({WINDOW_SEC // 60} min)",
        "",
        "Why this exists: CLAUDE.md requires that claims of 'Fixed', 'Verified', "
        "'Root Cause', 'Confirmed working' be backed by a tool call in the recent "
        "context window. 17 of 25 bad-thinking cases this month broke this rule.",
        "",
        "To proceed, do ONE of:",
        f"  1. Read the file you are about to edit (refreshes the window).",
        f"  2. Run a verifying Bash/Grep/Glob on the relevant path or state.",
        f"  3. Pass RECENT_EVIDENCE_BYPASS: 1 in tool args (one-shot bypass).",
        f"  4. Set RECENT_EVIDENCE_MODE=bypass env var (session-wide bypass).",
    ]
    reason = "\n".join(lines)
    return {
        "decision": "block",
        "reason": reason,
        "blocking_hook": "PreToolUse_recent_evidence_gate.py",
        "continue": False,
        "autonomous_recovery": True,
        "next_action": "Read the file you are about to edit, or run a verifying Grep/Bash.",
    }


def evaluate_request(data: dict) -> dict | None:
    """Return block payload if the call should be blocked, else None."""
    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})
    if not isinstance(tool_input, dict):
        tool_input = {}

    # Self-filter: only gate Edit/Write family tools
    if tool_name not in WRITE_TOOLS:
        return None

    # Bypass check (per-call takes precedence over env)
    if is_arg_bypass(tool_input) or ENV_BYPASS:
        return None

    terminal_id = get_terminal_id(tool_input)
    if not terminal_id:
        # Missing terminal identity disables stateful enforcement. Do not
        # invent a fallback identity — that risks cross-terminal bleed.
        logger.warning("Recent-evidence gate skipped: missing terminal_id")
        return None

    state = load_state(terminal_id)
    age = evidence_age_seconds(state)
    if age is None:
        return create_block_payload(tool_name, state)
    if age > WINDOW_SEC:
        return create_block_payload(tool_name, state)

    return None


def run(data: dict) -> dict | None:
    """In-process entry point for PreToolUse router execution."""
    return evaluate_request(data)


def main() -> None:
    if not ENABLED:
        sys.exit(0)
    if MODE == "bypass":
        sys.exit(0)

    data = parse_stdin()
    payload = evaluate_request(data)
    if payload:
        print(payload.get("reason", "Recent evidence required before edit."), file=sys.stderr)
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()