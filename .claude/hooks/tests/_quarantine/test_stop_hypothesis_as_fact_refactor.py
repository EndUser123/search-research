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
        assert False, f"Verification engine import failed: {e}"
        return  # unreachable

    # Test evidence store import
    try:
        from evidence_store import load_tool_events_for_context
        print("✓ Evidence store import successful")
    except ImportError as e:
        assert False, f"Evidence store import failed: {e}"
        return  # unreachable

    # Test Stop hook import
    try:
        import Stop_hypothesis_as_fact_gate
        print("✓ Stop hook import successful")
    except ImportError as e:
        assert False, f"Stop hook import failed: {e}"
        return  # unreachable

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

        assert claims, "extract_claims() returned no claims"
        print("✓ extract_claims() works")

    except Exception as e:
        assert False, f"extract_claims() failed: {e}"

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

        assert verdicts, "build_verdicts() returned no verdicts"
        print("✓ build_verdicts() works")

    except Exception as e:
        assert False, f"build_verdicts() failed: {e}"

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

        assert "allow" in result, "Stop hook run() returned unexpected format"
        print("✓ Stop hook run() works")

    except Exception as e:
        assert False, f"Stop hook run() failed: {e}"

def test_no_false_positive_on_quoted_incident():
    """Regression: quoted incident examples in markdown tables must not trigger MECHANISM claims.

    The _strip_non_assertion_contexts preprocessor strips markdown table rows
    before claim extraction. Without it, MECHANISM patterns match quoted incident
    text documenting bad behavior, causing false positives.
    """
    print("\nTesting false-positive prevention on quoted incident...")

    try:
        import Stop_hypothesis_as_fact_gate
        from verification import extract_claims

        # Simulated LLM response that documents a bad-incident example in a markdown table.
        # The MECHANISM pattern would match "when it can't complete within the timeout
        # window, it marks session context as degraded" if not stripped.
        response_with_table = """
## Common Failure Patterns

| Pattern | Description | Impact |
|---------|-------------|--------|
| TIMEOUT_HANDLER | When it can't complete within the timeout window, it marks session context as degraded | Session state corruption |

The handler retries with exponential backoff.
"""
        data = {
            "session_id": "test-session-table",
            "terminal_id": "test-terminal-table",
            "response_text": response_with_table,
        }

        result = Stop_hypothesis_as_fact_gate.run(data)

        # Gate should allow this — no genuine mechanism claims, just a quoted example
        assert result.get("allow") is True, f"Expected allow=True, got {result}"
        reason = result.get("reason", "")
        assert "No claims detected" in reason, f"Unexpected reason: {reason}"

        # Double-check: claims extracted from stripped text should be zero
        stripped = Stop_hypothesis_as_fact_gate._strip_non_assertion_contexts(response_with_table)
        claims = extract_claims(stripped)
        mechanism_claims = [c for c in claims if c.type.value == "MECHANISM"]
        assert len(mechanism_claims) == 0, (
            f"Expected 0 MECHANISM claims on quoted-incident text, got {len(mechanism_claims)}"
        )

        print("✓ No false positive on quoted incident in markdown table")

    except Exception as e:
        assert False, f"False-positive regression test failed: {e}"


if __name__ == "__main__":
    print("=" * 60)
    print("TASK-009 Refactoring Tests")
    print("=" * 60)

    test_imports()
    test_extract_claims()
    test_build_verdicts()
    test_stop_hook_run()
    test_no_false_positive_on_quoted_incident()

    print("\n" + "=" * 60)
    print("✓ ALL TESTS PASSED - TASK-009 refactoring complete")
    print("=" * 60)
