"""Tests for conflict_arbiter.py - Extended with new precedence rules.

Tests cover:
- Original 3 rules (fast mode, high-confidence, token budget)
- New Rule 4: Synergy gating
- New Rule 5: Questioning gating
- New Rule 6: Performance gating
"""

from __future__ import annotations

# Import the module under test
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "UserPromptSubmit_modules"))
from conflict_arbiter import (
    ArbiterResult,
    resolve_conflict,
)


# Mock Enhancer class (since we can't import the real one in tests)
@dataclass(frozen=True)
class MockEnhancer:
    """Mock cognitive enhancer for testing."""

    name: str
    intent: str = "implementation"
    confidence: int = 1
    rationale: str = ""
    tag: str = ""
    injection: str = ""

    def __getattr__(self, name: str) -> Any:
        # Provide default values for any missing attributes
        return None


class TestOriginalRules:
    """Test the original 3 precedence rules."""

    def test_fast_mode_caps_enhancers(self):
        """Test Rule 1: Fast mode limits to lightweight enhancers."""
        enhancers = [
            MockEnhancer(name="assumption_surfacing", tag="cognitive"),
            MockEnhancer(name="outcome_anchoring", tag="cognitive"),
            MockEnhancer(name="inversion_prompting", tag="cognitive"),
            MockEnhancer(name="chestertons_fence", tag="cognitive"),
        ]

        result = resolve_conflict(
            enhancers=enhancers,
            mode_selection="sequential",
            reasoning_confidence=2,
            prompt_mode="fast",
        )

        # Should only keep lightweight enhancers (assumption_surfacing, outcome_anchoring)
        assert len(result.enhancers) == 2
        assert result.enhancers[0].name == "assumption_surfacing"
        assert result.enhancers[1].name == "outcome_anchoring"
        assert "Fast mode" in result.rationale

    def test_high_confidence_override(self):
        """Test Rule 2: High-confidence reasoning overrides cognitive."""
        enhancers = [
            MockEnhancer(name="assumption_surfacing", tag="cognitive"),
            MockEnhancer(name="outcome_anchoring", tag="cognitive"),
            MockEnhancer(name="inversion_prompting", tag="cognitive"),
            MockEnhancer(name="chestertons_fence", tag="cognitive"),
        ]

        result = resolve_conflict(
            enhancers=enhancers,
            mode_selection="sequential",
            reasoning_confidence=3,  # High confidence
            prompt_mode=None,
        )

        # Should reduce to 1-2 enhancers
        assert len(result.enhancers) == 2
        assert "High-confidence reasoning mode" in result.rationale
        assert "confidence=3" in result.rationale

    def test_token_budget_cap(self):
        """Test Rule 3: Token budget limits total injection."""
        enhancers = [
            MockEnhancer(name=f"framework_{i}", tag="cognitive") for i in range(10)
        ]

        result = resolve_conflict(
            enhancers=enhancers,
            mode_selection="sequential",
            reasoning_confidence=2,
            prompt_mode=None,
            token_limit=300,  # Low limit
        )

        # Should reduce enhancers to fit budget
        # Budget: 300 - 50 (mode) = 250, / 100 = 2.5 -> 2 enhancers
        assert len(result.enhancers) <= 2
        assert "Token budget cap" in result.rationale
        assert result.token_budget_applied is True


class TestSynergyGating:
    """Test Rule 4: Synergy gating between frameworks and modes."""

    def test_valid_synergy_combination(self):
        """Test that valid framework+mode combinations are allowed."""
        enhancers = [
            MockEnhancer(name="assumption_surfacing", tag="cognitive"),
        ]

        result = resolve_conflict(
            enhancers=enhancers,
            mode_selection="sequential",  # Valid combo with assumption_surfacing
            reasoning_confidence=2,
            prompt_mode=None,
            synergy_combinations=[
                ("assumption_surfacing", "sequential"),
                ("socratic_decomposition", "multi_agent"),
            ],
        )

        # Should keep the enhancer (valid combination)
        assert len(result.enhancers) == 1
        assert result.synergy_gate_applied is False
        assert "No conflicts detected" in result.rationale or len(result.rationale) == 0

    def test_invalid_synergy_combination_removed(self):
        """Test that invalid framework+mode combinations are blocked."""
        enhancers = [
            MockEnhancer(name="socratic_decomposition", tag="cognitive"),
            MockEnhancer(name="outcome_anchoring", tag="cognitive"),
        ]

        result = resolve_conflict(
            enhancers=enhancers,
            mode_selection="sequential",  # Poor synergy with socratic_decomposition
            reasoning_confidence=2,
            prompt_mode=None,
            synergy_combinations=[
                ("assumption_surfacing", "sequential"),
                ("socratic_decomposition", "multi_agent"),  # Not sequential
                ("outcome_anchoring", "two_stage"),  # Not sequential
            ],
        )

        # Should remove both enhancers (both have poor synergy with sequential)
        assert len(result.enhancers) == 0
        assert result.mode_selection is None  # Mode also cleared
        assert result.synergy_gate_applied is True
        assert "Synergy gating" in result.rationale

    def test_partial_synergy_filtering(self):
        """Test that only incompatible enhancers are removed."""
        enhancers = [
            MockEnhancer(name="assumption_surfacing", tag="cognitive"),
            MockEnhancer(name="socratic_decomposition", tag="cognitive"),
        ]

        result = resolve_conflict(
            enhancers=enhancers,
            mode_selection="sequential",
            reasoning_confidence=2,
            prompt_mode=None,
            synergy_combinations=[
                ("assumption_surfacing", "sequential"),  # Valid
                ("socratic_decomposition", "multi_agent"),  # Invalid with sequential
            ],
        )

        # Should keep only assumption_surfacing
        assert len(result.enhancers) == 1
        assert result.enhancers[0].name == "assumption_surfacing"
        assert result.synergy_gate_applied is True
        assert "poor mode synergy" in result.rationale.lower()

    def test_default_synergy_combinations(self):
        """Test that default synergy combinations work."""
        enhancers = [
            MockEnhancer(name="inversion_prompting", tag="cognitive"),
        ]

        result = resolve_conflict(
            enhancers=enhancers,
            mode_selection="graph",  # High synergy with inversion_prompting
            reasoning_confidence=2,
            prompt_mode=None,
        )

        # Should keep the enhancer (valid default combination)
        assert len(result.enhancers) == 1
        assert result.synergy_gate_applied is False


class TestQuestioningGating:
    """Test Rule 5: Questioning pattern gating."""

    def test_questioning_pattern_without_investigation(self):
        """Test that questioning patterns trigger gating without investigation."""
        enhancers = [
            MockEnhancer(name="assumption_surfacing", tag="cognitive"),
            MockEnhancer(name="outcome_anchoring", tag="cognitive"),
        ]

        result = resolve_conflict(
            enhancers=enhancers,
            mode_selection="sequential",
            reasoning_confidence=2,
            prompt_mode=None,
            user_message="Why this specific value? We should use 100ms threshold.",
            questioning_patterns=["Why this specific value"],
        )

        # Should reduce cognitive load
        assert len(result.enhancers) == 1
        assert result.questioning_gate_applied is True
        assert "Questioning gating" in result.rationale
        assert "without investigation" in result.rationale

    def test_questioning_pattern_with_investigation(self):
        """Test that investigation prevents questioning gating."""
        enhancers = [
            MockEnhancer(name="assumption_surfacing", tag="cognitive"),
            MockEnhancer(name="outcome_anchoring", tag="cognitive"),
        ]

        result = resolve_conflict(
            enhancers=enhancers,
            mode_selection="sequential",
            reasoning_confidence=2,
            prompt_mode=None,
            user_message="Why this specific value? Let me investigate the codebase.",
            questioning_patterns=["Why this specific value"],
        )

        # Should not reduce (has investigation)
        assert len(result.enhancers) == 2
        assert result.questioning_gate_applied is False

    def test_multiple_questioning_patterns(self):
        """Test that multiple questioning patterns are detected."""
        enhancers = [
            MockEnhancer(name="assumption_surfacing", tag="cognitive"),
            MockEnhancer(name="socratic_decomposition", tag="cognitive"),
        ]

        result = resolve_conflict(
            enhancers=enhancers,
            mode_selection="multi_agent",
            reasoning_confidence=2,
            prompt_mode=None,
            user_message="Are you sure about concurrency? Is this necessary?",
            questioning_patterns=[
                "Are you sure about concurrency",
                "Is this necessary",
            ],
        )

        # Should reduce cognitive load
        assert len(result.enhancers) == 1
        assert result.questioning_gate_applied is True

    def test_no_questioning_pattern(self):
        """Test that normal messages don't trigger questioning gating."""
        enhancers = [
            MockEnhancer(name="assumption_surfacing", tag="cognitive"),
        ]

        result = resolve_conflict(
            enhancers=enhancers,
            mode_selection="sequential",
            reasoning_confidence=2,
            prompt_mode=None,
            user_message="Implement the new feature for user authentication.",
            questioning_patterns=["Why this specific value"],
        )

        # Should not reduce
        assert len(result.enhancers) == 1
        assert result.questioning_gate_applied is False

    def test_default_questioning_patterns(self):
        """Test that default questioning patterns work."""
        enhancers = [
            MockEnhancer(name="outcome_anchoring", tag="cognitive"),
        ]

        result = resolve_conflict(
            enhancers=enhancers,
            mode_selection="two_stage",
            reasoning_confidence=2,
            prompt_mode=None,
            user_message="What happens at scale? We should set timeout to 5000ms.",
        )

        # Should trigger with default pattern
        assert result.questioning_gate_applied is True


class TestPerformanceGating:
    """Test Rule 6: Performance gating."""

    def test_performance_within_threshold(self):
        """Test that acceptable performance doesn't trigger gating."""
        enhancers = [
            MockEnhancer(name="assumption_surfacing", tag="cognitive"),
            MockEnhancer(name="outcome_anchoring", tag="cognitive"),
        ]

        result = resolve_conflict(
            enhancers=enhancers,
            mode_selection="sequential",
            reasoning_confidence=2,
            prompt_mode=None,
            timing_ms=45.0,  # Within 60ms threshold
            max_detection_ms=60.0,
        )

        # Should not block
        assert len(result.enhancers) == 2
        assert result.mode_selection == "sequential"
        assert result.performance_gate_applied is False

    def test_performance_exceeds_threshold(self):
        """Test that slow detection triggers performance gating."""
        enhancers = [
            MockEnhancer(name="assumption_surfacing", tag="cognitive"),
            MockEnhancer(name="outcome_anchoring", tag="cognitive"),
        ]

        result = resolve_conflict(
            enhancers=enhancers,
            mode_selection="sequential",
            reasoning_confidence=2,
            prompt_mode=None,
            timing_ms=85.0,  # Exceeds 60ms threshold
            max_detection_ms=60.0,
        )

        # Should disable both systems
        assert len(result.enhancers) == 0
        assert result.mode_selection is None
        assert result.performance_gate_applied is True
        assert "Performance gating" in result.rationale
        assert "85.0ms" in result.rationale
        assert "systems disabled" in result.rationale.lower()

    def test_performance_gating_with_other_rules(self):
        """Test that performance gating overrides other rules."""
        enhancers = [
            MockEnhancer(name="assumption_surfacing", tag="cognitive"),
            MockEnhancer(name="socratic_decomposition", tag="cognitive"),
        ]

        result = resolve_conflict(
            enhancers=enhancers,
            mode_selection="sequential",
            reasoning_confidence=3,
            prompt_mode="fast",
            timing_ms=100.0,  # Very slow
            max_detection_ms=60.0,
        )

        # Performance gating should override everything
        assert len(result.enhancers) == 0
        assert result.mode_selection is None
        assert result.performance_gate_applied is True


class TestRuleInteractions:
    """Test interactions between multiple rules."""

    def test_fast_mode_and_synergy_gating(self):
        """Test interaction between fast mode and synergy gating."""
        enhancers = [
            MockEnhancer(name="assumption_surfacing", tag="cognitive"),
            MockEnhancer(name="socratic_decomposition", tag="cognitive"),
            MockEnhancer(name="chestertons_fence", tag="cognitive"),
        ]

        result = resolve_conflict(
            enhancers=enhancers,
            mode_selection="sequential",
            reasoning_confidence=2,
            prompt_mode="fast",
            synergy_combinations=[
                ("assumption_surfacing", "sequential"),
                ("chestertons_fence", "sequential"),
            ],
        )

        # Fast mode reduces to lightweight, then synergy filters further
        # Fast mode keeps: assumption_surfacing, outcome_anchoring (lightweight)
        # But outcome_anchoring not in list, so only assumption_surfacing
        # chestertons_fence removed by fast mode (not lightweight)
        assert len(result.enhancers) <= 2
        assert result.synergy_gate_applied is True or "Fast mode" in result.rationale

    def test_all_rules_combined(self):
        """Test all rules working together."""
        enhancers = [
            MockEnhancer(name="assumption_surfacing", tag="cognitive"),
            MockEnhancer(name="outcome_anchoring", tag="cognitive"),
            MockEnhancer(name="socratic_decomposition", tag="cognitive"),
        ]

        result = resolve_conflict(
            enhancers=enhancers,
            mode_selection="sequential",
            reasoning_confidence=3,
            prompt_mode="fast",
            token_limit=150,
            synergy_combinations=[
                ("assumption_surfacing", "sequential"),
            ],
            user_message="Why this specific value?",
            questioning_patterns=["Why this specific value"],
        )

        # Multiple rules should apply
        assert len(result.rationale.split(" | ")) >= 2  # At least 2 rules triggered
        assert result.synergy_gate_applied or "Fast mode" in result.rationale

    def test_performance_overrides_all(self):
        """Test that performance gating overrides all other rules."""
        enhancers = [
            MockEnhancer(name="assumption_surfacing", tag="cognitive"),
        ]

        result = resolve_conflict(
            enhancers=enhancers,
            mode_selection="sequential",
            reasoning_confidence=4,
            prompt_mode=None,
            token_limit=1000,
            synergy_combinations=[("assumption_surfacing", "sequential")],
            user_message="Normal message",
            timing_ms=200.0,  # Very slow
            max_detection_ms=60.0,
        )

        # Performance gating should override everything
        assert len(result.enhancers) == 0
        assert result.mode_selection is None
        assert result.performance_gate_applied is True


class TestArbiterResult:
    """Test ArbiterResult dataclass."""

    def test_arbiter_result_immutable(self):
        """Test that ArbiterResult is frozen."""
        enhancers = [MockEnhancer(name="test", tag="cognitive")]

        result = ArbiterResult(
            enhancers=enhancers,
            mode_selection="sequential",
            reasoning_confidence=2,
            token_budget_applied=False,
            synergy_gate_applied=False,
            questioning_gate_applied=False,
            performance_gate_applied=False,
            rationale="test",
        )

        # Should raise error (frozen dataclass)
        with pytest.raises(Exception):  # FrozenInstanceError
            result.enhancers = []


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_enhancers(self):
        """Test with no enhancers."""
        result = resolve_conflict(
            enhancers=[],
            mode_selection="sequential",
            reasoning_confidence=2,
            prompt_mode=None,
        )

        assert len(result.enhancers) == 0
        assert result.mode_selection == "sequential"

    def test_no_mode_selection(self):
        """Test with no mode selection."""
        enhancers = [MockEnhancer(name="test", tag="cognitive")]

        result = resolve_conflict(
            enhancers=enhancers,
            mode_selection=None,
            reasoning_confidence=0,
            prompt_mode=None,
        )

        assert len(result.enhancers) == 1
        assert result.mode_selection is None

    def test_zero_max_detection_ms(self):
        """Test with zero max detection time (always block)."""
        enhancers = [MockEnhancer(name="test", tag="cognitive")]

        result = resolve_conflict(
            enhancers=enhancers,
            mode_selection="sequential",
            reasoning_confidence=2,
            prompt_mode=None,
            timing_ms=0.1,
            max_detection_ms=0.0,
        )

        # Should block (any time > 0 is too much)
        assert result.performance_gate_applied is True

    def test_empty_user_message(self):
        """Test with empty user message."""
        enhancers = [MockEnhancer(name="test", tag="cognitive")]

        result = resolve_conflict(
            enhancers=enhancers,
            mode_selection="sequential",
            reasoning_confidence=2,
            prompt_mode=None,
            user_message="",
        )

        # Should not trigger questioning gating
        assert result.questioning_gate_applied is False

    def test_none_parameters_use_defaults(self):
        """Test that None parameters use built-in defaults."""
        enhancers = [MockEnhancer(name="assumption_surfacing", tag="cognitive")]

        result = resolve_conflict(
            enhancers=enhancers,
            mode_selection="sequential",
            reasoning_confidence=2,
            prompt_mode=None,
            synergy_combinations=None,  # Use default
            questioning_patterns=None,  # Use default
        )

        # Should work with defaults
        assert len(result.enhancers) == 1
        assert result.synergy_gate_applied is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
