#!/usr/bin/env python3
"""
Unit tests for unified_prompting_system module.

Tests for unified prompting system functionality.
"""


from prompting_framework.unified_prompting_system import (
    IntegrationLevel,
    SystemConfig,
    SystemMode,
    UnifiedRequest,
    UnifiedResponse,
)


class TestSystemMode:
    """Test SystemMode enum."""

    def test_all_modes_defined(self):
        """Verify all expected modes are defined."""
        expected_modes = [
            "standalone",
            "framework_enhanced",
            "fully_integrated",
            "adaptive",
        ]
        actual_values = [m.value for m in SystemMode]
        for expected in expected_modes:
            assert expected in actual_values


class TestIntegrationLevel:
    """Test IntegrationLevel enum."""

    def test_all_levels_defined(self):
        """Verify all expected levels are defined."""
        expected_levels = [
            "minimal",
            "basic",
            "advanced",
            "complete",
        ]
        actual_values = [l.value for l in IntegrationLevel]
        for expected in expected_levels:
            assert expected in actual_values


class TestUnifiedRequest:
    """Test UnifiedRequest dataclass."""

    def test_create_request(self):
        """Create a unified request."""
        request = UnifiedRequest(
            request_id="req_1",
            prompt="Analyze the code",
            mode=SystemMode.FRAMEWORK_ENHANCED,
            integration_level=IntegrationLevel.ADVANCED,
            context={"language": "python", "domain": "security"},
            techniques=["chain_of_thought"],
            enable_enhancement=True,
        )
        assert request.request_id == "req_1"
        assert request.mode == SystemMode.FRAMEWORK_ENHANCED

    def test_request_with_defaults(self):
        """Create request with default values."""
        request = UnifiedRequest(
            request_id="req_2",
            prompt="Simple prompt",
        )
        assert request.mode == SystemMode.STANDALONE
        assert request.integration_level == IntegrationLevel.BASIC
        assert request.techniques == []

    def test_request_with_full_context(self):
        """Create request with comprehensive context."""
        request = UnifiedRequest(
            request_id="req_3",
            prompt="Complex request",
            mode=SystemMode.FULLY_INTEGRATED,
            integration_level=IntegrationLevel.COMPLETE,
            context={
                "language": "javascript",
                "domain": "frontend",
                "framework": "react",
                "user_level": "expert",
            },
            techniques=["self_refine", "chain_of_verification"],
            enable_enhancement=True,
            enable_validation=True,
            enable_optimization=True,
        )
        assert len(request.context) == 4
        assert len(request.techniques) == 2


class TestUnifiedResponse:
    """Test UnifiedResponse dataclass."""

    def test_create_response_success(self):
        """Create successful unified response."""
        response = UnifiedResponse(
            request_id="req_1",
            success=True,
            response="Here is the analysis",
            mode_used=SystemMode.FRAMEWORK_ENHANCED,
            techniques_applied=["chain_of_thought"],
            execution_time=3.5,
            quality_score=0.85,
            metadata={
                "enhancements": ["added context"],
                "iterations": 1,
            },
        )
        assert response.success is True
        assert response.quality_score == 0.85

    def test_create_response_failure(self):
        """Create failed unified response."""
        response = UnifiedResponse(
            request_id="req_2",
            success=False,
            response="",
            mode_used=SystemMode.STANDALONE,
            techniques_applied=[],
            execution_time=0.5,
            error_message="Failed to process request",
        )
        assert response.success is False
        assert "Failed" in response.error_message

    def test_response_with_full_metadata(self):
        """Create response with comprehensive metadata."""
        response = UnifiedResponse(
            request_id="req_3",
            success=True,
            response="Optimized response",
            mode_used=SystemMode.ADAPTIVE,
            techniques_applied=["self_refine", "query_fanout"],
            execution_time=8.0,
            quality_score=0.92,
            metadata={
                "enhancements": ["context", "examples"],
                "iterations": 3,
                "cache_hits": 2,
                "optimizations": ["early_exit", "caching"],
                "validation_results": {"passed": True},
            },
        )
        assert len(response.techniques_applied) == 2
        assert len(response.metadata["optimizations"]) == 2


class TestSystemConfig:
    """Test SystemConfig dataclass."""

    def test_create_config(self):
        """Create system configuration."""
        config = SystemConfig(
            default_mode=SystemMode.ADAPTIVE,
            default_integration=IntegrationLevel.ADVANCED,
            enable_caching=True,
            cache_ttl=3600,
            max_concurrent_requests=10,
            timeout=30.0,
            quality_threshold=0.7,
        )
        assert config.default_mode == SystemMode.ADAPTIVE
        assert config.enable_caching is True

    def test_config_with_defaults(self):
        """Create config with default values."""
        config = SystemConfig()
        assert config.default_mode == SystemMode.STANDALONE
        assert config.default_integration == IntegrationLevel.BASIC
        assert config.enable_caching is False

    def test_high_performance_config(self):
        """High-performance system configuration."""
        config = SystemConfig(
            default_mode=SystemMode.FULLY_INTEGRATED,
            default_integration=IntegrationLevel.COMPLETE,
            enable_caching=True,
            cache_ttl=7200,
            max_concurrent_requests=50,
            timeout=60.0,
            quality_threshold=0.8,
            enable_optimization=True,
            enable_validation=True,
        )
        assert config.max_concurrent_requests == 50
        assert config.quality_threshold == 0.8


class TestSystemModes:
    """Test different system modes."""

    def test_standalone_mode(self):
        """Standalone system mode."""
        assert SystemMode.STANDALONE.value == "standalone"

    def test_framework_enhanced_mode(self):
        """Framework-enhanced system mode."""
        assert SystemMode.FRAMEWORK_ENHANCED.value == "framework_enhanced"

    def test_fully_integrated_mode(self):
        """Fully integrated system mode."""
        assert SystemMode.FULLY_INTEGRATED.value == "fully_integrated"

    def test_adaptive_mode(self):
        """Adaptive system mode."""
        assert SystemMode.ADAPTIVE.value == "adaptive"


class TestIntegrationLevels:
    """Test different integration levels."""

    def test_minimal_level(self):
        """Minimal integration level."""
        assert IntegrationLevel.MINIMAL.value == "minimal"

    def test_basic_level(self):
        """Basic integration level."""
        assert IntegrationLevel.BASIC.value == "basic"

    def test_advanced_level(self):
        """Advanced integration level."""
        assert IntegrationLevel.ADVANCED.value == "advanced"

    def test_complete_level(self):
        """Complete integration level."""
        assert IntegrationLevel.COMPLETE.value == "complete"


class TestEdgeCases:
    """Test edge cases for unified system."""

    def test_empty_context(self):
        """Handle request with empty context."""
        request = UnifiedRequest(
            request_id="empty",
            prompt="Simple question",
            context={},
        )
        assert len(request.context) == 0

    def test_no_techniques(self):
        """Handle request with no techniques."""
        request = UnifiedRequest(
            request_id="no_tech",
            prompt="Direct question",
            techniques=[],
        )
        assert len(request.techniques) == 0

    def test_zero_execution_time(self):
        """Handle cached response."""
        response = UnifiedResponse(
            request_id="cached",
            success=True,
            response="From cache",
            mode_used=SystemMode.STANDALONE,
            techniques_applied=[],
            execution_time=0.0,
            quality_score=0.8,
        )
        assert response.execution_time == 0.0

    def test_perfect_quality(self):
        """Handle perfect quality score."""
        response = UnifiedResponse(
            request_id="perfect",
            success=True,
            response="Perfect response",
            mode_used=SystemMode.ADAPTIVE,
            techniques_applied=["chain_of_thought"],
            execution_time=5.0,
            quality_score=1.0,
        )
        assert response.quality_score == 1.0

    def test_minimal_quality(self):
        """Handle minimal quality score."""
        response = UnifiedResponse(
            request_id="minimal",
            success=True,
            response="Minimal response",
            mode_used=SystemMode.STANDALONE,
            techniques_applied=[],
            execution_time=1.0,
            quality_score=0.0,
        )
        assert response.quality_score == 0.0


class TestIntegrationScenarios:
    """Test various integration scenarios."""

    def test_standalone_mode_request(self):
        """Request in standalone mode."""
        request = UnifiedRequest(
            request_id="standalone",
            prompt="Direct question",
            mode=SystemMode.STANDALONE,
            integration_level=IntegrationLevel.MINIMAL,
        )
        assert request.mode == SystemMode.STANDALONE
        assert request.integration_level == IntegrationLevel.MINIMAL

    def test_fully_integrated_mode_request(self):
        """Request in fully integrated mode."""
        request = UnifiedRequest(
            request_id="integrated",
            prompt="Complex task",
            mode=SystemMode.FULLY_INTEGRATED,
            integration_level=IntegrationLevel.COMPLETE,
            techniques=["chain_of_thought", "self_refine", "chain_of_verification"],
            enable_enhancement=True,
            enable_validation=True,
            enable_optimization=True,
        )
        assert request.mode == SystemMode.FULLY_INTEGRATED
        assert len(request.techniques) == 3

    def test_adaptive_mode_response(self):
        """Response from adaptive mode."""
        response = UnifiedResponse(
            request_id="adaptive",
            success=True,
            response="Adaptively optimized response",
            mode_used=SystemMode.ADAPTIVE,
            techniques_applied=["self_refine"],
            execution_time=4.0,
            quality_score=0.88,
            metadata={
                "mode_selection_reason": "High complexity detected",
                "adaptive_optimizations": ["early_exit", "caching"],
            },
        )
        assert response.mode_used == SystemMode.ADAPTIVE
        assert "mode_selection_reason" in response.metadata
