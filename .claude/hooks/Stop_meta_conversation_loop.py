#!/usr/bin/env python3
"""
Meta-conversation loop detector for Stop hook.

Detects when the model talks about work instead of doing it — a pattern where
consecutive turns contain only analysis/prose with no productive tool calls.

Detection:
  - A "meta" turn: response > 200 chars AND no Edit/Write/Bash tool
  - A "loop": 4+ consecutive meta turns
  - Block on second loop within same session

State: Rolling window of last 6 turns, per-terminal, stored in
  state/stop_meta_conversation/{terminal_id}.json

Author: Stop System Team
Created: 2026-05-12
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

_Hook_Dir = Path(__file__).parent.resolve()
sys.path.insert(0, str(_Hook_Dir))

# State directory
_STATE_SUBDIR = "stop_meta_conversation"
_TURN_WINDOW = 6  # Track last 6 turns
_META_THRESHOLD = 200  # chars
_LOOP_THRESHOLD = 4  # consecutive meta turns to trigger
_TTL_SECONDS = 60 * 60  # 1 hour


def _get_state_dir() -> Path:
    base = Path(os.environ.get("CSF_STATE_DIR", "P:/.claude/state"))
    return base / _STATE_SUBDIR


def _state_path(terminal_id: str) -> Path:
    return _get_state_dir() / f"{terminal_id}.json"


def _load_state(path: Path) -> dict:
    if not path.exists():
        return {"turns": [], "loop_count": 0, "updated_at": 0}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"turns": [], "loop_count": 0, "updated_at": 0}


def _save_state(path: Path, state: dict) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(state, ensure_ascii=True), encoding="utf-8")
    except OSError:
        pass


def _is_productive_turn(tool_events: list[dict]) -> bool:
    """Return True if any Edit/Write/Bash tool was used this turn."""
    for event in tool_events:
        name = event.get("name", "")
        if name in ("Edit", "Write", "MultiEdit", "Bash"):
            return True
    return False


def _classify_turn(response: str, tool_events: list[dict]) -> bool:
    """Return True if this turn is 'meta' (no productive tools, verbose response)."""
    if len(response) < _META_THRESHOLD:
        return False
    return not _is_productive_turn(tool_events)


def run_meta_conversation_loop(data: dict) -> dict | None:
    """
    Detect meta-conversation loop: 4+ consecutive turns of analysis without action.

    Returns None (pass) or a dict with systemMessage/advisory.
    """
    terminal_id = data.get("terminal_id") or os.environ.get("CLAUDE_TERMINAL_ID", "")
    if not terminal_id:
        return None

    response_text = data.get("output_text", "")
    tool_events = data.get("tool_events", [])
    if isinstance(tool_events, dict):
        tool_events = tool_events.get("events", [])

    # Classify current turn
    current_is_meta = _classify_turn(response_text, tool_events)

    # Load rolling window
    path = _state_path(terminal_id)
    state = _load_state(path)

    # Filter stale turns (older than TTL)
    now = int(time.time())
    state["turns"] = [
        t for t in state.get("turns", []) if (now - t.get("ts", 0)) < _TTL_SECONDS
    ]

    # Add current turn to window
    state["turns"].append({"meta": current_is_meta, "ts": now})

    # Keep only last _TURN_WINDOW turns
    state["turns"] = state["turns"][-_TURN_WINDOW:]

    # Count consecutive meta turns
    consecutive = 0
    for t in reversed(state["turns"]):
        if t.get("meta"):
            consecutive += 1
        else:
            break

    state["updated_at"] = now

    # Determine outcome
    if consecutive >= _LOOP_THRESHOLD:
        state["loop_count"] = state.get("loop_count", 0) + 1
        _save_state(path, state)

        if state["loop_count"] >= 2:
            # Second loop — block
            return {
                "decision": "block",
                "systemMessage": (
                    "META-CONVERSATION LOOP: You have spent 4+ consecutive turns "
                    f"discussing the work without taking action (loop #{state['loop_count']}).\n\n"
                    "Rule: If you have a design, start implementing. If you need information, "
                    "use a tool. Do not continue discussing the approach.\n\n"
                    "Take one concrete action now: Edit, Write, or Bash."
                ),
            }
        else:
            # First loop — advisory
            return {
                "decision": "warn",
                "systemMessage": (
                    f"META-CONVERSATION WARNING: You have spent {consecutive} consecutive turns "
                    "discussing the work without taking action.\n\n"
                    "Rule: Productive turns include Edit/Write/Bash tools. "
                    "If you have a design, start implementing. If you need information, use a tool.\n\n"
                    "This is your first warning. A second loop will block."
                ),
            }
    else:
        # Not a loop — reset loop_count if we had a productive turn
        if not current_is_meta:
            state["loop_count"] = 0

    _save_state(path, state)
    return None


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import tempfile

    # Patch state dir to temp dir for testing
    orig_get_state_dir = _get_state_dir

    with tempfile.TemporaryDirectory() as tmpdir:
        def _tmp_state_dir():
            return Path(tmpdir)

        # Swap state dir
        import stop_meta_conversation_loop as mod
        mod._get_state_dir = _tmp_state_dir
        path_fn = mod._state_path

        tid = "test_meta_conv"
        path = Path(tmpdir) / f"{tid}.json"

        def run(data):
            data = dict(data)
            data.setdefault("terminal_id", tid)
            return run_meta_conversation_loop(data)

        # Test 1: No meta loop (short responses)
        result = run({"output_text": "Short.", "tool_events": []})
        assert result is None, f"Expected None for short response, got {result}"

        # Test 2: No meta loop (productive turn)
        result = run({"output_text": "A" * 300, "tool_events": [{"name": "Edit"}]})
        assert result is None, f"Expected None for productive turn, got {result}"

        # Test 3: First loop — advisory
        for _ in range(4):
            run({"output_text": "Discussing the approach and what to do next." * 10, "tool_events": []})
        state = json.loads(path.read_text())
        assert state["loop_count"] == 1, f"Expected loop_count=1, got {state['loop_count']}"
        result = run({"output_text": "More discussion." * 10, "tool_events": []})
        assert result is not None and result["decision"] == "warn", f"Expected warn, got {result}"

        # Test 4: Second loop — block
        for _ in range(4):
            run({"output_text": "More talking." * 10, "tool_events": []})
        result = run({"output_text": "Even more." * 10, "tool_events": []})
        assert result is not None and result["decision"] == "block", f"Expected block, got {result}"

        # Test 5: Productive turn resets loop count
        run({"output_text": "Short", "tool_events": [{"name": "Edit"}]})
        for _ in range(3):
            run({"output_text": "Meta " * 20, "tool_events": []})
        state = json.loads(path.read_text())
        assert state["loop_count"] == 0, f"Expected loop_count=0 after productive, got {state['loop_count']}"

        print("All Stop_meta_conversation_loop.py self-tests passed.", file=sys.stderr)