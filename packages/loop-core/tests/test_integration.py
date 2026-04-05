"""Integration tests for loop-core package."""

from unittest.mock import patch

import pytest

from scripts.plan_parser import PlanParseError, detect_incomplete_tasks, parse_plan_tasks
from scripts.state_manager import LoopStateError, TerminalStateManager


class TestLoopLifecycle:
    """Integration tests for complete loop lifecycle."""

    @pytest.fixture
    def sample_plan(self, tmp_path):
        """Create sample plan file."""
        plan_file = tmp_path / "test_plan.md"
        plan_content = """
# Test Plan

- [ ] TASK-001 Initialize state
- [ ] TASK-002 Process data [tag:important]
- [ ] TASK-037 Save results after:TASK-002

- [x] TASK-004 Already done
"""
        plan_file.write_text(plan_content)
        return plan_file

    @pytest.fixture
    def temp_state_dir(self, tmp_path):
        """Create temporary state directory."""
        state_dir = tmp_path / "terminals" / "test_terminal"
        state_dir.mkdir(parents=True)
        return state_dir

    @pytest.fixture
    def state_manager(self, temp_state_dir):
        """Create TerminalStateManager with temporary directory."""
        with patch("core.state_manager.get_terminal_state_dir", return_value=temp_state_dir):
            return TerminalStateManager(terminal_id="test_terminal")

    def test_full_lifecycle_parse_and_persist(self, sample_plan, state_manager):
        """Test parsing plan and persisting state to file."""
        # Parse plan
        tasks = parse_plan_tasks(sample_plan)
        assert len(tasks) == 4

        # Get incomplete tasks
        incomplete = detect_incomplete_tasks(tasks)
        assert len(incomplete) == 3

        # Persist current task to state
        state_manager.write_state("loop_state", {
            "current_task_id": incomplete[0]["id"],
            "completed_tasks": ["TASK-004"],
            "failed_tasks": [],
        })

        # Verify state persistence
        loaded_state = state_manager.read_state("loop_state")
        assert loaded_state["current_task_id"] == "TASK-001"
        assert loaded_state["completed_tasks"] == ["TASK-004"]

    def test_state_persistence_across_sessions(self, sample_plan, temp_state_dir):
        """Test state persists across multiple manager instances."""
        # Session 1: Write state
        with patch("core.state_manager.get_terminal_state_dir", return_value=temp_state_dir):
            manager1 = TerminalStateManager(terminal_id="test_terminal")
            manager1.write_state("session_test", {"value": "from_session_1"})

        # Session 2: Read state
        with patch("core.state_manager.get_terminal_state_dir", return_value=temp_state_dir):
            manager2 = TerminalStateManager(terminal_id="test_terminal")
            loaded = manager2.read_state("session_test")
            assert loaded["value"] == "from_session_1"

    def test_plan_update_handling(self, tmp_path, temp_state_dir):
        """Test handling plan file updates during loop execution."""
        plan_file = tmp_path / "dynamic_plan.md"
        plan_file.write_text("- [ ] TASK-001 Original task\n")

        with patch("core.state_manager.get_terminal_state_dir", return_value=temp_state_dir):
            TerminalStateManager(terminal_id="test_terminal")

            # Parse original plan
            tasks1 = parse_plan_tasks(plan_file)
            assert len(tasks1) == 1

            # Update plan file
            plan_file.write_text("- [ ] TASK-001 Original task\n- [ ] TASK-002 New task\n")

            # Parse updated plan
            tasks2 = parse_plan_tasks(plan_file)
            assert len(tasks2) == 2

    def test_error_recovery_corrupted_state(self, temp_state_dir):
        """Test recovery from corrupted state file."""
        with patch("core.state_manager.get_terminal_state_dir", return_value=temp_state_dir):
            manager = TerminalStateManager(terminal_id="test_terminal")

            # Create corrupted state file
            state_file = temp_state_dir / "corrupt.json"
            state_file.write_text("{invalid json}")

            # Should raise LoopStateError
            with pytest.raises(LoopStateError, match="Corrupted state file"):
                manager.read_state("corrupt")

    def test_lock_prevents_concurrent_writes(self, temp_state_dir):
        """Test lock mechanism prevents concurrent writes."""
        with patch("core.state_manager.get_terminal_state_dir", return_value=temp_state_dir):
            manager1 = TerminalStateManager(terminal_id="test_terminal")
            manager2 = TerminalStateManager(terminal_id="test_terminal")

            # Manager 1 acquires lock
            assert manager1.acquire_lock("write_lock") is True

            # Manager 2 should fail to acquire same lock
            assert manager2.acquire_lock("write_lock") is False

            # Manager 1 releases lock
            manager1.release_lock("write_lock")

            # Manager 2 should now succeed
            assert manager2.acquire_lock("write_lock") is True

            # Cleanup
            manager2.release_lock("write_lock")

    def test_multi_terminal_isolation(self, tmp_path):
        """Test that different terminals have isolated state."""
        terminal_a_dir = tmp_path / "terminals" / "terminal_a"
        terminal_b_dir = tmp_path / "terminals" / "terminal_b"
        terminal_a_dir.mkdir(parents=True)
        terminal_b_dir.mkdir(parents=True)

        # Terminal A writes state
        with patch("core.state_manager.get_terminal_state_dir") as mock_dir:
            mock_dir.side_effect = lambda tid: (
                terminal_a_dir if tid == "terminal_a" else terminal_b_dir
            )

            manager_a = TerminalStateManager(terminal_id="terminal_a")
            manager_b = TerminalStateManager(terminal_id="terminal_b")

            manager_a.write_state("test", {"terminal": "A"})
            manager_b.write_state("test", {"terminal": "B"})

            # Each terminal should have independent state
            state_a = manager_a.read_state("test")
            state_b = manager_b.read_state("test")

            assert state_a["terminal"] == "A"
            assert state_b["terminal"] == "B"

    def test_error_recovery_plan_not_found(self, tmp_path):
        """Test PlanParseError raised for missing plan file."""
        with pytest.raises(PlanParseError, match="Plan file not found"):
            parse_plan_tasks(tmp_path / "nonexistent.md")

    def test_state_metadata_tracking(self, sample_plan, state_manager):
        """Test tracking loop metadata in state."""
        tasks = parse_plan_tasks(sample_plan)
        incomplete = detect_incomplete_tasks(tasks)

        # Write state with metadata
        state_manager.write_state("loop_state", {
            "current_task_id": incomplete[0]["id"],
            "completed_tasks": [],
            "failed_tasks": [],
            "loop_metadata": {
                "plan_path": str(sample_plan),
                "started_at": "2026-03-14T10:00:00",
                "last_update": "2026-03-14T10:15:00",
            },
        })

        # Verify metadata persists
        state = state_manager.read_state("loop_state")
        assert "loop_metadata" in state
        assert state["loop_metadata"]["plan_path"] == str(sample_plan)
        assert state["loop_metadata"]["started_at"] == "2026-03-14T10:00:00"

    def test_progress_tracking_across_tasks(self, sample_plan, state_manager):
        """Test tracking progress as tasks complete."""
        tasks = parse_plan_tasks(sample_plan)
        incomplete = detect_incomplete_tasks(tasks)

        # Start with first task
        state = {
            "current_task_id": incomplete[0]["id"],
            "completed_tasks": [],
            "failed_tasks": [],
        }
        state_manager.write_state("loop_state", state)

        # Simulate completing first task
        state["current_task_id"] = incomplete[1]["id"]
        state["completed_tasks"].append(incomplete[0]["id"])
        state_manager.write_state("loop_state", state)

        # Verify progress persisted
        loaded = state_manager.read_state("loop_state")
        assert loaded["current_task_id"] == "TASK-002"
        assert "TASK-001" in loaded["completed_tasks"]
