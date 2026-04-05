#!/usr/bin/env python3
"""Test refactored Stop_hypothesis_as_fact_gate imports and basic functionality."""

import sys
from pathlib import Path

# Add hooks directory to path
hooks_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(hooks_dir))

def test_imports():
    """Test that all imports work."""
    print("Testing imports...")

    # Test verification engine imports
    try:
        from verification import Claim, build_verdicts, extract_claims
        from verification.engine import VerificationStatus
        print("✓ Verification engine imports successful")
    except ImportError as e:
        print(f"✗ Verification engine import failed: {e}")
        return False

    # Test evidence store import
    try:
        from evidence_store import load_tool_events_for_context
        print("✓ Evidence store import successful")
    except ImportError as e:
        print(f"✗ Evidence store import failed: {e}")
        return False

    # Test Stop hook import
    try:
        import Stop_hypothesis_as_fact_gate
        print("✓ Stop hook import successful")
    except ImportError as e:
        print(f"✗ Stop hook import failed: {e}")
        return False

    return True

def test_extract_claims():
    """Test claim extraction with new engine."""
    print("\nTesting extract_claims...")

    try:
        from verification import extract_claims

        text = "Package has no skill/ directory and documentation states X"
        claims = extract_claims(text)

        print(f"  Extracted {len(claims)} claims")
        for claim in claims:
            print(f"  - {claim.type}: {claim.text[:50]}...")

        if claims:
            print("✓ extract_claims() works")
            return True
        else:
            print("✗ No claims extracted (unexpected)")
            return False

    except Exception as e:
        print(f"✗ extract_claims() failed: {e}")
        return False

def test_build_verdicts():
    """Test verdict building with new engine."""
    print("\nTesting build_verdicts...")

    try:
        from verification import build_verdicts, extract_claims

        text = "Package has no skill/ directory"
        claims = extract_claims(text)

        # Mock tool events
        tool_events = [
            {
                "name": "Glob",
                "command": "packages/handoff/skill/*",
                "output": "No matches found",
                "timestamp": "2026-03-15T10:00:00Z"
            }
        ]

        verdicts = build_verdicts(claims, tool_events)

        print(f"  Built {len(verdicts)} verdicts")
        for verdict in verdicts:
            print(f"  - {verdict.status.value}: {verdict.claim_id}")

        if verdicts:
            print("✓ build_verdicts() works")
            return True
        else:
            print("✗ No verdicts built (unexpected)")
            return False

    except Exception as e:
        print(f"✗ build_verdicts() failed: {e}")
        return False

def test_stop_hook_run():
    """Test Stop hook run() with mock data."""
    print("\nTesting Stop hook run()...")

    try:
        import Stop_hypothesis_as_fact_gate

        # Mock hook data
        data = {
            "session_id": "test-session-123",
            "terminal_id": "test-terminal-456",
            "response_text": "This is a test response that is too short to analyze properly"
        }

        result = Stop_hypothesis_as_fact_gate.run(data)

        print(f"  Result: allow={result.get('allow')}, reason={result.get('reason', '')[:50]}...")

        if "allow" in result:
            print("✓ Stop hook run() works")
            return True
        else:
            print("✗ Stop hook run() returned unexpected format")
            return False

    except Exception as e:
        print(f"✗ Stop hook run() failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("TASK-009 Refactoring Tests")
    print("=" * 60)

    all_passed = True

    all_passed &= test_imports()
    all_passed &= test_extract_claims()
    all_passed &= test_build_verdicts()
    all_passed &= test_stop_hook_run()

    print("\n" + "=" * 60)
    if all_passed:
        print("✓ ALL TESTS PASSED - TASK-009 refactoring complete")
    else:
        print("✗ SOME TESTS FAILED - review errors above")
    print("=" * 60)

    sys.exit(0 if all_passed else 1)
