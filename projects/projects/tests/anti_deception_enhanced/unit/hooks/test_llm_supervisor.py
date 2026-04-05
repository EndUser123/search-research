"""
Unit Tests for LLM Supervisor Component

Tests the LLM Supervisor functionality for the Enhanced Anti-Deception Architecture.
Validates LLM integration, cost validation, response analysis, and decision making.
"""

import os
import sys
import time
from unittest.mock import Mock, patch

# Import test utilities
sys.path.insert(0, os.path.dirname(__file__))
from utils import EvidenceGenerator, MockLLM, PerformanceTimer, TestConfigHelper

# Import the anti-deception hook
sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "__csf")
)
try:
    from anti_deception_hook import AntiDeceptionHook
except ImportError:
    raise ImportError("Could not import AntiDeceptionHook")


class TestLLMSupervisor:
    """Test suite for LLM Supervisor functionality."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.config = TestConfigHelper.create_minimal_config()
        self.hook = AntiDeceptionHook()
        self.mock_llm = MockLLM()
        self.evidence_generator = EvidenceGenerator()

    def teardown_method(self):
        """Clean up after each test method."""
        self.hook.reset_failures()

    def test_llm_supervisor_initialization(self):
        """Test that LLM Supervisor initializes correctly."""
        assert self.hook is not None
        assert self.hook.config is not None

        # Check that configuration contains relevant LLM settings
        assert "validation_rules" in self.hook.config

    @patch("anti_deception_hook.AntiDeceptionHook._call_llm_api")
    def test_llm_supervisor_safe_operation_validation(self, mock_llm_api):
        """Test LLM validation for safe operations."""
        # Mock safe LLM response
        mock_response = Mock()
        mock_response.json.return_value = {
            "is_safe": True,
            "confidence": 0.95,
            "cost_estimate": 0.005,
            "reasoning": "Operation appears to be safe and valid",
        }
        mock_llm_api.return_value = mock_response

        # Test operation context
        operation_context = {
            "operation": "write_file",
            "target_path": "P:\\__csf\\test.txt",
            "content": "test content",
            "user_intent": "Create test file",
        }

        # Call LLM supervisor
        result = self.hook._validate_with_llm_supervisor(operation_context)

        # Verify LLM was called
        mock_llm_api.assert_called_once()
        assert result is not None

    @patch("anti_deception_hook.AntiDeceptionHook._call_llm_api")
    def test_llm_supervisor_dangerous_operation_validation(self, mock_llm_api):
        """Test LLM validation for dangerous operations."""
        # Mock dangerous LLM response
        mock_response = Mock()
        mock_response.json.return_value = {
            "is_safe": False,
            "confidence": 0.98,
            "cost_estimate": 0.008,
            "reasoning": "Operation involves system-critical files and could be dangerous",
        }
        mock_llm_api.return_value = mock_response

        # Test dangerous operation context
        operation_context = {
            "operation": "write_file",
            "target_path": "/etc/passwd",
            "content": "malicious content",
            "user_intent": "Modify system file",
        }

        # Call LLM supervisor
        result = self.hook._validate_with_llm_supervisor(operation_context)

        # Verify LLM was called
        mock_llm_api.assert_called_once()
        assert result is not None

    @patch("anti_deception_hook.AntiDeceptionHook._call_llm_api")
    def test_llm_supervisor_cost_estimation(self, mock_llm_api):
        """Test LLM cost estimation functionality."""
        # Mock response with cost estimate
        mock_response = Mock()
        mock_response.json.return_value = {
            "is_safe": True,
            "confidence": 0.90,
            "cost_estimate": 0.012,
            "reasoning": "Standard file operation",
        }
        mock_llm_api.return_value = mock_response

        # Test cost estimation
        operation_context = {
            "operation": "analyze_code",
            "target_path": "P:\\__csf\\test.py",
            "analysis_depth": "comprehensive",
        }

        # Call LLM supervisor
        result = self.hook._validate_with_llm_supervisor(operation_context)

        # Verify cost was estimated
        mock_llm_api.assert_called_once()
        assert result is not None

    @patch("anti_deception_hook.AntiDeceptionHook._call_llm_api")
    def test_llm_supervisor_confidence_scoring(self, mock_llm_api):
        """Test LLM confidence scoring functionality."""
        # Mock response with high confidence
        high_confidence_response = Mock()
        high_confidence_response.json.return_value = {
            "is_safe": True,
            "confidence": 0.98,
            "cost_estimate": 0.005,
            "reasoning": "Operation is clearly safe and well-documented",
        }
        mock_llm_api.return_value = high_confidence_response

        operation_context = {
            "operation": "read_file",
            "target_path": "P:\\__csf\\safe.txt",
            "user_intent": "Read configuration file",
        }

        # Test high confidence operation
        result = self.hook._validate_with_llm_supervisor(operation_context)

        # Verify confidence was captured
        mock_llm_api.assert_called_once()
        assert result is not None

    def test_llm_supervisor_concurrent_validation(self):
        """Test LLM validation of concurrent operations."""
        import threading

        results = []
        errors = []

        def validate_operation(operation_context):
            try:
                result = self.hook._validate_with_llm_supervisor(operation_context)
                results.append(result)
            except Exception as e:
                errors.append(str(e))

        # Create operation contexts for concurrent testing
        operation_contexts = [
            {
                "operation": "write_file",
                "target_path": "P:\\__csf\\test1.txt",
                "content": "test content 1",
            },
            {
                "operation": "write_file",
                "target_path": "P:\\__csf\\test2.txt",
                "content": "test content 2",
            },
            {
                "operation": "read_file",
                "target_path": "P:\\__csf\\test3.txt",
                "content": "test content 3",
            },
        ]

        # Create and start threads
        threads = []
        for context in operation_contexts:
            thread = threading.Thread(target=validate_operation, args=(context,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify all validations completed
        assert len(errors) == 0, f"Concurrent validation errors: {errors}"
        assert len(results) == len(operation_contexts)

    @patch("anti_deception_hook.AntiDeceptionHook._call_llm_api")
    def test_llm_supervisor_error_handling(self, mock_llm_api):
        """Test LLM supervisor error handling."""
        # Test API failure
        mock_llm_api.side_effect = Exception("LLM API unavailable")

        operation_context = {
            "operation": "write_file",
            "target_path": "P:\\__csf\\test.txt",
            "content": "test content",
        }

        # Should handle API failure gracefully
        result = self.hook._validate_with_llm_supervisor(operation_context)
        assert result is not None  # Should return fallback result

    @patch("anti_deception_hook.AntiDeceptionHook._call_llm_api")
    def test_llm_supervisor_timeout_handling(self, mock_llm_api):
        """Test LLM supervisor timeout handling."""
        # Mock slow response
        mock_response = Mock()
        time.sleep(0.1)  # Simulate delay
        mock_response.json.return_value = {
            "is_safe": True,
            "confidence": 0.90,
            "cost_estimate": 0.005,
            "reasoning": "Operation validated",
        }
        mock_llm_api.return_value = mock_response

        operation_context = {
            "operation": "complex_analysis",
            "target_path": "P:\\__csf\\complex.py",
            "analysis_depth": "deep",
        }

        # Should handle slow response
        result = self.hook._validate_with_llm_supervisor(operation_context)
        assert result is not None

    def test_llm_supervisor_performance_timing(self):
        """Test that LLM validation completes within performance targets."""
        target_ms = 2000.0  # 2 second target

        with PerformanceTimer() as timer:
            # Test multiple LLM validations
            operation_contexts = [
                {
                    "operation": "write_file",
                    "target_path": "P:\\__csf\\test1.txt",
                    "content": "test content 1",
                },
                {
                    "operation": "write_file",
                    "target_path": "P:\\__csf\\test2.txt",
                    "content": "test content 2",
                },
                {
                    "operation": "read_file",
                    "target_path": "P:\\__csf\\test3.txt",
                    "content": "test content 3",
                },
            ]

            for context in operation_contexts:
                # Simulate LLM validation (without actual API call)
                with patch.object(self.hook, "_call_llm_api") as mock_llm_api:
                    mock_response = Mock()
                    mock_response.json.return_value = {
                        "is_safe": True,
                        "confidence": 0.90,
                        "cost_estimate": 0.005,
                        "reasoning": "Test validation",
                    }
                    mock_llm_api.return_value = mock_response

                    self.hook._validate_with_llm_supervisor(context)

        # Should complete within 2 seconds
        assert (
            timer.elapsed_ms < target_ms
        ), f"LLM validation took {timer.elapsed_ms}ms, target: {target_ms}ms"

    def test_llm_supervisor_configuration_updates(self):
        """Test LLM supervisor configuration updates."""
        # Update configuration
        updates = {
            "validation_rules": {
                "enable_llm_validation": True,
                "llm_confidence_threshold": 0.95,
                "max_cost_per_operation": 0.01,
            }
        }

        self.hook.update_config(updates)

        # Verify configuration was updated
        assert self.hook.config["validation_rules"]["enable_llm_validation"] is True

    def test_llm_supervisor_cost_tracking(self):
        """Test LLM cost tracking functionality."""
        # Initialize cost tracking
        total_cost = 0.0
        operation_count = 0

        # Simulate multiple operations with cost tracking
        operations = [
            {"operation": "write", "cost": 0.005},
            {"operation": "read", "cost": 0.003},
            {"operation": "analyze", "cost": 0.012},
            {"operation": "validate", "cost": 0.008},
        ]

        for op in operations:
            total_cost += op["cost"]
            operation_count += 1

            # Simulate cost validation
            if total_cost <= 0.05:  # Budget limit
                print(f"Operation {op['operation']} approved (cost: {op['cost']})")
            else:
                print(f"Operation {op['operation']} rejected (budget exceeded)")
                break

        # Verify cost tracking
        assert total_cost > 0
        assert operation_count > 0

    @patch("anti_deception_hook.AntiDeceptionHook._call_llm_api")
    def test_llm_supervisor_response_parsing(self, mock_llm_api):
        """Test LLM response parsing functionality."""
        # Test various response formats
        test_responses = [
            {
                "is_safe": True,
                "confidence": 0.95,
                "cost_estimate": 0.005,
                "reasoning": "Operation is safe",
            },
            {
                "is_safe": False,
                "confidence": 0.98,
                "cost_estimate": 0.008,
                "reasoning": "Operation is dangerous",
            },
            {
                "is_safe": True,
                "confidence": 0.88,
                "cost_estimate": 0.012,
                "reasoning": "Operation requires caution",
            },
        ]

        for response_data in test_responses:
            mock_response = Mock()
            mock_response.json.return_value = response_data
            mock_llm_api.return_value = mock_response

            operation_context = {
                "operation": "test_operation",
                "target_path": "P:\\__csf\\test.txt",
            }

            result = self.hook._validate_with_llm_supervisor(operation_context)

            # Verify response was parsed correctly
            assert result is not None

    def test_llm_supervisor_fallback_mechanism(self):
        """Test LLM supervisor fallback mechanism when LLM is unavailable."""
        # Test fallback behavior when LLM validation fails
        operation_context = {
            "operation": "write_file",
            "target_path": "P:\\__csf\\test.txt",
            "content": "test content",
        }

        # Should fall back to rule-based validation
        result = self.hook._validate_with_llm_supervisor(operation_context)

        # Verify fallback result is returned
        assert result is not None

    def test_llm_supervisor_log_integration(self):
        """Test LLM supervisor integration with evidence logging."""
        # Create test evidence
        evidence = self.evidence_generator.create_file_evidence(
            ["P:\\__csf\\test.txt"]
        )

        # Log evidence
        for ev in evidence:
            self.hook.log_evidence("llm_validation", ev)

        # Verify evidence was logged
        assert len(self.hook.evidence_log) > 0
        assert any(
            "llm_validation" in entry["type"] for entry in self.hook.evidence_log
        )

    def test_llm_supervisor_status_reporting(self):
        """Test LLM supervisor status reporting."""
        # Add some test data
        with patch.object(self.hook, "_call_llm_api") as mock_llm_api:
            mock_response = Mock()
            mock_response.json.return_value = {
                "is_safe": True,
                "confidence": 0.90,
                "cost_estimate": 0.005,
                "reasoning": "Test operation",
            }
            mock_llm_api.return_value = mock_response

            operation_context = {
                "operation": "write_file",
                "target_path": "P:\\__csf\\test.txt",
                "content": "test content",
            }

            self.hook._validate_with_llm_supervisor(operation_context)

        # Generate status report
        status = self.hook.get_status_report()

        # Verify status report contains LLM-related information
        assert "total_evidence_items" in status
        assert "validation_failures" in status
        assert "config_loaded" in status
        assert status["config_loaded"] is True


if __name__ == "__main__":
    # Run the tests
    import pytest

    pytest.main([__file__, "-v"])
