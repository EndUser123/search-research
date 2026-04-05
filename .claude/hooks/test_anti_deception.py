#!/usr/bin/env python3
"""Test anti-deception mechanisms"""
import json
import subprocess
import sys
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent

def test_skill_enforcement_gate():
    """Test skill_enforcement_gate blocks bash simulation"""
    print("\n" + "="*60)
    print("TEST 1: Skill Enforcement Gate - Bash Simulation")
    print("="*60)

    # First, set pending skill state
    test_input = {
        "tool_name": "bash_tool",
        "tool_input": {
            "command": "python -c \"print('/q execution')\""
        }
    }

    hook_path = HOOKS_DIR / "skill_enforcement_gate.py"

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

    if result.returncode == 2:
        print("✅ PASS: Hook blocked with exit code 2")
        return True
    else:
        print("❌ FAIL: Hook did not block")
        return False

def test_bash_router_with_skill_gate():
    """Test PreToolUse_bash_router includes skill gate"""
    print("\n" + "="*60)
    print("TEST 2: Bash Router Integration")
    print("="*60)

    # Check if skill_enforcement_gate is in HOOK_SEQUENCE
    router_path = HOOKS_DIR / "PreToolUse_bash_router.py"
    content = router_path.read_text()

    if "skill_enforcement_gate.py" in content:
        print("✅ PASS: skill_enforcement_gate in router")
        return True
    else:
        print("❌ FAIL: skill_enforcement_gate NOT in router")
        return False

def test_affirmation_detector():
    """Test anti-sycophancy affirmation detector"""
    print("\n" + "="*60)
    print("TEST 3: Affirmation Detector")
    print("="*60)

    try:
        sys.path.insert(0, str(HOOKS_DIR))
        from anti_sycophancy.affirmation_detector import detect_affirmation

        # Test case: sycophantic response
        test_response = "You're right, I'll fix that now."
        result = detect_affirmation(test_response)

        if result:
            print(f"✅ PASS: Detected '{result.matched}'")
            print(f"  Severity: {result.severity}")
            return True
        else:
            print("❌ FAIL: Did not detect sycophancy")
            return False
    except ImportError as e:
        print(f"❌ FAIL: Import error - {e}")
        return False

def test_overconfidence_detector():
    """Test overconfidence detector"""
    print("\n" + "="*60)
    print("TEST 4: Overconfidence Detector")
    print("="*60)

    try:
        from anti_sycophancy.overconfidence_detector import detect_overconfidence

        test_response = "This explains why the test failed - the system is broken."
        result = detect_overconfidence(test_response)

        if result:
            print(f"✅ PASS: Detected '{result.matched}'")
            print(f"  Type: {result.pattern_type}")
            return True
        else:
            print("❌ FAIL: Did not detect overconfidence")
            return False
    except ImportError as e:
        print(f"❌ FAIL: Import error - {e}")
        return False

def test_lazy_closure_detector():
    """Test lazy closure detector"""
    print("\n" + "="*60)
    print("TEST 5: Lazy Closure Detector")
    print("="*60)

    try:
        from anti_sycophancy.lazy_closure_detector import detect_lazy_closure

        test_response = "Current approach is appropriate. My closure is administrative acknowledgment."
        result = detect_lazy_closure(test_response)

        if result:
            print(f"✅ PASS: Detected '{result.matched}'")
            print(f"  Type: {result.pattern_type}")
            return True
        else:
            print("❌ FAIL: Did not detect lazy closure")
            return False
    except ImportError as e:
        print(f"❌ FAIL: Import error - {e}")
        return False

if __name__ == "__main__":
    results = []

    results.append(test_skill_enforcement_gate())
    results.append(test_bash_router_with_skill_gate())
    results.append(test_affirmation_detector())
    results.append(test_overconfidence_detector())
    results.append(test_lazy_closure_detector())

    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("✅ ALL TESTS PASSED")
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED")
        sys.exit(1)
