#!/usr/bin/env python3
"""Test entity_correlation_gate stdin detection fix"""
import json
import subprocess
import sys
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent

def test_hook_mode():
    """Test that hook processes JSON from stdin"""
    print("TEST: Hook mode with JSON stdin")

    hook_path = HOOKS_DIR / "entity_correlation_gate.py"
    test_input = {
        "response": "Test response text"
    }

    result = subprocess.run(
        [sys.executable, str(hook_path)],
        input=json.dumps(test_input),
        capture_output=True,
        text=True,
        timeout=5
    )

    print(f"Exit code: {result.returncode}")
    print(f"Stdout: {result.stdout}")
    print(f"Stderr: {result.stderr}")

    # Should NOT print argparse help
    if "usage:" in result.stdout or "--help" in result.stdout:
        print("❌ FAIL: Printed argparse help instead of processing hook")
        return False

    # Should print JSON output
    try:
        output = json.loads(result.stdout)
        print("✅ PASS: Returned valid JSON (hook mode)")
        return True
    except json.JSONDecodeError:
        print("❌ FAIL: Did not return valid JSON")
        return False

def test_cli_mode():
    """Test that CLI mode still works"""
    print("\nTEST: CLI mode with --list-entities")

    hook_path = HOOKS_DIR / "entity_correlation_gate.py"

    result = subprocess.run(
        [sys.executable, str(hook_path, "--list-entities")],
        stdin=subprocess.DEVNULL,  # Close stdin so hook doesn't try to read it
        capture_output=True,
        text=True,
        timeout=5
    )

    print(f"Exit code: {result.returncode}")
    print(f"Stdout preview: {result.stdout[:200]}")

    if "Configured Entities:" in result.stdout:
        print("✅ PASS: CLI mode works")
        return True
    else:
        print("❌ FAIL: CLI mode broken")
        return False

if __name__ == "__main__":
    results = []
    results.append(test_hook_mode())
    results.append(test_cli_mode())

    print("\n" + "="*60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    sys.exit(0 if passed == total else 1)
