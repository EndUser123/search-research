"""
Unit Tests for LLM Supervisor with Hybrid Validation
======================================================

Tests the LLM Supervisor implementation that combines rule-based and LLM-based
validation with cost optimization and recursive safety.
"""

import asyncio
from unittest.mock import AsyncMock

import pytest

# Import the LLM Supervisor components
try:
    from llm_supervisor import HybridValidationEngine, LLMSupervisor, ValidationLevel
except ImportError:
    pytest.skip("LLM Supervisor components not available", allow_module_level=True)


class TestLLMSupervisor:
    """Test LLMSupervisor core functionality."""

    @pytest.fixture
    def supervisor(self):
        """Create LLMSupervisor instance for testing."""
        return LLMSupervisor(validation_level=ValidationLevel.STANDARD)

    @pytest.fixture
    def high_security_supervisor(self):
        """Create high-security LLMSupervisor instance."""
        return LLMSupervisor(validation_level=ValidationLevel.HIGH_SECURITY)

    @pytest.fixture
    def sample_validation_context(self):
        """Sample validation context for testing."""
        return {
            "operation": "file_edit",
            "tool_name": "Edit",
            "file_path": "src/main.py",
            "changes": [
                {"line": 42, "old": "print('hello')", "new": "print('hello world')"}
            ],
            "risk_level": "low",
            "evidence": {"code_review": "completed", "tests_pass": True},
        }

    def test_validation_level_enums(self):
        """Test ValidationLevel enum values and ordering."""
        assert ValidationLevel.BASIC.value == 1
        assert ValidationLevel.STANDARD.value == 2
        assert ValidationLevel.HIGH_SECURITY.value == 3
        assert ValidationLevel.PARANOID.value == 4

    def test_supervisor_initialization(self, supervisor):
        """Test LLMSupervisor initialization."""
        assert supervisor.validation_level == ValidationLevel.STANDARD
        assert hasattr(supervisor, "rule_validator")
        assert hasattr(supervisor, "llm_validator")
        assert hasattr(supervisor, "cost_optimizer")

    def test_high_security_configuration(self, high_security_supervisor):
        """Test high-security mode configuration."""
        assert (
            high_security_supervisor.validation_level == ValidationLevel.HIGH_SECURITY
        )
        # High security should enable more stringent validation
        assert high_security_supervisor.enable_llm_validation is True
        assert high_security_supervisor.enable_recursive_safety is True

    @pytest.mark.asyncio
    async def test_rule_based_validation_success(
        self, supervisor, sample_validation_context
    ):
        """Test successful rule-based validation."""
        # Mock rule validator to pass
        supervisor.rule_validator.validate = AsyncMock(
            return_value={"is_valid": True, "issues": [], "confidence": 0.95}
        )

        result = await supervisor._validate_rules(sample_validation_context)

        assert result["is_valid"] is True
        assert len(result["issues"]) == 0
        assert result["confidence"] > 0.9

    @pytest.mark.asyncio
    async def test_rule_based_validation_failure(self, supervisor):
        """Test rule-based validation failure."""
        dangerous_context = {
            "operation": "file_deletion",
            "tool_name": "Bash",
            "command": "rm -rf /important/data",
            "risk_level": "critical",
        }

        # Mock rule validator to detect danger
        supervisor.rule_validator.validate = AsyncMock(
            return_value={
                "is_valid": False,
                "issues": [
                    {
                        "type": "security_violation",
                        "severity": "critical",
                        "description": "Dangerous file deletion command",
                    }
                ],
                "confidence": 1.0,
            }
        )

        result = await supervisor._validate_rules(dangerous_context)

        assert result["is_valid"] is False
        assert len(result["issues"]) > 0
        assert result["issues"][0]["type"] == "security_violation"

    @pytest.mark.asyncio
    async def test_llm_validation_triggering(
        self, high_security_supervisor, sample_validation_context
    ):
        """Test LLM validation triggering conditions."""
        # Mock rule validator to return uncertainty
        high_security_supervisor.rule_validator.validate = AsyncMock(
            return_value={
                "is_valid": True,
                "issues": [],
                "confidence": 0.6,  # Low confidence triggers LLM validation
            }
        )

        # Mock LLM validator
        high_security_supervisor.llm_validator.validate = AsyncMock(
            return_value={
                "is_valid": True,
                "analysis": "Semantic analysis confirms code change is safe",
                "confidence": 0.92,
                "recommendations": ["Consider adding tests for the new functionality"],
            }
        )

        result = await high_security_supervisor.validate_operation(
            sample_validation_context
        )

        assert result["is_valid"] is True
        assert "llm_analysis" in result
        assert result["llm_analysis"]["confidence"] > 0.9

    @pytest.mark.asyncio
    async def test_cost_optimization(self, supervisor, sample_validation_context):
        """Test cost optimization prevents unnecessary LLM calls."""
        # Mock rule validator with high confidence
        supervisor.rule_validator.validate = AsyncMock(
            return_value={
                "is_valid": True,
                "issues": [],
                "confidence": 0.98,  # High confidence - no LLM needed
            }
        )

        # Mock LLM validator - should not be called
        supervisor.llm_validator.validate = AsyncMock(
            return_value={"is_valid": True, "confidence": 0.95}
        )

        result = await supervisor.validate_operation(sample_validation_context)

        # LLM should not be called due to cost optimization
        supervisor.llm_validator.validate.assert_not_called()
        assert result["is_valid"] is True
        assert "llm_analysis" not in result

    @pytest.mark.asyncio
    async def test_recursive_safety_prevention(self, high_security_supervisor):
        """Test recursive safety prevents infinite loops."""
        # Create context that might trigger recursion
        recursive_context = {
            "operation": "validation",
            "tool_name": "LLMSupervisor",
            "metadata": {"is_recursive_call": True},
        }

        # Should detect and prevent recursive validation
        result = await high_security_supervisor.validate_operation(recursive_context)

        assert result["is_valid"] is False
        assert any(
            "recursive" in issue.get("description", "").lower()
            for issue in result.get("issues", [])
        )

    @pytest.mark.asyncio
    async def test_stop_hook_integration(self, supervisor):
        """Test integration with Stop hook."""
        # Simulate stop hook activation
        supervisor.stop_hook_active = True

        context = {
            "operation": "test_execution",
            "tool_name": "Bash",
            "metadata": {"stop_hook_active": True},
        }

        # Should handle stop hook context properly
        result = await supervisor.validate_operation(context)

        assert result is not None
        # Stop hook should influence validation behavior
        assert result.get("stop_hook_processed", False) is True


class TestHybridValidationEngine:
    """Test HybridValidationEngine combining rule and LLM validation."""

    @pytest.fixture
    def hybrid_engine(self):
        """Create HybridValidationEngine for testing."""
        return HybridValidationEngine()

    @pytest.fixture
    def complex_validation_context(self):
        """Complex context requiring both rule and LLM validation."""
        return {
            "operation": "architecture_change",
            "tool_name": "Edit",
            "file_path": "src/core/system.py",
            "changes": [
                {
                    "type": "class_modification",
                    "class_name": "AuthenticationManager",
                    "changes": ["add_biometric_auth", "remove_legacy_support"],
                }
            ],
            "risk_level": "high",
            "evidence": {"security_review": "pending", "impact_analysis": "incomplete"},
        }

    @pytest.mark.asyncio
    async def test_hybrid_validation_workflow(
        self, hybrid_engine, complex_validation_context
    ):
        """Test complete hybrid validation workflow."""
        # Mock rule validator - detects potential issues
        hybrid_engine.rule_validator.validate = AsyncMock(
            return_value={
                "is_valid": True,
                "issues": [
                    {
                        "type": "security_concern",
                        "severity": "warning",
                        "description": "Authentication system modification detected",
                    }
                ],
                "confidence": 0.7,  # Moderate confidence triggers LLM
            }
        )

        # Mock LLM validator - provides semantic analysis
        hybrid_engine.llm_validator.validate = AsyncMock(
            return_value={
                "is_valid": True,
                "analysis": {
                    "semantic_safety": "safe",
                    "architecture_impact": "significant",
                    "security_implications": "requires_review",
                    "recommendations": [
                        "Add comprehensive security testing",
                        "Document deprecation of legacy auth",
                        "Ensure backward compatibility during transition",
                    ],
                },
                "confidence": 0.88,
            }
        )

        result = await hybrid_engine.validate(complex_validation_context)

        assert result["is_valid"] is True
        assert "rule_validation" in result
        assert "llm_validation" in result
        assert len(result["llm_validation"]["analysis"]["recommendations"]) > 0

    @pytest.mark.asyncio
    async def test_confidence_combination_logic(self, hybrid_engine):
        """Test confidence scoring from multiple validators."""
        context = {"operation": "test", "risk_level": "medium"}

        # Mock different confidence levels
        hybrid_engine.rule_validator.validate = AsyncMock(
            return_value={"is_valid": True, "issues": [], "confidence": 0.85}
        )

        hybrid_engine.llm_validator.validate = AsyncMock(
            return_value={"is_valid": True, "confidence": 0.92}
        )

        result = await hybrid_engine.validate(context)

        # Combined confidence should be weighted appropriately
        assert result["combined_confidence"] > 0.85
        assert result["combined_confidence"] <= 1.0

    @pytest.mark.asyncio
    async def test_validation_failure_handling(self, hybrid_engine):
        """Test handling of validation failures."""
        dangerous_context = {
            "operation": "system_config_change",
            "risk_level": "critical",
        }

        # Rule validator fails
        hybrid_engine.rule_validator.validate = AsyncMock(
            return_value={
                "is_valid": False,
                "issues": [
                    {
                        "type": "security_violation",
                        "severity": "critical",
                        "description": "Unauthorized system configuration change",
                    }
                ],
                "confidence": 1.0,
            }
        )

        result = await hybrid_engine.validate(dangerous_context)

        assert result["is_valid"] is False
        assert len(result["critical_issues"]) > 0
        # Should not call LLM validator when rule validation fails critically
        hybrid_engine.llm_validator.validate.assert_not_called()

    @pytest.mark.asyncio
    async def test_performance_optimization(self, hybrid_engine):
        """Test performance optimization features."""
        low_risk_context = {
            "operation": "comment_addition",
            "risk_level": "low",
            "file_path": "docs/readme.md",
        }

        # Mock fast rule validation for low-risk operations
        hybrid_engine.rule_validator.validate = AsyncMock(
            return_value={"is_valid": True, "issues": [], "confidence": 0.98}
        )

        import time

        start_time = time.time()

        result = await hybrid_engine.validate(low_risk_context)

        execution_time = time.time() - start_time

        # Should complete quickly without LLM validation
        assert execution_time < 0.5  # Sub-500ms for low-risk operations
        assert result["is_valid"] is True
        assert "llm_validation" not in result

    @pytest.mark.asyncio
    async def test_cache_integration(self, hybrid_engine):
        """Test caching of validation results."""
        context = {"operation": "duplicate_test", "file_path": "test.py"}

        # Mock validations
        hybrid_engine.rule_validator.validate = AsyncMock(
            return_value={"is_valid": True, "confidence": 0.9}
        )

        # First validation
        result1 = await hybrid_engine.validate(context)

        # Reset mock call count
        hybrid_engine.rule_validator.validate.reset_mock()

        # Second validation - should use cache
        result2 = await hybrid_engine.validate(context)

        # Rule validator should not be called again due to caching
        hybrid_engine.rule_validator.validate.assert_not_called()
        assert result1["combined_confidence"] == result2["combined_confidence"]


class TestErrorHandlingAndEdgeCases:
    """Test error handling and edge cases."""

    @pytest.fixture
    def supervisor(self):
        """Create supervisor for edge case testing."""
        return LLMSupervisor()

    @pytest.mark.asyncio
    async def test_llm_validator_unavailable(self, supervisor):
        """Test behavior when LLM validator is unavailable."""
        context = {"operation": "test", "risk_level": "medium"}

        # Mock rule validator
        supervisor.rule_validator.validate = AsyncMock(
            return_value={"is_valid": True, "confidence": 0.8}
        )

        # Mock LLM validator to raise exception
        supervisor.llm_validator.validate = AsyncMock(
            side_effect=Exception("LLM service unavailable")
        )

        result = await supervisor.validate_operation(context)

        # Should gracefully handle LLM unavailability
        assert result["is_valid"] is True
        assert "llm_error" in result
        assert result["llm_error"]["type"] == "service_unavailable"

    @pytest.mark.asyncio
    async def test_malformed_context_handling(self, supervisor):
        """Test handling of malformed or incomplete contexts."""
        malformed_contexts = [
            {},  # Empty context
            {"operation": None},  # None values
            {"risk_level": "unknown"},  # Unknown risk level
            {"operation": "test", "tool_name": ""},  # Empty strings
        ]

        for context in malformed_contexts:
            result = await supervisor.validate_operation(context)

            # Should handle gracefully without crashing
            assert result is not None
            assert "is_valid" in result

    @pytest.mark.asyncio
    async def test_timeout_handling(self, supervisor):
        """Test timeout handling for long-running validations."""

        # Mock slow rule validator
        async def slow_validation(context):
            await asyncio.sleep(5)  # 5 second delay
            return {"is_valid": True, "confidence": 0.9}

        supervisor.rule_validator.validate = slow_validation

        context = {"operation": "timeout_test"}

        # Should handle timeout gracefully
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(
                supervisor.validate_operation(context),
                timeout=1.0,  # 1 second timeout
            )

    @pytest.mark.asyncio
    async def test_concurrent_validation_safety(self, supervisor):
        """Test safety of concurrent validation requests."""
        contexts = [
            {"operation": f"test_{i}", "risk_level": "medium"} for i in range(10)
        ]

        # Mock validator
        supervisor.rule_validator.validate = AsyncMock(
            return_value={"is_valid": True, "confidence": 0.9}
        )

        # Run validations concurrently
        tasks = [supervisor.validate_operation(context) for context in contexts]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # All validations should complete successfully
        assert len(results) == 10
        for result in results:
            assert not isinstance(result, Exception)
            assert result["is_valid"] is True
