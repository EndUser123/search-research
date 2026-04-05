"""
Tests for PreToolUse_bash_syntax_validator

Tests bash path syntax validation and Python -c code validation.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "__lib"))

from PreToolUse_bash_syntax_validator import (
    _extract_python_c_code,
    _normalize_shell_escaped_code,
    run,
    validate_bash_paths,
    validate_python_c,
)


class TestValidateBashPaths:
    """Test Windows path validation in bash commands."""

    def test_malformed_windows_path_missing_backslashes(self):
        """Should detect malformed Windows path (missing backslashes after drive)."""
        # Note: No backslashes at all in path (C:Usersbrsth...)
        command = 'python P:Usersbrsth.claudeskillsreflectreflect.py'
        is_valid, error = validate_bash_paths(command)
        assert is_valid is False
        assert "missing backslashes" in error.lower()
        assert "P:Usersbrsth.claudeskillsreflectreflect.py" in error

    def test_malformed_windows_path_users_missing_backslash(self):
        """Should detect C:Usersbrsth pattern (missing backslash after Users)."""
        # Note: No backslash after Users (C:Usersbrsth instead of C:\Users\brsth)
        command = "cat C:Usersbrsth.claude.state.file.json"
        is_valid, error = validate_bash_paths(command)
        assert is_valid is False
        assert "missing backslashes" in error.lower()

    def test_wellformed_windows_path_with_backslashes(self):
        """Should allow well-formed Windows paths."""
        # Note: Double backslashes in Python string = single backslash in actual string
        # So "\\\\" in Python source = "\" in the actual command string
        command = "cat C:\\\\Users\\\\brsth\\\\.claude\\\\state\\\\file.json"
        is_valid, error = validate_bash_paths(command)
        assert is_valid is True
        assert error is None

    def test_wellformed_windows_path_forward_slashes(self):
        """Should allow Windows paths with forward slashes (valid in bash)."""
        command = 'cat P:/__csf/skills/reflect/reflect.py'
        is_valid, error = validate_bash_paths(command)
        assert is_valid is True
        assert error is None

    def test_unix_path_allowed(self):
        """Should allow Unix-style paths."""
        command = 'cat /home/user/file.txt'
        is_valid, error = validate_bash_paths(command)
        assert is_valid is True
        assert error is None

    def test_no_path_allowed(self):
        """Should allow commands without paths."""
        command = 'echo "hello world"'
        is_valid, error = validate_bash_paths(command)
        assert is_valid is True
        assert error is None

    def test_drive_letter_only_allowed(self):
        """Should allow drive letter alone (e.g., "C:")."""
        command = 'cd C:'
        is_valid, error = validate_bash_paths(command)
        assert is_valid is True
        assert error is None

    def test_url_not_flagged_as_path(self):
        """Should not flag URLs as malformed paths."""
        command = 'curl https://example.com/file.txt'
        is_valid, error = validate_bash_paths(command)
        assert is_valid is True
        assert error is None

    def test_http_url_not_flagged(self):
        """Should not flag http:// URLs."""
        command = 'wget http://example.com/download'
        is_valid, error = validate_bash_paths(command)
        assert is_valid is True
        assert error is None


class TestExtractPythonCCode:
    """Test Python -c code extraction from bash commands."""

    def test_extract_python_c_code_double_quote(self):
        """Should extract python -c code with double quotes."""
        command = 'python -c "print(1 + 1)"'
        code, quote = _extract_python_c_code(command)
        assert code == "print(1 + 1)"
        assert quote == '"'

    def test_extract_python_c_code_single_quote(self):
        """Should extract python -c code with single quotes."""
        command = "python -c 'print(1 + 1)'"
        code, quote = _extract_python_c_code(command)
        assert code == "print(1 + 1)"
        assert quote == "'"

    def test_extract_python_c_code_python3(self):
        """Should extract python3 -c code."""
        command = 'python3 -c "import sys; print(sys.version)"'
        code, quote = _extract_python_c_code(command)
        assert code == "import sys; print(sys.version)"
        assert quote == '"'

    def test_extract_python_c_code_no_match(self):
        """Should return None, None for non-python -c commands."""
        command = 'echo "hello"'
        code, quote = _extract_python_c_code(command)
        assert code is None
        assert quote is None


class TestValidatePythonC:
    """Test Python -c code syntax validation."""

    def test_valid_python_code(self):
        """Should allow valid Python code."""
        code = "print(1 + 1)"
        result = validate_python_c(code, '"')
        assert result is None

    def test_invalid_python_syntax(self):
        """Should block invalid Python syntax."""
        code = "print(1 + "
        result = validate_python_c(code, '"')
        assert result is not None
        assert result["decision"] == "block"
        assert "syntax error" in result["message"].lower()

    def test_valid_python_with_import(self):
        """Should allow valid Python with imports."""
        code = "import sys; print(sys.version)"
        result = validate_python_c(code, '"')
        assert result is None

    def test_python_code_with_unclosed_string(self):
        """Should detect unclosed string in Python code."""
        code = 'print("hello world)'
        result = validate_python_c(code, '"')
        assert result is not None
        assert result["decision"] == "block"


class TestNormalizeShellEscapedCode:
    """Test shell-escaped code normalization."""

    def test_normalize_double_quotes(self):
        """Should normalize escaped double quotes."""
        code = 'print(\\"hello\\")'
        normalized = _normalize_shell_escaped_code(code, '"')
        assert normalized == 'print("hello")'

    def test_normalize_single_quotes(self):
        """Should normalize escaped single quotes."""
        code = "print(\\'hello\\')"
        normalized = _normalize_shell_escaped_code(code, "'")
        assert normalized == "print('hello')"

    def test_normalize_powerstyle_escape(self):
        """Should normalize PowerShell-style escape."""
        code = 'print(`"hello`")'
        normalized = _normalize_shell_escaped_code(code, '"')
        assert normalized == 'print("hello")'

    def test_normalize_newlines(self):
        """Should normalize CRLF to LF."""
        code = "print(1)\r\nprint(2)"
        normalized = _normalize_shell_escaped_code(code, '"')
        assert normalized == "print(1)\nprint(2)"


class TestRunIntegration:
    """Integration tests for run() function."""

    def test_non_bash_tool_returns_none(self):
        """Should allow non-Bash tools."""
        data = {"tool_name": "Write", "tool_input": {"file_path": "test.txt"}}
        result = run(data)
        assert result is None

    def test_empty_command_returns_none(self):
        """Should allow empty commands."""
        data = {"tool_name": "Bash", "tool_input": {"command": ""}}
        result = run(data)
        assert result is None

    def test_python_c_valid_code_returns_none(self):
        """Should allow valid Python -c code."""
        data = {"tool_name": "Bash", "tool_input": {"command": 'python -c "print(1 + 1)"'}}
        result = run(data)
        assert result is None

    def test_python_c_invalid_code_blocks_in_block_mode(self):
        """Should block invalid Python -c code in block mode."""
        import os
        old_mode = os.environ.get("BASH_SYNTAX_VALIDATOR_MODE")
        try:
            os.environ["BASH_SYNTAX_VALIDATOR_MODE"] = "block"
            data = {"tool_name": "Bash", "tool_input": {"command": 'python -c "print(1 + "'}}
            result = run(data)
            assert result is not None
            assert result["decision"] == "block"
        finally:
            if old_mode:
                os.environ["BASH_SYNTAX_VALIDATOR_MODE"] = old_mode
            else:
                os.environ.pop("BASH_SYNTAX_VALIDATOR_MODE", None)

    def test_malformed_path_blocks_in_block_mode(self):
        """Should block malformed Windows path in block mode."""
        import os
        old_mode = os.environ.get("BASH_SYNTAX_VALIDATOR_MODE")
        try:
            os.environ["BASH_SYNTAX_VALIDATOR_MODE"] = "block"
            # Note: No backslashes in malformed path
            data = {"tool_name": "Bash", "tool_input": {"command": "cat C:Usersbrsth.file.txt"}}
            result = run(data)
            assert result is not None
            assert result["decision"] == "block"
            assert "bash path syntax error" in result["message"].lower()
        finally:
            if old_mode:
                os.environ["BASH_SYNTAX_VALIDATOR_MODE"] = old_mode
            else:
                os.environ.pop("BASH_SYNTAX_VALIDATOR_MODE", None)

    def test_wellformed_path_allows(self):
        """Should normalize well-formed drive paths to shell-safe forward slashes."""
        # Note: Double backslashes in Python = single backslashes in actual command
        data = {"tool_name": "Bash", "tool_input": {"command": "cat C:\\\\Users\\\\brsth\\\\file.txt"}}
        result = run(data)
        assert result is not None
        assert result["decision"] == "modify"
        assert result["tool_input"]["command"] == "cat C:/Users/brsth/file.txt"

    def test_python_script_drive_path_returns_modify(self):
        """Should normalize drive-qualified Python script paths before execution."""
        data = {
            "tool_name": "Bash",
            "tool_input": {"command": 'python "P:\\.claude\\hooks\\PreToolUse.py"'},
        }
        result = run(data)
        assert result is not None
        assert result["decision"] == "modify"
        assert result["tool_input"]["command"] == 'python "P:/.claude/hooks/PreToolUse.py"'

    def test_missing_python_script_path_blocks(self):
        """Should block clearly missing Python script paths before Python executes."""
        data = {
            "tool_name": "Bash",
            "tool_input": {
                "command": 'python "P:\\.claude\\skills\\plan-workflow\\lib\\plan_builder.py"'
            },
        }
        result = run(data)
        assert result is not None
        assert result["decision"] == "block"
        assert "does not exist" in result["message"]
        assert "plan_builder.py" in result["message"]

    def test_relative_python_script_after_cd_is_not_preblocked(self):
        """Should not pre-block relative scripts when a prior cd changes runtime cwd."""
        data = {
            "tool_name": "Bash",
            "tool_input": {
                "command": "cd P:/.claude/hooks && python PreToolUse.py",
                "cwd": "P:/",
            },
        }
        result = run(data)
        assert result is None

    def test_create_then_run_python_script_is_not_preblocked(self):
        """Should not pre-block scripts that may be created earlier in the same shell command."""
        data = {
            "tool_name": "Bash",
            "tool_input": {
                "command": "cat > P:/.tmp/generated_demo.py <<'PY'\nprint(1)\nPY\npython P:/.tmp/generated_demo.py",
            },
        }
        result = run(data)
        assert result is None

    def test_hook_disabled_returns_none(self):
        """Should allow all commands when hook is disabled."""
        import os
        old_enabled = os.environ.get("BASH_SYNTAX_VALIDATOR_ENABLED")
        try:
            os.environ["BASH_SYNTAX_VALIDATOR_ENABLED"] = "false"
            # Note: Malformed path but hook is disabled
            data = {"tool_name": "Bash", "tool_input": {"command": "cat C:Usersbrsth.file.txt"}}
            result = run(data)
            assert result is None
        finally:
            if old_enabled:
                os.environ["BASH_SYNTAX_VALIDATOR_ENABLED"] = old_enabled
            else:
                os.environ.pop("BASH_SYNTAX_VALIDATOR_ENABLED", None)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
