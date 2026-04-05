"""Integration tests for loop_policy and loop_observability modules.

These tests verify the complete loop lifecycle using policy-based exit decisions
and observability logging. Tests follow the TDD workflow: RED → GREEN → REFACTOR.
"""

from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from scripts.loop_observability import log_decision, update_metrics
from scripts.loop_policy import (
    ConfigIntegrityError,
    ConfigLoadError,
    clear_plan_cache,
    load_config,
    parse_plan_with_cache,
    should_exit,
    should_run_verifier,
)
from scripts.state_manager import TerminalStateManager


class TestConfigLoading:
    """Test configuration loading and validation."""

    def test_load_valid_config(self, tmp_path):
        """Test loading a valid config file."""
        config_file = tmp_path / ".claude" / "loop" / "config.yaml"
        config_file.parent.mkdir(parents=True)

        config_content = {
            "version": 1,
            "exit_policy": {
                "min_completion_indicators": 2,
                "require_exit_signal": True,
                "require_all_tasks_complete": True,
                "require_verification_pass": False,
            },
            "verification": {
                "enabled": True,
                "skill": "verify",
                "write_report": ".claude/loop/verification_report.md",
            },
            "plans": {
                "default_plan": "plan.md",
                "allow_per_terminal_plan": False,
            },
            "logging": {
                "decision_log": ".claude/loop/logs/decision.log",
                "verifier_log": ".claude/loop/logs/verifier.log",
            },
        }

        with open(config_file, "w") as f:
            yaml.dump(config_content, f)

        config = load_config(str(config_file))
        assert config["version"] == 1
        assert config["exit_policy"]["min_completion_indicators"] == 2
        assert config["verification"]["enabled"] is True

    def test_load_config_missing_file(self, tmp_path):
        """Test ConfigLoadError raised when config file missing."""
        with pytest.raises(ConfigLoadError, match="Config file not found"):
            load_config(str(tmp_path / "nonexistent.yaml"))

    def test_load_config_invalid_yaml(self, tmp_path):
        """Test ConfigLoadError raised for invalid YAML."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("invalid: yaml: content: [")

        with pytest.raises(ConfigLoadError, match="Failed to parse config file"):
            load_config(str(config_file))

    def test_load_config_missing_version(self, tmp_path):
        """Test ConfigIntegrityError raised when version missing."""
        config_file = tmp_path / "config.yaml"
        config_content = {
            "exit_policy": {
                "min_completion_indicators": 2,
                "require_exit_signal": True,
                "require_all_tasks_complete": True,
                "require_verification_pass": False,
            },
            "verification": {"enabled": True},
            "plans": {"default_plan": "plan.md"},
            "logging": {},
        }
        with open(config_file, "w") as f:
            yaml.dump(config_content, f)

        with pytest.raises(ConfigIntegrityError, match="Missing required config section: version"):
            load_config(str(config_file))

    def test_load_config_unsupported_version(self, tmp_path):
        """Test ConfigIntegrityError raised for unsupported version."""
        config_file = tmp_path / "config.yaml"
        config_content = {
            "version": 99,
            "exit_policy": {
                "min_completion_indicators": 2,
                "require_exit_signal": True,
                "require_all_tasks_complete": True,
                "require_verification_pass": False,
            },
            "verification": {"enabled": True},
            "plans": {"default_plan": "plan.md"},
            "logging": {},
        }
        with open(config_file, "w") as f:
            yaml.dump(config_content, f)

        with pytest.raises(ConfigIntegrityError, match="Unsupported config version: 99"):
            load_config(str(config_file))

    def test_load_config_invalid_min_indicators(self, tmp_path):
        """Test ConfigIntegrityError raised for invalid min_completion_indicators."""
        config_file = tmp_path / "config.yaml"
        config_content = {
            "version": 1,
            "exit_policy": {
                "min_completion_indicators": 0,  # Must be >= 1
                "require_exit_signal": True,
                "require_all_tasks_complete": True,
                "require_verification_pass": False,
            },
            "verification": {"enabled": True},
            "plans": {"default_plan": "plan.md"},
            "logging": {},
        }
        with open(config_file, "w") as f:
            yaml.dump(config_content, f)

        with pytest.raises(ConfigIntegrityError, match="min_completion_indicators must be >= 1"):
            load_config(str(config_file))


class TestExitPolicy:
    """Test policy-based exit decision logic."""

    @pytest.fixture
    def valid_config(self):
        """Create valid config for testing."""
        return {
            "version": 1,
            "exit_policy": {
                "min_completion_indicators": 2,
                "require_exit_signal": True,
                "require_all_tasks_complete": True,
                "require_verification_pass": False,
            },
            "verification": {"enabled": True},
            "plans": {"default_plan": "plan.md"},
            "logging": {},
        }

    @pytest.fixture
    def sample_tasks(self):
        """Create sample task list."""
        return [
            {"id": "TASK-001", "text": "Task 1", "complete": True},
            {"id": "TASK-002", "text": "Task 2", "complete": True},
            {"id": "TASK-003", "text": "Task 3", "complete": False},
        ]

    def test_should_exit_all_conditions_met(self, valid_config):
        """Test exit when all conditions are satisfied."""
        # All tasks must be complete when require_all_tasks_complete is True
        all_complete_tasks = [
            {"id": "TASK-001", "text": "Task 1", "complete": True},
            {"id": "TASK-002", "text": "Task 2", "complete": True},
        ]

        loop_state = {
            "completion_indicators": 2,
            "ralph_status": {"EXIT_SIGNAL": True},
            "verification_status": {"passed": True},
        }

        result = should_exit(all_complete_tasks, loop_state, valid_config)
        assert result is True

    def test_should_exit_missing_min_indicators(self, valid_config, sample_tasks):
        """Test continue when completion indicators too low."""
        loop_state = {
            "completion_indicators": 1,  # Below min of 2
            "ralph_status": {"EXIT_SIGNAL": True},
        }

        result = should_exit(sample_tasks, loop_state, valid_config)
        assert result is False

    def test_should_exit_missing_exit_signal(self, valid_config, sample_tasks):
        """Test continue when EXIT_SIGNAL not set."""
        loop_state = {
            "completion_indicators": 2,
            "ralph_status": {"EXIT_SIGNAL": False},
        }

        result = should_exit(sample_tasks, loop_state, valid_config)
        assert result is False

    def test_should_exit_incomplete_tasks(self, valid_config, sample_tasks):
        """Test continue when tasks incomplete and require_all_tasks_complete is True."""
        loop_state = {
            "completion_indicators": 2,
            "ralph_status": {"EXIT_SIGNAL": True},
        }

        result = should_exit(sample_tasks, loop_state, valid_config)
        assert result is False  # TASK-003 is incomplete

    def test_should_exit_allows_incomplete_tasks(self, tmp_path):
        """Test exit when require_all_tasks_complete is False."""
        config = {
            "version": 1,
            "exit_policy": {
                "min_completion_indicators": 2,
                "require_exit_signal": True,
                "require_all_tasks_complete": False,  # Allow incomplete tasks
                "require_verification_pass": False,
            },
            "verification": {"enabled": True},
            "plans": {"default_plan": "plan.md"},
            "logging": {},
        }

        tasks = [
            {"id": "TASK-001", "text": "Task 1", "complete": True},
            {"id": "TASK-002", "text": "Task 2", "complete": False},  # Incomplete
        ]

        loop_state = {
            "completion_indicators": 2,
            "ralph_status": {"EXIT_SIGNAL": True},
        }

        result = should_exit(tasks, loop_state, config)
        assert result is True  # Exits despite incomplete task

    def test_should_exit_requires_verification(self, tmp_path):
        """Test exit requires verification pass when enabled."""
        config = {
            "version": 1,
            "exit_policy": {
                "min_completion_indicators": 2,
                "require_exit_signal": True,
                "require_all_tasks_complete": True,
                "require_verification_pass": True,  # Require verification
            },
            "verification": {"enabled": True},
            "plans": {"default_plan": "plan.md"},
            "logging": {},
        }

        tasks = [
            {"id": "TASK-001", "text": "Task 1", "complete": True},
            {"id": "TASK-002", "text": "Task 2", "complete": True},
        ]

        loop_state = {
            "completion_indicators": 2,
            "ralph_status": {"EXIT_SIGNAL": True},
            "verification_status": {"passed": False},  # Verification failed
        }

        result = should_exit(tasks, loop_state, config)
        assert result is False  # Continue due to failed verification


class TestVerificationTriggering:
    """Test verification triggering logic."""

    @pytest.fixture
    def verification_config(self):
        """Create config with verification enabled."""
        return {
            "version": 1,
            "exit_policy": {
                "min_completion_indicators": 2,
                "require_exit_signal": True,
                "require_all_tasks_complete": True,
                "require_verification_pass": True,
            },
            "verification": {"enabled": True},
            "plans": {"default_plan": "plan.md"},
            "logging": {},
        }

    def test_should_run_verifier_first_time(self, verification_config):
        """Test verification runs when no status exists."""
        loop_state = {}

        result = should_run_verifier(loop_state, verification_config)
        assert result is True

    def test_should_run_verifier_already_passed(self, verification_config):
        """Test verification doesn't re-run if already passed."""
        loop_state = {"verification_status": {"passed": True}}

        result = should_run_verifier(loop_state, verification_config)
        assert result is False

    def test_should_run_verifier_failed_retry(self, verification_config):
        """Test verification retries after failure."""
        loop_state = {"verification_status": {"passed": False}}

        result = should_run_verifier(loop_state, verification_config)
        assert result is True

    def test_should_run_verifier_disabled(self, verification_config):
        """Test verification doesn't run when disabled."""
        config = verification_config.copy()
        config["verification"]["enabled"] = False

        loop_state = {}

        result = should_run_verifier(loop_state, config)
        assert result is False

    def test_should_run_verifier_not_required(self, tmp_path):
        """Test verification doesn't run when not required by exit policy."""
        config = {
            "version": 1,
            "exit_policy": {
                "min_completion_indicators": 2,
                "require_exit_signal": True,
                "require_all_tasks_complete": True,
                "require_verification_pass": False,  # Not required
            },
            "verification": {"enabled": True},
            "plans": {"default_plan": "plan.md"},
            "logging": {},
        }

        loop_state = {}

        result = should_run_verifier(loop_state, config)
        assert result is False


class TestPlanCaching:
    """Test plan parsing with caching."""

    def test_parse_plan_with_cache_first_call(self, tmp_path):
        """Test first call parses plan and caches result."""
        plan_file = tmp_path / "plan.md"
        plan_content = """
# Test Plan

- [ ] TASK-001 First task
- [ ] TASK-002 Second task
"""
        plan_file.write_text(plan_content)

        # Clear cache to ensure clean state
        clear_plan_cache()

        tasks = parse_plan_with_cache(plan_file)
        assert len(tasks) == 2
        assert tasks[0]["id"] == "TASK-001"
        assert tasks[1]["id"] == "TASK-002"

    def test_parse_plan_with_cache_second_call(self, tmp_path):
        """Test second call uses cache."""
        plan_file = tmp_path / "plan.md"
        plan_content = """
- [ ] TASK-001 First task
"""
        plan_file.write_text(plan_content)

        clear_plan_cache()

        # First call - parses and caches
        tasks1 = parse_plan_with_cache(plan_file)

        # Second call - should use cache
        tasks2 = parse_plan_with_cache(plan_file)

        assert tasks1 == tasks2

    def test_parse_plan_with_cache_invalidation(self, tmp_path):
        """Test cache invalidates when file changes."""
        plan_file = tmp_path / "plan.md"
        plan_file.write_text("- [ ] TASK-001 Original task\n")

        clear_plan_cache()

        # First parse
        tasks1 = parse_plan_with_cache(plan_file)
        assert len(tasks1) == 1
        assert tasks1[0]["text"] == "Original task"

        # Modify file
        import time
        time.sleep(0.01)  # Ensure different mtime
        plan_file.write_text("- [ ] TASK-001 Modified task\n")

        # Second parse should get modified content
        tasks2 = parse_plan_with_cache(plan_file)
        assert len(tasks2) == 1
        assert tasks2[0]["text"] == "Modified task"


class TestObservability:
    """Test observability logging and metrics."""

    def test_log_decision_creates_log_entry(self, tmp_path):
        """Test log_decision creates JSON line entry."""
        with patch("scripts.loop_observability.get_terminal_log_dir") as mock_dir:
            log_dir = tmp_path / "logs"
            log_dir.mkdir(parents=True)
            mock_dir.return_value = log_dir

            log_decision("test_terminal", "task_started", {"task_id": "TASK-001"})

            log_file = log_dir / "decision.log"
            assert log_file.exists()

            content = log_file.read_text()
            assert "task_started" in content
            assert "TASK-001" in content
            assert "test_terminal" in content

    def test_log_decision_append_multiple_entries(self, tmp_path):
        """Test log_decision appends multiple entries."""
        with patch("scripts.loop_observability.get_terminal_log_dir") as mock_dir:
            log_dir = tmp_path / "logs"
            log_dir.mkdir(parents=True)
            mock_dir.return_value = log_dir

            log_decision("test_terminal", "iteration_start", {"iteration": 1})
            log_decision("test_terminal", "task_complete", {"task_id": "TASK-001"})
            log_decision("test_terminal", "iteration_end", {"iteration": 1})

            log_file = log_dir / "decision.log"
            lines = log_file.read_text().strip().split("\n")
            assert len(lines) == 3

    def test_log_decision_best_effort(self, tmp_path):
        """Test log_decision fails gracefully on I/O errors."""
        # Simulate permission error by using a directory as file path
        with patch("scripts.loop_observability.get_terminal_log_dir") as mock_dir:
            mock_dir.return_value = tmp_path  # Directory instead of log dir

            # Should not raise exception
            log_decision("test_terminal", "test_event", {})

            # No error logged, function returns gracefully
            assert True

    def test_update_metrics_creates_metrics_file(self, tmp_path):
        """Test update_metrics creates loop_metrics.json."""
        with patch("scripts.loop_observability.get_terminal_state_dir") as mock_dir:
            state_dir = tmp_path / "state"
            state_dir.mkdir(parents=True)
            mock_dir.return_value = state_dir

            update_metrics("test_terminal", {"tasks_completed": 1, "iterations": 1})

            metrics_file = state_dir / "loop_metrics.json"
            assert metrics_file.exists()

            import json
            with open(metrics_file) as f:
                metrics = json.load(f)

            assert metrics["tasks_completed"] == 1
            assert metrics["iterations"] == 1
            assert "last_update" in metrics

    def test_update_metrics_merges_with_existing(self, tmp_path):
        """Test update_metrics merges with existing metrics."""
        with patch("scripts.loop_observability.get_terminal_state_dir") as mock_dir:
            state_dir = tmp_path / "state"
            state_dir.mkdir(parents=True)
            mock_dir.return_value = state_dir

            # Initial metrics
            update_metrics("test_terminal", {"tasks_completed": 1})

            # Update with more metrics
            update_metrics("test_terminal", {"tasks_completed": 1, "iterations": 1})

            metrics_file = state_dir / "loop_metrics.json"
            import json
            with open(metrics_file) as f:
                metrics = json.load(f)

            assert metrics["tasks_completed"] == 2  # Summed
            assert metrics["iterations"] == 1

    def test_update_metrics_best_effort(self, tmp_path):
        """Test update_metrics fails gracefully on I/O errors."""
        with patch("scripts.loop_observability.get_terminal_state_dir") as mock_dir:
            # Simulate error by returning a file path instead of directory
            mock_dir.return_value = tmp_path / "file.txt"

            # Should not raise exception
            update_metrics("test_terminal", {"test": 1})

            assert True


class TestFullLoopLifecycle:
    """Integration tests for complete loop lifecycle with policy and observability."""

    @pytest.fixture
    def loop_environment(self, tmp_path):
        """Set up complete loop environment with config, plan, and state."""
        # Create config
        config_dir = tmp_path / ".claude" / "loop"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "config.yaml"

        config_content = {
            "version": 1,
            "exit_policy": {
                "min_completion_indicators": 2,
                "require_exit_signal": True,
                "require_all_tasks_complete": True,
                "require_verification_pass": False,
            },
            "verification": {"enabled": False},
            "plans": {"default_plan": "plan.md", "allow_per_terminal_plan": False},
            "logging": {
                "decision_log": ".claude/loop/logs/decision.log",
                "verifier_log": ".claude/loop/logs/verifier.log",
            },
        }
        with open(config_file, "w") as f:
            yaml.dump(config_content, f)

        # Create plan
        plan_file = tmp_path / "plan.md"
        plan_content = """
# Test Plan

- [ ] TASK-001 First task
- [ ] TASK-002 Second task
- [ ] TASK-003 Third task
"""
        plan_file.write_text(plan_content)

        # Create state and log directories
        state_dir = tmp_path / "terminals" / "test_terminal"
        log_dir = state_dir / "logs"
        state_dir.mkdir(parents=True)
        log_dir.mkdir(parents=True)

        return {
            "config_path": str(config_file),
            "plan_path": str(plan_file),
            "state_dir": state_dir,
            "log_dir": log_dir,
            "terminal_id": "test_terminal",
        }

    def test_full_iteration_workflow(self, loop_environment):
        """Test complete iteration: detect terminal → read state → load config → parse plan → execute → update → log → check exit."""

        # Mock terminal detection
        with patch("scripts.state_manager.get_terminal_id", return_value="test_terminal"):
            with patch("scripts.state_paths.get_terminal_state_dir", return_value=loop_environment["state_dir"]):
                with patch("scripts.loop_observability.get_terminal_log_dir", return_value=loop_environment["log_dir"]):
                    # Step 1: Detect terminal_id (already done via patch)
                    terminal_id = "test_terminal"

                    # Step 2: Read loop_state
                    state_mgr = TerminalStateManager(terminal_id=terminal_id)
                    loop_state = state_mgr.read_state("loop_state")

                    # Initialize state if None
                    if loop_state is None:
                        loop_state = {
                            "current_task_id": None,
                            "completed_tasks": [],
                            "failed_tasks": [],
                            "completion_indicators": 0,
                        }
                    else:
                        # Reset completion_indicators for this test
                        loop_state["completion_indicators"] = 0

                    # Step 3: Load config (fresh each iteration)
                    config = load_config(loop_environment["config_path"])

                    # Step 4: Parse plan
                    clear_plan_cache()  # Ensure fresh parse
                    tasks = parse_plan_with_cache(loop_environment["plan_path"])

                    # Step 5: Execute /code for task (simulated)
                    current_task = tasks[0]
                    loop_state["current_task_id"] = current_task["id"]
                    loop_state["completed_tasks"].append(current_task["id"])
                    loop_state["completion_indicators"] += 1

                    # Step 6: Update loop_state
                    state_mgr.write_state("loop_state", loop_state)

                    # Step 7: Log decision
                    log_decision(
                        terminal_id,
                        "iteration_complete",
                        {
                            "task_id": current_task["id"],
                            "completion_indicators": loop_state["completion_indicators"],
                        }
                    )

                    # Step 8: Check should_exit
                    should_exit_now = should_exit(tasks, loop_state, config)

                    # Verify iteration completed
                    assert loop_state["current_task_id"] == "TASK-001"
                    assert "TASK-001" in loop_state["completed_tasks"]
                    assert loop_state["completion_indicators"] == 1

                    # Verify exit decision (should continue - not enough indicators)
                    assert should_exit_now is False

                    # Verify log entry created
                    log_file = loop_environment["log_dir"] / "decision.log"
                    assert log_file.exists()
                    log_content = log_file.read_text()
                    assert "iteration_complete" in log_content

    def test_config_changes_mid_run(self, loop_environment):
        """Test that config changes are detected each iteration."""
        import time

        config_file = Path(loop_environment["config_path"])

        # Load initial config
        config1 = load_config(str(config_file))
        assert config1["exit_policy"]["min_completion_indicators"] == 2

        # Modify config
        time.sleep(0.01)  # Ensure different mtime
        with open(config_file, "r") as f:
            config_content = yaml.safe_load(f)
        config_content["exit_policy"]["min_completion_indicators"] = 5

        with open(config_file, "w") as f:
            yaml.dump(config_content, f)

        # Load updated config
        config2 = load_config(str(config_file))
        assert config2["exit_policy"]["min_completion_indicators"] == 5

    def test_observability_decision_log_entries(self, loop_environment):
        """Test that decision log captures all iteration events."""
        with patch("scripts.loop_observability.get_terminal_log_dir", return_value=loop_environment["log_dir"]):
            terminal_id = loop_environment["terminal_id"]

            # Log iteration events
            log_decision(terminal_id, "iteration_start", {"iteration": 1})
            log_decision(terminal_id, "task_started", {"task_id": "TASK-001"})
            log_decision(terminal_id, "task_complete", {"task_id": "TASK-001"})
            log_decision(terminal_id, "iteration_end", {"iteration": 1})

            # Verify log entries
            log_file = loop_environment["log_dir"] / "decision.log"
            log_content = log_file.read_text()
            lines = log_content.strip().split("\n")

            assert len(lines) == 4

            import json
            for line in lines:
                entry = json.loads(line)
                assert "timestamp" in entry
                assert "terminal_id" in entry
                assert entry["terminal_id"] == terminal_id
