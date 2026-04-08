#!/usr/bin/env python3
"""Test orphaned PID file cleanup in SessionStart_semantic_daemon.py

This test verifies that the _kill_stale_daemons_aggressive() function
properly cleans up orphaned PID files.

Run: python P:/__csf/src/daemons/test_pid_file_cleanup.py
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

# Add paths
sys.path.insert(0, str(Path("P:/__csf/src")))
sys.path.insert(0, str(Path("P:/.claude/hooks")))


def test_orphaned_pid_file_cleanup():
    """Test that orphaned PID files are cleaned up correctly."""
    from SessionStart_semantic_daemon import _kill_stale_daemons_aggressive

    # Use a temporary directory for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Mock SHARED_CSF_ROOT to use temp directory
        with patch.object(sys.modules["SessionStart_semantic_daemon"], "SHARED_CSF_ROOT", tmpdir):
            # Create test PID directory
            data_dir = tmpdir / "data"
            data_dir.mkdir(parents=True, exist_ok=True)

            # Create orphaned PID files (with fake PIDs that don't exist)
            orphaned_files = [
                data_dir / "csf_semantic_12345_1770760000.pid",
                data_dir / "csf_semantic_67890_1770760001.pid",
                data_dir / "csf_semantic_99999_1770760002.pid",
            ]
            for f in orphaned_files:
                f.write_text("fake_pid")

            # Create a malformed PID file
            malformed = data_dir / "csf_semantic_invalid.pid"
            malformed.write_text("bad_format")

            # Verify files were created
            created_files = list(data_dir.glob("csf_semantic_*.pid"))
            print(f"Created {len(created_files)} test PID files:")
            for f in created_files:
                print(f"  - {f.name}")

            # Run the cleanup function
            print("\nRunning _kill_stale_daemons_aggressive()...")

            # Mock psutil to return False for all PIDs (no processes running)
            with patch("psutil.pid_exists", return_value=False):
                with patch("psutil.process_iter", return_value=[]):
                    result = _kill_stale_daemons_aggressive()

            # Check results
            remaining_files = list(data_dir.glob("csf_semantic_*.pid"))
            print(f"\nCleanup result: {result} daemon(s) killed")
            print(f"Remaining PID files: {len(remaining_files)}")

            if len(remaining_files) == 0:
                print("✅ SUCCESS: All orphaned PID files were cleaned up")
                return True
            else:
                print("❌ FAILURE: Some PID files were not cleaned up:")
                for f in remaining_files:
                    print(f"  - {f.name}")
                return False


def test_running_pid_preserved():
    """Test that PID files for running processes are preserved."""

    # Get current PID (which is definitely running)
    current_pid = os.getpid()

    from SessionStart_semantic_daemon import _kill_stale_daemons_aggressive

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Mock SHARED_CSF_ROOT to use temp directory
        with patch.object(sys.modules["SessionStart_semantic_daemon"], "SHARED_CSF_ROOT", tmpdir):
            data_dir = tmpdir / "data"
            data_dir.mkdir(parents=True, exist_ok=True)

            # Create a PID file for the current (running) process
            current_pid_file = data_dir / f"csf_semantic_{current_pid}_{1234567890}.pid"
            current_pid_file.write_text(str(current_pid))

            # Create orphaned PID files
            orphaned_file = data_dir / "csf_semantic_99999_1770760000.pid"
            orphaned_file.write_text("99999")

            print(f"Created PID file for running process: {current_pid_file.name}")
            print(f"Created orphaned PID file: {orphaned_file.name}")

            # Mock psutil.pid_exists to only return True for current_pid
            def mock_pid_exists(pid):
                return pid == current_pid

            # Run cleanup
            print("\nRunning _kill_stale_daemons_aggressive()...")
            with patch("psutil.pid_exists", side_effect=mock_pid_exists):
                with patch("psutil.process_iter", return_value=[]):
                    result = _kill_stale_daemons_aggressive()

            # Check results
            remaining_files = list(data_dir.glob("csf_semantic_*.pid"))
            print(f"\nRemaining PID files: {len(remaining_files)}")

            if len(remaining_files) == 1 and remaining_files[0].name == current_pid_file.name:
                print("✅ SUCCESS: Running process PID file preserved, orphaned file removed")
                return True
            else:
                print("❌ FAILURE: Unexpected PID file state")
                for f in remaining_files:
                    print(f"  - {f.name}")
                return False


if __name__ == "__main__":
    print("=" * 60)
    print("Test 1: Orphaned PID file cleanup")
    print("=" * 60)
    test1 = test_orphaned_pid_file_cleanup()

    print("\n" + "=" * 60)
    print("Test 2: Running process PID preserved")
    print("=" * 60)
    test2 = test_running_pid_preserved()

    print("\n" + "=" * 60)
    if test1 and test2:
        print("All tests PASSED ✅")
        sys.exit(0)
    else:
        print("Some tests FAILED ❌")
        sys.exit(1)
