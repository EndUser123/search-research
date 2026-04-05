#!/usr/bin/env python3
"""
Test suite for PreToolUse_authorization_gate.py

Run: python test_authorization_gate.py
"""

import json
import subprocess
import sys
from pathlib import Path


def run_hook(input_data: dict) -> dict:
    """Run the hook with given input and return the result."""
    hook_path = Path(__file__).resolve().parent.parent / "PreToolUse_authorization_gate.py"
    
    result = subprocess.run(
        [sys.executable, str(hook_path)],
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
            print(f"  Reason: {result.get('reason')[:150]}...")
    
    return passed


def make_input(command: str, user_message: str) -> dict:
    """Helper to construct hook input."""
    return {
        "tool_input": {"command": command},
        "conversation": [
            {"role": "user", "content": user_message}
        ]
    }


def main():
    print("=" * 60)
    print("Authorization Gate Hook Tests")
    print("=" * 60)
    print()
    
    tests_passed = 0
    tests_total = 0
    
    # ===== SHOULD BLOCK (confirmatory only) =====
    print("--- Confirmatory-only cases (should BLOCK) ---")
    
    tests_total += 1
    if test_case(
        "git rm with 'correct' → BLOCK",
        make_input("git rm -r src/old_module/", "correct"),
        "block"
    ):
        tests_passed += 1
    
    tests_total += 1
    if test_case(
        "git rm with 'that's right' → BLOCK",
        make_input("git rm file.py", "that's right"),
        "block"
    ):
        tests_passed += 1
    
    tests_total += 1
    if test_case(
        "rm -rf with 'looks good' → BLOCK",
        make_input("rm -rf ./temp/", "looks good"),
        "block"
    ):
        tests_passed += 1
    
    tests_total += 1
    if test_case(
        "git reset --hard with 'optimal' → BLOCK",
        make_input("git reset --hard HEAD~1", "that's optimal"),
        "block"
    ):
        tests_passed += 1
    
    tests_total += 1
    if test_case(
        "Bare 'yes' without action verb → BLOCK",
        make_input("git rm -r hypergraph/", "yes"),
        "block"
    ):
        tests_passed += 1
    
    tests_total += 1
    if test_case(
        "'good approach' → BLOCK",
        make_input("git clean -fd", "good approach"),
        "block"
    ):
        tests_passed += 1
    
    print()
    print("--- Explicit authorization cases (should ALLOW) ---")
    
    # ===== SHOULD ALLOW (explicit authorization) =====
    
    tests_total += 1
    if test_case(
        "'do it' → ALLOW",
        make_input("git rm -r old_code/", "do it"),
        "allow"
    ):
        tests_passed += 1
    
    tests_total += 1
    if test_case(
        "'proceed' → ALLOW",
        make_input("rm -rf ./cache/", "proceed"),
        "allow"
    ):
        tests_passed += 1
    
    tests_total += 1
    if test_case(
        "'yes, proceed' → ALLOW",
        make_input("git reset --hard", "yes, proceed"),
        "allow"
    ):
        tests_passed += 1
    
    tests_total += 1
    if test_case(
        "'go ahead' → ALLOW",
        make_input("git rm file.py", "go ahead"),
        "allow"
    ):
        tests_passed += 1
    
    tests_total += 1
    if test_case(
        "'delete it' → ALLOW",
        make_input("rm -rf temp/", "delete it"),
        "allow"
    ):
        tests_passed += 1
    
    tests_total += 1
    if test_case(
        "'yes, delete them' → ALLOW",
        make_input("git rm -r src/old/", "yes, delete them"),
        "allow"
    ):
        tests_passed += 1
    
    tests_total += 1
    if test_case(
        "'execute' → ALLOW",
        make_input("git clean -fd", "execute"),
        "allow"
    ):
        tests_passed += 1

    print()
    print("--- Non-destructive commands (should ALLOW regardless) ---")
    
    # ===== NON-DESTRUCTIVE (always allow) =====
    
    tests_total += 1
    if test_case(
        "git status (non-destructive) → ALLOW",
        make_input("git status", "correct"),
        "allow"
    ):
        tests_passed += 1
    
    tests_total += 1
    if test_case(
        "ls command → ALLOW",
        make_input("ls -la", "yes"),
        "allow"
    ):
        tests_passed += 1
    
    tests_total += 1
    if test_case(
        "cat file → ALLOW",
        make_input("cat README.md", "looks good"),
        "allow"
    ):
        tests_passed += 1
    
    tests_total += 1
    if test_case(
        "git log → ALLOW",
        make_input("git log --oneline -10", "that's right"),
        "allow"
    ):
        tests_passed += 1
    
    print()
    print("--- Edge cases ---")
    
    tests_total += 1
    if test_case(
        "git push --force with 'ship it' → ALLOW",
        make_input("git push --force origin main", "ship it"),
        "allow"
    ):
        tests_passed += 1
    
    tests_total += 1
    if test_case(
        "git push -f with just 'ok' → BLOCK",
        make_input("git push -f", "ok"),
        "block"
    ):
        tests_passed += 1
    
    print()
    print("=" * 60)
    print(f"Results: {tests_passed}/{tests_total} tests passed")
    print("=" * 60)
    
    return 0 if tests_passed == tests_total else 1


if __name__ == "__main__":
    sys.exit(main())
