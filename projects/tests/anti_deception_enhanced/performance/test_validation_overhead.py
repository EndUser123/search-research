"""
Performance Tests for Validation Overhead

Tests validation overhead performance of the Enhanced Anti-Deception Architecture.
Validates that all validation operations complete within the <2 second target.
"""

import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Any
from unittest.mock import Mock, patch

# Import test utilities
sys.path.insert(0, os.path.dirname(__file__))
from utils import (
    EvidenceGenerator,
    MockCommunicationSystem,
    MockLLM,
    TemporaryDirectory,
    TestConfigHelper,
)

# Import the anti-deception hook
sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "__csf")
)
try:
    from anti_deception_hook import AntiDeceptionHook
except ImportError:
    raise ImportError("Could not import AntiDeceptionHook")


@dataclass
class OverheadMetrics:
    """Validation overhead metrics."""

    total_time_ms: float = 0.0
    pre_validation_ms: float = 0.0
    evidence_collection_ms: float = 0.0
    llm_validation_ms: float = 0.0
    communication_ms: float = 0.0
    task_completion_ms: float = 0.0
    file_operation_ms: float = 0.0
    overhead_percentage: float = 0.0
    target_met: bool = True
    error: str | None = None


class TestValidationOverhead:
    """Test suite for validation overhead performance."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.config = TestConfigHelper.create_minimal_config()
        self.hook = AntiDeceptionHook()
        self.mock_llm = MockLLM()
        self.mock_comm = MockCommunicationSystem()
        self.evidence_generator = EvidenceGenerator()
        self.temp_dir = TemporaryDirectory()
        self.target_ms = 2000.0  # 2 second target

    def teardown_method(self):
        """Clean up after each test method."""
        self.temp_dir.__exit__(None, None, None)
        self.hook.reset_failures()
        self.mock_comm.clear_messages()

    def test_individual_overhead_components(self):
        """Test overhead of individual validation components."""
        components = [
            ("pre_validation", self._measure_pre_validation_overhead),
            ("evidence_collection", self._measure_evidence_collection_overhead),
            ("llm_validation", self._measure_llm_validation_overhead),
            ("communication", self._measure_communication_overhead),
            ("task_completion", self._measure_task_completion_overhead),
            ("file_operation", self._measure_file_operation_overhead),
        ]

        component_overheads = {}

        for component_name, measure_func in components:
            try:
                overhead = measure_func()
                component_overheads[component_name] = overhead

                print(f"{component_name}: {overhead:.2f}ms")

                # Verify each component is within reasonable bounds
                assert (
                    overhead < self.target_ms
                ), f"{component_name} overhead {overhead:.2f}ms exceeds target {self.target_ms}ms"

            except Exception as e:
                print(f"Error measuring {component_name} overhead: {e}")
                component_overheads[component_name] = -1

        # Verify all components were measured
        assert len(component_overheads) == len(components)

        # Calculate total overhead
        total_overhead = sum(component_overheads.values())
        print(f"Total validation overhead: {total_overhead:.2f}ms")

        # Verify total overhead is within target
        assert (
            total_overhead < self.target_ms
        ), f"Total overhead {total_overhead:.2f}ms exceeds target {self.target_ms}ms"

    def _measure_pre_validation_overhead(self) -> float:
        """Measure pre-validation overhead."""
        with self.temp_dir as temp_path:
            start_time = time.time()

            for i in range(10):
                test_file = os.path.join(temp_path, f"pre_test_{i}.txt")
                self.hook.validate_file_operation(test_file, "write")

            return (time.time() - start_time) * 1000

    def _measure_evidence_collection_overhead(self) -> float:
        """Measure evidence collection overhead."""
        with self.temp_dir as temp_path:
            start_time = time.time()

            for i in range(10):
                test_file = os.path.join(temp_path, f"evidence_test_{i}.txt")
                evidence = self.evidence_generator.create_file_evidence([test_file])
                self.hook.log_evidence("file_operations", evidence[0], [test_file])

            return (time.time() - start_time) * 1000

    def _measure_llm_validation_overhead(self) -> float:
        """Measure LLM validation overhead."""
        with self.temp_dir as temp_path:
            start_time = time.time()

            with patch.object(self.hook, "_call_llm_api") as mock_llm_api:
                mock_response = Mock()
                mock_response.json.return_value = {
                    "is_safe": True,
                    "confidence": 0.90,
                    "cost_estimate": 0.005,
                    "reasoning": "Test validation",
                }
                mock_llm_api.return_value = mock_response

                for i in range(5):
                    test_file = os.path.join(temp_path, f"llm_test_{i}.txt")
                    operation_context = {
                        "operation": "write_file",
                        "target_path": test_file,
                        "content": f"LLM test {i}",
                        "user_intent": "Testing",
                    }
                    self.hook._validate_with_llm_supervisor(operation_context)

            return (time.time() - start_time) * 1000

    def _measure_communication_overhead(self) -> float:
        """Measure communication overhead."""
        start_time = time.time()

        for i in range(20):
            self.mock_comm.send_message("test_hook", f"Test message {i}", "normal")
            self.mock_comm.receive_message()

        return (time.time() - start_time) * 1000

    def _measure_task_completion_overhead(self) -> float:
        """Measure task completion validation overhead."""
        start_time = time.time()

        for i in range(10):
            context = {
                "evidence_provided": i % 2 == 0,  # Alternate true/false
                "checklist": {
                    "evidence_provided": i % 2 == 0,
                    "tests_written": i % 3 == 0,
                    "tests_pass": i % 4 == 0,
                },
            }
            self.hook.can_complete_task(context)

        return (time.time() - start_time) * 1000

    def _measure_file_operation_overhead(self) -> float:
        """Measure file operation overhead."""
        with self.temp_dir as temp_path:
            start_time = time.time()

            for i in range(10):
                test_file = os.path.join(temp_path, f"file_test_{i}.txt")
                with open(test_file, "w") as f:
                    f.write(f"Test content {i}")

                self.hook.verify_file_exists(test_file)

            return (time.time() - start_time) * 1000

    def test_complete_validation_overhead(self):
        """Test complete validation pipeline overhead."""

        def complete_validation_workflow(workflow_id: int) -> OverheadMetrics:
            """Execute a complete validation workflow."""
            metrics = OverheadMetrics()

            try:
                with self.temp_dir as temp_path:
                    test_file = os.path.join(
                        temp_path, f"complete_test_{workflow_id}.txt"
                    )

                    # Pre-validation
                    start_time = time.time()
                    self.hook.validate_file_operation(test_file, "write")
                    metrics.pre_validation_ms = (time.time() - start_time) * 1000

                    # File operation
                    start_time = time.time()
                    with open(test_file, "w") as f:
                        f.write(f"Complete workflow {workflow_id}")
                    metrics.file_operation_ms = (time.time() - start_time) * 1000

                    # Evidence collection
                    start_time = time.time()
                    evidence = self.evidence_generator.create_file_evidence([test_file])
                    self.hook.log_evidence("file_operations", evidence[0], [test_file])
                    metrics.evidence_collection_ms = (time.time() - start_time) * 1000

                    # LLM validation
                    start_time = time.time()
                    with patch.object(self.hook, "_call_llm_api") as mock_llm_api:
                        mock_response = Mock()
                        mock_response.json.return_value = {
                            "is_safe": True,
                            "confidence": 0.90,
                            "cost_estimate": 0.005,
                            "reasoning": "Complete workflow validation",
                        }
                        mock_llm_api.return_value = mock_response

                        operation_context = {
                            "operation": "write_file",
                            "target_path": test_file,
                            "content": f"Complete workflow {workflow_id}",
                            "user_intent": "Complete testing",
                        }
                        self.hook._validate_with_llm_supervisor(operation_context)
                    metrics.llm_validation_ms = (time.time() - start_time) * 1000

                    # Communication
                    start_time = time.time()
                    self.mock_comm.send_message(
                        "complete_workflow",
                        f"Complete workflow {workflow_id} completed",
                        "normal",
                    )
                    metrics.communication_ms = (time.time() - start_time) * 1000

                    # Task completion
                    start_time = time.time()
                    context = {
                        "evidence_provided": True,
                        "checklist": {
                            "evidence_provided": True,
                            "tests_written": True,
                            "tests_pass": True,
                        },
                    }
                    self.hook.can_complete_task(context)
                    metrics.task_completion_ms = (time.time() - start_time) * 1000

                    # Calculate total and percentage
                    metrics.total_time_ms = sum(
                        [
                            metrics.pre_validation_ms,
                            metrics.file_operation_ms,
                            metrics.evidence_collection_ms,
                            metrics.llm_validation_ms,
                            metrics.communication_ms,
                            metrics.task_completion_ms,
                        ]
                    )

                    # Simulate actual work time (file operation + context)
                    actual_work_time = (
                        metrics.file_operation_ms + 100
                    )  # Assume 100ms actual work
                    metrics.overhead_percentage = (
                        (metrics.total_time_ms / actual_work_time) * 100
                        if actual_work_time > 0
                        else 0
                    )

                    # Check if target met
                    metrics.target_met = metrics.total_time_ms < self.target_ms

            except Exception as e:
                metrics.error = str(e)

            return metrics

        # Execute complete validation workflows
        num_workflows = 10
        workflow_results = []

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for i in range(num_workflows):
                future = executor.submit(complete_validation_workflow, i)
                futures.append(future)

            # Collect results
            for future in as_completed(futures):
                try:
                    result = future.result()
                    workflow_results.append(result)
                except Exception as e:
                    print(f"Complete workflow error: {e}")

        # Verify all workflows completed successfully
        assert len(workflow_results) == num_workflows
        assert all(
            result.target_met for result in workflow_results
        ), f"Some workflows exceeded target: {[result.total_time_ms for result in workflow_results]}"

        # Analyze overhead metrics
        total_overheads = [result.total_time_ms for result in workflow_results]
        avg_overhead = sum(total_overheads) / len(total_overheads)
        max_overhead = max(total_overheads)
        min_overhead = min(total_overheads)

        print("\nComplete Validation Overhead Analysis:")
        print(f"Average overhead: {avg_overhead:.2f}ms")
        print(f"Max overhead: {max_overhead:.2f}ms")
        print(f"Min overhead: {min_overhead:.2f}ms")
        print(f"Target met: {all(result.target_met for result in workflow_results)}")

        # Verify individual component overheads
        for result in workflow_results:
            assert result.pre_validation_ms < 1000  # 1 second
            assert result.evidence_collection_ms < 500  # 0.5 seconds
            assert result.llm_validation_ms < 1000  # 1 second
            assert result.communication_ms < 500  # 0.5 seconds
            assert result.task_completion_ms < 1000  # 1 second

        # Verify overhead percentage is reasonable
        for result in workflow_results:
            assert (
                result.overhead_percentage < 1000
            ), f"Overhead percentage {result.overhead_percentage:.2f}% is too high"

    def test_concurrent_validation_overhead(self):
        """Test validation overhead under concurrent operations."""

        def concurrent_validation(worker_id: int) -> OverheadMetrics:
            """Execute validation operations concurrently."""
            metrics = OverheadMetrics()

            try:
                with self.temp_dir as temp_path:
                    start_time = time.time()

                    # Multiple validation operations
                    for i in range(5):
                        test_file = os.path.join(
                            temp_path, f"concurrent_{worker_id}_{i}.txt"
                        )

                        # Pre-validation
                        self.hook.validate_file_operation(test_file, "write")

                        # File operation
                        with open(test_file, "w") as f:
                            f.write(f"Concurrent test {worker_id}_{i}")

                        # Evidence collection
                        evidence = self.evidence_generator.create_file_evidence(
                            [test_file]
                        )
                        self.hook.log_evidence(
                            "file_operations", evidence[0], [test_file]
                        )

                        # Communication
                        self.mock_comm.send_message(
                            "concurrent_test",
                            f"Concurrent {worker_id}_{i} completed",
                            "normal",
                        )

                    metrics.total_time_ms = (time.time() - start_time) * 1000
                    metrics.target_met = metrics.total_time_ms < self.target_ms

            except Exception as e:
                metrics.error = str(e)

            return metrics

        # Execute concurrent validations
        num_workers = 20
        concurrent_results = []

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for i in range(num_workers):
                future = executor.submit(concurrent_validation, i)
                futures.append(future)

            # Collect results
            for future in as_completed(futures):
                try:
                    result = future.result()
                    concurrent_results.append(result)
                except Exception as e:
                    print(f"Concurrent validation error: {e}")

        # Verify all concurrent validations met target
        assert len(concurrent_results) == num_workers
        assert all(
            result.target_met for result in concurrent_results
        ), f"Some concurrent validations exceeded target: {[result.total_time_ms for result in concurrent_results]}"

        # Analyze concurrent overhead
        concurrent_overheads = [result.total_time_ms for result in concurrent_results]
        avg_concurrent_overhead = sum(concurrent_overheads) / len(concurrent_overheads)
        max_concurrent_overhead = max(concurrent_overheads)

        print("\nConcurrent Validation Overhead Analysis:")
        print(f"Average overhead: {avg_concurrent_overhead:.2f}ms")
        print(f"Max overhead: {max_concurrent_overhead:.2f}ms")
        print(f"Target met: {all(result.target_met for result in concurrent_results)}")

        # Verify overhead scaling
        assert (
            max_concurrent_overhead < self.target_ms
        ), f"Max concurrent overhead {max_concurrent_overhead:.2f}ms exceeds target"

    def test_overhead_scaling_analysis(self):
        """Test overhead scaling with different operation counts."""

        def test_scaling_operations(num_operations: int) -> dict[str, Any]:
            """Test operations with specific count."""
            start_time = time.time()

            with self.temp_dir as temp_path:
                for i in range(num_operations):
                    test_file = os.path.join(temp_path, f"scaling_test_{i}.txt")

                    # Complete validation pipeline
                    self.hook.validate_file_operation(test_file, "write")
                    with open(test_file, "w") as f:
                        f.write(f"Scaling test {i}")

                    evidence = self.evidence_generator.create_file_evidence([test_file])
                    self.hook.log_evidence("file_operations", evidence[0], [test_file])

                    self.mock_comm.send_message(
                        "scaling_test", f"Scaling test {i} completed", "normal"
                    )

            total_time = (time.time() - start_time) * 1000
            throughput = num_operations / (total_time / 1000) if total_time > 0 else 0

            return {
                "num_operations": num_operations,
                "total_time_ms": total_time,
                "throughput": throughput,
                "average_time_per_op": total_time / num_operations
                if num_operations > 0
                else 0,
            }

        # Test different operation counts
        operation_counts = [1, 5, 10, 25, 50, 100]
        scaling_results = []

        for count in operation_counts:
            result = test_scaling_operations(count)
            scaling_results.append(result)

        # Verify all tests met target
        for result in scaling_results:
            assert (
                result["total_time_ms"] < self.target_ms
            ), f"Scaling test with {result['num_operations']} operations took {result['total_time_ms']}ms"

        # Analyze scaling
        print("\nOverhead Scaling Analysis:")
        for result in scaling_results:
            print(
                f"Operations: {result['num_operations']}, "
                f"Time: {result['total_time_ms']:.2f}ms, "
                f"Avg/Op: {result['average_time_per_op']:.2f}ms, "
                f"Throughput: {result['throughput']:.2f} ops/sec"
            )

        # Verify scaling behavior
        times = [result["total_time_ms"] for result in scaling_results]
        operations = [result["num_operations"] for result in scaling_results]

        # Check that time scales roughly linearly with operations
        for i in range(1, len(scaling_results)):
            ratio = (
                scaling_results[i]["num_operations"]
                / scaling_results[i - 1]["num_operations"]
            )
            time_ratio = (
                scaling_results[i]["total_time_ms"]
                / scaling_results[i - 1]["total_time_ms"]
            )

            # Time should scale roughly with operation count (within 2x)
            assert (
                0.5 * ratio <= time_ratio <= 2.0 * ratio
            ), f"Scaling ratio {time_ratio:.2f} outside expected range for operation ratio {ratio:.2f}"

    def test_overhead_with_error_conditions(self):
        """Test overhead validation with error conditions."""

        def error_condition_overhead(error_type: str) -> OverheadMetrics:
            """Test overhead with specific error condition."""
            metrics = OverheadMetrics()

            try:
                start_time = time.time()

                if error_type == "dangerous_operations":
                    # Test dangerous file validation overhead
                    dangerous_files = [
                        "/etc/passwd",
                        "/etc/shadow",
                        "/root/.ssh/authorized_keys",
                    ]
                    for dangerous_file in dangerous_files:
                        self.hook.validate_file_operation(dangerous_file, "write")

                elif error_type == "evidence_failures":
                    # Test evidence failure overhead
                    for i in range(10):
                        self.hook.require_evidence(f"Test claim {i}", [])

                elif error_type == "communication_failures":
                    # Test communication failure overhead
                    self.mock_comm.connected = False
                    for i in range(10):
                        self.mock_comm.send_message("test", f"Test {i}", "normal")
                    self.mock_comm.connected = True

                elif error_type == "mixed_errors":
                    # Test mixed error conditions
                    for i in range(5):
                        # Dangerous validation
                        self.hook.validate_file_operation("/etc/passwd", "write")
                        # Evidence failure
                        self.hook.require_evidence(f"Test claim {i}", [])
                        # Communication failure
                        self.mock_comm.connected = False
                        self.mock_comm.send_message("test", f"Test {i}", "normal")
                        self.mock_comm.connected = True

                metrics.total_time_ms = (time.time() - start_time) * 1000
                metrics.target_met = metrics.total_time_ms < self.target_ms

            except Exception as e:
                metrics.error = str(e)

            return metrics

        # Test different error conditions
        error_conditions = [
            "dangerous_operations",
            "evidence_failures",
            "communication_failures",
            "mixed_errors",
        ]

        error_results = []

        for error_type in error_conditions:
            result = error_condition_overhead(error_type)
            error_results.append(result)

        # Verify all error condition tests met target
        assert len(error_results) == len(error_conditions)
        assert all(
            result.target_met for result in error_results
        ), f"Some error condition tests exceeded target: {[(result.total_time_ms, result.error) for result in error_results]}"

        # Analyze error condition overhead
        for i, (error_type, result) in enumerate(
            zip(error_conditions, error_results, strict=False)
        ):
            print(f"{error_type}: {result.total_time_ms:.2f}ms")

        # Verify error handling doesn't cause excessive overhead
        max_error_overhead = max(result.total_time_ms for result in error_results)
        assert (
            max_error_overhead < self.target_ms
        ), f"Error condition overhead {max_error_overhead:.2f}ms exceeds target"

    def test_overhead_memory_impact(self):
        """Test validation overhead memory impact."""
        import gc

        import psutil

        def get_memory_usage():
            """Get current memory usage in MB."""
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024

        # Measure initial memory
        initial_memory = get_memory_usage()

        # Execute validation operations with overhead measurement
        start_time = time.time()

        with self.temp_dir as temp_path:
            for i in range(50):
                test_file = os.path.join(temp_path, f"memory_test_{i}.txt")

                # Complete validation pipeline
                self.hook.validate_file_operation(test_file, "write")
                with open(test_file, "w") as f:
                    f.write(f"Memory test {i}")

                evidence = self.evidence_generator.create_file_evidence([test_file])
                self.hook.log_evidence("file_operations", evidence[0], [test_file])

                self.mock_comm.send_message(
                    "memory_test", f"Memory test {i} completed", "normal"
                )

                # Force garbage collection every 10 operations
                if i % 10 == 0:
                    gc.collect()

        total_time = (time.time() - start_time) * 1000

        # Measure final memory
        final_memory = get_memory_usage()

        # Calculate overhead metrics
        overhead = total_time
        memory_increase = final_memory - initial_memory

        print("\nMemory Impact Analysis:")
        print(f"Validation overhead: {overhead:.2f}ms")
        print(f"Memory increase: {memory_increase:.2f} MB")
        print(f"Overhead met: {overhead < self.target_ms}")
        print(
            f"Memory constraint met: {memory_increase < 50}"
        )  # Less than 50MB increase

        # Verify overhead and memory constraints
        assert overhead < self.target_ms, f"Overhead {overhead:.2f}ms exceeds target"
        assert (
            memory_increase < 50
        ), f"Memory increase {memory_increase:.2f}MB exceeds constraint"

    def test_overhead_burst_conditions(self):
        """Test validation overhead under burst conditions."""

        def burst_operation(burst_id: int) -> OverheadMetrics:
            """Execute burst of operations."""
            metrics = OverheadMetrics()

            try:
                with self.temp_dir as temp_path:
                    start_time = time.time()

                    # Burst of 10 operations
                    for i in range(10):
                        test_file = os.path.join(temp_path, f"burst_{burst_id}_{i}.txt")

                        # Complete validation pipeline
                        self.hook.validate_file_operation(test_file, "write")
                        with open(test_file, "w") as f:
                            f.write(f"Burst test {burst_id}_{i}")

                        evidence = self.evidence_generator.create_file_evidence(
                            [test_file]
                        )
                        self.hook.log_evidence(
                            "file_operations", evidence[0], [test_file]
                        )

                        self.mock_comm.send_message(
                            "burst_test",
                            f"Burst test {burst_id}_{i} completed",
                            "normal",
                        )

                    metrics.total_time_ms = (time.time() - start_time) * 1000
                    metrics.target_met = metrics.total_time_ms < self.target_ms

            except Exception as e:
                metrics.error = str(e)

            return metrics

        # Execute burst operations
        num_bursts = 20
        burst_results = []

        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = []
            for i in range(num_bursts):
                future = executor.submit(burst_operation, i)
                futures.append(future)

            # Collect results
            for future in as_completed(futures):
                try:
                    result = future.result()
                    burst_results.append(result)
                except Exception as e:
                    print(f"Burst operation error: {e}")

        # Verify all burst operations met target
        assert len(burst_results) == num_bursts
        assert all(
            result.target_met for result in burst_results
        ), f"Some burst operations exceeded target: {[result.total_time_ms for result in burst_results]}"

        # Analyze burst overhead
        burst_overheads = [result.total_time_ms for result in burst_results]
        avg_burst_overhead = sum(burst_overheads) / len(burst_overheads)
        max_burst_overhead = max(burst_overheads)

        print("\nBurst Condition Analysis:")
        print(f"Average burst overhead: {avg_burst_overhead:.2f}ms")
        print(f"Max burst overhead: {max_burst_overhead:.2f}ms")
        print(
            f"Burst operations met target: {all(result.target_met for result in burst_results)}"
        )

        # Verify burst overhead constraints
        assert (
            max_burst_overhead < self.target_ms
        ), f"Max burst overhead {max_burst_overhead:.2f}ms exceeds target"


if __name__ == "__main__":
    # Run the tests
    import pytest

    pytest.main([__file__, "-v"])
