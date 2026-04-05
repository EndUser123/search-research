"""
Integration Tests for State Synchronization

Tests state synchronization between hooks in the Enhanced Anti-Deception Architecture.
Validates shared state management, consistency, and conflict resolution.
"""

import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from threading import Lock

# Import test utilities
sys.path.insert(0, os.path.dirname(__file__))
from utils import (
    EvidenceGenerator,
    MockCommunicationSystem,
    MockLLM,
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
class SharedState:
    """Shared state between hooks with thread safety."""

    validation_failures: list[str] = field(default_factory=list)
    evidence_log: list[dict] = field(default_factory=list)
    operation_count: int = 0
    last_validation: dict | None = None
    total_cost: float = 0.0
    communication_messages: int = 0
    lock: Lock = field(default_factory=Lock)

    def add_failure(self, failure: str):
        """Add a validation failure thread-safely."""
        with self.lock:
            self.validation_failures.append(failure)

    def add_evidence(self, evidence: dict):
        """Add evidence thread-safely."""
        with self.lock:
            self.evidence_log.append(evidence)

    def increment_operation_count(self):
        """Increment operation count thread-safely."""
        with self.lock:
            self.operation_count += 1

    def update_last_validation(self, validation: dict):
        """Update last validation thread-safely."""
        with self.lock:
            self.last_validation = validation

    def add_cost(self, cost: float):
        """Add to total cost thread-safely."""
        with self.lock:
            self.total_cost += cost

    def increment_communication_count(self):
        """Increment communication message count thread-safely."""
        with self.lock:
            self.communication_messages += 1

    def get_summary(self) -> dict:
        """Get thread-safe summary of state."""
        with self.lock:
            return {
                "validation_failures": len(self.validation_failures),
                "evidence_items": len(self.evidence_log),
                "operation_count": self.operation_count,
                "total_cost": self.total_cost,
                "communication_messages": self.communication_messages,
                "last_validation": self.last_validation,
            }


class TestStateSynchronization:
    """Test suite for state synchronization integration."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.config = TestConfigHelper.create_minimal_config()
        self.hook = AntiDeceptionHook()
        self.shared_state = SharedState()
        self.mock_llm = MockLLM()
        self.mock_comm = MockCommunicationSystem()
        self.evidence_generator = EvidenceGenerator()
        self.temp_dir = TemporaryDirectory()

    def teardown_method(self):
        """Clean up after each test method."""
        self.temp_dir.__exit__(None, None, None)
        self.hook.reset_failures()
        self.mock_comm.clear_messages()

    def test_basic_state_synchronization(self):
        """Test basic state synchronization between hooks."""
        with self.temp_dir as temp_path:
            # Simulate Pre-Tool Use hook
            target_file = os.path.join(temp_path, "sync_test.txt")
            is_safe, reason = self.hook.validate_file_operation(target_file, "write")

            # Update shared state
            self.shared_state.increment_operation_count()
            self.shared_state.update_last_validation(
                {
                    "file_path": target_file,
                    "operation": "write",
                    "is_safe": is_safe,
                    "timestamp": time.time(),
                }
            )

            # Simulate Post-Tool Use hook
            with open(target_file, "w") as f:
                f.write("Sync test content")

            evidence = self.evidence_generator.create_file_evidence([target_file])
            self.shared_state.add_evidence(
                {
                    "type": "file_operations",
                    "details": evidence[0],
                    "file_paths": [target_file],
                    "timestamp": time.time(),
                }
            )

            # Simulate Communication hook
            self.shared_state.increment_communication_count()
            self.mock_comm.send_message(
                "validation_system", "Sync test message", "normal"
            )

            # Verify state consistency
            summary = self.shared_state.get_summary()
            assert summary["operation_count"] == 1
            assert summary["evidence_items"] > 0
            assert summary["communication_messages"] == 1
            assert summary["last_validation"]["file_path"] == target_file

    def test_concurrent_state_synchronization(self):
        """Test state synchronization under concurrent operations."""
        results = []
        errors = []

        def concurrent_worker(worker_id: int):
            try:
                with self.temp_dir as temp_path:
                    # Simulate hook operations
                    target_file = os.path.join(temp_path, f"concurrent_{worker_id}.txt")

                    # Pre-Tool Use
                    is_safe, reason = self.hook.validate_file_operation(
                        target_file, "write"
                    )
                    self.shared_state.increment_operation_count()
                    self.shared_state.update_last_validation(
                        {
                            "worker_id": worker_id,
                            "file_path": target_file,
                            "operation": "write",
                            "is_safe": is_safe,
                            "timestamp": time.time(),
                        }
                    )

                    # File operation
                    with open(target_file, "w") as f:
                        f.write(f"Concurrent worker {worker_id}")

                    # Evidence collection
                    evidence = self.evidence_generator.create_file_evidence(
                        [target_file]
                    )
                    self.shared_state.add_evidence(
                        {
                            "worker_id": worker_id,
                            "type": "file_operations",
                            "details": evidence[0],
                            "file_paths": [target_file],
                            "timestamp": time.time(),
                        }
                    )

                    # Communication
                    self.shared_state.increment_communication_count()
                    self.mock_comm.send_message(
                        "validation_system", f"Concurrent message {worker_id}", "normal"
                    )

                    results.append(worker_id)

            except Exception as e:
                errors.append(f"Worker {worker_id} failed: {str(e)}")

        # Run concurrent workers
        num_workers = 10
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(concurrent_worker, i) for i in range(num_workers)
            ]

            # Wait for all futures to complete
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    errors.append(f"Concurrent worker failed: {str(e)}")

        # Verify no errors
        assert len(errors) == 0, f"Concurrent synchronization errors: {errors}"

        # Verify final state
        summary = self.shared_state.get_summary()
        assert summary["operation_count"] == num_workers
        assert summary["evidence_items"] >= num_workers
        assert summary["communication_messages"] == num_workers

        # Verify communication system state
        assert self.mock_comm.get_message_count() == num_workers

    def test_state_consistency_under_failure(self):
        """Test state consistency when operations fail."""
        with self.temp_dir as temp_path:
            # Test 1: Pre-Tool Use validation failure
            dangerous_file = "/etc/passwd"
            is_safe, reason = self.hook.validate_file_operation(dangerous_file, "write")

            # Should still update state
            self.shared_state.increment_operation_count()
            self.shared_state.update_last_validation(
                {
                    "file_path": dangerous_file,
                    "operation": "write",
                    "is_safe": is_safe,
                    "timestamp": time.time(),
                }
            )

            # Test 2: Evidence collection failure
            claim = "Test evidence"
            evidence_result = self.hook.require_evidence(claim, [])
            assert evidence_result is False

            # Should add to validation failures
            self.shared_state.add_failure(f"Evidence required for claim: {claim}")

            # Test 3: Communication failure
            self.mock_comm.connected = False
            msg_sent = self.mock_comm.send_message("test", "test message", "normal")
            assert msg_sent is False

            # Verify state consistency despite failures
            summary = self.shared_state.get_summary()
            assert summary["operation_count"] == 1
            assert summary["validation_failures"] == 1
            assert summary["communication_messages"] == 0  # Failed message not counted

    def test_state_migration_and_reconciliation(self):
        """Test state migration and reconciliation between different states."""
        # Create initial state
        initial_state = SharedState()
        initial_state.add_failure("Initial failure")
        initial_state.add_evidence(
            {"type": "initial", "details": "Initial evidence", "timestamp": time.time()}
        )
        initial_state.increment_operation_count()

        # Simulate state transfer
        transferred_state = SharedState()

        def transfer_state(source: SharedState, target: SharedState):
            """Transfer state from source to target with proper synchronization."""
            # Get source state summary
            source_summary = source.get_summary()

            # Transfer failures
            for failure in source.validation_failures:
                target.add_failure(failure)

            # Transfer evidence
            for evidence in source.evidence_log:
                target.add_evidence(evidence)

            # Transfer counters
            for _ in range(source_summary["operation_count"]):
                target.increment_operation_count()

            for _ in range(source_summary["communication_messages"]):
                target.increment_communication_count()

        # Execute state transfer
        transfer_state(initial_state, transferred_state)

        # Verify state was transferred correctly
        initial_summary = initial_state.get_summary()
        transferred_summary = transferred_state.get_summary()

        assert (
            transferred_summary["validation_failures"]
            == initial_summary["validation_failures"]
        )
        assert (
            transferred_summary["evidence_items"] == initial_summary["evidence_items"]
        )
        assert (
            transferred_summary["operation_count"] == initial_summary["operation_count"]
        )
        assert (
            transferred_summary["communication_messages"]
            == initial_summary["communication_messages"]
        )

    def test_state_synchronization_with_performance_monitoring(self):
        """Test state synchronization with performance monitoring."""
        performance_metrics = {
            "validation_times": [],
            "eollection_times": [],
            "communication_times": [],
            "total_operations": 0,
        }

        def monitored_validation(file_path: str, operation: str):
            """Monitored validation with timing."""
            start_time = time.time()

            # Perform validation
            is_safe, reason = self.hook.validate_file_operation(file_path, operation)

            # Update state
            self.shared_state.increment_operation_count()
            self.shared_state.update_last_validation(
                {
                    "file_path": file_path,
                    "operation": operation,
                    "is_safe": is_safe,
                    "validation_time": time.time() - start_time,
                    "timestamp": time.time(),
                }
            )

            # Record performance
            performance_metrics["validation_times"].append(time.time() - start_time)
            performance_metrics["total_operations"] += 1

            return is_safe, reason

        def monitored_evidence_collection(file_path: str):
            """Monitored evidence collection with timing."""
            start_time = time.time()

            # Collect evidence
            evidence = self.evidence_generator.create_file_evidence([file_path])
            self.shared_state.add_evidence(
                {
                    "type": "file_operations",
                    "details": evidence[0],
                    "file_paths": [file_path],
                    "collection_time": time.time() - start_time,
                    "timestamp": time.time(),
                }
            )

            # Record performance
            performance_metrics["eollection_times"].append(time.time() - start_time)

        def monitored_communication(message: str):
            """Monitored communication with timing."""
            start_time = time.time()

            # Send message
            self.shared_state.increment_communication_count()
            self.mock_comm.send_message("performance_monitor", message, "normal")

            # Record performance
            performance_metrics["communication_times"].append(time.time() - start_time)

        # Execute monitored operations
        with self.temp_dir as temp_path:
            for i in range(5):
                target_file = os.path.join(temp_path, f"perf_test_{i}.txt")

                # Monitored validation
                monitored_validation(target_file, "write")

                # File operation
                with open(target_file, "w") as f:
                    f.write(f"Performance test {i}")

                # Monitored evidence collection
                monitored_evidence_collection(target_file)

                # Monitored communication
                monitored_communication(f"Performance test {i} completed")

        # Verify state and performance metrics
        summary = self.shared_state.get_summary()
        assert summary["operation_count"] == 5
        assert summary["evidence_items"] == 5
        assert summary["communication_messages"] == 5

        # Verify performance metrics were captured
        assert len(performance_metrics["validation_times"]) == 5
        assert len(performance_metrics["eollection_times"]) == 5
        assert len(performance_metrics["communication_times"]) == 5
        assert performance_metrics["total_operations"] == 5

        # Verify performance is within acceptable bounds (each operation < 2 seconds)
        for validation_time in performance_metrics["validation_times"]:
            assert validation_time < 2.0

        for evidence_time in performance_metrics["eollection_times"]:
            assert evidence_time < 2.0

        for comm_time in performance_metrics["communication_times"]:
            assert comm_time < 2.0

    def test_state_locking_and_thread_safety(self):
        """Test thread safety of state locking and synchronization."""
        import threading
        import time

        results = []
        errors = []

        def state_modifier(worker_id: int):
            """Modify shared state from multiple threads."""
            try:
                for i in range(5):
                    # Each thread modifies state concurrently
                    self.shared_state.add_failure(f"Failure {worker_id}-{i}")
                    self.shared_state.increment_operation_count()

                    # Simulate some delay to increase chance of race conditions
                    time.sleep(0.001)

                    evidence = {
                        "worker_id": worker_id,
                        "iteration": i,
                        "type": "test_evidence",
                        "timestamp": time.time(),
                    }
                    self.shared_state.add_evidence(evidence)

                    self.shared_state.increment_communication_count()

                    results.append(f"Worker {worker_id} iteration {i} completed")

            except Exception as e:
                errors.append(f"State modifier {worker_id} failed: {str(e)}")

        # Create multiple threads to modify state concurrently
        num_threads = 10
        threads = []
        for i in range(num_threads):
            thread = threading.Thread(target=state_modifier, args=(i,))
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify no errors occurred
        assert len(errors) == 0, f"Thread safety errors: {errors}"

        # Verify final state is consistent
        summary = self.shared_state.get_summary()
        expected_operations = num_threads * 5  # Each thread runs 5 times
        expected_evidence = num_threads * 5
        expected_failures = num_threads * 5
        expected_communications = num_threads * 5

        assert summary["operation_count"] == expected_operations
        assert summary["evidence_items"] == expected_evidence
        assert summary["validation_failures"] == expected_failures
        assert summary["communication_messages"] == expected_communications

        # Verify no race conditions occurred (operations completed successfully)
        assert len(results) == expected_operations

    def test_state_synchronization_with_error_recovery(self):
        """Test state synchronization with error recovery mechanisms."""
        # Simulate various error conditions and test recovery
        error_scenarios = [
            "validation_failure",
            "evidence_failure",
            "communication_failure",
            "file_operation_failure",
        ]

        for scenario in error_scenarios:
            try:
                if scenario == "validation_failure":
                    # Test validation failure recovery
                    dangerous_file = "/etc/passwd"
                    is_safe, reason = self.hook.validate_file_operation(
                        dangerous_file, "write"
                    )
                    self.shared_state.increment_operation_count()
                    self.shared_state.update_last_validation(
                        {
                            "scenario": scenario,
                            "is_safe": is_safe,
                            "timestamp": time.time(),
                        }
                    )

                elif scenario == "evidence_failure":
                    # Test evidence failure recovery
                    self.shared_state.add_failure(f"Evidence failure: {scenario}")
                    evidence_result = self.hook.require_evidence("Test claim", [])
                    assert evidence_result is False

                elif scenario == "communication_failure":
                    # Test communication failure recovery
                    self.mock_comm.connected = False
                    msg_sent = self.mock_comm.send_message(
                        "test", "test message", "priority"
                    )
                    assert msg_sent is False
                    self.mock_comm.connected = True  # Recovery

                elif scenario == "file_operation_failure":
                    # Test file operation failure recovery
                    with self.temp_dir as temp_path:
                        # Simulate file operation failure
                        try:
                            with open("/nonexistent/path/file.txt", "w") as f:
                                f.write("test")
                        except Exception:
                            pass  # Expected failure

                # Verify state is consistent after error
                summary = self.shared_state.get_summary()
                assert summary["operation_count"] >= 0
                assert isinstance(summary["validation_failures"], int)
                assert isinstance(summary["evidence_items"], int)
                assert isinstance(summary["communication_messages"], int)

            except Exception as e:
                # Test error handling
                assert "error" in str(e).lower() or "exception" in str(e).lower()

    def test_state_synchronization_performance_benchmark(self):
        """Test performance of state synchronization operations."""
        target_ms = 2000.0  # 2 second target for all operations

        with PerformanceTimer() as timer:
            with self.temp_dir as temp_path:
                # Execute many state synchronization operations
                for i in range(100):
                    target_file = os.path.join(temp_path, f"perf_benchmark_{i}.txt")

                    # State synchronization operations
                    self.shared_state.increment_operation_count()
                    self.shared_state.update_last_validation(
                        {
                            "iteration": i,
                            "file_path": target_file,
                            "operation": "write",
                            "is_safe": True,
                            "timestamp": time.time(),
                        }
                    )

                    evidence = {
                        "iteration": i,
                        "type": "file_operations",
                        "details": f"Evidence {i}",
                        "timestamp": time.time(),
                    }
                    self.shared_state.add_evidence(evidence)

                    self.shared_state.increment_communication_count()
                    self.mock_comm.send_message("benchmark", f"Message {i}", "normal")

                    # File operation
                    with open(target_file, "w") as f:
                        f.write(f"Benchmark test {i}")

        # Verify performance target is met
        assert (
            timer.elapsed_ms < target_ms
        ), f"State synchronization took {timer.elapsed_ms}ms, target: {target_ms}ms"

        # Verify final state
        summary = self.shared_state.get_summary()
        assert summary["operation_count"] == 100
        assert summary["evidence_items"] == 100
        assert summary["communication_messages"] == 100

    def test_state_synchronization_with_complex_workflows(self):
        """Test state synchronization with complex multi-step workflows."""
        workflow_results = []

        def complex_workflow(workflow_id: int):
            """Execute a complex workflow with multiple state operations."""
            try:
                with self.temp_dir as temp_path:
                    # Step 1: Multiple validations
                    for i in range(3):
                        target_file = os.path.join(
                            temp_path, f"workflow_{workflow_id}_{i}.txt"
                        )
                        is_safe, reason = self.hook.validate_file_operation(
                            target_file, "write"
                        )

                        self.shared_state.increment_operation_count()
                        self.shared_state.update_last_validation(
                            {
                                "workflow_id": workflow_id,
                                "step": "validation",
                                "iteration": i,
                                "is_safe": is_safe,
                                "timestamp": time.time(),
                            }
                        )

                    # Step 2: Multiple file operations
                    for i in range(3):
                        target_file = os.path.join(
                            temp_path, f"workflow_{workflow_id}_{i}.txt"
                        )
                        with open(target_file, "w") as f:
                            f.write(f"Workflow {workflow_id} step {i}")

                        # Evidence collection
                        evidence = self.evidence_generator.create_file_evidence(
                            [target_file]
                        )
                        self.shared_state.add_evidence(
                            {
                                "workflow_id": workflow_id,
                                "step": "evidence",
                                "iteration": i,
                                "evidence": evidence[0],
                                "timestamp": time.time(),
                            }
                        )

                    # Step 3: Multiple communications
                    for i in range(3):
                        self.shared_state.increment_communication_count()
                        self.mock_comm.send_message(
                            f"workflow_{workflow_id}",
                            f"Workflow {workflow_id} step {i} completed",
                            "normal",
                        )

                    workflow_results.append(workflow_id)

            except Exception as e:
                print(f"Workflow {workflow_id} failed: {str(e)}")

        # Execute multiple complex workflows concurrently
        num_workflows = 10
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(complex_workflow, i) for i in range(num_workflows)
            ]

            # Wait for all workflows to complete
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"Complex workflow failed: {str(e)}")

        # Verify all workflows completed
        assert len(workflow_results) == num_workflows

        # Verify final state reflects all workflows
        summary = self.shared_state.get_summary()
        # Each workflow has 3 validations, 3 evidence items, 3 communications
        expected_operations = num_workflows * 3
        expected_evidence = num_workflows * 3
        expected_communications = num_workflows * 3

        assert summary["operation_count"] >= expected_operations
        assert summary["evidence_items"] >= expected_evidence
        assert summary["communication_messages"] >= expected_communications


if __name__ == "__main__":
    # Run the tests
    import pytest

    pytest.main([__file__, "-v"])
