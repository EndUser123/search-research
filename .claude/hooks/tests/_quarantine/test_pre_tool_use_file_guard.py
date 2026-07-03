#!/usr/bin/env python3
"""
Comprehensive unit tests for PreToolUse_file_existence_guard.py

Tests cover:
- Allow conditions (non-write tools, new files, Edit tool)
- Block conditions (identical content)
- Ask conditions (different content requires justification)
- Fail-open conditions (invalid JSON, missing file_path, unreadable files)
- Performance optimization (large file sampling)
- State file creation for coordination

Performance target: All tests should complete in <2 seconds total
"""

import json
import subprocess
import tempfile
from pathlib import Path

import pytest


def run_hook(tool_name: str, tool_input: dict) -> tuple[dict, int]:
    """Run hook and return (output_dict, exit_code)."""
    input_data = json.dumps({"tool_name": tool_name, "tool_input": tool_input})

    result = subprocess.run(
        ["python", "P:/.claude/hooks/PreToolUse_file_existence_guard.py"],
        input=input_data,
        capture_output=True,
        text=True,
    )

    try:
        output = json.loads(result.stdout) if result.stdout.strip() else {}
    except json.JSONDecodeError:
        output = {}

    return output, result.returncode


def test_non_write_operation_allowed():
    """Non-write operations should return empty dict (allow)."""
    output, exit_code = run_hook("Read", {"file_path": "test.txt"})

    assert exit_code == 0
    # Should have empty output (no blocking)
    assert output == {}


def test_new_file_allowed():
    """File doesn't exist should return empty dict (allow)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "new_file.txt"

        output, exit_code = run_hook("Write", {
            "file_path": str(test_file),
            "content": "New content"
        })

        assert exit_code == 0
        # Should have empty output (no blocking for new files)
        assert output == {}


def test_identical_content_denied():
    """File exists with identical content should block."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "existing.txt"
        content = "Same content"

        # Create file with content
        test_file.write_text(content, encoding="utf-8")

        # Try to write identical content
        output, exit_code = run_hook("Write", {
            "file_path": str(test_file),
            "content": content
        })

        # Check permissionDecision in output
        decision = output.get("hookSpecificOutput", {}).get("permissionDecision")
        reason = output.get("hookSpecificOutput", {}).get("permissionDecisionReason", "")

        assert exit_code == 0  # JSON output = exit 0
        assert decision == "deny"
        assert "identical content" in reason.lower()


def test_different_content_asked():
    """File exists with different content should ask for justification."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "existing.txt"

        # Create file with old content
        test_file.write_text("Old content", encoding="utf-8")

        # Try to write different content
        output, exit_code = run_hook("Write", {
            "file_path": str(test_file),
            "content": "New content"
        })

        decision = output.get("hookSpecificOutput", {}).get("permissionDecision")
        reason = output.get("hookSpecificOutput", {}).get("permissionDecisionReason", "")

        assert exit_code == 0
        assert decision == "ask"  # Ask user for confirmation
        assert "different content" in reason.lower()


def test_edit_tool_not_checked():
    """Edit tool should bypass file existence check."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "edit_test.txt"
        test_file.write_text("Original", encoding="utf-8")

        output, exit_code = run_hook("Edit", {
            "file_path": str(test_file),
            "old_string": "Original",
            "new_string": "Modified"
        })

        assert exit_code == 0
        # Should have empty output (Edit operations not checked)
        assert output == {}


def test_large_file_performance():
    """File >1MB should use sample comparison for performance."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "large.txt"

        # Create file >1MB
        large_content = "x" * (2 * 1024 * 1024)  # 2MB
        test_file.write_text(large_content, encoding="utf-8")

        # Try to write same content (should sample and detect match)
        output, exit_code = run_hook("Write", {
            "file_path": str(test_file),
            "content": large_content
        })

        # Should block due to identical content (detected via sample)
        decision = output.get("hookSpecificOutput", {}).get("permissionDecision")
        assert exit_code == 0
        assert decision == "deny"


def test_invalid_json_fail_open():
    """Invalid JSON input should fail-open (allow operation)."""
    result = subprocess.run(
        ["python", "P:/.claude/hooks/PreToolUse_file_existence_guard.py"],
        input="invalid json",
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0


def test_missing_file_path_fail_open():
    """Missing file_path should fail-open (allow operation)."""
    output, exit_code = run_hook("Write", {"content": "No path"})

    assert exit_code == 0
    assert output.get("block") != True


def test_unreadable_file_fail_open():
    """Unreadable file should fail-open (allow operation)."""
    # Use a path that likely can't be read
    output, exit_code = run_hook("Write", {
        "file_path": "N:/nonexistent/drive/file.txt",
        "content": "content"
    })

    assert exit_code == 0
    # Should have empty output (file doesn't exist, treated as new file)
    assert output == {}


def test_state_file_created():
    """State file should be created for coordination."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "state_test.txt"
        test_file.write_text("Existing", encoding="utf-8")

        # Block on identical content
        output, exit_code = run_hook("Write", {
            "file_path": str(test_file),
            "content": "Existing"
        })

        decision = output.get("hookSpecificOutput", {}).get("permissionDecision")
        assert decision == "deny"

        # Check state file was created (in hooks/state/ directory)
        state_dir = Path("P:/.claude/hooks/state")
        state_files = list(state_dir.glob("file_existence_decision_*.json"))

        # Should have at least one state file
        assert len(state_files) > 0

        # Verify state file structure
        state_file = state_files[0]
        state_data = json.loads(state_file.read_text())
        assert "file_path" in state_data
        assert "decision" in state_data
        assert "reason" in state_data
        assert "timestamp" in state_data

        # Clean up state file
        for f in state_files:
            f.unlink()


def test_empty_content_allowed():
    """Writing empty content to non-existent file should be allowed."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "empty.txt"

        output, exit_code = run_hook("Write", {
            "file_path": str(test_file),
            "content": ""
        })

        assert exit_code == 0
        assert output == {}


def test_content_with_special_chars():
    """Content with special characters should be handled correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "special.txt"
        content = "Line 1\nLine 2\tTabbed\nUnicode: café"

        test_file.write_text(content, encoding="utf-8")

        output, exit_code = run_hook("Write", {
            "file_path": str(test_file),
            "content": content
        })

        decision = output.get("hookSpecificOutput", {}).get("permissionDecision")
        assert exit_code == 0
        assert decision == "deny"


def test_multiple_write_operations():
    """Multiple write operations to same file should be tracked."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "multiple.txt"

        # First write (new file)
        output1, exit_code1 = run_hook("Write", {
            "file_path": str(test_file),
            "content": "Version 1"
        })
        assert exit_code1 == 0
        assert output1 == {}

        # Create the file
        test_file.write_text("Version 1", encoding="utf-8")

        # Second write (identical content)
        output2, exit_code2 = run_hook("Write", {
            "file_path": str(test_file),
            "content": "Version 1"
        })
        decision2 = output2.get("hookSpecificOutput", {}).get("permissionDecision")
        assert exit_code2 == 0
        assert decision2 == "deny"


def test_write_tool_bypass():
    """Non-write tools should bypass the guard entirely."""
    tools_to_test = [
        ("Read", {"file_path": "test.txt"}),
        ("Glob", {"pattern": "*.py"}),
        ("Grep", {"pattern": "test", "path": "."}),
        ("Bash", {"command": "echo test"}),
    ]

    for tool_name, tool_input in tools_to_test:
        output, exit_code = run_hook(tool_name, tool_input)
        assert exit_code == 0, f"{tool_name} should exit 0"
        assert output == {}, f"{tool_name} should return empty dict"


def test_path_variations():
    """Different path parameter names should be recognized."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "path_test.txt"

        # Test with "path" instead of "file_path"
        output, exit_code = run_hook("Write", {
            "path": str(test_file),
            "content": "Test"
        })

        assert exit_code == 0
        assert output == {}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
