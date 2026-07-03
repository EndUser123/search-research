"""Standalone hook tests without pytest - bypasses conftest.py issues."""
import json
import subprocess
import sys
from pathlib import Path

# Hook path
HOOK_PATH = Path(__file__).resolve().parent.parent / "PreToolUse" / "PreToolUse_skill_pattern_gate.py"


def _run_hook(user_message: str, tool_name: str = "", tool_input: dict = None, transcript: list = None) -> dict:
    """Execute hook script and parse JSON output."""
    data = {
        "tool_name": tool_name,
        "input": tool_input or {},
        "user_message": user_message,
    }

    if transcript:
        data["transcript"] = transcript

    result = subprocess.run(
        [sys.executable, str(HOOK_PATH)],
        input=json.dumps(data),
        capture_output=True,
        text=True,
        timeout=5,
    )

    if result.stdout.strip():
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return {"error": result.stdout}
    else:
        return {}


def test_slash_command_without_skill_tool_blocks():
    """Test that /code with Bash tool (no Skill) blocks."""
    result = _run_hook(
        user_message="/code test me",
        tool_name="Bash",
        tool_input={"command": "echo test"}
    )

    assert result is not None, "Expected block result"
    assert result.get("block") is True, f"Expected block=True, got: {result}"
    assert "SKILL-FIRST GATE" in result.get("reason", ""), f"Expected skill-first error message, got: {result}"
    print("✓ test_slash_command_without_skill_tool_blocks PASSED")


def test_slash_command_with_skill_tool_allows():
    """Test that /code with Skill('code') tool allows."""
    result = _run_hook(
        user_message="/code test me",
        tool_name="Skill",
        tool_input={"skill": "code"}
    )

    assert result == {}, f"Expected allow result, got: {result}"
    print("✓ test_slash_command_with_skill_tool_allows PASSED")


def test_slash_command_with_skill_then_bash_allows():
    """Test that /code with Skill('code') then Bash allows both."""
    result = _run_hook(
        user_message="/code test me",
        tool_name="Bash",
        tool_input={"command": "echo test"},
        transcript=[
            {
                "content": [
                    {
                        "type": "tool_use",
                        "name": "Skill",
                        "input": {"skill": "code"}
                    }
                ]
            }
        ]
    )

    assert result == {}, f"Expected allow result after Skill tool, got: {result}"
    print("✓ test_slash_command_with_skill_then_bash_allows PASSED")


def test_no_slash_command_allows_any_tool():
    """Test that regular messages (no slash) allow all tools."""
    result = _run_hook(
        user_message="help me with git",
        tool_name="Bash",
        tool_input={"command": "git status"}
    )

    assert result == {}, f"Expected allow result for non-slash commands, got: {result}"
    print("✓ test_no_slash_command_allows_any_tool PASSED")


def test_different_slash_command_blocks_respective_skill():
    """Test that /verify blocks until Skill('verify') is used."""
    result = _run_hook(
        user_message="/verify the file",
        tool_name="Read",
        tool_input={"file_path": "test.md"}
    )

    assert result is not None, "Expected block result"
    assert result.get("block") is True, f"Expected block=True, got: {result}"
    print("✓ test_different_slash_command_blocks_respective_skill PASSED")


def test_missing_state_file_allows_read_tool():
    """Test that Read tool works even when state file doesn't exist."""
    result = _run_hook(
        user_message="check the file",
        tool_name="Read",
        tool_input={"file_path": "test.md"}
    )

    assert result == {}, f"Expected allow result for Read without slash command, got: {result}"
    print("✓ test_missing_state_file_allows_read_tool PASSED")


def test_stateless_gate_no_file_dependency():
    """Verify stateless gate doesn't depend on state file existence."""
    result = _run_hook(
        user_message="help me",
        tool_name="Bash",
        tool_input={"command": "echo test"}
    )

    assert result == {}, f"Expected allow result without state file dependency, got: {result}"
    print("✓ test_stateless_gate_no_file_dependency PASSED")


if __name__ == "__main__":
    print("Running stateless skill-first gate tests...\n")

    tests = [
        test_slash_command_without_skill_tool_blocks,
        test_slash_command_with_skill_tool_allows,
        test_slash_command_with_skill_then_bash_allows,
        test_no_slash_command_allows_any_tool,
        test_different_slash_command_blocks_respective_skill,
        test_missing_state_file_allows_read_tool,
        test_stateless_gate_no_file_dependency,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__} FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} ERROR: {e}")
            failed += 1

    print(f"\n{'='*60}")
    print(f"Results: {passed} passed, {failed} failed")
    print(f"{'='*60}")

    sys.exit(0 if failed == 0 else 1)
