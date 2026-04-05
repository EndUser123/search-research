#!/usr/bin/env python3
"""
Unit tests for tdd/enforcement_tiers.py

Tests TDD phase-specific enforcement tier configuration:
- RED/GREEN phases: enforce (block on violation)
- REFACTOR phase: warn (advisory only)
- COMPLETE phase: none (no enforcement)

ADR: P:/.claude/arch_decisions/ADR-20260324-clean-room-tdd-loop.md
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add hooks directory to path
hooks_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(hooks_dir))


def test_default_tier_red_is_enforce():
    """Test that RED phase defaults to enforce."""
    from tdd.enforcement_tiers import EnforcementTier, get_enforcement_tier

    tier = get_enforcement_tier("red")
    assert tier == EnforcementTier.ENFORCE, "RED phase should default to enforce"


def test_default_tier_green_is_enforce():
    """Test that GREEN phase defaults to enforce."""
    from tdd.enforcement_tiers import EnforcementTier, get_enforcement_tier

    tier = get_enforcement_tier("green")
    assert tier == EnforcementTier.ENFORCE, "GREEN phase should default to enforce"


def test_default_tier_refactor_is_warn():
    """Test that REFACTOR phase defaults to warn."""
    from tdd.enforcement_tiers import EnforcementTier, get_enforcement_tier

    tier = get_enforcement_tier("refactor")
    assert tier == EnforcementTier.WARN, "REFACTOR phase should default to warn"


def test_default_tier_complete_is_none():
    """Test that COMPLETE phase defaults to none."""
    from tdd.enforcement_tiers import EnforcementTier, get_enforcement_tier

    tier = get_enforcement_tier("complete")
    assert tier == EnforcementTier.NONE, "COMPLETE phase should default to none"


def test_unknown_phase_defaults_to_none():
    """Test that unknown phases default to none."""
    from tdd.enforcement_tiers import EnforcementTier, get_enforcement_tier

    tier = get_enforcement_tier("unknown_phase")
    assert tier == EnforcementTier.NONE, "Unknown phase should default to none"


def test_case_insensitive_phase_lookup():
    """Test that phase lookup is case-insensitive."""
    from tdd.enforcement_tiers import EnforcementTier, EnforcementTierManager

    manager = EnforcementTierManager()

    assert manager.get_tier("RED") == EnforcementTier.ENFORCE
    assert manager.get_tier("Red") == EnforcementTier.ENFORCE
    assert manager.get_tier("REFACTOR") == EnforcementTier.WARN
    assert manager.get_tier("Refactor") == EnforcementTier.WARN


def test_should_block_for_enforce_tier():
    """Test should_block returns True only for enforce tier."""
    from tdd.enforcement_tiers import EnforcementTierManager

    manager = EnforcementTierManager()

    assert manager.should_block("red") is True
    assert manager.should_block("green") is True
    assert manager.should_block("refactor") is False
    assert manager.should_block("complete") is False


def test_should_warn_for_warn_tier():
    """Test should_warn returns True only for warn tier."""
    from tdd.enforcement_tiers import EnforcementTierManager

    manager = EnforcementTierManager()

    assert manager.should_warn("red") is False
    assert manager.should_warn("green") is False
    assert manager.should_warn("refactor") is True
    assert manager.should_warn("complete") is False


def test_get_config_returns_tier_config():
    """Test get_config returns TierConfig with all fields."""
    from tdd.enforcement_tiers import EnforcementTier, EnforcementTierManager

    manager = EnforcementTierManager()
    config = manager.get_config("red")

    assert config.phase == "red"
    assert config.tier == EnforcementTier.ENFORCE
    assert len(config.rationale) > 0


def test_get_all_tiers():
    """Test get_all_tiers returns all tier configurations."""
    from tdd.enforcement_tiers import EnforcementTierManager

    manager = EnforcementTierManager()
    all_tiers = manager.get_all_tiers()

    assert "red" in all_tiers
    assert "green" in all_tiers
    assert "refactor" in all_tiers
    assert "complete" in all_tiers
    assert "none" in all_tiers


def test_handles_missing_settings_file():
    """Test missing settings.json uses defaults."""
    from tdd.enforcement_tiers import EnforcementTier, EnforcementTierManager

    manager = EnforcementTierManager(config_path=Path("/nonexistent/settings.json"))

    assert manager.get_tier("red") == EnforcementTier.ENFORCE
    assert manager.get_tier("refactor") == EnforcementTier.WARN


def test_should_enforce_convenience_function():
    """Test should_enforce convenience function."""
    from tdd.enforcement_tiers import should_enforce

    assert should_enforce("red") is True
    assert should_enforce("green") is True
    assert should_enforce("refactor") is False
    assert should_enforce("complete") is False


def test_phase_enum_handling():
    """Test handling of enum-like objects with value attribute."""
    from tdd.enforcement_tiers import EnforcementTier, get_enforcement_tier

    # Mock enum-like object
    class MockPhase:
        def __init__(self, value):
            self.value = value

    phase = MockPhase("RED")
    tier = get_enforcement_tier(phase)
    assert tier == EnforcementTier.ENFORCE


def main():
    """Run all tests."""
    import pytest

    exit_code = pytest.main([__file__, "-v"])
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
