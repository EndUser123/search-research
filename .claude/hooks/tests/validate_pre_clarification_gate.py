#!/usr/bin/env python3
"""
Test suite for Stop_pre_clarification_gate.py

Run: python test_pre_clarification_gate.py
"""

import json
import subprocess
import sys
from pathlib import Path


def run_hook(input_data: dict) -> dict:
    """Run the hook with given input and return the result."""
    hook_path = Path(__file__).resolve().parent.parent / "Stop_pre_clarification_gate.py"
    
    result = subprocess.run(
        [sys.executable, str(hook_path],
        input=json.dumps(input_data),
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"Hook error: {result.stderr}")
        return {"decision": "error", "stderr": result.stderr}
    
    return json.loads(result.stdout)


def test_case(name: str, input_data: dict, expected_decision: str) -> bool:
    """Run a test case and report result."""
    result = run_hook(input_data)
    passed = result.get("decision") == expected_decision
    
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status}: {name}")
    
    if not passed:
        print(f"  Expected: {expected_decision}")
        print(f"  Got: {result.get('decision')}")
        if result.get("reason"):
            print(f"  Reason: {result.get('reason')[:100]}...")
    
    return passed


def main():
    print("=" * 60)
    print("Pre-Clarification Gate Hook Tests")
    print("=" * 60)
    print()
    
    tests_passed = 0
    tests_total = 0
    
    # Test 1: Clarification question WITHOUT search → BLOCK
    tests_total += 1
    if test_case(
        "Clarification question without search should BLOCK",
        {
            "stop_message": {
                "content": "Where should the gear emoji appear? Is it in the statusline or somewhere else?"
            },
            "tool_uses": []
        },
        "block"
    ):
        tests_passed += 1
    
    # Test 2: Clarification question WITH search → ALLOW
    tests_total += 1
    if test_case(
        "Clarification question with prior search should ALLOW",
        {
            "stop_message": {
                "content": "Based on my search, the gear emoji should appear in the statusline. Is this what you expected?"
            },
            "tool_uses": [
                {"name": "Search", "args": {"pattern": "gear"}}
            ]
        },
        "allow"
    ):
        tests_passed += 1
    
    # Test 3: No clarification question → ALLOW
    tests_total += 1
    if test_case(
        "Normal response without clarification should ALLOW",
        {
            "stop_message": {
                "content": "I've implemented the fix. The gear emoji now appears correctly in the statusline."
            },
            "tool_uses": []
        },
        "allow"
    ):
        tests_passed += 1
    
    # Test 4: User preference question → ALLOW (excluded pattern)
    tests_total += 1
    if test_case(
        "User preference question should ALLOW (excluded)",
        {
            "stop_message": {
                "content": "Would you like me to add more logging? Do you want verbose output?"
            },
            "tool_uses": []
        },
        "allow"
    ):
        tests_passed += 1
    
    # Test 5: "What is X" pattern → BLOCK
    tests_total += 1
    if test_case(
        "'What is X' clarification should BLOCK",
        {
            "stop_message": {
                "content": "What is the gear emoji supposed to indicate? I need more information."
            },
            "tool_uses": []
        },
        "block"
    ):
        tests_passed += 1
    
    # Test 6: Read tool counts as investigation → ALLOW
    tests_total += 1
    if test_case(
        "read_file tool should count as investigation",
        {
            "stop_message": {
                "content": "What is the current configuration? I couldn't find it in the file I read."
            },
            "tool_uses": [
                {"name": "read_file", "args": {"path": "config.json"}}
            ]
        },
        "allow"
    ):
        tests_passed += 1
    
    # Test 7: List content format → should parse correctly
    tests_total += 1
    if test_case(
        "List content format should parse",
        {
            "stop_message": {
                "content": [
                    {"type": "text", "text": "I checked the file. "},
                    {"type": "text", "text": "Where should the icon appear?"}
                ]
            },
            "tool_uses": []
        },
        "block"
    ):
        tests_passed += 1
    
    # Test 8: "Should I..." offering is OK → ALLOW
    tests_total += 1
    if test_case(
        "'Should I do X' offers should ALLOW",
        {
            "stop_message": {
                "content": "Should I add error handling? Should I create a test file?"
            },
            "tool_uses": []
        },
        "allow"
    ):
        tests_passed += 1
    
    print()
    print("=" * 60)
    print(f"Results: {tests_passed}/{tests_total} tests passed")
    print("=" * 60)
    
    return 0 if tests_passed == tests_total else 1


if __name__ == "__main__":
    sys.exit(main())
