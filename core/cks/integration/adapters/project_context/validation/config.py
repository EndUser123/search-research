"""Validation configuration for project context operations.

Provides configuration for blocking vs warning mode.

Constitutional Requirements:
- Solo developer optimization (simple configuration)
- Evidence-based implementation (user has full control)
- Force multiplier (prevents accidental cross-project operations)
- No enterprise bloat (direct Python, no complex frameworks)
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ValidationConfig:
    """Configuration for validation behavior."""

    # Whether to block mismatched operations (True) or just warn (False)
    blocking_mode: bool = False

    # Whether to auto-detect context from current directory
    auto_detect_context: bool = True

    # Whether to require explicit confirmation when bypassing validation
    require_confirmation: bool = False

    @classmethod
    def from_env(cls) -> ValidationConfig:
        """Load configuration from environment variables."""
        return cls(
            blocking_mode=os.getenv("CKS_BLOCKING_MODE", "false").lower() == "true",
            auto_detect_context=os.getenv("CKS_AUTO_DETECT_CONTEXT", "true").lower() == "true",
            require_confirmation=os.getenv("CKS_REQUIRE_CONFIRMATION", "false").lower() == "true",
        )

    @classmethod
    def from_file(cls, config_path: Path | None = None) -> ValidationConfig:
        """Load configuration from JSON file."""
        if config_path is None:
            config_path = Path.home() / ".cks" / "validation_config.json"

        if not config_path.exists():
            return cls.from_env()

        import json

        with open(config_path) as f:
            data = json.load(f)

        return cls(
            blocking_mode=data.get("blocking_mode", False),
            auto_detect_context=data.get("auto_detect_context", True),
            require_confirmation=data.get("require_confirmation", False),
        )

    def to_file(self, config_path: Path | None = None) -> None:
        """Save configuration to JSON file."""
        if config_path is None:
            config_path = Path.home() / ".cks" / "validation_config.json"

        config_path.parent.mkdir(parents=True, exist_ok=True)

        import json

        with open(config_path, "w") as f:
            json.dump(
                {
                    "blocking_mode": self.blocking_mode,
                    "auto_detect_context": self.auto_detect_context,
                    "require_confirmation": self.require_confirmation,
                },
                f,
                indent=2,
            )


# Global configuration instance
_global_config: ValidationConfig | None = None


def get_config() -> ValidationConfig:
    """Get global validation configuration."""
    global _global_config
    if _global_config is None:
        _global_config = ValidationConfig.from_env()
    return _global_config


def set_config(config: ValidationConfig) -> None:
    """Set global validation configuration."""
    global _global_config
    _global_config = config
