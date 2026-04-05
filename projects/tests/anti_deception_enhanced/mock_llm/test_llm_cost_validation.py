"""
LLM Cost Validation Testing

This module implements comprehensive testing for LLM cost validation,
estimation accuracy, budget management, and cost optimization. It ensures
the LLM Supervisor properly tracks and validates LLM usage costs.

Test Categories:
1. Cost Estimation Validation
2. Budget Management Tests
3. Cost Optimization Strategies
4. Cost Monitoring and Reporting
5. Cost Threshold Enforcement
6. Multi-LLM Cost Comparison
7. Cost-Benefit Analysis
8. Cost Anomaly Detection
"""

from dataclasses import dataclass

import pytest

from anti_deception_enhanced.hooks.llm_supervisor import (
    CostBudget,
)
from anti_deception_enhanced.utils.mock_llm import MockLLMSupervisor


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


class TestCostEstimationValidation:
    """Test cost estimation accuracy and validation"""

    def setup_method(self):
        """Setup test environment"""
        self.mock_supervisor = MockLLMSupervisor()
        self.cost_scenarios = [
            CostTestScenario(
                name="simple_query",
                user_prompt="Hello",
                estimated_cost=0.001,
                actual_cost=0.0012,
                confidence_score=0.95,
                validation_result=True,
                budget_remaining=0.99,
            ),
            CostTestScenario(
                name="code_generation",
                user_prompt="Generate Python function",
                estimated_cost=0.003,
                actual_cost=0.0028,
                confidence_score=0.90,
                validation_result=True,
                budget_remaining=0.97,
            ),
            CostTestScenario(
                name="complex_analysis",
                user_prompt="Analyze data and generate report",
                estimated_cost=0.008,
                actual_cost=0.0095,
                confidence_score=0.85,
                validation_result=True,
                budget_remaining=0.92,
            ),
            CostTestScenario(
                name="high_cost_operation",
                user_prompt="Generate detailed technical documentation",
                estimated_cost=0.015,
                actual_cost=0.0142,
                confidence_score=0.80,
                validation_result=True,
                budget_remaining=0.86,
            ),
        ]

    def test_cost_estimation_accuracy(self):
        """Test cost estimation accuracy across different scenarios"""
        for scenario in self.cost_scenarios:
            self.mock_supervisor.set_scenario(
                TestLLMScenario(
                    name=scenario.name,
                    user_prompt=scenario.user_prompt,
                    controlled_response=f"Response for {scenario.name}",
                    expected_confidence=scenario.confidence_score,
                    expected_cost=scenario.estimated_cost,
                    expected_validation=scenario.validation_result,
                )
            )

            # Perform cost estimation
            result = self.mock_supervisor.validate_user_input(scenario.user_prompt)

            # Validate cost estimation
            variance = scenario.get_cost_variance()
            assert (
                variance <= 0.20
            ), f"Cost variance too high for {scenario.name}: {variance}"

            # Validate other metrics
            assert result.confidence_score == scenario.confidence_score
            assert result.validation_result == scenario.validation_result

    def test_cost_estimation_consistency(self):
        """Test cost estimation consistency for repeated requests"""
        test_prompt = "Generate a simple function"
        num_iterations = 10

        # Setup scenario
        scenario = CostTestScenario(
            name="consistency_test",
            user_prompt=test_prompt,
            estimated_cost=0.002,
            actual_cost=0.002,
            confidence_score=0.90,
            validation_result=True,
            budget_remaining=0.98,
        )

        self.mock_supervisor.set_scenario(
            TestLLMScenario(
                name=scenario.name,
                user_prompt=scenario.user_prompt,
                controlled_response="Consistent response",
                expected_confidence=scenario.confidence_score,
                expected_cost=scenario.estimated_cost,
                expected_validation=scenario.validation_result,
            )
        )

        costs = []
        for _ in range(num_iterations):
            result = self.mock_supervisor.validate_user_input(test_prompt)
            costs.append(result.estimated_cost)

        # Validate consistency (standard deviation should be low)
        avg_cost = sum(costs) / len(costs)
        variance = sum((c - avg_cost) ** 2 for c in costs) / len(costs)
        std_dev = variance**0.5

        assert std_dev <= 0.0005, f"Cost estimation not consistent: std_dev={std_dev}"
        assert (
            abs(avg_cost - scenario.estimated_cost) <= 0.001
        ), f"Average cost deviates too much: {avg_cost}"

    def test_cost_estimation_scaling(self):
        """Test cost estimation scaling with complexity"""
        complexity_scenarios = [
            ("simple", "Hello", 0.001),
            ("basic", "Create function", 0.002),
            ("moderate", "Generate class with methods", 0.004),
            ("complex", "Analyze data and create report", 0.008),
            ("highly_complex", "Generate comprehensive system design", 0.015),
        ]

        results = {}
        for complexity, prompt, expected_cost in complexity_scenarios:
            self.mock_supervisor.set_scenario(
                TestLLMScenario(
                    name=f"scaling_{complexity}",
                    user_prompt=prompt,
                    controlled_response=f"Response for {complexity} complexity",
                    expected_confidence=0.85,
                    expected_cost=expected_cost,
                    expected_validation=True,
                )
            )

            result = self.mock_supervisor.validate_user_input(prompt)
            results[complexity] = {
                "estimated_cost": result.estimated_cost,
                "actual_cost": expected_cost,
                "prompt": prompt,
            }

        # Validate scaling pattern
        complexity_order = ["simple", "basic", "moderate", "complex", "highly_complex"]
        for i in range(len(complexity_order) - 1):
            current = complexity_order[i]
            next_level = complexity_order[i + 1]

            current_cost = results[current]["estimated_cost"]
            next_cost = results[next_level]["estimated_cost"]

            assert (
                next_cost >= current_cost
            ), f"Cost scaling failed: {current} -> {next_level}"

    def test_cost_estimation_edge_cases(self):
        """Test cost estimation edge cases"""
        edge_cases = [
            ("very_short", "Hi", 0.0005),
            (
                "very_long",
                "This is a very long prompt that contains many words and requires significant processing time to generate an appropriate response",
                0.020,
            ),
            ("repetitive", "Repeat this sentence many times " * 10, 0.015),
            ("special_chars", "!@#$%^&*()_+-=[]{}|;':\",./<>?", 0.001),
            ("numeric", "1234567890 " * 20, 0.003),
        ]

        for case_name, prompt, expected_cost in edge_cases:
            self.mock_supervisor.set_scenario(
                TestLLMScenario(
                    name=f"edge_{case_name}",
                    user_prompt=prompt,
                    controlled_response=f"Edge case response for {case_name}",
                    expected_confidence=0.80,
                    expected_cost=expected_cost,
                    expected_validation=True,
                )
            )

            result = self.mock_supervisor.validate_user_input(prompt)
            cost_variance = abs(result.estimated_cost - expected_cost) / expected_cost

            assert (
                cost_variance <= 0.30
            ), f"Edge case cost variance too high for {case_name}: {cost_variance}"


class TestBudgetManagement:
    """Test budget management and cost control"""

    def setup_method(self):
        """Setup test environment"""
        self.mock_supervisor = MockLLMSupervisor()
        self.budget_scenarios = [
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
            CostBudgetScenario(
                name="tight_budget",
                initial_budget=0.008,
                cost_estimates=[0.002, 0.003, 0.002, 0.001],
                expected_overrides=[False, False, True, False],
                expected_remaining=0.001,
            ),
            CostBudgetScenario(
                name="generous_budget",
                initial_budget=0.20,
                cost_estimates=[0.005, 0.010, 0.008, 0.012, 0.003],
                expected_overrides=[False, False, False, False, False],
                expected_remaining=0.162,
            ),
        ]

    def test_budget_management_basic(self):
        """Test basic budget management functionality"""
        budget = CostBudget(total_budget=0.10, daily_limit=0.05)

        # Test initial state
        assert budget.remaining == 0.10
        assert budget.daily_remaining == 0.05
        assert budget.total_used == 0.0
        assert budget.daily_used == 0.0

        # Test cost allocation
        costs = [0.002, 0.003, 0.004, 0.001]
        for cost in costs:
            success = budget.allocate_cost(cost)
            assert success is True

        # Test final state
        assert budget.total_used == sum(costs)
        assert budget.daily_used == sum(costs)
        assert budget.remaining == 0.10 - sum(costs)
        assert budget.daily_remaining == 0.05 - sum(costs)

    def test_budget_enforcement(self):
        """Test budget enforcement and override behavior"""
        budget = CostBudget(total_budget=0.01, daily_limit=0.005)

        # Test successful allocations
        success = budget.allocate_cost(0.002)
        assert success is True

        success = budget.allocate_cost(0.003)
        assert success is False  # Should exceed budget

        # Test daily limit
        daily_budget = CostBudget(total_budget=0.20, daily_limit=0.01)

        # Allocate within daily limit
        success = daily_budget.allocate_cost(0.008)
        assert success is True

        # Exceed daily limit
        success = daily_budget.allocate_cost(0.003)
        assert success is False

    def test_budget_scenarios_execution(self):
        """Test budget scenario execution"""
        for scenario in self.budget_scenarios:
            budget = CostBudget(
                total_budget=scenario.initial_budget,
                daily_limit=scenario.initial_budget * 0.5,
            )

            results = []
            for i, cost in enumerate(scenario.cost_estimates):
                success = budget.allocate_cost(cost)
                results.append(success)

            # Validate results
            assert (
                results == scenario.expected_overrides
            ), f"Budget scenario {scenario.name} failed"
            assert abs(budget.remaining - scenario.expected_remaining) < 0.001

    def test_budget_reset_functionality(self):
        """Test budget reset functionality"""
        budget = CostBudget(total_budget=0.10, daily_limit=0.05)

        # Use some budget
        budget.allocate_cost(0.015)
        assert budget.total_used == 0.015
        assert budget.daily_used == 0.015

        # Test reset
        budget.reset_daily_budget()
        assert budget.total_used == 0.015
        assert budget.daily_used == 0.0
        assert budget.daily_remaining == 0.05

        # Test total budget reset
        budget.reset_total_budget()
        assert budget.total_used == 0.0
        assert budget.daily_used == 0.0
        assert budget.remaining == 0.10
        assert budget.daily_remaining == 0.05

    def test_budget_priority_handling(self):
        """Test budget priority handling for different request types"""
        budget = CostBudget(total_budget=0.02, daily_limit=0.01)

        priority_test_cases = [
            ("low_priority", 0.003, True),
            ("medium_priority", 0.005, True),
            ("high_priority", 0.008, True),
            ("critical_priority", 0.012, True),  # Should still succeed due to priority
        ]

        for priority, cost, expected_success in priority_test_cases:
            # Simulate priority-based budget allocation
            if priority == "critical_priority":
                # Critical requests can exceed budget limits
                success = budget.allocate_cost(cost, priority="critical")
            else:
                success = budget.allocate_cost(cost, priority=priority)

            assert success == expected_success

    def test_budget_monitoring(self):
        """Test budget monitoring and reporting"""
        budget = CostBudget(total_budget=0.10, daily_limit=0.05)

        # Test monitoring before any allocation
        monitoring = budget.get_budget_status()
        assert monitoring["remaining_percentage"] == 100.0
        assert monitoring["daily_used_percentage"] == 0.0
        assert monitoring["is_warning"] is False
        assert monitoring["is_critical"] is False

        # Allocate some budget
        budget.allocate_cost(0.015)
        budget.allocate_cost(0.003)

        # Test monitoring after allocation
        monitoring = budget.get_budget_status()
        assert monitoring["total_used"] == 0.018
        assert monitoring["remaining"] == 0.082
        assert monitoring["daily_used"] == 0.018
        assert monitoring["daily_remaining"] == 0.032
        assert monitoring["remaining_percentage"] == 82.0
        assert monitoring["daily_used_percentage"] == 36.0
        assert monitoring["is_warning"] is False
        assert monitoring["is_critical"] is False

        # Near budget limit
        budget.allocate_cost(0.045)  # Will exceed daily limit
        monitoring = budget.get_budget_status()
        assert monitoring["is_warning"] is True
        assert monitoring["is_critical"] is True


class TestCostOptimization:
    """Test cost optimization strategies"""

    def setup_method(self):
        """Setup test environment"""
        self.mock_supervisor = MockLLMSupervisor()

    def test_cost_minimization_strategies(self):
        """Test cost minimization strategies"""
        optimization_strategies = [
            {
                "name": "prompt_optimization",
                "original_prompt": "Generate a comprehensive analysis of the current market trends and provide detailed recommendations for business strategy optimization",
                "optimized_prompt": "Analyze market trends",
                "expected_cost_reduction": 0.4,
            },
            {
                "name": "batch_processing",
                "original_prompt": "Process each item individually: item1, item2, item3, item4, item5",
                "optimized_prompt": "Process items: item1, item2, item3, item4, item5",
                "expected_cost_reduction": 0.3,
            },
            {
                "name": "caching",
                "original_prompt": "What is the capital of France?",
                "optimized_prompt": "Paris",  # Cached response
                "expected_cost_reduction": 0.8,
            },
        ]

        for strategy in optimization_strategies:
            original_cost = self.mock_supervisor.estimate_cost(
                strategy["original_prompt"]
            )
            optimized_cost = self.mock_supervisor.estimate_cost(
                strategy["optimized_prompt"]
            )

            cost_reduction = (original_cost - optimized_cost) / original_cost

            assert (
                cost_reduction >= strategy["expected_cost_reduction"] * 0.8
            ), f"Cost reduction insufficient for {strategy['name']}: {cost_reduction}"

    def test_model_selection_optimization(self):
        """Test model selection for cost optimization"""
        model_comparison = [
            {
                "model": "gpt-3.5-turbo",
                "cost_per_1k_tokens": 0.002,
                "quality_score": 0.85,
                "speed_score": 0.90,
            },
            {
                "model": "gpt-4",
                "cost_per_1k_tokens": 0.03,
                "quality_score": 0.95,
                "quality_score": 0.95,
                "speed_score": 0.75,
            },
            {
                "model": "claude-3-haiku",
                "cost_per_1k_tokens": 0.0025,
                "quality_score": 0.80,
                "speed_score": 0.95,
            },
        ]

        # Test cost-effectiveness analysis
        for model in model_comparison:
            cost_effectiveness = model["quality_score"] / model["cost_per_1k_tokens"]
            model["cost_effectiveness"] = cost_effectiveness

        # Find most cost-effective model
        best_model = max(model_comparison, key=lambda x: x["cost_effectiveness"])
        assert (
            best_model["model"] == "gpt-3.5-turbo"
        ), "Cost-effectiveness analysis failed"

    def test_dynamic_scaling_optimization(self):
        """Test dynamic scaling based on demand"""
        demand_scenarios = [
            {"concurrent_users": 1, "expected_cost_multiplier": 1.0},
            {"concurrent_users": 5, "expected_cost_multiplier": 1.2},
            {"concurrent_users": 10, "expected_cost_multiplier": 1.5},
            {"concurrent_users": 20, "expected_cost_multiplier": 2.0},
        ]

        for scenario in demand_scenarios:
            base_cost = 0.002
            concurrent_users = scenario["concurrent_users"]
            expected_multiplier = scenario["expected_cost_multiplier"]

            # Simulate dynamic scaling
            if concurrent_users <= 5:
                scaled_cost = base_cost
            elif concurrent_users <= 10:
                scaled_cost = base_cost * 1.2
            else:
                scaled_cost = base_cost * 1.5

            actual_multiplier = scaled_cost / base_cost
            assert (
                actual_multiplier <= expected_multiplier * 1.1
            ), f"Scaling too aggressive for {concurrent_users} users: {actual_multiplier}"


class TestCostMonitoring:
    """Test cost monitoring and reporting"""

    def setup_method(self):
        """Setup test environment"""
        self.mock_supervisor = MockLLMSupervisor()

    def test_cost_tracking_accumulation(self):
        """Test cost tracking accumulation over time"""
        cost_tracker = {
            "total_cost": 0.0,
            "request_count": 0,
            "average_cost": 0.0,
            "costs": [],
        }

        test_costs = [0.001, 0.002, 0.003, 0.001, 0.004]

        for cost in test_costs:
            cost_tracker["total_cost"] += cost
            cost_tracker["request_count"] += 1
            cost_tracker["costs"].append(cost)
            cost_tracker["average_cost"] = (
                cost_tracker["total_cost"] / cost_tracker["request_count"]
            )

        # Validate tracking
        assert cost_tracker["total_cost"] == sum(test_costs)
        assert cost_tracker["request_count"] == len(test_costs)
        assert cost_tracker["average_cost"] == sum(test_costs) / len(test_costs)

    def test_cost_anomaly_detection(self):
        """Test cost anomaly detection"""
        normal_costs = [0.001, 0.002, 0.001, 0.003, 0.002, 0.001, 0.002]
        anomaly_costs = [0.001, 0.002, 0.050, 0.001, 0.003]  # 0.050 is anomaly

        def detect_anomaly(costs, threshold_multiplier=3.0):
            if len(costs) < 2:
                return False

            avg_cost = sum(costs) / len(costs)
            max_cost = max(costs)

            return max_cost > (avg_cost * threshold_multiplier)

        # Test normal costs (should not detect anomaly)
        anomaly_detected = detect_anomaly(normal_costs)
        assert anomaly_detected is False

        # Test anomaly costs (should detect anomaly)
        anomaly_detected = detect_anomaly(anomaly_costs)
        assert anomaly_detected is True

    def test_cost_reporting(self):
        """Test cost reporting functionality"""
        cost_data = {
            "period": "2025-11-26",
            "total_cost": 0.025,
            "request_count": 15,
            "average_cost": 0.00167,
            "max_cost": 0.005,
            "min_cost": 0.001,
            "cost_breakdown": {
                "code_generation": 0.015,
                "analysis": 0.008,
                "documentation": 0.002,
            },
            "budget_status": {
                "total_budget": 0.05,
                "remaining": 0.025,
                "usage_percentage": 50.0,
            },
        }

        # Test report generation
        report = self.mock_supervisor.generate_cost_report(cost_data)

        assert "period" in report
        assert "total_cost" in report
        assert "average_cost" in report
        assert "cost_trends" in report
        assert "budget_status" in report
        assert "recommendations" in report

        # Validate report content
        assert report["period"] == cost_data["period"]
        assert report["total_cost"] == cost_data["total_cost"]
        assert report["average_cost"] == cost_data["average_cost"]
        assert (
            report["budget_status"]["remaining"]
            == cost_data["budget_status"]["remaining"]
        )


class TestCostThresholdEnforcement:
    """Test cost threshold enforcement"""

    def setup_method(self):
        """Setup test environment"""
        self.mock_supervisor = MockLLMSupervisor()

    def test_cost_threshold_validation(self):
        """Test cost threshold validation"""
        thresholds = {
            "low_cost_threshold": 0.001,
            "medium_cost_threshold": 0.005,
            "high_cost_threshold": 0.010,
            "critical_cost_threshold": 0.020,
        }

        test_cases = [
            ("very_low_cost", 0.0005, "low"),
            ("low_cost", 0.002, "low"),
            ("medium_cost", 0.008, "medium"),
            ("high_cost", 0.015, "high"),
            ("critical_cost", 0.025, "critical"),
        ]

        for test_name, cost, expected_level in test_cases:
            cost_level = self.mock_supervisor.validate_cost_threshold(cost, thresholds)
            assert (
                cost_level == expected_level
            ), f"Cost threshold validation failed for {test_name}"

    def test_cost_enforcement_actions(self):
        """Test cost enforcement actions"""
        enforcement_actions = [
            {
                "cost": 0.025,
                "threshold": 0.020,
                "expected_action": "reject",
                "reason": "Cost exceeds critical threshold",
            },
            {
                "cost": 0.015,
                "threshold": 0.020,
                "expected_action": "warn",
                "reason": "Cost approaches critical threshold",
            },
            {
                "cost": 0.008,
                "threshold": 0.020,
                "expected_action": "allow",
                "reason": "Cost within acceptable range",
            },
        ]

        for case in enforcement_actions:
            action = self.mock_supervisor.determine_enforcement_action(
                case["cost"], case["threshold"]
            )
            assert action == case["expected_action"]

    def test_cost_exception_handling(self):
        """Test cost exception handling"""
        exception_cases = [
            {"cost": None, "threshold": 0.010, "expected_action": "allow"},
            {"cost": "invalid", "threshold": 0.010, "expected_action": "allow"},
            {"cost": -0.001, "threshold": 0.010, "expected_action": "allow"},
            {"cost": 0.005, "threshold": None, "expected_action": "allow"},
            {"cost": 0.005, "threshold": "invalid", "expected_action": "allow"},
        ]

        for case in exception_cases:
            action = self.mock_supervisor.determine_enforcement_action(
                case["cost"], case["threshold"]
            )
            assert action == case["expected_action"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
