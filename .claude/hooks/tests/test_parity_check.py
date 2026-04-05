"""
Tests for check_parity.py - Parity log monitoring script.

This test file verifies the check_parity main() function behavior for:
- Empty parity log file (no mismatches)
- Single parity mismatch entry
- Multiple parity mismatch entries with output truncation

Run with: pytest P:/.claude/hooks/tests/test_parity_check.py -v
"""

import json
import sys
from io import StringIO
from pathlib import Path

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# The check_parity module doesn't exist yet - this will cause ModuleNotFoundError
try:
    from check_parity import main
except (ImportError, ModuleNotFoundError):
    # check_parity doesn't exist yet - this is expected in RED phase
    main = None


@pytest.mark.skipif(main is None, reason="check_parity not implemented yet")
def test_main_returns_0_when_no_parity_log_exists(tmp_path, monkeypatch):
    """
    Test that main() returns 0 when parity log file doesn't exist.

    This verifies that when there's no parity log file (meaning no mismatches
    have ever been recorded), the function returns 0 (success) and prints
    an appropriate message.

    Given: No parity log file exists
    When: main() is called
    Then: Returns 0 and prints "No parity log found" message
    """
    # Patch the PARITY_LOG constant to use temp path
    parity_log = tmp_path / "parity_mismatches.jsonl"
    monkeypatch.setattr("check_parity.PARITY_LOG", parity_log)

    # Capture stdout
    output = StringIO()
    monkeypatch.setattr("sys.stdout", output)

    result = main()

    assert result == 0
    assert "No parity log found" in output.getvalue()


@pytest.mark.skipif(main is None, reason="check_parity not implemented yet")
def test_main_returns_0_when_parity_log_is_empty(tmp_path, monkeypatch):
    """
    Test that main() returns 0 when parity log exists but is empty.

    This verifies that when the parity log file exists but contains no
    entries, the function returns 0 (success) and prints an appropriate
    message.

    Given: Parity log file exists but is empty
    When: main() is called
    Then: Returns 0 and prints "Parity log is empty" message
    """
    # Create empty parity log file
    parity_log = tmp_path / "parity_mismatches.jsonl"
    parity_log.write_text("")

    # Patch the PARITY_LOG constant
    monkeypatch.setattr("check_parity.PARITY_LOG", parity_log)

    # Capture stdout
    output = StringIO()
    monkeypatch.setattr("sys.stdout", output)

    result = main()

    assert result == 0
    assert "Parity log is empty" in output.getvalue()


@pytest.mark.skipif(main is None, reason="check_parity not implemented yet")
def test_main_returns_1_with_single_mismatch(tmp_path, monkeypatch):
    """
    Test that main() returns 1 when parity log has 1 mismatch.

    This verifies that when there's exactly one parity mismatch recorded,
    the function returns 1 (failure) and prints details about the mismatch.

    Given: Parity log contains exactly 1 mismatch entry
    When: main() is called
    Then: Returns 1 and prints mismatch details
    """
    # Create parity log with 1 mismatch
    parity_log = tmp_path / "parity_mismatches.jsonl"
    mismatch = {
        "ts": "2026-02-04T10:00:00",
        "hook": "test_hook",
        "subprocess_result": {"decision": "allow"},
        "inprocess_result": {"decision": "block"}
    }
    parity_log.write_text(json.dumps(mismatch))

    # Patch the PARITY_LOG constant
    monkeypatch.setattr("check_parity.PARITY_LOG", parity_log)

    # Capture stdout
    output = StringIO()
    monkeypatch.setattr("sys.stdout", output)

    result = main()

    assert result == 1
    output_text = output.getvalue()
    assert "Found 1 parity mismatches" in output_text
    assert "test_hook" in output_text
    assert "subprocess: allow" in output_text
    assert "inprocess:  block" in output_text


@pytest.mark.skipif(main is None, reason="check_parity not implemented yet")
def test_main_returns_1_with_three_mismatches(tmp_path, monkeypatch):
    """
    Test that main() returns 1 with 3 mismatches and shows last 10.

    This verifies that when there are multiple parity mismatches, the
    function returns 1 (failure), reports the total count, and shows
    the last 10 entries (or all if less than 10).

    Given: Parity log contains 3 mismatch entries
    When: main() is called
    Then: Returns 1, reports 3 mismatches, and shows all 3 details
    """
    # Create parity log with 3 mismatches
    parity_log = tmp_path / "parity_mismatches.jsonl"
    mismatches = [
        {
            "ts": "2026-02-04T10:00:00",
            "hook": "test_hook_1",
            "subprocess_result": {"decision": "allow"},
            "inprocess_result": {"decision": "block"}
        },
        {
            "ts": "2026-02-04T10:01:00",
            "hook": "test_hook_2",
            "subprocess_result": {"decision": "block"},
            "inprocess_result": {"decision": "allow"}
        },
        {
            "ts": "2026-02-04T10:02:00",
            "hook": "test_hook_3",
            "subprocess_result": {"decision": "allow"},
            "inprocess_result": {"decision": "deny"}
        }
    ]
    parity_log.write_text("\n".join(json.dumps(m) for m in mismatches))

    # Patch the PARITY_LOG constant
    monkeypatch.setattr("check_parity.PARITY_LOG", parity_log)

    # Capture stdout
    output = StringIO()
    monkeypatch.setattr("sys.stdout", output)

    result = main()

    assert result == 1
    output_text = output.getvalue()
    assert "Found 3 parity mismatches" in output_text
    # All 3 hooks should be shown
    assert "test_hook_1" in output_text
    assert "test_hook_2" in output_text
    assert "test_hook_3" in output_text


def test_check_parity_module_import():
    """
    Characterization test: Verify check_parity module can be imported.

    This test is expected to FAIL in the RED phase because:
    1. The check_parity.py module doesn't exist yet, OR
    2. The main() function hasn't been implemented yet

    Once check_parity is implemented, this test should pass.
    """
    from check_parity import main

    # If we get here, the import succeeded
    assert main is not None
    assert callable(main)
