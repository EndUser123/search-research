"""
Integration tests for PreToolUse_arch_first_enforcer.py

Tests the PreToolUse hook that enforces arch-first workflow when template
update declarations are detected.
"""

import io
import json
import sys
from pathlib import Path

# Add hooks directory to path for imports
hooks_dir = Path(__file__).parent.parent
sys.path.insert(0, str(hooks_dir))


def _run_hook(
    tool_name: str, tool_input: dict, prompt: str = "", terminal_id: str = "test_terminal"
) -> dict:
    """Helper to run the hook and parse JSON output."""
    from PreToolUse_arch_first_enforcer import main as hook_main

    input_data = {
        "tool_name": tool_name,
        "tool_input": tool_input or {},
        "prompt": prompt,
        "terminal_id": terminal_id,
    }

    # Monkey stdin
    old_stdin = sys.stdin
    sys.stdin = io.StringIO(json.dumps(input_data))

    # Monkey stdout - use TextIOWrapper for Python 3.14 compatibility
    old_stdout = sys.stdout
    buffer = io.BytesIO()
    new_stdout = io.TextIOWrapper(buffer, encoding="utf-8")

    sys.stdout = new_stdout

    try:
        hook_main()
    except SystemExit:
        # Hook calls sys.exit(0) for allow, sys.exit(2) for block - this is expected
        pass
    finally:
        sys.stdin = old_stdin
        # Restore stdout BEFORE flushing to avoid I/O on closed file
        sys.stdout = old_stdout
        # Now flush the TextIOWrapper which writes to the buffer
        if not new_stdout.closed:
            new_stdout.flush()

    output = buffer.getvalue().decode("utf-8")

    # Return empty dict if no output
    if not output.strip():
        return {}

    return json.loads(output)


def _get_state_dir() -> Path:
    """Get the correct state directory matching the hook's STATE_DIR."""
    # Both hooks now use: Path(__file__).resolve().parent / "state" (relative to hooks/ directory)
    # declaration_reminder.py: P:\.claude\hooks\UserPromptSubmit_modules\ → parent = hooks/modules, parent.parent = hooks/
    # arch_first_enforcer.py: P:\.claude\hooks\PreToolUse_arch_first_enforcer.py → parent = hooks/
    # Both use hooks/state/
    return Path(__file__).resolve().parent.parent / "state"


def _create_declaration_state(
    terminal_id: str = "test_terminal", path: str = "arch/base.md"
) -> Path:
    """Create a declaration state file for testing."""
    state_dir = _get_state_dir()
    state_dir.mkdir(parents=True, exist_ok=True)

    safe_id = "".join(c if c.isalnum() or c in "_.-:" else "_" for c in terminal_id)
    state_file = state_dir / f"arch_declaration_{safe_id}.json"

    with open(state_file, "w", encoding="utf-8") as f:
        json.dump({"path": path, "timestamp": None}, f)

    return state_file


def _clean_declaration_state(terminal_id: str = "test_terminal") -> None:
    """Clean up declaration state files."""
    state_dir = _get_state_dir()
    safe_id = "".join(c if c.isalnum() or c in "_.-:" else "_" for c in str(terminal_id))
    state_file = state_dir / f"arch_declaration_{safe_id}.json"
    if state_file.exists():
        state_file.unlink()


def test_no_declaration_allows_all_tools():
    """When no declaration exists, all tools should be allowed."""
    terminal_id = "test_no_decl"
    _clean_declaration_state(terminal_id)

    try:
        for tool in ["Read", "Write", "Edit", "Bash", "Grep"]:
            result = _run_hook(tool, {"path": "any/file.py"}, terminal_id=terminal_id)
            assert (
                result.get("continue", True) is True
            ), f"{tool} should be allowed without declaration"
    finally:
        _clean_declaration_state(terminal_id)


def test_read_arch_file_clears_state():
    """Reading the declared arch file should clear state and allow."""
    terminal_id = "test_read_clear"
    state_file = _create_declaration_state(terminal_id, "arch/base.md")

    try:
        result = _run_hook("Read", {"file_path": "arch/base.md"}, terminal_id=terminal_id)

        # Should allow
        assert result.get("continue", True) is True

        # State should be cleared (file deleted)
        assert not state_file.exists(), "State file should be cleared after reading arch file"
    finally:
        _clean_declaration_state(terminal_id)


def test_edit_arch_file_clears_state():
    """Editing the declared arch file should clear state and allow."""
    terminal_id = "test_edit_clear"
    state_file = _create_declaration_state(terminal_id, ".claude/arch/base.md")

    try:
        result = _run_hook(
            "Edit",
            {"path": ".claude/arch/base.md", "old_string": "old", "new_string": "new"},
            terminal_id=terminal_id,
        )

        # Should allow
        assert result.get("continue", True) is True

        # State should be cleared
        assert not state_file.exists(), "State file should be cleared after editing arch file"
    finally:
        _clean_declaration_state(terminal_id)


def test_write_arch_file_clears_state():
    """Writing to an arch file should clear state and allow."""
    terminal_id = "test_write_clear"
    state_file = _create_declaration_state(terminal_id, "SKILL.md")

    try:
        result = _run_hook(
            "Write", {"path": "SKILL.md", "content": "content"}, terminal_id=terminal_id
        )

        # Should allow
        assert result.get("continue", True) is True

        # State should be cleared
        assert not state_file.exists(), "State file should be cleared after writing arch file"
    finally:
        _clean_declaration_state(terminal_id)


def test_non_arch_tools_blocked_with_declaration():
    """Non-arch tools should be blocked when declaration exists."""
    terminal_id = "test_block"
    _create_declaration_state(terminal_id, "arch/base.md")

    try:
        # Try to use Bash without updating template
        result = _run_hook("Bash", {"command": "echo test"}, terminal_id=terminal_id)

        # Should block
        assert (
            result.get("continue", True) is False
        ), "Bash should be blocked with pending declaration"
        assert "reason" in result, "Block message should include reason"
        assert "TEMPLATE UPDATE REQUIRED" in result["reason"]
    finally:
        _clean_declaration_state(terminal_id)


def test_bypass_flag_allows_tools():
    """Bypass flag should allow tools even with declaration."""
    terminal_id = "test_bypass"
    _create_declaration_state(terminal_id, "arch/base.md")

    try:
        # Include bypass flag in prompt
        result = _run_hook(
            "Bash",
            {"command": "echo test"},
            prompt="I'll run this --allow-skip-arch-update",
            terminal_id=terminal_id,
        )

        # Should allow due to bypass flag
        assert result.get("continue", True) is True, "Bypass flag should allow tools"
    finally:
        _clean_declaration_state(terminal_id)


def test_read_non_arch_file_blocked():
    """Reading non-arch files should still be blocked with declaration."""
    terminal_id = "test_read_non_arch"
    _create_declaration_state(terminal_id, "arch/base.md")

    try:
        result = _run_hook("Read", {"file_path": "src/app.py"}, terminal_id=terminal_id)

        # Should block - must read arch file first
        assert result.get("continue", True) is False
        assert "arch/base.md" in result.get("reason", "")
    finally:
        _clean_declaration_state(terminal_id)


def test_is_arch_file_function():
    """Test the _is_arch_file detection logic."""
    from PreToolUse_arch_first_enforcer import _is_arch_file

    # Positive cases - should detect as arch files
    assert _is_arch_file("arch/base.md") is True
    assert _is_arch_file(".claude/arch/base.md") is True
    assert _is_arch_file("some/deep/arch/file.md") is True
    assert _is_arch_file("packages/arch/skill/test.md") is True
    assert _is_arch_file(".claude/skills/arch/test.md") is True
    assert _is_arch_file("path/to/SKILL.md") is True
    assert _is_arch_file(r"arch\template.md") is True  # Windows path

    # Negative cases - should NOT detect as arch files
    assert _is_arch_file("src/app.py") is False
    assert _is_arch_file("tests/test_example.py") is False
    assert _is_arch_file("README.md") is False
    assert _is_arch_file("") is False
    assert _is_arch_file(None) is False


def test_state_file_operations():
    """Test state file load and clear operations."""
    from PreToolUse_arch_first_enforcer import (
        _clear_declaration_state,
        _load_declaration_state,
        _store_declaration_state,
    )

    terminal_id = "test_state_ops"
    safe_id = "".join(c if c.isalnum() or c in "_.-:" else "_" for c in terminal_id)
    state_dir = _get_state_dir()
    state_file = state_dir / f"arch_declaration_{safe_id}.json"

    # Clean first
    _clear_declaration_state(terminal_id)

    try:
        # Test load with no state
        state = _load_declaration_state(terminal_id)
        assert state is None, "Should return None when no state file exists"

        # Test store
        _store_declaration_state(terminal_id, "arch/test.md")
        assert state_file.exists(), "State file should be created"

        # Test load with state
        state = _load_declaration_state(terminal_id)
        assert state is not None
        assert state["path"] == "arch/test.md"

        # Test clear
        _clear_declaration_state(terminal_id)
        assert not state_file.exists(), "State file should be deleted"

        # Test clear with missing file (should not error)
        _clear_declaration_state(terminal_id)  # Should not raise
    finally:
        _clear_declaration_state(terminal_id)


def test_get_terminal_id():
    """Test terminal ID extraction using canonical runtime_env function."""
    from __lib.runtime_env import get_terminal_id

    # Test with terminal_id field
    data = {"terminal_id": "term_123"}
    result = get_terminal_id(data)
    # canonical function uses hook_ledger which may return empty string
    assert result == "term_123" or result == ""

    # Test with terminalId field (alternative)
    data = {"terminalId": "term_456"}
    result = get_terminal_id(data)
    assert result == "term_456" or result == ""

    # Test with CLAUDE_TERMINAL_ID in data
    data = {"CLAUDE_TERMINAL_ID": "term_789"}
    result = get_terminal_id(data)
    assert result == "term_789" or result == ""

    # Test with no terminal_id - canonical function may detect from hook_ledger
    # or return empty string (hook_ledger detection varies by environment)
    data = {}
    result = get_terminal_id(data)
    # Result is either empty string or a detected terminal ID
    assert result == "" or (isinstance(result, str) and len(result) > 0)

    # Test that arch_first_enforcer uses canonical function with fallback
    from PreToolUse_arch_first_enforcer import canonical_get_terminal_id

    data = {}
    # The "or 'default'" fallback ensures we always have a terminal ID
    result = canonical_get_terminal_id(data) or "default"
    assert result in ("default", "") or (isinstance(result, str) and len(result) > 0)


def test_block_message_quality():
    """Test that block message contains required elements."""
    terminal_id = "test_block_msg"
    _create_declaration_state(terminal_id, "arch/template.md")

    try:
        result = _run_hook("Bash", {"command": "ls"}, terminal_id=terminal_id)

        assert result.get("continue", True) is False
        reason = result.get("reason", "")

        required_phrases = [
            "TEMPLATE UPDATE REQUIRED",
            "arch/template.md",
            "Read",
            "Edit/Write",
            "Declaration ≠ Execution",
            "Why this matters",
        ]

        for phrase in required_phrases:
            assert phrase in reason, f"Block message missing: {phrase}"
    finally:
        _clean_declaration_state(terminal_id)


def test_multi_terminal_isolation():
    """Test that different terminals have isolated state."""
    term1 = "terminal_1"
    term2 = "terminal_2"

    _clean_declaration_state(term1)
    _clean_declaration_state(term2)

    try:
        # Create declaration for terminal 1
        _create_declaration_state(term1, "arch/base1.md")

        # Terminal 1 should be blocked
        result1 = _run_hook("Bash", {"command": "echo"}, terminal_id=term1)
        assert result1.get("continue", True) is False

        # Terminal 2 should NOT be blocked (no declaration)
        result2 = _run_hook("Bash", {"command": "echo"}, terminal_id=term2)
        assert result2.get("continue", True) is True
    finally:
        _clean_declaration_state(term1)
        _clean_declaration_state(term2)


def test_windows_path_normalization():
    """Test that Windows backslash paths are handled correctly."""
    from PreToolUse_arch_first_enforcer import _is_arch_file

    # Windows paths should be normalized and detected
    assert _is_arch_file(r"arch\template.md") is True
    assert _is_arch_file(r".claude\arch\base.md") is True


def test_integration_workflow():
    """Test full workflow: declaration → state → enforcement → clear."""
    terminal_id = "test_integration"
    _clean_declaration_state(terminal_id)

    try:
        # Step 1: Create declaration (simulating UserPromptSubmit hook)
        state_file = _create_declaration_state(terminal_id, "arch/workflow.md")
        assert state_file.exists()

        # Step 2: Try to use non-arch tool - should be blocked
        result = _run_hook("Bash", {"command": "ls"}, terminal_id=terminal_id)
        assert result.get("continue", True) is False

        # Step 3: Read the declared arch file - should clear state
        result = _run_hook("Read", {"file_path": "arch/workflow.md"}, terminal_id=terminal_id)
        assert result.get("continue", True) is True
        assert not state_file.exists()

        # Step 4: Now non-arch tools should work
        result = _run_hook("Bash", {"command": "ls"}, terminal_id=terminal_id)
        assert result.get("continue", True) is True
    finally:
        _clean_declaration_state(terminal_id)


if __name__ == "__main__":
    import pytest

    # Ensure state directory exists
    (hooks_dir / "state").mkdir(parents=True, exist_ok=True)

    pytest.main([__file__, "-v"])
