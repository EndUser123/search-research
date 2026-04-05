"""Configuration loader for cognitive & reasoning systems.

Loads and validates the unified cognitive_reasoning_config.json file.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Config file path
CONFIG_PATH = Path(__file__).resolve().parent.parent / "cognitive_reasoning_config.json"


@dataclass(frozen=True)
class CognitiveFrameworkConfig:
    """Configuration for a single cognitive framework."""
    enabled: bool
    patterns: list[str]
    intent: str
    confidence_min: int


@dataclass(frozen=True)
class ReasoningModeConfig:
    """Configuration for a single reasoning mode."""
    enabled: bool
    patterns: list[str]
    confidence_min: float


@dataclass(frozen=True)
class ThinkProfileConfig:
    """Configuration for a single think profile."""
    enabled: bool
    strong_patterns: list[str]
    weak_patterns: list[str]
    weak_count: int


@dataclass(frozen=True)
class CognitiveReasoningConfig:
    """Unified configuration for all cognitive & reasoning systems.

    Attributes:
        enabled: Master enable/disable toggle
        cognitive_frameworks: Settings for 9 cognitive frameworks
        reasoning_modes: Settings for 4 reasoning modes
        think_profiles: Settings for 7 think profiles
        synergy_detection: Framework+mode synergy combinations
        questioning_patterns: Integration with questioning_patterns.md
        performance: Performance thresholds
        user_modes: User mode overrides (#rca, #fast, #deep)
        skills: Skill enhancement settings
    """
    enabled: bool
    cognitive_frameworks: dict[str, Any]
    reasoning_modes: dict[str, Any]
    think_profiles: dict[str, Any]
    synergy_detection: dict[str, Any]
    questioning_patterns: dict[str, Any]
    performance: dict[str, Any]
    user_modes: dict[str, Any]
    skills: dict[str, Any]

    @classmethod
    def load(cls) -> CognitiveReasoningConfig:
        """Load configuration from JSON file.

        Returns:
            CognitiveReasoningConfig instance

        Raises:
            FileNotFoundError: If config file doesn't exist
            json.JSONDecodeError: If config file is invalid JSON
            ValueError: If config validation fails
        """
        if not CONFIG_PATH.exists():
            raise FileNotFoundError(f"Configuration file not found: {CONFIG_PATH}")

        with open(CONFIG_PATH, encoding="utf-8") as f:
            data = json.load(f)

        # Validate required top-level sections
        required_sections = [
            "cognitive_frameworks",
            "reasoning_modes",
            "think_profiles",
            "synergy_detection",
            "questioning_patterns",
            "performance",
        ]
        for section in required_sections:
            if section not in data:
                raise ValueError(f"Missing required config section: {section}")

        # Validate enabled flag
        if not isinstance(data.get("enabled", True), bool):
            raise ValueError("Config 'enabled' must be boolean")

        return cls(**{
            "enabled": data.get("enabled", True),
            "cognitive_frameworks": data["cognitive_frameworks"],
            "reasoning_modes": data["reasoning_modes"],
            "think_profiles": data["think_profiles"],
            "synergy_detection": data["synergy_detection"],
            "questioning_patterns": data["questioning_patterns"],
            "performance": data["performance"],
            "user_modes": data.get("user_modes", {}),
            "skills": data.get("skills", {}),
        })

    def get_framework_config(self, framework_name: str) -> CognitiveFrameworkConfig | None:
        """Get configuration for a specific cognitive framework.

        Args:
            framework_name: Name of the framework (e.g., "assumption_surfacing")

        Returns:
            CognitiveFrameworkConfig or None if framework not found/disabled
        """
        frameworks = self.cognitive_frameworks.get("frameworks", {})
        if framework_name not in frameworks:
            return None

        fw_data = frameworks[framework_name]
        if not fw_data.get("enabled", True):
            return None

        return CognitiveFrameworkConfig(
            enabled=fw_data["enabled"],
            patterns=fw_data["patterns"],
            intent=fw_data["intent"],
            confidence_min=fw_data.get("confidence_min", 1),
        )

    def get_mode_config(self, mode_name: str) -> ReasoningModeConfig | None:
        """Get configuration for a specific reasoning mode.

        Args:
            mode_name: Name of the mode (e.g., "sequential")

        Returns:
            ReasoningModeConfig or None if mode not found/disabled
        """
        modes = self.reasoning_modes.get("modes", {})
        if mode_name not in modes:
            return None

        mode_data = modes[mode_name]
        if not mode_data.get("enabled", True):
            return None

        return ReasoningModeConfig(
            enabled=mode_data["enabled"],
            patterns=mode_data["patterns"],
            confidence_min=mode_data.get("confidence_min", 0.5),
        )

    def get_profile_config(self, profile_name: str) -> ThinkProfileConfig | None:
        """Get configuration for a specific think profile.

        Args:
            profile_name: Name of the profile (e.g., "debug_rca")

        Returns:
            ThinkProfileConfig or None if profile not found/disabled
        """
        profiles = self.think_profiles.get("profiles", {})
        if profile_name not in profiles:
            return None

        profile_data = profiles[profile_name]
        if not profile_data.get("enabled", True):
            return None

        return ThinkProfileConfig(
            enabled=profile_data["enabled"],
            strong_patterns=profile_data["strong_patterns"],
            weak_patterns=profile_data["weak_patterns"],
            weak_count=profile_data.get("weak_count", 2),
        )

    def get_synergy_score(self, framework: str, mode: str) -> float:
        """Get synergy score for a framework+mode combination.

        Args:
            framework: Framework name (e.g., "assumption_surfacing")
            mode: Mode name (e.g., "sequential")

        Returns:
            Synergy score 0.0-1.0, or 0.0 if combination not defined
        """
        matrix = self.synergy_detection.get("synergy_matrix", {})
        if framework not in matrix:
            return 0.0

        return matrix[framework].get(mode, 0.0)

    def is_questioning_enabled(self) -> bool:
        """Check if questioning patterns integration is enabled.

        Returns:
            True if questioning patterns are enabled
        """
        return self.questioning_patterns.get("enabled", False)


# Module-level cache for loaded config
_loaded_config: CognitiveReasoningConfig | None = None


def load_config(reload: bool = False) -> CognitiveReasoningConfig:
    """Load configuration (with caching).

    Args:
        reload: Force reload from disk even if already loaded

    Returns:
        CognitiveReasoningConfig instance

    Raises:
        FileNotFoundError: If config file doesn't exist
        json.JSONDecodeError: If config file is invalid JSON
        ValueError: If config validation fails
    """
    global _loaded_config

    if _loaded_config is None or reload:
        _loaded_config = CognitiveReasoningConfig.load()

    return _loaded_config


def get_config() -> CognitiveReasoningConfig:
    """Get cached configuration (loads if not already loaded).

    Returns:
        CognitiveReasoningConfig instance

    Raises:
        FileNotFoundError: If config file doesn't exist
        json.JSONDecodeError: If config file is invalid JSON
        ValueError: If config validation fails
    """
    global _loaded_config

    if _loaded_config is None:
        return load_config()

    return _loaded_config
