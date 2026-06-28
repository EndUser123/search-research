#!/usr/bin/env python3
"""
PostToolUse_recent_evidence_tracker.py - Tracks evidence-gathering tool calls
==========================================================================

Silently records the timestamp of the most recent "evidence" tool call
(Read, Bash, Grep, Glob, WebFetch, WebSearch) on a per-terminal basis.
The companion PreToolUse_recent_evidence_gate.py reads this state to block
Edit/Write when no fresh evidence exists.

WHY THIS EXISTS:
  CLAUDE.md requires: "Before emitting any claim starting with 'Root Cause:',
  'Fixed.', 'Verified.', etc., list the tool calls from the last 3 turns
  that justify the claim." This hook enforces that rule STRUCTURALLY at
  Edit/Write time, before the claim is even made, by requiring evidence
  activity in the recent window.

FAILURE MODE CAUGHT:
  "I shipped a 'verified' fix based on file-read, not execution."
  "Two consecutive incidents this month traced to confident verdicts
  without verifying tool calls in recent context."

LIFECYCLE: PostToolUse (silent observation -- never blocks, never exits 2)

Configuration:
  No env var to enable/disable. Tracking is always-on; the BLOCKING gate
  is the PreToolUse companion which is gated by RECENT_EVIDENCE_GATE_ENABLED.

State Management:
  Uses terminal_detection.detect_terminal_id() for session isolation.
  State file: recent_evidence_{terminal_id}.json
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
import sys
import time
from pathlib import Path

# Import terminal_detection for session isolation (consistent with 12+ other hooks)
_marketplace_plugins = _hooks_dir.parent.parent.parent
_skill_guard_path = _marketplace_plugins / "skill-guard" / "src"
if _skill_guard_path.exists():
    sys.path.insert(0, str(_skill_guard_path))
else:
    _skill_guard_path = _marketplace_plugins.parent / "skill-guard" / "src"
    if _skill_guard_path.exists():
        sys.path.insert(0, str(_skill_guard_path))
from __lib.terminal_detection import detect_terminal_id

# Tools that count as "evidence" - they return fresh information from a source
# other than the model's own prior context.
EVIDENCE_TOOLS = frozenset({
    "Read",
    "Bash",
    "Grep",
    "Glob",
    "WebFetch",
    "WebSearch",
    "LS",
    "ListMcpResources",
})

# State directory - mirrors the dependency_verification_gate pattern
HOOK_DIR = Path(__file__).resolve().parent
STATE_DIR = Path(os.environ.get("CSF_STATE_DIR") or str(Path("P:/") / ".claude" / "state")) / "cc-aca-epistemic"
STATE_DIR.mkdir(exist_ok=True)


def get_terminal_id(tool_input: dict) -> str:
    """Resolve terminal ID with the same priority chain as the dependency gate."""
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
    return STATE_DIR / f"recent_evidence_{terminal_id}.json"


def load_state(terminal_id: str) -> dict:
    state_path = get_state_path(terminal_id)
    if not state_path.exists():
        return {"last_evidence_ts": 0.0, "last_tool": ""}
    try:
        with state_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {"last_evidence_ts": 0.0, "last_tool": ""}


def save_state(terminal_id: str, state: dict) -> None:
    state_path = get_state_path(terminal_id)
    try:
        # Atomic write: write to .tmp then replace.
        # Concurrent PostToolUse events for the same terminal would otherwise
        # race on partial JSON writes.
        tmp_path = state_path.with_suffix(".json.tmp")
        with tmp_path.open("w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
        os.replace(tmp_path, state_path)
    except OSError:
        # State is observation-only. Fail silent.
        pass


def parse_stdin() -> dict:
    """Parse stdin JSON; return {} on parse failure (this hook never blocks)."""
    try:
        return json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError, OSError):
        return {}


def main() -> None:
    data = parse_stdin()
    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})
    if not isinstance(tool_input, dict):
        tool_input = {}

    # Self-filters by tool_name. Non-evidence tools are no-ops.
    if tool_name not in EVIDENCE_TOOLS:
        sys.exit(0)

    terminal_id = get_terminal_id(tool_input)
    if not terminal_id:
        # Missing terminal identity disables stateful tracking silently.
        sys.exit(0)

    state = load_state(terminal_id)
    state["last_evidence_ts"] = time.time()
    state["last_tool"] = tool_name
    save_state(terminal_id, state)

    # Silent observation - no stdout, no stderr.
    sys.exit(0)


if __name__ == "__main__":
    main()