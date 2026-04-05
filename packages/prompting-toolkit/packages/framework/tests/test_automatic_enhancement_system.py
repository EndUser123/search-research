#!/usr/bin/env python3
"""
Unit tests for automatic_enhancement_system module.

Tests for automatic enhancement system functionality.
"""


from prompting_framework.automatic_enhancement_system import (
    EnhancementLevel,
    EnhancementResult,
    EnhancementSystemConfig,
    EnhancementTrigger,
)


class TestEnhancementTrigger:
    """Test EnhancementTrigger enum."""

    def test_all_triggers_defined(self):
        """Verify all expected triggers are defined."""
        expected_triggers = [
            "ambiguity_detected",
            "complexity_low",
            "domain_mismatch",
            "missing_context",
            "quality_threshold",
        ]
        actual_values = [t.value for t in EnhancementTrigger]
        for expected in expected_triggers:
            assert expected in actual_values


class TestEnhancementLevel:
    """Test EnhancementLevel enum."""

    def test_all_levels_defined(self):
        """Verify all expected levels are defined."""
        expected_levels = [
            "minimal",
            "moderate",
            "significant",
            "complete",
        ]
        actual_values = [l.value for l in EnhancementLevel]
        for expected in expected_levels:
            assert expected in actual_values


class TestEnhancementResult:
    """Test EnhancementResult dataclass."""

    def test_create_result(self):
        """Create an enhancement result."""
        result = EnhancementResult(
            original_prompt="Write code",
            enhanced_prompt="Write a Python function that validates user input",
            trigger=EnhancementTrigger.AMBIGUITY_DETECTED,
            level=EnhancementLevel.MODERATE,
            confidence=0.85,
            auto_applied=True,
        )
        assert result.trigger == EnhancementTrigger.AMBIGUITY_DETECTED
        assert result.level == EnhancementLevel.MODERATE
        assert result.auto_applied is True

    def test_result_without_auto_apply(self):
        """Result without auto-application."""
        result = EnhancementResult(
            original_prompt="Help",
            enhanced_prompt="Help me debug this issue",
            trigger=EnhancementTrigger.COMPLEXITY_LOW,
            level=EnhancementLevel.MINIMAL,
            confidence=0.6,
            auto_applied=False,
            reason="Requires user confirmation",
        )
        assert result.auto_applied is False


class TestEnhancementSystemConfig:
    """Test EnhancementSystemConfig dataclass."""

    def test_create_config(self):
        """Create enhancement system configuration."""
        config = EnhancementSystemConfig(
            auto_apply=True,
            min_confidence=0.7,
            max_enhancement_level=EnhancementLevel.SIGNIFICANT,
            enabled_triggers=[
                EnhancementTrigger.AMBIGUITY_DETECTED,
                EnhancementTrigger.MISSING_CONTEXT,
            ],
        )
        assert config.auto_apply is True
        assert config.min_confidence == 0.7

    def test_conservative_config(self):
        """Conservative enhancement configuration."""
        config = EnhancementSystemConfig(
            auto_apply=False,
            min_confidence=0.9,
            max_enhancement_level=EnhancementLevel.MINIMAL,
            enabled_triggers=[EnhancementTrigger.QUALITY_THRESHOLD],
        )
        assert config.auto_apply is False
        assert config.min_confidence == 0.9


class TestEnhancementTriggers:
    """Test different enhancement triggers."""

    def test_ambiguity_detected_trigger(self):
        """Ambiguity detected trigger."""
        assert EnhancementTrigger.AMBIGUITY_DETECTED.value == "ambiguity_detected"

    def test_complexity_low_trigger(self):
        """Complexity low trigger."""
        assert EnhancementTrigger.COMPLEXITY_LOW.value == "complexity_low"

    def test_domain_mismatch_trigger(self):
        """Domain mismatch trigger."""
        assert EnhancementTrigger.DOMAIN_MISMATCH.value == "domain_mismatch"

    def test_missing_context_trigger(self):
        """Missing context trigger."""
        assert EnhancementTrigger.MISSING_CONTEXT.value == "missing_context"

    def test_quality_threshold_trigger(self):
        """Quality threshold trigger."""
        assert EnhancementTrigger.QUALITY_THRESHOLD.value == "quality_threshold"


class TestEnhancementLevels:
    """Test different enhancement levels."""

    def test_minimal_level(self):
        """Minimal enhancement level."""
        assert EnhancementLevel.MINIMAL.value == "minimal"

    def test_moderate_level(self):
        """Moderate enhancement level."""
        assert EnhancementLevel.MODERATE.value == "moderate"

    def test_significant_level(self):
        """Significant enhancement level."""
        assert EnhancementLevel.SIGNIFICANT.value == "significant"

    def test_complete_level(self):
        """Complete enhancement level."""
        assert EnhancementLevel.COMPLETE.value == "complete"


class TestEdgeCases:
    """Test edge cases for automatic enhancement."""

    def test_no_enhancement_needed(self):
        """Handle case where no enhancement is needed."""
        result = EnhancementResult(
            original_prompt="Write a Python function that sorts a list of integers in ascending order using the built-in sort method",
            enhanced_prompt="Write a Python function that sorts a list of integers in ascending order using the built-in sort method",
            trigger=None,
            level=EnhancementLevel.MINIMAL,
            confidence=1.0,
            auto_applied=False,
            reason="Prompt already optimal",
        )
        assert result.level == EnhancementLevel.MINIMAL
        assert result.confidence == 1.0

    def test_max_enhancement(self):
        """Handle maximum enhancement level."""
        result = EnhancementResult(
            original_prompt="do it",
            enhanced_prompt="Implement a comprehensive solution that addresses all requirements, includes error handling, documentation, testing, and follows best practices for production deployment",
            trigger=EnhancementTrigger.AMBIGUITY_DETECTED,
            level=EnhancementLevel.COMPLETE,
            confidence=0.95,
            auto_applied=True,
        )
        assert result.level == EnhancementLevel.COMPLETE

    def test_low_confidence_no_auto_apply(self):
        """Low confidence should not auto-apply."""
        result = EnhancementResult(
            original_prompt="help",
            enhanced_prompt="help me with this specific task",
            trigger=EnhancementTrigger.COMPLEXITY_LOW,
            level=EnhancementLevel.MINIMAL,
            confidence=0.4,
            auto_applied=False,
            reason="Confidence too low for auto-apply",
        )
        assert result.confidence < 0.5
        assert result.auto_applied is False


class TestEnhancementScenarios:
    """Test various enhancement scenarios."""

    def test_ambiguity_trigger_enhancement(self):
        """Enhancement triggered by ambiguity."""
        result = EnhancementResult(
            original_prompt="fix this",
            enhanced_prompt="Fix the null pointer exception in the authentication module that occurs when users have expired tokens",
            trigger=EnhancementTrigger.AMBIGUITY_DETECTED,
            level=EnhancementLevel.SIGNIFICANT,
            confidence=0.9,
            auto_applied=True,
        )
        assert result.trigger == EnhancementTrigger.AMBIGUITY_DETECTED
        assert result.level == EnhancementLevel.SIGNIFICANT

    def test_missing_context_enhancement(self):
        """Enhancement triggered by missing context."""
        result = EnhancementResult(
            original_prompt="Create a web API",
            enhanced_prompt="Create a RESTful API using FastAPI for user management with endpoints for registration, login, and profile updates",
            trigger=EnhancementTrigger.MISSING_CONTEXT,
            level=EnhancementLevel.MODERATE,
            confidence=0.85,
            auto_applied=True,
        )
        assert result.trigger == EnhancementTrigger.MISSING_CONTEXT
        assert "FastAPI" in result.enhanced_prompt

    def test_multi_trigger_enhancement(self):
        """Enhancement triggered by multiple factors."""
        result = EnhancementResult(
            original_prompt="optimize",
            enhanced_prompt="Optimize the SQL query for the orders table by adding appropriate indexes on the customer_id and date columns to reduce query time from 500ms to under 50ms",
            trigger=EnhancementTrigger.AMBIGUITY_DETECTED,  # Primary trigger
            level=EnhancementLevel.COMPLETE,
            confidence=0.92,
            auto_applied=True,
            additional_triggers=[
                EnhancementTrigger.MISSING_CONTEXT,
                EnhancementTrigger.COMPLEXITY_LOW,
            ],
        )
        assert result.trigger == EnhancementTrigger.AMBIGUITY_DETECTED
        assert len(result.additional_triggers) == 2
