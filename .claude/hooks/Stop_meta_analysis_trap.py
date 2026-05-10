#!/usr/bin/env python3
"""
Meta-analysis trap detector for Stop hook.

Detects when the model analyzes WHY it violated a rule instead of fixing the output.
This is a Phase 2 hook — fires after a prior violation was detected in the same session.

Block condition:
  - Output contains meta-analysis phrase AND prior turn had a violation

State: Uses hook_state_manager.check_meta_analysis_trap() for detection.
Per-session state: tracks whether a violation occurred in the prior turn.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

_Hook_Dir = Path(__file__).parent.resolve()
sys.path.insert(0, str(_Hook_Dir))

from hook_state_manager import (
    check_meta_analysis_trap,
    get_last_violations,
)

# ---------------------------------------------------------------------------
# Gate registration
# ---------------------------------------------------------------------------

GATE_NAME = "meta_analysis_trap"

# Phrases that indicate meta-analysis instead of fixing
_META_PHRASES = [
    "root cause is i",
    "what i should have",
    "the actual fix should",
    "i diagnosed but didn't",
    "why i put",
    "i should have rendered",
    "the reason i used",
    "i'm analyzing why",
    "let me analyze why",
    "what i meant was",
    "the underlying issue is that i",
]


def run_meta_analysis_trap(data: dict) -> dict | None:
    """
    Block meta-analysis trap: analyzing violation instead of fixing output.

    Returns None (pass) or a blocking error dict.
    """
    terminal_id = data.get("terminal_id") or os.environ.get("TERMINAL_ID", "")
    session_id = data.get("session_id") or ""

    if not terminal_id:
        return None

    output_text = data.get("output_text", "")
    all_violations = data.get("all_violations", [])

    if not output_text:
        return None

    # Check if output contains meta-analysis trap phrases
    if not check_meta_analysis_trap(output_text):
        return None

    # Meta-analysis detected — check if prior turn had a violation
    last = get_last_violations(terminal_id, session_id)

    if not last or last.get("session_id") != session_id or not last.get("violations"):
        # No prior violation — just advisory (meta-analysis is bad style even without prior violation)
        if output_text.strip():
            return {
                "type": "warning",
                "severity": "warning",
                "gate": GATE_NAME,
                "error": (
                    "META-ANALYSIS TRAP DETECTED\n\n"
                    "You're analyzing why the violation occurred instead of fixing it.\n"
                    "Stop explaining. Fix the output directly."
                ),
                "violations": ["meta_analysis_trap"],
            }
        return None

    # Prior violation existed — block
    prior_violations = last.get("violations", [])
    violation_list = ", ".join(sorted(prior_violations))
    return {
        "type": "block",
        "severity": "block",
        "gate": GATE_NAME,
        "error": (
            f"META-ANALYSIS TRAP: You analyzed why instead of fixing\n"
            f"Previous violations: {violation_list}\n\n"
            "Stop analyzing. Fix the output and resubmit."
        ),
        "violations": ["meta_analysis_trap"],
    }


def on_load() -> None:
    """Smoke test on import."""
    from hook_state_manager import check_meta_analysis_trap
    assert callable(check_meta_analysis_trap)


if __name__ == "__main__":
    import sys

    print("Running Stop_meta_analysis_trap.py self-test...", file=sys.stderr)

    # Test 1: Meta-analysis with prior violation → BLOCK
    from hook_state_manager import set_last_violations, clear_state
    tid = "test_terminal_meta"
    sid = "test_session_meta"
    clear_state(tid, "last_violations.json")
    set_last_violations(tid, sid, turn_number=1, violations=["lazy_fix"],
                         user_corrected=False, acknowledged=False)

    data = {
        "terminal_id": tid,
        "session_id": sid,
        "output_text": "The root cause is I treated 'exact line' as a range.",
        "all_violations": [{"type": "lazy_fix"}],
    }
    result = run_meta_analysis_trap(data)
    assert result is not None, "Expected block on meta-analysis with prior violation"
    assert result["severity"] == "block"

    # Test 2: Meta-analysis without prior violation → WARNING
    clear_state(tid, "last_violations.json")
    data = {
        "terminal_id": tid,
        "session_id": sid,
        "output_text": "The root cause is I misunderstood the requirement.",
        "all_violations": [{"type": "minor_style"}],
    }
    result = run_meta_analysis_trap(data)
    assert result is not None, "Expected warning on meta-analysis without prior violation"
    assert result["severity"] == "warning"

    # Test 3: No meta-analysis → pass
    data = {
        "terminal_id": tid,
        "session_id": sid,
        "output_text": "The fix is to use a conditional check instead.",
        "all_violations": [],
    }
    result = run_meta_analysis_trap(data)
    assert result is None, f"Expected None without meta-analysis, got {result}"

    # Clean up
    clear_state(tid, "last_violations.json")

    print("All Stop_meta_analysis_trap.py self-tests passed.", file=sys.stderr)
