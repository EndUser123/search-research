#!/usr/bin/env python3
"""
Repetition blocker for Stop hook — blocks repeated violations after acknowledgment.

CRITICAL Phase 1 hook. Detects when the same violation appears in consecutive
turns after the user/system corrected it. Blocks on second occurrence.

Block conditions:
  - Same violation in turn N and N+1 AND acknowledged in N → BLOCK
  - Same violation 3+ times regardless of acknowledgment → BLOCK
  - "Understood" / "You're right" in turn N, same error in N+1 → BLOCK

Special case: lazy_fix — 1st=advisory, 2nd=warning, 3rd=block
Special case: confidence_without_evidence — 1st=advisory, 2nd=warning, 3rd=block

State: .claude/.artifacts/{terminal_id}/hook_state/last_violations.json
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Add hooks directory to path for shared imports
_Hook_Dir = Path(__file__).parent.resolve()
sys.path.insert(0, str(_Hook_Dir))

from hook_state_manager import (
    check_acknowledgment,
    check_violation_repeated,
    escalation_level,
    get_last_violations,
    get_violation_count,
    increment_violation_count,
    set_last_violations,
)

# ---------------------------------------------------------------------------
# Gate registration
# ---------------------------------------------------------------------------

GATE_NAME = "repetition_blocker"

# Types that get special lazy_fix escalation (advisory → warning → block)
_LAZY_ESCALATION_TYPES = frozenset({
    "lazy_fix",
    "confidence_without_evidence",
    "workaround",
    # Gate names that map to lazy escalation behavior
    "lazy_workaround_gate",
    "recommendation_gate",
    "unverified_stance",
})

# Types that block immediately on repetition (no gradual escalation)
_IMMEDIATE_BLOCK_TYPES = frozenset({
    "fabricated_evidence",
    "circular_reasoning",
    "meta_analysis_trap",
    "fake_done",
    "tool_hallucination",
    "agreement_without_understanding",
    # Gate names that map to immediate block behavior
    "safety_gate",
    "correction_acknowledgment",
})

# ---------------------------------------------------------------------------
# Gate function
# ---------------------------------------------------------------------------

def run_repetition_blocker(data: dict) -> dict | None:
    """
    Block repeated violations after acknowledgment/correction.

    Returns None (pass) or a blocking error dict.
    """
    # Extract scope
    terminal_id = data.get("terminal_id") or os.environ.get("TERMINAL_ID", "")
    session_id = data.get("session_id") or ""

    if not terminal_id:
        return None

    # Get current turn's violations from aggregator output
    all_violations = data.get("all_violations", [])
    if not all_violations:
        return None

    current_violation_types = {v.get("type") for v in all_violations}

    # Check each violation type for repetition
    blocking_types = set()
    warning_types = set()

    for vtype in current_violation_types:
        # Read count BEFORE incrementing (current session appearances before this turn)
        count = get_violation_count(terminal_id, session_id, vtype)
        is_repeated, was_acknowledged = check_violation_repeated(
            terminal_id, session_id, vtype
        )

        if is_repeated:
            # Violation repeated from previous turn — escalate based on occurrence count
            if vtype in _IMMEDIATE_BLOCK_TYPES:
                blocking_types.add(vtype)
            elif vtype in _LAZY_ESCALATION_TYPES:
                if count >= 2:
                    blocking_types.add(vtype)
                else:
                    warning_types.add(vtype)
            else:
                # Generic: block on 2nd+ repetition (count >= 2 means 3rd+ occurrence)
                if count >= 2:
                    blocking_types.add(vtype)
                else:
                    warning_types.add(vtype)
        else:
            # First occurrence in session — apply escalation level for special types
            if vtype in _LAZY_ESCALATION_TYPES:
                lvl = escalation_level(terminal_id, session_id, vtype,
                                      thresholds=(1, 2, 3))
                if lvl == "warning":
                    warning_types.add(vtype)
                elif lvl == "block":
                    blocking_types.add(vtype)
            # Non-escalation types pass on first occurrence

    # Increment counts AFTER checking (for next turn's comparison)
    for vtype in current_violation_types:
        increment_violation_count(terminal_id, session_id, vtype)

    # Build block message
    if blocking_types:
        violation_list = ", ".join(sorted(blocking_types))
        return {
            "type": "block",
            "severity": "block",
            "gate": GATE_NAME,
            "error": (
                f"REPEATED VIOLATION(S) AFTER CORRECTION: {violation_list}\n\n"
                "You acknowledged this violation but repeated it.\n"
                "Don't explain. Don't apologize. Fix the output and resubmit."
            ),
            "violations": list(blocking_types),
        }

    if warning_types:
        violation_list = ", ".join(sorted(warning_types))
        return {
            "type": "warning",
            "severity": "warning",
            "gate": GATE_NAME,
            "error": (
                f"REPEATED VIOLATION(S): {violation_list}\n\n"
                "This violation appeared before. Fix it now."
            ),
            "violations": list(warning_types),
        }

    return None


def on_load() -> None:
    """Smoke test on import."""
    # Verify state manager is accessible
    import hook_state_manager
    assert hasattr(hook_state_manager, "read_state")
    assert hasattr(hook_state_manager, "write_state")
    assert hasattr(hook_state_manager, "check_violation_repeated")


if __name__ == "__main__":
    # Self-test
    import uuid
    from hook_state_manager import clear_state

    print("Running Stop_repetition_blocker.py self-test...", file=sys.stderr)

    tid = "test_terminal_blocker"
    sid = "test_session_blocker"

    # Clean up any stale state from prior runs
    clear_state(tid, "last_violations.json")
    clear_state(tid, "lazy_fix_count.json")
    clear_state(tid, "test.json")

    # Test 1: First occurrence of a NEW violation type → None (pass-through)
    # Use a unique type to avoid any stale state interactions
    fresh_type = f"test_violation_{uuid.uuid4().hex[:8]}"

    # Simulate Turn N: set last_violations with a DIFFERENT violation type
    # so the fresh_type appears truly new
    set_last_violations(tid, sid, turn_number=1,
                        violations=["some_other_violation"],
                        user_corrected=False, acknowledged=False)

    data = {
        "terminal_id": tid,
        "session_id": sid,
        "output_text": "Here's the fix.",
        "all_violations": [{"type": fresh_type}],
    }
    result = run_repetition_blocker(data)
    assert result is None, f"Expected None on first occurrence, got {result}"

    # Clean up
    clear_state(tid, "last_violations.json")
    clear_state(tid, f"{fresh_type}_count.json")

    # Test 2: Repeated lazy_fix after acknowledgment → WARNING
    # (1st repeat = warning for lazy_fix escalation type)
    # Pre-increment count so this is the 2nd occurrence overall
    increment_violation_count(tid, sid, "lazy_fix")  # count becomes 1

    # Write prior state so check_violation_repeated finds lazy_fix in previous turn
    set_last_violations(tid, sid, turn_number=3,
                        violations=["lazy_fix"],
                        user_corrected=True, acknowledged=True)

    data = {
        "terminal_id": tid,
        "session_id": sid,
        "output_text": "You're right, I apologize for that.",
        "all_violations": [{"type": "lazy_fix"}],
    }
    result = run_repetition_blocker(data)
    assert result is not None, "Expected warning on first repeated violation"
    assert result["severity"] == "warning", f"Expected warning, got {result['severity']}"
    assert "lazy_fix" in result["violations"], f"Expected lazy_fix in violations: {result['violations']}"

    # Test 3: Triple occurrence of lazy_fix → BLOCK
    # Count is now 2 after the increment above, so next repeat = 3rd occurrence
    clear_state(tid, "last_violations.json")  # Clear so repeated check sees prior
    # Write prior state with lazy_fix so check_violation_repeated detects repetition
    set_last_violations(tid, sid, turn_number=4,
                        violations=["lazy_fix"],
                        user_corrected=False, acknowledged=False)

    data["all_violations"] = [{"type": "lazy_fix"}]
    data["output_text"] = "Still working on it."
    result = run_repetition_blocker(data)
    assert result is not None, "Expected block on triple occurrence"
    assert result["severity"] == "block", f"Expected block, got {result.get('severity')}"

    # Clean up test state
    clear_state(tid, "last_violations.json")
    clear_state(tid, "lazy_fix_count.json")
    clear_state(tid, "test.json")

    print("All Stop_repetition_blocker.py self-tests passed.", file=sys.stderr)
