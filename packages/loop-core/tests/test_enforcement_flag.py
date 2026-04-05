"""Tests for TASK-018: enforcement.enabled feature flag.

Tests the enforcement mode feature flag that controls minimal vs full policy:
- Disabled mode: Minimal policy (EXIT_SIGNAL + completion_indicators only)
- Enabled mode: Full policy (all flags including verification)
"""

from pathlib import Path

import pytest
import yaml

from scripts.loop_policy import (
    ConfigIntegrityError,
    load_config,
    should_exit,
)


class TestEnforcementFlagConfig:
    """Test suite for enforcement.enabled configuration."""

    def test_load_config_with_enforcement_enabled(self, tmp_path: Path):
        """Test loading config with enforcement.enabled=true."""
        config_data = {
            "version": 1,
            "enforcement": {"enabled": True},
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

        config = load_config(str(config_file))

        assert config["enforcement"]["enabled"] is True
        assert config["exit_policy"]["require_verification_pass"] is True

    def test_load_config_with_enforcement_disabled(self, tmp_path: Path):
        """Test loading config with enforcement.enabled=false."""
        config_data = {
            "version": 1,
            "enforcement": {"enabled": False},
            "exit_policy": {
                "min_completion_indicators": 2,
                "require_exit_signal": True,
                "require_all_tasks_complete": True,
                "require_verification_pass": True,  # Ignored when enforcement disabled
            },
            "verification": {"enabled": True, "skill": "prd-verifier", "write_report": ".claude/loop/verification-report.md"},
            "plans": {"default_plan": "plan.md", "allow_per_terminal_plan": True},
            "logging": {"decision_log": "decision.log", "verifier_log": "verifier.log"},
        }

        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump(config_data))

        config = load_config(str(config_file))

        assert config["enforcement"]["enabled"] is False

    def test_load_config_defaults_enforcement_to_enabled(self, tmp_path: Path):
        """Test that enforcement defaults to enabled when not specified."""
        config_data = {
            "version": 1,
            # No enforcement section - should default to enabled
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

        config = load_config(str(config_file))

        # Should default to enabled (backward compatible)
        assert config.get("enforcement", {}).get("enabled", True) is True

    def test_enforcement_flag_must_be_boolean(self, tmp_path: Path):
        """Test that enforcement.enabled must be a boolean."""
        config_data = {
            "version": 1,
            "enforcement": {"enabled": "not-a-boolean"},
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

        with pytest.raises(ConfigIntegrityError, match="Invalid type for field enforcement.enabled"):
            load_config(str(config_file))


class TestEnforcementModeExitBehavior:
    """Test suite for enforcement mode behavior in should_exit()."""

    @pytest.fixture
    def sample_tasks(self):
        """Create sample tasks list."""
        return [
            {"id": "TASK-001", "text": "Task 1", "complete": True},
            {"id": "TASK-002", "text": "Task 2", "complete": True},
            {"id": "TASK-003", "text": "Task 3", "complete": False},  # Incomplete
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

    def test_disabled_mode_exits_with_minimal_conditions(self, sample_tasks, sample_loop_state):
        """Test that disabled mode exits with EXIT_SIGNAL + completion_indicators only."""
        config = {
            "version": 1,
            "enforcement": {"enabled": False},
            "exit_policy": {
                "min_completion_indicators": 2,
                "require_exit_signal": True,
                "require_all_tasks_complete": True,  # Ignored in disabled mode
                "require_verification_pass": True,  # Ignored in disabled mode
            },
            "verification": {"enabled": True},
        }

        loop_state = sample_loop_state.copy()
        loop_state["completion_indicators"] = 2
        loop_state["ralph_status"] = {"EXIT_SIGNAL": True}
        # No verification status, incomplete tasks - should still exit

        result = should_exit(sample_tasks, loop_state, config)
        assert result is True, "Should exit with minimal conditions when enforcement disabled"

    def test_disabled_mode_requires_min_completion_indicators(self, sample_tasks, sample_loop_state):
        """Test that disabled mode still requires min_completion_indicators."""
        config = {
            "version": 1,
            "enforcement": {"enabled": False},
            "exit_policy": {
                "min_completion_indicators": 2,
                "require_exit_signal": True,
                "require_all_tasks_complete": True,
                "require_verification_pass": True,
            },
            "verification": {"enabled": True},
        }

        loop_state = sample_loop_state.copy()
        loop_state["completion_indicators"] = 1  # Below minimum
        loop_state["ralph_status"] = {"EXIT_SIGNAL": True}

        result = should_exit(sample_tasks, loop_state, config)
        assert result is False, "Should not exit without min_completion_indicators"

    def test_disabled_mode_requires_exit_signal(self, sample_tasks, sample_loop_state):
        """Test that disabled mode requires EXIT_SIGNAL."""
        config = {
            "version": 1,
            "enforcement": {"enabled": False},
            "exit_policy": {
                "min_completion_indicators": 2,
                "require_exit_signal": True,
                "require_all_tasks_complete": True,
                "require_verification_pass": True,
            },
            "verification": {"enabled": True},
        }

        loop_state = sample_loop_state.copy()
        loop_state["completion_indicators"] = 2
        # No EXIT_SIGNAL

        result = should_exit(sample_tasks, loop_state, config)
        assert result is False, "Should not exit without EXIT_SIGNAL"

    def test_enabled_mode_requires_all_conditions(self, sample_tasks, sample_loop_state):
        """Test that enabled mode requires all exit policy conditions."""
        config = {
            "version": 1,
            "enforcement": {"enabled": True},
            "exit_policy": {
                "min_completion_indicators": 2,
                "require_exit_signal": True,
                "require_all_tasks_complete": True,  # Enforced
                "require_verification_pass": True,  # Enforced
            },
            "verification": {"enabled": True},
        }

        loop_state = sample_loop_state.copy()
        loop_state["completion_indicators"] = 2
        loop_state["ralph_status"] = {"EXIT_SIGNAL": True}
        loop_state["verification_status"] = {"passed": True}

        # One task incomplete - should not exit
        result = should_exit(sample_tasks, loop_state, config)
        assert result is False, "Should not exit with incomplete tasks when enforcement enabled"

    def test_enabled_mode_exits_with_all_conditions_met(self, sample_tasks, sample_loop_state):
        """Test that enabled mode exits when all conditions are met."""
        config = {
            "version": 1,
            "enforcement": {"enabled": True},
            "exit_policy": {
                "min_completion_indicators": 2,
                "require_exit_signal": True,
                "require_all_tasks_complete": True,
                "require_verification_pass": True,
            },
            "verification": {"enabled": True},
        }

        loop_state = sample_loop_state.copy()
        loop_state["completion_indicators"] = 2
        loop_state["ralph_status"] = {"EXIT_SIGNAL": True}
        loop_state["verification_status"] = {"passed": True}

        # Mark all tasks complete
        tasks_all_complete = [task.copy() for task in sample_tasks]
        tasks_all_complete[2]["complete"] = True

        result = should_exit(tasks_all_complete, loop_state, config)
        assert result is True, "Should exit when all conditions met when enforcement enabled"

    def test_enabled_mode_requires_verification_pass(self, sample_tasks, sample_loop_state):
        """Test that enabled mode requires verification pass."""
        config = {
            "version": 1,
            "enforcement": {"enabled": True},
            "exit_policy": {
                "min_completion_indicators": 2,
                "require_exit_signal": True,
                "require_all_tasks_complete": True,
                "require_verification_pass": True,
            },
            "verification": {"enabled": True},
        }

        loop_state = sample_loop_state.copy()
        loop_state["completion_indicators"] = 2
        loop_state["ralph_status"] = {"EXIT_SIGNAL": True}
        loop_state["verification_status"] = {"passed": False}  # Verification failed

        tasks_all_complete = [task.copy() for task in sample_tasks]
        tasks_all_complete[2]["complete"] = True

        result = should_exit(tasks_all_complete, loop_state, config)
        assert result is False, "Should not exit without verification pass when enforcement enabled"


class TestEnforcementModeTransitions:
    """Test suite for switching between enforcement modes."""

    def test_switch_from_disabled_to_enabled_mid_run(self, tmp_path: Path):
        """Test switching from disabled to enabled mode during loop execution."""
        config_data = {
            "version": 1,
            "enforcement": {"enabled": False},
            "exit_policy": {
                "min_completion_indicators": 2,
                "require_exit_signal": True,
                "require_all_tasks_complete": True,
                "require_verification_pass": True,
            },
            "verification": {"enabled": True, "skill": "prd-verifier", "write_report": ".claude/loop/verification-report.md"},
            "plans": {"default_plan": "plan.md", "allow_per_terminal_plan": False},
            "logging": {"decision_log": "decision.log", "verifier_log": "verifier.log"},
        }

        config_file = tmp_path / ".claude" / "loop" / "config.yaml"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.write_text(yaml.dump(config_data))

        # Load initial config (disabled)
        config1 = load_config(str(config_file))
        assert config1["enforcement"]["enabled"] is False

        # State that would exit in disabled mode
        loop_state = {
            "completion_indicators": 2,
            "ralph_status": {"EXIT_SIGNAL": True},
        }

        tasks = [
            {"id": "TASK-001", "text": "Task 1", "complete": True},
            {"id": "TASK-002", "text": "Task 2", "complete": False},  # Incomplete
        ]

        # Should exit in disabled mode
        result1 = should_exit(tasks, loop_state, config1)
        assert result1 is True, "Should exit in disabled mode with minimal conditions"

        # Switch to enabled mode
        config_data["enforcement"]["enabled"] = True
        config_file.write_text(yaml.dump(config_data))

        # Load new config (enabled)
        config2 = load_config(str(config_file))
        assert config2["enforcement"]["enabled"] is True

        # Should NOT exit in enabled mode (incomplete task, no verification)
        result2 = should_exit(tasks, loop_state, config2)
        assert result2 is False, "Should not exit in enabled mode without all conditions"

    def test_switch_from_enabled_to_disabled_mid_run(self, tmp_path: Path):
        """Test switching from enabled to disabled mode during loop execution."""
        config_data = {
            "version": 1,
            "enforcement": {"enabled": True},
            "exit_policy": {
                "min_completion_indicators": 2,
                "require_exit_signal": True,
                "require_all_tasks_complete": True,
                "require_verification_pass": True,
            },
            "verification": {"enabled": True, "skill": "prd-verifier", "write_report": ".claude/loop/verification-report.md"},
            "plans": {"default_plan": "plan.md", "allow_per_terminal_plan": False},
            "logging": {"decision_log": "decision.log", "verifier_log": "verifier.log"},
        }

        config_file = tmp_path / ".claude" / "loop" / "config.yaml"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.write_text(yaml.dump(config_data))

        # Load initial config (enabled)
        config1 = load_config(str(config_file))
        assert config1["enforcement"]["enabled"] is True

        # State that would NOT exit in enabled mode
        loop_state = {
            "completion_indicators": 2,
            "ralph_status": {"EXIT_SIGNAL": True},
        }

        tasks = [
            {"id": "TASK-001", "text": "Task 1", "complete": True},
            {"id": "TASK-002", "text": "Task 2", "complete": False},  # Incomplete
        ]

        # Should not exit in enabled mode
        result1 = should_exit(tasks, loop_state, config1)
        assert result1 is False, "Should not exit in enabled mode without all conditions"

        # Switch to disabled mode
        config_data["enforcement"]["enabled"] = False
        config_file.write_text(yaml.dump(config_data))

        # Load new config (disabled)
        config2 = load_config(str(config_file))
        assert config2["enforcement"]["enabled"] is False

        # Should exit in disabled mode
        result2 = should_exit(tasks, loop_state, config2)
        assert result2 is True, "Should exit in disabled mode with minimal conditions"


class TestEnforcementFlagEdgeCases:
    """Test suite for enforcement flag edge cases."""

    def test_backward_compatibility_no_enforcement_section(self, tmp_path: Path):
        """Test that config without enforcement section defaults to enabled mode."""
        config_data = {
            "version": 1,
            # No enforcement section
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

        config = load_config(str(config_file))

        # Should default to enabled (backward compatible)
        assert config.get("enforcement", {}).get("enabled", True) is True

    @pytest.fixture
    def sample_tasks(self):
        """Create sample tasks list."""
        return [
            {"id": "TASK-001", "text": "Task 1", "complete": True},
            {"id": "TASK-002", "text": "Task 2", "complete": True},
        ]

    @pytest.fixture
    def sample_loop_state(self):
        """Create sample loop state."""
        return {
            "completion_indicators": 2,
            "ralph_status": {"EXIT_SIGNAL": True},
            "verification_status": {"passed": True},
        }

    def test_disabled_mode_ignores_require_all_tasks_complete(self, sample_tasks, sample_loop_state):
        """Test that disabled mode ignores require_all_tasks_complete."""
        config = {
            "version": 1,
            "enforcement": {"enabled": False},
            "exit_policy": {
                "min_completion_indicators": 2,
                "require_exit_signal": True,
                "require_all_tasks_complete": False,  # Explicitly false
                "require_verification_pass": False,  # Explicitly false
            },
            "verification": {"enabled": False},
        }

        # Even with flags set to false, disabled mode only uses EXIT_SIGNAL + min_indicators
        result = should_exit(sample_tasks, sample_loop_state, config)
        assert result is True, "Disabled mode should exit with minimal conditions"

    def test_disabled_mode_with_require_exit_signal_false(self, sample_tasks, sample_loop_state):
        """Test disabled mode behavior when require_exit_signal is false."""
        config = {
            "version": 1,
            "enforcement": {"enabled": False},
            "exit_policy": {
                "min_completion_indicators": 2,
                "require_exit_signal": False,  # Should be ignored in disabled mode
                "require_all_tasks_complete": True,
                "require_verification_pass": True,
            },
            "verification": {"enabled": True},
        }

        # Disabled mode should still require EXIT_SIGNAL even if flag is false
        loop_state = sample_loop_state.copy()
        del loop_state["ralph_status"]  # No EXIT_SIGNAL

        result = should_exit(sample_tasks, loop_state, config)
        assert result is False, "Disabled mode should require EXIT_SIGNAL regardless of flag"
