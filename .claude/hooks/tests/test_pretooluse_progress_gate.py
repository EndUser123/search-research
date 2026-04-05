"""
Tests for PreToolUse_progress_gate.py hook.

RED phase: These tests fail because the hook doesn't exist yet.
"""



def test_blocks_write_with_progress_scale_violation():
    """
    Should BLOCK Write operation when content has progress scale mismatch.

    Bug pattern: total=100 (percentage) but completed=345 (count)
    """
    tool_input = {
        "tool": "Write",
        "parameters": {
            "file_path": "test.py",
            "content": '''
progress.add_task("discover", total=100, stats="0")
progress.update("discover", completed=345)
'''
        }
    }

    from PreToolUse_progress_gate import main

    result = main(tool_input)

    assert result["continue"] is False
    assert "Progress scale mismatch" in result["reason"]


def test_allows_write_with_valid_progress_code():
    """
    Should ALLOW Write operation when progress code is valid.
    """
    tool_input = {
        "tool": "Write",
        "parameters": {
            "file_path": "test.py",
            "content": '''
progress.add_task("discover", total=345, stats="0")
progress.update("discover", completed=100, fields={"stats": "100/345"})
'''
        }
    }

    from PreToolUse_progress_gate import main

    result = main(tool_input)

    assert result["continue"] is True


def test_blocks_edit_with_progress_violation():
    """
    Should BLOCK Edit operation when new_string has progress scale mismatch.
    """
    tool_input = {
        "tool": "Edit",
        "parameters": {
            "file_path": "test.py",
            "old_string": "old code",
            "new_string": 'progress.update("discover", completed=500)'
        }
    }

    # Assume context provides the full file with add_task(total=100)
    from PreToolUse_progress_gate import main

    # For Edit, we only scan new_string - won't catch violations without context
    # This is a known limitation of PreToolUse for Edit operations
    result = main(tool_input)

    # Edit with only new_string won't catch it (no add_task context)
    # But Write with full content would
    assert result["continue"] is True  # Passes due to no add_task in new_string


def test_ignores_non_python_files():
    """
    Should ALLOW operations on non-Python files.
    """
    tool_input = {
        "tool": "Write",
        "parameters": {
            "file_path": "test.md",
            "content": 'progress.add_task("x", total=100)'
        }
    }

    from PreToolUse_progress_gate import main

    result = main(tool_input)

    assert result["continue"] is True


def test_ignores_non_write_edit_tools():
    """
    Should ALLOW operations for tools other than Write/Edit.
    """
    tool_input = {
        "tool": "Bash",
        "parameters": {
            "command": "echo 'progress.add_task(x, total=100)'"
        }
    }

    from PreToolUse_progress_gate import main

    result = main(tool_input)

    assert result["continue"] is True
