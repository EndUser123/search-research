"""Tests for TerminalStateManager."""

import json
import os
from unittest.mock import patch

import pytest

from scripts.state_manager import LoopStateError, TerminalStateManager


class TestTerminalStateManager:
    """Test suite for TerminalStateManager class."""

    def test_init_with_terminal_id(self):
        """Test initialization with explicit terminal ID."""
        manager = TerminalStateManager(terminal_id="test_terminal")
        assert manager.terminal_id == "test_terminal"
        assert manager.state_dir.name == "test_terminal"

    def test_init_auto_detect_terminal_id(self):
        """Test initialization with auto-detected terminal ID."""
        manager = TerminalStateManager()
        assert manager.terminal_id is not None
        assert manager.state_dir.exists()

    @pytest.fixture
    def temp_state_dir(self, tmp_path):
        """Create temporary state directory for testing."""
        state_dir = tmp_path / "terminals" / "test_terminal"
        state_dir.mkdir(parents=True)
        yield state_dir

    @pytest.fixture
    def manager(self, temp_state_dir):
        """Create TerminalStateManager with temporary state directory."""
        with patch("core.state_manager.get_terminal_state_dir", return_value=temp_state_dir):
            return TerminalStateManager(terminal_id="test_terminal")

    def test_read_state_existing_file(self, manager):
        """Test reading existing state file."""
        state_file = manager.state_dir / "test.json"
        state_file.write_text(json.dumps({"key": "value"}))

        result = manager.read_state("test")
        assert result == {"key": "value"}

    def test_read_state_missing_file(self, manager):
        """Test reading missing state file returns None."""
        result = manager.read_state("nonexistent")
        assert result is None

    def test_read_state_corrupted_file(self, manager):
        """Test reading corrupted state file raises LoopStateError."""
        state_file = manager.state_dir / "corrupt.json"
        state_file.write_text("{invalid json}")

        with pytest.raises(LoopStateError, match="Corrupted state file"):
            manager.read_state("corrupt")

    def test_write_state_creates_file(self, manager):
        """Test writing state creates file with correct content."""
        manager.write_state("test", {"key": "value"})

        state_file = manager.state_dir / "test.json"
        assert state_file.exists()
        content = json.loads(state_file.read_text())
        assert content == {"key": "value"}

    def test_write_state_atomic_operation(self, manager):
        """Test write operation is atomic (temp file + rename)."""
        manager.write_state("atomic", {"data": "test"})

        state_file = manager.state_dir / "atomic.json"
        assert state_file.exists()

        # No temp files left behind
        temp_files = list(manager.state_dir.glob("*.tmp"))
        assert len(temp_files) == 0

    def test_write_state_overwrites_existing(self, manager):
        """Test writing state overwrites existing file."""
        manager.write_state("overwrite", {"version": 1})
        manager.write_state("overwrite", {"version": 2})

        state_file = manager.state_dir / "overwrite.json"
        content = json.loads(state_file.read_text())
        assert content == {"version": 2}

    def test_acquire_lock_success(self, manager):
        """Test successful lock acquisition."""
        result = manager.acquire_lock("test_lock")
        assert result is True

        lock_file = manager.state_dir / "test_lock.lock"
        assert lock_file.exists()
        assert lock_file.read_text().strip() == str(os.getpid())

    def test_acquire_lock_already_held(self, manager):
        """Test acquiring lock already held returns False."""
        # Create lock file manually with current process PID
        lock_file = manager.state_dir / "held.lock"
        lock_file.write_text(str(os.getpid()))  # Current process PID

        result = manager.acquire_lock("held")
        assert result is False

    def test_acquire_lock_stale_cleanup(self, manager):
        """Test stale lock (nonexistent PID) is cleaned up."""
        # Create lock file with nonexistent PID
        lock_file = manager.state_dir / "stale.lock"
        lock_file.write_text("1")  # PID 1 unlikely to be ours

        result = manager.acquire_lock("stale")
        assert result is True

        # Lock should now have our PID
        assert lock_file.read_text().strip() == str(os.getpid())

    def test_release_lock_success(self, manager):
        """Test successful lock release."""
        manager.acquire_lock("release_test")
        manager.release_lock("release_test")

        lock_file = manager.state_dir / "release_test.lock"
        assert not lock_file.exists()

    def test_release_lock_missing_file(self, manager):
        """Test releasing missing lock doesn't raise error."""
        # Should not raise exception
        manager.release_lock("nonexistent")

    def test_is_pid_running_current_process(self, manager):
        """Test _is_pid_running returns True for current process."""
        assert manager._is_pid_running(os.getpid()) is True

    def test_is_pid_running_nonexistent_process(self, manager):
        """Test _is_pid_running returns False for nonexistent process."""
        # Use PID 1 (unlikely to exist or be accessible)
        assert manager._is_pid_running(999999) is False

    def test_multi_terminal_isolation(self, tmp_path):
        """Test different terminals have separate state directories."""
        terminal_a_dir = tmp_path / "terminals" / "terminal_a"
        terminal_b_dir = tmp_path / "terminals" / "terminal_b"
        terminal_a_dir.mkdir(parents=True)
        terminal_b_dir.mkdir(parents=True)

        with patch("core.state_manager.get_terminal_state_dir") as mock_dir:
            mock_dir.side_effect = lambda tid: (
                terminal_a_dir if tid == "terminal_a" else terminal_b_dir
            )

            manager_a = TerminalStateManager(terminal_id="terminal_a")
            manager_b = TerminalStateManager(terminal_id="terminal_b")

            manager_a.write_state("test", {"terminal": "A"})
            manager_b.write_state("test", {"terminal": "B"})

            # Each terminal should have its own state
            assert (terminal_a_dir / "test.json").exists()
            assert (terminal_b_dir / "test.json").exists()

            content_a = json.loads((terminal_a_dir / "test.json").read_text())
            content_b = json.loads((terminal_b_dir / "test.json").read_text())

            assert content_a["terminal"] == "A"
            assert content_b["terminal"] == "B"
