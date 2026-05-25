"""
PreToolUse hook for sequential thinking mode enforcement.

Injects system-message based on iteration count and enforces mode switching:
- Iteration 0: Initial generation mode
- Iteration 1: Critique mode
- Iteration 2: Improvement mode
"""

from __future__ import annotations


# --- plugin bootstrap ---
import sys as _s; from pathlib import Path as _P
_l = _P(__file__).resolve().parent.parent.parent / "__lib"
if str(_l) not in _s.path: _s.path.insert(0, str(_l))
from _bootstrap import bootstrap; _hooks_dir = bootstrap(__file__)
# --- end bootstrap ---


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
    # CHANGE-002: Multi-hypothesis tracking modes
    "multi_hypothesis": """You are in MULTI-HYPOTHESIS mode. Generate 2-3 competing explanations for the problem.

For each hypothesis:
1. State the explanation clearly
2. Identify what evidence would support it
3. Identify what evidence would refute it

Maintain all hypotheses as equally plausible until evidence discriminates between them.""",
    "hypothesis_critique": """You are in HYPOTHESIS CRITIQUE mode. Evaluate each competing hypothesis against the evidence.

For each hypothesis:
1. Compare predictions to actual observations
2. Identify inconsistencies or contradictions
3. Rank hypotheses by explanatory power

Do NOT eliminate a hypothesis until you have strong evidence against it.""",
    "hypothesis_resolution": """You are in HYPOTHESIS RESOLUTION mode. Synthesize the best explanation from competing hypotheses.

1. Select the hypothesis best supported by evidence
2. Explain why other hypotheses were weaker
3. Identify what additional evidence would strengthen confidence

This is your final answer - make it comprehensive and well-reasoned.""",
    # CHANGE-005: Self-investigation mode for RCA/diagnostic sessions
    # Triggers when user invokes /rca or similar diagnostic skill
    "self_investigation": """You are in SELF-INVESTIGATION mode. Before producing any output:

MANDATORY PRE-FLIGHT CHECKLIST:
1. Git history: Run `git log --oneline -5 -- <path>` for every file involved in the symptom
2. File existence: Check plausible alternative locations when a file is missing (e.g., .bak, old/, sibling directories)
3. State artifacts: Check session state, telemetry logs, and hook events relevant to the symptom
4. MCP/tools: Use available MCP servers (Serena, Context7, CKS/CHS search) before asking the user

TRACE IT YOURSELF — DO NOT ASK THE USER TO CHECK, PASTE, OR DESCRIBE.

Only after verifying all four checks above may you proceed to diagnosis.
If any check reveals something missing, trace its current location before concluding.""",
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

    # CHANGE-002: Check hypothesis_mode flag first
    is_hypothesis_mode = active_session.get("hypothesis_mode", False)

    if is_hypothesis_mode:
        # Hypothesis mode uses iteration-based mode mapping
        # NOTE: Use current_iteration (pre-increment) to match existing investigation mode pattern
        # Investigation mode at StopHook uses next_iteration (post-increment), so we use current_iteration here
        phase_order = ["multi_hypothesis", "hypothesis_critique", "hypothesis_resolution"]
        mode_key = phase_order[min(current_iteration, len(phase_order) - 1)]
        mode_message = MODE_MESSAGES[mode_key]

        # Inject hypotheses context if available
        hypotheses = active_session.get("hypotheses", [])
        if hypotheses:
            hypothesis_context = _format_hypothesis_context(hypotheses)
            mode_message = f"{mode_message}\n\n{hypothesis_context}"

        # Inject verdict if available (hypothesis_resolution phase)
        verdict = active_session.get("verdict")
        if verdict:
            mode_message = f"{mode_message}\n\nWinning hypothesis: {verdict}"

        return {
            "additionalContext": (
                f"<sequential_thinking_mode>\n"
                f"Session: {session_id}\n"
                f"Iteration: {current_iteration} of 2\n"
                f"Mode: {mode_key.upper()}\n"
                f"</sequential_thinking_mode>\n\n"
                f"{mode_message}\n"
            ),
            "tokens": 250,
        }

    # CHANGE-005: Self-investigation mode for RCA/diagnostic sessions
    is_self_investigation = active_session.get("is_self_investigation", False)
    if is_self_investigation:
        mode_key = "self_investigation"
        mode_message = MODE_MESSAGES[mode_key]
        return {
            "additionalContext": (
                f"<sequential_thinking_mode>\n"
                f"Session: {session_id}\n"
                f"Iteration: {current_iteration} of 2\n"
                f"Mode: {mode_key.upper()}\n"
                f"</sequential_thinking_mode>\n\n"
                f"{mode_message}\n"
            ),
            "tokens": 300,
        }

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


def _format_hypothesis_context(hypotheses: list) -> str:
    """Format hypotheses for injection into mode messages.

    Args:
        hypotheses: List of {"id": "H1", "claim": "...", "status": "active"} objects

    Returns:
        Formatted string listing current hypotheses
    """
    if not hypotheses:
        return "No hypotheses tracked yet."

    lines = ["Current hypotheses under consideration:"]
    for h in hypotheses:
        status_emoji = "✓" if h.get("status") == "active" else "?"
        lines.append(f"  {status_emoji} {h['id']}: {h['claim']}")

    return "\n".join(lines)


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
        print(json.dumps(result))

    sys.exit(0)
