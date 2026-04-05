"""
Stop hook for sequential thinking iteration management.

Reads response output, saves to state file, increments iteration counter,
and manages loop completion or continuation.

Loop protocol: return {"allow": False, "reason": "..."} to force continuation.
The reason text is injected into Claude's context as the next iteration prompt.

OUTPUT FORMAT NOTE:
    This hook runs as a standalone command (not through Stop_router.py).
    The output format uses {"allow": bool, "reason": str} which is accepted
    by Claude Code's Stop hook interface. The Stop_router.py normalizes
    this to {"decision": "block"/"allow"} for hooks in its ACTIVE_RUNTIME_HOOKS,
    but this hook operates independently.

    See PROTOCOL.md for the canonical Stop hook output specification.
"""

from __future__ import annotations

import json

# Import state management
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from __lib.sequential_state import (
    add_intermediate_answer,
    set_final_answer,
    should_continue,
    update_state,
)

# State directory
STATE_DIR = Path("P:/").resolve() / ".claude" / "state" / "sequential-thinking"

# Import tag emission for standardized [SEQ] tags (runtime emission pattern)
sys.path.insert(0, str(Path(__file__).parent))
from UserPromptSubmit_modules.tag_emission import emit_tag  # noqa: E402

_MODE_INSTRUCTIONS = {
    "critique": (
        "Critically analyze your previous answer and identify:\n"
        "1. Logical gaps or errors in the reasoning\n"
        "2. Unstated assumptions\n"
        "3. Alternative perspectives not considered\n"
        "4. Weakest parts of the argument\n"
        "Be specific and constructive."
    ),
    "improvement": (
        "Based on the critique, provide an improved final answer that:\n"
        "1. Fixes the logical errors identified\n"
        "2. Strengthens weak areas with better support\n"
        "3. Acknowledges complexity where appropriate\n"
        "This is your final answer — make it comprehensive and well-reasoned."
    ),
}


def stop(data: dict) -> dict:
    """Stop hook to manage sequential thinking iteration loop.

    Args:
        data: Stop hook data dictionary

    Returns:
        {"allow": False, "reason": "..."} to force next iteration, or {"allow": True} to stop.
    """
    terminal_id = data.get("terminal_id", "")
    response_output = data.get("response_output", "")

    # Find active sequential thinking session for this terminal
    active_session = _find_active_session(terminal_id)

    if not active_session:
        return {"allow": True}  # No active session, allow stop

    session_id = uuid.UUID(active_session["session_id"])
    current_iteration = active_session.get("current_iteration", 0)

    # Save current output as intermediate answer
    if response_output:
        add_intermediate_answer(session_id, response_output, terminal_id)

    # Check if should continue
    if should_continue(session_id, terminal_id=terminal_id):
        # Increment iteration and continue
        next_iteration = current_iteration + 1
        update_state(session_id, {"current_iteration": next_iteration}, terminal_id)

        # Determine next mode and instructions
        mode_key = "critique" if next_iteration == 1 else "improvement"
        mode_instructions = _MODE_INSTRUCTIONS[mode_key]

        # Block stop to force next iteration — reason is injected into Claude's context
        # Runtime emission pattern: call emit_tag() at call site (not module-level variable)
        return {
            "allow": False,
            "reason": (
                f"{emit_tag('SEQ')}\n"
                f"<sequential_thinking_continuation>\n"
                f"Iteration {next_iteration} of 2 — {mode_key.upper()} MODE\n"
                f"</sequential_thinking_continuation>\n\n"
                f"{mode_instructions}"
            ),
        }
    else:
        # Session complete - save final answer and deactivate
        set_final_answer(session_id, response_output, terminal_id)

        return {"allow": True}


_SESSION_TTL_SECONDS = 7200  # 2 hours — prevents loops from orphaned state files


def _find_active_session(terminal_id: str) -> dict | None:
    """Find the active sequential thinking session for this terminal.

    Also cleans up stale state files (older than TTL) to prevent disk bloat.

    Args:
        terminal_id: Terminal identifier for multi-terminal isolation

    Returns:
        State dict if active session found, None otherwise
    """
    import time

    if not STATE_DIR.exists():
        return None

    now = time.time()

    # List all state files for this terminal
    pattern = f"*_{terminal_id}.json" if terminal_id else "*.json"
    state_files = list(STATE_DIR.glob(pattern))

    # Find active session
    for state_file in state_files:
        try:
            # TTL check: skip sessions whose state file hasn't been touched in 2 hours
            age_seconds = now - state_file.stat().st_mtime
            if age_seconds > _SESSION_TTL_SECONDS:
                # Clean up stale file instead of just skipping
                try:
                    state_file.unlink()
                except OSError:
                    pass  # Ignore cleanup errors
                continue

            state = json.loads(state_file.read_text(encoding="utf-8"))
            if state.get("active", False):
                return state
        except (OSError, json.JSONDecodeError):
            continue

    return None


if __name__ == "__main__":
    import json
    import sys

    try:
        data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, OSError):
        sys.exit(0)

    result = stop(data) or {}

    output = {"allow": result.get("allow", True)}
    if not result.get("allow") and result.get("reason"):
        output["reason"] = result["reason"]
    print(json.dumps(output))
    sys.exit(0)
