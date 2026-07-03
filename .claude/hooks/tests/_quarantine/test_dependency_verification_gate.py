#!/usr/bin/env python3
"""Tests for PreToolUse_dependency_verification_gate.py

v2.1: Updated to use terminal_id instead of session_id (aligns with terminal_detection module).
"""

import json
import sys
from pathlib import Path
from unittest.mock import patch

# Add hooks directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import the gate module
import PreToolUse_dependency_verification_gate

PreToolUse_dependency_verification_gate.ENABLED = True


def create_hook_input(tool_name: str, command: str, terminal_id: str = "test-terminal-123") -> str:
    """Create hook input JSON string."""
    data = {
        "tool_name": tool_name,
        "tool_input": {"command": command, "terminal_id": terminal_id} if command else {},
    }
    return json.dumps(data)


def run_hook(
    tool_name: str, command: str, terminal_id: str = "test-terminal-123"
) -> tuple[int, str]:
    """Run hook and return exit code and output."""
    import io
    from contextlib import redirect_stderr, redirect_stdout

    input_data = create_hook_input(tool_name, command, terminal_id)

    # Capture stdout and stderr
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()

    # Simulate stdin
    old_stdin = sys.stdin
    sys.stdin = io.StringIO(input_data)

    try:
        with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
            try:
                PreToolUse_dependency_verification_gate.main()
                exit_code = 0
            except SystemExit as e:
                exit_code = e.code if e.code is not None else 0
    finally:
        sys.stdin = old_stdin

    output = stdout_capture.getvalue() + stderr_capture.getvalue()
    return exit_code, output


def create_hook_payload(
    tool_name: str, command: str, terminal_id: str = "test-terminal-123"
) -> dict:
    """Create hook input dict for in-process execution."""
    return {
        "tool_name": tool_name,
        "tool_input": {
            "command": command,
            "terminal_id": terminal_id,
        }
        if command
        else {},
    }


# ===== POSITIVE CASES (should block) =====


def test_npm_install_scoped_package():
    """Should block npm install @scope/package without verification."""
    exit_code, output = run_hook("Bash", "npm install @modelcontextprotocol/server-exa")
    assert exit_code == 2, f"Expected exit code 2, got {exit_code}"
    assert "@modelcontextprotocol/server-exa" in output or "package" in output.lower()
    assert "verify" in output.lower() or "npm view" in output.lower()


def test_npm_install_simple_package():
    """Should block npm install package-name without verification."""
    exit_code, output = run_hook("Bash", "npm install exa-mcp-server")
    assert exit_code == 2, f"Expected exit code 2, got {exit_code}"
    assert "exa-mcp-server" in output or "package" in output.lower()


def test_pip_install_package():
    """Should block pip install package-name without verification."""
    exit_code, output = run_hook("Bash", "pip install requests")
    assert exit_code == 2, f"Expected exit code 2, got {exit_code}"
    assert "requests" in output or "package" in output.lower()
    assert (
        "verify" in output.lower()
        or "pip search" in output.lower()
        or "pip index" in output.lower()
    )


def test_uv_pip_install_multiple_packages():
    """Should block uv pip install and surface all unverified packages."""
    exit_code, output = run_hook("Bash", "uv pip install mcp fastmcp")
    assert exit_code == 2, f"Expected exit code 2, got {exit_code}"

    result = json.loads(output)
    assert result.get("decision") == "block"
    assert result.get("blocking_hook") == "PreToolUse_dependency_verification_gate.py"
    assert result.get("packages") == ["mcp", "fastmcp"]
    assert result.get("next_actions") == [
        "pip index versions mcp",
        "pip index versions fastmcp",
    ]
    assert "mcp" in result.get("reason", "")
    assert "fastmcp" in result.get("reason", "")


def test_run_blocks_uv_pip_install_multiple_packages():
    """In-process run() should block uv pip install with all unverified packages."""
    result = PreToolUse_dependency_verification_gate.run(
        create_hook_payload("Bash", "uv pip install mcp fastmcp")
    )

    assert result is not None
    assert result.get("decision") == "block"
    assert result.get("packages") == ["mcp", "fastmcp"]
    assert result.get("next_actions") == [
        "pip index versions mcp",
        "pip index versions fastmcp",
    ]


def test_cargo_add_crate():
    """Should block cargo add crate-name without verification."""
    exit_code, output = run_hook("Bash", "cargo add tokio")
    assert exit_code == 2, f"Expected exit code 2, got {exit_code}"
    assert "tokio" in output or "crate" in output.lower()
    assert "verify" in output.lower() or "cargo search" in output.lower()


def test_npm_install_with_flags():
    """Should block npm install even with flags."""
    exit_code, output = run_hook("Bash", "npm install -g @scope/package")
    assert exit_code == 2, f"Expected exit code 2, got {exit_code}"


# ===== NEGATIVE CASES (should allow) =====


def test_npm_view_verification():
    """Should allow npm view (verification command)."""
    exit_code, output = run_hook("Bash", "npm view @modelcontextprotocol/server-exa")
    assert exit_code == 0, f"Expected exit code 0, got {exit_code}: {output}"


def test_npm_search_verification():
    """Should allow npm search (verification command)."""
    exit_code, output = run_hook("Bash", "npm search exa-mcp-server")
    assert exit_code == 0, f"Expected exit code 0, got {exit_code}: {output}"


def test_pip_search_verification():
    """Should allow pip search (verification command)."""
    exit_code, output = run_hook("Bash", "pip search requests")
    assert exit_code == 0, f"Expected exit code 0, got {exit_code}: {output}"


def test_pip_index_versions():
    """Should allow pip index versions (verification command)."""
    exit_code, output = run_hook("Bash", "pip index versions requests")
    assert exit_code == 0, f"Expected exit code 0, got {exit_code}: {output}"


def test_cargo_search_verification():
    """Should allow cargo search (verification command)."""
    exit_code, output = run_hook("Bash", "cargo search tokio")
    assert exit_code == 0, f"Expected exit code 0, got {exit_code}: {output}"


def test_non_package_command():
    """Should allow non-package-related commands."""
    exit_code, output = run_hook("Bash", "git commit -m 'message'")
    assert exit_code == 0, f"Expected exit code 0, got {exit_code}: {output}"


def test_non_bash_tool():
    """Should allow non-Bash tools."""
    exit_code, output = run_hook("Read", "some_file.txt")
    assert exit_code == 0, f"Expected exit code 0, got {exit_code}: {output}"


# ===== EDGE CASES =====


def test_empty_command():
    """Should allow empty command."""
    exit_code, output = run_hook("Bash", "")
    assert exit_code == 0, f"Expected exit code 0, got {exit_code}: {output}"


def test_missing_terminal_id_fails_open():
    """Missing terminal identity should disable stateful enforcement instead of inventing shared state."""
    with patch.dict("os.environ", {"CLAUDE_TERMINAL_ID": ""}, clear=False):
        with patch.object(
            PreToolUse_dependency_verification_gate, "detect_terminal_id", return_value=""
        ):
            result = PreToolUse_dependency_verification_gate.run(
                {
                    "tool_name": "Bash",
                    "tool_input": {"command": "pip install requests"},
                }
            )

    assert result is None


def test_malformed_json():
    """Should allow malformed JSON input."""
    import io
    from contextlib import redirect_stderr, redirect_stdout

    old_stdin = sys.stdin
    sys.stdin = io.StringIO("{invalid json}")

    try:
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()

        with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
            try:
                PreToolUse_dependency_verification_gate.main()
                exit_code = 0
            except SystemExit as e:
                exit_code = e.code if e.code is not None else 0
    finally:
        sys.stdin = old_stdin

    assert exit_code == 0, f"Expected exit code 0 for malformed JSON, got {exit_code}"


def test_local_package_install():
    """Should allow local package installs (./path or file: protocol)."""
    exit_code, output = run_hook("Bash", "npm install ./local-package")
    assert exit_code == 0, f"Expected exit code 0 for local install, got {exit_code}: {output}"

    exit_code, output = run_hook("Bash", "npm install file:./local-package.tgz")
    assert exit_code == 0, f"Expected exit code 0 for file: install, got {exit_code}: {output}"


# ===== NEW TESTS: Session State Tracking =====


def test_verified_package_cached():
    """Should allow install after verification (cached in state)."""
    # First call: verification command should be allowed
    exit_code, output = run_hook("Bash", "npm view @scope/package")
    assert exit_code == 0, f"Expected exit code 0 for verification, got {exit_code}: {output}"

    # Second call: install should be allowed (package verified)
    exit_code, output = run_hook("Bash", "npm install @scope/package")
    assert (
        exit_code == 0
    ), f"Expected exit code 0 for install after verification, got {exit_code}: {output}"


def test_state_persists_across_calls():
    """Verified package should persist across multiple hook invocations."""
    # Verify package
    exit_code, output = run_hook("Bash", "pip search requests")
    assert exit_code == 0, f"Expected exit code 0 for verification, got {exit_code}: {output}"

    # Install once (should be allowed)
    exit_code, output = run_hook("Bash", "pip install requests")
    assert exit_code == 0, f"Expected exit code 0 for first install, got {exit_code}: {output}"

    # Install again (should still be allowed)
    exit_code, output = run_hook("Bash", "pip install requests")
    assert exit_code == 0, f"Expected exit code 0 for second install, got {exit_code}: {output}"


def test_unverified_package_not_cached():
    """Unverified package should not benefit from cache."""
    # Try to install without verification
    exit_code, output = run_hook("Bash", "npm install different-package")
    assert exit_code == 2, f"Expected exit code 2 for unverified install, got {exit_code}: {output}"


# ===== NEW TESTS: Bypass Mechanism =====


def test_bypass_flag_allows_install():
    """Bypass flag should allow install without verification."""
    exit_code, output = run_hook(
        "Bash", "npm install @scope/package --bypass-dependency-verification"
    )
    assert exit_code == 0, f"Expected exit code 0 with bypass flag, got {exit_code}: {output}"


def test_bypass_env_var_allows_install():
    """Bypass env var should allow install without verification."""
    import os

    old_val = os.environ.get("DEPENDENCY_VERIFICATION_MODE")
    try:
        os.environ["DEPENDENCY_VERIFICATION_MODE"] = "bypass"
        exit_code, output = run_hook("Bash", "npm install @scope/package")
        assert (
            exit_code == 0
        ), f"Expected exit code 0 with bypass env var, got {exit_code}: {output}"
    finally:
        if old_val is None:
            os.environ.pop("DEPENDENCY_VERIFICATION_MODE", None)
        else:
            os.environ["DEPENDENCY_VERIFICATION_MODE"] = old_val


# ===== NEW TESTS: Improved Verification Detection =====


def test_word_boundary_verification_detection():
    """Verification commands should be detected with word boundaries."""
    # Should allow (word boundary matches)
    exit_code, output = run_hook("Bash", "npm view @scope/package")
    assert exit_code == 0, f"Expected exit code 0 for npm view, got {exit_code}: {output}"

    # Should allow (word boundary matches)
    exit_code, output = run_hook("Bash", "npm search package-name")
    assert exit_code == 0, f"Expected exit code 0 for npm search, got {exit_code}: {output}"


def test_hyphenated_command_not_verification():
    """Hyphenated commands should NOT be detected as verification."""
    # Should block (npm-view-package is not a verification command)
    exit_code, output = run_hook("Bash", "npm install npm-view-package")
    assert exit_code == 2, f"Expected exit code 2 for hyphenated package, got {exit_code}: {output}"


# ===== NEW TESTS: Autonomous Recovery Message Format =====


def test_autonomous_recovery_message_format_npm():
    """Blocked npm install should include autonomous recovery guidance."""
    exit_code, output = run_hook("Bash", "npm install test-package")
    assert exit_code == 2, f"Expected exit code 2, got {exit_code}"

    # Parse JSON output
    try:
        result = json.loads(output)
        assert result.get("decision") == "block", "Expected decision: block"
        assert result.get("continue") == False, "Expected continue: false"
        assert "autonomous_recovery" in result, "Missing autonomous_recovery field"
        assert result.get("autonomous_recovery") == True, "Expected autonomous_recovery: true"
        assert "next_action" in result, "Missing next_action field"
        assert (
            result.get("next_action") == "npm view test-package"
        ), f"Expected next_action='npm view test-package', got {result.get('next_action')}"

        # Check message content
        reason = result.get("reason", "")
        assert "You can continue" in reason, "Message should include continuation guidance"
        assert "Verify package exists" in reason, "Message should include verification actions"
        assert "npm view test-package" in reason, "Message should include verification command"
    except json.JSONDecodeError:
        # If not JSON, check for key phrases in plain text
        assert (
            "You CAN Continue" in output or "CAN Continue" in output
        ), "Message should indicate LLM can continue"
        assert (
            "npm view test-package" in output or "verify" in output.lower()
        ), "Message should include verification guidance"


def test_autonomous_recovery_message_format_pip():
    """Blocked pip install should include autonomous recovery guidance."""
    exit_code, output = run_hook("Bash", "pip install requests")
    assert exit_code == 2, f"Expected exit code 2, got {exit_code}"

    # Parse JSON output
    try:
        result = json.loads(output)
        assert result.get("decision") == "block", "Expected decision: block"
        assert result.get("autonomous_recovery") == True, "Expected autonomous_recovery: true"
        assert "next_action" in result, "Missing next_action field"
        assert (
            result.get("next_action") == "pip index versions requests"
        ), f"Expected pip verification command, got {result.get('next_action')}"
    except json.JSONDecodeError:
        # If not JSON, check for key phrases
        assert (
            "You CAN Continue" in output or "CAN Continue" in output
        ), "Message should indicate LLM can continue"


def test_autonomous_recovery_message_format_cargo():
    """Blocked cargo add should include autonomous recovery guidance."""
    exit_code, output = run_hook("Bash", "cargo add tokio")
    assert exit_code == 2, f"Expected exit code 2, got {exit_code}"

    # Parse JSON output
    try:
        result = json.loads(output)
        assert result.get("decision") == "block", "Expected decision: block"
        assert result.get("autonomous_recovery") == True, "Expected autonomous_recovery: true"
        assert "next_action" in result, "Missing next_action field"
        assert (
            result.get("next_action") == "cargo search tokio"
        ), f"Expected cargo verification command, got {result.get('next_action')}"
    except json.JSONDecodeError:
        # If not JSON, check for key phrases
        assert (
            "You CAN Continue" in output or "CAN Continue" in output
        ), "Message should indicate LLM can continue"


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
