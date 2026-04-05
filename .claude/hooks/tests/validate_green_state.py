#!/usr/bin/env python3
"""Test green state validator - external blame bias detection."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path("P:/.claude/hooks")))

from StopHook_green_state_validator import (
    check_blame_evidence_proximity,
    detect_evidence,
    detect_external_blame,
    validate_green_state,
)

print("=" * 60)
print("GREEN STATE VALIDATOR TESTS")
print("=" * 60)

# ============================================================================
# TEST CASES
# ============================================================================

TEST_CASES = [
    # (name, text, should_flag, description)

    # === Should FLAG - No evidence ===
    (
        "pre_existing_no_evidence",
        "This appears to be a pre-existing issue in the database module.",
        True,
        "Pre-existing claim without git/branch evidence"
    ),
    (
        "proximity_bias_didnt_touch",
        "I didn't touch that file, so the error must be unrelated to my changes.",
        True,
        "Classic proximity bias - assuming file distance = no causation"
    ),
    (
        "not_in_diff",
        "This error existed before - it's not in my diff.",
        True,
        "Using diff scope to dismiss causation"
    ),
    (
        "probably_before",
        "The bug was probably there before I started.",
        True,
        "Speculative pre-existing without investigation"
    ),
    (
        "baseline_issue",
        "This is a baseline issue that predates the current changes.",
        True,
        "Baseline claim without verification"
    ),
    (
        "unrelated_changes",
        "The failure is unrelated to my changes - it's in a completely different module.",
        True,
        "Module distance doesn't prove no causation (imports!)"
    ),
    (
        "already_broken",
        "This code was already broken when I found it.",
        True,
        "Already broken claim without evidence"
    ),

    # === Should NOT FLAG - Has evidence ===
    (
        "with_git_blame",
        "This appears to be a pre-existing issue. I verified with git blame that this code was added in commit abc1234, which predates my session.",
        False,
        "Pre-existing with git blame evidence"
    ),
    (
        "with_git_log",
        "I didn't modify this file, but I checked git log and confirmed the bug was introduced in issue #42.",
        False,
        "Proximity claim with issue reference"
    ),
    (
        "reproduces_on_main",
        "The error reproduces on clean main branch, confirming it's pre-existing.",
        False,
        "Verified reproduction on main"
    ),
    (
        "documented_issue",
        "This is a pre-existing issue - see GitHub issue #123 for details.",
        False,
        "Reference to documented issue"
    ),
    (
        "verified_predates",
        "I verified that this error predates my changes by checking HEAD~5.",
        False,
        "Git history verification"
    ),

    # === Should NOT FLAG - No blame claim ===
    (
        "normal_investigation",
        "The tests are failing. Let me investigate the root cause.",
        False,
        "Normal investigation, no external blame"
    ),
    (
        "self_attribution",
        "I found the bug in my recent changes to the parser.",
        False,
        "Self-attribution (correct behavior)"
    ),
    (
        "factual_observation",
        "The error occurs in the authentication module when processing invalid tokens.",
        False,
        "Factual observation without blame"
    ),
]

# ============================================================================
# RUN TESTS
# ============================================================================

print("\n--- Individual Pattern Tests ---\n")

passed = 0
failed = 0

for name, text, should_flag, description in TEST_CASES:
    result = validate_green_state(text)
    flagged = not result["valid"]

    if flagged == should_flag:
        status = "✓ PASS"
        passed += 1
    else:
        status = "✗ FAIL"
        failed += 1

    print(f"[{status}] {name}")
    print(f"  Desc: {description}")
    print(f"  Text: {text[:60]}...")
    print(f"  Expected: {'FLAG' if should_flag else 'PASS'}, Got: {'FLAG' if flagged else 'PASS'}")

    if result["blame_detected"]:
        print(f"  Blame patterns: {[b['text'] for b in result['blame_detected']]}")
    if result["evidence_detected"]:
        print(f"  Evidence found: {[e['text'] for e in result['evidence_detected']]}")
    if result["unsupported_blame"]:
        print(f"  Unsupported: {[u['text'] for u in result['unsupported_blame']]}")
    print()

# ============================================================================
# EDGE CASES
# ============================================================================

print("--- Edge Case Tests ---\n")

# Test evidence proximity
print("Test: Evidence proximity window")
text_with_distant_evidence = """
I found that git blame shows this was added in commit xyz123 last month.

[... 1000 characters of other content ...]

This is clearly a pre-existing issue that I didn't cause.
"""

blame = detect_external_blame(text_with_distant_evidence)
evidence = detect_evidence(text_with_distant_evidence)
unsupported = check_blame_evidence_proximity(blame, evidence, text_with_distant_evidence, window=500)

print(f"  Blame patterns found: {len(blame)}")
print(f"  Evidence patterns found: {len(evidence)}")
print(f"  Unsupported (evidence too far): {len(unsupported)}")
print()

# Test multiple blame patterns
print("Test: Multiple blame patterns in one response")
multi_blame = """
I didn't touch that file, and this is clearly a pre-existing issue.
The bug was probably there before, and it's unrelated to my changes.
"""

result = validate_green_state(multi_blame)
print(f"  Blame patterns: {len(result['blame_detected'])}")
print(f"  All patterns: {[b['text'] for b in result['blame_detected']]}")
print()

# ============================================================================
# SUMMARY
# ============================================================================

print("=" * 60)
print(f"RESULTS: {passed} passed, {failed} failed")
print("=" * 60)

if failed > 0:
    print("\n⚠️  Some tests failed - review patterns above")
    sys.exit(1)
else:
    print("\n✓ All tests passed")
    sys.exit(0)
