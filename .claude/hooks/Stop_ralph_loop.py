#!/usr/bin/env python3
"""
Stop Hook for Ralph Loop - Clean-Room TDD Loop v2.

Advisory hook that logs state when stopping during an active Ralph Loop.
Non-blocking - provides context and warnings only.

Responsibilities:
- Log state on stop during active loop
- Check iteration count against MAX_ITERATIONS
- Provide advisory warnings when approaching limit
- Track active contract files

ADR: P:/.claude/arch_decisions/ADR-20260324-clean-room-tdd-loop.md
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

# Add hooks directory to path for imports
hooks_dir = Path(__file__).resolve().parent
if str(hooks_dir) not in sys.path:
    sys.path.insert(0, str(hooks_dir))

from tdd.tdd_phase_state import TDDPhaseState, TDDPhaseStateManager

# Maximum iterations before escalation (from ADR)
MAX_ITERATIONS = 10

# Warning threshold (80% of max)
WARNING_THRESHOLD = int(MAX_ITERATIONS * 0.8)


def process_hook(
    input_data: dict[str, Any],
    state_dir: Path | None = None,
) -> tuple[bool, str, dict[str, Any] | None]:
    """Process Stop hook for Ralph Loop state logging.

    This is an ADVISORY hook - it never blocks, only provides context.

    Args:
        input_data: Hook input containing session_id, terminal_id
        state_dir: Optional state directory override

    Returns:
        Tuple of (allow, reason, context):
        - allow: Always True (advisory)
        - reason: Description of loop state
        - context: Dict with loop_active, iterations, active_files, etc.
    """
    # Check bypass environment variable
    bypass_env = os.environ.get("RALPH_LOOP_BYPASS", "0")
    if bypass_env == "1":
        return True, "Ralph loop bypass enabled", {"bypassed": True}

    session_id = input_data.get("session_id", "default")
    terminal_id = input_data.get("terminal_id", "default")

    # Initialize state manager
    if state_dir is None:
        state_dir = Path("P:/.claude/state/tdd95")

    manager = TDDPhaseStateManager(
        session_id=session_id,
        terminal_id=terminal_id,
        state_dir=state_dir,
    )

    # Get all tracked files
    all_files = manager.get_all_files()

    if not all_files:
        # No active contracts
        return True, "No active TDD contracts", {"loop_active": False, "contracts": 0}

    # Find active loop files (in GREEN or RED phase)
    active_files = []
    total_iterations = 0
    phases = {}

    for file_path, file_state in all_files.items():
        phase = file_state.phase
        iterations = file_state.iteration
        phases[str(file_path)] = {
            "phase": phase.value,
            "iterations": iterations,
        }

        # Active loop = in GREEN or RED phase
        if phase in (TDDPhaseState.GREEN, TDDPhaseState.RED):
            active_files.append(str(file_path))
            total_iterations += iterations

    if not active_files:
        # No active loops (all COMPLETE or NONE)
        return (
            True,
            "No active Ralph loops",
            {
                "loop_active": False,
                "contracts": len(all_files),
                "phases": phases,
            },
        )

    # Build context
    context = {
        "loop_active": True,
        "contracts": len(all_files),
        "active_files": active_files,
        "iterations": total_iterations,
        "max_iterations": MAX_ITERATIONS,
        "phases": phases,
    }

    # Check if approaching limit
    if total_iterations >= WARNING_THRESHOLD:
        reason = (
            f"⚠️ APPROACHING MAX ITERATIONS: {total_iterations}/{MAX_ITERATIONS}. "
            f"Active contracts: {len(active_files)}. "
            f"Consider escalating to human if loop continues."
        )
        context["warning"] = True
        context["warning_type"] = "approaching_max_iterations"
    else:
        reason = (
            f"Ralph loop active: {len(active_files)} contract(s), "
            f"{total_iterations} iteration(s). "
            f"Max: {MAX_ITERATIONS}."
        )

    return True, reason, context


if __name__ == "__main__":
    import json

    # Read input from stdin
    try:
        input_text = sys.stdin.read()
        input_data = json.loads(input_text) if input_text.strip() else {}
    except json.JSONDecodeError:
        print(json.dumps({"decision": "allow", "reason": "Invalid JSON input"}))
        sys.exit(0)

    allow, reason, context = process_hook(input_data)

    result = {
        "decision": "allow" if allow else "deny",
        "reason": reason,
    }
    if context:
        result["context"] = context

    print(json.dumps(result))
    sys.exit(0 if allow else 2)
