#!/usr/bin/env python3
"""
Validation test suite for repetition prevention hooks.

Tests all 7 validation scenarios from the hardening spec:
1. Repetition after acknowledgment
2. Triple repetition
3. Acknowledgment loop
4. Meta-analysis trap
5. Circular reasoning
6. Cross-session isolation
7. Terminal isolation

Run with: python test_repetition_prevention.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_Hook_Dir = Path(__file__).parent.resolve()
sys.path.insert(0, str(_Hook_Dir))

from hook_state_manager import (
    clear_state,
    get_state_dir,
    get_violation_count,
    increment_violation_count,
    set_last_violations,
    check_violation_repeated,
    check_acknowledgment,
    check_meta_analysis_trap,
    check_fake_done,
    push_explanation,
    is_circular_explanation,
    track_confidence_claim,
    track_workaround,
)
from Stop_repetition_blocker import run_repetition_blocker
from Stop_acknowledgment_loop import run_acknowledgment_loop
from Stop_meta_analysis_trap import run_meta_analysis_trap
from Stop_fake_done_detector import run_fake_done_detector


def test_1_repetition_after_acknowledgment():
    """Turn 1: lazy_fix violation → advisory. Turn 2: 'You're right' + lazy_fix → BLOCK."""
    tid = "test_t1_term"
    sid = "test_t1_sess"

    clear_state(tid, "last_violations.json")
    clear_state(tid, "lazy_fix_count.json")

    # Turn 1: lazy_fix violation (first occurrence = pass-through)
    # No prior state → pass
    data = {
        "terminal_id": tid,
        "session_id": sid,
        "output_text": "The fix involves using a conditional check.",
        "all_violations": [{"type": "lazy_fix"}],
    }
    result = run_repetition_blocker(data)
    # First occurrence without prior state → pass-through (advisory)
    assert result is None, f"T1 Turn 1: Expected None, got {result}"
    # Simulate Stop.py state management: record this turn's violations
    set_last_violations(tid, sid, turn_number=2, violations=["lazy_fix"],
                         user_corrected=False, acknowledged=False)

    # Turn 2: Same violation → WARNING (first repeat, count=1 after increment)
    data = {
        "terminal_id": tid,
        "session_id": sid,
        "output_text": "This is the fix.",
        "all_violations": [{"type": "lazy_fix"}],
    }
    result = run_repetition_blocker(data)
    assert result is not None, "T1 Turn 2: Expected a result"
    assert result["severity"] == "warning", f"T1 Turn 2: Expected warning, got {result['severity']}"
    # Simulate Stop.py state management
    set_last_violations(tid, sid, turn_number=3, violations=["lazy_fix"],
                         user_corrected=False, acknowledged=False)

    # Turn 3: Third occurrence → BLOCK (count=2 after increment, >= 2 threshold)
    data = {
        "terminal_id": tid,
        "session_id": sid,
        "output_text": "You're right, I apologize for using 'regardless of'.",
        "all_violations": [{"type": "lazy_fix"}],
    }
    result = run_repetition_blocker(data)
    assert result is not None, "T1 Turn 3: Expected block"
    assert result["severity"] == "block"
    assert "lazy_fix" in result["violations"]

    clear_state(tid, "last_violations.json")
    clear_state(tid, "lazy_fix_count.json")
    print("  Test 1: PASS — repetition after acknowledgment blocks")


def test_2_triple_repetition():
    """Turn 1: confidence_without_evidence → pass. Turn 2: Same → warning. Turn 3: Same → BLOCK."""
    tid = "test_t2_unique"  # Unique to avoid state pollution
    sid = "test_t2_sess"

    clear_state(tid, "last_violations.json")
    clear_state(tid, "confidence_without_evidence_count.json")

    # Turn 1: First occurrence → pass-through (no prior state, count=0, not repeated)
    data = {
        "terminal_id": tid,
        "session_id": sid,
        "output_text": "I'm confident this is the optimal approach.",
        "all_violations": [{"type": "confidence_without_evidence"}],
    }
    result = run_repetition_blocker(data)
    assert result is None, f"T2: Expected None on 1st occurrence, got {result}"
    # Simulate Stop.py state management
    set_last_violations(tid, sid, turn_number=2, violations=["confidence_without_evidence"],
                         user_corrected=False, acknowledged=False)

    # Turn 2: Second occurrence → warning (count=1 after increment, repeated)
    data = {
        "terminal_id": tid,
        "session_id": sid,
        "output_text": "This is definitely the right solution.",
        "all_violations": [{"type": "confidence_without_evidence"}],
    }
    result = run_repetition_blocker(data)
    assert result is not None, "T2: Expected warning on 2nd occurrence"
    assert result["severity"] == "warning", f"T2: Expected warning, got {result['severity']}"
    # Simulate Stop.py state management
    set_last_violations(tid, sid, turn_number=3, violations=["confidence_without_evidence"],
                         user_corrected=False, acknowledged=False)

    # Turn 3: Third occurrence → BLOCK (count=2 after increment, repeated, >= 2 threshold)
    data = {
        "terminal_id": tid,
        "session_id": sid,
        "output_text": "I'm certain this approach is correct.",
        "all_violations": [{"type": "confidence_without_evidence"}],
    }
    result = run_repetition_blocker(data)
    assert result is not None, "T2: Expected block on 3rd occurrence"
    assert result["severity"] == "block", f"T2: Expected block, got {result['severity']}"

    clear_state(tid, "last_violations.json")
    clear_state(tid, "confidence_without_evidence_count.json")
    print("  Test 2: PASS — triple repetition escalates to block")


def test_3_acknowledgment_loop():
    """Turn 1: Error. Turn 2: 'Acknowledged' + same error → BLOCK."""
    tid = "test_terminal_t3"
    sid = "test_session_t3"

    # Test: Acknowledgment + same violation in same output → BLOCK
    data = {
        "terminal_id": tid,
        "session_id": sid,
        "output_text": "You're right, I apologize. The lazy fix was using 'regardless of'.",
        "all_violations": [{"type": "lazy_fix"}],
    }
    result = run_acknowledgment_loop(data)
    assert result is not None, "T3: Expected block on ack loop"
    assert result["severity"] == "block"
    assert "lazy_fix" in result["violations"]

    # Test: Acknowledgment without repetition → pass
    data = {
        "terminal_id": tid,
        "session_id": sid,
        "output_text": "You're right, I'll fix the documentation.",
        "all_violations": [{"type": "other_violation"}],
    }
    result = run_acknowledgment_loop(data)
    assert result is None, f"T3: Expected None when no repeated violation, got {result}"

    print("  Test 3: PASS — acknowledgment loop detected and blocked")


def test_4_meta_analysis_trap():
    """Turn 1: Violation. Turn 2: 'The root cause is I...' → BLOCK."""
    tid = "test_terminal_t4"
    sid = "test_session_t4"

    clear_state(tid, "last_violations.json")

    # Turn 1: Violation occurred
    set_last_violations(tid, sid, turn_number=1, violations=["lazy_fix"],
                         user_corrected=False, acknowledged=False)

    # Turn 2: Meta-analysis trap → BLOCK
    data = {
        "terminal_id": tid,
        "session_id": sid,
        "output_text": "The root cause is I treated 'exact line' as a range.",
        "all_violations": [{"type": "lazy_fix"}],
    }
    result = run_meta_analysis_trap(data)
    assert result is not None, "T4: Expected block on meta-analysis trap"
    assert result["severity"] == "block"

    clear_state(tid, "last_violations.json")
    print("  Test 4: PASS — meta-analysis trap blocked")


def test_5_circular_reasoning():
    """Turn 1: Explains X. Turn 2: 'Let me clarify X' (semantically identical) → warning.
    Turn 3: Same explanation → BLOCK."""
    tid = "test_t5_unique"  # Unique to avoid state pollution
    sid = "test_t5_sess"

    clear_state(tid, "last_violations.json")
    clear_state(tid, "explanation_history.json")

    # Push two identical explanation hashes
    explanation_hash = "abc123"
    history1 = push_explanation(tid, sid, explanation_hash)
    assert len(history1) == 1

    history2 = push_explanation(tid, sid, explanation_hash)
    assert len(history2) == 2

    # Third push triggers circular detection (threshold=3)
    history3 = push_explanation(tid, sid, explanation_hash)
    assert len(history3) == 3

    is_circular = is_circular_explanation(tid, sid, explanation_hash)
    assert is_circular, "T5: Expected True for 3rd identical explanation"

    # Non-circular explanation should pass
    clear_state(tid, "explanation_history.json")
    push_explanation(tid, sid, "different_hash_1")
    push_explanation(tid, sid, "different_hash_2")
    is_circular = is_circular_explanation(tid, sid, "different_hash_3")
    assert not is_circular, "T5: Expected False when no repetition"

    clear_state(tid, "explanation_history.json")
    print("  Test 5: PASS — circular reasoning detection works")


def test_6_cross_session_isolation():
    """Session 1: 2x lazy_fix violations. Session 2: lazy_fix violation → advisory (counter reset)."""
    tid = "test_terminal_t6"
    sid1 = "test_session_t6_a"
    sid2 = "test_session_t6_b"

    clear_state(tid, "last_violations.json")
    clear_state(tid, "lazy_fix_count.json")

    # Session 1: Two violations
    increment_violation_count(tid, sid1, "lazy_fix")
    increment_violation_count(tid, sid1, "lazy_fix")

    # Session 2: Same violation type should start fresh
    count_s2 = get_violation_count(tid, sid2, "lazy_fix")
    assert count_s2 == 0, f"T6: Expected 0 for new session, got {count_s2}"

    # Session 1 count should still be 2
    count_s1 = get_violation_count(tid, sid1, "lazy_fix")
    assert count_s1 == 2, f"T6: Session 1 count should be 2, got {count_s1}"

    clear_state(tid, "last_violations.json")
    clear_state(tid, "lazy_fix_count.json")
    print("  Test 6: PASS — cross-session isolation works")


def test_7_terminal_isolation():
    """Terminal A: 2x violations. Terminal B: Same violation → advisory (separate counter)."""
    tid_a = "test_terminal_t7_a"
    tid_b = "test_terminal_t7_b"
    sid = "test_session_t7"

    for t in [tid_a, tid_b]:
        clear_state(t, "last_violations.json")
        clear_state(t, "lazy_fix_count.json")

    # Terminal A: Two violations
    increment_violation_count(tid_a, sid, "lazy_fix")
    increment_violation_count(tid_a, sid, "lazy_fix")

    # Terminal B: Should start fresh
    count_b = get_violation_count(tid_b, sid, "lazy_fix")
    assert count_b == 0, f"T7: Expected 0 for new terminal, got {count_b}"

    # Terminal A count should still be 2
    count_a = get_violation_count(tid_a, sid, "lazy_fix")
    assert count_a == 2, f"T7: Terminal A count should be 2, got {count_a}"

    for t in [tid_a, tid_b]:
        clear_state(t, "last_violations.json")
        clear_state(t, "lazy_fix_count.json")
    print("  Test 7: PASS — terminal isolation works")


def main():
    print("\n=== Repetition Prevention Hooks — Validation Suite ===\n")

    tests = [
        ("Repetition after acknowledgment", test_1_repetition_after_acknowledgment),
        ("Triple repetition escalation", test_2_triple_repetition),
        ("Acknowledgment loop detection", test_3_acknowledgment_loop),
        ("Meta-analysis trap detection", test_4_meta_analysis_trap),
        ("Circular reasoning detection", test_5_circular_reasoning),
        ("Cross-session isolation", test_6_cross_session_isolation),
        ("Terminal isolation", test_7_terminal_isolation),
    ]

    passed = 0
    failed = 0

    for name, test_fn in tests:
        try:
            test_fn()
            passed += 1
        except AssertionError as e:
            print(f"  FAIL: {e}")
            failed += 1
        except Exception as e:
            print(f"  ERROR: {e}")
            failed += 1

    print(f"\n{'='*55}")
    print(f"Results: {passed} passed, {failed} failed")
    if failed == 0:
        print("All validation tests passed.")
    else:
        print(f"{failed} test(s) failed — review and fix.")
    print()

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
