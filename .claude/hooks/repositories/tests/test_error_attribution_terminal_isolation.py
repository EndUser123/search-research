"""Tests for ErrorAttributionTracker terminal isolation feature.

These tests verify terminal-specific state file handling for proper
isolation between concurrent terminal sessions.

This is a TDD RED phase test - tests verify DESIRED behavior that
does not yet exist in the implementation.

Run with:
    pytest P:/.claude/hooks/repositories/tests/test_error_attribution_terminal_isolation.py -v
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# ============================================================================
# SHARED FIXTURES
# ============================================================================

@pytest.fixture
def temp_state_dir():
    """Create a temporary directory for state files during testing.

    Yields:
        Path: Path to temporary state directory.

    Cleanup:
        Removes temporary directory after test completion.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        state_path = Path(tmpdir)
        yield state_path


@pytest.fixture
def error_tracker_with_temp_state(temp_state_dir):
    """Create ErrorAttributionTracker with STATE_FILE redirected to temp dir.

    This fixture patches the STATE_FILE constant in the module so that
    tests write to a temporary directory instead of the production location.

    Args:
        temp_state_dir: Path to temporary state directory.

    Returns:
        ErrorAttributionTracker: Instance with STATE_FILE redirected.
    """
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

    from posttooluse import error_attribution_tracker

    # Store original STATE_FILE
    original_state_file = error_attribution_tracker.STATE_FILE

    # Create temp state file path
    temp_state_file = temp_state_dir / "error_attribution.json"

    # Patch STATE_FILE at module level
    error_attribution_tracker.STATE_FILE = temp_state_file

    # Import and create tracker
    from posttooluse.error_attribution_tracker import ErrorAttributionTracker

    tracker = ErrorAttributionTracker()

    yield tracker, temp_state_dir

    # Restore original STATE_FILE
    error_attribution_tracker.STATE_FILE = original_state_file


@pytest.fixture
def sample_error_response():
    """Sample tool response containing an error with source attribution.

    Returns:
        dict: Tool response with error source pattern.
    """
    return {
        "output": "[python .claude/hooks/test_hook.py] error: Test error message"
    }


# ============================================================================
# TEST CLASSES
# ============================================================================

class TestTerminalIdStoredInState:
    """Tests for terminal_id being stored in state file.

    These tests verify that when ErrorAttributionTracker initializes,
    it imports and stores terminal_id from terminal_detection module.
    """

    def test_terminal_id_stored_in_state(
        self, error_tracker_with_temp_state, sample_error_response
    ) -> None:
        """Verify terminal_id is included in state dict when error detected.

        Given: ErrorAttributionTracker is initialized (which should call detect_terminal_id)
        When: An error with source attribution is detected and state is written
        Then: State file should contain "terminal_id" field with the detected value

        NOTE: This test FAILS in RED phase because the implementation does not
        yet import or store terminal_id.
        """
        # Arrange
        tracker, temp_dir = error_tracker_with_temp_state

        # Act - Process the error response
        result = tracker.process(
            tool_name="Bash",
            tool_input={"command": "echo test"},
            tool_response=sample_error_response
        )

        # Extract error info to trigger state write
        error_info = tracker._extract_error_source(sample_error_response["output"])
        tracker._write_state(error_info)

        # Assert - Check state file contains terminal_id
        # The state file should be at temp_dir/error_attribution.json
        # (or terminal-specific if implemented)
        state_files = list(temp_dir.glob("error_attribution*.json"))
        assert len(state_files) >= 1, "At least one state file should exist"

        state_data = json.loads(state_files[0].read_text())
        assert "terminal_id" in state_data, (
            "State should contain terminal_id field - FAILS because feature not implemented yet"
        )


class TestTerminalSpecificStateFile:
    """Tests for terminal-specific state file naming.

    These tests verify that when terminal_id is available, state is
    written to error_attribution_{terminal_id}.json instead of the
    default error_attribution.json.
    """

    def test_terminal_specific_state_file(
        self, error_tracker_with_temp_state, sample_error_response
    ) -> None:
        """Verify state is written to terminal-specific file when terminal_id available.

        Given: ErrorAttributionTracker is initialized with a detectable terminal_id
        When: State is written after error detection
        Then: State should be written to error_attribution_{terminal_id}.json

        NOTE: This test FAILS in RED phase because the implementation always
        writes to error_attribution.json regardless of terminal_id.
        """
        # Arrange - Set a mock terminal_id
        tracker, temp_dir = error_tracker_with_temp_state

        # Mock terminal detection to return a specific ID
        with patch('posttooluse.error_attribution_tracker.detect_terminal_id') as mock_detect:
            mock_detect.return_value = "env_abc123def"

            # Re-initialize to pick up the mocked terminal_id
            import importlib

            from posttooluse import error_attribution_tracker
            importlib.reload(error_attribution_tracker)

            from posttooluse.error_attribution_tracker import ErrorAttributionTracker
            tracker = ErrorAttributionTracker()

        # Act
        error_info = tracker._extract_error_source(sample_error_response["output"])
        tracker._write_state(error_info)

        # Assert
        # Look for terminal-specific file
        terminal_specific_files = list(temp_dir.glob("error_attribution_env_abc123def.json"))
        assert len(terminal_specific_files) == 1, (
            "Terminal-specific state file should exist - FAILS because feature not implemented"
        )


class TestFallbackToDefaultStateFile:
    """Tests for fallback behavior when terminal_id is None.

    These tests verify that when terminal_id cannot be detected (None),
    the system falls back to the original error_attribution.json filename.
    """

    def test_fallback_to_default_state_file(
        self, error_tracker_with_temp_state, sample_error_response
    ) -> None:
        """Verify original state file is used when terminal_id is None.

        Given: ErrorAttributionTracker has terminal_id = None (detection fails)
        When: State is written after error detection
        Then: State should be written to error_attribution.json (original filename)

        NOTE: This test should PASS even before implementation since the
        current code already uses error_attribution.json. But we include
        it for completeness.
        """
        # Arrange - Mock terminal detection to return None
        tracker, temp_dir = error_tracker_with_temp_state

        with patch('posttooluse.error_attribution_tracker.detect_terminal_id') as mock_detect:
            mock_detect.return_value = None

            import importlib

            from posttooluse import error_attribution_tracker
            importlib.reload(error_attribution_tracker)

            from posttooluse.error_attribution_tracker import ErrorAttributionTracker
            tracker = ErrorAttributionTracker()

        # Act
        error_info = tracker._extract_error_source(sample_error_response["output"])
        tracker._write_state(error_info)

        # Assert
        default_state_file = temp_dir / "error_attribution.json"
        assert default_state_file.exists(), (
            "Default state file should exist when terminal_id is None"
        )


class TestTerminalIsolation:
    """Tests for proper isolation between different terminals.

    These tests verify that different terminal sessions maintain separate
    state files, preventing cross-terminal contamination.
    """

    def test_terminal_isolation(
        self, error_tracker_with_temp_state, sample_error_response
    ) -> None:
        """Verify different terminals write to different state files.

        Given: Two ErrorAttributionTracker instances with different terminal_ids
        When: Both write state after error detection
        Then: Each should have its own terminal-specific state file

        NOTE: This test FAILS in RED phase because both instances currently
        write to the same error_attribution.json file.
        """
        # Arrange - Create tracker1 with terminal_id = "env_terminal_001"
        tracker1, temp_dir = error_tracker_with_temp_state

        with patch('posttooluse.error_attribution_tracker.detect_terminal_id') as mock_detect:
            mock_detect.return_value = "env_terminal_001"

            import importlib

            from posttooluse import error_attribution_tracker
            importlib.reload(error_attribution_tracker)

            from posttooluse.error_attribution_tracker import ErrorAttributionTracker
            tracker1 = ErrorAttributionTracker()

        # Create tracker2 with terminal_id = "env_terminal_002"
        with patch('posttooluse.error_attribution_tracker.detect_terminal_id') as mock_detect:
            mock_detect.return_value = "env_terminal_002"

            import importlib

            from posttooluse import error_attribution_tracker
            importlib.reload(error_attribution_tracker)

            from posttooluse.error_attribution_tracker import ErrorAttributionTracker
            tracker2 = ErrorAttributionTracker()

        # Act - Write state from both trackers
        error_info = tracker1._extract_error_source(sample_error_response["output"])
        tracker1._write_state(error_info)

        error_info2 = tracker2._extract_error_source(sample_error_response["output"])
        tracker2._write_state(error_info2)

        # Assert - Verify both terminal-specific files exist
        state_file_1 = temp_dir / "error_attribution_env_terminal_001.json"
        state_file_2 = temp_dir / "error_attribution_env_terminal_002.json"

        assert state_file_1.exists(), (
            "Terminal 001 state file should exist - FAILS because feature not implemented"
        )
        assert state_file_2.exists(), (
            "Terminal 002 state file should exist - FAILS because feature not implemented"
        )

        # Verify each file has correct terminal_id
        state_data_1 = json.loads(state_file_1.read_text())
        state_data_2 = json.loads(state_file_2.read_text())

        assert state_data_1["terminal_id"] == "env_terminal_001"
        assert state_data_2["terminal_id"] == "env_terminal_002"

        # Verify isolation - different files
        assert state_file_1 != state_file_2, "Different terminals should have different state files"
