"""Configuration schema for Ralph-style autonomous loops.

This module defines the configuration structure for loop-core, including exit policies,
verification settings, plan management, and logging configuration.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


class ConfigError(Exception):
    """Exception raised for configuration errors."""

    pass


@dataclass
class ExitPolicyConfig:
    """Configuration for loop exit policy.

    Attributes:
        min_completion_indicators: Minimum number of completion indicators before exit
        require_exit_signal: Require explicit EXIT_SIGNAL in plan file
        require_all_tasks_complete: Require all tasks to be marked complete
        require_verification_pass: Require verification pass to exit
    """

    min_completion_indicators: int
    require_exit_signal: bool
    require_all_tasks_complete: bool
    require_verification_pass: bool

    def __post_init__(self):
        """Validate exit policy configuration."""
        if not isinstance(self.min_completion_indicators, int):
            raise ConfigError(
                f"min_completion_indicators must be an integer, got {type(self.min_completion_indicators).__name__}"
            )
        if self.min_completion_indicators < 1:
            raise ConfigError(
                f"min_completion_indicators must be >= 1, got {self.min_completion_indicators}"
            )
        if not isinstance(self.require_exit_signal, bool):
            raise ConfigError(
                f"require_exit_signal must be a boolean, got {type(self.require_exit_signal).__name__}"
            )
        if not isinstance(self.require_all_tasks_complete, bool):
            raise ConfigError(
                f"require_all_tasks_complete must be a boolean, got {type(self.require_all_tasks_complete).__name__}"
            )
        if not isinstance(self.require_verification_pass, bool):
            raise ConfigError(
                f"require_verification_pass must be a boolean, got {type(self.require_verification_pass).__name__}"
            )


@dataclass
class VerificationConfig:
    """Configuration for verification behavior.

    Attributes:
        enabled: Whether verification is enabled
        skill: Name of the verification skill to use
        write_report: Path to write verification report
        fields: List of verification fields to include in report
    """

    enabled: bool
    skill: str
    write_report: str
    fields: list[str] | None = None

    def __post_init__(self):
        """Validate verification configuration."""
        if not isinstance(self.enabled, bool):
            raise ConfigError(
                f"enabled must be a boolean, got {type(self.enabled).__name__}"
            )
        if not isinstance(self.skill, str):
            raise ConfigError(
                f"skill must be a string, got {type(self.skill).__name__}"
            )
        if not self.skill or not self.skill.strip():
            raise ConfigError("skill cannot be empty")
        if not isinstance(self.write_report, str):
            raise ConfigError(
                f"write_report must be a string, got {type(self.write_report).__name__}"
            )
        # Set default fields if not provided
        if self.fields is None:
            self.fields = ["prd_coverage", "spec_compliance", "implementation_quality"]
        # Validate fields
        if not isinstance(self.fields, list):
            raise ConfigError(
                f"fields must be a list, got {type(self.fields).__name__}"
            )
        # Validate each field is a non-empty string
        for field in self.fields:
            if not isinstance(field, str):
                raise ConfigError(
                    f"field must be a string, got {type(field).__name__}"
                )
            if not field or not field.strip():
                raise ConfigError("field cannot be an empty string")


@dataclass
class PlansConfig:
    """Configuration for plan management.

    Attributes:
        default_plan: Default plan file path
        allow_per_terminal_plan: Allow each terminal to have its own plan
    """

    default_plan: str
    allow_per_terminal_plan: bool

    def __post_init__(self):
        """Validate plans configuration."""
        if not isinstance(self.default_plan, str):
            raise ConfigError(
                f"default_plan must be a string, got {type(self.default_plan).__name__}"
            )
        if not self.default_plan or not self.default_plan.strip():
            raise ConfigError("default_plan cannot be empty")
        if not isinstance(self.allow_per_terminal_plan, bool):
            raise ConfigError(
                f"allow_per_terminal_plan must be a boolean, got {type(self.allow_per_terminal_plan).__name__}"
            )


@dataclass
class LoggingConfig:
    """Configuration for logging.

    Attributes:
        decision_log: Path to decision log file
        verifier_log: Path to verifier log file
    """

    decision_log: str
    verifier_log: str

    def __post_init__(self):
        """Validate logging configuration."""
        if not isinstance(self.decision_log, str):
            raise ConfigError(
                f"decision_log must be a string, got {type(self.decision_log).__name__}"
            )
        if not self.decision_log or not self.decision_log.strip():
            raise ConfigError("decision_log cannot be empty")
        if not isinstance(self.verifier_log, str):
            raise ConfigError(
                f"verifier_log must be a string, got {type(self.verifier_log).__name__}"
            )
        if not self.verifier_log or not self.verifier_log.strip():
            raise ConfigError("verifier_log cannot be empty")


@dataclass
class ConfigSchema:
    """Complete configuration schema for loop-core.

    Attributes:
        version: Configuration version
        exit_policy: Exit policy configuration
        verification: Verification configuration
        plans: Plan management configuration
        logging: Logging configuration
    """

    version: int
    exit_policy: ExitPolicyConfig
    verification: VerificationConfig
    plans: PlansConfig
    logging: LoggingConfig

    def __post_init__(self):
        """Validate complete configuration."""
        if not isinstance(self.version, int):
            raise ConfigError(
                f"version must be an integer, got {type(self.version).__name__}"
            )
        if self.version < 1:
            raise ConfigError(f"version must be >= 1, got {self.version}")

        # Validate sub-configurations
        if not isinstance(self.exit_policy, ExitPolicyConfig):
            raise ConfigError(
                f"exit_policy must be ExitPolicyConfig, got {type(self.exit_policy).__name__}"
            )
        if not isinstance(self.verification, VerificationConfig):
            raise ConfigError(
                f"verification must be VerificationConfig, got {type(self.verification).__name__}"
            )
        if not isinstance(self.plans, PlansConfig):
            raise ConfigError(
                f"plans must be PlansConfig, got {type(self.plans).__name__}"
            )
        if not isinstance(self.logging, LoggingConfig):
            raise ConfigError(
                f"logging must be LoggingConfig, got {type(self.logging).__name__}"
            )

    @staticmethod
    def _validate_config_dict(config_dict: dict[str, Any]) -> None:
        """Validate that all required sections exist in config dict.

        Args:
            config_dict: Dictionary to validate

        Raises:
            ConfigError: If required sections are missing
        """
        required_sections = {
            "version",
            "exit_policy",
            "verification",
            "plans",
            "logging",
        }

        missing_sections = required_sections - set(config_dict.keys())
        if missing_sections:
            raise ConfigError(
                f"Missing required config sections: {', '.join(sorted(missing_sections))}"
            )

        # Validate exit_policy subsections
        exit_policy_required = {
            "min_completion_indicators",
            "require_exit_signal",
            "require_all_tasks_complete",
            "require_verification_pass",
        }
        exit_policy_keys = set(config_dict.get("exit_policy", {}).keys())
        missing_exit_policy = exit_policy_required - exit_policy_keys
        if missing_exit_policy:
            raise ConfigError(
                f"Missing required exit_policy fields: {', '.join(sorted(missing_exit_policy))}"
            )

        # Validate verification subsections
        verification_required = {"enabled", "skill", "write_report"}
        verification_keys = set(config_dict.get("verification", {}).keys())
        missing_verification = verification_required - verification_keys
        if missing_verification:
            raise ConfigError(
                f"Missing required verification fields: {', '.join(sorted(missing_verification))}"
            )

        # Validate plans subsections
        plans_required = {"default_plan", "allow_per_terminal_plan"}
        plans_keys = set(config_dict.get("plans", {}).keys())
        missing_plans = plans_required - plans_keys
        if missing_plans:
            raise ConfigError(
                f"Missing required plans fields: {', '.join(sorted(missing_plans))}"
            )

        # Validate logging subsections
        logging_required = {"decision_log", "verifier_log"}
        logging_keys = set(config_dict.get("logging", {}).keys())
        missing_logging = logging_required - logging_keys
        if missing_logging:
            raise ConfigError(
                f"Missing required logging fields: {', '.join(sorted(missing_logging))}"
            )

    @classmethod
    def from_dict(cls, config_dict: dict[str, Any]) -> "ConfigSchema":
        """Create ConfigSchema from dictionary.

        Args:
            config_dict: Dictionary containing configuration

        Returns:
            ConfigSchema instance

        Raises:
            ConfigError: If configuration is invalid
        """
        cls._validate_config_dict(config_dict)

        try:
            exit_policy = ExitPolicyConfig(**config_dict["exit_policy"])
            verification = VerificationConfig(**config_dict["verification"])
            plans = PlansConfig(**config_dict["plans"])
            logging_config = LoggingConfig(**config_dict["logging"])

            return cls(
                version=config_dict["version"],
                exit_policy=exit_policy,
                verification=verification,
                plans=plans,
                logging=logging_config,
            )
        except TypeError as e:
            raise ConfigError(f"Invalid configuration structure: {e}") from e
        except ConfigError:
            raise
        except Exception as e:
            raise ConfigError(f"Failed to create configuration: {e}") from e

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary.

        Returns:
            Dictionary representation of configuration
        """
        return {
            "version": self.version,
            "exit_policy": {
                "min_completion_indicators": self.exit_policy.min_completion_indicators,
                "require_exit_signal": self.exit_policy.require_exit_signal,
                "require_all_tasks_complete": self.exit_policy.require_all_tasks_complete,
                "require_verification_pass": self.exit_policy.require_verification_pass,
            },
            "verification": {
                "enabled": self.verification.enabled,
                "skill": self.verification.skill,
                "write_report": self.verification.write_report,
                "fields": self.verification.fields,
            },
            "plans": {
                "default_plan": self.plans.default_plan,
                "allow_per_terminal_plan": self.plans.allow_per_terminal_plan,
            },
            "logging": {
                "decision_log": self.logging.decision_log,
                "verifier_log": self.logging.verifier_log,
            },
        }

    @classmethod
    def load_from_file(cls, config_path: Path | str) -> "ConfigSchema":
        """Load configuration from YAML file.

        Args:
            config_path: Path to configuration file

        Returns:
            ConfigSchema instance

        Raises:
            ConfigError: If file cannot be read or parsed
        """
        config_path = Path(config_path)

        if not config_path.exists():
            raise ConfigError(f"Config file not found: {config_path}")

        try:
            content = config_path.read_text()
            config_dict = yaml.safe_load(content)
        except yaml.YAMLError as e:
            raise ConfigError(f"Failed to parse config file {config_path}: {e}") from e
        except Exception as e:
            raise ConfigError(f"Failed to read config file {config_path}: {e}") from e

        if not isinstance(config_dict, dict):
            raise ConfigError(
                f"Config file must contain a dictionary, got {type(config_dict).__name__}"
            )

        return cls.from_dict(config_dict)

    @classmethod
    def get_default(cls) -> "ConfigSchema":
        """Get default configuration.

        Returns:
            ConfigSchema instance with default values
        """
        return cls(
            version=1,
            exit_policy=ExitPolicyConfig(
                min_completion_indicators=2,
                require_exit_signal=True,
                require_all_tasks_complete=True,
                require_verification_pass=True,
            ),
            verification=VerificationConfig(
                enabled=True,
                skill="prd-verifier",
                write_report=".claude/loop/verification-report.md",
            ),
            plans=PlansConfig(
                default_plan="plan.md",
                allow_per_terminal_plan=True,
            ),
            logging=LoggingConfig(
                decision_log="decision.log",
                verifier_log="verifier.log",
            ),
        )
