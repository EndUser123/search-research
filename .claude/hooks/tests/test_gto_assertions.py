#!/usr/bin/env python3
"""
Unit tests for gto_assertions.py

Tests:
- GTOAssertionRunner executes assertions from evals.json
- file_exists assertion type
- test_passes assertion type
- no_import_errors assertion type
- Result aggregation produces pass/fail summary
- Atomic write pattern for JSON state (FM-2408)
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

# Add hooks directory to path
hooks_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(hooks_dir))


def test_file_exists_assertion_passes():
    """Test that file_exists assertion passes when file exists."""
    from tdd.gto_assertions import GTOAssertionRunner

    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "exists.txt"
        test_file.write_text("content")

        runner = GTOAssertionRunner(base_path=Path(tmpdir))
        result = runner.run_assertion({"type": "file_exists", "path": "exists.txt"})

        assert result.passed is True
        assert "file_exists" in result.assertion


def test_file_exists_assertion_fails():
    """Test that file_exists assertion fails when file missing."""
    from tdd.gto_assertions import GTOAssertionRunner

    with tempfile.TemporaryDirectory() as tmpdir:
        runner = GTOAssertionRunner(base_path=Path(tmpdir))
        result = runner.run_assertion({"type": "file_exists", "path": "nonexistent.txt"})

        assert result.passed is False
        assert result.reason != ""


def test_test_passes_assertion_with_pytest():
    """Test that test_passes assertion runs pytest correctly."""
    from tdd.gto_assertions import GTOAssertionRunner

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a passing test file
        test_file = Path(tmpdir) / "test_example.py"
        test_file.write_text("""
def test_always_passes():
    assert True
""")

        runner = GTOAssertionRunner(base_path=Path(tmpdir))
        result = runner.run_assertion({"type": "test_passes", "test_file": "test_example.py"})

        assert result.passed is True


def test_test_passes_assertion_fails_on_failing_test():
    """Test that test_passes assertion fails when test fails."""
    from tdd.gto_assertions import GTOAssertionRunner

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a failing test file
        test_file = Path(tmpdir) / "test_fail.py"
        test_file.write_text("""
def test_always_fails():
    assert False, "Intentional failure"
""")

        runner = GTOAssertionRunner(base_path=Path(tmpdir))
        result = runner.run_assertion({"type": "test_passes", "test_file": "test_fail.py"})

        assert result.passed is False


def test_no_import_errors_assertion_passes():
    """Test that no_import_errors assertion passes for valid Python."""
    from tdd.gto_assertions import GTOAssertionRunner

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a valid Python file
        py_file = Path(tmpdir) / "valid.py"
        py_file.write_text("""
import os
import sys

def hello():
    return "world"
""")

        runner = GTOAssertionRunner(base_path=Path(tmpdir))
        result = runner.run_assertion({"type": "no_import_errors", "file": "valid.py"})

        assert result.passed is True


def test_no_import_errors_assertion_fails():
    """Test that no_import_errors assertion fails for broken imports."""
    from tdd.gto_assertions import GTOAssertionRunner

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a file with import error
        py_file = Path(tmpdir) / "broken.py"
        py_file.write_text("""
import nonexistent_module_xyz

def broken():
    pass
""")

        runner = GTOAssertionRunner(base_path=Path(tmpdir))
        result = runner.run_assertion({"type": "no_import_errors", "file": "broken.py"})

        assert result.passed is False


def test_run_all_assertions_from_evals_json():
    """Test running all assertions from evals.json file."""
    from tdd.gto_assertions import GTOAssertionRunner

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test file
        test_file = Path(tmpdir) / "test_pass.py"
        test_file.write_text("def test_ok(): assert True")

        # Create evals.json
        evals_file = Path(tmpdir) / "evals.json"
        evals_data = {
            "assertions": [
                {"type": "file_exists", "path": "test_pass.py"},
                {"type": "no_import_errors", "file": "test_pass.py"},
            ]
        }
        evals_file.write_text(json.dumps(evals_data, indent=2))

        runner = GTOAssertionRunner(base_path=Path(tmpdir))
        summary = runner.run_all(evals_file)

        assert summary["total"] == 2
        assert summary["passed"] == 2
        assert summary["failed"] == 0
        assert summary["status"] == "pass"


def test_result_aggregation_mixed_results():
    """Test result aggregation with mixed pass/fail."""
    from tdd.gto_assertions import GTOAssertionRunner

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create files
        exists_file = Path(tmpdir) / "exists.txt"
        exists_file.write_text("content")

        # Create evals.json with mixed assertions
        evals_file = Path(tmpdir) / "evals.json"
        evals_data = {
            "assertions": [
                {"type": "file_exists", "path": "exists.txt"},  # pass
                {"type": "file_exists", "path": "missing.txt"},  # fail
            ]
        }
        evals_file.write_text(json.dumps(evals_data, indent=2))

        runner = GTOAssertionRunner(base_path=Path(tmpdir))
        summary = runner.run_all(evals_file)

        assert summary["total"] == 2
        assert summary["passed"] == 1
        assert summary["failed"] == 1
        assert summary["status"] == "fail"


def test_atomic_write_for_json_state():
    """Test that JSON state writes use atomic write pattern (FM-2408)."""
    from tdd.gto_assertions import GTOAssertionRunner

    with tempfile.TemporaryDirectory() as tmpdir:
        runner = GTOAssertionRunner(base_path=Path(tmpdir))
        state_file = Path(tmpdir) / "state" / "assertion_state.json"

        # Save state
        runner.save_state(state_file, {"test": "data", "count": 1})

        # Verify temp file was cleaned up
        temp_file = state_file.with_suffix(".tmp")
        assert not temp_file.exists(), "Temp file should be cleaned up after atomic write"

        # Verify state file exists and is valid JSON
        assert state_file.exists()
        with open(state_file, encoding="utf-8") as f:
            data = json.load(f)
        assert data["test"] == "data"
        assert data["count"] == 1


def test_load_state_from_json():
    """Test loading state from JSON file."""
    from tdd.gto_assertions import GTOAssertionRunner

    with tempfile.TemporaryDirectory() as tmpdir:
        runner = GTOAssertionRunner(base_path=Path(tmpdir))
        state_file = Path(tmpdir) / "state" / "existing_state.json"
        state_file.parent.mkdir(parents=True, exist_ok=True)

        # Create existing state
        state_file.write_text(json.dumps({"existing": "state", "value": 42}))

        # Load state
        loaded = runner.load_state(state_file)

        assert loaded["existing"] == "state"
        assert loaded["value"] == 42


def test_unknown_assertion_type_fails_gracefully():
    """Test that unknown assertion types fail gracefully."""
    from tdd.gto_assertions import GTOAssertionRunner

    with tempfile.TemporaryDirectory() as tmpdir:
        runner = GTOAssertionRunner(base_path=Path(tmpdir))
        result = runner.run_assertion({"type": "unknown_assertion_type", "some": "field"})

        assert result.passed is False
        assert "Unknown assertion type" in result.reason


def main():
    """Run all tests."""
    import pytest

    exit_code = pytest.main([__file__, "-v"])
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
