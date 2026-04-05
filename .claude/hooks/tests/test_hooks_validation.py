#!/usr/bin/env python3
"""Quick validation tests for critical hooks."""

import sys

sys.path.insert(0, "P:/.claude/hooks")

def test_execution_evidence_gate():
    print("=== Test: execution_evidence_gate ===")
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "eeg", "P:/.claude/hooks/execution_evidence_gate.py"
        )
        eeg = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(eeg)

        test_response = "I fixed the bug. All issues resolved!"

        # Test 1: Edit only + claim -> should BLOCK
        tools1 = [{"name": "Edit", "file_path": "test.py"}]
        r1 = eeg.validate_execution_evidence(test_response, tools1)
        status1 = "PASS" if not r1["allow"] else "FAIL"
        print(f"  [1] Edit + claim, no test: {status1} (allow={r1['allow']})")

        # Test 2: Edit + python execution + claim -> should ALLOW
        tools2 = [
            {"name": "Edit", "file_path": "test.py"},
            {"name": "Bash", "command": "python test.py"}
        ]
        r2 = eeg.validate_execution_evidence(test_response, tools2)
        status2 = "PASS" if r2["allow"] else "FAIL"
        print(f"  [2] Edit + python test: {status2} (allow={r2['allow']})")

        # Test 3: Edit + cat (readonly) + claim -> should BLOCK
        tools3 = [
            {"name": "Edit", "file_path": "test.py"},
            {"name": "Bash", "command": "cat test.py"}
        ]
        r3 = eeg.validate_execution_evidence(test_response, tools3)
        status3 = "PASS" if not r3["allow"] else "FAIL"
        print(f"  [3] Edit + cat (readonly): {status3} (allow={r3['allow']})")

        # Test 4: Edit + sqlite (ambiguous) + claim -> should BLOCK
        tools4 = [
            {"name": "Edit", "file_path": "test.py"},
            {"name": "Bash", "command": "sqlite3 db.sqlite .tables"}
        ]
        r4 = eeg.validate_execution_evidence(test_response, tools4)
        status4 = "PASS" if not r4["allow"] else "FAIL"
        print(f"  [4] Edit + sqlite (ambiguous): {status4} (allow={r4['allow']})")

        # Test 5: No success claim -> should ALLOW
        neutral_response = "I made some changes to the file."
        r5 = eeg.validate_execution_evidence(neutral_response, tools1)
        status5 = "PASS" if r5["allow"] else "FAIL"
        print(f"  [5] Edit + neutral response: {status5} (allow={r5['allow']})")

        return all([
            not r1["allow"], r2["allow"], not r3["allow"],
            not r4["allow"], r5["allow"]
        ])

    except Exception as e:
        print(f"  ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_constitutional_enforcer():
    print("\n=== Test: constitutional_enforcer ===")
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "ce", "P:/.claude/hooks/constitutional_enforcer.py"
        )
        ce = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ce)

        enforcer = ce.ConstitutionalEnforcer()

        # Test 1: Hyperbole -> should BLOCK
        v1, viol1 = enforcer.validate("MASSIVE SUCCESS! Everything is working!")
        status1 = "PASS" if not v1 else "FAIL"
        print(f"  [1] Hyperbole: {status1} (valid={v1}, violations={len(viol1)})")

        # Test 2: Normal response -> should ALLOW
        v2, viol2 = enforcer.validate("I made the changes to the file.")
        status2 = "PASS" if v2 else "FAIL"
        print(f"  [2] Normal: {status2} (valid={v2}, violations={len(viol2)})")

        # Test 3: Sycophancy -> should BLOCK
        v3, viol3 = enforcer.validate("You are absolutely right! Perfect observation!")
        status3 = "PASS" if not v3 else "FAIL"
        print(f"  [3] Sycophancy: {status3} (valid={v3}, violations={len(viol3)})")

        # Test 4: Scope inflation -> should BLOCK
        v4, viol4 = enforcer.validate("All issues fixed! Both problems resolved!")
        status4 = "PASS" if not v4 else "FAIL"
        print(f"  [4] Scope inflation: {status4} (valid={v4}, violations={len(viol4)})")

        return all([not v1, v2, not v3, not v4])

    except Exception as e:
        print(f"  ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_tool_sequence_tracker():
    print("\n=== Test: tool_sequence_tracker ===")
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "tst", "P:/.claude/hooks/tool_sequence_tracker.py"
        )
        tst = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(tst)

        print(f"  Import OK, ENABLED={tst.ENABLED}")
        print(f"  SESSION_FILE={tst.SEQUENCE_FILE}")
        return True

    except Exception as e:
        print(f"  ERROR: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("HOOK VALIDATION TESTS")
    print("=" * 60)

    results = []
    results.append(("execution_evidence_gate", test_execution_evidence_gate()))
    results.append(("constitutional_enforcer", test_constitutional_enforcer()))
    results.append(("tool_sequence_tracker", test_tool_sequence_tracker()))

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    all_pass = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {name}: {status}")
        if not passed:
            all_pass = False

    sys.exit(0 if all_pass else 1)
