"""Tests for loop config schema validation."""

from pathlib import Path

import pytest
import yaml

from scripts.config_schema import (
    ConfigError,
    ConfigSchema,
    ExitPolicyConfig,
    LoggingConfig,
    PlansConfig,
    VerificationConfig,
)


class TestConfigSchemaLoading:
    """Test suite for config schema loading and validation."""

    @pytest.fixture
    def sample_config_path(self, tmp_path: Path) -> Path:
        """Create a sample config file for testing."""
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
                "fields": ["prd_coverage", "spec_compliance", "implementation_quality"],
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

        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump(config_data))
        return config_file

    @pytest.fixture
    def invalid_config_path(self, tmp_path: Path) -> Path:
        """Create an invalid config file for testing."""
        config_data = {
            "version": "invalid",  # Should be int
            "exit_policy": {
                # Missing required fields
            },
        }

        config_file = tmp_path / "invalid_config.yaml"
        config_file.write_text(yaml.dump(config_data))
        return config_file

    def test_load_valid_config(self, sample_config_path: Path):
        """Test loading a valid config file."""
        config = ConfigSchema.load_from_file(sample_config_path)

        assert config.version == 1
        assert config.exit_policy.min_completion_indicators == 2
        assert config.exit_policy.require_exit_signal is True
        assert config.exit_policy.require_all_tasks_complete is True
        assert config.exit_policy.require_verification_pass is True
        assert config.verification.enabled is True
        assert config.verification.skill == "prd-verifier"
        assert config.verification.write_report == ".claude/loop/verification-report.md"
        assert config.verification.fields == ["prd_coverage", "spec_compliance", "implementation_quality"]
        assert config.plans.default_plan == "plan.md"
        assert config.plans.allow_per_terminal_plan is True
        assert config.logging.decision_log == "decision.log"
        assert config.logging.verifier_log == "verifier.log"

    def test_load_missing_config_file(self, tmp_path: Path):
        """Test loading a missing config file raises ConfigError."""
        missing_path = tmp_path / "nonexistent.yaml"

        with pytest.raises(ConfigError, match="Config file not found"):
            ConfigSchema.load_from_file(missing_path)

    def test_load_invalid_yaml(self, tmp_path: Path):
        """Test loading invalid YAML raises ConfigError."""
        invalid_yaml = tmp_path / "invalid.yaml"
        invalid_yaml.write_text("invalid: yaml: content: [unclosed")

        with pytest.raises(ConfigError, match="Failed to parse config file"):
            ConfigSchema.load_from_file(invalid_yaml)

    def test_load_invalid_schema(self, invalid_config_path: Path):
        """Test loading config with invalid schema raises ConfigError."""
        with pytest.raises(ConfigError, match="Missing required config sections"):
            ConfigSchema.load_from_file(invalid_config_path)

    def test_exit_policy_config_validation(self):
        """Test ExitPolicyConfig field validation."""
        # Valid config
        exit_policy = ExitPolicyConfig(
            min_completion_indicators=2,
            require_exit_signal=True,
            require_all_tasks_complete=True,
            require_verification_pass=True,
        )
        assert exit_policy.min_completion_indicators == 2

        # Invalid min_completion_indicators (must be >= 1)
        with pytest.raises(ConfigError):
            ExitPolicyConfig(
                min_completion_indicators=0,  # Invalid
                require_exit_signal=True,
                require_all_tasks_complete=True,
                require_verification_pass=True,
            )

    def test_verification_config_validation(self):
        """Test VerificationConfig field validation."""
        # Valid config with fields
        verification = VerificationConfig(
            enabled=True,
            skill="prd-verifier",
            write_report=".claude/loop/verification-report.md",
            fields=["prd_coverage", "spec_compliance", "implementation_quality"],
        )
        assert verification.enabled is True
        assert verification.fields == ["prd_coverage", "spec_compliance", "implementation_quality"]

        # Valid config without fields (uses defaults)
        verification_minimal = VerificationConfig(
            enabled=True,
            skill="prd-verifier",
            write_report=".claude/loop/verification-report.md",
        )
        assert verification_minimal.fields == ["prd_coverage", "spec_compliance", "implementation_quality"]

        # Invalid skill name (empty)
        with pytest.raises(ConfigError):
            VerificationConfig(
                enabled=True,
                skill="",  # Invalid
                write_report=".claude/loop/verification-report.md",
            )

        # Invalid field name (empty string in list)
        with pytest.raises(ConfigError):
            VerificationConfig(
                enabled=True,
                skill="prd-verifier",
                write_report=".claude/loop/verification-report.md",
                fields=["prd_coverage", "", "implementation_quality"],  # Invalid empty field
            )

        # Invalid field name (not a string)
        with pytest.raises(ConfigError):
            VerificationConfig(
                enabled=True,
                skill="prd-verifier",
                write_report=".claude/loop/verification-report.md",
                fields=["prd_coverage", 123, "implementation_quality"],  # Invalid type
            )

    def test_plans_config_validation(self):
        """Test PlansConfig field validation."""
        # Valid config
        plans = PlansConfig(
            default_plan="plan.md",
            allow_per_terminal_plan=True,
        )
        assert plans.default_plan == "plan.md"

        # Invalid default_plan (empty)
        with pytest.raises(ConfigError):
            PlansConfig(
                default_plan="",  # Invalid
                allow_per_terminal_plan=True,
            )

    def test_logging_config_validation(self):
        """Test LoggingConfig field validation."""
        # Valid config
        logging = LoggingConfig(
            decision_log="decision.log",
            verifier_log="verifier.log",
        )
        assert logging.decision_log == "decision.log"

        # Invalid log file (empty)
        with pytest.raises(ConfigError):
            LoggingConfig(
                decision_log="",  # Invalid
                verifier_log="verifier.log",
            )

    def test_get_default_config(self):
        """Test getting default configuration."""
        config = ConfigSchema.get_default()

        assert config.version == 1
        assert config.exit_policy.min_completion_indicators == 2
        assert config.exit_policy.require_exit_signal is True
        assert config.verification.enabled is True
        assert config.plans.default_plan == "plan.md"
        assert config.logging.decision_log == "decision.log"

    def test_config_to_dict(self, sample_config_path: Path):
        """Test converting config to dictionary."""
        config = ConfigSchema.load_from_file(sample_config_path)
        config_dict = config.to_dict()

        assert config_dict["version"] == 1
        assert config_dict["exit_policy"]["min_completion_indicators"] == 2
        assert config_dict["verification"]["enabled"] is True
        assert config_dict["plans"]["default_plan"] == "plan.md"
        assert config_dict["logging"]["decision_log"] == "decision.log"


class TestConfigFileIntegration:
    """Integration tests for config file loading in actual project structure."""

    def test_load_default_project_config(self):
        """Test loading the default project config file."""
        # Check if default config exists
        config_path = Path.cwd() / ".claude" / "loop" / "config.yaml"

        if config_path.exists():
            config = ConfigSchema.load_from_file(config_path)
            assert config.version == 1
            assert isinstance(config.exit_policy, ExitPolicyConfig)
            assert isinstance(config.verification, VerificationConfig)
            assert isinstance(config.plans, PlansConfig)
            assert isinstance(config.logging, LoggingConfig)
        else:
            pytest.skip("Default config file not found (expected during RED phase)")

    def test_config_file_has_documented_defaults(self):
        """Test that config file has comments documenting defaults."""
        config_path = Path.cwd() / ".claude" / "loop" / "config.yaml"

        if config_path.exists():
            content = config_path.read_text()

            # Check for key documentation comments
            assert "# Minimum number of completion indicators before exit" in content or "# Minimum" in content
            assert "# Require explicit EXIT_SIGNAL in plan file" in content or "# Require" in content
            assert "# Verification skill to run" in content or "# Verification" in content
            assert "# Default plan file path" in content or "# Default" in content
        else:
            pytest.skip("Default config file not found (expected during RED phase)")
