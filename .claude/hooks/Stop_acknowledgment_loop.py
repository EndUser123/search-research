#!/usr/bin/env python3
"""
Acknowledgment loop detector for Stop hook.

Detects when the model acknowledges a violation but repeats the same violation
in the same turn. This is distinct from repetition_blocker — it checks whether
the CURRENT output both acknowledges AND repeats a violation.

Block condition:
  Turn N: Output contains acknowledgment phrase AND same violation pattern present

State: Uses hook_state_manager.check_acknowledgment() for detection.
No persistent state needed — this is a per-turn intra-output check.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

_Hook_Dir = Path(__file__).parent.resolve()
sys.path.insert(0, str(_Hook_Dir))

from hook_state_manager import check_acknowledgment, check_meta_analysis_trap

# ---------------------------------------------------------------------------
# Gate registration
# ---------------------------------------------------------------------------

GATE_NAME = "acknowledgment_loop"

# Phrases that indicate acknowledgment of a correction
_ACK_PATTERNS = (
    "you're right",
    "you're correct",
    "acknowledged",
    "i apologize",
    "that was wrong",
    "i was mistaken",
    "you caught",
    "the hook is correct",
    "i understand now",
    "fair point",
    "good catch",
)

# Violation type labels to detect in output
_VIOLATION_LABELS = (
    "lazy_fix",
    "confidence_without_evidence",
    "fabricated_evidence",
    "circular_reasoning",
    "meta_analysis_trap",
    "fake_done",
    "tool_hallucination",
    "workaround",
    "overconfidence",
    "affirmation_without_evidence",
)


def run_acknowledgment_loop(data: dict) -> dict | None:
    """
    Detect acknowledgment loop: output acknowledges violation but repeats it.

    Returns None (pass) or a blocking error dict.
    """
    terminal_id = data.get("terminal_id") or os.environ.get("TERMINAL_ID", "")
    if not terminal_id:
        return None

    output_text = data.get("output_text", "")
    all_violations = data.get("all_violations", [])

    if not output_text or not all_violations:
        return None

    # Check if output acknowledges a correction
    if not check_acknowledgment(output_text):
        return None

    # Output acknowledges — check if it also repeats a violation
    # Look for violation labels in the output text
    lower_output = output_text.lower()

    repeated_types = []
    for v in all_violations:
        vtype = v.get("type", "")
        if vtype in _VIOLATION_LABELS or vtype in lower_output:
            repeated_types.append(vtype)
        # Also match gate names that indicate violations (e.g., "lazy_workaround_gate")
        elif any(label in vtype for label in ("lazy", "workaround", "unverified",
                                                "epistemic", "overconfidence",
                                                "fabricat", "sycophan")):
            repeated_types.append(vtype)

    # Also check for meta-analysis trap patterns (analyzing WHY instead of fixing)
    if check_meta_analysis_trap(output_text):
        repeated_types.append("meta_analysis_trap")

    if not repeated_types:
        return None

    # Acknowledgment + same violation repeated → block
    violation_list = ", ".join(sorted(set(repeated_types)))
    return {
        "type": "block",
        "severity": "block",
        "gate": GATE_NAME,
        "error": (
            f"ACKNOWLEDGMENT LOOP DETECTED: {violation_list}\n\n"
            "You acknowledged this violation but repeated it in the same response.\n"
            "Don't explain. Don't apologize. Fix the output and resubmit."
        ),
        "violations": list(set(repeated_types)),
    }


def on_load() -> None:
    """Smoke test on import."""
    from hook_state_manager import check_acknowledgment, check_meta_analysis_trap
    assert callable(check_acknowledgment)
    assert callable(check_meta_analysis_trap)


if __name__ == "__main__":
    import sys

    print("Running Stop_acknowledgment_loop.py self-test...", file=sys.stderr)

    # Test 1: Acknowledgment + same violation → BLOCK
    data = {
        "terminal_id": "test_terminal_ack",
        "session_id": "test_session_ack",
        "output_text": "You're right, I apologize. The lazy fix was using 'regardless of'.",
        "all_violations": [{"type": "lazy_fix"}],
    }
    result = run_acknowledgment_loop(data)
    assert result is not None, "Expected block on ack + repeated violation"
    assert result["severity"] == "block"
    assert "lazy_fix" in result["violations"]

    # Test 2: Acknowledgment without violation → pass
    data = {
        "terminal_id": "test_terminal_ack",
        "session_id": "test_session_ack",
        "output_text": "You're right, I'll fix that.",
        "all_violations": [{"type": "other_violation"}],
    }
    result = run_acknowledgment_loop(data)
    assert result is None, f"Expected None when no repeated violation, got {result}"

    # Test 3: No acknowledgment → pass
    data = {
        "terminal_id": "test_terminal_ack",
        "session_id": "test_session_ack",
        "output_text": "The fix is to use a conditional check.",
        "all_violations": [{"type": "lazy_fix"}],
    }
    result = run_acknowledgment_loop(data)
    assert result is None, f"Expected None without acknowledgment, got {result}"

    # Test 4: Meta-analysis trap detected → BLOCK
    data = {
        "terminal_id": "test_terminal_ack",
        "session_id": "test_session_ack",
        "output_text": "You're right. The root cause is I treated 'exact line' as a range.",
        "all_violations": [{"type": "confidence_without_evidence"}],
    }
    result = run_acknowledgment_loop(data)
    assert result is not None, "Expected block on meta-analysis trap"
    assert "meta_analysis_trap" in result["violations"]

    print("All Stop_acknowledgment_loop.py self-tests passed.", file=sys.stderr)
