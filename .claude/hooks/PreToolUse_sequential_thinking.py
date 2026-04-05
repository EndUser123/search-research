"""
PreToolUse hook for sequential thinking mode enforcement.

Injects system-message based on iteration count and enforces mode switching:
- Iteration 0: Initial generation mode
- Iteration 1: Critique mode
- Iteration 2: Improvement mode
"""

from __future__ import annotations

# Import state management
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from __lib.sequential_state import update_state

# State directory to find active sessions
STATE_DIR = Path("P:/").resolve() / ".claude" / "state" / "sequential-thinking"

# System message templates for each mode
MODE_MESSAGES = {
    "initial": """You are in INITIAL mode. Generate your best answer to the user's request using clear, step-by-step reasoning.

After completing your answer, the system will automatically transition to critique mode.""",
    "critique": """You are in CRITIQUE mode. Critically analyze the previous answer and identify:

1. **Logical gaps or errors**: What reasoning steps were flawed or missing?
2. **Assumptions**: What unstated assumptions were made? Are they valid?
3. **Alternative perspectives**: What other viewpoints or approaches should be considered?
4. **Weaknesses**: Which parts of the answer are least convincing or need improvement?

Be specific and constructive. Focus on improving the quality of reasoning, not on style.""",
    "improvement": """You are in IMPROVEMENT mode. Based on the critique, provide an improved answer that:

1. **Addresses identified gaps**: Fix the logical errors and missing reasoning
2. **Strengthens weak areas**: Provide better support for uncertain claims
3. **Incorporates alternative perspectives**: Acknowledge complexity where appropriate
4. **Synthesizes insights**: Combine the best of both the original and critique

This is your final answer - make it comprehensive and well-reasoned.""",
}


def pre_tool_use(data: dict) -> dict:
    """PreToolUse hook to inject sequential thinking mode messages.

    Args:
        data: PreToolUse hook data dictionary

    Returns:
        Dictionary with additionalContext if sequential thinking active, empty dict otherwise
    """
    terminal_id = data.get("terminal_id", "")

    # Find active sequential thinking session for this terminal
    active_session = _find_active_session(terminal_id)

    if not active_session:
        return {}  # No active session

    session_id = active_session["session_id"]
    current_iteration = active_session.get("current_iteration", 0)
    current_mode = active_session.get("mode", "initial")

    # Determine mode based on iteration
    if current_iteration == 0:
        new_mode = "initial"
    elif current_iteration == 1:
        new_mode = "critique"
    elif current_iteration == 2:
        new_mode = "improvement"
    else:
        # Beyond max iterations - don't inject
        return {}

    # Update mode if changed
    if new_mode != current_mode:
        update_state(uuid.UUID(session_id), {"mode": new_mode}, terminal_id)

    # Get system message for current mode
    mode_message = MODE_MESSAGES.get(new_mode, "")

    if not mode_message:
        return {}

    # Inject context with mode-specific instructions
    return {
        "additionalContext": (
            f"<sequential_thinking_mode>\n"
            f"Session: {session_id}\n"
            f"Iteration: {current_iteration} of 2\n"
            f"Mode: {new_mode.upper()}\n"
            f"</sequential_thinking_mode>\n\n"
            f"{mode_message}\n"
        ),
        "tokens": 200,  # Estimated token count for injection
    }


_SESSION_TTL_SECONDS = 7200  # 2 hours — prevents stale sessions from poisoning context


def _find_active_session(terminal_id: str) -> dict | None:
    """Find the active sequential thinking session for this terminal.

    Args:
        terminal_id: Terminal identifier for multi-terminal isolation

    Returns:
        State dict if active session found, None otherwise
    """
    import json
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

    result = pre_tool_use(data)

    if result and result.get("additionalContext"):
        print(result["additionalContext"])

    sys.exit(0)
