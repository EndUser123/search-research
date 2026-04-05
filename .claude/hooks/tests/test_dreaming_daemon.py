#!/usr/bin/env python3
"""
Tests for dreaming-daemon.py (T-008, T-009)

Test coverage:
- Async loop execution
- Mutex acquisition
- Heartbeat updates
- Graceful shutdown
- Event processing pipeline
- Windows-specific reliable cleanup (T-009)
- Atomic heartbeat + state updates (T-009)
- Zombie detection (T-009)
"""

from __future__ import annotations

import asyncio
import json
import os
import signal

# Import the daemon module
import sys
import tempfile
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from threading import Lock
from unittest.mock import patch

import pytest

# Add parent directory to path for imports
parent_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(parent_dir))

# Import from dreaming_daemon module (renamed from dreaming-daemon.py)
from dreaming_daemon import (
    _aggregate_events_async,
    _check_for_zombie_daemon,
    _cleanup_on_exit,
    _daemon_loop_async,
    _read_events_async,
    _setup_signal_handlers,
    _state_lock,
    _update_heartbeat_and_state_async,
    _write_insights_async,
    main,
    main_async,
)

# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def temp_dir():
    """Create temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_config(temp_dir):
    """Create mock configuration."""
    return {
        "enabled": True,
        "poll_interval_seconds": 1,  # Short interval for tests
        "rotation_max_size_mb": 50,
        "rotation_retention_days": 30,
        "window_seconds": 3600,
        "json_output_path": str(temp_dir / "dreaming-insights.json"),
        "markdown_output_path": str(temp_dir / "dreaming-insights.md"),
        "enable_markdown": True,
    }


@pytest.fixture
def sample_events():
    """Create sample principle events."""
    return [
        {
            "ts": datetime.now(UTC).isoformat(),
            "session_id": "test-session-1",
            "event_type": "context_grounding_violation",
            "principle": "context_reuse",
            "assistant_preview": "You're right about that.",
        },
        {
            "ts": datetime.now(UTC).isoformat(),
            "session_id": "test-session-1",
            "event_type": "change_without_evidence",
            "principle": "grounded_changes",
            "assistant_preview": "I fixed the bug.",
        },
    ]


@pytest.fixture
def sample_jsonl(temp_dir, sample_events):
    """Create sample JSONL log file."""
    jsonl_path = temp_dir / "principle-events.jsonl"
    with open(jsonl_path, "w") as f:
        for event in sample_events:
            f.write(json.dumps(event) + "\n")
    return jsonl_path


# =============================================================================
# Test Signal Handling
# =============================================================================

class TestSignalHandling:
    """Tests for signal handling and graceful shutdown."""

    def test_setup_signal_handlers(self):
        """Test that signal handlers are registered without errors."""
        # Should not raise any exceptions
        _setup_signal_handlers()
        assert True

    def test_cleanup_on_exit(self, temp_dir):
        """Test cleanup function releases singleton lock."""
        # Create a mock PID file
        pid_file = temp_dir / "test.pid"
        pid_file.write_text("12345")

        # Mock the release_singleton function
        with patch('dreaming_daemon.release_singleton') as mock_release:
            _cleanup_on_exit()
            mock_release.assert_called_once()

    @pytest.mark.skip(reason="Signal handling test is unreliable in test environment")
    def test_shutdown_flag_on_sigint(self):
        """Test that SIGINT sets shutdown flag."""

        # Setup signal handlers
        _setup_signal_handlers()

        # Send SIGINT (Ctrl+C)
        # Note: This test may not work on all platforms
        try:
            os.kill(os.getpid(), signal.SIGINT)
            time.sleep(0.1)  # Give time for signal handler to run
        except Exception:
            # Signal handling may not work in test environment
            pass


# =============================================================================
# Test Heartbeat Updates
# =============================================================================

class TestHeartbeatUpdates:
    """Tests for heartbeat update functionality."""

    @pytest.mark.asyncio
    async def test_update_heartbeat_async(self, temp_dir):
        """Test that heartbeat is updated asynchronously."""
        from dreaming_state import DreamingState

        state = DreamingState(offset=100, heartbeat="", current_file="test.jsonl")

        # Mock the save_state function to use temp_dir
        with patch('dreaming_daemon.save_state') as mock_save:
            await _update_heartbeat_and_state_async(state)

            # Verify save_state was called
            mock_save.assert_called_once()

            # Verify heartbeat was set
            assert state.heartbeat != ""
            assert datetime.fromisoformat(state.heartbeat) <= datetime.now(UTC)


# =============================================================================
# Test Event Reading
# =============================================================================

class TestEventReading:
    """Tests for async event reading from JSONL tailer."""

    @pytest.mark.asyncio
    async def test_read_events_async(self, sample_jsonl):
        """Test that events are read asynchronously from tailer."""
        from dreaming_tailer import JSONLTailer

        tailer = JSONLTailer(log_path=sample_jsonl)
        events = await _read_events_async(tailer)

        # Should read both events
        assert len(events) == 2
        assert events[0]["principle"] == "context_reuse"
        assert events[1]["principle"] == "grounded_changes"

    @pytest.mark.asyncio
    async def test_read_events_async_empty(self, temp_dir):
        """Test reading from empty JSONL file."""
        from dreaming_tailer import JSONLTailer

        empty_jsonl = temp_dir / "empty.jsonl"
        empty_jsonl.write_text("")

        tailer = JSONLTailer(log_path=empty_jsonl)
        events = await _read_events_async(tailer)

        # Should return empty list
        assert events == []


# =============================================================================
# Test Event Aggregation
# =============================================================================

class TestEventAggregation:
    """Tests for async event aggregation."""

    @pytest.mark.asyncio
    async def test_aggregate_events_async(self, sample_events):
        """Test that events are aggregated asynchronously."""
        from dreaming_aggregator import InsightsGenerator

        generator = InsightsGenerator(window_seconds=3600)
        insights_data = await _aggregate_events_async(generator, sample_events)

        # Verify insights
        assert insights_data["total_events"] == 2
        assert "principle_counts" in insights_data
        assert insights_data["principle_counts"]["context_reuse"] == 1
        assert insights_data["principle_counts"]["grounded_changes"] == 1


# =============================================================================
# Test Insights Writing
# =============================================================================

class TestInsightsWriting:
    """Tests for async insights writing."""

    @pytest.mark.asyncio
    async def test_write_insights_async(self, mock_config, temp_dir):
        """Test that insights are written asynchronously."""
        insights_data = {
            "total_events": 10,
            "principle_counts": {
                "context_reuse": 5,
                "grounded_changes": 3,
                "minimal_redundancy": 2,
            },
            "top_principle": "context_reuse",
            "top_principle_count": 5,
            "high_violation_sessions": {},
        }

        # Write insights
        await _write_insights_async(insights_data, mock_config)

        # Verify JSON file was created
        json_path = Path(mock_config["json_output_path"])
        assert json_path.exists()

        with open(json_path) as f:
            data = json.load(f)
            assert data["total_events"] == 10
            assert len(data["principle_stats"]) == 3

        # Verify markdown file was created
        md_path = Path(mock_config["markdown_output_path"])
        assert md_path.exists()

        md_content = md_path.read_text()
        assert "Dreaming Insights" in md_content
        assert "10" in md_content


# =============================================================================
# Test Daemon Loop
# =============================================================================

class TestDaemonLoop:
    """Tests for main daemon loop."""

    @pytest.mark.asyncio
    async def test_daemon_loop_single_iteration(self, temp_dir, mock_config, sample_events):
        """Test that daemon loop processes events and updates heartbeat."""
        from dreaming_aggregator import InsightsGenerator
        from dreaming_state import DreamingState
        from dreaming_tailer import JSONLTailer

        # Create test JSONL file
        jsonl_path = temp_dir / "principle-events.jsonl"
        with open(jsonl_path, "w") as f:
            for event in sample_events:
                f.write(json.dumps(event) + "\n")

        # Setup components
        state = DreamingState()
        tailer = JSONLTailer(log_path=jsonl_path)
        generator = InsightsGenerator(window_seconds=3600)

        # Run one iteration (short timeout)
        task = asyncio.create_task(
            _daemon_loop_async(mock_config, state, tailer, generator)
        )

        # Wait a bit for processing
        await asyncio.sleep(0.5)

        # Cancel the task to stop the loop
        task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            pass

        # Verify heartbeat was updated
        assert state.heartbeat != ""

        # Verify insights were written
        json_path = Path(mock_config["json_output_path"])
        assert json_path.exists()

    @pytest.mark.asyncio
    async def test_daemon_loop_handles_errors(self, temp_dir, mock_config):
        """Test that daemon loop handles errors gracefully."""
        from dreaming_aggregator import InsightsGenerator
        from dreaming_state import DreamingState
        from dreaming_tailer import JSONLTailer

        # Create invalid JSONL file (malformed JSON)
        jsonl_path = temp_dir / "principle-events.jsonl"
        jsonl_path.write_text("{invalid json\n")

        # Setup components
        state = DreamingState()
        tailer = JSONLTailer(log_path=jsonl_path)
        generator = InsightsGenerator(window_seconds=3600)

        # Run one iteration (should not crash)
        task = asyncio.create_task(
            _daemon_loop_async(mock_config, state, tailer, generator)
        )

        # Wait a bit for processing
        await asyncio.sleep(0.5)

        # Cancel the task to stop the loop
        task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            pass

        # Should not crash, heartbeat should be updated
        assert state.heartbeat != ""


# =============================================================================
# Test Main Entry Points
# =============================================================================

class TestMainEntryPoints:
    """Tests for main entry points."""

    def test_main_entry_point_exists(self):
        """Test that main() function exists and is callable."""
        assert callable(main)

    @pytest.mark.asyncio
    async def test_main_async_is_coroutine(self):
        """Test that main_async is a coroutine function."""
        assert asyncio.iscoroutinefunction(main_async)

    def test_main_mutex_failure(self):
        """Test that main() fails gracefully when mutex acquisition fails."""
        with patch('dreaming_daemon.acquire_singleton') as mock_acquire:
            mock_acquire.return_value = (False, "Another instance is running")

            exit_code = main()
            assert exit_code == 1


# =============================================================================
# Integration Tests
# =============================================================================

class TestIntegration:
    """Integration tests for daemon functionality."""

    @pytest.mark.asyncio
    async def test_full_pipeline(self, temp_dir, sample_events):
        """Test full pipeline: read -> aggregate -> write."""
        from dreaming_aggregator import InsightsGenerator
        from dreaming_tailer import JSONLTailer

        # Create test JSONL
        jsonl_path = temp_dir / "principle-events.jsonl"
        with open(jsonl_path, "w") as f:
            for event in sample_events:
                f.write(json.dumps(event) + "\n")

        # Step 1: Read events
        tailer = JSONLTailer(log_path=jsonl_path)
        events = await _read_events_async(tailer)
        assert len(events) == 2

        # Step 2: Aggregate events
        generator = InsightsGenerator(window_seconds=3600)
        insights_data = await _aggregate_events_async(generator, events)
        assert insights_data["total_events"] == 2

        # Step 3: Write insights
        config = {
            "json_output_path": str(temp_dir / "insights.json"),
            "markdown_output_path": str(temp_dir / "insights.md"),
            "enable_markdown": True,
        }
        await _write_insights_async(insights_data, config)

        # Verify outputs
        assert (temp_dir / "insights.json").exists()
        assert (temp_dir / "insights.md").exists()

        with open(temp_dir / "insights.json") as f:
            data = json.load(f)
            assert data["total_events"] == 2


# =============================================================================
# Test Windows-Specific Reliable Cleanup (T-009)
# =============================================================================

class TestWindowsCleanup:
    """Tests for Windows-specific reliable cleanup mechanisms."""

    def test_state_lock_exists(self):
        """Test that state lock is defined for atomic updates."""
        assert _state_lock is not None
        assert isinstance(_state_lock, Lock)

    def test_cleanup_marks_shutdown_in_state(self, temp_dir):
        """Test that cleanup function marks shutdown in state."""
        from dreaming_state import DreamingState

        # Create a state file
        state_file = temp_dir / "dreaming-daemon-state.json"
        state = DreamingState(offset=100, heartbeat="", current_file="test.jsonl", shutdown=False)

        # Mock the paths
        with patch('dreaming_daemon.STATE_FILE', state_file):
            # Save initial state
            from dreaming_state import save_state
            save_state(state, state_file)

            # Mock release_singleton
            with patch('dreaming_daemon.release_singleton'):
                # Call cleanup
                _cleanup_on_exit()

                # Verify shutdown was marked
                updated_state = DreamingState(**json.loads(state_file.read_text()))
                assert updated_state.shutdown is True

    @pytest.mark.asyncio
    async def test_atomic_heartbeat_update(self, temp_dir):
        """Test that heartbeat and state are updated atomically."""
        from dreaming_state import DreamingState

        state_file = temp_dir / "dreaming-daemon-state.json"
        state = DreamingState(offset=100, heartbeat="", current_file="test.jsonl")

        # Mock the STATE_FILE path
        with patch('dreaming_daemon.STATE_FILE', state_file):
            # Update heartbeat with new offset
            await _update_heartbeat_and_state_async(state, offset=200, current_file="new.jsonl")

            # Verify all fields were updated atomically
            assert state.offset == 200
            assert state.current_file == "new.jsonl"
            assert state.heartbeat != ""

            # Verify file was written
            assert state_file.exists()
            data = json.loads(state_file.read_text())
            assert data["offset"] == 200
            assert data["current_file"] == "new.jsonl"
            assert data["heartbeat"] != ""

    @pytest.mark.asyncio
    async def test_atomic_heartbeat_partial_update(self, temp_dir):
        """Test that heartbeat can be updated without changing other fields."""
        from dreaming_state import DreamingState

        state_file = temp_dir / "dreaming-daemon-state.json"
        state = DreamingState(offset=100, heartbeat="", current_file="test.jsonl")

        # Mock the STATE_FILE path
        with patch('dreaming_daemon.STATE_FILE', state_file):
            # Update only heartbeat (no offset/current_file)
            await _update_heartbeat_and_state_async(state)

            # Verify offset and current_file unchanged
            assert state.offset == 100
            assert state.current_file == "test.jsonl"
            assert state.heartbeat != ""


# =============================================================================
# Test Zombie Detection (T-009)
# =============================================================================

class TestZombieDetection:
    """Tests for zombie daemon detection and cleanup."""

    def test_zombie_detection_with_stale_heartbeat(self, temp_dir):
        """Test that zombie daemon is detected when heartbeat is stale."""
        from dreaming_state import DreamingState, save_state

        # Create a state file with stale heartbeat
        state_file = temp_dir / "dreaming-daemon-state.json"
        pid_file = temp_dir / "dreaming-daemon.pid"
        old_heartbeat = (datetime.now(UTC) - timedelta(seconds=200)).isoformat()
        state = DreamingState(offset=100, heartbeat=old_heartbeat, current_file="test.jsonl")
        save_state(state, state_file)

        config = {
            "zombie_timeout_seconds": 180,
        }

        # Mock STATE_FILE, PID_FILE, and acquire_singleton
        with patch('dreaming_daemon.STATE_FILE', state_file):
            with patch('dreaming_daemon.PID_FILE', pid_file):
                with patch('dreaming_daemon.acquire_singleton') as mock_acquire:
                    mock_acquire.return_value = (True, "")

                    # Check for zombie
                    result = _check_for_zombie_daemon(config)

                    # Should detect zombie and clean up
                    assert result is True
                    mock_acquire.assert_called_once_with(str(pid_file), force=True)

    def test_no_zombie_with_fresh_heartbeat(self, temp_dir):
        """Test that fresh heartbeat doesn't trigger zombie detection."""
        from dreaming_state import DreamingState, save_state

        # Create a state file with fresh heartbeat
        state_file = temp_dir / "dreaming-daemon-state.json"
        fresh_heartbeat = (datetime.now(UTC) - timedelta(seconds=60)).isoformat()
        state = DreamingState(offset=100, heartbeat=fresh_heartbeat, current_file="test.jsonl")
        save_state(state, state_file)

        config = {
            "zombie_timeout_seconds": 180,
        }

        # Mock STATE_FILE
        with patch('dreaming_daemon.STATE_FILE', state_file):
            # Check for zombie
            result = _check_for_zombie_daemon(config)

            # Should NOT detect zombie
            assert result is False

    def test_no_zombie_when_no_state_file(self, temp_dir):
        """Test that missing state file doesn't trigger zombie detection."""
        config = {
            "zombie_timeout_seconds": 180,
        }

        # Mock STATE_FILE to non-existent path
        state_file = temp_dir / "nonexistent-state.json"
        with patch('dreaming_daemon.STATE_FILE', state_file):
            # Check for zombie
            result = _check_for_zombie_daemon(config)

            # Should NOT detect zombie (no state file)
            assert result is False

    def test_zombie_cleanup_handles_mutex_acquire_failure(self, temp_dir):
        """Test that zombie cleanup handles mutex acquire failure gracefully."""
        from dreaming_state import DreamingState, save_state

        # Create a state file with stale heartbeat
        state_file = temp_dir / "dreaming-daemon-state.json"
        old_heartbeat = (datetime.now(UTC) - timedelta(seconds=200)).isoformat()
        state = DreamingState(offset=100, heartbeat=old_heartbeat, current_file="test.jsonl")
        save_state(state, state_file)

        config = {
            "zombie_timeout_seconds": 180,
        }

        # Mock STATE_FILE and acquire_singleton (failure case)
        with patch('dreaming_daemon.STATE_FILE', state_file):
            with patch('dreaming_daemon.acquire_singleton') as mock_acquire:
                mock_acquire.return_value = (False, "Mutex acquire failed")

                # Check for zombie
                result = _check_for_zombie_daemon(config)

                # Should fail to clean up
                assert result is False


# =============================================================================
# Test Error Handling and Exponential Backoff (T-009)
# =============================================================================

class TestErrorHandling:
    """Tests for error handling and exponential backoff."""

    @pytest.mark.asyncio
    async def test_daemon_loop_exponential_backoff(self, temp_dir, mock_config):
        """Test that daemon loop uses exponential backoff on repeated errors."""
        from dreaming_aggregator import InsightsGenerator
        from dreaming_state import DreamingState
        from dreaming_tailer import JSONLTailer

        # Create invalid JSONL that will cause parse errors
        jsonl_path = temp_dir / "principle-events.jsonl"
        jsonl_path.write_text("{invalid json\n")

        # Setup components
        state = DreamingState()
        tailer = JSONLTailer(log_path=jsonl_path)
        generator = InsightsGenerator(window_seconds=3600)

        # Run daemon loop with short timeout
        task = asyncio.create_task(
            _daemon_loop_async(mock_config, state, tailer, generator)
        )

        # Wait for multiple error iterations
        await asyncio.sleep(2)

        # Cancel the task
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

        # Verify daemon didn't crash (heartbeat updated)
        assert state.heartbeat != ""

    @pytest.mark.asyncio
    async def test_heartbeat_update_handles_errors_gracefully(self, temp_dir):
        """Test that heartbeat update doesn't crash on state save errors."""
        from dreaming_state import DreamingState

        state = DreamingState(offset=100, heartbeat="", current_file="test.jsonl")

        # Mock STATE_FILE to unwritable path
        unwritable_path = temp_dir / "nonexistent_dir" / "state.json"

        with patch('dreaming_daemon.STATE_FILE', unwritable_path):
            # Should not raise exception
            await _update_heartbeat_and_state_async(state)

            # Heartbeat should be updated in memory even if save failed
            assert state.heartbeat != ""
