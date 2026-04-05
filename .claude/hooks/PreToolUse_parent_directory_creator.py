#!/usr/bin/env python3
"""
PreToolUse Hook: Parent Directory Creator

Ensures parent directories exist before Write/Edit operations to prevent
the Write tool's silent failure bug where it reports success but fails to
create files when parent directories don't exist.

Root Cause: Write tool reports "Wrote N lines" even when file creation fails
silently due to missing parent directories. This hook creates those directories
before the Write tool runs, preventing the silent failure.

Configuration:
    PARENT_DIR_CREATOR_ENABLED: "true" (default) or "false" to disable
"""

from __future__ import annotations

from pathlib import Path

# Configuration
env_var = "PARENT_DIR_CREATOR_ENABLED"
default_enabled = True
tool_matcher = {"Write", "Edit"}  # Only applies to Write and Edit tools


def ensure_parent_directory(file_path: str) -> bool:
    """Ensure parent directory exists for a file path.

    Args:
        file_path: Path to file (can be relative or absolute)

    Returns:
        True if directory exists or was created, False if failed

    Raises:
        OSError: If directory creation fails for unexpected reasons
    """
    path = Path(file_path)

    # Get parent directory
    parent = path.parent

    # If parent is "." or empty, current directory is fine
    if str(parent) == "." or not str(parent):
        return True

    # Check if parent directory exists
    if parent.exists():
        if parent.is_dir():
            return True
        else:
            # Parent exists but is a file, not a directory
            # This is an error condition - don't try to fix it
            return False

    # Create parent directory (and any missing ancestors)
    try:
        parent.mkdir(parents=True, exist_ok=True)
        return True
    except OSError as e:
        # Log the error but don't fail the hook
        # The Write tool will fail with its own error message
        import logging

        logger = logging.getLogger(__name__)
        logger.addHandler(logging.NullHandler())
        logger.debug(f"Failed to create parent directory for {file_path}: {e}")
        return False


def run(data: dict) -> dict | None:
    """Hook entry point.

    Args:
        data: Tool invocation data with keys:
            - tool_name: str - Name of the tool being invoked
            - tool_input: dict - Tool parameters including 'file_path'

    Returns:
        None if allowed (directory created or already exists)
        dict with 'continue': False and 'reason' if blocked
    """
    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})

    # Only process Write and Edit tools
    if tool_name not in tool_matcher:
        return None

    # Extract file path from tool_input
    file_path = tool_input.get("file_path", "")
    if not file_path:
        return None

    # Ensure parent directory exists
    if ensure_parent_directory(file_path):
        # Directory exists or was created - allow the tool to proceed
        return None
    else:
        # Failed to create directory - block with error
        return {
            "continue": False,
            "reason": (
                f"Cannot create parent directory for: {file_path}\n"
                f"The Write/Edit tool requires parent directories to exist.\n"
                f"Either create the directory manually or check path permissions."
            ),
        }


# Self-test
if __name__ == "__main__":
    import tempfile

    def test_case(description: str, tool_data: dict, expected: dict | None):
        result = run(tool_data)
        passed = (expected is None and result is None) or (
            result is not None
            and expected is not None
            and result.get("continue") == expected.get("continue")
        )
        status = "PASS" if passed else "FAIL"
        print(f"{status}: {description}")
        if not passed and expected is not None:
            print(f"  Expected: {expected}")
            print(f"  Got: {result}")
        return passed

    print("Testing PreToolUse_parent_directory_creator.py\n")

    # Test 1: Write to existing directory - should allow
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test.txt"
        test_case(
            "Write to existing directory",
            {"tool_name": "Write", "tool_input": {"file_path": str(test_file)}},
            None,  # Should allow (return None)
        )

    # Test 2: Write to non-existent nested directory - should create parent
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "nested" / "dir" / "test.txt"
        result = run({"tool_name": "Write", "tool_input": {"file_path": str(test_file)}})
        if result is None:
            print(f"  PASS: Parent directory created for {test_file}")
            # Verify directory was created
            if test_file.parent.exists():
                print(f"  VERIFIED: {test_file.parent} exists")
                # Clean up
                test_file.parent.rmdir()
                test_file.parent.parent.rmdir()
            else:
                print(f"  FAIL: {test_file.parent} was not created")
        else:
            print(f"  FAIL: {result}")

    # Test 3: Edit operation - should also work
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test.txt"
        # Create file first
        test_file.touch()
        test_case(
            "Edit existing file",
            {"tool_name": "Edit", "tool_input": {"file_path": str(test_file)}},
            None,  # Should allow
        )
        test_file.unlink()

    # Test 4: Non-Write tool - should not process
    test_case(
        "Read tool should be ignored",
        {"tool_name": "Read", "tool_input": {"file_path": "test.txt"}},
        None,  # Should return None (not processed)
    )

    print("\nAll tests completed")
