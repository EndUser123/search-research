#!/usr/bin/env python3
"""Tests for hook_error_rca.py - No-handwave gate validation."""

import pytest


def test_gate_blocks_cosmetic_without_evidence():
    """Test 1: Gate should BLOCK cosmetic dismissal without evidence."""
    # Import here to avoid import errors if module doesn't exist yet
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from hook_error_rca import no_handwave_gate

    passed, reason = no_handwave_gate([], 'Root cause: cosmetic display artifact')
    assert not passed, f'Should block: {reason}'
    assert 'BLOCKED' in reason or 'No hooks were tested' in reason
    print('TEST 1 PASSED: empty results + cosmetic = blocked')


def test_gate_blocks_cosmetic_with_stderr_hooks():
    """Test 2: Gate should BLOCK cosmetic when hooks have stderr."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from hook_error_rca import no_handwave_gate

    results = [{'hook_file': 'test.py', 'verdict': 'pass_with_stderr'}]
    passed, reason = no_handwave_gate(results, 'Root cause: cosmetic display artifact')
    assert not passed, f'Should block: {reason}'
    assert 'stderr' in reason.lower()
    print('TEST 2 PASSED: stderr hooks + cosmetic = blocked')


def test_gate_allows_explicit_not_found():
    """Test 3: Gate should ALLOW explicit 'not found'."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from hook_error_rca import no_handwave_gate

    results = [{'hook_file': 'test.py', 'verdict': 'pass'}]
    passed, reason = no_handwave_gate(results, 'Root cause not found. Investigation incomplete.')
    assert passed, f'Should pass: {reason}'
    print('TEST 3 PASSED: explicit unknown = allowed')


def test_gate_allows_specific_root_cause():
    """Test 4: Gate should ALLOW specific root cause with evidence."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from hook_error_rca import no_handwave_gate

    results = [{'hook_file': 'bad.py', 'verdict': 'fail_error'}]
    passed, reason = no_handwave_gate(results, 'Root cause: bad.py fails with ImportError at line 23')
    assert passed, f'Should pass: {reason}'
    print('TEST 4 PASSED: specific root cause = allowed')


def test_gate_blocks_empty_results_without_dismissal_or_specificity():
    """Test 5: Gate should BLOCK empty results without dismissal language or specificity.

    TEST-015: Missing case - empty test_results + non-dismissal without specificity
    should be blocked due to no evidence AND no specificity.

    Evidence from code review:
    - Line 875-879: Empty results block with "No hooks were tested" message
    - Line 931-935: Non-dismissal without specificity blocked separately

    This test verifies both gates fire correctly.
    """
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from hook_error_rca import no_handwave_gate

    # Empty results + non-dismissal language without specificity
    # Should return False with reason about missing hooks/evidence
    passed, reason = no_handwave_gate([], 'Something broke')
    assert not passed, f'Should block: {reason}'
    # Verify it mentions no hooks tested (empty results check at line 875)
    assert 'No hooks were tested' in reason, f'Expected "No hooks were tested" in reason, got: {reason}'
    print('TEST 5 PASSED: empty results + non-dismissal = blocked (no hooks tested)')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
