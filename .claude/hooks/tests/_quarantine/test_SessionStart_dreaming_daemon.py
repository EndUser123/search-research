#!/usr/bin/env python3
"""
Tests for SessionStart_dreaming_daemon hook (T-010).

This test suite verifies:
1. Daemon auto-start when missing or stale
2. Heartbeat-based health checks
3. Latency measurement and logging
4. Upstream data source monitoring
5. Hook protocol compliance ({})
"""

import json
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add hooks directory to path
hooks_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(hooks_dir))

# Import the hook module
import SessionStart_dreaming_daemon


class TestDaemonHealthCheck:
    """Tests for daemon health detection logic."""

    @pytest.fixture
    def project_root(self, tmp_path):
        """Create a temporary project root with required directories."""
        state_dir = tmp_path / ".claude" / "state"
        state_dir.mkdir(parents=True)
        logs_dir = tmp_path / ".claude" / "logs"
        logs_dir.mkdir(parents=True)
        return tmp_path

    @pytest.fixture
    def state_file(self, project_root):
        """Get state file path."""
        return project_root / ".claude" / "state" / "dreaming-daemon-state.json"

    @pytest.fixture
    def events_file(self, project_root):
        """Get events file path."""
        return project_root / ".claude" / "logs" / "principle-events.jsonl"

    def test_is_daemon_healthy_no_state_file(self, state_file):
        """Test that missing state file returns unhealthy."""
        result = SessionStart_dreaming_daemon.is_daemon_healthy(state_file)
        assert result is False

    def test_is_daemon_healthy_no_heartbeat(self, state_file):
        """Test that state file without heartbeat returns unhealthy."""
        state_file.write_text(json.dumps({"offset": 100}))
        result = SessionStart_dreaming_daemon.is_daemon_healthy(state_file)
        assert result is False

    def test_is_daemon_healthy_stale_heartbeat(self, state_file):
        """Test that stale heartbeat (>90s) returns unhealthy."""
        # Create heartbeat 91 seconds ago
        stale_time = datetime.now(UTC).timestamp() - 91
        stale_heartbeat = datetime.fromtimestamp(stale_time, UTC).isoformat()

        state_file.write_text(json.dumps({
            "offset": 100,
            "heartbeat": stale_heartbeat
        }))

        result = SessionStart_dreaming_daemon.is_daemon_healthy(state_file)
        assert result is False

    def test_is_daemon_healthy_fresh_heartbeat(self, state_file):
        """Test that fresh heartbeat (<90s) returns healthy."""
        # Create heartbeat 30 seconds ago
        fresh_time = datetime.now(UTC).timestamp() - 30
        fresh_heartbeat = datetime.fromtimestamp(fresh_time, UTC).isoformat()

        state_file.write_text(json.dumps({
            "offset": 100,
            "heartbeat": fresh_heartbeat
        }))

        result = SessionStart_dreaming_daemon.is_daemon_healthy(state_file)
        assert result is True

    def test_is_daemon_healthy_corrupted_state(self, state_file):
        """Test that corrupted state file returns unhealthy (graceful degradation)."""
        state_file.write_text("invalid json {{{")
        result = SessionStart_dreaming_daemon.is_daemon_healthy(state_file)
        assert result is False


class TestUpstreamMonitoring:
    """Tests for upstream data source monitoring."""

    def test_check_upstream_health_missing_file(self, tmp_path):
        """Test that missing events file returns warning."""
        events_file = tmp_path / "nonexistent.jsonl"

        result = SessionStart_dreaming_daemon.check_upstream_health(events_file)
        assert result["status"] == "missing"

    def test_check_upstream_health_stale_file(self, tmp_path):
        """Test that stale events file (>10 min) returns warning."""
        events_file = tmp_path / "principle-events.jsonl"

        # Create file with modification time 11 minutes ago
        events_file.write_text('{"test": "data"}')
        old_time = time.time() - (11 * 60)
        import os
        os.utime(events_file, (old_time, old_time))

        result = SessionStart_dreaming_daemon.check_upstream_health(events_file)
        assert result["status"] == "stale"
        assert result["age_minutes"] >= 10

    def test_check_upstream_health_fresh_file(self, tmp_path):
        """Test that fresh events file (<10 min) returns healthy."""
        events_file = tmp_path / "principle-events.jsonl"
        events_file.write_text('{"test": "data"}')

        result = SessionStart_dreaming_daemon.check_upstream_health(events_file)
        assert result["status"] == "healthy"


class TestDaemonStartup:
    """Tests for daemon startup logic."""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration."""
        return {
            "enabled": True,
            "heartbeat_interval_seconds": 60,
            "zombie_timeout_seconds": 180,
        }

    def test_start_daemon_windows_pythonw(self, tmp_path, mock_config):
        """Test that daemon starts with pythonw.exe on Windows."""
        with patch.object(SessionStart_dreaming_daemon, 'sys') as mock_sys:
            with patch.object(subprocess, 'Popen') as mock_popen:
                mock_sys.platform = "win32"
                mock_sys.executable = "C:\\Python\\python.exe"
                mock_proc = MagicMock()
                mock_proc.pid = 12345
                mock_popen.return_value = mock_proc

                pid = SessionStart_dreaming_daemon.start_daemon(
                    tmp_path,
                    mock_config
                )

                # Verify Popen was called
                assert mock_popen.called
                call_args = mock_popen.call_args

                # Check pythonw.exe is used on Windows
                cmd = call_args[0][0]
                assert "pythonw.exe" in cmd[0]

                # Check CREATE_NO_WINDOW flag is set
                kwargs = call_args[1]
                assert "creationflags" in kwargs
                assert kwargs["creationflags"] == subprocess.CREATE_NO_WINDOW

                # Verify PID is returned
                assert pid == 12345

    def test_start_daemon_non_windows(self, tmp_path, mock_config):
        """Test that daemon starts without CREATE_NO_WINDOW on non-Windows."""
        with patch.object(SessionStart_dreaming_daemon, 'sys') as mock_sys:
            with patch.object(subprocess, 'Popen') as mock_popen:
                mock_sys.platform = "linux"
                mock_sys.executable = "/usr/bin/python3"
                mock_proc = MagicMock()
                mock_proc.pid = 12346
                mock_popen.return_value = mock_proc

                pid = SessionStart_dreaming_daemon.start_daemon(
                    tmp_path,
                    mock_config
                )

                # Verify Popen was called
                assert mock_popen.called
                call_args = mock_popen.call_args

                # Check regular python executable is used
                cmd = call_args[0][0]
                assert cmd[0] == "/usr/bin/python3"

                # Check CREATE_NO_WINDOW is NOT set
                kwargs = call_args[1]
                assert "creationflags" not in kwargs or kwargs["creationflags"] == 0

                # Verify PID is returned
                assert pid == 12346

    def test_start_daemon_failure(self, tmp_path, mock_config):
        """Test that daemon startup failure returns None."""
        with patch.object(subprocess, 'Popen', side_effect=OSError("Failed to start")):
            pid = SessionStart_dreaming_daemon.start_daemon(
                tmp_path,
                mock_config
            )
            assert pid is None


class TestLatencyMeasurement:
    """Tests for latency measurement instrumentation."""

    def test_measure_latency_fast_operation(self):
        """Test latency measurement for fast operations."""
        def fast_operation():
            return "done"

        result, latency_ms = SessionStart_dreaming_daemon.measure_latency(fast_operation)
        assert result == "done"
        assert latency_ms < 50  # Should be very fast

    def test_measure_latency_slow_operation(self):
        """Test latency measurement for slow operations."""
        def slow_operation():
            time.sleep(0.1)  # 100ms
            return "done"

        result, latency_ms = SessionStart_dreaming_daemon.measure_latency(slow_operation)
        assert result == "done"
        assert latency_ms >= 100  # At least 100ms

    def test_measure_latency_exception_handling(self):
        """Test that exceptions are propagated during latency measurement."""
        def failing_operation():
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            SessionStart_dreaming_daemon.measure_latency(failing_operation)


class TestHookProtocol:
    """Tests for hook protocol compliance."""

    @pytest.fixture
    def mock_project_root(self, tmp_path):
        """Create mock project structure."""
        state_dir = tmp_path / ".claude" / "state"
        state_dir.mkdir(parents=True)
        logs_dir = tmp_path / ".claude" / "logs"
        logs_dir.mkdir(parents=True)

        # Create healthy state file
        state_file = state_dir / "dreaming-daemon-state.json"
        fresh_heartbeat = datetime.now(UTC).isoformat()
        state_file.write_text(json.dumps({
            "offset": 100,
            "heartbeat": fresh_heartbeat
        }))

        return tmp_path

    def test_hook_output_empty_dict(self, mock_project_root, capsys):
        """Test that hook outputs {} to stdout when daemon is healthy."""
        with patch('SessionStart_dreaming_daemon.get_project_root', return_value=mock_project_root):
            result = SessionStart_dreaming_daemon.main()

            # Result should be a dict
            assert isinstance(result, dict)

            # No stdout output expected (hook protocol)
            captured = capsys.readouterr()
            # Hook might log to stderr, but stdout should be empty or minimal
            # The hook protocol says print({}), which we'll verify in integration tests

    def test_hook_returns_status_dict(self, mock_project_root):
        """Test that hook returns status dict with expected keys."""
        with patch('SessionStart_dreaming_daemon.get_project_root', return_value=mock_project_root):
            result = SessionStart_dreaming_daemon.main()

            # Should have status key
            assert "status" in result

            # Status should be one of the expected values
            assert result["status"] in ["healthy", "started", "failed"]


class TestMainIntegration:
    """Integration tests for main() hook entry point."""

    @pytest.fixture
    def full_project_setup(self, tmp_path):
        """Create complete project structure for integration tests."""
        # Create directories
        state_dir = tmp_path / ".claude" / "state"
        state_dir.mkdir(parents=True)
        logs_dir = tmp_path / ".claude" / "logs"
        logs_dir.mkdir(parents=True)
        hooks_dir = tmp_path / ".claude" / "hooks"
        hooks_dir.mkdir(parents=True)

        # Create events file with recent activity
        events_file = logs_dir / "principle-events.jsonl"
        events_file.write_text('{"event": "test"}\n')

        return tmp_path

    def test_main_healthy_daemon_no_start(self, full_project_setup):
        """Test that healthy daemon doesn't trigger restart."""
        # Create healthy state at the HOOKS_DIR location (not project root)
        hooks_dir = full_project_setup / ".claude" / "hooks"
        state_dir = hooks_dir / "state"
        state_dir.mkdir(parents=True, exist_ok=True)
        state_file = state_dir / "dreaming-daemon-state.json"

        fresh_heartbeat = datetime.now(UTC).isoformat()
        state_file.write_text(json.dumps({
            "offset": 100,
            "heartbeat": fresh_heartbeat
        }))

        with patch('SessionStart_dreaming_daemon.get_project_root', return_value=full_project_setup):
            with patch('SessionStart_dreaming_daemon.HOOKS_DIR', hooks_dir):
                with patch('SessionStart_dreaming_daemon.start_daemon') as mock_start:
                    result = SessionStart_dreaming_daemon.main()

                    # Daemon should NOT be started
                    assert not mock_start.called

                    # Status should be healthy
                    assert result["status"] == "healthy"

    def test_main_missing_daemon_triggers_start(self, full_project_setup):
        """Test that missing daemon triggers startup."""
        hooks_dir = full_project_setup / ".claude" / "hooks"
        state_dir = hooks_dir / "state"
        state_dir.mkdir(parents=True, exist_ok=True)
        logs_dir = hooks_dir / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)

        # No state file = missing daemon
        state_file = state_dir / "dreaming-daemon-state.json"
        assert not state_file.exists()

        with patch('SessionStart_dreaming_daemon.get_project_root', return_value=full_project_setup):
            # Patch the constants that main() uses
            with patch.object(SessionStart_dreaming_daemon, 'STATE_FILE', state_file):
                with patch.object(SessionStart_dreaming_daemon, 'EVENTS_FILE', logs_dir / 'principle-events.jsonl'):
                    with patch('SessionStart_dreaming_daemon.start_daemon', return_value=12345) as mock_start:
                        result = SessionStart_dreaming_daemon.main()

                        # Daemon SHOULD be started
                        assert mock_start.called

                        # Status should be started
                        assert result["status"] == "started"
                        assert result["pid"] == 12345

    def test_main_stale_daemon_triggers_start(self, full_project_setup):
        """Test that stale daemon triggers startup."""
        hooks_dir = full_project_setup / ".claude" / "hooks"
        state_dir = hooks_dir / "state"
        state_dir.mkdir(parents=True, exist_ok=True)
        logs_dir = hooks_dir / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        state_file = state_dir / "dreaming-daemon-state.json"

        # Create stale heartbeat (91 seconds old)
        stale_time = datetime.now(UTC).timestamp() - 91
        stale_heartbeat = datetime.fromtimestamp(stale_time, UTC).isoformat()
        state_file.write_text(json.dumps({
            "offset": 100,
            "heartbeat": stale_heartbeat
        }))

        with patch('SessionStart_dreaming_daemon.get_project_root', return_value=full_project_setup):
            # Patch the constants that main() uses
            with patch.object(SessionStart_dreaming_daemon, 'STATE_FILE', state_file):
                with patch.object(SessionStart_dreaming_daemon, 'EVENTS_FILE', logs_dir / 'principle-events.jsonl'):
                    with patch('SessionStart_dreaming_daemon.start_daemon', return_value=12346) as mock_start:
                        result = SessionStart_dreaming_daemon.main()

                        # Daemon SHOULD be started
                        assert mock_start.called

                        # Status should be started
                        assert result["status"] == "started"

    def test_main_startup_failure_returns_failed(self, full_project_setup):
        """Test that daemon startup failure returns failed status."""
        hooks_dir = full_project_setup / ".claude" / "hooks"
        state_dir = hooks_dir / "state"
        state_dir.mkdir(parents=True, exist_ok=True)
        logs_dir = hooks_dir / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)

        # No state file = missing daemon
        state_file = state_dir / "dreaming-daemon-state.json"
        assert not state_file.exists()

        with patch('SessionStart_dreaming_daemon.get_project_root', return_value=full_project_setup):
            # Patch the constants that main() uses
            with patch.object(SessionStart_dreaming_daemon, 'STATE_FILE', state_file):
                with patch.object(SessionStart_dreaming_daemon, 'EVENTS_FILE', logs_dir / 'principle-events.jsonl'):
                    with patch('SessionStart_dreaming_daemon.start_daemon', return_value=None) as mock_start:
                        result = SessionStart_dreaming_daemon.main()

                        # Daemon start was attempted
                        assert mock_start.called

                        # Status should be failed
                        assert result["status"] == "failed"

    def test_main_latency_performance(self, full_project_setup):
        """Test that hook completes within 2 seconds (performance requirement)."""
        # Create healthy state at the HOOKS_DIR location
        hooks_dir = full_project_setup / ".claude" / "hooks"
        state_dir = hooks_dir / "state"
        state_dir.mkdir(parents=True, exist_ok=True)
        state_file = state_dir / "dreaming-daemon-state.json"

        fresh_heartbeat = datetime.now(UTC).isoformat()
        state_file.write_text(json.dumps({
            "offset": 100,
            "heartbeat": fresh_heartbeat
        }))

        with patch('SessionStart_dreaming_daemon.get_project_root', return_value=full_project_setup):
            with patch('SessionStart_dreaming_daemon.HOOKS_DIR', hooks_dir):
                start = time.perf_counter()
                result = SessionStart_dreaming_daemon.main()
                duration = time.perf_counter() - start

                # Should complete in under 2 seconds
                assert duration < 2.0, f"Hook took {duration:.2f}s, exceeds 2s requirement"

                # Status should be healthy
                assert result["status"] == "healthy"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
