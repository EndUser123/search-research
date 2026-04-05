"""
Mock LLM Testing Package

This package provides comprehensive testing infrastructure for LLM integration
with controlled responses, cost validation, and performance benchmarking.

Package Structure:
- test_llm_controlled_responses.py: Basic LLM response testing and controlled scenarios
- test_llm_cost_validation.py: Cost estimation, budget management, and optimization
- mock_llm_utils.py: Utility classes and helpers for LLM testing
"""

import asyncio
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from unittest.mock import AsyncMock, Mock, patch

import pytest

from anti_deception_enhanced.hooks import AntiDeceptionHook
from anti_deception_enhanced.hooks.llm_supervisor import (
    CostBudget,
    LLMResponse,
    LLMSupervisor,
)
from anti_deception_enhanced.utils.evidence import EvidenceEntry, EvidenceLevel


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

    def to_response(self) -> "MockLLMResponse":
        """Convert scenario to mock response"""
        return MockLLMResponse(
            content=self.controlled_response,
            confidence_score=self.expected_confidence,
            estimated_cost=self.expected_cost,
            validation_result=self.expected_validation,
            response_time=self.response_delay,
        )


@dataclass
class CostTestScenario:
    """Test scenario for cost validation"""

    name: str
    user_prompt: str
    estimated_cost: float
    actual_cost: float
    confidence_score: float
    validation_result: bool
    budget_remaining: float
    cost_efficiency: float = 1.0

    def get_cost_variance(self) -> float:
        """Calculate cost variance"""
        return abs(self.actual_cost - self.estimated_cost) / self.estimated_cost


@dataclass
class CostBudgetScenario:
    """Test scenario for budget management"""

    name: str
    initial_budget: float
    cost_estimates: list[float]
    expected_overrides: list[bool]
    expected_remaining: float
    priority_handling: str = "standard"


class MockLLMResponse:
    """Mock LLM response for testing"""

    def __init__(
        self,
        content: str,
        confidence_score: float,
        estimated_cost: float,
        validation_result: bool,
        response_time: float = 0.1,
    ):
        self.content = content
        self.confidence_score = confidence_score
        self.estimated_cost = estimated_cost
        self.validation_result = validation_result
        self.response_time = response_time

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return {
            "content": self.content,
            "confidence_score": self.confidence_score,
            "estimated_cost": self.estimated_cost,
            "validation_result": self.validation_result,
            "response_time": self.response_time,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MockLLMResponse":
        """Create from dictionary"""
        return cls(
            content=data.get("content", ""),
            confidence_score=data.get("confidence_score", 0.0),
            estimated_cost=data.get("estimated_cost", 0.0),
            validation_result=data.get("validation_result", False),
            response_time=data.get("response_time", 0.1),
        )


class MockLLMSupervisor:
    """Mock LLM Supervisor for testing"""

    def __init__(self):
        self.current_scenario: TestLLMScenario | None = None
        self.cost_budget: CostBudget | None = None
        self.response_history: list[LLMResponse] = []
        self.cost_history: list[float] = []

    def set_scenario(self, scenario: TestLLMScenario):
        """Set current test scenario"""
        self.current_scenario = scenario

    def set_budget(self, budget: CostBudget):
        """Set budget for testing"""
        self.cost_budget = budget

    def validate_user_input(self, user_prompt: str) -> LLMResponse:
        """Validate user input with controlled response"""
        if not self.current_scenario:
            # Default response
            return LLMResponse(
                content="Default safe response",
                confidence_score=0.80,
                estimated_cost=0.002,
                validation_result=True,
                response_time=0.1,
            )

        # Simulate response delay
        time.sleep(self.current_scenario.response_delay)

        # Create response
        response = LLMResponse(
            content=self.current_scenario.controlled_response,
            confidence_score=self.current_scenario.expected_confidence,
            estimated_cost=self.current_scenario.expected_cost,
            validation_result=self.current_scenario.expected_validation,
            response_time=self.current_scenario.response_delay,
        )

        # Track history
        self.response_history.append(response)
        self.cost_history.append(response.estimated_cost)

        return response

    def estimate_cost(self, prompt: str) -> float:
        """Estimate cost for prompt"""
        # Simple cost estimation based on prompt length and complexity
        base_cost = 0.001
        length_factor = len(prompt) / 100
        complexity_factor = 1.0

        if any(
            word in prompt.lower()
            for word in ["generate", "create", "analyze", "implement"]
        ):
            complexity_factor = 1.5

        return base_cost * (1 + length_factor) * complexity_factor

    def format_message_for_llm(self, user_message: str) -> str:
        """Format message for LLM"""
        # Simple formatting logic for testing
        if "delete" in user_message.lower() and "file" in user_message.lower():
            return "dangerous_request"
        elif any(word in user_message.lower() for word in ["hello", "hi", "hey"]):
            return "greeting"
        elif "function" in user_message.lower() or "class" in user_message.lower():
            return "code_generation"
        else:
            return "user_query"

    def detect_request_priority(self, user_message: str) -> str:
        """Detect request priority"""
        if "urgent" in user_message.lower() or "critical" in user_message.lower():
            return "high"
        elif "background" in user_message.lower() or "routine" in user_message.lower():
            return "low"
        else:
            return "medium"

    def validate_cost_threshold(self, cost: float, thresholds: dict[str, float]) -> str:
        """Validate cost against thresholds"""
        if cost > thresholds.get("critical_cost_threshold", 0.020):
            return "critical"
        elif cost > thresholds.get("high_cost_threshold", 0.010):
            return "high"
        elif cost > thresholds.get("medium_cost_threshold", 0.005):
            return "medium"
        elif cost > thresholds.get("low_cost_threshold", 0.001):
            return "low"
        else:
            return "low"

    def determine_enforcement_action(self, cost: float, threshold: float) -> str:
        """Determine enforcement action"""
        try:
            if cost is None or threshold is None:
                return "allow"

            if isinstance(cost, str) or isinstance(threshold, str):
                return "allow"

            if cost <= threshold * 0.8:
                return "allow"
            elif cost <= threshold:
                return "warn"
            else:
                return "reject"
        except (TypeError, ValueError):
            return "allow"

    def generate_cost_report(self, cost_data: dict[str, Any]) -> dict[str, Any]:
        """Generate cost report"""
        report = cost_data.copy()

        # Add cost trends
        if "costs" in cost_data:
            costs = cost_data["costs"]
            report["cost_trends"] = {
                "average_cost": sum(costs) / len(costs) if costs else 0,
                "max_cost": max(costs) if costs else 0,
                "min_cost": min(costs) if costs else 0,
                "cost_variance": max(costs) - min(costs) if len(costs) > 1 else 0,
            }

        # Add recommendations
        report["recommendations"] = []
        if cost_data.get("usage_percentage", 0) > 80:
            report["recommendations"].append("Consider increasing budget")
        if cost_data.get("average_cost", 0) > 0.005:
            report["recommendations"].append("Optimize prompt length")
        if len(cost_data.get("costs", [])) > 100:
            report["recommendations"].append("Implement caching")

        return report


# Pytest fixtures
@pytest.fixture
def mock_llm_supervisor():
    """Fixture for MockLLMSupervisor"""
    return MockLLMSupervisor()


@pytest.fixture
def test_scenarios():
    """Fixture for test scenarios"""
    return [
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
    ]


@pytest.fixture
def budget_scenarios():
    """Fixture for budget scenarios"""
    return [
        CostBudgetScenario(
            name="small_budget",
            initial_budget=0.01,
            cost_estimates=[0.002, 0.003, 0.001, 0.004],
            expected_overrides=[False, False, False, True],
            expected_remaining=0.003,
        ),
        CostBudgetScenario(
            name="medium_budget",
            initial_budget=0.05,
            cost_estimates=[0.003, 0.007, 0.004, 0.006, 0.002],
            expected_overrides=[False, False, False, False, False],
            expected_remaining=0.028,
        ),
    ]


@pytest.fixture
def cost_thresholds():
    """Fixture for cost thresholds"""
    return {
        "low_cost_threshold": 0.001,
        "medium_cost_threshold": 0.005,
        "high_cost_threshold": 0.010,
        "critical_cost_threshold": 0.020,
    }


# Test configuration
TEST_CONFIG = {
    "max_response_time": 1.0,
    "max_cost_variance": 0.20,
    "min_confidence_threshold": 0.70,
    "budget_warning_threshold": 0.80,
    "budget_critical_threshold": 0.95,
    "concurrent_requests": 5,
    "max_concurrent_time": 2.0,
}


# Test markers
pytest.mark.llm_testing = pytest.mark.filterwarnings(
    "ignore::pytest.PytestUnhandledThreadExceptionWarning"
)
pytest.mark.cost_testing = pytest.mark.filterwarnings(
    "ignore::pytest.PytestUnhandledThreadExceptionWarning"
)
pytest.mark.performance_testing = pytest.mark.filterwarnings(
    "ignore::pytest.PytestUnhandledThreadExceptionWarning"
)


# Test helpers
def validate_llm_response(
    response: LLMResponse,
    expected_confidence: float,
    expected_cost: float,
    expected_validation: bool,
):
    """Validate LLM response against expected values"""
    assert response.confidence_score == expected_confidence
    assert abs(response.estimated_cost - expected_cost) < 0.001
    assert response.validation_result == expected_validation


def validate_cost_variance(
    actual_cost: float, estimated_cost: float, max_variance: float = 0.20
):
    """Validate cost variance within acceptable range"""
    variance = abs(actual_cost - estimated_cost) / estimated_cost
    assert variance <= max_variance, f"Cost variance too high: {variance}"


def validate_budget_allocation(
    budget: CostBudget, allocated_costs: list[float], expected_success: list[bool]
):
    """Validate budget allocation results"""
    results = []
    for cost in allocated_costs:
        success = budget.allocate_cost(cost)
        results.append(success)

    assert results == expected_success
    return results


def run_concurrent_llm_requests(
    supervisor: MockLLMSupervisor, prompts: list[str], max_workers: int = 3
) -> list[LLMResponse]:
    """Run concurrent LLM requests"""
    results = []

    def make_request(prompt):
        scenario = TestLLMScenario(
            name=f"concurrent_{prompt[:10].lower().replace(' ', '_')}",
            user_prompt=prompt,
            controlled_response=f"Concurrent response for {prompt}",
            expected_confidence=0.85,
            expected_cost=0.002,
            expected_validation=True,
        )
        supervisor.set_scenario(scenario)
        return supervisor.validate_user_input(prompt)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_prompt = {
            executor.submit(make_request, prompt): prompt for prompt in prompts
        }

        for future in as_completed(future_to_prompt):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                pytest.fail(f"Concurrent request failed: {e}")

    return results


# Test data generators
def generate_test_prompts():
    """Generate test prompts for various scenarios"""
    return [
        "Hello",
        "Create a Python function",
        "Generate a report",
        "Analyze data",
        "Delete files",
        "Read configuration",
        "Write to system files",
        "Create backup",
    ]


def generate_cost_test_data():
    """Generate cost test data"""
    return [
        ("simple", 0.001),
        ("basic", 0.002),
        ("moderate", 0.004),
        ("complex", 0.008),
        ("highly_complex", 0.015),
    ]


# Performance utilities
def measure_llm_performance(
    supervisor: MockLLMSupervisor, prompt: str, iterations: int = 10
) -> dict[str, float]:
    """Measure LLM performance metrics"""
    times = []
    costs = []
    confidences = []

    for _ in range(iterations):
        start_time = time.time()
        scenario = TestLLMScenario(
            name="perf_test",
            user_prompt=prompt,
            controlled_response="Performance test response",
            expected_confidence=0.85,
            expected_cost=0.002,
            expected_validation=True,
        )
        supervisor.set_scenario(scenario)

        result = supervisor.validate_user_input(prompt)
        end_time = time.time()

        times.append(end_time - start_time)
        costs.append(result.estimated_cost)
        confidences.append(result.confidence_score)

    return {
        "avg_time": sum(times) / len(times),
        "avg_cost": sum(costs) / len(costs),
        "avg_confidence": sum(confidences) / len(confidences),
        "max_time": max(times),
        "min_time": min(times),
        "time_std": (
            sum((t - sum(times) / len(times)) ** 2 for t in times) / len(times)
        )
        ** 0.5,
    }


# Cleanup utilities
def cleanup_llm_testing(supervisor: MockLLMSupervisor):
    """Clean up LLM testing state"""
    supervisor.response_history.clear()
    supervisor.cost_history.clear()
    supervisor.current_scenario = None
    supervisor.cost_budget = None


# Integration test helpers
def test_llm_communication_integration(
    hook: AntiDeceptionHook, supervisor: MockLLMSupervisor
):
    """Test LLM integration with communication system"""
    test_cases = [
        ("Hello, can you help me?", True),
        ("Delete all files", False),
        ("Create a Python function", True),
        ("sudo rm -rf /", False),
    ]

    for prompt, expected_validation in test_cases:
        scenario = TestLLMScenario(
            name=f"comm_{prompt[:10].lower().replace(' ', '_')}",
            user_prompt=prompt,
            controlled_response="Integration test response",
            expected_confidence=0.85,
            expected_cost=0.002,
            expected_validation=expected_validation,
        )
        supervisor.set_scenario(scenario)

        # Test validation
        result = supervisor.validate_user_input(prompt)
        assert result.validation_result == expected_validation


def test_llm_hook_coordination(hook: AntiDeceptionHook, supervisor: MockLLMSupervisor):
    """Test LLM coordination with other hooks"""
    test_scenarios = [
        ("Create a safe file", True, True),
        ("Delete system files", False, False),
        ("Read config file", True, True),
    ]

    for user_input, expected_pre_tool, expected_llm in test_scenarios:
        # Setup LLM scenario
        llm_scenario = TestLLMScenario(
            name=f"coord_{user_input[:10].lower().replace(' ', '_')}",
            user_prompt=user_input,
            controlled_response="Coordinated response",
            expected_confidence=0.85,
            expected_cost=0.002,
            expected_validation=expected_llm,
        )
        supervisor.set_scenario(llm_scenario)

        # Test coordination
        pre_tool_result = hook.pre_tool_use.validate_file_path(user_input)
        llm_result = supervisor.validate_user_input(user_input)

        # Validate consistency
        assert pre_tool_result.validation_result == expected_pre_tool
        assert llm_result.validation_result == expected_llm

        # Test combined validation
        overall_validation = (
            pre_tool_result.validation_result and llm_result.validation_result
        )
        assert overall_validation == (expected_pre_tool and expected_llm)


# Test configuration
PYTEST_CONFIG = {
    "addopts": "-v --tb=short --strict-markers",
    "testpaths": ["."],
    "python_files": ["test_*.py"],
    "python_classes": ["Test*"],
    "python_functions": ["test_*"],
    "markers": {
        "llm_testing": "LLM testing markers",
        "cost_testing": "Cost testing markers",
        "performance_testing": "Performance testing markers",
        "slow": "Slow running tests",
        "integration": "Integration tests",
    },
}


__all__ = [
    "MockLLMResponse",
    "MockLLMSupervisor",
    "TestLLMScenario",
    "CostTestScenario",
    "CostBudgetScenario",
    "validate_llm_response",
    "validate_cost_variance",
    "validate_budget_allocation",
    "run_concurrent_llm_requests",
    "generate_test_prompts",
    "generate_cost_test_data",
    "measure_llm_performance",
    "cleanup_llm_testing",
    "test_llm_communication_integration",
    "test_llm_hook_coordination",
]
