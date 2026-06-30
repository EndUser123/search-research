# test_hook_upgrades.py
import json
import subprocess
import sys
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))


def _run_posttooluse(data: dict) -> dict:
    """Run PostToolUse.py as subprocess, return parsed JSON output."""
    result = subprocess.run(
        [sys.executable, str(HOOKS_DIR / "PostToolUse.py")],
        input=json.dumps(data).encode(),
        capture_output=True,
        timeout=10,
    )
    assert result.returncode == 0, f"Hook crashed: {result.stderr.decode()}"
    stdout = result.stdout.decode().strip()
    return json.loads(stdout) if stdout else {}


def test_posttooluse_error_injection():
    """PostToolUse should inject advisory on Bash error."""
    data = {
        "tool_name": "Bash",
        "tool_input": {"command": "false"},
        "tool_result": "exit code 1",
        "session_id": "test_session",
        "terminal_id": "test_terminal",
    }
    output = _run_posttooluse(data)
    hso = output.get("hookSpecificOutput", {})
    assert hso.get("hookEventName") == "PostToolUse"
    assert "revised hypothesis" in hso.get("additionalContext", "").lower()


def test_posttooluse_empty_grep_injects():
    """PostToolUse should inject advisory on empty Grep results."""
    data = {
        "tool_name": "Grep",
        "tool_input": {"pattern": "nonexistent"},
        "tool_result": "",
        "session_id": "test_session",
        "terminal_id": "test_terminal",
    }
    output = _run_posttooluse(data)
    assert "hookSpecificOutput" in output


def test_posttooluse_successful_read_no_injection():
    """PostToolUse should NOT inject on successful Read."""
    data = {
        "tool_name": "Read",
        "tool_input": {"file_path": "somefile.py"},
        "tool_result": "file contents here",
        "session_id": "test_session",
        "terminal_id": "test_terminal",
    }
    output = _run_posttooluse(data)
    # Should have empty dict or just "{}"
    assert not output.get("hookSpecificOutput")


def test_posttooluse_no_such_file_error():
    """PostToolUse should inject advisory on 'No such file' error."""
    data = {
        "tool_name": "Bash",
        "tool_input": {"command": "cat missing.txt"},
        "tool_result": "cat: missing.txt: No such file or directory",
        "session_id": "test_session",
        "terminal_id": "test_terminal",
    }
    output = _run_posttooluse(data)
    hso = output.get("hookSpecificOutput", {})
    assert hso.get("hookEventName") == "PostToolUse"
    assert "revised hypothesis" in hso.get("additionalContext", "").lower()


def test_posttooluse_glob_no_results():
    """PostToolUse should inject advisory on Glob with no results."""
    data = {
        "tool_name": "Glob",
        "tool_input": {"pattern": "*.nonexistent"},
        "tool_result": "No files found",
        "session_id": "test_session",
        "terminal_id": "test_terminal",
    }
    output = _run_posttooluse(data)
    assert "hookSpecificOutput" in output


def test_posttooluse_populated_grep_no_injection():
    """Populated Grep whose output merely contains '0 matches' must NOT inject.

    Regression for the substring-FP under audit: the old predicate fired on
    any result containing '0 matches' / 'No files found' as a substring.
    """
    data = {
        "tool_name": "Grep",
        "tool_input": {"pattern": "matches"},
        "tool_result": "src/foo.py:42: shows 0 matches for legacy token\nsrc/bar.py:1: real hit",
        "session_id": "test_session",
        "terminal_id": "test_terminal",
    }
    output = _run_posttooluse(data)
    assert not output.get("hookSpecificOutput"), "Populated Grep must not trigger no-results injection"


def test_posttooluse_structured_empty_results_injects():
    """Structured empty results list ({'results': []}) must inject."""
    data = {
        "tool_name": "Glob",
        "tool_input": {"pattern": "*.x"},
        "tool_result": {"results": []},
        "session_id": "test_session",
        "terminal_id": "test_terminal",
    }
    output = _run_posttooluse(data)
    assert "hookSpecificOutput" in output


def test_posttooluse_structured_populated_no_injection():
    """Structured populated results list must NOT inject."""
    data = {
        "tool_name": "Grep",
        "tool_input": {"pattern": "x"},
        "tool_result": {"results": ["src/a.py", "src/b.py"]},
        "session_id": "test_session",
        "terminal_id": "test_terminal",
    }
    output = _run_posttooluse(data)
    assert not output.get("hookSpecificOutput")
