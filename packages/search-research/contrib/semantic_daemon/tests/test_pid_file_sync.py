"""TDD tests for PID file synchronization in UnifiedSemanticDaemon.

Tests verify that:
1. After daemon start(), the PID file contains the same PID as the discovery file
2. PID file is written atomically (uses temp file + rename pattern)
3. If PID file exists with different PID, it gets overwritten
4. Mock the actual daemon startup to test just the PID file writing logic

RED Phase: All tests should FAIL until implementation is complete.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Setup path - add project root
csf_root = Path(__file__).parent.parent.parent.parent.parent


class TestPIDFileSyncAfterStart:
    """Tests for PID file synchronization after daemon start()."""

    @patch("search_research.contrib.semantic_daemon.unified_semantic_daemon.WIN32_AVAILABLE", True)
    def test_pid_file_matches_discovery_file_after_start(self):
        """
        Test that after daemon start(), the PID file contains the same PID as the discovery file.

        Given: Daemon is started
        When: We check both the PID file and discovery file
        Then: Both files should contain the same PID
        """
        from search_research.contrib.semantic_daemon.unified_semantic_daemon import (
            UnifiedSemanticDaemon,
        )

        # Create a temporary directory for test files
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Patch DISCOVERY_FILE to use temp directory
            discovery_path = tmpdir / "discovery.json"
            with patch("search_research.contrib.semantic_daemon.unified_semantic_daemon.DISCOVERY_FILE", discovery_path):
                # Create daemon instance
                daemon = UnifiedSemanticDaemon()

                # Get PID file path (should be in temp dir with derived name)
                pid_file = tmpdir / f"csf_semantic_{daemon.pid}_{daemon.timestamp}.pid"

                # Call _write_discovery_file and _write_pid_file directly
                daemon._write_discovery_file()
                daemon._write_pid_file(pid_file)

                # Verify discovery file was written
                assert discovery_path.exists(), "Discovery file should exist after write"

                # TEST: PID file should exist
                assert pid_file.exists(), f"PID file should exist after write: {pid_file}"

                # TEST: PID file should contain daemon's PID
                pid_file_content = pid_file.read_text().strip()
                assert pid_file_content == str(
                    daemon.pid
                ), f"PID file should contain {daemon.pid}, got {pid_file_content}"

                # TEST: Discovery file should also exist and contain same PID
                discovery_data = json.loads(discovery_path.read_text())
                assert (
                    discovery_data["pid"] == daemon.pid
                ), f"Discovery file PID should be {daemon.pid}"

                # TEST: Both files should have the same PID
                assert pid_file_content == str(
                    discovery_data["pid"]
                ), "PID file and discovery file should contain the same PID"


class TestPIDFileAtomicWrite:
    """Tests for atomic PID file writing using temp file + rename pattern."""

    @patch("search_research.contrib.semantic_daemon.unified_semantic_daemon.WIN32_AVAILABLE", True)
    def test_pid_file_written_atomically(self):
        """
        Test that PID file is written atomically using temp file + rename.

        Given: Daemon needs to write a PID file
        When: The PID file write operation occurs
        Then: It should use temp file + rename pattern for atomicity
        """

        from search_research.contrib.semantic_daemon.unified_semantic_daemon import (
            UnifiedSemanticDaemon,
        )

        # Create daemon instance
        daemon = UnifiedSemanticDaemon()

        # Mock the file operations to verify atomic write pattern
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            pid_file = tmpdir / "test.pid"
            temp_pid_file = tmpdir / "test.pid.tmp"

            # Mock open() to track write pattern
            written_files = []

            def mock_write_impl(file_path, data):
                """Track which files are written."""
                written_files.append(str(file_path))
                # Actually write the file for verification
                file_path.write_text(data)

            # Call _write_pid_file (method we expect to exist)
            # This should fail initially because the method doesn't exist
            assert hasattr(
                daemon, "_write_pid_file"
            ), "Daemon should have _write_pid_file method for atomic PID writing"

            # Mock os.replace to verify rename pattern
            with patch("os.replace") as mock_replace:
                with patch("pathlib.Path.write_text") as mock_write:
                    # Set up the mock to track temp file write
                    def track_write(data):
                        written_files.append("write_text called")

                    mock_write.side_effect = track_write

                    # Call the method
                    daemon._write_pid_file(pid_file)

                    # Verify temp file + rename pattern was used
                    # Should write to temp file first, then rename
                    assert any(
                        ".tmp" in str(call) for call in mock_replace.call_args_list
                    ), "Should use temp file with .tmp extension for atomic write"
                    mock_replace.assert_called_once()


class TestPIDFileOverwriteDifferentPID:
    """Tests for overwriting PID file with different PID."""

    @patch("search_research.contrib.semantic_daemon.unified_semantic_daemon.WIN32_AVAILABLE", True)
    def test_pid_file_overwritten_with_different_pid(self):
        """
        Test that if PID file exists with different PID, it gets overwritten.

        Given: PID file exists with a stale PID
        When: Daemon writes a new PID file
        Then: The PID file should be overwritten with the new PID
        """
        from search_research.contrib.semantic_daemon.unified_semantic_daemon import (
            UnifiedSemanticDaemon,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create a stale PID file with old PID
            old_pid = 12345
            pid_file = tmpdir / "daemon.pid"
            pid_file.write_text(str(old_pid))

            # Verify old PID is in file
            assert pid_file.read_text().strip() == str(old_pid), "Setup: Old PID should be in file"

            # Create new daemon with different PID
            with patch(
                "search_research.contrib.semantic_daemon.unified_semantic_daemon.DISCOVERY_FILE", tmpdir / "discovery.json"
            ):
                daemon = UnifiedSemanticDaemon()

                new_pid = daemon.pid

                # Call _write_pid_file with the stale file path
                daemon._write_pid_file(pid_file)

                # TEST: PID file should now contain new PID, not old PID
                current_content = pid_file.read_text().strip()
                assert current_content == str(
                    new_pid
                ), f"PID file should contain new PID {new_pid}, not old PID {old_pid}"
                assert current_content != str(
                    old_pid
                ), "PID file should not contain the old stale PID"


class TestPIDFileWriteMethodExists:
    """Tests to verify _write_pid_file method exists and is callable."""

    @patch("search_research.contrib.semantic_daemon.unified_semantic_daemon.WIN32_AVAILABLE", True)
    def test_write_pid_file_method_exists(self):
        """
        Test that daemon has _write_pid_file method.

        Given: UnifiedSemanticDaemon is instantiated
        When: We check for _write_pid_file method
        Then: The method should exist and be callable
        """
        from search_research.contrib.semantic_daemon.unified_semantic_daemon import (
            UnifiedSemanticDaemon,
        )

        daemon = UnifiedSemanticDaemon()

        assert hasattr(daemon, "_write_pid_file"), "Daemon should have _write_pid_file method"
        assert callable(daemon._write_pid_file), "_write_pid_file should be callable"

    @patch("search_research.contrib.semantic_daemon.unified_semantic_daemon.WIN32_AVAILABLE", True)
    def test_write_pid_file_accepts_path_argument(self):
        """
        Test that _write_pid_file accepts optional path argument.

        Given: Daemon has _write_pid_file method
        When: We call it with a custom path
        Then: It should accept the path argument
        """
        import inspect

        from search_research.contrib.semantic_daemon.unified_semantic_daemon import (
            UnifiedSemanticDaemon,
        )

        daemon = UnifiedSemanticDaemon()

        # Check method signature
        sig = inspect.signature(daemon._write_pid_file)
        params = list(sig.parameters.keys())

        # Should have at most one parameter (optional path)
        assert (
            len(params) <= 1
        ), f"_write_pid_file should have at most 1 parameter, got {len(params)}"

        # If it has a parameter, it should accept a Path
        if params:
            # Verify we can call it with a Path
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                try:
                    # This should not raise an error
                    daemon._write_pid_file(Path(tmp.name))
                except TypeError as e:
                    if "positional argument" in str(e):
                        pytest.fail(f"_write_pid_file should accept Path argument: {e}")
                finally:
                    # Cleanup
                    try:
                        Path(tmp.name).unlink(missing_ok=True)
                    except:
                        pass
