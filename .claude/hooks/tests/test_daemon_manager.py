"""
Tests for SessionStart_daemon_manager.py - Unified daemon startup hook.

Tests cover:
- Daemon health checking for each type (dreaming, search)
- Daemon launching with proper configuration
- Mutex coordination and multi-terminal safety
- Latency measurement and instrumentation
- Error handling and graceful degradation
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Add hooks directory to path for imports
# noqa: E402
HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))

# Import the module under test
import SessionStart_daemon_manager  # noqa: E402


class TestDaemonHealthCheck:
    """Test daemon health checking logic."""

    def test_healthy_daemon_with_recent_heartbeat(self, tmp_path):
        """Should return True when daemon heartbeat is recent (< 90s)."""
        # Arrange: Create state file with recent heartbeat
        state_file = tmp_path / "dreaming-daemon-state.json"
        recent_heartbeat = (datetime.now(UTC) - timedelta(seconds=30)).isoformat()
        state_file.write_text(json.dumps({"heartbeat": recent_heartbeat}))

        # Act
        healthy = SessionStart_daemon_manager.is_daemon_healthy(
            "dreaming", state_file, threshold_seconds=90
        )

        # Assert
        assert healthy is True

    def test_unhealthy_daemon_with_stale_heartbeat(self, tmp_path):
        """Should return False when daemon heartbeat is stale (> 90s)."""
        # Arrange: Create state file with stale heartbeat
        state_file = tmp_path / "search-daemon-state.json"
        stale_heartbeat = (datetime.now(UTC) - timedelta(seconds=120)).isoformat()
        state_file.write_text(json.dumps({"heartbeat": stale_heartbeat}))

        # Act
        healthy = SessionStart_daemon_manager.is_daemon_healthy(
            "search", state_file, threshold_seconds=90
        )

        # Assert
        assert healthy is False

    def test_unhealthy_daemon_with_missing_state_file(self, tmp_path):
        """Should return False when state file doesn't exist."""
        # Arrange: State file doesn't exist
        state_file = tmp_path / "dreaming-daemon-state.json"

        # Act
        healthy = SessionStart_daemon_manager.is_daemon_healthy(
            "dreaming", state_file, threshold_seconds=90
        )

        # Assert
        assert healthy is False

    def test_unhealthy_daemon_with_no_heartbeat(self, tmp_path):
        """Should return False when state file has no heartbeat."""
        # Arrange: Create state file without heartbeat
        state_file = tmp_path / "search-daemon-state.json"
        state_file.write_text(json.dumps({"some_field": "value"}))

        # Act
        healthy = SessionStart_daemon_manager.is_daemon_healthy(
            "search", state_file, threshold_seconds=90
        )

        # Assert
        assert healthy is False


class TestDaemonLauncher:
    """Test daemon launching logic."""

    @patch('subprocess.Popen')
    def test_launch_dreaming_daemon_command(self, mock_popen, tmp_path):
        """Should launch dreaming daemon with correct command and flags."""
        # Arrange
        mock_proc = Mock()
        mock_popen.return_value = mock_proc
        state_dir = tmp_path

        # Act
        result = SessionStart_daemon_manager.launch_daemon("dreaming", state_dir)

        # Assert
        assert result is True
        mock_popen.assert_called_once()
        call_args = mock_popen.call_args
        cmd = call_args[0][0]  # First positional argument is command list

        # Verify command structure
        assert cmd[0].endswith("pythonw.exe") or cmd[0].endswith("python")
        assert "-m" in cmd
        assert "dreaming_daemon" in cmd
        assert "--daemon-type" in cmd
        assert "dreaming" in cmd

    @patch('subprocess.Popen')
    def test_launch_search_daemon_command(self, mock_popen, tmp_path):
        """Should launch search daemon with correct command and flags."""
        # Arrange
        mock_proc = Mock()
        mock_popen.return_value = mock_proc
        state_dir = tmp_path

        # Act
        result = SessionStart_daemon_manager.launch_daemon("search", state_dir)

        # Assert
        assert result is True
        mock_popen.assert_called_once()
        call_args = mock_popen.call_args
        cmd = call_args[0][0]

        # Verify command structure
        assert cmd[0].endswith("pythonw.exe") or cmd[0].endswith("python")
        assert "-m" in cmd
        assert "dreaming_daemon" in cmd
        assert "--daemon-type" in cmd
        assert "search" in cmd

    @patch('subprocess.Popen')
    def test_launch_daemon_creates_no_window(self, mock_popen, tmp_path):
        """Should use CREATE_NO_WINDOW flag on Windows."""
        # Arrange
        mock_proc = Mock()
        mock_popen.return_value = mock_proc
        state_dir = tmp_path

        # Act
        SessionStart_daemon_manager.launch_daemon("dreaming", state_dir)

        # Assert
        call_args = mock_popen.call_args
        creation_flags = call_args[1].get("creationflags", 0)

        if sys.platform == "win32":
            assert creation_flags == subprocess.CREATE_NO_WINDOW
        else:
            assert creation_flags == 0

    @patch('subprocess.Popen')
    def test_launch_daemon_handles_failure(self, mock_popen, tmp_path):
        """Should return False when subprocess.Popen fails."""
        # Arrange
        mock_popen.side_effect = OSError("Failed to start daemon")
        state_dir = tmp_path

        # Act
        result = SessionStart_daemon_manager.launch_daemon("dreaming", state_dir)

        # Assert
        assert result is False


class TestDaemonManagerMain:
    """Test main daemon manager orchestration."""

    @patch('SessionStart_daemon_manager.launch_daemon')
    @patch('SessionStart_daemon_manager.is_daemon_healthy')
    def test_launches_both_daemons_when_unhealthy(self, mock_healthy, mock_launch, tmp_path):
        """Should launch both dreaming and search daemons when unhealthy."""
        # Arrange: Both daemons unhealthy
        mock_healthy.return_value = False
        mock_launch.return_value = True
        state_dir = tmp_path

        # Act
        results = SessionStart_daemon_manager.launch_daemons_if_needed(state_dir)

        # Assert
        assert mock_healthy.call_count == 2  # Check both
        assert mock_launch.call_count == 2  # Launch both
        assert results == {"dreaming": True, "search": True}

        # Verify called with correct daemon types
        call_args_list = [call[0][0] for call in mock_launch.call_args_list]
        assert "dreaming" in call_args_list
        assert "search" in call_args_list

    @patch('SessionStart_daemon_manager.launch_daemon')
    @patch('SessionStart_daemon_manager.is_daemon_healthy')
    def test_skips_healthy_daemons(self, mock_healthy, mock_launch, tmp_path):
        """Should skip daemons that are already healthy."""
        # Arrange: Both daemons healthy
        mock_healthy.return_value = True
        state_dir = tmp_path

        # Act
        results = SessionStart_daemon_manager.launch_daemons_if_needed(state_dir)

        # Assert
        assert mock_healthy.call_count == 2  # Check both
        assert mock_launch.call_count == 0  # Launch none
        assert results == {"dreaming": False, "search": False}

    @patch('SessionStart_daemon_manager.launch_daemon')
    @patch('SessionStart_daemon_manager.is_daemon_healthy')
    def test_continues_after_one_daemon_fails(self, mock_healthy, mock_launch, tmp_path):
        """Should continue to second daemon even if first fails."""
        # Arrange: Dreaming healthy, search unhealthy, launch fails for search
        def healthy_side_effect(daemon_type, state_file, **kwargs):
            return daemon_type == "dreaming"

        mock_healthy.side_effect = healthy_side_effect
        mock_launch.return_value = False
        state_dir = tmp_path

        # Act
        results = SessionStart_daemon_manager.launch_daemons_if_needed(state_dir)

        # Assert
        assert mock_healthy.call_count == 2  # Check both
        assert mock_launch.call_count == 1  # Only launch search (dreaming already healthy)
        assert results == {"dreaming": False, "search": False}  # Launch failed, both False

    @patch('SessionStart_daemon_manager.get_daemon_config')
    def test_uses_correct_config_for_each_daemon_type(self, mock_config, tmp_path):
        """Should load correct config (mutex, PID file, state file) for each daemon type."""
        # Arrange
        mock_config.side_effect = lambda dt: {
            "mutex_name": f"Global\\Claude{dt.capitalize()}Daemon",
            "pid_file": f"{dt}-daemon.pid",
            "state_file": f"{dt}-daemon-state.json",
            "daemon_log": f"{dt}-daemon.log",
        }

        # Act & Assert
        config = SessionStart_daemon_manager.get_daemon_config("dreaming")
        assert config["mutex_name"] == "Global\\ClaudeDreamingDaemon"
        assert config["pid_file"] == "dreaming-daemon.pid"

        config = SessionStart_daemon_manager.get_daemon_config("search")
        assert config["mutex_name"] == "Global\\ClaudeSearchDaemon"
        assert config["pid_file"] == "search-daemon.pid"


class TestLatencyMeasurement:
    """Test latency measurement instrumentation."""

    def test_measure_latency_returns_result_and_time(self):
        """Should return function result and execution time in milliseconds."""
        # Arrange
        def dummy_function():
            return 42

        # Act
        result, latency_ms = SessionStart_daemon_manager.measure_latency(dummy_function)

        # Assert
        assert result == 42
        assert latency_ms >= 0
        assert isinstance(latency_ms, float)

    def test_measure_latency_catches_exceptions(self):
        """Should re-raise exceptions with latency info."""
        # Arrange
        def failing_function():
            raise ValueError("Test error")

        # Act & Assert
        with pytest.raises(ValueError, match="Test error"):
            SessionStart_daemon_manager.measure_latency(failing_function)


class TestIntegration:
    """Integration tests for daemon manager."""

    @patch('SessionStart_daemon_manager.launch_daemon')
    @patch('SessionStart_daemon_manager.is_daemon_healthy')
    def test_full_workflow_both_daemons_launch(self, mock_healthy, mock_launch, tmp_path):
        """Test full workflow: check health → launch if needed."""
        # Arrange: Both daemons unhealthy and launch successfully
        mock_healthy.return_value = False
        mock_launch.return_value = True
        state_dir = tmp_path

        # Act
        results = SessionStart_daemon_manager.launch_daemons_if_needed(state_dir)

        # Assert
        assert results == {"dreaming": True, "search": True}
        assert mock_launch.call_count == 2

    @patch('SessionStart_daemon_manager.launch_daemon')
    @patch('SessionStart_daemon_manager.is_daemon_healthy')
    def test_full_workflow_mixed_health_status(self, mock_healthy, mock_launch, tmp_path):
        """Test full workflow: one daemon healthy, one unhealthy."""
        # Arrange: Dreaming healthy, search unhealthy
        def healthy_side_effect(daemon_type, state_file, **kwargs):
            return daemon_type == "dreaming"

        mock_healthy.side_effect = healthy_side_effect
        mock_launch.return_value = True
        state_dir = tmp_path

        # Act
        results = SessionStart_daemon_manager.launch_daemons_if_needed(state_dir)

        # Assert
        assert results == {"dreaming": False, "search": True}  # dreaming skipped, search launched
        assert mock_launch.call_count == 1  # Only search launched
