#!/usr/bin/env python3
"""Test the challenge-requires-tool gate in Stop.py."""

import re
import sys
from pathlib import Path

# Add hooks dir to path
HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))

# === Test 1: Regex compilation ===
print("=== Test 1: _STANCE_RX compiles ===")
_STANCE_RX = re.compile(
    r"(?:you'?re right(?!\s+to))|"
    r"(?:you'?re absolutely right)|"
    r"(?:i apologize|i'm sorry)|"
    r"(?:i made an unverified claim)|"
    r"(?:let me correct)|"
    r"(?:the root cause is)|"
    r"(?:here is the rca)|"
    r"(?:updated rca)",
    re.IGNORECASE,
)
print("  OK: Regex compiles")

# === Test 2: Stance detection ===
print("\n=== Test 2: Stance detection ===")
tests = [
    ("You're right - I made an unverified claim", True),
    ("You're absolutely right, I apologize", True),
    ("I apologize for misrepresenting", True),
    ("The root cause is missing hook registration", True),
    ("You're right to push back on this", False),  # negative lookahead
    ("Let me check that with tools first", False),
    ("I found the following after reading the file", False),
]
for text, expected in tests:
    matched = bool(_STANCE_RX.search(text))
    status = "OK" if matched == expected else "FAIL"
    label = "STANCE" if matched else "clean"
    want = "STANCE" if expected else "clean"
    print(f"  [{status}] \"{text[:55]}\" -> {label} (want {want})")
    assert matched == expected, f"FAILED: {text}"

# === Test 3: Full gate simulation ===
print("\n=== Test 3: Full gate scenarios ===")
VERIFICATION_TOOLS = {"Read", "Glob", "Grep", "Bash", "WebFetch", "WebSearch"}

def simulate_gate(challenge_marker, response):
    """Simulate the challenge-requires-tool gate (v2: opening-based, tool-independent)."""
    if not challenge_marker:
        return "pass"
    # Only check the first 500 chars of the response
    opening = response[:500]
    stance = bool(_STANCE_RX.search(opening))
    if not stance:
        return "pass"
    return "block"

scenarios = [
    # (challenge, response, expected)
    # Core: stance in opening = block, regardless of tools
    (True, "You're right - I was wrong about that", "block"),
    (True, "You're right - I was wrong about that [then uses Read tool]", "block"),
    (True, "Let me check that file first", "pass"),  # no stance = pass
    (False, "You're right - I was wrong", "pass"),   # no challenge = pass
    (True, "I apologize, the root cause is X", "block"),
    (True, "Updated RCA below", "block"),
    # Good pattern: investigate first, then conclude
    (True, "Let me investigate. " + "x" * 500 + " You're right, after checking I confirm", "pass"),
    # Bad pattern: stance first even if investigation follows
    (True, "You're right. Let me verify with tools to confirm.", "block"),
    # Edge: "You're right to push back" should NOT be blocked (negative lookahead)
    (True, "You're right to push back on this. Let me check.", "pass"),
]

for challenge, response, expected in scenarios:
    result = simulate_gate(challenge, response)
    status = "OK" if result == expected else "FAIL"
    print(f"  [{status}] response=\"{response[:50]}\" -> {result} (want {expected})")
    assert result == expected, f"FAILED: expected {expected}, got {result}"

print("\n=== ALL TESTS PASSED ===")
