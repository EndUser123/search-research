"""Tests for loop_policy.py module.

Tests all 16 combinations of exit policy flags:
- min_completion_indicators (requires signal)
- require_exit_signal (true/false)
- require_all_tasks_complete (true/false)
- require_verification_pass (true/false)

Also tests config integrity validation and plan caching.
"""

from pathlib import Path

import pytest
import yaml

from scripts.loop_policy import (
    ConfigIntegrityError,
    ConfigLoadError,
    load_config,
    should_exit,
    should_run_verifier,
)


class TestLoadConfig:
    """Test suite for load_config() function."""

    def test_load_valid_config(self, tmp_path: Path):
        """Test loading a valid config file."""
        config_data = {
            "version": 1,
            "exit_policy": {
                "min_completion_indicators": 2,
                "require_exit_signal": True,
                "require_all_tasks_complete": True,
                "require_verification_pass": True,
            },
            "verification": {
                "enabled": True,
                "skill": "prd-verifier",
                "write_report": ".claude/loop/verification-report.md",
            },
            "plans": {
                "default_plan": "plan.md",
                "allow_per_terminal_plan": True,
            },
            "logging": {
                "decision_log": "decision.log",
                "verifier_log": "verifier.log",
            },
        }

        config_file = tmp_path / ".claude" / "loop" / "config.yaml"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.write_text(yaml.dump(config_data))

        config = load_config(str(config_file))

        assert config["version"] == 1
        assert config["exit_policy"]["min_completion_indicators"] == 2
        assert config["exit_policy"]["require_exit_signal"] is True
        assert config["verification"]["enabled"] is True

    def test_load_config_with_default_path(self, tmp_path: Path):
        """Test loading config from default .claude/loop/config.yaml path."""
        config_data = {
            "version": 1,
            "exit_policy": {
                "min_completion_indicators": 2,
                "require_exit_signal": True,
                "require_all_tasks_complete": True,
                "require_verification_pass": True,
            },
            "verification": {"enabled": True, "skill": "prd-verifier", "write_report": ".claude/loop/verification-report.md"},
            "plans": {"default_plan": "plan.md", "allow_per_terminal_plan": True},
            "logging": {"decision_log": "decision.log", "verifier_log": "verifier.log"},
        }

        # Create config at default path
        config_file = tmp_path / ".claude" / "loop" / "config.yaml"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.write_text(yaml.dump(config_data))

        # Change to tmp_path directory
        original_cwd = Path.cwd()
        try:
            import os

            os.chdir(tmp_path)
            config = load_config()  # Should use default path
            assert config["version"] == 1
        finally:
            os.chdir(original_cwd)

    def test_load_config_missing_file(self, tmp_path: Path):
        """Test loading a missing config file raises ConfigLoadError."""
        missing_path = tmp_path / "nonexistent.yaml"

        with pytest.raises(ConfigLoadError, match="Config file not found"):
            load_config(str(missing_path))

    def test_load_config_invalid_yaml(self, tmp_path: Path):
        """Test loading invalid YAML raises ConfigLoadError."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("invalid: yaml: content: [unclosed")

        with pytest.raises(ConfigLoadError, match="Failed to parse config file"):
            load_config(str(config_file))

    def test_load_config_missing_version(self, tmp_path: Path):
        """Test loading config without version raises ConfigIntegrityError."""
        config_data = {
            "exit_policy": {
                "min_completion_indicators": 2,
                "require_exit_signal": True,
                "require_all_tasks_complete": True,
                "require_verification_pass": True,
            },
        }

        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump(config_data))

        with pytest.raises(ConfigIntegrityError, match="Missing required config section: version"):
            load_config(str(config_file))

    def test_load_config_missing_exit_policy(self, tmp_path: Path):
        """Test loading config without exit_policy raises ConfigIntegrityError."""
        config_data = {
            "version": 1,
            "verification": {"enabled": True, "skill": "prd-verifier", "write_report": ".claude/loop/verification-report.md"},
        }

        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump(config_data))

        with pytest.raises(ConfigIntegrityError, match="Missing required config section: exit_policy"):
            load_config(str(config_file))

    def test_load_config_missing_verification(self, tmp_path: Path):
        """Test loading config without verification raises ConfigIntegrityError."""
        config_data = {
            "version": 1,
            "exit_policy": {
                "min_completion_indicators": 2,
                "require_exit_signal": True,
                "require_all_tasks_complete": True,
                "require_verification_pass": True,
            },
        }

        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump(config_data))

        with pytest.raises(ConfigIntegrityError, match="Missing required config section: verification"):
            load_config(str(config_file))

    def test_load_config_invalid_min_completion_indicators(self, tmp_path: Path):
        """Test loading config with invalid min_completion_indicators raises ConfigIntegrityError."""
        config_data = {
            "version": 1,
            "exit_policy": {
                "min_completion_indicators": 0,  # Invalid: must be >= 1
                "require_exit_signal": True,
                "require_all_tasks_complete": True,
                "require_verification_pass": True,
            },
            "verification": {"enabled": True, "skill": "prd-verifier", "write_report": ".claude/loop/verification-report.md"},
            "plans": {"default_plan": "plan.md", "allow_per_terminal_plan": True},
            "logging": {"decision_log": "decision.log", "verifier_log": "verifier.log"},
        }

        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump(config_data))

        with pytest.raises(ConfigIntegrityError, match="min_completion_indicators must be >= 1"):
            load_config(str(config_file))


class TestShouldExit:
    """Test suite for should_exit() function with all 16 policy flag combinations."""

    @pytest.fixture
    def sample_tasks(self):
        """Create sample tasks list."""
        return [
            {"id": "TASK-001", "text": "Task 1", "complete": True},
            {"id": "TASK-002", "text": "Task 2", "complete": True},
            {"id": "TASK-003", "text": "Task 3", "complete": False},
        ]

    @pytest.fixture
    def sample_loop_state(self):
        """Create sample loop state."""
        return {
            "current_task_id": "TASK-003",
            "completed_tasks": ["TASK-001", "TASK-002"],
            "failed_tasks": [],
            "completion_indicators": 2,
            "loop_metadata": {
                "plan_path": "/path/to/plan.md",
                "started_at": "2026-03-14T10:00:00",
                "last_update": "2026-03-14T10:15:00",
                "iterations": 3,
            },
        }

    @pytest.fixture
    def sample_config(self):
        """Create sample config with all flags enabled."""
        return {
            "version": 1,
            "exit_policy": {
                "min_completion_indicators": 2,
                "require_exit_signal": True,
                "require_all_tasks_complete": True,
                "require_verification_pass": True,
            },
            "verification": {"enabled": True, "skill": "prd-verifier"},
        }

    # Test all 16 combinations of exit policy flags
    # Format: test_exit_{signal}_{all_complete}_{verification}_{min_indicators}

    def test_exit_true_true_true_2_with_signal_pass(self, sample_tasks, sample_loop_state, sample_config):
        """Test exit with all flags true, 2 indicators, signal present, verification pass."""
        # All conditions met
        loop_state = sample_loop_state.copy()
        loop_state["completion_indicators"] = 2
        loop_state["ralph_status"] = {"EXIT_SIGNAL": True}
        loop_state["verification_status"] = {"passed": True}

        # Mark all tasks complete
        tasks = [task.copy() for task in sample_tasks]
        tasks[2]["complete"] = True

        result = should_exit(tasks, loop_state, sample_config)
        assert result is True

    def test_exit_true_true_true_2_with_signal_fail(self, sample_tasks, sample_loop_state, sample_config):
        """Test exit with all flags true, 2 indicators, signal present, verification fail."""
        loop_state = sample_loop_state.copy()
        loop_state["completion_indicators"] = 2
        loop_state["ralph_status"] = {"EXIT_SIGNAL": True}
        loop_state["verification_status"] = {"passed": False}

        tasks = [task.copy() for task in sample_tasks]
        tasks[2]["complete"] = True

        result = should_exit(tasks, loop_state, sample_config)
        assert result is False  # Verification failed

    def test_exit_true_true_true_2_no_signal(self, sample_tasks, sample_loop_state, sample_config):
        """Test exit with all flags true, 2 indicators, no signal."""
        loop_state = sample_loop_state.copy()
        loop_state["completion_indicators"] = 2
        # No EXIT_SIGNAL

        tasks = [task.copy() for task in sample_tasks]
        tasks[2]["complete"] = True
        loop_state["verification_status"] = {"passed": True}

        result = should_exit(tasks, loop_state, sample_config)
        assert result is False  # No EXIT_SIGNAL

    def test_exit_true_true_true_1_indicator(self, sample_tasks, sample_loop_state, sample_config):
        """Test exit with all flags true, 1 indicator (below min)."""
        loop_state = sample_loop_state.copy()
        loop_state["completion_indicators"] = 1
        loop_state["ralph_status"] = {"EXIT_SIGNAL": True}
        loop_state["verification_status"] = {"passed": True}

        tasks = [task.copy() for task in sample_tasks]
        tasks[2]["complete"] = True

        result = should_exit(tasks, loop_state, sample_config)
        assert result is False  # Insufficient indicators

    def test_exit_true_false_true_2_incomplete_task(self, sample_tasks, sample_loop_state, sample_config):
        """Test exit with require_all_tasks_complete=false, incomplete task allowed."""
        config = sample_config.copy()
        config["exit_policy"]["require_all_tasks_complete"] = False

        loop_state = sample_loop_state.copy()
        loop_state["completion_indicators"] = 2
        loop_state["ralph_status"] = {"EXIT_SIGNAL": True}
        loop_state["verification_status"] = {"passed": True}

        # One task incomplete
        tasks = [task.copy() for task in sample_tasks]

        result = should_exit(tasks, loop_state, config)
        assert result is True  # Incomplete tasks allowed

    def test_exit_false_true_true_2_no_signal_required(self, sample_tasks, sample_loop_state, sample_config):
        """Test exit with require_exit_signal=false, no signal needed."""
        config = sample_config.copy()
        config["exit_policy"]["require_exit_signal"] = False

        loop_state = sample_loop_state.copy()
        loop_state["completion_indicators"] = 2
        # No EXIT_SIGNAL needed
        loop_state["verification_status"] = {"passed": True}

        tasks = [task.copy() for task in sample_tasks]
        tasks[2]["complete"] = True

        result = should_exit(tasks, loop_state, config)
        assert result is True  # Signal not required

    def test_exit_true_true_false_2_no_verification(self, sample_tasks, sample_loop_state, sample_config):
        """Test exit with require_verification_pass=false, no verification needed."""
        config = sample_config.copy()
        config["exit_policy"]["require_verification_pass"] = False

        loop_state = sample_loop_state.copy()
        loop_state["completion_indicators"] = 2
        loop_state["ralph_status"] = {"EXIT_SIGNAL": True}
        # No verification needed

        tasks = [task.copy() for task in sample_tasks]
        tasks[2]["complete"] = True

        result = should_exit(tasks, loop_state, config)
        assert result is True  # Verification not required

    def test_exit_false_false_false_1_minimal(self, sample_tasks, sample_loop_state):
        """Test exit with all flags false, minimal conditions."""
        config = {
            "version": 1,
            "exit_policy": {
                "min_completion_indicators": 1,
                "require_exit_signal": False,
                "require_all_tasks_complete": False,
                "require_verification_pass": False,
            },
            "verification": {"enabled": False},
        }

        loop_state = sample_loop_state.copy()
        loop_state["completion_indicators"] = 1
        # No signal, no verification needed

        # Tasks not complete
        tasks = [task.copy() for task in sample_tasks]

        result = should_exit(tasks, loop_state, config)
        assert result is True  # Minimal requirements met

    def test_exit_all_flags_false_0_indicators(self, sample_tasks, sample_loop_state):
        """Test exit with all flags false, 0 indicators fails."""
        config = {
            "version": 1,
            "exit_policy": {
                "min_completion_indicators": 1,
                "require_exit_signal": False,
                "require_all_tasks_complete": False,
                "require_verification_pass": False,
            },
            "verification": {"enabled": False},
        }

        loop_state = sample_loop_state.copy()
        loop_state["completion_indicators"] = 0  # Below minimum

        tasks = [task.copy() for task in sample_tasks]

        result = should_exit(tasks, loop_state, config)
        assert result is False  # Insufficient indicators

    def test_exit_combination_matrix(self, sample_tasks, sample_loop_state):
        """Test matrix of all 16 combinations of boolean flags."""
        tasks_all_complete = [task.copy() for task in sample_tasks]
        tasks_all_complete[2]["complete"] = True

        tasks_incomplete = [task.copy() for task in sample_tasks]

        # Test all 16 combinations
        combinations = [
            # (signal, all_complete, verification, expected, tasks, loop_state_override)
            (True, True, True, True, tasks_all_complete, {"EXIT_SIGNAL": True, "passed": True}),
            (True, True, True, False, tasks_all_complete, {"EXIT_SIGNAL": True, "passed": False}),
            (True, True, False, True, tasks_all_complete, {"EXIT_SIGNAL": True}),
            (True, False, True, True, tasks_incomplete, {"EXIT_SIGNAL": True, "passed": True}),
            (True, False, False, True, tasks_incomplete, {"EXIT_SIGNAL": True}),
            (False, True, True, True, tasks_all_complete, {"EXIT_SIGNAL": False, "passed": True}),  # Signal not required
            (False, True, False, True, tasks_all_complete, {"EXIT_SIGNAL": False}),  # Signal not required
            (False, False, True, True, tasks_incomplete, {"EXIT_SIGNAL": False, "passed": True}),  # Incomplete allowed
            (False, False, False, True, tasks_incomplete, {"EXIT_SIGNAL": False}),  # Incomplete allowed
            (True, True, True, False, tasks_all_complete, {"EXIT_SIGNAL": True, "passed": False}),  # Verification failed
            (True, False, True, False, tasks_incomplete, {"EXIT_SIGNAL": True, "passed": False}),  # Verification failed
            (True, True, False, False, tasks_all_complete, {}),  # No signal
            (False, True, True, False, tasks_all_complete, {"EXIT_SIGNAL": False, "passed": False}),  # Verification failed
            (False, False, True, False, tasks_incomplete, {"EXIT_SIGNAL": False, "passed": False}),  # Verification failed
            (True, False, False, True, tasks_incomplete, {"EXIT_SIGNAL": True}),  # Incomplete allowed, signal present, no verification needed
            (False, False, False, True, tasks_incomplete, {"EXIT_SIGNAL": False}),  # No signal required, incomplete allowed, no verification
        ]

        for i, (signal, all_complete, verification, expected, tasks, ls_override) in enumerate(combinations):
            config = {
                "version": 1,
                "exit_policy": {
                    "min_completion_indicators": 2,
                    "require_exit_signal": signal,
                    "require_all_tasks_complete": all_complete,
                    "require_verification_pass": verification,
                },
                "verification": {"enabled": verification},
            }

            loop_state = sample_loop_state.copy()
            loop_state["completion_indicators"] = 2
            if "EXIT_SIGNAL" in ls_override:
                loop_state["ralph_status"] = {"EXIT_SIGNAL": ls_override["EXIT_SIGNAL"]}
            if "passed" in ls_override:
                loop_state["verification_status"] = {"passed": ls_override["passed"]}

            result = should_exit(tasks, loop_state, config)
            assert result is expected, f"Combination {i} failed: signal={signal}, all_complete={all_complete}, verification={verification}, expected={expected}, got={result}"


class TestShouldRunVerifier:
    """Test suite for should_run_verifier() function."""

    @pytest.fixture
    def sample_loop_state(self):
        """Create sample loop state."""
        return {
            "current_task_id": "TASK-003",
            "completed_tasks": ["TASK-001", "TASK-002"],
            "failed_tasks": [],
            "completion_indicators": 2,
            "loop_metadata": {
                "plan_path": "/path/to/plan.md",
                "started_at": "2026-03-14T10:00:00",
                "last_update": "2026-03-14T10:15:00",
                "iterations": 3,
            },
        }

    def test_should_run_verifier_enabled_and_required(self, sample_loop_state):
        """Test verifier runs when enabled and required by exit policy."""
        config = {
            "version": 1,
            "exit_policy": {"require_verification_pass": True},
            "verification": {"enabled": True},
        }

        result = should_run_verifier(sample_loop_state, config)
        assert result is True

    def test_should_run_verifier_disabled(self, sample_loop_state):
        """Test verifier doesn't run when disabled."""
        config = {
            "version": 1,
            "exit_policy": {"require_verification_pass": True},
            "verification": {"enabled": False},
        }

        result = should_run_verifier(sample_loop_state, config)
        assert result is False

    def test_should_run_verifier_not_required(self, sample_loop_state):
        """Test verifier doesn't run when not required by exit policy."""
        config = {
            "version": 1,
            "exit_policy": {"require_verification_pass": False},
            "verification": {"enabled": True},
        }

        result = should_run_verifier(sample_loop_state, config)
        assert result is False

    def test_should_run_verifier_already_passed(self, sample_loop_state):
        """Test verifier doesn't run if already passed."""
        loop_state = sample_loop_state.copy()
        loop_state["verification_status"] = {"passed": True, "timestamp": "2026-03-14T10:15:00"}

        config = {
            "version": 1,
            "exit_policy": {"require_verification_pass": True},
            "verification": {"enabled": True},
        }

        result = should_run_verifier(loop_state, config)
        assert result is False

    def test_should_run_verifier_already_failed(self, sample_loop_state):
        """Test verifier runs again if previously failed."""
        loop_state = sample_loop_state.copy()
        loop_state["verification_status"] = {"passed": False, "timestamp": "2026-03-14T10:15:00"}

        config = {
            "version": 1,
            "exit_policy": {"require_verification_pass": True},
            "verification": {"enabled": True},
        }

        result = should_run_verifier(loop_state, config)
        assert result is True  # Should retry

    def test_should_run_verifier_no_status(self, sample_loop_state):
        """Test verifier runs when no previous status."""
        config = {
            "version": 1,
            "exit_policy": {"require_verification_pass": True},
            "verification": {"enabled": True},
        }

        result = should_run_verifier(sample_loop_state, config)
        assert result is True


class TestPlanCaching:
    """Test suite for plan caching functionality."""

    def test_plan_cache_hit(self, tmp_path: Path):
        """Test that plan parsing is cached on second call."""
        plan_file = tmp_path / "plan.md"
        plan_content = """
# Plan

- [x] TASK-001: Complete task 1
- [ ] TASK-002: Complete task 2
- [ ] TASK-003: Complete task 3
"""
        plan_file.write_text(plan_content)

        # First call should parse
        from scripts.loop_policy import parse_plan_with_cache

        tasks1 = parse_plan_with_cache(str(plan_file))
        assert len(tasks1) == 3

        # Second call should use cache
        tasks2 = parse_plan_with_cache(str(plan_file))
        assert len(tasks2) == 3
        assert tasks1 == tasks2

    def test_plan_cache_invalidation_on_file_change(self, tmp_path: Path):
        """Test that cache is invalidated when plan file changes."""
        plan_file = tmp_path / "plan.md"
        plan_content = """
# Plan

- [x] TASK-001: Complete task 1
- [ ] TASK-002: Complete task 2
"""
        plan_file.write_text(plan_content)

        from scripts.loop_policy import parse_plan_with_cache
        import time

        # First call
        tasks1 = parse_plan_with_cache(str(plan_file))
        assert len(tasks1) == 2

        # Ensure file modification time changes
        time.sleep(0.01)

        # Modify file
        new_content = plan_content + "- [ ] TASK-003: Complete task 3\n"
        plan_file.write_text(new_content)

        # Second call should see new content
        tasks2 = parse_plan_with_cache(str(plan_file))
        assert len(tasks2) == 3
        assert tasks1 != tasks2

    def test_plan_cache_with_different_files(self, tmp_path: Path):
        """Test that cache handles different plan files separately."""
        plan_file1 = tmp_path / "plan1.md"
        plan_file2 = tmp_path / "plan2.md"

        plan_file1.write_text("- [x] Task 1 from plan 1\n")
        plan_file2.write_text("- [x] Task 2 from plan 2\n")

        from scripts.loop_policy import parse_plan_with_cache

        tasks1 = parse_plan_with_cache(str(plan_file1))
        tasks2 = parse_plan_with_cache(str(plan_file2))

        assert len(tasks1) == 1
        assert len(tasks2) == 1
        # Task IDs are generated sequentially (TASK-001, TASK-002, etc.)
        # So both will have TASK-001, but different text
        assert tasks1[0]["id"] == "TASK-001"
        assert tasks2[0]["id"] == "TASK-001"
        assert tasks1[0]["text"] == "Task 1 from plan 1"
        assert tasks2[0]["text"] == "Task 2 from plan 2"
        # Verify they're from different cache entries
        assert tasks1 != tasks2


class TestConfigReloadMidRun:
    """Test suite for config reload behavior during loop execution (TASK-011)."""

    def test_config_changes_mid_run_affect_exit_decision(self, tmp_path: Path):
        """Test that config changes mid-run affect exit decisions (TASK-011)."""
        # Create initial config requiring exit signal
        config_data = {
            "version": 1,
            "exit_policy": {
                "min_completion_indicators": 2,
                "require_exit_signal": True,  # Initially require signal
                "require_all_tasks_complete": True,
                "require_verification_pass": False,
            },
            "verification": {"enabled": False, "skill": "verify", "write_report": ".claude/loop/verification_report.md"},
            "plans": {"default_plan": "plan.md", "allow_per_terminal_plan": False},
            "logging": {"decision_log": ".claude/loop/logs/decision.log", "verifier_log": ".claude/loop/logs/verifier.log"},
        }

        config_file = tmp_path / ".claude" / "loop" / "config.yaml"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.write_text(yaml.dump(config_data))

        # Load initial config
        config1 = load_config(str(config_file))
        assert config1["exit_policy"]["require_exit_signal"] is True

        # Simulate loop state that would exit without signal requirement
        loop_state = {
            "current_task_id": "TASK-002",
            "completed_tasks": ["TASK-001", "TASK-002"],
            "failed_tasks": [],
            "completion_indicators": 2,
            "loop_metadata": {
                "plan_path": "/path/to/plan.md",
                "started_at": "2026-03-14T10:00:00",
                "last_update": "2026-03-14T10:15:00",
                "iterations": 2,
            },
        }

        tasks = [
            {"id": "TASK-001", "text": "Task 1", "complete": True},
            {"id": "TASK-002", "text": "Task 2", "complete": True},
        ]

        # First iteration: should not exit (no EXIT_SIGNAL)
        result1 = should_exit(tasks, loop_state, config1)
        assert result1 is False, "Should not exit without EXIT_SIGNAL"

        # Modify config mid-run: disable exit signal requirement
        config_data["exit_policy"]["require_exit_signal"] = False
        config_file.write_text(yaml.dump(config_data))

        # Load config again (simulating next iteration)
        config2 = load_config(str(config_file))
        assert config2["exit_policy"]["require_exit_signal"] is False, "Config should reflect changes"

        # Second iteration: should exit (signal requirement removed)
        result2 = should_exit(tasks, loop_state, config2)
        assert result2 is True, "Should exit after config change"

    def test_config_invalid_mid_run_raises_error(self, tmp_path: Path):
        """Test that invalid config mid-run is detected (TASK-011-B)."""
        # Create valid initial config
        config_data = {
            "version": 1,
            "exit_policy": {
                "min_completion_indicators": 2,
                "require_exit_signal": True,
                "require_all_tasks_complete": True,
                "require_verification_pass": False,
            },
            "verification": {"enabled": False, "skill": "verify", "write_report": ".claude/loop/verification_report.md"},
            "plans": {"default_plan": "plan.md", "allow_per_terminal_plan": False},
            "logging": {"decision_log": ".claude/loop/logs/decision.log", "verifier_log": ".claude/loop/logs/verifier.log"},
        }

        config_file = tmp_path / ".claude" / "loop" / "config.yaml"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.write_text(yaml.dump(config_data))

        # Load initial config (valid)
        config1 = load_config(str(config_file))
        assert config1["version"] == 1

        # Corrupt config mid-run
        config_file.write_text("invalid: yaml: [unclosed")

        # Loading corrupted config should raise error
        with pytest.raises(ConfigLoadError, match="Failed to parse config file"):
            load_config(str(config_file))

    def test_config_missing_mid_run_raises_error(self, tmp_path: Path):
        """Test that missing config mid-run is detected (TASK-011-B)."""
        # Create config
        config_data = {
            "version": 1,
            "exit_policy": {
                "min_completion_indicators": 2,
                "require_exit_signal": True,
                "require_all_tasks_complete": True,
                "require_verification_pass": False,
            },
            "verification": {"enabled": False, "skill": "verify", "write_report": ".claude/loop/verification_report.md"},
            "plans": {"default_plan": "plan.md", "allow_per_terminal_plan": False},
            "logging": {"decision_log": ".claude/loop/logs/decision.log", "verifier_log": ".claude/loop/logs/verifier.log"},
        }

        config_file = tmp_path / ".claude" / "loop" / "config.yaml"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.write_text(yaml.dump(config_data))

        # Load initial config
        config1 = load_config(str(config_file))
        assert config1["version"] == 1

        # Delete config mid-run
        config_file.unlink()

        # Loading missing config should raise error
        with pytest.raises(ConfigLoadError, match="Config file not found"):
            load_config(str(config_file))

    def test_config_no_module_level_caching(self, tmp_path: Path):
        """Test that load_config doesn't cache at module level (TASK-011)."""
        # Create config
        config_data = {
            "version": 1,
            "exit_policy": {
                "min_completion_indicators": 2,
                "require_exit_signal": True,
                "require_all_tasks_complete": True,
                "require_verification_pass": False,
            },
            "verification": {"enabled": False, "skill": "verify", "write_report": ".claude/loop/verification_report.md"},
            "plans": {"default_plan": "plan.md", "allow_per_terminal_plan": False},
            "logging": {"decision_log": ".claude/loop/logs/decision.log", "verifier_log": ".claude/loop/logs/verifier.log"},
        }

        config_file = tmp_path / ".claude" / "loop" / "config.yaml"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.write_text(yaml.dump(config_data))

        # Load config multiple times
        config1 = load_config(str(config_file))
        config2 = load_config(str(config_file))

        # Both should be valid
        assert config1["version"] == 1
        assert config2["version"] == 1

        # Modify config
        config_data["exit_policy"]["min_completion_indicators"] = 5
        config_file.write_text(yaml.dump(config_data))

        # Load again - should get new value
        config3 = load_config(str(config_file))
        assert config3["exit_policy"]["min_completion_indicators"] == 5, "Should load new config value"

        # First two loads should still have old value (no caching)
        assert config1["exit_policy"]["min_completion_indicators"] == 2
        assert config2["exit_policy"]["min_completion_indicators"] == 2

    def test_config_reload_performance_acceptable(self, tmp_path: Path):
        """Test that config reload overhead is acceptable (TASK-011-B)."""
        import time

        # Create config
        config_data = {
            "version": 1,
            "exit_policy": {
                "min_completion_indicators": 2,
                "require_exit_signal": True,
                "require_all_tasks_complete": True,
                "require_verification_pass": False,
            },
            "verification": {"enabled": False, "skill": "verify", "write_report": ".claude/loop/verification_report.md"},
            "plans": {"default_plan": "plan.md", "allow_per_terminal_plan": False},
            "logging": {"decision_log": ".claude/loop/logs/decision.log", "verifier_log": ".claude/loop/logs/verifier.log"},
        }

        config_file = tmp_path / ".claude" / "loop" / "config.yaml"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.write_text(yaml.dump(config_data))

        # Measure reload performance
        start = time.perf_counter()
        for _ in range(100):  # Load 100 times
            load_config(str(config_file))
        elapsed = time.perf_counter() - start

        # Should be fast: < 1 second for 100 loads (< 10ms per load)
        assert elapsed < 1.0, f"Config reload too slow: {elapsed:.3f}s for 100 loads"

        # Average per load should be < 10ms
        avg_time = elapsed / 100
        assert avg_time < 0.01, f"Average config load time too high: {avg_time*1000:.2f}ms"


class TestConfigIntegrity:
    """Test suite for config integrity validation."""

    def test_config_version_validation(self, tmp_path: Path):
        """Test that config version is validated."""
        config_data = {
            "version": 99,  # Unsupported version
            "exit_policy": {
                "min_completion_indicators": 2,
                "require_exit_signal": True,
                "require_all_tasks_complete": True,
                "require_verification_pass": True,
            },
            "verification": {"enabled": True, "skill": "prd-verifier", "write_report": ".claude/loop/verification-report.md"},
            "plans": {"default_plan": "plan.md", "allow_per_terminal_plan": True},
            "logging": {"decision_log": "decision.log", "verifier_log": "verifier.log"},
        }

        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump(config_data))

        with pytest.raises(ConfigIntegrityError, match="Unsupported config version"):
            load_config(str(config_file))

    def test_config_missing_required_sections(self, tmp_path: Path):
        """Test that all required sections are present."""
        config_data = {
            "version": 1,
            "exit_policy": {
                "min_completion_indicators": 2,
                "require_exit_signal": True,
                "require_all_tasks_complete": True,
                "require_verification_pass": True,
            },
            # Missing verification, plans, logging
        }

        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump(config_data))

        with pytest.raises(ConfigIntegrityError, match="Missing required config section"):
            load_config(str(config_file))

    def test_config_field_type_validation(self, tmp_path: Path):
        """Test that config field types are validated."""
        config_data = {
            "version": 1,
            "exit_policy": {
                "min_completion_indicators": "invalid",  # Should be int
                "require_exit_signal": True,
                "require_all_tasks_complete": True,
                "require_verification_pass": True,
            },
            "verification": {"enabled": True, "skill": "prd-verifier", "write_report": ".claude/loop/verification-report.md"},
            "plans": {"default_plan": "plan.md", "allow_per_terminal_plan": True},
            "logging": {"decision_log": "decision.log", "verifier_log": "verifier.log"},
        }

        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump(config_data))

        with pytest.raises(ConfigIntegrityError, match="Invalid type for field"):
            load_config(str(config_file))


class TestParsePlanRequirements:
    """Test suite for parse_plan_requirements() function."""

    def test_parse_plan_with_acceptance_criteria(self, tmp_path: Path):
        """Test extracting acceptance criteria from plan."""
        plan_content = """# Implementation Plan

## Acceptance Criteria

- [ ] All tests pass
- [ ] Documentation complete
- [ ] Code reviewed

## Tasks

- [ ] Task 1
- [ ] Task 2
"""
        plan_file = tmp_path / "plan.md"
        plan_file.write_text(plan_content)

        from scripts.loop_policy import parse_plan_requirements

        requirements = parse_plan_requirements(plan_file)

        assert len(requirements["acceptance_criteria"]) == 3
        assert "All tests pass" in requirements["acceptance_criteria"]
        assert "Documentation complete" in requirements["acceptance_criteria"]
        assert "Code reviewed" in requirements["acceptance_criteria"]

    def test_parse_plan_with_success_metrics(self, tmp_path: Path):
        """Test extracting success metrics from plan."""
        plan_content = """# Implementation Plan

## Success Metrics

- [ ] 90% test coverage
- [ ] < 100ms response time
- [ ] Zero critical bugs

## Tasks

- [ ] Task 1
"""
        plan_file = tmp_path / "plan.md"
        plan_file.write_text(plan_content)

        from scripts.loop_policy import parse_plan_requirements

        requirements = parse_plan_requirements(plan_file)

        assert len(requirements["success_metrics"]) == 3
        assert "90% test coverage" in requirements["success_metrics"]
        assert "Zero critical bugs" in requirements["success_metrics"]

    def test_parse_plan_with_constraints(self, tmp_path: Path):
        """Test extracting constraints from plan."""
        plan_content = """# Implementation Plan

## Constraints

- Must use Python 3.14+
- Must be backward compatible
- No external dependencies

## Tasks

- [ ] Task 1
"""
        plan_file = tmp_path / "plan.md"
        plan_file.write_text(plan_content)

        from scripts.loop_policy import parse_plan_requirements

        requirements = parse_plan_requirements(plan_file)

        assert len(requirements["constraints"]) >= 2

    def test_parse_plan_missing_file(self):
        """Test that missing plan file raises error."""
        from scripts.loop_policy import parse_plan_requirements

        with pytest.raises(FileNotFoundError):
            parse_plan_requirements("nonexistent.md")

    def test_parse_plan_no_requirements_section(self, tmp_path: Path):
        """Test plan without requirements section."""
        plan_content = """
# Implementation Plan

## Tasks

- [ ] Task 1
- [ ] Task 2
"""
        plan_file = tmp_path / "plan.md"
        plan_file.write_text(plan_content)

        from scripts.loop_policy import parse_plan_requirements

        requirements = parse_plan_requirements(plan_file)

        assert len(requirements["requirements"]) == 0


class TestVerifyCompletionAgainstRequirements:
    """Test suite for verify_completion_against_requirements() function."""

    def test_all_requirements_met(self):
        """Test when all requirements are satisfied."""
        tasks = [
            {"text": "All tests pass", "complete": True},
            {"text": "Documentation complete", "complete": True},
            {"text": "Code reviewed", "complete": True},
        ]

        requirements = {
            "requirements": ["All tests pass", "Documentation complete", "Code reviewed"]
        }

        from scripts.loop_policy import verify_completion_against_requirements

        result = verify_completion_against_requirements(tasks, requirements)

        assert result["all_requirements_met"] is True
        assert len(result["missing_criteria"]) == 0
        assert result["completion_rate"] == 1.0

    def test_some_requirements_missing(self):
        """Test when some requirements are not satisfied."""
        tasks = [
            {"text": "All tests pass", "complete": True},
            # Missing: Documentation complete
            # Missing: Code reviewed
        ]

        requirements = {
            "requirements": ["All tests pass", "Documentation complete", "Code reviewed"]
        }

        from scripts.loop_policy import verify_completion_against_requirements

        result = verify_completion_against_requirements(tasks, requirements)

        assert result["all_requirements_met"] is False
        assert len(result["missing_criteria"]) == 2
        assert result["completion_rate"] == pytest.approx(0.333, rel=0.01)

    def test_partial_match_fuzzy_matching(self):
        """Test fuzzy matching of task text to requirements."""
        tasks = [
            {"text": "Implement all tests and they pass", "complete": True},
            # Partial match for "Documentation complete"
        ]

        requirements = {
            "requirements": ["All tests pass", "Documentation complete"]
        }

        from scripts.loop_policy import verify_completion_against_requirements

        result = verify_completion_against_requirements(tasks, requirements)

        # "Implement all tests and they pass" should match "All tests pass"
        assert result["all_requirements_met"] is False
        assert len(result["matched_criteria"]) == 1

    def test_empty_requirements(self):
        """Test with empty requirements list."""
        tasks = [
            {"text": "Some task", "complete": True},
        ]

        requirements = {
            "requirements": []
        }

        from scripts.loop_policy import verify_completion_against_requirements

        result = verify_completion_against_requirements(tasks, requirements)

        assert result["all_requirements_met"] is True
        assert result["completion_rate"] == 1.0


class TestExtractUserConcernsFromChat:
    """Test suite for extract_user_concerns_from_chat() function."""

    def test_extract_blocker_concerns(self, tmp_path: Path):
        """Test extracting blocker concerns from transcript."""
        import json

        transcript = [
            {"role": "assistant", "content": "Here's the implementation"},
            {"role": "user", "content": "This is blocked, can't proceed without fixing the API"},
            {"role": "assistant", "content": "I'll fix it"},
        ]

        transcript_file = tmp_path / "transcript.jsonl"
        with open(transcript_file, "w") as f:
            for turn in transcript:
                f.write(json.dumps(turn) + "\n")

        from scripts.loop_policy import extract_user_concerns_from_chat

        concerns = extract_user_concerns_from_chat(str(transcript_file), lookback_turns=10)

        assert len(concerns) == 1
        assert concerns[0]["severity"] == "blocker"
        assert "blocked" in concerns[0]["concern"].lower()

    def test_extract_issue_concerns(self, tmp_path: Path):
        """Test extracting issue concerns from transcript."""
        import json

        transcript = [
            {"role": "assistant", "content": "Done"},
            {"role": "user", "content": "There's a bug in the login flow"},
            {"role": "assistant", "content": "I'll fix it"},
        ]

        transcript_file = tmp_path / "transcript.jsonl"
        with open(transcript_file, "w") as f:
            for turn in transcript:
                f.write(json.dumps(turn) + "\n")

        from scripts.loop_policy import extract_user_concerns_from_chat

        concerns = extract_user_concerns_from_chat(str(transcript_file), lookback_turns=10)

        assert len(concerns) == 1
        assert concerns[0]["severity"] == "issue"

    def test_no_concerns(self, tmp_path: Path):
        """Test transcript with no concerns."""
        import json

        transcript = [
            {"role": "assistant", "content": "Implementation complete"},
            {"role": "user", "content": "Looks good, thanks"},
            {"role": "assistant", "content": "You're welcome"},
        ]

        transcript_file = tmp_path / "transcript.jsonl"
        with open(transcript_file, "w") as f:
            for turn in transcript:
                f.write(json.dumps(turn) + "\n")

        from scripts.loop_policy import extract_user_concerns_from_chat

        concerns = extract_user_concerns_from_chat(str(transcript_file), lookback_turns=10)

        assert len(concerns) == 0

    def test_missing_transcript_file(self):
        """Test with missing transcript file."""
        from scripts.loop_policy import extract_user_concerns_from_chat

        concerns = extract_user_concerns_from_chat("nonexistent.jsonl", lookback_turns=10)

        assert len(concerns) == 0

    def test_none_transcript_path(self):
        """Test with None transcript path."""
        from scripts.loop_policy import extract_user_concerns_from_chat

        concerns = extract_user_concerns_from_chat(None, lookback_turns=10)

        assert len(concerns) == 0

    def test_lookback_turns_limit(self, tmp_path: Path):
        """Test that lookback_turns limits analysis scope."""
        import json

        # Create 20 turns, with concerns in turns 5, 10, 15, 19
        transcript = []
        for i in range(20):
            if i in [4, 9, 14, 18]:  # 0-indexed
                transcript.append({"role": "user", "content": f"This is wrong #{i}"})
            else:
                transcript.append({"role": "assistant", "content": f"Response #{i}"})

        transcript_file = tmp_path / "transcript.jsonl"
        with open(transcript_file, "w") as f:
            for turn in transcript:
                f.write(json.dumps(turn) + "\n")

        from scripts.loop_policy import extract_user_concerns_from_chat

        # Only look at last 10 turns (should find concerns at turns 14, 18)
        concerns = extract_user_concerns_from_chat(str(transcript_file), lookback_turns=10)

        # Should find 2 concerns (from last 10 turns)
        assert len(concerns) == 2


class TestPracticalVerificationIntegration:
    """Integration tests for practical verification with should_exit()."""

    def test_should_exit_with_practical_verification_pass(self, tmp_path: Path):
        """Test should_exit() with practical verification that passes."""
        # Create plan with requirements
        plan_content = """
# Plan

## Acceptance Criteria

- [ ] Task 1 complete
- [ ] Task 2 complete

## Tasks

- [ ] Task 1 complete
- [ ] Task 2 complete
"""
        plan_file = tmp_path / "plan.md"
        plan_file.write_text(plan_content)

        # Create empty transcript (no concerns)
        import json
        transcript_file = tmp_path / "transcript.jsonl"
        transcript_file.write_text(json.dumps({"role": "user", "content": "Looks good"}) + "\n")

        # Config with verification enabled
        config = {
            "version": 1,
            "exit_policy": {
                "min_completion_indicators": 1,
                "require_exit_signal": True,
                "require_all_tasks_complete": False,
                "require_verification_pass": True,
            },
            "verification": {"enabled": True, "skill": "prd-verifier", "write_report": ".claude/loop/verification-report.md"},
            "plans": {"default_plan": "plan.md", "allow_per_terminal_plan": True},
            "logging": {"decision_log": "decision.log", "verifier_log": "verifier.log"},
        }

        # Tasks that meet requirements
        tasks = [
            {"text": "Task 1 complete", "complete": True},
            {"text": "Task 2 complete", "complete": True},
        ]

        # Loop state with EXIT_SIGNAL and metadata
        loop_state = {
            "completion_indicators": 2,
            "ralph_status": {"EXIT_SIGNAL": True},
            "metadata": {
                "plan_path": str(plan_file),
                "transcript_path": str(transcript_file),
            },
        }

        from scripts.loop_policy import should_exit

        result = should_exit(tasks, loop_state, config)

        assert result is True

    def test_should_exit_with_practical_verification_fail_requirements(self, tmp_path: Path):
        """Test should_exit() fails when requirements not met."""
        # Create plan with requirements
        plan_content = """
# Plan

## Acceptance Criteria

- [ ] Task 1 complete
- [ ] Task 2 complete

## Tasks

- [ ] Task 1 complete
- [ ] Task 2 complete
"""
        plan_file = tmp_path / "plan.md"
        plan_file.write_text(plan_content)

        # Create empty transcript (no concerns)
        import json
        transcript_file = tmp_path / "transcript.jsonl"
        transcript_file.write_text(json.dumps({"role": "user", "content": "Continue"}) + "\n")

        # Config with verification enabled
        config = {
            "version": 1,
            "exit_policy": {
                "min_completion_indicators": 1,
                "require_exit_signal": True,
                "require_all_tasks_complete": False,
                "require_verification_pass": True,
            },
            "verification": {"enabled": True, "skill": "prd-verifier", "write_report": ".claude/loop/verification-report.md"},
            "plans": {"default_plan": "plan.md", "allow_per_terminal_plan": True},
            "logging": {"decision_log": "decision.log", "verifier_log": "verifier.log"},
        }

        # Tasks that DON'T meet requirements (only one task complete)
        tasks = [
            {"text": "Task 1 complete", "complete": True},
            # Missing: Task 2 complete
        ]

        # Loop state with EXIT_SIGNAL and metadata
        loop_state = {
            "completion_indicators": 1,
            "ralph_status": {"EXIT_SIGNAL": True},
            "metadata": {
                "plan_path": str(plan_file),
                "transcript_path": str(transcript_file),
            },
        }

        from scripts.loop_policy import should_exit

        result = should_exit(tasks, loop_state, config)

        assert result is False
        assert loop_state["verification_status"]["passed"] is False
        assert loop_state["verification_status"]["reason"] == "Requirements not met"

    def test_should_exit_with_practical_verification_fail_user_concerns(self, tmp_path: Path):
        """Test should_exit() fails when user has concerns."""
        # Create plan with requirements
        plan_content = """
# Plan

## Acceptance Criteria

- [ ] Task 1 complete

## Tasks

- [ ] Task 1 complete
"""
        plan_file = tmp_path / "plan.md"
        plan_file.write_text(plan_content)

        # Create transcript with user concern
        import json
        transcript_file = tmp_path / "transcript.jsonl"
        transcript = [
            {"role": "assistant", "content": "Task 1 is done"},
            {"role": "user", "content": "This is blocked, doesn't work"},
        ]
        with open(transcript_file, "w") as f:
            for turn in transcript:
                f.write(json.dumps(turn) + "\n")

        # Config with verification enabled
        config = {
            "version": 1,
            "exit_policy": {
                "min_completion_indicators": 1,
                "require_exit_signal": True,
                "require_all_tasks_complete": False,
                "require_verification_pass": True,
            },
            "verification": {"enabled": True, "skill": "prd-verifier", "write_report": ".claude/loop/verification-report.md"},
            "plans": {"default_plan": "plan.md", "allow_per_terminal_plan": True},
            "logging": {"decision_log": "decision.log", "verifier_log": "verifier.log"},
        }

        # Tasks that meet requirements
        tasks = [
            {"text": "Task 1 complete", "complete": True},
        ]

        # Loop state with EXIT_SIGNAL and metadata
        loop_state = {
            "completion_indicators": 1,
            "ralph_status": {"EXIT_SIGNAL": True},
            "metadata": {
                "plan_path": str(plan_file),
                "transcript_path": str(transcript_file),
            },
        }

        from scripts.loop_policy import should_exit

        result = should_exit(tasks, loop_state, config)

        assert result is False
        assert loop_state["verification_status"]["passed"] is False
        assert loop_state["verification_status"]["reason"] == "User concerns detected"
        assert len(loop_state["verification_status"]["concerns"]) > 0

    def test_should_exit_with_practical_verification_missing_plan(self, tmp_path: Path):
        """Test should_exit() fails gracefully when plan missing."""
        # Config with verification enabled
        config = {
            "version": 1,
            "exit_policy": {
                "min_completion_indicators": 1,
                "require_exit_signal": True,
                "require_all_tasks_complete": False,
                "require_verification_pass": False,  # Verification not required
            },
            "verification": {"enabled": True, "skill": "prd-verifier", "write_report": ".claude/loop/verification-report.md"},
            "plans": {"default_plan": "plan.md", "allow_per_terminal_plan": True},
            "logging": {"decision_log": "decision.log", "verifier_log": "verifier.log"},
        }

        # Loop state without plan_path (should not crash)
        loop_state = {
            "completion_indicators": 1,
            "ralph_status": {"EXIT_SIGNAL": True},
            "metadata": {},  # No plan_path
        }

        tasks = [{"text": "Task 1", "complete": True}]

        from scripts.loop_policy import should_exit

        # Should not crash, should exit based on basic conditions
        result = should_exit(tasks, loop_state, config)

        assert result is True
