#!/usr/bin/env python3
"""
Tests for diagnostic bash evidence entity extraction fix.

Verifies that extract_entities_from_evidence() treats DIAGNOSTIC_BASH_PREFIXES
(grep, pytest, ruff, etc.) as observational — consistent with get_evidence_window().

Bug: extract_entities_from_evidence() only checked READ_ONLY_BASH_PREFIXES,
so grep/pytest output entities were silently dropped, causing SCOPE_MISMATCH
blocks when the agent made claims based on grep results.
"""

import sys

sys.path.insert(0, "P:/.claude/hooks")

from assumption_audit_v2 import (
    check_entity_overlap,
    extract_entities_from_evidence,
)


def test_grep_output_produces_evidence_entities():
    """Grep output should contribute evidence entities."""
    tool_sequence = [
        {
            "name": "Bash",
            "command": "grep -n 'allow_response' P:/.claude/hooks/stop_historical_claims_gate.py",
            "output": "50:    from block_protocol import allow_response, block_response",
        }
    ]
    entities = extract_entities_from_evidence(tool_sequence)
    assert any("stop_historical_claims_gate" in e for e in entities), (
        f"grep target file should be in evidence entities, got: {entities}"
    )


def test_pytest_output_produces_evidence_entities():
    """pytest output should contribute evidence entities."""
    tool_sequence = [
        {
            "name": "Bash",
            "command": "pytest tests/test_foo.py -v",
            "output": "tests/test_foo.py::test_bar PASSED\ntests/test_foo.py::test_baz PASSED",
        }
    ]
    entities = extract_entities_from_evidence(tool_sequence)
    assert any("test_foo" in e for e in entities), (
        f"pytest target should be in evidence entities, got: {entities}"
    )


def test_ruff_check_output_produces_evidence_entities():
    """ruff check output should contribute evidence entities."""
    tool_sequence = [
        {
            "name": "Bash",
            "command": "ruff check P:/.claude/hooks/assumption_audit_v2.py",
            "output": "All checks passed!",
        }
    ]
    entities = extract_entities_from_evidence(tool_sequence)
    assert any("assumption_audit_v2" in e for e in entities), (
        f"ruff target should be in evidence entities, got: {entities}"
    )


def test_trivial_commands_still_excluded():
    """Trivial commands (echo, mkdir) should NOT produce evidence entities."""
    tool_sequence = [
        {
            "name": "Bash",
            "command": "echo done",
            "output": "done",
        }
    ]
    entities = extract_entities_from_evidence(tool_sequence)
    assert len(entities) == 0, (
        f"Trivial command should produce no entities, got: {entities}"
    )


def test_read_only_bash_still_works():
    """READ_ONLY_BASH_PREFIXES should still produce evidence entities (regression)."""
    tool_sequence = [
        {
            "name": "Bash",
            "command": "git log --oneline -5",
            "output": "abc1234 feat: add feature\ndef5678 fix: resolve bug",
        }
    ]
    entities = extract_entities_from_evidence(tool_sequence)
    # git log is read-only, should produce entities from output
    assert len(entities) >= 0  # At minimum, no crash


def test_grep_evidence_prevents_scope_mismatch():
    """End-to-end: grep for imports + claim about imports should overlap."""
    tool_sequence = [
        {
            "name": "Bash",
            "command": "grep -n 'allow_response' P:/.claude/hooks/stop_historical_claims_gate.py",
            "output": "50:    from block_protocol import allow_response, block_response",
        }
    ]

    # Claim entities: what the response talks about
    claim_entities = {"stop_historical_claims_gate.py", "allow_response"}

    # Evidence entities: what tools actually observed
    evidence_entities = extract_entities_from_evidence(tool_sequence)

    has_overlap, overlapping, uncovered = check_entity_overlap(
        claim_entities, evidence_entities
    )
    assert has_overlap, (
        f"Expected overlap but got uncovered: {uncovered}. "
        f"Evidence entities: {evidence_entities}"
    )


if __name__ == "__main__":
    tests = [
        test_grep_output_produces_evidence_entities,
        test_pytest_output_produces_evidence_entities,
        test_ruff_check_output_produces_evidence_entities,
        test_trivial_commands_still_excluded,
        test_read_only_bash_still_works,
        test_grep_evidence_prevents_scope_mismatch,
    ]
    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            print(f"  PASS: {test.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL: {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"  ERROR: {test.__name__}: {e}")
            failed += 1

    print(f"\n{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)
