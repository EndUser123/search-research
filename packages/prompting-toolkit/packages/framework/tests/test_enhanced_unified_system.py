#!/usr/bin/env python3
"""
Unit tests for enhanced_unified_system module.

Tests for enhanced unified prompting system.
"""


from prompting_framework.enhanced_unified_system import (
    EnhancedSystemConfig,
    EnhancedSystemResult,
    EnhancementType,
    SystemEnhancement,
)


class TestEnhancementType:
    """Test EnhancementType enum."""

    def test_all_types_defined(self):
        """Verify all expected types are defined."""
        expected_types = [
            "performance",
            "quality",
            "capability",
            "integration",
            "scalability",
        ]
        actual_values = [t.value for t in EnhancementType]
        for expected in expected_types:
            assert expected in actual_values


class TestSystemEnhancement:
    """Test SystemEnhancement dataclass."""

    def test_create_enhancement(self):
        """Create a system enhancement."""
        enhancement = SystemEnhancement(
            enhancement_id="enh_1",
            enhancement_type=EnhancementType.PERFORMANCE,
            name="Cache optimization",
            description="Add caching layer for faster responses",
            priority=1,
            enabled=True,
        )
        assert enhancement.enhancement_type == EnhancementType.PERFORMANCE
        assert enhancement.priority == 1

    def test_enhancement_high_priority(self):
        """Create high priority enhancement."""
        enhancement = SystemEnhancement(
            enhancement_id="critical",
            enhancement_type=EnhancementType.QUALITY,
            name="Quality gate",
            description="Add quality validation",
            priority=1,  # High priority
            enabled=True,
        )
        assert enhancement.priority == 1


class TestEnhancedSystemConfig:
    """Test EnhancedSystemConfig dataclass."""

    def test_create_config(self):
        """Create enhanced system configuration."""
        enhancements = [
            SystemEnhancement(
                enhancement_id="e1",
                enhancement_type=EnhancementType.CAPABILITY,
                name="Tool support",
                description="Enable tool use",
                priority=2,
                enabled=True,
            )
        ]

        config = EnhancedSystemConfig(
            config_id="config_1",
            base_mode="adaptive",
            enhancements=enhancements,
            auto_enable=False,
            max_enhancements=5,
        )
        assert len(config.enhancements) == 1
        assert config.max_enhancements == 5

    def test_config_no_enhancements(self):
        """Create config with no enhancements."""
        config = EnhancedSystemConfig(
            config_id="minimal",
            base_mode="basic",
            enhancements=[],
        )
        assert len(config.enhancements) == 0


class TestEnhancedSystemResult:
    """Test EnhancedSystemResult dataclass."""

    def test_create_result_success(self):
        """Create successful enhanced system result."""
        result = EnhancedSystemResult(
            request_id="req_1",
            success=True,
            response="Enhanced response",
            base_mode="adaptive",
            enhancements_applied=["caching", "validation"],
            execution_time=3.5,
            quality_improvement=0.2,
            performance_improvement=0.3,
        )
        assert result.success is True
        assert result.quality_improvement == 0.2
        assert result.performance_improvement == 0.3

    def test_result_with_improvements(self):
        """Result showing multiple improvements."""
        result = EnhancedSystemResult(
            request_id="req_2",
            success=True,
            response="Optimized response",
            base_mode="adaptive",
            enhancements_applied=["caching", "parallel_processing", "compression"],
            execution_time=2.0,
            quality_improvement=0.15,
            performance_improvement=0.5,
        )
        assert len(result.enhancements_applied) == 3
        assert result.performance_improvement > result.quality_improvement


class TestEnhancementTypes:
    """Test different enhancement types."""

    def test_performance_type(self):
        """Performance enhancement type."""
        assert EnhancementType.PERFORMANCE.value == "performance"

    def test_quality_type(self):
        """Quality enhancement type."""
        assert EnhancementType.QUALITY.value == "quality"

    def test_capability_type(self):
        """Capability enhancement type."""
        assert EnhancementType.CAPABILITY.value == "capability"

    def test_integration_type(self):
        """Integration enhancement type."""
        assert EnhancementType.INTEGRATION.value == "integration"

    def test_scalability_type(self):
        """Scalability enhancement type."""
        assert EnhancementType.SCALABILITY.value == "scalability"


class TestEdgeCases:
    """Test edge cases for enhanced system."""

    def test_zero_improvements(self):
        """Handle result with no improvements."""
        result = EnhancedSystemResult(
            request_id="no_change",
            success=True,
            response="Standard response",
            base_mode="basic",
            enhancements_applied=[],
            execution_time=2.0,
            quality_improvement=0.0,
            performance_improvement=0.0,
        )
        assert result.quality_improvement == 0.0
        assert result.performance_improvement == 0.0

    def test_negative_improvement(self):
        """Handle regression in improvements."""
        result = EnhancedSystemResult(
            request_id="regression",
            success=True,
            response="Response",
            base_mode="adaptive",
            enhancements_applied=["experimental_feature"],
            execution_time=5.0,
            quality_improvement=-0.1,
            performance_improvement=-0.2,
        )
        assert result.quality_improvement < 0
        assert result.performance_improvement < 0
