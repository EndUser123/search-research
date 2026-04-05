"""
Test suite for stale discovery file detection in is_daemon_running().

These tests CAPTURE CURRENT BEHAVIOR before refactoring to add stale
discovery file detection and cleanup.

Run with: pytest P:/.claude/hooks/tests/test_stale_discovery_detection.py -v

Related files:
- P:/.claude/hooks/SessionStart_semantic_daemon.py - Source file to test
- P:/.claude/hooks/tests/TEST_PATTERNS.md - Test patterns reference
"""

import json
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Generator
from unittest.mock import MagicMock, patch

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


# Staleness threshold constant (must match implementation)
STALENESS_THRESHOLD_SECONDS: int = 300


@contextmanager
def _mock_win32file(pipe_exists: bool = False) -> Generator[None, None, None]:
    """
    Context manager to mock win32file module for testing.

    Args:
        pipe_exists: If True, CreateFile succeeds. If False, raises exception.

    Yields:
        None
    """
    mock_handle = MagicMock()
    mock_win32 = MagicMock()
    mock_win32.GENERIC_READ = 1
    mock_win32.OPEN_EXISTING = 3
    mock_win32.CloseHandle = MagicMock()

    if pipe_exists:
        mock_win32.CreateFile.return_value = mock_handle
    else:
        mock_win32.CreateFile.side_effect = Exception("Pipe not found")

    sys.modules["win32file"] = mock_win32

    try:
        yield
    finally:
        if "win32file" in sys.modules:
            del sys.modules["win32file"]


@contextmanager
def _patch_daemon_constants(
    discovery_file: Path,
    csf_root: Path,
    pid_file: Path | None = None,
) -> Generator[None, None, None]:
    """
    Context manager to patch daemon module constants.

    Args:
        discovery_file: Path to use for DISCOVERY_FILE constant.
        csf_root: Path to use for SHARED_CSF_ROOT constant.
        pid_file: Path to use for PID_FILE constant (optional).

    Yields:
        None
    """
    # Clear and reload module
    if "SessionStart_semantic_daemon" in sys.modules:
        del sys.modules["SessionStart_semantic_daemon"]


    patches = [
        patch.object(
            sys.modules["SessionStart_semantic_daemon"],
            "DISCOVERY_FILE",
            discovery_file,
        ),
        patch.object(
            sys.modules["SessionStart_semantic_daemon"],
            "SHARED_CSF_ROOT",
            csf_root,
        ),
    ]

    if pid_file is not None:
        patches.append(
            patch.object(
                sys.modules["SessionStart_semantic_daemon"],
                "PID_FILE",
                pid_file,
            )
        )

    for p in patches:
        p.start()

    try:
        yield
    finally:
        for p in patches:
            p.stop()
        if "SessionStart_semantic_daemon" in sys.modules:
            del sys.modules["SessionStart_semantic_daemon"]


class TestIsDaemonRunningStaleDiscovery:
    """
    Tests for is_daemon_running() behavior with stale discovery files.

    Current behavior (characterization):
    - is_daemon_running() only checks if pipe exists
    - Does NOT check discovery file timestamp
    - Does NOT clean up stale discovery files

    Expected behavior (after fix):
    - Detect discovery files older than 300 seconds (5 minutes)
    - Return False for stale discovery files (daemon not running)
    - Clean up stale discovery files
    """

    @pytest.fixture
    def mock_paths(self, tmp_path: Path) -> Dict[str, Path]:
        """
        Create mock paths for testing.

        Args:
            tmp_path: Pytest's temporary path fixture.

        Returns:
            Dictionary with paths for csf_root, data_dir, discovery_file, pid_file, log_file.
        """
        csf_root = tmp_path / "__csf"
        csf_root.mkdir(parents=True)
        data_dir = csf_root / "data"
        data_dir.mkdir(parents=True)

        return {
            "csf_root": csf_root,
            "data_dir": data_dir,
            "discovery_file": data_dir / "semantic_daemon_discovery.json",
            "pid_file": data_dir / "semantic_daemon.pid",
            "log_file": data_dir / "semantic_daemon.log",
        }

    @pytest.fixture
    def stale_discovery_data(self) -> Dict[str, Any]:
        """
        Create stale discovery file data (> 5 minutes old).

        Returns:
            Dictionary with pipe_name, pid, and timestamp fields.
        """
        return {
            "pipe_name": r"\\.\pipe\csf_nip_semantic_test_stale",
            "pid": 12345,
            "timestamp": time.time() - 301,  # More than 5 minutes ago
        }

    @pytest.fixture
    def fresh_discovery_data(self) -> Dict[str, Any]:
        """
        Create fresh discovery file data (< 5 minutes old).

        Returns:
            Dictionary with pipe_name, pid, and timestamp fields.
        """
        return {
            "pipe_name": r"\\.\pipe\csf_nip_semantic_test_fresh",
            "pid": 12346,
            "timestamp": time.time() - 60,  # 1 minute ago
        }

    def test_stale_discovery_file_characterization(
        self, mock_paths: Dict[str, Path], stale_discovery_data: Dict[str, Any]
    ) -> None:
        """
        Characterization: is_daemon_running() with stale discovery file.

        CAPTURES CURRENT BEHAVIOR:
        - Stale discovery files are NOT checked for timestamp
        - Pipe existence test may succeed even with stale discovery file
        - Stale discovery files are NOT cleaned up

        Given: Discovery file with timestamp > 300 seconds ago
        When: is_daemon_running() is called
        Then: Currently returns True (incorrect - should return False)
              and does NOT clean up stale file (should clean up)

        This test FAILS because the feature is NOT implemented yet.
        """
        # Arrange: Write stale discovery file
        mock_paths["discovery_file"].write_text(
            json.dumps(stale_discovery_data)
        )

        with _mock_win32file(pipe_exists=False):
            with _patch_daemon_constants(
                discovery_file=mock_paths["discovery_file"],
                csf_root=mock_paths["csf_root"],
                pid_file=mock_paths["pid_file"],
            ):
                from SessionStart_semantic_daemon import is_daemon_running

                # Act: Call is_daemon_running
                result = is_daemon_running()

                # Assert: Expected behavior after fix
                # With stale discovery file, should return False
                # and discovery file should be cleaned up
                assert result is False, (
                    "is_daemon_running() should return False for "
                    "stale discovery files (> 300 seconds)"
                )

                # Discovery file should be cleaned up
                assert not mock_paths["discovery_file"].exists(), (
                    "Stale discovery file should be cleaned up"
                )

    def test_fresh_discovery_file_returns_true(
        self, mock_paths: Dict[str, Path], fresh_discovery_data: Dict[str, Any]
    ) -> None:
        """
        Test that fresh discovery files (< 5 minutes) are treated as valid.

        Given: Discovery file with timestamp < 300 seconds ago
        When: is_daemon_running() is called and pipe exists
        Then: Returns True (daemon is running)
        """
        # Arrange: Write fresh discovery file
        mock_paths["discovery_file"].write_text(
            json.dumps(fresh_discovery_data)
        )

        with _mock_win32file(pipe_exists=True):
            with _patch_daemon_constants(
                discovery_file=mock_paths["discovery_file"],
                csf_root=mock_paths["csf_root"],
                pid_file=mock_paths["pid_file"],
            ):
                import win32file
                from SessionStart_semantic_daemon import is_daemon_running

                # Act
                result = is_daemon_running()

                # Assert: Fresh discovery file should return True
                assert result is True

                # Discovery file should NOT be cleaned up
                assert mock_paths["discovery_file"].exists()

                # Pipe handle should be closed
                win32file.CloseHandle.assert_called_once()

    def test_stale_exactly_300_seconds_boundary(
        self, mock_paths: Dict[str, Path]
    ) -> None:
        """
        Test boundary condition: exactly 300 seconds should be considered stale.

        Given: Discovery file with timestamp exactly 300 seconds ago
        When: is_daemon_running() is called
        Then: Returns False (at or over threshold = stale)
        """
        # Create discovery file exactly at threshold
        boundary_data = {
            "pipe_name": r"\\.\pipe\csf_nip_semantic_boundary",
            "pid": 12347,
            "timestamp": time.time() - 300,  # Exactly 5 minutes
        }

        mock_paths["discovery_file"].write_text(json.dumps(boundary_data))

        with _mock_win32file(pipe_exists=False):
            with _patch_daemon_constants(
                discovery_file=mock_paths["discovery_file"],
                csf_root=mock_paths["csf_root"],
                pid_file=mock_paths["pid_file"],
            ):
                from SessionStart_semantic_daemon import is_daemon_running

                # Act
                result = is_daemon_running()

                # Assert: At threshold, should be considered stale
                assert result is False, (
                    "Discovery files at exactly 300 seconds should be "
                    "considered stale"
                )

                # Discovery file should be cleaned up
                assert not mock_paths["discovery_file"].exists()

    def test_missing_discovery_file_returns_false(
        self, mock_paths: Dict[str, Path]
    ) -> None:
        """
        Test behavior when discovery file doesn't exist.

        Given: No discovery file exists
        When: is_daemon_running() is called
        Then: Returns False (no daemon info available)
        """
        # Discovery file doesn't exist by default in tmp_path

        with _mock_win32file(pipe_exists=False):
            with _patch_daemon_constants(
                discovery_file=mock_paths["discovery_file"],
                csf_root=mock_paths["csf_root"],
            ):
                from SessionStart_semantic_daemon import is_daemon_running

                # Act
                result = is_daemon_running()

                # Assert: No discovery file means daemon not running
                assert result is False

    def test_stale_discovery_with_pipe_still_exists(
        self, mock_paths: Dict[str, Path], stale_discovery_data: Dict[str, Any]
    ) -> None:
        """
        Test edge case: stale discovery but pipe still exists.

        Given: Stale discovery file but pipe still accessible
        When: is_daemon_running() is called
        Then: Returns True (pipe exists) but cleans stale discovery

        This handles case where daemon is healthy but discovery
        file wasn't updated (timestamp drift).
        """
        mock_paths["discovery_file"].write_text(
            json.dumps(stale_discovery_data)
        )

        with _mock_win32file(pipe_exists=True):
            with _patch_daemon_constants(
                discovery_file=mock_paths["discovery_file"],
                csf_root=mock_paths["csf_root"],
                pid_file=mock_paths["pid_file"],
            ):
                from SessionStart_semantic_daemon import is_daemon_running

                # Act
                result = is_daemon_running()

                # Assert: Pipe exists so daemon IS running
                assert result is True, (
                    "Pipe exists should return True even with "
                    "stale discovery file"
                )

                # But stale discovery file should still be cleaned up
                # so it gets refreshed with current timestamp
                assert not mock_paths["discovery_file"].exists(), (
                    "Stale discovery file should be cleaned up even "
                    "if pipe exists"
                )


class TestStaleDiscoveryCleanup:
    """
    Tests specifically for cleanup behavior of stale discovery files.

    These tests verify that stale discovery files are properly removed
    to prevent false positives in daemon detection.
    """

    @pytest.fixture
    def setup_stale_scenario(self, tmp_path: Path) -> Dict[str, Any]:
        """
        Set up a stale discovery file scenario.

        Args:
            tmp_path: Pytest's temporary path fixture.

        Returns:
            Dictionary with discovery_file, csf_root, and stale_data.
        """
        csf_root = tmp_path / "__csf"
        csf_root.mkdir(parents=True)
        data_dir = csf_root / "data"
        data_dir.mkdir(parents=True)

        discovery_file = data_dir / "semantic_daemon_discovery.json"

        # Write stale discovery file
        stale_data = {
            "pipe_name": r"\\.\pipe\csf_nip_semantic_stale",
            "pid": 99999,
            "timestamp": time.time() - 400,  # > 5 minutes
        }
        discovery_file.write_text(json.dumps(stale_data))

        return {
            "discovery_file": discovery_file,
            "csf_root": csf_root,
            "stale_data": stale_data,
        }

    def test_cleanup_happens_on_detection(
        self, setup_stale_scenario: Dict[str, Any]
    ) -> None:
        """
        Test that stale discovery file is cleaned up during detection.

        Given: Stale discovery file exists
        When: is_daemon_running() detects staleness
        Then: Discovery file is removed
        """
        discovery_file = setup_stale_scenario["discovery_file"]

        # Verify file exists before test
        assert discovery_file.exists()

        with _mock_win32file(pipe_exists=False):
            with _patch_daemon_constants(
                discovery_file=discovery_file,
                csf_root=setup_stale_scenario["csf_root"],
            ):
                from SessionStart_semantic_daemon import is_daemon_running

                # Act
                is_daemon_running()

                # Assert: File should be cleaned up
                assert not discovery_file.exists(), (
                    "Stale discovery file should be cleaned up"
                )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
