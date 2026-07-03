#!/usr/bin/env python3
"""
Integration test for the unified wrapper validator hook.

Tests that PostToolUse_wrapper_validator.py correctly validates both
Python and PowerShell files after Write/Edit operations.
"""

import os
import sys
import tempfile
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "__lib"))

from PostToolUse_wrapper_validator import run


def test_python_file_missing_forwarding():
    """Hook should detect Python function missing argument forwarding."""
    py_content = """
def broken_wrapper(path, filter):
    # Does NOT forward the parameters to any target function
    return path + "/" + filter
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(py_content)
        f.flush()
        file_path = Path(f.name)

    try:
        # Simulate PostToolUse hook data
        hook_data = {
            "tool_name": "Write",
            "tool_input": {"file_path": str(file_path)},
            "tool_response": "",
        }

        result = run(hook_data)

        # Should have findings and not be null
        assert result is not None, "Hook should return findings for .py files"
        assert "findings" in result, "Result should include findings"
        assert any(
            "missing" in f.lower() for f in result["findings"]
        ), f"Should detect missing forwarding, got: {result['findings']}"

        print("✅ Python file missing forwarding detected correctly")
    finally:
        os.unlink(file_path)


def test_python_file_with_forwarding():
    """Hook should pass Python function with correct forwarding."""
    py_content = """
def valid_wrapper(*args, **kwargs):
    target_function(*args, **kwargs)
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(py_content)
        f.flush()
        file_path = Path(f.name)

    try:
        hook_data = {
            "tool_name": "Write",
            "tool_input": {"file_path": str(file_path)},
            "tool_response": "",
        }

        result = run(hook_data)

        assert result is not None
        assert result["status"] == "PASS", f"Should PASS with forwarding, got: {result}"

        print("✅ Python file with forwarding validated correctly")
    finally:
        os.unlink(file_path)


def test_non_script_file_skipped():
    """Hook should skip non-script files."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("Not a script file")
        f.flush()
        file_path = Path(f.name)

    try:
        hook_data = {
            "tool_name": "Write",
            "tool_input": {"file_path": str(file_path)},
            "tool_response": "",
        }

        result = run(hook_data)

        # Should return None for non-script files
        assert result is None, f"Should skip .txt files, got: {result}"

        print("✅ Non-script files skipped correctly")
    finally:
        os.unlink(file_path)


def test_edit_tool_validation():
    """Hook should also validate on Edit operations."""
    py_content = """
def broken_wrapper(path, filter):
    return path + "/" + filter
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(py_content)
        f.flush()
        file_path = Path(f.name)

    try:
        hook_data = {
            "tool_name": "Edit",
            "tool_input": {"file_path": str(file_path)},
            "tool_response": "",
        }

        result = run(hook_data)

        assert result is not None
        assert any("missing" in f.lower() for f in result["findings"])

        print("✅ Edit tool validation works")
    finally:
        os.unlink(file_path)


if __name__ == "__main__":
    test_python_file_missing_forwarding()
    test_python_file_with_forwarding()
    test_non_script_file_skipped()
    test_edit_tool_validation()
    print("\n✅ All integration tests passed!")
