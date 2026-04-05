#!/usr/bin/env python3
"""
Tests for PreToolUse_file_existence_guard.py
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
    """Non-write operations should be allowed."""
    output, exit_code = run_hook("Read", {"file_path": "test.txt"})

    assert exit_code == 0
    # Should have empty output (no blocking)
    assert output == {}


def test_new_file_allowed():
    """New file creation should be allowed."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "new_file.txt"

        output, exit_code = run_hook("Write", {
            "file_path": str(test_file),
            "content": "New content"
        })

        assert exit_code == 0
        # Should have empty output (no blocking for new files)
        assert output == {}


def test_identical_content_blocked():
    """Writing identical content to existing file should be blocked."""
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


def test_different_content_allowed_with_justification():
    """Writing different content should be allowed with justification request."""
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


def test_edit_tool_allowed():
    """Edit tool should always be allowed (content comparison not practical)."""
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


def test_large_file_sample_performance():
    """Large files should use sampling for performance."""
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


def test_invalid_json_passes_through():
    """Invalid JSON input should allow operation (fail-open)."""
    result = subprocess.run(
        ["python", "P:/.claude/hooks/PreToolUse_file_existence_guard.py"],
        input="invalid json",
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0


def test_missing_file_path_passes_through():
    """Missing file_path should allow operation."""
    output, exit_code = run_hook("Write", {"content": "No path"})

    assert exit_code == 0
    assert output.get("block") != True


def test_unreadable_file_passes_through():
    """Unreadable file should allow operation (fail-open)."""
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

        # Clean up state file
        for f in state_files:
            f.unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
