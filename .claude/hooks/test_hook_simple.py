#!/usr/bin/env python3
"""Simple test of empirical_claims_gate with mocked tool sequence."""

import os
import sys
from pathlib import Path

# Enable the hook
os.environ["EMPIRICAL_CLAIMS_GATE_ENABLED"] = "true"
os.environ["EMPIRICAL_CLAIMS_GATE_DEBUG"] = "true"

# Add hooks to path
hooks_dir = Path("P:/.claude/hooks")
sys.path.insert(0, str(hooks_dir))

# Mock load_tool_sequence BEFORE importing empirical_claims_gate
import tool_sequence_manager

original_load = tool_sequence_manager.load_tool_sequence
original_get_all = tool_sequence_manager.ToolSequenceManager.get_all

def mock_get_all(cls):
    return {"tools": [], "session_id": "test", "updated": ""}

tool_sequence_manager.ToolSequenceManager.get_all = classmethod(lambda cls: mock_get_all(cls))

# Now import the hook
from empirical_claims_gate import extract_response, validate_empirical_claims


def run_test_case(name, messages, tools_used, should_block):
    """Run a single test case."""
    print(f"\nTest: {name}")
    print(f"  Expected: {'BLOCK (exit 2)' if should_block else 'ALLOW (exit 0)'}")

    input_data = {
        "type": "transcript",
        "messages": messages,
        "tools_used": tools_used
    }

    response = extract_response(input_data)
    result = validate_empirical_claims(response, tools_used)

    if not result["allow"]:
        if should_block:
            print(f"  ✓ PASS: Would block (reason: {result['reason'][:60]}...)")
            return True
        else:
            print("  ✗ FAIL: Would block but should allow")
            return False
    else:
        if should_block:
            print(f"  ✗ FAIL: Would allow but should block (reason: {result['reason']})")
            return False
        else:
            print(f"  ✓ PASS: Would allow (reason: {result['reason']})")
            return True

# Run tests
print("=" * 60)
print("Testing empirical_claims_gate with mocked tool sequence")
print("=" * 60)

tests = [
    ("Unverified enumeration", [
        {"role": "user", "content": "How many tasks?"},
        {"role": "assistant", "content": "Found 13 tasks with the tag."}
    ], [], True),

    ("Verified enumeration with Grep", [
        {"role": "user", "content": "How many tasks?"},
        {"role": "assistant", "content": "Found 13 tasks with the tag."}
    ], [{"name": "Grep"}], False),

    ("General knowledge", [
        {"role": "user", "content": "What is Git?"},
        {"role": "assistant", "content": "Git is a version control system."}
    ], [], False),

    ("Success claim without execution", [
        {"role": "user", "content": "Fix the bug"},
        {"role": "assistant", "content": "The bug is now fixed and working."}
    ], [], True),

    ("Code behavior claim without reading", [
        {"role": "user", "content": "How does this function work?"},
        {"role": "assistant", "content": "The function handles authentication by validating tokens."}
    ], [], True),
]

results = []
for name, messages, tools, should_block in tests:
    try:
        results.append(run_test_case(name, messages, tools, should_block))
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        results.append(False)

# Summary
print("\n" + "=" * 60)
passed = sum(results)
total = len(results)
print(f"Results: {passed}/{total} passed")

if passed == total:
    print("✓ All tests passed!")
    sys.exit(0)
else:
    print("✗ Some tests failed")
    sys.exit(1)
