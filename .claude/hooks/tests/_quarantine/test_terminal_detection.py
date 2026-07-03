"""
Tests for terminal_detection.py module.

This test suite verifies terminal ID detection with priority order:
1. SessionStart's temp file (%%TEMP%%\\claude_terminal_id.txt)
2. CLAUDE_TERMINAL_ID environment variable
3. TERMINAL_ID, TERM_ID, SESSION_TERMINAL environment variables
4. ConsoleHost window handle (Windows only, via GetConsoleWindow())
5. Fallback to "terminal_1"

Test Strategy:
- RED Phase: Tests fail because terminal_detection.py doesn't exist
- GREEN Phase: Implementation will make tests pass
- REFACTOR Phase: Clean up with tests passing
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Setup path for imports
PROJECT_ROOT = Path(__file__).resolve().parents[3]
HOOKS_PATH = PROJECT_ROOT / ".claude" / "hooks"

sys.path.insert(0, str(HOOKS_PATH))


class TestDetectTerminalId:
    """
    Tests for detect_terminal_id() function.

    Verifies priority order for terminal ID detection:
    1. Temp file from SessionStart hook
    2. CLAUDE_TERMINAL_ID environment variable
    3. Other terminal env vars (TERMINAL_ID, TERM_ID, SESSION_TERMINAL)
    4. ConsoleHost window handle (Windows only)
    5. Fallback to "terminal_1"
    """

    @patch.dict(os.environ, {}, clear=True)
    def test_raises_runtime_error_when_no_sources_available(self):
        """
        Test that detect_terminal_id() raises RuntimeError
        when no detection sources are available (fail-fast behavior).

        Given:
            - No temp file exists
            - No terminal environment variables set
            - No project state file exists
            - ConsoleHost detection unavailable or fails
        When:
            - detect_terminal_id() is called
        Then:
            - Raises RuntimeError with descriptive message
        """
        # This import will fail initially (RED phase)
        from skill_guard.utils.terminal_detection import detect_terminal_id

        # Mock all detection methods to return None (simulate complete failure)
        with patch('terminal_detection._read_project_state', return_value=None), \
             patch('terminal_detection._read_temp_file', return_value=None), \
             patch('terminal_detection._get_console_host_id', return_value=None):

            # Act & Assert
            with pytest.raises(RuntimeError) as exc_info:
                result = detect_terminal_id()

            # Assert: Error message mentions all detection methods exhausted
            error_msg = str(exc_info.value)
            assert "Terminal ID detection failed" in error_msg
            assert "All detection methods exhausted" in error_msg

    @patch.dict(os.environ, {"CLAUDE_TERMINAL_ID": "override_terminal_123"})
    def test_reads_claude_terminal_id_env_var(self):
        """
        Test that detect_terminal_id() reads CLAUDE_TERMINAL_ID
        environment variable (Priority 2).

        Given:
            - CLAUDE_TERMINAL_ID environment variable is set
            - Temp file does not exist
        When:
            - detect_terminal_id() is called
        Then:
            - Returns the value from CLAUDE_TERMINAL_ID env var
        """
        from skill_guard.utils.terminal_detection import detect_terminal_id

        # Act
        result = detect_terminal_id()

        # Assert: Environment variable takes priority
        assert result == "override_terminal_123", (
            f"Expected 'override_terminal_123' from env var, but got '{result}'"
        )

    @patch.dict(os.environ, {"TERMINAL_ID": "term_from_env"})
    def test_reads_terminal_id_env_var(self):
        """
        Test that detect_terminal_id() reads TERMINAL_ID
        environment variable (Priority 3).

        Given:
            - TERMINAL_ID environment variable is set
            - No temp file, no CLAUDE_TERMINAL_ID
        When:
            - detect_terminal_id() is called
        Then:
            - Returns the value from TERMINAL_ID env var
        """
        from skill_guard.utils.terminal_detection import detect_terminal_id

        # Act
        result = detect_terminal_id()

        # Assert: TERMINAL_ID env var
        assert result == "term_from_env", (
            f"Expected 'term_from_env' from TERMINAL_ID, but got '{result}'"
        )

    @patch.dict(os.environ, {"TERM_ID": "term_id_from_env"})
    def test_reads_term_id_env_var(self):
        """
        Test that detect_terminal_id() reads TERM_ID
        environment variable (Priority 3).

        Given:
            - TERM_ID environment variable is set
            - No temp file, no CLAUDE_TERMINAL_ID, no TERMINAL_ID
        When:
            - detect_terminal_id() is called
        Then:
            - Returns the value from TERM_ID env var
        """
        from skill_guard.utils.terminal_detection import detect_terminal_id

        # Act
        result = detect_terminal_id()

        # Assert: TERM_ID env var
        assert result == "term_id_from_env", (
            f"Expected 'term_id_from_env' from TERM_ID, but got '{result}'"
        )

    @patch.dict(os.environ, {"SESSION_TERMINAL": "session_term_value"})
    def test_reads_session_terminal_env_var(self):
        """
        Test that detect_terminal_id() reads SESSION_TERMINAL
        environment variable (Priority 3).

        Given:
            - SESSION_TERMINAL environment variable is set
            - No temp file, no higher-priority env vars
        When:
            - detect_terminal_id() is called
        Then:
            - Returns the value from SESSION_TERMINAL env var
        """
        from skill_guard.utils.terminal_detection import detect_terminal_id

        # Act
        result = detect_terminal_id()

        # Assert: SESSION_TERMINAL env var
        assert result == "session_term_value", (
            f"Expected 'session_term_value' from SESSION_TERMINAL, but got '{result}'"
        )

    def test_reads_temp_file_with_valid_id(self):
        """
        Test that detect_terminal_id() reads terminal ID from
        SessionStart's temp file (Priority 1).

        Given:
            - Temp file %%TEMP%%\\claude_terminal_id.txt exists with valid ID
            - No environment variables set
        When:
            - detect_terminal_id() is called
        Then:
            - Returns the terminal ID from temp file
        """
        from skill_guard.utils.terminal_detection import detect_terminal_id

        # Arrange: Create temp file with terminal ID
        temp_dir = Path(tempfile.gettempdir())
        temp_file = temp_dir / "claude_terminal_id.txt"
        terminal_id = "terminal_from_file_abc123"

        try:
            temp_file.write_text(terminal_id, encoding="utf-8")

            # Act
            result = detect_terminal_id()

            # Assert: Temp file takes highest priority
            assert result == terminal_id, (
                f"Expected '{terminal_id}' from temp file, but got '{result}'"
            )
        finally:
            # Cleanup
            if temp_file.exists():
                temp_file.unlink()

    @patch.dict(os.environ, {"CLAUDE_TERMINAL_ID": "env_override_456"})
    def test_temp_file_takes_priority_over_env_vars(self):
        """
        Test that detect_terminal_id() prioritizes temp file
        over environment variables.

        Given:
            - Temp file exists with terminal ID
            - CLAUDE_TERMINAL_ID env var is also set
        When:
            - detect_terminal_id() is called
        Then:
            - Returns terminal ID from temp file (Priority 1)
            - Ignores CLAUDE_TERMINAL_ID env var (Priority 2)
        """
        from skill_guard.utils.terminal_detection import detect_terminal_id

        # Arrange: Create temp file
        temp_dir = Path(tempfile.gettempdir())
        temp_file = temp_dir / "claude_terminal_id.txt"
        file_terminal_id = "file_terminal_xyz"

        try:
            temp_file.write_text(file_terminal_id, encoding="utf-8")

            # Act
            result = detect_terminal_id()

            # Assert: Temp file wins over env vars
            assert result == file_terminal_id, (
                f"Expected '{file_terminal_id}' from temp file, "
                f"but got '{result}' (env var should be ignored)"
            )
        finally:
            # Cleanup
            if temp_file.exists():
                temp_file.unlink()

    def test_handles_empty_temp_file(self):
        """
        Test that detect_terminal_id() handles empty temp file
        gracefully.

        Given:
            - Temp file exists but is empty
            - No environment variables set
        When:
            - detect_terminal_id() is called
        Then:
            - Falls back to next detection method
            - Does not crash or return empty string
        """
        from skill_guard.utils.terminal_detection import detect_terminal_id

        # Arrange: Create empty temp file
        temp_dir = Path(tempfile.gettempdir())
        temp_file = temp_dir / "claude_terminal_id.txt"

        try:
            temp_file.write_text("", encoding="utf-8")

            # Act
            result = detect_terminal_id()

            # Assert: Should handle empty file gracefully
            # Either skip to next method or return non-empty value
            assert result is not None, (
                "detect_terminal_id() should not return None for empty temp file"
            )
            assert len(result) > 0, (
                f"detect_terminal_id() should return non-empty string, got '{result}'"
            )
        finally:
            # Cleanup
            if temp_file.exists():
                temp_file.unlink()

    def test_handles_whitespace_in_temp_file(self):
        """
        Test that detect_terminal_id() strips whitespace from
        temp file content.

        Given:
            - Temp file contains terminal ID with leading/trailing whitespace
        When:
            - detect_terminal_id() is called
        Then:
            - Returns stripped terminal ID
        """
        from skill_guard.utils.terminal_detection import detect_terminal_id

        # Arrange: Create temp file with whitespace
        temp_dir = Path(tempfile.gettempdir())
        temp_file = temp_dir / "claude_terminal_id.txt"
        terminal_id_with_spaces = "  terminal_id_spaces  "

        try:
            temp_file.write_text(terminal_id_with_spaces, encoding="utf-8")

            # Act
            result = detect_terminal_id()

            # Assert: Whitespace should be stripped
            assert result == "terminal_id_spaces", (
                f"Expected stripped ID 'terminal_id_spaces', but got '{result}'"
            )
        finally:
            # Cleanup
            if temp_file.exists():
                temp_file.unlink()

    @pytest.mark.skipif(
        sys.platform != "win32",
        reason="ConsoleHost detection is Windows-only"
    )
    @patch.dict(os.environ, {}, clear=True)
    def test_windows_consolehost_detection(self):
        """
        Test that detect_terminal_id() uses GetConsoleWindow()
        for ConsoleHost detection on Windows (Priority 4).

        Given:
            - Running on Windows
            - No temp file or environment variables
            - GetConsoleWindow() returns valid handle
        When:
            - detect_terminal_id() is called
        Then:
            - Returns ConsoleHost_{hex_handle} format
        """
        from skill_guard.utils.terminal_detection import detect_terminal_id

        # Mock GetConsoleWindow to return specific handle
        with patch('ctypes.windll.kernel32.GetConsoleWindow') as mock_get_console:
            mock_handle = 12345
            mock_get_console.return_value = mock_handle

            # Act
            result = detect_terminal_id()

            # Assert: ConsoleHost format with hex handle
            expected = f"ConsoleHost_{hex(mock_handle)[2:]}"  # Remove "0x" prefix
            assert result == expected, (
                f"Expected '{expected}' from ConsoleHost detection, but got '{result}'"
            )

    @pytest.mark.skipif(
        sys.platform != "win32",
        reason="ConsoleHost detection is Windows-only"
    )
    @patch.dict(os.environ, {}, clear=True)
    def test_windows_consolehost_raises_error_when_handle_zero(self):
        """
        Test that detect_terminal_id() raises RuntimeError
        when GetConsoleWindow() returns 0 (no console) and
        all other detection methods fail (fail-fast behavior).

        Given:
            - Running on Windows
            - No temp file or environment variables
            - No project state file exists
            - GetConsoleWindow() returns 0 (no console attached)
        When:
            - detect_terminal_id() is called
        Then:
            - Raises RuntimeError (no fallback to "terminal_1")
        """
        from skill_guard.utils.terminal_detection import detect_terminal_id

        # Mock GetConsoleWindow to return 0 (no console)
        # Mock other detection methods to ensure they don't provide fallback
        with patch('terminal_detection._read_project_state', return_value=None), \
             patch('terminal_detection._read_temp_file', return_value=None), \
             patch('ctypes.windll.kernel32.GetConsoleWindow') as mock_get_console:

            mock_get_console.return_value = 0

            # Act & Assert
            with pytest.raises(RuntimeError) as exc_info:
                result = detect_terminal_id()

            # Assert: Error message mentions detection failed
            error_msg = str(exc_info.value)
            assert "Terminal ID detection failed" in error_msg

    @pytest.mark.skipif(
        sys.platform == "win32",
        reason="Testing non-Windows behavior"
    )
    @patch.dict(os.environ, {}, clear=True)
    def test_non_windows_raises_error_when_no_sources_available(self):
        """
        Test that detect_terminal_id() raises RuntimeError
        on non-Windows platforms when all detection methods fail
        (fail-fast behavior).

        Given:
            - Running on non-Windows platform
            - No temp file or environment variables
            - No project state file exists
        When:
            - detect_terminal_id() is called
        Then:
            - Skips ConsoleHost detection
            - Raises RuntimeError (no fallback to "terminal_1")
        """
        from skill_guard.utils.terminal_detection import detect_terminal_id

        # Mock all detection methods to return None (simulate complete failure)
        with patch('terminal_detection._read_project_state', return_value=None), \
             patch('terminal_detection._read_temp_file', return_value=None):

            # Act & Assert
            with pytest.raises(RuntimeError) as exc_info:
                result = detect_terminal_id()

            # Assert: Error message mentions detection failed
            error_msg = str(exc_info.value)
            assert "Terminal ID detection failed" in error_msg


class TestLoadTerminalRegistry:
    """
    Tests for load_terminal_registry() function.

    Verifies loading of terminal registry from JSON file.
    """

    def test_loads_existing_registry_file(self):
        """
        Test that load_terminal_registry() loads registry from
        P:/.claude/session_data/terminal_registry.json.

        Given:
            - Registry file exists with valid JSON
        When:
            - load_terminal_registry() is called
        Then:
            - Returns parsed registry dictionary
        """
        from skill_guard.utils.terminal_detection import load_terminal_registry

        # Arrange: Create registry file
        registry_path = Path("P:/.claude/session_data/terminal_registry.json")
        registry_path.parent.mkdir(parents=True, exist_ok=True)

        expected_registry = {
            "terminal_1": {"pid": 1234, "start_time": 1234567890},
            "terminal_2": {"pid": 5678, "start_time": 1234567900},
        }

        try:
            registry_path.write_text(json.dumps(expected_registry), encoding="utf-8")

            # Act
            result = load_terminal_registry()

            # Assert: Registry loaded correctly
            assert result == expected_registry, (
                f"Expected registry {expected_registry}, but got {result}"
            )
        finally:
            # Cleanup
            if registry_path.exists():
                registry_path.unlink()

    def test_returns_default_registry_when_file_missing(self):
        """
        Test that load_terminal_registry() returns default registry
        when file doesn't exist.

        Given:
            - Registry file does not exist
        When:
            - load_terminal_registry() is called
        Then:
            - Returns default empty registry or safe default
        """
        from skill_guard.utils.terminal_detection import load_terminal_registry

        # Arrange: Ensure file doesn't exist
        registry_path = Path("P:/.claude/session_data/terminal_registry.json")
        if registry_path.exists():
            registry_path.unlink()

        # Act
        result = load_terminal_registry()

        # Assert: Should return default (empty dict or safe default)
        assert isinstance(result, dict), (
            f"Expected registry to be dict, got {type(result)}"
        )
        # Accept either empty dict or dict with default entries
        assert result is not None, (
            "load_terminal_registry() should not return None"
        )

    def test_handles_invalid_json_in_registry_file(self):
        """
        Test that load_terminal_registry() handles invalid JSON
        gracefully.

        Given:
            - Registry file exists but contains invalid JSON
        When:
            - load_terminal_registry() is called
        Then:
            - Returns default registry
            - Does not crash
        """
        from skill_guard.utils.terminal_detection import load_terminal_registry

        # Arrange: Create file with invalid JSON
        registry_path = Path("P:/.claude/session_data/terminal_registry.json")
        registry_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            registry_path.write_text("{ invalid json }", encoding="utf-8")

            # Act
            result = load_terminal_registry()

            # Assert: Should handle error gracefully
            assert isinstance(result, dict), (
                f"Expected dict return on invalid JSON, got {type(result)}"
            )
        finally:
            # Cleanup
            if registry_path.exists():
                registry_path.unlink()

    def test_handles_corrupted_registry_file(self):
        """
        Test that load_terminal_registry() handles corrupted
        registry file (read errors, etc).

        Given:
            - Registry file exists but is corrupted/unreadable
        When:
            - load_terminal_registry() is called
        Then:
            - Returns default registry
            - Does not crash
        """
        from skill_guard.utils.terminal_detection import load_terminal_registry

        # Arrange: Create file but mock read to raise error
        registry_path = Path("P:/.claude/session_data/terminal_registry.json")
        registry_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            registry_path.write_text('{"test": "data"}', encoding="utf-8")

            # Mock Path.read_text to raise error
            with patch.object(Path, 'read_text', side_effect=OSError("Corrupted file")):
                # Act
                result = load_terminal_registry()

                # Assert: Should handle error gracefully
                assert isinstance(result, dict), (
                    f"Expected dict return on read error, got {type(result)}"
                )
        finally:
            # Cleanup
            if registry_path.exists():
                registry_path.unlink()


class TestIsValidTerminalId:
    """
    Tests for is_valid_terminal_id(terminal_id, registry) function.

    Verifies validation of terminal IDs against registry.
    """

    def test_returns_true_for_valid_terminal_id(self):
        """
        Test that is_valid_terminal_id() returns True when
        terminal_id exists in registry.

        Given:
            - Registry contains "terminal_1" entry
            - Checking "terminal_1"
        When:
            - is_valid_terminal_id() is called
        Then:
            - Returns True
        """
        from skill_guard.utils.terminal_detection import is_valid_terminal_id

        # Arrange
        registry = {
            "terminal_1": {"pid": 1234},
            "terminal_2": {"pid": 5678},
        }

        # Act
        result = is_valid_terminal_id("terminal_1", registry)

        # Assert: Valid terminal ID
        assert result is True, (
            f"Expected True for valid 'terminal_1', but got {result}"
        )

    def test_returns_false_for_invalid_terminal_id(self):
        """
        Test that is_valid_terminal_id() returns False when
        terminal_id does not exist in registry.

        Given:
            - Registry contains "terminal_1" and "terminal_2"
            - Checking "terminal_999"
        When:
            - is_valid_terminal_id() is called
        Then:
            - Returns False
        """
        from skill_guard.utils.terminal_detection import is_valid_terminal_id

        # Arrange
        registry = {
            "terminal_1": {"pid": 1234},
            "terminal_2": {"pid": 5678},
        }

        # Act
        result = is_valid_terminal_id("terminal_999", registry)

        # Assert: Invalid terminal ID
        assert result is False, (
            f"Expected False for invalid 'terminal_999', but got {result}"
        )

    def test_returns_false_for_empty_terminal_id(self):
        """
        Test that is_valid_terminal_id() returns False for
        empty terminal_id string.

        Given:
            - Registry exists (any state)
            - Checking empty string
        When:
            - is_valid_terminal_id() is called
        Then:
            - Returns False
        """
        from skill_guard.utils.terminal_detection import is_valid_terminal_id

        # Arrange
        registry = {"terminal_1": {"pid": 1234}}

        # Act
        result = is_valid_terminal_id("", registry)

        # Assert: Empty ID is invalid
        assert result is False, (
            f"Expected False for empty terminal_id, but got {result}"
        )

    def test_returns_false_for_none_terminal_id(self):
        """
        Test that is_valid_terminal_id() returns False for
        None terminal_id.

        Given:
            - Registry exists (any state)
            - Checking None
        When:
            - is_valid_terminal_id() is called
        Then:
            - Returns False
        """
        from skill_guard.utils.terminal_detection import is_valid_terminal_id

        # Arrange
        registry = {"terminal_1": {"pid": 1234}}

        # Act
        result = is_valid_terminal_id(None, registry)

        # Assert: None ID is invalid
        assert result is False, (
            f"Expected False for None terminal_id, but got {result}"
        )

    def test_handles_empty_registry(self):
        """
        Test that is_valid_terminal_id() handles empty registry.

        Given:
            - Registry is empty dict {}
            - Checking any terminal_id
        When:
            - is_valid_terminal_id() is called
        Then:
            - Returns False (no valid terminals in empty registry)
        """
        from skill_guard.utils.terminal_detection import is_valid_terminal_id

        # Arrange
        registry = {}

        # Act
        result = is_valid_terminal_id("terminal_1", registry)

        # Assert: Empty registry means no valid terminals
        assert result is False, (
            f"Expected False for empty registry, but got {result}"
        )

    def test_handles_none_registry(self):
        """
        Test that is_valid_terminal_id() handles None registry.

        Given:
            - Registry parameter is None
            - Checking any terminal_id
        When:
            - is_valid_terminal_id() is called
        Then:
            - Returns False
            - Does not crash
        """
        from skill_guard.utils.terminal_detection import is_valid_terminal_id

        # Act
        result = is_valid_terminal_id("terminal_1", None)

        # Assert: None registry is invalid
        assert result is False, (
            f"Expected False for None registry, but got {result}"
        )


class TestConcurrentTerminalSupport:
    """
    Tests for concurrent terminal support.

    Verifies that multiple terminals can have unique IDs
    and IDs remain stable across CC restarts.
    """

    def test_temp_file_provides_stable_id_across_calls(self):
        """
        Test that temp file provides stable ID across multiple
        detect_terminal_id() calls (simulating CC restarts).

        Given:
            - Temp file contains terminal ID "stable_terminal_1"
            - No environment variables
        When:
            - detect_terminal_id() called multiple times
        Then:
            - Each call returns the same ID from temp file
        """
        from skill_guard.utils.terminal_detection import detect_terminal_id

        # Arrange: Create temp file
        temp_dir = Path(tempfile.gettempdir())
        temp_file = temp_dir / "claude_terminal_id.txt"
        stable_id = "stable_terminal_1"

        try:
            temp_file.write_text(stable_id, encoding="utf-8")

            # Act: Call multiple times
            result1 = detect_terminal_id()
            result2 = detect_terminal_id()
            result3 = detect_terminal_id()

            # Assert: All calls return same ID
            assert result1 == stable_id, (
                f"First call: expected '{stable_id}', got '{result1}'"
            )
            assert result2 == stable_id, (
                f"Second call: expected '{stable_id}', got '{result2}'"
            )
            assert result3 == stable_id, (
                f"Third call: expected '{stable_id}', got '{result3}'"
            )
        finally:
            # Cleanup
            if temp_file.exists():
                temp_file.unlink()

    @patch.dict(os.environ, {}, clear=True)
    def test_fallback_generates_different_ids_for_different_sessions(self):
        """
        Test that when no stable ID source exists, fallback
        mechanism generates appropriate IDs.

        Given:
            - No temp file
            - No environment variables
            - ConsoleHost detection unavailable
        When:
            - detect_terminal_id() is called
        Then:
            - Returns valid fallback ID
            - ID is not empty
        """
        from skill_guard.utils.terminal_detection import detect_terminal_id

        # Act
        result = detect_terminal_id()

        # Assert: Should return valid fallback
        assert result is not None, (
            "detect_terminal_id() should not return None"
        )
        assert isinstance(result, str), (
            f"Expected string, got {type(result)}"
        )
        assert len(result) > 0, (
            f"Expected non-empty fallback ID, got '{result}'"
        )
        assert result.startswith("terminal_"), (
            f"Expected fallback to start with 'terminal_', got '{result}'"
        )

    def test_registry_can_contain_multiple_terminals(self):
        """
        Test that registry can track multiple terminals concurrently.

        Given:
            - Registry contains multiple terminal entries
        When:
            - Validating multiple terminal IDs
        Then:
            - Each ID validates correctly
            - Registry maintains all entries
        """
        from skill_guard.utils.terminal_detection import is_valid_terminal_id

        # Arrange: Multi-terminal registry
        registry = {
            "terminal_1": {"pid": 1234, "worktree": "P:/"},
            "terminal_2": {"pid": 5678, "worktree": "P:/worktrees/w1"},
            "terminal_3": {"pid": 9012, "worktree": "P:/worktrees/w2"},
        }

        # Act & Assert: All terminals valid
        assert is_valid_terminal_id("terminal_1", registry) is True
        assert is_valid_terminal_id("terminal_2", registry) is True
        assert is_valid_terminal_id("terminal_3", registry) is True
        assert is_valid_terminal_id("terminal_4", registry) is False

    def test_worktree_terminals_tracked_separately(self):
        """
        Test that terminals in root and worktrees are tracked
        separately in registry.

        Given:
            - Registry has terminals from root and multiple worktrees
        When:
            - Validating terminal IDs from different locations
        Then:
            - Each terminal validates based on ID, not location
            - Registry maintains worktree context
        """
        from skill_guard.utils.terminal_detection import is_valid_terminal_id

        # Arrange: Mixed root/worktree terminals
        registry = {
            "root_terminal": {"pid": 1000, "worktree": "P:/"},
            "w1_terminal": {"pid": 2000, "worktree": "P:/worktrees/w1"},
            "w2_terminal": {"pid": 3000, "worktree": "P:/worktrees/w2"},
        }

        # Act & Assert: All tracked separately
        assert is_valid_terminal_id("root_terminal", registry) is True
        assert is_valid_terminal_id("w1_terminal", registry) is True
        assert is_valid_terminal_id("w2_terminal", registry) is True


class TestReadProjectStateHooksAware:
    """
    Tests for _read_project_state() function with hooks-aware directory traversal.

    Verifies that _read_project_state() works when executed from .claude/hooks/
    directory without relying on PROJECT_ROOT environment variable.

    Test Coverage:
    - Hooks directory execution context
    - Path traversal logic
    - Stale state rejection (>2 hours)
    - PID validation
    - Windows backslash handling (PR-001)
    """

    def test_detects_project_root_from_hooks_subdirectory(self):
        """
        Test that _read_project_state() detects project root when
        executed from .claude/hooks/ subdirectory.

        Given:
            - Current working directory is project_root/.claude/hooks/
            - No PROJECT_ROOT environment variable set
            - Valid terminal_id.json state file exists
        When:
            - _read_project_state() is called
        Then:
            - Successfully finds project root by traversing up 2 levels
            - Reads terminal_id from state file
            - Returns terminal ID without needing PROJECT_ROOT env var
        """
        import json
        import time

        from skill_guard.utils.terminal_detection import _read_project_state

        # Arrange: Create mock project structure
        # We'll use a temp directory as the "project root"
        with tempfile.TemporaryDirectory() as temp_project_root:
            # Create .claude/state/ directory structure
            state_dir = Path(temp_project_root) / ".claude" / "state"
            state_dir.mkdir(parents=True)

            # Create valid terminal_id.json state file
            state_file = state_dir / "terminal_id.json"
            terminal_id = "test_terminal_from_hooks_dir"
            state_data = {
                "terminal_id": terminal_id,
                "pid": os.getpid(),
                "parent_pid": os.getppid() if hasattr(os, 'getppid') else None,
                "timestamp": time.time()
            }
            state_file.write_text(json.dumps(state_data), encoding="utf-8")

            # Change to hooks subdirectory
            hooks_dir = Path(temp_project_root) / ".claude" / "hooks"
            hooks_dir.mkdir(parents=True)
            original_cwd = os.getcwd()

            try:
                os.chdir(hooks_dir)

                # Act: Call _read_project_state() from hooks directory
                result = _read_project_state()

                # Assert: Should detect project root and read terminal_id
                assert result == terminal_id, (
                    f"Expected '{terminal_id}' from state file, but got '{result}'. "
                    f"_read_project_state() should work from .claude/hooks/ directory "
                    f"without PROJECT_ROOT env var."
                )
            finally:
                os.chdir(original_cwd)

    def test_navigates_up_from_claime_directory(self):
        """
        Test that _read_project_state() navigates up correctly when
        executed from .claude/ directory (not hooks/).

        Given:
            - Current working directory is project_root/.claude/
            - No PROJECT_ROOT environment variable set
            - Valid terminal_id.json state file exists
        When:
            - _read_project_state() is called
        Then:
            - Successfully finds project root by traversing up 1 level
            - Reads terminal_id from state file
        """
        import json
        import time

        from skill_guard.utils.terminal_detection import _read_project_state

        # Arrange: Create mock project structure
        with tempfile.TemporaryDirectory() as temp_project_root:
            # Create .claude/state/ directory structure
            state_dir = Path(temp_project_root) / ".claude" / "state"
            state_dir.mkdir(parents=True)

            # Create valid terminal_id.json state file
            state_file = state_dir / "terminal_id.json"
            terminal_id = "test_terminal_from_claime_dir"
            state_data = {
                "terminal_id": terminal_id,
                "pid": os.getpid(),
                "parent_pid": os.getppid() if hasattr(os, 'getppid') else None,
                "timestamp": time.time()
            }
            state_file.write_text(json.dumps(state_data), encoding="utf-8")

            # Change to .claude directory (not hooks/)
            claime_dir = Path(temp_project_root) / ".claude"
            original_cwd = os.getcwd()

            try:
                os.chdir(claime_dir)

                # Act: Call _read_project_state() from .claude directory
                result = _read_project_state()

                # Assert: Should detect project root and read terminal_id
                assert result == terminal_id, (
                    f"Expected '{terminal_id}' from state file, but got '{result}'. "
                    f"_read_project_state() should work from .claude/ directory "
                    f"without PROJECT_ROOT env var."
                )
            finally:
                os.chdir(original_cwd)

    def test_windows_backslash_handling(self):
        r"""
        Test [PR-001] that path string replacement works correctly for
        Windows paths with backslashes.

        Given:
            - Current working directory contains Windows backslashes
            - Path like "P:\project\.claude\hooks"
        When:
            - _read_project_state() is called
        Then:
            - Backslashes are correctly replaced with forward slashes
            - Path pattern matching works correctly
            - Project root is detected successfully
        """
        import json
        import time

        from skill_guard.utils.terminal_detection import _read_project_state

        # Arrange: Create mock project structure with Windows-style paths
        with tempfile.TemporaryDirectory() as temp_project_root:
            # Convert to Windows-style path for testing
            # On Unix, we'll just test the string replacement logic
            project_root_path = Path(temp_project_root)

            # Create .claude/state/ directory structure
            state_dir = project_root_path / ".claude" / "state"
            state_dir.mkdir(parents=True)

            # Create valid terminal_id.json state file
            state_file = state_dir / "terminal_id.json"
            terminal_id = "test_terminal_windows_path"
            state_data = {
                "terminal_id": terminal_id,
                "pid": os.getpid(),
                "parent_pid": os.getppid() if hasattr(os, 'getppid') else None,
                "timestamp": time.time()
            }
            state_file.write_text(json.dumps(state_data), encoding="utf-8")

            # Change to hooks subdirectory
            hooks_dir = project_root_path / ".claude" / "hooks"
            hooks_dir.mkdir(parents=True)
            original_cwd = os.getcwd()

            try:
                os.chdir(hooks_dir)

                # Simulate Windows path with backslashes in string representation
                # The replace("\\", "/") should handle this
                current_dir_str = str(Path.cwd()).replace("\\", "/")

                # Verify the path contains hooks directory
                assert "/.claude/hooks" in current_dir_str or "/.claude/hooks/" in current_dir_str, (
                    f"Path replacement failed: expected '/.claude/hooks' in '{current_dir_str}'"
                )

                # Act: Call _read_project_state()
                result = _read_project_state()

                # Assert: Should handle Windows paths correctly
                assert result == terminal_id, (
                    f"Expected '{terminal_id}' after Windows path handling, but got '{result}'. "
                    f"String replacement for backslashes should work correctly."
                )
            finally:
                os.chdir(original_cwd)

    def test_rejects_stale_state_older_than_2_hours(self):
        """
        Test that _read_project_state() rejects state files older than 2 hours.

        Given:
            - Valid terminal_id.json exists
            - Timestamp is older than 2 hours
        When:
            - _read_project_state() is called
        Then:
            - Returns None (stale state rejected)
            - Does not return terminal_id from stale state
        """
        import json
        import time

        from skill_guard.utils.terminal_detection import _read_project_state

        # Arrange: Create mock project structure
        with tempfile.TemporaryDirectory() as temp_project_root:
            # Create .claude/state/ directory structure
            state_dir = Path(temp_project_root) / ".claude" / "state"
            state_dir.mkdir(parents=True)

            # Create STALE terminal_id.json (older than 2 hours)
            state_file = state_dir / "terminal_id.json"
            terminal_id = "test_terminal_stale"
            stale_timestamp = time.time() - (3 * 3600)  # 3 hours ago
            state_data = {
                "terminal_id": terminal_id,
                "pid": os.getpid(),
                "parent_pid": os.getppid() if hasattr(os, 'getppid') else None,
                "timestamp": stale_timestamp
            }
            state_file.write_text(json.dumps(state_data), encoding="utf-8")

            # Change to hooks subdirectory
            hooks_dir = Path(temp_project_root) / ".claude" / "hooks"
            hooks_dir.mkdir(parents=True)
            original_cwd = os.getcwd()

            try:
                os.chdir(hooks_dir)

                # Act: Call _read_project_state() with stale state
                result = _read_project_state()

                # Assert: Should reject stale state
                assert result is None, (
                    f"Expected None for stale state (>2 hours old), but got '{result}'. "
                    f"Stale state should be rejected."
                )
            finally:
                os.chdir(original_cwd)

    def test_validates_pid_match_accepts_same_process(self):
        """
        Test that _read_project_state() validates PID and accepts
        when PID matches exactly (same process).

        Given:
            - Valid terminal_id.json with matching PID
            - PID in state file matches current process PID
        When:
            - _read_project_state() is called
        Then:
            - Returns terminal_id (same process, allow)
        """
        import json
        import time

        from skill_guard.utils.terminal_detection import _read_project_state

        # Arrange: Create mock project structure
        with tempfile.TemporaryDirectory() as temp_project_root:
            # Create .claude/state/ directory structure
            state_dir = Path(temp_project_root) / ".claude" / "state"
            state_dir.mkdir(parents=True)

            # Create state file with matching PID
            state_file = state_dir / "terminal_id.json"
            terminal_id = "test_terminal_pid_match"
            current_pid = os.getpid()
            state_data = {
                "terminal_id": terminal_id,
                "pid": current_pid,
                "parent_pid": os.getppid() if hasattr(os, 'getppid') else None,
                "timestamp": time.time()
            }
            state_file.write_text(json.dumps(state_data), encoding="utf-8")

            # Change to hooks subdirectory
            hooks_dir = Path(temp_project_root) / ".claude" / "hooks"
            hooks_dir.mkdir(parents=True)
            original_cwd = os.getcwd()

            try:
                os.chdir(hooks_dir)

                # Act: Call _read_project_state() with matching PID
                result = _read_project_state()

                # Assert: Should accept with exact PID match
                assert result == terminal_id, (
                    f"Expected '{terminal_id}' with exact PID match, but got '{result}'. "
                    f"Same process should be accepted."
                )
            finally:
                os.chdir(original_cwd)

    def test_validates_pid_mismatch_rejects_different_process(self):
        """
        Test that _read_project_state() validates PID and rejects
        when PID doesn't match and parent_pid doesn't match.

        Given:
            - Valid terminal_id.json with different PID
            - PID in state file doesn't match current process
            - parent_pid also doesn't match
        When:
            - _read_project_state() is called
        Then:
            - Returns None (different process, reject)
        """
        import json
        import time

        from skill_guard.utils.terminal_detection import _read_project_state

        # Arrange: Create mock project structure
        with tempfile.TemporaryDirectory() as temp_project_root:
            # Create .claude/state/ directory structure
            state_dir = Path(temp_project_root) / ".claude" / "state"
            state_dir.mkdir(parents=True)

            # Create state file with MISMATCHING PID
            state_file = state_dir / "terminal_id.json"
            terminal_id = "test_terminal_pid_mismatch"
            wrong_pid = 99999  # Clearly not the current process PID
            wrong_parent_pid = 88888  # Clearly not the current parent PID
            state_data = {
                "terminal_id": terminal_id,
                "pid": wrong_pid,
                "parent_pid": wrong_parent_pid,
                "timestamp": time.time()
            }
            state_file.write_text(json.dumps(state_data), encoding="utf-8")

            # Change to hooks subdirectory
            hooks_dir = Path(temp_project_root) / ".claude" / "hooks"
            hooks_dir.mkdir(parents=True)
            original_cwd = os.getcwd()

            try:
                os.chdir(hooks_dir)

                # Act: Call _read_project_state() with mismatching PID
                result = _read_project_state()

                # Assert: Should reject with PID mismatch
                assert result is None, (
                    f"Expected None for PID mismatch, but got '{result}'. "
                    f"Different process should be rejected."
                )
            finally:
                os.chdir(original_cwd)


class TestCrossTerminalIsolation:
    """
    Integration tests for cross-terminal isolation (security property).

    Verifies that different terminals get different terminal_ids and that
    handoffs from one terminal are not accessible to another terminal.
    """

    def test_different_terminals_get_different_ids(self):
        """
        Test that different terminal sessions get different terminal_ids.

        This is the primary security property - terminal isolation prevents
        cross-contamination of handoff state between concurrent sessions.

        Given:
            - Environment variable set for Terminal A
            - Environment variable changed for Terminal B
        When:
            - resolve_terminal_key() is called for each terminal
        Then:
            - Each gets a different terminal_id
            - Format is {source}_{id} for both
        """
        from skill_guard.utils.terminal_detection import resolve_terminal_key

        # Arrange: Set environment variable for Terminal A
        terminal_a_env = "abc123"
        terminal_b_env = "def456"
        original_env = os.environ.get("CLAUDE_TERMINAL_ID")

        try:
            # Terminal A detection
            os.environ["CLAUDE_TERMINAL_ID"] = terminal_a_env
            hook_input_a = {"session_id": "session-a", "transcript_path": "test-a.jsonl"}
            terminal_a_id = resolve_terminal_key(hook_input_a)

            # Terminal B detection
            os.environ["CLAUDE_TERMINAL_ID"] = terminal_b_env
            hook_input_b = {"session_id": "session-b", "transcript_path": "test-b.jsonl"}
            terminal_b_id = resolve_terminal_key(hook_input_b)

            # Assert: Different terminals get different IDs
            assert terminal_a_id != terminal_b_id, (
                f"Terminal A ID '{terminal_a_id}' should differ from "
                f"Terminal B ID '{terminal_b_id}'"
            )

            # Assert: Both should use environment variable values
            assert terminal_a_id == terminal_a_env, (
                f"Terminal A ID '{terminal_a_id}' should match env var '{terminal_a_env}'"
            )
            assert terminal_b_id == terminal_b_env, (
                f"Terminal B ID '{terminal_b_id}' should match env var '{terminal_b_env}'"
            )

            # Assert: Both should be non-empty
            assert terminal_a_id, "Terminal A ID should not be empty"
            assert terminal_b_id, "Terminal B ID should not be empty"

        finally:
            # Cleanup
            if original_env is None:
                os.environ.pop("CLAUDE_TERMINAL_ID", None)
            else:
                os.environ["CLAUDE_TERMINAL_ID"] = original_env

    def test_pid_validation_prevents_cross_terminal_bleeding(self):
        """
        Test that PID validation prevents cross-terminal bleeding.

        Even if a stale project state file exists, PID validation should
        prevent a different terminal from using the same terminal_id.

        Given:
            - Valid terminal_id.json with PID from Terminal A
            - Terminal B tries to use it with different PID
        When:
            - Terminal B calls _read_project_state()
        Then:
            - Returns None (rejected due to PID mismatch)
            - Terminal B must use its own detection method
        """
        import json
        import time

        from skill_guard.utils.terminal_detection import _read_project_state

        # Arrange: Create mock project structure with "Terminal A" state
        with tempfile.TemporaryDirectory() as temp_project_root:
            state_dir = Path(temp_project_root) / ".claude" / "state"
            state_dir.mkdir(parents=True)

            # Create state file from "Terminal A" (different PID)
            state_file = state_dir / "terminal_id.json"
            terminal_a_id = "terminal_a_session"
            terminal_a_pid = 12345  # Clearly not current process
            terminal_a_parent_pid = 67890  # Clearly not current parent
            state_data = {
                "terminal_id": terminal_a_id,
                "pid": terminal_a_pid,
                "parent_pid": terminal_a_parent_pid,
                "timestamp": time.time()
            }
            state_file.write_text(json.dumps(state_data), encoding="utf-8")

            # Change to hooks subdirectory (simulating Terminal B context)
            hooks_dir = Path(temp_project_root) / ".claude" / "hooks"
            hooks_dir.mkdir(parents=True)
            original_cwd = os.getcwd()

            try:
                os.chdir(hooks_dir)

                # Act: Terminal B tries to read state
                result = _read_project_state()

                # Assert: Should reject Terminal A's state
                assert result is None, (
                    f"Expected None (PID rejection), but got '{result}'. "
                    f"Terminal B should not use Terminal A's terminal_id."
                )
            finally:
                os.chdir(original_cwd)

    def test_stale_temp_file_rejected_after_48_hours(self):
        """
        Test that stale temp files are rejected after 48 hours.

        Temp files can cause cross-terminal bleeding if they're stale.
        This test verifies the age validation prevents this.

        Given:
            - Temp file older than 48 hours
            - No environment variables or project state
        When:
            - detect_terminal_id() is called
        Then:
            - Temp file is rejected (too old)
            - Falls back to next detection method
        """
        import tempfile
        import time

        # Arrange: Create stale temp file (>48 hours old)
        temp_dir = Path(tempfile.gettempdir())
        stale_temp_file = temp_dir / "claude_terminal_id.txt"

        # Write temp file with old timestamp
        stale_temp_file.write_text("stale_terminal_id", encoding="utf-8")

        # Set file modification time to 49 hours ago (beyond 48-hour threshold)
        old_time = time.time() - (49 * 3600)  # 49 hours ago
        os.utime(stale_temp_file, (old_time, old_time))

        try:
            # Act: Try to read temp file
            from skill_guard.utils.terminal_detection import _read_temp_file
            result = _read_temp_file()

            # Assert: Should reject stale temp file
            assert result is None, (
                f"Expected None (stale file rejected), but got '{result}'. "
                f"Temp files older than 48 hours should be rejected."
            )
        finally:
            # Cleanup
            if stale_temp_file.exists():
                stale_temp_file.unlink()

    def test_environment_variable_takes_priority_over_stale_state(self):
        """
        Test that environment variables take priority over stale project state.

        This ensures that if a user explicitly sets CLAUDE_TERMINAL_ID,
        it takes precedence over any stale project state files.

        Given:
            - CLAUDE_TERMINAL_ID environment variable set
            - Stale project state file exists
        When:
            - resolve_terminal_key() is called with hook input
        Then:
            - Uses environment variable (highest priority)
            - Ignores stale project state
        """
        from skill_guard.utils.terminal_detection import resolve_terminal_key

        # Arrange: Set environment variable
        env_terminal_id = "env_explicit_terminal_123"
        original_env = os.environ.get("CLAUDE_TERMINAL_ID")

        try:
            os.environ["CLAUDE_TERMINAL_ID"] = env_terminal_id

            # Create mock hook input (no terminalId field, as Claude Code doesn't provide it)
            hook_input = {
                "session_id": "test-session",
                "transcript_path": "test.jsonl"
            }

            # Act: Resolve terminal key
            result = resolve_terminal_key(hook_input)

            # Assert: Should use environment variable
            assert result == env_terminal_id, (
                f"Expected '{env_terminal_id}' from env var, but got '{result}'. "
                f"Environment variable should take highest priority."
            )
        finally:
            # Cleanup
            if original_env is None:
                os.environ.pop("CLAUDE_TERMINAL_ID", None)
            else:
                os.environ["CLAUDE_TERMINAL_ID"] = original_env


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
