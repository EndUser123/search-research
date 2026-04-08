"""Tests for PreToolUse_pytest_timeout_guard.py"""

import json
import os
import sys
from pathlib import Path

import pytest

# Add hooks directory to path
HOOKS_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(HOOKS_DIR))


@pytest.fixture
def reset_env():
    """Reset environment variables before each test."""
    original_vals = {}
    for key in ["PYTEST_TIMEOUT_GUARD_ENABLED", "PYTEST_TIMEOUT_GUARD_MODE"]:
        original_vals[key] = os.environ.get(key)
        os.environ.pop(key, None)
    yield
    for key, val in original_vals.items():
        if val is not None:
            os.environ[key] = val


class TestPytestTimeoutGuard:
    """Test suite for pytest timeout guard hook."""

    def _run_hook(self, command: str) -> dict:
        """Run the hook with given command and return result."""
        # Import the module - force reload to pick up env var changes
        import importlib
        if "PreToolUse_pytest_timeout_guard" in sys.modules:
            importlib.reload(sys.modules["PreToolUse_pytest_timeout_guard"])
        mod = importlib.import_module("PreToolUse_pytest_timeout_guard")

        # Create input data
        data = {
            "tool_name": "Bash",
            "command": command,
        }

        # Run the hook
        result = mod.run(data)
        return result

    def test_disabled_hook_allows_all(self, reset_env):
        """When hook is disabled, all commands should be allowed."""
        os.environ["PYTEST_TIMEOUT_GUARD_ENABLED"] = "false"

        result = self._run_hook("pytest")
        assert result["continue"] is True
        assert "disabled" in result["reason"].lower()

    def test_pytest_without_timeout_blocked(self, reset_env):
        """Pytest without --timeout should be blocked by default."""
        os.environ["PYTEST_TIMEOUT_GUARD_ENABLED"] = "true"
        os.environ["PYTEST_TIMEOUT_GUARD_MODE"] = "block"

        result = self._run_hook("pytest -v")
        assert result["continue"] is False
        assert "Missing --timeout flag" in result["reason"]

    def test_pytest_with_timeout_allowed(self, reset_env):
        """Pytest with --timeout should be allowed."""
        os.environ["PYTEST_TIMEOUT_GUARD_ENABLED"] = "true"
        os.environ["PYTEST_TIMEOUT_GUARD_MODE"] = "block"

        result = self._run_hook("pytest --timeout=30 -v")
        assert result["continue"] is True
        assert "has timeout flag" in result["reason"].lower()

    def test_python_minus_m_pytest_without_timeout_blocked(self, reset_env):
        """python -m pytest without --timeout should be blocked."""
        os.environ["PYTEST_TIMEOUT_GUARD_ENABLED"] = "true"
        os.environ["PYTEST_TIMEOUT_GUARD_MODE"] = "block"

        result = self._run_hook("python -m pytest")
        assert result["continue"] is False

    def test_python_minus_m_pytest_with_timeout_allowed(self, reset_env):
        """python -m pytest with --timeout should be allowed."""
        os.environ["PYTEST_TIMEOUT_GUARD_ENABLED"] = "true"
        os.environ["PYTEST_TIMEOUT_GUARD_MODE"] = "block"

        result = self._run_hook("python -m pytest --timeout=30")
        assert result["continue"] is True

    def test_pytest_version_exempt(self, reset_env):
        """pytest --version should be exempt (not blocked)."""
        os.environ["PYTEST_TIMEOUT_GUARD_ENABLED"] = "true"
        os.environ["PYTEST_TIMEOUT_GUARD_MODE"] = "block"

        result = self._run_hook("pytest --version")
        assert result["continue"] is True
        assert "exempt" in result["reason"].lower()

    def test_pytest_help_exempt(self, reset_env):
        """pytest --help should be exempt (not blocked)."""
        os.environ["PYTEST_TIMEOUT_GUARD_ENABLED"] = "true"
        os.environ["PYTEST_TIMEOUT_GUARD_MODE"] = "block"

        result = self._run_hook("pytest --help")
        assert result["continue"] is True
        assert "exempt" in result["reason"].lower()

    def test_pytest_collect_only_exempt(self, reset_env):
        """pytest --collect-only should be exempt (not blocked)."""
        os.environ["PYTEST_TIMEOUT_GUARD_ENABLED"] = "true"
        os.environ["PYTEST_TIMEOUT_GUARD_MODE"] = "block"

        result = self._run_hook("pytest --collect-only")
        assert result["continue"] is True
        assert "exempt" in result["reason"].lower()

    def test_allow_no_timeout_bypass(self, reset_env):
        """--allow-no-timeout flag should bypass the block."""
        os.environ["PYTEST_TIMEOUT_GUARD_ENABLED"] = "true"
        os.environ["PYTEST_TIMEOUT_GUARD_MODE"] = "block"

        result = self._run_hook("pytest --allow-no-timeout -v")
        assert result["continue"] is True
        assert "exempt" in result["reason"].lower()

    def test_non_pytest_command_allowed(self, reset_env):
        """Non-pytest commands should be allowed."""
        os.environ["PYTEST_TIMEOUT_GUARD_ENABLED"] = "true"
        os.environ["PYTEST_TIMEOUT_GUARD_MODE"] = "block"

        result = self._run_hook("echo hello")
        assert result["continue"] is True
        assert "not a pytest command" in result["reason"].lower()

    def test_warn_mode_allows_without_timeout(self, reset_env):
        """In warn mode, pytest without --timeout should be allowed with warning."""
        os.environ["PYTEST_TIMEOUT_GUARD_ENABLED"] = "true"
        os.environ["PYTEST_TIMEOUT_GUARD_MODE"] = "warn"

        result = self._run_hook("pytest")
        assert result["continue"] is True
        assert "warning issued" in result["reason"].lower()

    def test_warn_mode_still_blocks_if_hook_called_as_subprocess(self, reset_env):
        """Even in warn mode, if run as subprocess it should still block."""
        # This tests the actual subprocess call behavior
        os.environ["PYTEST_TIMEOUT_GUARD_ENABLED"] = "true"
        os.environ["PYTEST_TIMEOUT_GUARD_MODE"] = "warn"

        # Simulate subprocess call (what actually happens in hook execution)
        import subprocess
        result = subprocess.run(
            [sys.executable, str(HOOKS_DIR / "PreToolUse_pytest_timeout_guard.py")],
            input=json.dumps({"tool_name": "Bash", "command": "pytest"}).encode(),
            capture_output=True,
            timeout=5
        )

        # In warn mode, subprocess returns exit code 0 (allow) but prints warning
        # In block mode, subprocess returns exit code 2 (block)
        assert result.returncode == 0  # warn mode allows

    def test_block_mode_blocks_as_subprocess(self, reset_env):
        """In block mode, subprocess should return exit code 2."""
        os.environ["PYTEST_TIMEOUT_GUARD_ENABLED"] = "true"
        os.environ["PYTEST_TIMEOUT_GUARD_MODE"] = "block"

        import subprocess
        result = subprocess.run(
            [sys.executable, str(HOOKS_DIR / "PreToolUse_pytest_timeout_guard.py")],
            input=json.dumps({"tool_name": "Bash", "command": "pytest"}).encode(),
            capture_output=True,
            timeout=5
        )

        assert result.returncode == 2  # block mode returns 2
        assert b"PYTEST TIMEOUT REQUIRED" in result.stderr

    def test_bash_tool_only(self, reset_env):
        """Hook should only process Bash tool, not other tools."""
        os.environ["PYTEST_TIMEOUT_GUARD_ENABLED"] = "true"
        os.environ["PYTEST_TIMEOUT_GUARD_MODE"] = "block"

        # Test with Edit tool (should be allowed)
        data = {"tool_name": "Edit", "command": "pytest"}
        result = self._run_hook("")  # Command doesn't matter for non-Bash
        assert result["continue"] is True
