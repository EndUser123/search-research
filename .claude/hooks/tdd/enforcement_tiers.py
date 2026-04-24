"""
Enforcement Tier Configuration for Clean-Room TDD Loop v2.

Provides constitutional enforcement tiers per TDD phase:
- RED: enforce (must write failing tests)
- GREEN: enforce (must write minimal implementation)
- REFACTOR: warn (optional improvement phase)
- COMPLETE: none (no enforcement needed)

ADR: P:/docs/adrs/ADR-20260324-clean-room-tdd-loop.md
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any


class EnforcementTier(Enum):
    """Enforcement tier levels for TDD phases."""

    ENFORCE = "enforce"  # Block on violation
    WARN = "warn"  # Advisory warning only
    NONE = "none"  # No enforcement


@dataclass(frozen=True)
class TierConfig:
    """Configuration for a single phase's enforcement tier."""

    phase: str
    tier: EnforcementTier
    rationale: str


# Default tier configuration per ADR
DEFAULT_TIERS: dict[str, EnforcementTier] = {
    "red": EnforcementTier.ENFORCE,
    "green": EnforcementTier.ENFORCE,
    "refactor": EnforcementTier.WARN,
    "complete": EnforcementTier.NONE,
    "none": EnforcementTier.NONE,
}

TIER_RATIONALES: dict[str, str] = {
    "red": "Must write failing tests before implementation",
    "green": "Must write minimal implementation",
    "refactor": "Optional improvement phase",
    "complete": "No enforcement needed",
    "none": "No active TDD cycle",
}


class EnforcementTierManager:
    """Manages enforcement tier configuration for TDD phases."""

    def __init__(
        self,
        config_path: Path | None = None,
        override_tiers: dict[str, str] | None = None,
    ):
        """Initialize enforcement tier manager.

        Args:
            config_path: Optional path to settings.json for custom tiers
            override_tiers: Optional dict to override default tiers
        """
        self._config_path = config_path
        self._tiers = self._load_tiers(override_tiers)

    def _load_tiers(self, override: dict[str, str] | None = None) -> dict[str, EnforcementTier]:
        """Load tier configuration from settings or use defaults.

        Args:
            override: Optional override dict

        Returns:
            Dict mapping phase names to EnforcementTier
        """
        tiers = dict(DEFAULT_TIERS)

        # Load from settings.json if available
        if self._config_path and self._config_path.exists():
            try:
                with open(self._config_path, encoding="utf-8") as f:
                    settings = json.load(f)
                custom_tiers = settings.get("tdd95_enforcement_tiers", {})
                for phase, tier_str in custom_tiers.items():
                    if tier_str in ("enforce", "warn", "none"):
                        tiers[phase.lower()] = EnforcementTier(tier_str)
            except (json.JSONDecodeError, OSError):
                pass  # Use defaults on error

        # Apply overrides
        if override:
            for phase, tier_str in override.items():
                if tier_str in ("enforce", "warn", "none"):
                    tiers[phase.lower()] = EnforcementTier(tier_str)

        return tiers

    def get_tier(self, phase: str | Any) -> EnforcementTier:
        """Get enforcement tier for a phase.

        Args:
            phase: Phase name (string or TDDPhaseState enum)

        Returns:
            EnforcementTier for the phase
        """
        # Handle enum or string
        phase_name = phase.value if hasattr(phase, "value") else str(phase)
        phase_name = phase_name.lower()

        return self._tiers.get(phase_name, EnforcementTier.NONE)

    def get_config(self, phase: str | Any) -> TierConfig:
        """Get full tier configuration for a phase.

        Args:
            phase: Phase name (string or TDDPhaseState enum)

        Returns:
            TierConfig with phase, tier, and rationale
        """
        phase_name = phase.value if hasattr(phase, "value") else str(phase)
        phase_name = phase_name.lower()

        tier = self.get_tier(phase_name)
        rationale = TIER_RATIONALES.get(phase_name, "Unknown phase")

        return TierConfig(phase=phase_name, tier=tier, rationale=rationale)

    def should_block(self, phase: str | Any) -> bool:
        """Check if violations should block for a phase.

        Args:
            phase: Phase name (string or TDDPhaseState enum)

        Returns:
            True if violations should block, False otherwise
        """
        return self.get_tier(phase) == EnforcementTier.ENFORCE

    def should_warn(self, phase: str | Any) -> bool:
        """Check if violations should warn for a phase.

        Args:
            phase: Phase name (string or TDDPhaseState enum)

        Returns:
            True if violations should warn, False otherwise
        """
        return self.get_tier(phase) == EnforcementTier.WARN

    def get_all_tiers(self) -> dict[str, EnforcementTier]:
        """Get all tier configurations.

        Returns:
            Dict mapping all phase names to their tiers
        """
        return dict(self._tiers)


def get_enforcement_tier(phase: str | Any) -> EnforcementTier:
    """Convenience function to get enforcement tier for a phase.

    Uses default configuration. For custom configuration, create
    an EnforcementTierManager instance.

    Args:
        phase: Phase name (string or TDDPhaseState enum)

    Returns:
        EnforcementTier for the phase
    """
    manager = EnforcementTierManager()
    return manager.get_tier(phase)


def should_enforce(phase: str | Any) -> bool:
    """Convenience function to check if phase requires enforcement.

    Args:
        phase: Phase name (string or TDDPhaseState enum)

    Returns:
        True if violations should block
    """
    return get_enforcement_tier(phase) == EnforcementTier.ENFORCE
