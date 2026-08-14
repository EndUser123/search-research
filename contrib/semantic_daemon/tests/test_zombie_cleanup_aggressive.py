#!/usr/bin/env python3
"""Integration tests for aggressive zombie cleanup behavior.

AT-011: Add aggressive zombie cleanup to prevent multiple daemon accumulation

Tests verify:
1. Multiple daemon processes running simultaneously are detected and cleaned up
2. Aggressive cleanup kills all but the discovery PID (canonical daemon)
3. Grace period for young daemons (<30 seconds, less than MAX_DAEMON_AGE=3600s)
4. Age-based self-termination for old orphan daemons (>1 hour)
5. psutil mocking to simulate multiple processes

RED Phase: All tests should FAIL until implementation is complete.

Note: Integration tests that actually start the daemon are mocked to avoid
hanging indefinitely. The tests focus on the aggressive cleanup logic behavior.
"""

import json
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import patch


class MockProcess:
    """Simple mock for psutil.Process with real info dict."""

    def __init__(self, info):
        self.info = info


def _make_mock_daemon_processes(pids, age_seconds=3600, cmdline=None):
    """Helper to create mock daemon processes."""
    if cmdline is None:
        cmdline = ["python", "-m", "daemons.unified_semantic_daemon"]
    current_time = time.time()
    processes = []
    for pid in pids:
        proc = MockProcess(
            {"pid": pid, "create_time": current_time - age_seconds, "cmdline": cmdline}
        )
        processes.append(proc)
    return iter(processes)


# Setup path - add project root
csf_root = Path(__file__).parent.parent.parent.parent.parent
if str(csf_root) not in sys.path:
    sys.path.insert(0, str(csf_root))


class TestAggressiveCleanupKillsAllButDiscoveryPID:
    """Tests for aggressive cleanup that kills all but the discovery PID."""

    @patch("search_research.contrib.semantic_daemon.unified_semantic_daemon.WIN32_AVAILABLE", True)
    def test_aggressive_cleanup_kills_non_discovery_daemons(self):
        """
        Test that aggressive cleanup kills all daemon processes except the discovery PID.

        Given: Multiple daemon processes running simultaneously with different PIDs
        And: Discovery file points to the canonical daemon (PID 100)
        When: Aggressive cleanup is triggered
        Then: All non-canonical daemons should be terminated
        And: The canonical daemon (discovery PID) should remain running
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            discovery_path = tmpdir / "discovery.json"

            # Setup: Create discovery file with canonical daemon PID
            canonical_pid = 100
            discovery_data = {
                "pipe_name": r"\\.\pipe\csf_semantic_100_1234567890",
                "pid": canonical_pid,
                "timestamp": int(time.time()),
            }
            discovery_path.write_text(json.dumps(discovery_data))

            # Mock psutil to simulate multiple daemon processes
            def mock_process_iter(*args, **kwargs):
                # Return list of processes including non-canonical daemons
                processes = []
                current_time = time.time()
                for pid in [200, 300, 400]:  # Non-canonical daemon PIDs
                    proc = MockProcess(
                        {
                            "pid": pid,
                            "create_time": current_time
                            - 3600,  # 1 hour old (older than grace period)
                            "cmdline": ["python", "-m", "daemons.unified_semantic_daemon"],
                        }
                    )
                    processes.append(proc)
                return iter(processes)

            # Apply psutil patch first, before using the daemon
            with patch(
                "search_research.contrib.semantic_daemon.unified_semantic_daemon.psutil.process_iter",
                side_effect=mock_process_iter,
            ):
                # Import after patch is applied
                from search_research.contrib.semantic_daemon.unified_semantic_daemon import (
                    UnifiedSemanticDaemon,
                )

                with patch("search_research.contrib.semantic_daemon.unified_semantic_daemon.DISCOVERY_FILE", discovery_path):
                    # Create daemon instance (simulating canonical daemon)
                    daemon = UnifiedSemanticDaemon.__new__(UnifiedSemanticDaemon)
                    daemon.pid = canonical_pid
                    daemon.timestamp = discovery_data["timestamp"]
                    daemon._pipe_name = discovery_data["pipe_name"]

                    # This method should exist to perform aggressive cleanup
                    # Initially it will fail because the method doesn't exist
                    assert hasattr(
                        daemon, "_aggressive_cleanup_zombies"
                    ), "Daemon should have _aggressive_cleanup_zombies method"

                    # Call aggressive cleanup
                    killed_count = daemon._aggressive_cleanup_zombies()

                    # Verify that non-canonical PIDs were terminated
                    assert (
                        killed_count == 3
                    ), f"Should terminate 3 non-canonical daemons, got {killed_count}"


class TestGracePeriodForYoungDaemons:
    """Tests for grace period for young daemons (<30 seconds)."""

    @patch("search_research.contrib.semantic_daemon.unified_semantic_daemon.WIN32_AVAILABLE", True)
    def test_young_daemons_get_grace_period(self):
        """
        Test that young daemons (<30 seconds old) receive grace period and are not terminated.

        Given: Multiple daemon processes running simultaneously
        And: Some daemons are less than 30 seconds old
        When: Aggressive cleanup is triggered
        Then: Young daemons should NOT be terminated (grace period)
        And: Only old daemons should be terminated
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            discovery_path = tmpdir / "discovery.json"

            # Setup: Create discovery file with canonical daemon
            canonical_pid = 100
            current_time = int(time.time())
            discovery_data = {
                "pipe_name": rf"\\.\pipe\csf_semantic_{canonical_pid}_{current_time}",
                "pid": canonical_pid,
                "timestamp": current_time,
            }
            discovery_path.write_text(json.dumps(discovery_data))

            # Mock psutil to simulate processes with different ages
            def mock_process_iter(*args, **kwargs):
                processes = []

                # Young daemon (20 seconds old) - should get grace
                young_pid = 200
                young_timestamp = current_time - 20
                young_proc = MockProcess(
                    {
                        "pid": young_pid,
                        "create_time": young_timestamp,
                        "cmdline": ["python", "-m", "daemons.unified_semantic_daemon"],
                    }
                )
                processes.append(young_proc)

                # Old daemon (2 hours old = 7200 seconds) - should be terminated
                old_pid = 300
                old_timestamp = current_time - 7200
                old_proc = MockProcess(
                    {
                        "pid": old_pid,
                        "create_time": old_timestamp,
                        "cmdline": ["python", "-m", "daemons.unified_semantic_daemon"],
                    }
                )
                processes.append(old_proc)

                return iter(processes)

            # Apply psutil patch first
            with patch(
                "search_research.contrib.semantic_daemon.unified_semantic_daemon.psutil.process_iter",
                side_effect=mock_process_iter,
            ):
                from search_research.contrib.semantic_daemon.unified_semantic_daemon import (
                    UnifiedSemanticDaemon,
                )

                with patch("search_research.contrib.semantic_daemon.unified_semantic_daemon.DISCOVERY_FILE", discovery_path):
                    # Create daemon instance
                    daemon = UnifiedSemanticDaemon.__new__(UnifiedSemanticDaemon)
                    daemon.pid = canonical_pid
                    daemon.timestamp = current_time
                    daemon._pipe_name = discovery_data["pipe_name"]

                    # Call aggressive cleanup (uses global GRACE_PERIOD_SECONDS constant)
                    killed_count = daemon._aggressive_cleanup_zombies()

                    # Verify only old daemon was terminated (young daemon got grace period)
                    # The mock has 2 daemons: young (20s) and old (2h)
                    # Only old daemon should be terminated
                    assert (
                        killed_count == 1
                    ), f"Should terminate 1 old daemon (>5 min), young daemon (<30s) gets grace. Got {killed_count}"


class TestAgeBasedSelfTermination:
    """Tests for age-based self-termination for old orphan daemons."""

    @patch("search_research.contrib.semantic_daemon.unified_semantic_daemon.WIN32_AVAILABLE", True)
    def test_old_orphan_daemon_self_terminates(self):
        """
        Test that old orphan daemons (>1 hour) not in discovery file self-terminate.

        Given: Daemon is older than MAX_DAEMON_AGE (3600 seconds = 1 hour)
        And: Daemon's PID is NOT in the discovery file
        When: Daemon checks if it should terminate based on age
        Then: Should return True (terminate)
        """
        from search_research.contrib.semantic_daemon.unified_semantic_daemon import (
            MAX_DAEMON_AGE,
            UnifiedSemanticDaemon,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            discovery_path = tmpdir / "discovery.json"

            # Create discovery file with DIFFERENT PID (not our daemon)
            discovery_pid = 999
            discovery_data = {
                "pipe_name": rf"\\.\pipe\csf_semantic_{discovery_pid}_1234567890",
                "pid": discovery_pid,
                "timestamp": int(time.time()),
            }
            discovery_path.write_text(json.dumps(discovery_data))

            with patch("search_research.contrib.semantic_daemon.unified_semantic_daemon.DISCOVERY_FILE", discovery_path):
                # Create old orphan daemon (>1 hour old, PID not in discovery)
                orphan_pid = 200
                old_timestamp = int(time.time()) - MAX_DAEMON_AGE - 100  # Older than MAX_DAEMON_AGE

                daemon = UnifiedSemanticDaemon.__new__(UnifiedSemanticDaemon)
                daemon.pid = orphan_pid
                daemon.timestamp = old_timestamp

                # Check if daemon should terminate
                should_terminate = daemon._should_terminate_based_on_age()

                # Verify old orphan daemon should terminate
                assert (
                    should_terminate is True
                ), "Old orphan daemon (>1 hour, not in discovery) should self-terminate"

    @patch("search_research.contrib.semantic_daemon.unified_semantic_daemon.WIN32_AVAILABLE", True)
    def test_young_orphan_daemon_continues_running(self):
        """
        Test that young orphan daemons (<1 hour) continue running even if not in discovery.

        Given: Daemon is younger than MAX_DAEMON_AGE (3600 seconds = 1 hour)
        And: Daemon's PID is NOT in the discovery file
        When: Daemon checks if it should terminate based on age
        Then: Should return False (continue running)
        """
        from search_research.contrib.semantic_daemon.unified_semantic_daemon import (
            UnifiedSemanticDaemon,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            discovery_path = tmpdir / "discovery.json"

            # No discovery file exists
            with patch("search_research.contrib.semantic_daemon.unified_semantic_daemon.DISCOVERY_FILE", discovery_path):
                # Create young orphan daemon (<1 hour old)
                orphan_pid = 200
                young_timestamp = int(time.time()) - 600  # 10 minutes old

                daemon = UnifiedSemanticDaemon.__new__(UnifiedSemanticDaemon)
                daemon.pid = orphan_pid
                daemon.timestamp = young_timestamp

                # Check if daemon should terminate
                should_terminate = daemon._should_terminate_based_on_age()

                # Verify young orphan daemon should continue running
                assert (
                    should_terminate is False
                ), "Young orphan daemon (<1 hour) should continue running"


class TestMultipleDaemonProcessesDetection:
    """Tests for detecting multiple daemon processes simultaneously."""

    @patch("search_research.contrib.semantic_daemon.unified_semantic_daemon.WIN32_AVAILABLE", True)
    def test_detects_multiple_daemon_processes(self):
        """
        Test that the system can detect multiple daemon processes running simultaneously.

        Given: Multiple python processes with semantic daemon command line
        When: Daemon process detection is performed
        Then: All daemon processes should be detected
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            discovery_path = tmpdir / "discovery.json"
            discovery_path.write_text(
                json.dumps(
                    {"pid": 100, "pipe_name": "\\\\.\\pipe\\test", "timestamp": int(time.time())}
                )
            )

            # Mock psutil to return multiple daemon processes
            def mock_process_iter(*args, **kwargs):
                processes = []
                daemon_cmdline = ["python", "-m", "daemons.unified_semantic_daemon"]
                current_time = time.time()

                for pid in [100, 200, 300, 400]:
                    proc = MockProcess(
                        {"pid": pid, "create_time": current_time, "cmdline": daemon_cmdline}
                    )
                    processes.append(proc)

                # Also add some non-daemon python processes
                other_proc = MockProcess(
                    {
                        "pid": 999,
                        "create_time": current_time,
                        "cmdline": ["python", "-m", "some_other_module"],
                    }
                )
                processes.append(other_proc)

                return iter(processes)

            # Apply psutil patch first
            with patch(
                "search_research.contrib.semantic_daemon.unified_semantic_daemon.psutil.process_iter",
                side_effect=mock_process_iter,
            ):
                from search_research.contrib.semantic_daemon.unified_semantic_daemon import (
                    UnifiedSemanticDaemon,
                )

                with patch("search_research.contrib.semantic_daemon.unified_semantic_daemon.DISCOVERY_FILE", discovery_path):
                    daemon = UnifiedSemanticDaemon.__new__(UnifiedSemanticDaemon)
                    daemon.pid = 100
                    daemon.timestamp = int(time.time())

                    # This method should detect all daemon processes
                    assert hasattr(
                        daemon, "_detect_all_daemon_processes"
                    ), "Daemon should have _detect_all_daemon_processes method"

                    detected_daemons = daemon._detect_all_daemon_processes()
                    detected_pids = [d["pid"] for d in detected_daemons]

                    # Should detect exactly 4 daemon processes
                    assert (
                        len(detected_daemons) == 4
                    ), f"Should detect 4 daemon processes, got {len(detected_daemons)}"

                    # Should NOT detect non-daemon python process
                    assert (
                        999 not in detected_pids
                    ), "Non-daemon python process should not be detected"

                    # Should detect all daemon PIDs
                    for pid in [100, 200, 300, 400]:
                        assert pid in detected_pids, f"Daemon PID {pid} should be detected"


class TestAggressiveCleanupIntegration:
    """Integration tests for aggressive cleanup behavior."""

    @patch("search_research.contrib.semantic_daemon.unified_semantic_daemon.WIN32_AVAILABLE", True)
    def test_aggressive_cleanup_integration_flow(self):
        """
        Test the full integration flow of aggressive zombie cleanup.

        Given: Multiple zombie daemons accumulated over time
        When: New daemon starts with aggressive cleanup enabled
        Then: All zombies should be cleaned up except canonical daemon
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            discovery_path = tmpdir / "discovery.json"
            current_time = int(time.time())

            # Setup discovery file
            canonical_pid = 100
            discovery_data = {
                "pipe_name": rf"\\.\pipe\csf_semantic_{canonical_pid}_{current_time}",
                "pid": canonical_pid,
                "timestamp": current_time,
            }
            discovery_path.write_text(json.dumps(discovery_data))

            # Mock zombie processes with different ages
            def mock_process_iter(*args, **kwargs):
                processes = []

                # Zombie 1: Very old (2 hours), should be killed
                z1 = MockProcess(
                    {
                        "pid": 200,
                        "create_time": current_time - 7200,
                        "cmdline": ["python", "-m", "daemons.unified_semantic_daemon"],
                    }
                )
                processes.append(z1)

                # Zombie 2: Medium age (30 minutes), should be killed
                z2 = MockProcess(
                    {
                        "pid": 300,
                        "create_time": current_time - 1800,
                        "cmdline": ["python", "-m", "daemons.unified_semantic_daemon"],
                    }
                )
                processes.append(z2)

                # Zombie 3: Very young (1 minute), should get grace
                z3 = MockProcess(
                    {
                        "pid": 400,
                        "create_time": current_time - 60,
                        "cmdline": ["python", "-m", "daemons.unified_semantic_daemon"],
                    }
                )
                processes.append(z3)

                return iter(processes)

            # Apply psutil patch first
            with patch(
                "search_research.contrib.semantic_daemon.unified_semantic_daemon.psutil.process_iter",
                side_effect=mock_process_iter,
            ):
                from search_research.contrib.semantic_daemon.unified_semantic_daemon import (
                    UnifiedSemanticDaemon,
                )

                with patch("search_research.contrib.semantic_daemon.unified_semantic_daemon.DISCOVERY_FILE", discovery_path):
                    # Mock kill() method to track termination
                    killed_pids = []

                    def mock_kill_proc(pid):
                        killed_pids.append(pid)

                    with patch("os.kill", side_effect=mock_kill_proc):
                        # Create new daemon instance
                        daemon = UnifiedSemanticDaemon.__new__(UnifiedSemanticDaemon)
                        daemon.pid = canonical_pid
                        daemon.timestamp = current_time
                        daemon._pipe_name = discovery_data["pipe_name"]

                        # Execute aggressive cleanup (uses global GRACE_PERIOD_SECONDS constant)
                        terminated_count = daemon._aggressive_cleanup_zombies()

                        # Verify cleanup results
                        # Old zombies (200, 300) should be terminated
                        # Young zombie (400) gets grace period
                        # Canonical daemon is not terminated
                        # Expected: 2 terminated (200, 300), 2 spared (400, canonical_pid)
                        assert (
                            terminated_count == 2
                        ), f"Should terminate 2 old zombies (>5 min), 2 get grace. Got {terminated_count}"


class TestAggressiveCleanupWithPsutilMocking:
    """Tests that use psutil mocking to simulate multiple processes."""

    @patch("search_research.contrib.semantic_daemon.unified_semantic_daemon.WIN32_AVAILABLE", True)
    def test_psutil_mocking_simulates_multiple_processes(self):
        """
        Test that psutil mocking correctly simulates multiple daemon processes.

        Given: Multiple daemon processes need to be simulated
        When: psutil.process_iter is mocked
        Then: The mock should return multiple daemon process objects
        """

        # Mock multiple daemon processes
        def mock_process_iter(*args, **kwargs):
            processes = []
            current_time = time.time()
            for pid in [100, 200, 300]:
                proc = MockProcess(
                    {
                        "pid": pid,
                        "create_time": current_time - 1000,
                        "cmdline": ["python", "-m", "daemons.unified_semantic_daemon"],
                    }
                )
                processes.append(proc)
            return iter(processes)

        with patch(
            "search_research.contrib.semantic_daemon.unified_semantic_daemon.psutil.process_iter", side_effect=mock_process_iter
        ):
            from search_research.contrib.semantic_daemon.unified_semantic_daemon import (
                UnifiedSemanticDaemon,
            )

            # Verify the mock is working correctly
            daemon = UnifiedSemanticDaemon.__new__(UnifiedSemanticDaemon)
            daemon.pid = 100

            # This test verifies the mocking setup works correctly
            # The actual aggressive cleanup logic tests use this mock
            assert hasattr(
                daemon, "_detect_all_daemon_processes"
            ), "Daemon should have _detect_all_daemon_processes method"

            detected = daemon._detect_all_daemon_processes()

            # Verify mock returned expected PIDs (detected is list of dicts with 'pid' key)
            detected_pids = [d["pid"] for d in detected]
            assert 100 in detected_pids, "Mock should return PID 100"
            assert 200 in detected_pids, "Mock should return PID 200"
            assert 300 in detected_pids, "Mock should return PID 300"
            assert len(detected) == 3, "Mock should return exactly 3 processes"
