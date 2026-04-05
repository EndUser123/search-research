"""
Unit Tests for PostToolUse BalancedValidationLogic
================================================

Tests the core validation logic implemented in the PostToolUse hook,
including parallel validation engines and balanced decision making.
"""

import time
from unittest.mock import AsyncMock

import pytest

# Import the actual PostToolUse hook components
try:
    from post_tool_use import (
        BalancedValidationLogic,
        ParallelValidationEngine,
        ValidationResult,
    )
except ImportError:
    pytest.skip("PostToolUse components not available", allow_module_level=True)


class TestBalancedValidationLogic:
    """Test BalancedValidationLogic implementation."""

    @pytest.fixture
    def validation_logic(self):
        """Create BalancedValidationLogic instance for testing."""
        return BalancedValidationLogic()

    @pytest.fixture
    def critical_security_violation(self):
        """Sample critical security violation."""
        return {
            "type": "security_violation",
            "severity": "critical",
            "description": "Potential command injection detected",
            "evidence": {"command": "rm -rf /", "pattern": "dangerous_file_operation"},
        }

    @pytest.fixture
    def error_missing_evidence(self):
        """Sample error with feedback requirement."""
        return {
            "type": "missing_evidence",
            "severity": "error",
            "description": "No evidence provided for file operation",
            "required_evidence": ["file_operation_record", "safety_validation"],
        }

    @pytest.fixture
    def warning_performance(self):
        """Sample warning that allows execution."""
        return {
            "type": "performance_degradation",
            "severity": "warning",
            "description": "Operation took longer than expected",
            "impact": "minor",
            "suggestion": "Consider optimization",
        }

    def test_validation_result_creation(self, validation_logic):
        """Test ValidationResult object creation and properties."""
        result = ValidationResult(
            is_valid=True,
            confidence=0.95,
            critical_issues=[],
            errors=[],
            warnings=["minor_performance_issue"],
            execution_time=0.8,
        )

        assert result.is_valid is True
        assert result.confidence == 0.95
        assert len(result.critical_issues) == 0
        assert len(result.errors) == 0
        assert len(result.warnings) == 1
        assert result.execution_time == 0.8

    def test_critical_block_execution(
        self, validation_logic, critical_security_violation
    ):
        """Test that critical issues block execution."""
        result = ValidationResult(
            is_valid=False,
            confidence=1.0,
            critical_issues=[critical_security_violation],
            errors=[],
            warnings=[],
        )

        assert result._should_block_execution() is True
        assert "security_violation" in result.get_blocking_reasons()

    def test_error_with_feedback_allows_execution(
        self, validation_logic, error_missing_evidence
    ):
        """Test that errors with feedback allow execution but require response."""
        result = ValidationResult(
            is_valid=True,
            confidence=0.7,
            critical_issues=[],
            errors=[error_missing_evidence],
            warnings=[],
        )

        assert result._should_block_execution() is False
        assert result.requires_feedback() is True
        assert "missing_evidence" in result.get_feedback_requirements()

    def test_warning_allows_execution(self, validation_logic, warning_performance):
        """Test that warnings allow execution without blocking."""
        result = ValidationResult(
            is_valid=True,
            confidence=0.9,
            critical_issues=[],
            errors=[],
            warnings=[warning_performance],
        )

        assert result._should_block_execution() is False
        assert result.requires_feedback() is False

    def test_multiple_issue_priority(
        self,
        validation_logic,
        critical_security_violation,
        error_missing_evidence,
        warning_performance,
    ):
        """Test that critical issues take priority over errors and warnings."""
        result = ValidationResult(
            is_valid=False,
            confidence=1.0,
            critical_issues=[critical_security_violation],
            errors=[error_missing_evidence],
            warnings=[warning_performance],
        )

        # Critical should block regardless of other issues
        assert result._should_block_execution() is True
        assert len(result.get_all_issues()) == 3

    def test_confidence_calculation(self, validation_logic):
        """Test confidence calculation based on issues found."""
        # High confidence - no issues
        result1 = ValidationResult(is_valid=True, confidence=1.0)
        assert result1.confidence == 1.0

        # Medium confidence - warnings only
        result2 = ValidationResult(
            is_valid=True, confidence=0.9, warnings=[{"type": "minor_issue"}]
        )
        assert result2.confidence == 0.9

        # Low confidence - errors present
        result3 = ValidationResult(
            is_valid=True, confidence=0.6, errors=[{"type": "missing_evidence"}]
        )
        assert result3.confidence == 0.6


class TestParallelValidationEngine:
    """Test ParallelValidationEngine implementation."""

    @pytest.fixture
    def validation_engine(self):
        """Create ParallelValidationEngine instance for testing."""
        return ParallelValidationEngine()

    @pytest.fixture
    def mock_hook_context(self):
        """Mock hook context for validation."""
        return {
            "tool_name": "Edit",
            "tool_result": {"success": True},
            "duration_ms": 150,
            "metadata": {"file_path": "test.py", "operation": "code_change"},
        }

    @pytest.mark.asyncio
    async def test_parallel_validation_execution(
        self, validation_engine, mock_hook_context
    ):
        """Test that validations run in parallel."""
        start_time = time.time()

        # Mock validation methods
        validation_engine._validate_security = AsyncMock(return_value=[])
        validation_engine._validate_performance = AsyncMock(return_value=[])
        validation_engine._validate_evidence = AsyncMock(return_value=[])
        validation_engine._validate_operation_safety = AsyncMock(return_value=[])

        result = await validation_engine.validate_operation(mock_hook_context)

        execution_time = time.time() - start_time

        # Should complete quickly due to parallel execution
        assert execution_time < 1.0  # Should be much less than sequential execution
        assert isinstance(result, ValidationResult)
        assert result.is_valid is True

    @pytest.mark.asyncio
    async def test_security_validation_detection(
        self, validation_engine, mock_hook_context
    ):
        """Test security validation detects dangerous patterns."""
        # Mock dangerous operation
        dangerous_context = {
            "tool_name": "Bash",
            "tool_result": {"success": True},
            "command": "rm -rf /important/file",
            "metadata": {"operation": "file_deletion"},
        }

        # Mock security validation to detect danger
        async def mock_security_validation(context):
            if "rm -rf" in context.get("command", ""):
                return [
                    {
                        "type": "security_violation",
                        "severity": "critical",
                        "description": "Dangerous file deletion command detected",
                    }
                ]
            return []

        validation_engine._validate_security = mock_security_validation
        validation_engine._validate_performance = AsyncMock(return_value=[])
        validation_engine._validate_evidence = AsyncMock(return_value=[])
        validation_engine._validate_operation_safety = AsyncMock(return_value=[])

        result = await validation_engine.validate_operation(dangerous_context)

        assert result.is_valid is False
        assert len(result.critical_issues) > 0
        assert result.critical_issues[0]["type"] == "security_violation"

    @pytest.mark.asyncio
    async def test_evidence_validation_missing_evidence(
        self, validation_engine, mock_hook_context
    ):
        """Test evidence validation detects missing evidence."""

        # Mock evidence validation to require evidence for code changes
        async def mock_evidence_validation(context):
            if context.get("metadata", {}).get("operation") == "code_change":
                return [
                    {
                        "type": "missing_evidence",
                        "severity": "error",
                        "description": "No evidence provided for code change",
                        "required_evidence": ["test_results", "code_review"],
                    }
                ]
            return []

        validation_engine._validate_security = AsyncMock(return_value=[])
        validation_engine._validate_performance = AsyncMock(return_value=[])
        validation_engine._validate_evidence = mock_evidence_validation
        validation_engine._validate_operation_safety = AsyncMock(return_value=[])

        result = await validation_engine.validate_operation(mock_hook_context)

        assert result.is_valid is True  # Errors with feedback allow execution
        assert len(result.errors) > 0
        assert result.errors[0]["type"] == "missing_evidence"
        assert result.requires_feedback() is True

    @pytest.mark.asyncio
    async def test_performance_validation_slow_operation(
        self, validation_engine, mock_hook_context
    ):
        """Test performance validation detects slow operations."""
        # Mock slow operation
        slow_context = {
            "tool_name": "Bash",
            "tool_result": {"success": True},
            "duration_ms": 5000,  # 5 seconds - very slow
            "metadata": {"operation": "data_processing"},
        }

        # Mock performance validation
        async def mock_performance_validation(context):
            if context.get("duration_ms", 0) > 3000:  # 3 second threshold
                return [
                    {
                        "type": "performance_degradation",
                        "severity": "warning",
                        "description": "Operation exceeded performance threshold",
                        "actual_time": context["duration_ms"],
                        "threshold_ms": 3000,
                    }
                ]
            return []

        validation_engine._validate_security = AsyncMock(return_value=[])
        validation_engine._validate_performance = mock_performance_validation
        validation_engine._validate_evidence = AsyncMock(return_value=[])
        validation_engine._validate_operation_safety = AsyncMock(return_value=[])

        result = await validation_engine.validate_operation(slow_context)

        assert result.is_valid is True  # Warnings allow execution
        assert len(result.warnings) > 0
        assert result.warnings[0]["type"] == "performance_degradation"

    @pytest.mark.asyncio
    async def test_cache_hit_performance(self, validation_engine, mock_hook_context):
        """Test that cache hits improve performance."""
        # First call - cache miss
        start_time = time.time()
        validation_engine._validate_security = AsyncMock(return_value=[])
        validation_engine._validate_performance = AsyncMock(return_value=[])
        validation_engine._validate_evidence = AsyncMock(return_value=[])
        validation_engine._validate_operation_safety = AsyncMock(return_value=[])

        result1 = await validation_engine.validate_operation(mock_hook_context)
        first_call_time = time.time() - start_time

        # Second call with same context - should hit cache
        start_time = time.time()
        result2 = await validation_engine.validate_operation(mock_hook_context)
        second_call_time = time.time() - start_time

        # Second call should be faster due to caching
        assert second_call_time < first_call_time
        assert result1.execution_time == result2.execution_time  # Same result

    @pytest.mark.asyncio
    async def test_validation_error_handling(
        self, validation_engine, mock_hook_context
    ):
        """Test handling of validation errors."""
        # Mock validation to raise an exception
        validation_engine._validate_security = AsyncMock(
            side_effect=Exception("Validation error")
        )
        validation_engine._validate_performance = AsyncMock(return_value=[])
        validation_engine._validate_evidence = AsyncMock(return_value=[])
        validation_engine._validate_operation_safety = AsyncMock(return_value=[])

        # Should handle errors gracefully
        result = await validation_engine.validate_operation(mock_hook_context)

        assert result is not None
        assert isinstance(result, ValidationResult)
        # Should mark as invalid due to validation error
        assert result.is_valid is False


class TestIntegrationScenarios:
    """Test realistic integration scenarios."""

    @pytest.mark.asyncio
    async def test_file_write_with_evidence(self):
        """Test file write operation with proper evidence."""
        engine = ParallelValidationEngine()

        context = {
            "tool_name": "Write",
            "tool_result": {"success": True},
            "metadata": {
                "file_path": "test.py",
                "operation": "file_creation",
                "evidence_provided": ["file_write_record", "safety_check"],
            },
        }

        # Mock validations for successful file write
        engine._validate_security = AsyncMock(return_value=[])
        engine._validate_performance = AsyncMock(return_value=[])
        engine._validate_evidence = AsyncMock(return_value=[])  # Evidence provided
        engine._validate_operation_safety = AsyncMock(return_value=[])

        result = await engine.validate_operation(context)

        assert result.is_valid is True
        assert len(result.critical_issues) == 0
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_bash_command_without_evidence(self):
        """Test bash command without required evidence."""
        engine = ParallelValidationEngine()

        context = {
            "tool_name": "Bash",
            "command": "python test.py",
            "tool_result": {"success": True, "stdout": "Tests passed"},
            "metadata": {
                "operation": "test_execution",
                "evidence_provided": [],  # No evidence
            },
        }

        # Mock validations - missing evidence for test execution
        engine._validate_security = AsyncMock(return_value=[])
        engine._validate_performance = AsyncMock(return_value=[])
        engine._validate_evidence = AsyncMock(
            return_value=[
                {
                    "type": "missing_evidence",
                    "severity": "error",
                    "description": "No test evidence provided for bash execution",
                    "required_evidence": ["test_results", "execution_log"],
                }
            ]
        )
        engine._validate_operation_safety = AsyncMock(return_value=[])

        result = await engine.validate_operation(context)

        assert result.is_valid is True  # Error with feedback allows execution
        assert len(result.errors) == 1
        assert result.errors[0]["type"] == "missing_evidence"
        assert result.requires_feedback() is True
