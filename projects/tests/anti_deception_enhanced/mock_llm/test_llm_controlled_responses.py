"""
Mock LLM Testing with Controlled Responses

This module implements comprehensive testing for the LLM Supervisor integration
with controlled responses and cost validation. It tests various LLM response patterns,
cost estimation accuracy, confidence scoring, and error handling.

Test Categories:
1. Basic LLM Response Testing
2. Cost Estimation Validation
3. Confidence Scoring Tests
4. Response Pattern Scenarios
5. Error Handling and Recovery
6. Performance Benchmarking
7. Integration with Communication System
8. Cross-Hook LLM Coordination
"""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from unittest.mock import patch

import pytest

from anti_deception_enhanced.hooks import AntiDeceptionHook
from anti_deception_enhanced.hooks.llm_supervisor import LLMResponse
from anti_deception_enhanced.utils.evidence import EvidenceEntry, EvidenceLevel
from anti_deception_enhanced.utils.mock_llm import MockLLMResponse, MockLLMSupervisor
from anti_deception_enhanced.utils.performance import PerformanceTimer


@dataclass
class TestLLMScenario:
    """Test scenario configuration for controlled LLM responses"""

    name: str
    user_prompt: str
    controlled_response: str
    expected_confidence: float
    expected_cost: float
    expected_validation: bool
    risk_level: str = "medium"
    response_delay: float = 0.1

    def to_response(self) -> MockLLMResponse:
        """Convert scenario to mock response"""
        return MockLLMResponse(
            content=self.controlled_response,
            confidence_score=self.expected_confidence,
            estimated_cost=self.expected_cost,
            validation_result=self.expected_validation,
            response_time=self.response_delay,
        )


class TestLLMResponseValidation:
    """Test basic LLM response validation and parsing"""

    def test_valid_llm_response_parsing(self):
        """Test parsing of valid LLM response"""
        response_data = {
            "content": "This is a safe operation",
            "confidence": 0.95,
            "cost": 0.002,
            "validation": True,
            "timestamp": time.time(),
        }

        response = LLMResponse.from_dict(response_data)
        assert response.content == response_data["content"]
        assert response.confidence_score == response_data["confidence"]
        assert response.estimated_cost == response_data["cost"]
        assert response.validation_result == response_data["validation"]

    def test_llm_response_validation_failure(self):
        """Test handling of invalid LLM response data"""
        invalid_responses = [
            {"content": "test", "confidence": 1.5},  # Invalid confidence
            {"content": "test", "cost": -0.001},  # Invalid cost
            {"content": "test", "validation": "yes"},  # Invalid validation type
            {"missing_content": "value"},  # Missing required field
            {},  # Empty response
            None,  # None response
        ]

        for invalid_data in invalid_responses:
            with pytest.raises((ValueError, KeyError, TypeError)):
                LLMResponse.from_dict(invalid_data)

    def test_llm_response_serialization(self):
        """Test LLM response serialization to dict"""
        original_response = LLMResponse(
            content="Test content",
            confidence_score=0.85,
            estimated_cost=0.003,
            validation_result=True,
            response_time=0.2,
        )

        serialized = original_response.to_dict()
        deserialized = LLMResponse.from_dict(serialized)

        assert deserialized.content == original_response.content
        assert deserialized.confidence_score == original_response.confidence_score
        assert deserialized.estimated_cost == original_response.estimated_cost
        assert deserialized.validation_result == original_response.validation_result


class TestControlledLLMResponses:
    """Test LLM supervisor with controlled response scenarios"""

    def setup_method(self):
        """Setup test environment"""
        self.mock_supervisor = MockLLMSupervisor()
        self.test_scenarios = [
            TestLLMScenario(
                name="safe_operation",
                user_prompt="Create a simple Python function",
                controlled_response="I'll create a safe Python function for you.",
                expected_confidence=0.95,
                expected_cost=0.002,
                expected_validation=True,
                risk_level="low",
            ),
            TestLLMScenario(
                name="potentially_unsafe",
                user_prompt="Delete all files in the current directory",
                controlled_response="I cannot delete all files as this could be dangerous.",
                expected_confidence=0.90,
                expected_cost=0.003,
                expected_validation=False,
                risk_level="high",
            ),
            TestLLMScenario(
                name="mixed_content",
                user_prompt="Read config.json and modify settings",
                controlled_response="I can help you read the config file safely.",
                expected_confidence=0.80,
                expected_cost=0.0025,
                expected_validation=True,
                risk_level="medium",
            ),
            TestLLMScenario(
                name="high_risk_command",
                user_prompt="sudo rm -rf /",
                controlled_response="This command is extremely dangerous and cannot be executed.",
                expected_confidence=0.98,
                expected_cost=0.004,
                expected_validation=False,
                risk_level="critical",
            ),
        ]

    def test_scenarios_execution(self):
        """Test execution of controlled LLM response scenarios"""
        for scenario in self.test_scenarios:
            # Configure mock response
            self.mock_supervisor.set_scenario(scenario)

            # Execute LLM validation
            result = self.mock_supervisor.validate_user_input(scenario.user_prompt)

            # Validate response matches expected values
            assert result.confidence_score == scenario.expected_confidence
            assert abs(result.estimated_cost - scenario.expected_cost) < 0.001
            assert result.validation_result == scenario.expected_validation

    def test_cost_estimation_accuracy(self):
        """Test cost estimation accuracy across different scenarios"""
        cost_test_cases = [
            ("Simple request", "Hello", 0.001, 0.0005),
            ("Complex request", "Write a detailed analysis", 0.005, 0.002),
            ("Code generation", "Generate Python class", 0.003, 0.0015),
            ("File operation", "Read and analyze file", 0.002, 0.001),
            ("Multiple steps", "Create function and test it", 0.004, 0.002),
        ]

        for description, prompt, expected_cost, tolerance in cost_test_cases:
            self.mock_supervisor.set_scenario(
                TestLLMScenario(
                    name=description.lower().replace(" ", "_"),
                    user_prompt=prompt,
                    controlled_response="Mock response",
                    expected_confidence=0.85,
                    expected_cost=expected_cost,
                    expected_validation=True,
                )
            )

            result = self.mock_supervisor.validate_user_input(prompt)
            cost_diff = abs(result.estimated_cost - expected_cost)
            assert (
                cost_diff <= tolerance
            ), f"Cost estimation error for {description}: {cost_diff}"

    def test_confidence_scoring_validation(self):
        """Test confidence scoring validation"""
        confidence_tests = [
            (0.99, "Very high confidence"),
            (0.95, "High confidence"),
            (0.85, "Medium confidence"),
            (0.75, "Low confidence"),
            (0.50, "Very low confidence"),
        ]

        for expected_confidence, description in confidence_tests:
            self.mock_supervisor.set_scenario(
                TestLLMScenario(
                    name=f"confidence_{description.lower().replace(' ', '_')}",
                    user_prompt=f"Test prompt for {description}",
                    controlled_response="Test response",
                    expected_confidence=expected_confidence,
                    expected_cost=0.002,
                    expected_validation=True,
                )
            )

            result = self.mock_supervisor.validate_user_input("Test prompt")
            assert result.confidence_score == expected_confidence

    def test_response_time_measurement(self):
        """Test response time measurement and performance"""
        time_scenarios = [
            (0.05, "Fast response"),
            (0.1, "Normal response"),
            (0.3, "Slow response"),
            (0.5, "Very slow response"),
        ]

        for response_time, description in time_scenarios:
            self.mock_supervisor.set_scenario(
                TestLLMScenario(
                    name=f"time_{description.lower().replace(' ', '_')}",
                    user_prompt="Test time measurement",
                    controlled_response="Time test response",
                    expected_confidence=0.90,
                    expected_cost=0.002,
                    expected_validation=True,
                    response_delay=response_time,
                )
            )

            start_time = time.time()
            result = self.mock_supervisor.validate_user_input("Test time measurement")
            actual_time = time.time() - start_time

            assert actual_time >= response_time
            assert actual_time <= response_time * 2  # Allow some variance

    def test_concurrent_llm_requests(self):
        """Test handling of concurrent LLM requests"""
        concurrent_requests = [
            "Request 1: Create simple function",
            "Request 2: Analyze data",
            "Request 3: Generate report",
            "Request 4: Validate input",
            "Request 5: Process results",
        ]

        results = []

        def make_request(prompt):
            scenario = TestLLMScenario(
                name=f"concurrent_{prompt.split(':')[0].lower().replace(' ', '_')}",
                user_prompt=prompt,
                controlled_response=f"Response for {prompt}",
                expected_confidence=0.85,
                expected_cost=0.002,
                expected_validation=True,
            )
            self.mock_supervisor.set_scenario(scenario)
            return self.mock_supervisor.validate_user_input(prompt)

        # Execute concurrent requests
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_prompt = {
                executor.submit(make_request, prompt): prompt
                for prompt in concurrent_requests
            }

            for future in as_completed(future_to_prompt):
                prompt = future_to_prompt[future]
                try:
                    result = future.result()
                    results.append((prompt, result))
                except Exception as e:
                    pytest.fail(f"Concurrent request failed for {prompt}: {e}")

        # Validate all requests completed
        assert len(results) == len(concurrent_requests)

        # Validate individual results
        for prompt, result in results:
            assert result.validation_result is True
            assert result.confidence_score == 0.85
            assert result.estimated_cost == 0.002

    def test_llm_response_patterns(self):
        """Test various LLM response patterns"""
        response_patterns = [
            {
                "name": "affirmative_safe",
                "pattern": "I'll help you create a safe function",
                "expected_validation": True,
                "confidence_range": (0.90, 0.98),
            },
            {
                "name": "cautious_approach",
                "pattern": "I need to be careful here, let me check",
                "expected_validation": True,
                "confidence_range": (0.70, 0.85),
            },
            {
                "name": "direct_refusal",
                "pattern": "I cannot perform this action as it's unsafe",
                "expected_validation": False,
                "confidence_range": (0.95, 0.99),
            },
            {
                "name": "conditional_approval",
                "pattern": "I can help with this if you provide more context",
                "expected_validation": True,
                "confidence_range": (0.60, 0.80),
            },
            {
                "name": "uncertain_response",
                "pattern": "This might be okay, but I'm not sure",
                "expected_validation": False,
                "confidence_range": (0.30, 0.60),
            },
        ]

        for pattern in response_patterns:
            scenario = TestLLMScenario(
                name=pattern["name"],
                user_prompt=f"Test {pattern['name'].replace('_', ' ')}",
                controlled_response=pattern["pattern"],
                expected_confidence=sum(pattern["confidence_range"]) / 2,
                expected_cost=0.002,
                expected_validation=pattern["expected_validation"],
            )

            self.mock_supervisor.set_scenario(scenario)
            result = self.mock_supervisor.validate_user_input("Test prompt")

            # Validate confidence is within expected range
            assert (
                pattern["confidence_range"][0]
                <= result.confidence_score
                <= pattern["confidence_range"][1]
            )
            assert result.validation_result == pattern["expected_validation"]


class TestLLMErrorHandling:
    """Test LLM error handling and recovery scenarios"""

    def setup_method(self):
        """Setup test environment"""
        self.mock_supervisor = MockLLMSupervisor()

    def test_llm_timeout_handling(self):
        """Test handling of LLM timeout scenarios"""
        timeout_scenario = TestLLMScenario(
            name="timeout_scenario",
            user_prompt="Test timeout",
            controlled_response="Delayed response",
            expected_confidence=0.0,
            expected_cost=0.0,
            expected_validation=False,
            response_delay=2.0,  # Simulate timeout
        )

        self.mock_supervisor.set_scenario(timeout_scenario)

        # Mock timeout behavior
        with patch("time.sleep", side_effect=TimeoutError("LLM timeout")):
            with pytest.raises(TimeoutError):
                self.mock_supervisor.validate_user_input("Test timeout")

    def test_llm_api_error_handling(self):
        """Test handling of LLM API errors"""
        error_scenarios = [
            ("ConnectionError", "Connection failed"),
            ("APIError", "API limit exceeded"),
            ("RateLimitError", "Too many requests"),
            ("AuthenticationError", "Invalid API key"),
            ("ServerError", "Internal server error"),
        ]

        for error_type, error_message in error_scenarios:
            self.mock_supervisor.set_scenario(
                TestLLMScenario(
                    name=f"api_error_{error_type.lower()}",
                    user_prompt="Test API error",
                    controlled_response="API error response",
                    expected_confidence=0.0,
                    expected_cost=0.0,
                    expected_validation=False,
                )
            )

            # Simulate API error
            with patch("requests.post", side_effect=Exception(error_message)):
                result = self.mock_supervisor.validate_user_input("Test API error")

                # Should return safe default response
                assert result.confidence_score == 0.0
                assert result.estimated_cost == 0.0
                assert result.validation_result is False

    def test_llm_malformed_response_handling(self):
        """Test handling of malformed LLM responses"""
        malformed_responses = [
            '{"incomplete": "response"}',
            '{"content": "valid", "confidence": "not_a_number"}',
            '{"content": "valid", "cost": "invalid"}',
            '{"content": "valid", "validation": "not_boolean"}',
            "invalid json response",
            "",
            None,
        ]

        for malformed_response in malformed_responses:
            self.mock_supervisor.set_scenario(
                TestLLMScenario(
                    name=f"malformed_{malformed_response[:10]}",
                    user_prompt="Test malformed response",
                    controlled_response=malformed_response,
                    expected_confidence=0.0,
                    expected_cost=0.0,
                    expected_validation=False,
                )
            )

            result = self.mock_supervisor.validate_user_input("Test malformed response")

            # Should handle gracefully with safe defaults
            assert result.confidence_score == 0.0
            assert result.estimated_cost == 0.0
            assert result.validation_result is False


class TestLLMPerformanceBenchmarking:
    """Test LLM performance characteristics"""

    def setup_method(self):
        """Setup test environment"""
        self.mock_supervisor = MockLLMSupervisor()

    def test_llm_response_time_benchmarking(self):
        """Test LLM response time benchmarking"""
        test_prompts = [
            "Simple request",
            "Medium complexity request",
            "Complex analysis request",
            "Multi-step operation request",
        ]

        performance_results = []

        for prompt in test_prompts:
            scenario = TestLLMScenario(
                name=f"perf_{prompt.lower().replace(' ', '_')}",
                user_prompt=prompt,
                controlled_response=f"Response for {prompt}",
                expected_confidence=0.85,
                expected_cost=0.002,
                expected_validation=True,
            )

            self.mock_supervisor.set_scenario(scenario)

            # Measure performance
            with PerformanceTimer() as timer:
                result = self.mock_supervisor.validate_user_input(prompt)

            performance_results.append(
                {
                    "prompt": prompt,
                    "response_time": timer.elapsed,
                    "confidence": result.confidence_score,
                    "cost": result.estimated_cost,
                    "validation": result.validation_result,
                }
            )

        # Validate performance meets requirements
        for result in performance_results:
            assert (
                result["response_time"] < 1.0
            ), f"Response too slow: {result['response_time']}"
            assert result["confidence"] == 0.85
            assert result["cost"] == 0.002
            assert result["validation"] is True

    def test_concurrent_llm_performance(self):
        """Test concurrent LLM performance characteristics"""
        num_requests = 10
        test_prompt = "Concurrent test request"

        # Setup scenario
        scenario = TestLLMScenario(
            name="concurrent_performance_test",
            user_prompt=test_prompt,
            controlled_response="Concurrent response",
            expected_confidence=0.85,
            expected_cost=0.002,
            expected_validation=True,
            response_delay=0.1,  # Simulate network delay
        )
        self.mock_supervisor.set_scenario(scenario)

        # Execute concurrent requests
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(self.mock_supervisor.validate_user_input, test_prompt)
                for _ in range(num_requests)
            ]

            results = []
            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    pytest.fail(f"Concurrent request failed: {e}")

        total_time = time.time() - start_time
        avg_time_per_request = total_time / num_requests

        # Validate performance
        assert len(results) == num_requests
        assert (
            avg_time_per_request < 0.5
        ), f"Average time too high: {avg_time_per_request}"
        assert total_time < 2.0, f"Total time too high: {total_time}"

        # Validate all results are correct
        for result in results:
            assert result.confidence_score == 0.85
            assert result.estimated_cost == 0.002
            assert result.validation_result is True


class TestLLMCommunicationIntegration:
    """Test LLM integration with communication system"""

    def setup_method(self):
        """Setup test environment"""
        self.mock_supervisor = MockLLMSupervisor()

    def test_llm_communication_message_format(self):
        """Test LLM communication message format validation"""
        test_cases = [
            {
                "user_message": "Hello, can you help me?",
                "expected_llm_format": "user_query",
                "expected_validation": True,
            },
            {
                "user_message": "Delete all files",
                "expected_llm_format": "dangerous_request",
                "expected_validation": False,
            },
            {
                "user_message": "Create a Python function",
                "expected_llm_format": "code_generation",
                "expected_validation": True,
            },
            {
                "user_message": "sudo rm -rf /",
                "expected_llm_format": "system_command",
                "expected_validation": False,
            },
        ]

        for case in test_cases:
            scenario = TestLLMScenario(
                name=f"comm_{case['user_message'].lower().replace(' ', '_')}",
                user_prompt=case["user_message"],
                controlled_response="Test LLM response",
                expected_confidence=0.85,
                expected_cost=0.002,
                expected_validation=case["expected_validation"],
            )

            self.mock_supervisor.set_scenario(scenario)

            # Test message formatting
            formatted_message = self.mock_supervisor.format_message_for_llm(
                case["user_message"]
            )
            assert formatted_message == case["expected_llm_format"]

            # Test validation
            result = self.mock_supervisor.validate_user_input(case["user_message"])
            assert result.validation_result == case["expected_validation"]

    def test_llm_priority_handling(self):
        """Test LLM priority handling for different request types"""
        priority_test_cases = [
            ("urgent security alert", "high"),
            ("routine code generation", "medium"),
            "background analysis task",
            "low priority documentation",
        ]

        for case in priority_test_cases:
            if isinstance(case, tuple):
                message, expected_priority = case
            else:
                message = case
                expected_priority = "medium"

            scenario = TestLLMScenario(
                name=f"priority_{message.lower().replace(' ', '_')}",
                user_prompt=message,
                controlled_response=f"Response for {message}",
                expected_confidence=0.85,
                expected_cost=0.002,
                expected_validation=True,
            )

            self.mock_supervisor.set_scenario(scenario)

            # Test priority detection
            detected_priority = self.mock_supervisor.detect_request_priority(message)
            assert detected_priority == expected_priority

            # Test priority-based processing
            result = self.mock_supervisor.validate_user_input(message)
            assert result.validation_result is True


class TestLLMHookCoordination:
    """Test LLM coordination with other hooks"""

    def setup_method(self):
        """Setup test environment"""
        self.mock_supervisor = MockLLMSupervisor()
        self.hook = AntiDeceptionHook()

    def test_llm_pre_tool_use_coordination(self):
        """Test LLM coordination with Pre-Tool Use hook"""
        test_scenarios = [
            {
                "user_input": "Create a safe file",
                "expected_pre_tool_validation": True,
                "expected_llm_validation": True,
                "expected_overall_validation": True,
            },
            {
                "user_input": "Delete system files",
                "expected_pre_tool_validation": False,
                "expected_llm_validation": False,
                "expected_overall_validation": False,
            },
            {
                "user_input": "Read config file",
                "expected_pre_tool_validation": True,
                "expected_llm_validation": True,
                "expected_overall_validation": True,
            },
        ]

        for scenario in test_scenarios:
            # Setup LLM scenario
            llm_scenario = TestLLMScenario(
                name=f"coord_{scenario['user_input'].lower().replace(' ', '_')}",
                user_prompt=scenario["user_input"],
                controlled_response="Coordinated response",
                expected_confidence=0.85,
                expected_cost=0.002,
                expected_validation=scenario["expected_llm_validation"],
            )
            self.mock_supervisor.set_scenario(llm_scenario)

            # Test coordination
            pre_tool_result = self.hook.pre_tool_use.validate_file_path(
                scenario["user_input"]
            )
            llm_result = self.mock_supervisor.validate_user_input(
                scenario["user_input"]
            )

            # Validate consistency
            assert (
                pre_tool_result.validation_result
                == scenario["expected_pre_tool_validation"]
            )
            assert llm_result.validation_result == scenario["expected_llm_validation"]

            # Test combined validation
            overall_validation = (
                pre_tool_result.validation_result and llm_result.validation_result
            )
            assert overall_validation == scenario["expected_overall_validation"]

    def test_llm_post_tool_use_coordination(self):
        """Test LLM coordination with Post-Tool Use hook"""
        test_evidence = [
            {
                "operation": "file_created",
                "content": "Created safe file",
                "expected_llm_validation": True,
            },
            {
                "operation": "system_modified",
                "content": "Modified system configuration",
                "expected_llm_validation": False,
            },
            {
                "operation": "data_processed",
                "content": "Processed user data",
                "expected_llm_validation": True,
            },
        ]

        for evidence in test_evidence:
            # Setup LLM scenario
            llm_scenario = TestLLMScenario(
                name=f"post_coord_{evidence['operation'].lower()}",
                user_prompt=evidence["operation"],
                controlled_response="Post-operation validation",
                expected_confidence=0.85,
                expected_cost=0.002,
                expected_validation=evidence["expected_llm_validation"],
            )
            self.mock_supervisor.set_scenario(llm_scenario)

            # Create evidence entry
            evidence_entry = EvidenceEntry(
                operation=evidence["operation"],
                content=evidence["content"],
                level=EvidenceLevel.INFO,
                metadata={"source": "test"},
            )

            # Test coordination
            post_tool_result = self.hook.post_tool_use.collect_evidence(evidence_entry)
            llm_result = self.mock_supervisor.validate_user_input(evidence["operation"])

            # Validate consistency
            assert llm_result.validation_result == evidence["expected_llm_validation"]
            assert (
                post_tool_result.validation_result
                == evidence["expected_llm_validation"]
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
