"""
Performance Tests for Parallel Execution

Tests parallel execution performance of the Enhanced Anti-Deception Architecture.
Validates that parallel validation performs within targets (<2 second validation overhead).
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
    PerformanceBenchmark,
    PerformanceTimer,
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
class PerformanceMetrics:
    """Performance metrics for parallel execution testing."""

    total_operations: int = 0
    total_time_ms: float = 0.0
    average_time_ms: float = 0.0
    max_time_ms: float = 0.0
    min_time_ms: float = 0.0
    throughput_ops_per_sec: float = 0.0
    target_met: bool = True
    errors: list[str] = field(default_factory=list)


class TestParallelExecution:
    """Test suite for parallel execution performance."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.config = TestConfigHelper.create_minimal_config()
        self.hook = AntiDeceptionHook()
        self.mock_llm = MockLLM()
        self.mock_comm = MockCommunicationSystem()
        self.evidence_generator = EvidenceGenerator()
        self.temp_dir = TemporaryDirectory()
        self.performance_benchmark = PerformanceBenchmark(target_ms=2000.0)

    def teardown_method(self):
        """Clean up after each test method."""
        self.temp_dir.__exit__(None, None, None)
        self.hook.reset_failures()
        self.mock_comm.clear_messages()

    def test_parallel_file_validation_performance(self):
        """Test parallel file validation performance."""
        target_ms = 2000.0  # 2 second target

        with PerformanceTimer() as timer:
            with self.temp_dir as temp_path:
                # Create test files
                test_files = []
                for i in range(50):
                    test_file = os.path.join(temp_path, f"parallel_test_{i}.txt")
                    with open(test_file, "w") as f:
                        f.write(f"Test content {i}")
                    test_files.append(test_file)

                # Execute parallel validations
                with ThreadPoolExecutor(max_workers=10) as executor:
                    futures = []
                    for test_file in test_files:
                        future = executor.submit(
                            self.hook.validate_file_operation, test_file, "write"
                        )
                        futures.append(future)

                    # Collect results
                    results = []
                    for future in as_completed(futures):
                        try:
                            is_safe, reason = future.result()
                            results.append((is_safe, reason))
                        except Exception as e:
                            self.performance_benchmark.results.append(
                                {
                                    "function": "parallel_file_validation",
                                    "elapsed_ms": 0,
                                    "target_ms": target_ms,
                                    "passed": False,
                                    "error": str(e),
                                    "timestamp": time.time(),
                                }
                            )

        # Verify performance target is met
        assert (
            timer.elapsed_ms < target_ms
        ), f"Parallel file validation took {timer.elapsed_ms}ms, target: {target_ms}ms"

        # Verify all validations completed
        assert len(results) == 50
        assert all(is_safe for is_safe, reason in results)

    def test_parallel_evidence_collection_performance(self):
        """Test parallel evidence collection performance."""
        target_ms = 2000.0  # 2 second target

        with PerformanceTimer() as timer:
            with self.temp_dir as temp_path:
                # Create test files
                test_files = []
                for i in range(30):
                    test_file = os.path.join(temp_path, f"evidence_test_{i}.txt")
                    with open(test_file, "w") as f:
                        f.write(f"Evidence content {i}")
                    test_files.append(test_file)

                # Execute parallel evidence collection
                with ThreadPoolExecutor(max_workers=8) as executor:
                    futures = []
                    for test_file in test_files:
                        evidence = self.evidence_generator.create_file_evidence(
                            [test_file]
                        )
                        future = executor.submit(
                            self.hook.log_evidence,
                            "file_operations",
                            evidence[0],
                            [test_file],
                        )
                        futures.append(future)

                    # Collect results
                    results = []
                    for future in as_completed(futures):
                        try:
                            future.result()  # log_evidence returns None
                            results.append(True)
                        except Exception as e:
                            results.append(False)
                            print(f"Evidence collection error: {e}")

        # Verify performance target is met
        assert (
            timer.elapsed_ms < target_ms
        ), f"Parallel evidence collection took {timer.elapsed_ms}ms, target: {target_ms}ms"

        # Verify all evidence was collected
        assert len(results) == 30
        assert all(results)

        # Verify evidence log was populated
        assert len(self.hook.evidence_log) >= 30

    def test_parallel_validation_pipeline_performance(self):
        """Test parallel validation pipeline performance."""
        target_ms = 2000.0  # 2 second target

        def validation_pipeline(file_path: str) -> dict[str, Any]:
            """Execute a complete validation pipeline for a file."""
            pipeline_results = {}

            # Step 1: Pre-validation
            start_time = time.time()
            is_safe, reason = self.hook.validate_file_operation(file_path, "write")
            pipeline_results["pre_validation_time"] = (time.time() - start_time) * 1000
            pipeline_results["pre_validation_safe"] = is_safe

            # Step 2: File operation
            start_time = time.time()
            with open(file_path, "w") as f:
                f.write(f"Pipeline test content {os.path.basename(file_path)}")
            pipeline_results["file_operation_time"] = (time.time() - start_time) * 1000

            # Step 3: Evidence collection
            start_time = time.time()
            evidence = self.evidence_generator.create_file_evidence([file_path])
            self.hook.log_evidence("file_operations", evidence[0], [file_path])
            pipeline_results["evidence_collection_time"] = (
                time.time() - start_time
            ) * 1000

            # Step 4: Task completion validation
            start_time = time.time()
            context = {
                "evidence_provided": True,
                "checklist": {
                    "evidence_provided": True,
                    "tests_written": True,
                    "tests_pass": True,
                },
            }
            can_complete, issues = self.hook.can_complete_task(context)
            pipeline_results["task_completion_time"] = (time.time() - start_time) * 1000
            pipeline_results["task_completion_success"] = can_complete

            # Step 5: Communication
            start_time = time.time()
            self.mock_comm.send_message(
                "validation_pipeline", f"Pipeline completed for {file_path}", "normal"
            )
            pipeline_results["communication_time"] = (time.time() - start_time) * 1000

            return pipeline_results

        with PerformanceTimer() as timer:
            with self.temp_dir as temp_path:
                # Create test files
                test_files = []
                for i in range(20):
                    test_file = os.path.join(temp_path, f"pipeline_test_{i}.txt")
                    test_files.append(test_file)

                # Execute parallel validation pipelines
                with ThreadPoolExecutor(max_workers=5) as executor:
                    futures = []
                    for test_file in test_files:
                        future = executor.submit(validation_pipeline, test_file)
                        futures.append(future)

                    # Collect results
                    all_results = []
                    for future in as_completed(futures):
                        try:
                            result = future.result()
                            all_results.append(result)
                        except Exception as e:
                            print(f"Pipeline error: {e}")
                            all_results.append(None)

        # Verify performance target is met
        assert (
            timer.elapsed_ms < target_ms
        ), f"Parallel validation pipeline took {timer.elapsed_ms}ms, target: {target_ms}ms"

        # Verify all pipelines completed
        assert len(all_results) == 20
        assert all(result is not None for result in all_results)

        # Calculate overall metrics
        total_pipeline_time = sum(
            result["pre_validation_time"]
            + result["file_operation_time"]
            + result["evidence_collection_time"]
            + result["task_completion_time"]
            + result["communication_time"]
            for result in all_results
        )
        average_pipeline_time = total_pipeline_time / len(all_results)

        print(f"Average pipeline time: {average_pipeline_time:.2f}ms")
        print(f"Total pipeline time: {total_pipeline_time:.2f}ms")
        print(f"Throughput: {len(all_results) / (timer.elapsed_ms / 1000):.2f} ops/sec")

    def test_concurrent_hook_performance(self):
        """Test performance of concurrent hook operations."""
        target_ms = 2000.0  # 2 second target

        def concurrent_hook_operations(operation_id: int) -> dict[str, float]:
            """Execute concurrent hook operations."""
            metrics = {}

            # Pre-Tool Use validation
            start_time = time.time()
            target_file = f"P:\\temp\\concurrent_test_{operation_id}.txt"
            is_safe, reason = self.hook.validate_file_operation(target_file, "write")
            metrics["pre_validation_time"] = (time.time() - start_time) * 1000

            # Evidence collection
            start_time = time.time()
            evidence = self.evidence_generator.create_file_evidence([target_file])
            self.hook.log_evidence("file_operations", evidence[0], [target_file])
            metrics["evidence_time"] = (time.time() - start_time) * 1000

            # LLM validation (mocked)
            start_time = time.time()
            with patch.object(self.hook, "_call_llm_api") as mock_llm_api:
                mock_response = Mock()
                mock_response.json.return_value = {
                    "is_safe": True,
                    "confidence": 0.90,
                    "cost_estimate": 0.005,
                    "reasoning": "Concurrent test operation",
                }
                mock_llm_api.return_value = mock_response

                operation_context = {
                    "operation": "write_file",
                    "target_path": target_file,
                    "content": f"Concurrent test {operation_id}",
                    "user_intent": "Concurrent testing",
                }

                self.hook._validate_with_llm_supervisor(operation_context)
                metrics["llm_time"] = (time.time() - start_time) * 1000

            # Communication
            start_time = time.time()
            self.mock_comm.send_message(
                "concurrent_test", f"Operation {operation_id} completed", "normal"
            )
            metrics["communication_time"] = (time.time() - start_time) * 1000

            return metrics

        with PerformanceTimer() as timer:
            # Execute concurrent hook operations
            num_operations = 15
            with ThreadPoolExecutor(max_workers=8) as executor:
                futures = []
                for i in range(num_operations):
                    future = executor.submit(concurrent_hook_operations, i)
                    futures.append(future)

                # Collect results
                all_metrics = []
                for future in as_completed(futures):
                    try:
                        metrics = future.result()
                        all_metrics.append(metrics)
                    except Exception as e:
                        print(f"Concurrent hook error: {e}")

        # Verify performance target is met
        assert (
            timer.elapsed_ms < target_ms
        ), f"Concurrent hook operations took {timer.elapsed_ms}ms, target: {target_ms}ms"

        # Verify all operations completed
        assert len(all_metrics) == num_operations

        # Analyze performance metrics
        total_times = []
        for metrics in all_metrics:
            total_time = sum(metrics.values())
            total_times.append(total_time)

        avg_time = sum(total_times) / len(total_times)
        max_time = max(total_times)
        min_time = min(total_times)

        print(f"Average concurrent hook time: {avg_time:.2f}ms")
        print(f"Max concurrent hook time: {max_time:.2f}ms")
        print(f"Min concurrent hook time: {min_time:.2f}ms")
        print(f"Throughput: {num_operations / (timer.elapsed_ms / 1000):.2f} ops/sec")

        # Verify individual components are within bounds
        for metrics in all_metrics:
            assert metrics["pre_validation_time"] < 1000  # 1 second
            assert metrics["evidence_time"] < 500  # 0.5 seconds
            assert metrics["llm_time"] < 1000  # 1 second
            assert metrics["communication_time"] < 500  # 0.5 seconds

    def test_parallel_error_handling_performance(self):
        """Test parallel error handling performance."""
        target_ms = 2000.0  # 2 second target

        def error_handling_operation(operation_id: int) -> dict[str, Any]:
            """Execute error handling operations."""
            results = {}

            # Test dangerous file validation
            start_time = time.time()
            dangerous_files = [
                "/etc/passwd",
                "/etc/shadow",
                "/root/.ssh/authorized_keys",
            ]
            for dangerous_file in dangerous_files:
                is_safe, reason = self.hook.validate_file_operation(
                    dangerous_file, "write"
                )
            results["dangerous_validation_time"] = (time.time() - start_time) * 1000

            # Test evidence requirement failure
            start_time = time.time()
            evidence_result = self.hook.require_evidence("Test claim", [])
            results["evidence_failure_time"] = (time.time() - start_time) * 1000

            # Test task completion with failures
            start_time = time.time()
            context = {
                "evidence_provided": False,
                "checklist": {
                    "evidence_provided": False,
                    "tests_written": False,
                    "tests_pass": False,
                },
            }
            can_complete, issues = self.hook.can_complete_task(context)
            results["task_completion_time"] = (time.time() - start_time) * 1000

            return results

        with PerformanceTimer() as timer:
            # Execute parallel error handling operations
            num_operations = 20
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = []
                for i in range(num_operations):
                    future = executor.submit(error_handling_operation, i)
                    futures.append(future)

                # Collect results
                all_results = []
                for future in as_completed(futures):
                    try:
                        result = future.result()
                        all_results.append(result)
                    except Exception as e:
                        print(f"Error handling operation failed: {e}")

        # Verify performance target is met
        assert (
            timer.elapsed_ms < target_ms
        ), f"Parallel error handling took {timer.elapsed_ms}ms, target: {target_ms}ms"

        # Verify all operations completed
        assert len(all_results) == num_operations

        # Analyze performance
        for results in all_results:
            assert results["dangerous_validation_time"] < 1000  # 1 second
            assert results["evidence_failure_time"] < 500  # 0.5 seconds
            assert results["task_completion_time"] < 1000  # 1 second

    def test_memory_usage_performance(self):
        """Test memory usage during parallel operations."""
        import gc

        import psutil

        def get_memory_usage():
            """Get current memory usage in MB."""
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024

        # Measure initial memory
        initial_memory = get_memory_usage()

        # Execute parallel operations
        with self.temp_dir as temp_path:
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = []
                for i in range(100):
                    test_file = os.path.join(temp_path, f"memory_test_{i}.txt")
                    future = executor.submit(
                        self.hook.validate_file_operation, test_file, "write"
                    )
                    futures.append(future)

                # Collect results
                results = []
                for future in as_completed(futures):
                    try:
                        is_safe, reason = future.result()
                        results.append((is_safe, reason))
                    except Exception as e:
                        print(f"Memory test error: {e}")

        # Measure peak memory
        peak_memory = get_memory_usage()

        # Force garbage collection
        gc.collect()

        # Measure final memory
        final_memory = get_memory_usage()

        print(f"Initial memory: {initial_memory:.2f} MB")
        print(f"Peak memory: {peak_memory:.2f} MB")
        print(f"Final memory: {final_memory:.2f} MB")
        print(f"Memory increase: {peak_memory - initial_memory:.2f} MB")

        # Verify memory constraints (less than 100MB increase)
        assert (
            peak_memory - initial_memory < 100
        ), f"Memory usage increased by {peak_memory - initial_memory:.2f} MB"

        # Verify all operations completed
        assert len(results) == 100
        assert all(is_safe for is_safe, reason in results)

    def test_scaling_performance(self):
        """Test performance scaling with different thread counts."""
        target_ms = 2000.0  # 2 second target

        def test_scaling_operations(num_threads: int) -> dict[str, Any]:
            """Test operations with specific thread count."""
            results = {}

            with ThreadPoolExecutor(max_workers=num_threads) as executor:
                futures = []
                for i in range(50):
                    test_file = f"P:\\temp\\scaling_test_{i}.txt"
                    future = executor.submit(
                        self.hook.validate_file_operation, test_file, "write"
                    )
                    futures.append(future)

                # Collect results
                start_time = time.time()
                completed = 0
                for future in as_completed(futures):
                    try:
                        is_safe, reason = future.result()
                        completed += 1
                    except Exception:
                        pass

                execution_time = (time.time() - start_time) * 1000

                results["execution_time_ms"] = execution_time
                results["completed_operations"] = completed
                results["throughput"] = (
                    completed / (execution_time / 1000) if execution_time > 0 else 0
                )

            return results

        # Test different thread counts
        thread_counts = [1, 2, 4, 8, 16]
        scaling_results = []

        for thread_count in thread_counts:
            results = test_scaling_operations(thread_count)
            scaling_results.append(
                {
                    "thread_count": thread_count,
                    "execution_time_ms": results["execution_time_ms"],
                    "completed_operations": results["completed_operations"],
                    "throughput": results["throughput"],
                }
            )

        # Verify all tests met performance target
        for result in scaling_results:
            assert (
                result["execution_time_ms"] < target_ms
            ), f"Scaling test with {result['thread_count']} threads took {result['execution_time_ms']}ms"

        # Print scaling analysis
        print("\nScaling Performance Analysis:")
        for result in scaling_results:
            print(
                f"Threads: {result['thread_count']}, Time: {result['execution_time_ms']:.2f}ms, "
                f"Throughput: {result['throughput']:.2f} ops/sec"
            )

        # Verify throughput improves with more threads (up to a point)
        throughputs = [result["throughput"] for result in scaling_results]
        assert (
            throughputs[-1] > throughputs[0]
        ), f"Throughput should improve: {throughputs[0]:.2f} -> {throughputs[-1]:.2f}"

    def test_load_balancing_performance(self):
        """Test performance with load balancing across multiple hooks."""
        # Create multiple hook instances for load balancing
        hooks = [AntiDeceptionHook() for _ in range(5)]
        temp_dirs = [TemporaryDirectory() for _ in range(5)]

        def load_balanced_operation(
            operation_id: int, hook_index: int
        ) -> dict[str, Any]:
            """Execute operation on a specific hook."""
            hook = hooks[hook_index]
            temp_dir = temp_dirs[hook_index]

            with temp_dir as temp_path:
                test_file = os.path.join(temp_path, f"load_balanced_{operation_id}.txt")

                start_time = time.time()

                # Execute pipeline
                hook.validate_file_operation(test_file, "write")
                with open(test_file, "w") as f:
                    f.write(f"Load balanced {operation_id}")

                evidence = self.evidence_generator.create_file_evidence([test_file])
                hook.log_evidence("file_operations", evidence[0], [test_file])

                execution_time = (time.time() - start_time) * 1000

                return {
                    "execution_time_ms": execution_time,
                    "hook_index": hook_index,
                    "operation_id": operation_id,
                }

        # Execute load balanced operations
        with PerformanceTimer() as timer:
            num_operations = 100
            operations_per_hook = num_operations // len(hooks)

            with ThreadPoolExecutor(max_workers=len(hooks)) as executor:
                futures = []
                for hook_index in range(len(hooks)):
                    for op_id in range(operations_per_hook):
                        future = executor.submit(
                            load_balanced_operation, op_id, hook_index
                        )
                        futures.append(future)

                # Collect results
                all_results = []
                for future in as_completed(futures):
                    try:
                        result = future.result()
                        all_results.append(result)
                    except Exception as e:
                        print(f"Load balanced error: {e}")

        # Verify performance target is met
        assert (
            timer.elapsed_ms < target_ms
        ), f"Load balancing took {timer.elapsed_ms}ms, target: {target_ms}ms"

        # Verify load balancing worked (each hook got similar load)
        hook_loads = {}
        for result in all_results:
            hook_index = result["hook_index"]
            hook_loads[hook_index] = hook_loads.get(hook_index, 0) + 1

        print(f"Load distribution across hooks: {hook_loads}")

        # Verify even load distribution
        max_load = max(hook_loads.values())
        min_load = min(hook_loads.values())
        load_ratio = max_load / min_load if min_load > 0 else 1

        assert load_ratio < 2.0, f"Load imbalance too high: {load_ratio:.2f}:1"

        # Verify performance consistency
        execution_times = [result["execution_time_ms"] for result in all_results]
        avg_time = sum(execution_times) / len(execution_times)
        max_time = max(execution_times)

        print(f"Average operation time: {avg_time:.2f}ms")
        print(f"Max operation time: {max_time:.2f}ms")

        # Clean up
        for temp_dir in temp_dirs:
            temp_dir.__exit__(None, None, None)

    def test_burst_performance(self):
        """Test performance during burst operations."""
        target_ms = 2000.0  # 2 second target

        def burst_operation(operation_id: int) -> dict[str, Any]:
            """Execute a burst operation."""
            results = {}

            # Simulate burst of operations
            start_time = time.time()
            for i in range(5):  # 5 operations per burst
                test_file = f"P:\\temp\\burst_test_{operation_id}_{i}.txt"
                self.hook.validate_file_operation(test_file, "write")

            results["validation_time"] = (time.time() - start_time) * 1000

            # Simulate evidence burst
            start_time = time.time()
            for i in range(3):  # 3 evidence items per burst
                evidence = self.evidence_generator.create_file_evidence(
                    [f"P:\\temp\\burst_test_{operation_id}_{i}.txt"]
                )
                self.hook.log_evidence("burst_operations", evidence[0], [])

            results["evidence_time"] = (time.time() - start_time) * 1000

            return results

        # Execute burst operations
        with PerformanceTimer() as timer:
            num_bursts = 20
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = []
                for i in range(num_bursts):
                    future = executor.submit(burst_operation, i)
                    futures.append(future)

                # Collect results
                all_results = []
                for future in as_completed(futures):
                    try:
                        result = future.result()
                        all_results.append(result)
                    except Exception as e:
                        print(f"Burst operation error: {e}")

        # Verify performance target is met
        assert (
            timer.elapsed_ms < target_ms
        ), f"Burst operations took {timer.elapsed_ms}ms, target: {target_ms}ms"

        # Analyze burst performance
        for results in all_results:
            assert results["validation_time"] < 1000  # 1 second
            assert results["evidence_time"] < 500  # 0.5 seconds

        print(f"Burst performance completed in {timer.elapsed_ms:.2f}ms")
        print(
            f"Total operations: {num_bursts * 5} validations, {num_bursts * 3} evidence items"
        )
        print(f"Throughput: {(num_bursts * 8) / (timer.elapsed_ms / 1000):.2f} ops/sec")


if __name__ == "__main__":
    # Run the tests
    import pytest

    pytest.main([__file__, "-v"])
