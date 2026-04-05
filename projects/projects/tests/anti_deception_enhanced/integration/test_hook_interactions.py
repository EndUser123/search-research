"""
Integration Tests for Hook Interactions

Tests the interactions between all hooks in the Enhanced Anti-Deception Architecture.
Validates PreToolUse, PostToolUse, LLM Supervisor, and Communication System integration.
"""

import json
import os
import sys
import time
from concurrent.futures import as_completed
from unittest.mock import Mock, patch

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


class TestHookInteractions:
    """Test suite for hook interactions integration."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.config = TestConfigHelper.create_minimal_config()
        self.hook = AntiDeceptionHook()
        self.mock_llm = MockLLM()
        self.mock_comm = MockCommunicationSystem()
        self.evidence_generator = EvidenceGenerator()
        self.temp_dir = TemporaryDirectory()

    def teardown_method(self):
        """Clean up after each test method."""
        self.temp_dir.__exit__(None, None, None)
        self.hook.reset_failures()
        self.mock_comm.clear_messages()

    def test_pre_to_post_tool_use_workflow(self):
        """Test complete workflow from Pre-Tool Use to Post-Tool Use."""
        with self.temp_dir as temp_path:
            # Step 1: Pre-Tool Use validation
            target_file = os.path.join(temp_path, "test_workflow.txt")
            is_safe, reason = self.hook.validate_file_operation(target_file, "write")

            assert is_safe is True
            assert "allowed" in reason.lower()

            # Step 2: Simulate file operation
            with open(target_file, "w") as f:
                f.write("Test workflow content")

            # Step 3: Post-Tool Use evidence collection
            evidence = self.evidence_generator.create_file_evidence([target_file])
            for ev in evidence:
                self.hook.log_evidence("file_operations", ev, [target_file])

            # Step 4: Post-Tool Use validation
            is_verified = self.hook.verify_file_exists(target_file)
            assert is_verified is True

            # Step 5: Task completion validation
            context = {
                "evidence_provided": True,
                "checklist": {
                    "evidence_provided": True,
                    "tests_written": True,
                    "tests_pass": True,
                },
            }

            can_complete, issues = self.hook.can_complete_task(context)
            assert len(issues) == 0 or can_complete is True

    def test_llm_supervisor_integration_workflow(self):
        """Test LLM Supervisor integration in the workflow."""
        with patch.object(self.hook, "_call_llm_api") as mock_llm_api:
            # Mock LLM response
            mock_response = Mock()
            mock_response.json.return_value = {
                "is_safe": True,
                "confidence": 0.95,
                "cost_estimate": 0.005,
                "reasoning": "File operation is safe and valid",
            }
            mock_llm_api.return_value = mock_response

            with self.temp_dir as temp_path:
                # Step 1: Pre-Tool Use validation with LLM
                target_file = os.path.join(temp_path, "llm_test.txt")
                operation_context = {
                    "operation": "write_file",
                    "target_path": target_file,
                    "content": "LLM test content",
                    "user_intent": "Create test file",
                }

                llm_result = self.hook._validate_with_llm_supervisor(operation_context)
                assert llm_result is not None

                # Step 2: Perform file operation
                with open(target_file, "w") as f:
                    f.write("LLM test content")

                # Step 3: Post-Tool Use evidence collection
                evidence = self.evidence_generator.create_file_evidence([target_file])
                self.hook.log_evidence("llm_validation", evidence[0], [target_file])

                # Step 4: Verify LLM cost tracking
                assert mock_llm_api.call_count == 1

    def test_communication_system_integration_workflow(self):
        """Test Communication System integration in the workflow."""
        with self.temp_dir as temp_path:
            # Step 1: Pre-Tool Use validation with communication
            target_file = os.path.join(temp_path, "comm_test.txt")

            # Send validation request to communication system
            validation_request = {
                "type": "pre_validation",
                "target_file": target_file,
                "operation": "write",
                "timestamp": time.time(),
            }

            request_sent = self.mock_comm.send_message(
                "pre_tool_use_hook", json.dumps(validation_request), "high"
            )
            assert request_sent is True

            # Step 2: Perform file operation
            with open(target_file, "w") as f:
                f.write("Communication test content")

            # Step 3: Post-Tool Use validation with communication
            validation_result = {
                "type": "post_validation",
                "target_file": target_file,
                "operation_successful": True,
                "evidence_collected": True,
                "timestamp": time.time(),
            }

            result_sent = self.mock_comm.send_message(
                "post_tool_use_hook", json.dumps(validation_result), "normal"
            )
            assert result_sent is True

            # Step 4: Verify communication system state
            assert self.mock_comm.get_message_count() == 2

            # Step 5: Process messages
            while self.mock_comm.get_message_count() > 0:
                msg = self.mock_comm.receive_message()
                if msg:
                    print(f"Processed {msg['message']}")

            assert self.mock_comm.get_message_count() == 0

    def test_full_integration_workflow(self):
        """Test complete integration workflow with all hooks."""
        with patch.object(self.hook, "_call_llm_api") as mock_llm_api:
            # Mock LLM response
            mock_response = Mock()
            mock_response.json.return_value = {
                "is_safe": True,
                "confidence": 0.92,
                "cost_estimate": 0.008,
                "reasoning": "Full integration test operation",
            }
            mock_llm_api.return_value = mock_response

            with self.temp_dir as temp_path:
                # Step 1: Pre-Tool Use validation with communication
                target_file = os.path.join(temp_path, "full_integration.txt")

                # Send pre-validation request
                pre_validation = {
                    "type": "pre_validation",
                    "target_file": target_file,
                    "operation": "write",
                    "user_intent": "Full integration test",
                }

                self.mock_comm.send_message(
                    "pre_tool_use_hook", json.dumps(pre_validation), "high"
                )

                # Step 2: LLM Supervisor validation
                operation_context = {
                    "operation": "write_file",
                    "target_path": target_file,
                    "content": "Full integration test content",
                    "user_intent": "Create test file",
                }

                llm_result = self.hook._validate_with_llm_supervisor(operation_context)
                assert llm_result is not None

                # Step 3: Perform file operation
                with open(target_file, "w") as f:
                    f.write("Full integration test content")

                # Step 4: Post-Tool Use evidence collection
                evidence = self.evidence_generator.create_file_evidence([target_file])
                for ev in evidence:
                    self.hook.log_evidence("file_operations", ev, [target_file])

                # Step 5: Send post-validation notification
                post_validation = {
                    "type": "post_validation",
                    "target_file": target_file,
                    "operation_successful": True,
                    "evidence_collected": True,
                    "llm_validated": True,
                    "timestamp": time.time(),
                }

                self.mock_comm.send_message(
                    "post_tool_use_hook", json.dumps(post_validation), "normal"
                )

                # Step 6: Task completion validation
                context = {
                    "evidence_provided": True,
                    "checklist": {
                        "evidence_provided": True,
                        "tests_written": True,
                        "tests_pass": True,
                        "code_reviewed": True,
                    },
                }

                can_complete, issues = self.hook.can_complete_task(context)
                assert len(issues) == 0 or can_complete is True

                # Step 7: Verify all components were used
                assert mock_llm_api.call_count == 1
                assert self.mock_comm.get_message_count() == 2
                assert len(self.hook.evidence_log) > 0

    def test_concurrent_hook_interactions(self):
        """Test concurrent interactions between hooks."""
        from concurrent.futures import ThreadPoolExecutor

        results = []
        errors = []

        def concurrent_workflow(workflow_id: int):
            try:
                with self.temp_dir as temp_path:
                    # Step 1: Pre-Tool Use validation
                    target_file = os.path.join(
                        temp_path, f"concurrent_{workflow_id}.txt"
                    )

                    is_safe, reason = self.hook.validate_file_operation(
                        target_file, "write"
                    )
                    assert is_safe is True

                    # Step 2: Perform file operation
                    with open(target_file, "w") as f:
                        f.write(f"Concurrent workflow {workflow_id}")

                    # Step 3: Evidence collection
                    evidence = self.evidence_generator.create_file_evidence(
                        [target_file]
                    )
                    self.hook.log_evidence(
                        "file_operations", evidence[0], [target_file]
                    )

                    # Step 4: Communication
                    validation_msg = {
                        "type": "concurrent_validation",
                        "workflow_id": workflow_id,
                        "target_file": target_file,
                        "timestamp": time.time(),
                    }

                    self.mock_comm.send_message(
                        "validation_system", json.dumps(validation_msg), "normal"
                    )

                    results.append(f"Workflow {workflow_id} completed")

            except Exception as e:
                errors.append(f"Workflow {workflow_id} failed: {str(e)}")

        # Run concurrent workflows
        num_workflows = 10
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(concurrent_workflow, i) for i in range(num_workflows)
            ]

            # Wait for all futures to complete
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    errors.append(f"Concurrent workflow failed: {str(e)}")

        # Verify results
        assert len(errors) == 0, f"Concurrent workflow errors: {errors}"
        assert len(results) == num_workflows

        # Verify communication system state
        assert self.mock_comm.get_message_count() == num_workflows

    def test_error_propagation_between_hooks(self):
        """Test error propagation between hooks."""
        with self.temp_dir as temp_path:
            # Test 1: Pre-Tool Use failure
            dangerous_file = "/etc/passwd"
            is_safe, reason = self.hook.validate_file_operation(dangerous_file, "write")

            assert is_safe is False
            assert (
                len(self.hook.validation_failures) == 0
            )  # Pre-Tool Use doesn't add failures

            # Test 2: Post-Tool Use evidence failure
            claim = "Evidence provided"
            evidence_result = self.hook.require_evidence(claim, [])
            assert evidence_result is False
            assert len(self.hook.validation_failures) > 0

            # Test 3: Task completion with failures
            context = {
                "evidence_provided": False,
                "checklist": {
                    "evidence_provided": False,
                    "tests_written": False,
                    "tests_pass": False,
                },
            }

            can_complete, issues = self.hook.can_complete_task(context)
            assert can_complete is False
            assert len(issues) > 0

            # Test 4: Communication system handles failures
            failure_msg = {
                "type": "validation_failure",
                "failures": len(self.hook.validation_failures),
                "timestamp": time.time(),
            }

            self.mock_comm.send_message(
                "error_handler", json.dumps(failure_msg), "high"
            )

            assert self.mock_comm.get_message_count() == 1

    def test_state_synchronization_between_hooks(self):
        """Test state synchronization between hooks."""
        # Initialize shared state
        shared_state = {
            "validation_failures": [],
            "evidence_log": [],
            "operation_count": 0,
            "last_validation": None,
        }

        def pre_tool_use_hook(file_path: str, operation: str):
            """Simulate Pre-Tool Use hook."""
            is_safe, reason = self.hook.validate_file_operation(file_path, operation)

            # Update shared state
            shared_state["operation_count"] += 1
            shared_state["last_validation"] = {
                "file_path": file_path,
                "operation": operation,
                "is_safe": is_safe,
                "timestamp": time.time(),
            }

            return is_safe, reason

        def post_tool_use_hook(file_path: str, evidence: list[str]):
            """Simulate Post-Tool Use hook."""
            for ev in evidence:
                self.hook.log_evidence("file_operations", ev, [file_path])

            # Update shared state
            shared_state["evidence_log"].extend(
                [
                    {
                        "type": "file_operations",
                        "evidence": ev,
                        "timestamp": time.time(),
                    }
                    for ev in evidence
                ]
            )

        def communication_hook(messages: list[dict]):
            """Simulate Communication hook."""
            for msg in messages:
                self.mock_comm.send_message(msg["to"], msg["message"], msg["priority"])
                shared_state["communication_count"] = (
                    shared_state.get("communication_count", 0) + 1
                )

        # Test state synchronization
        with self.temp_dir as temp_path:
            # Step 1: Pre-Tool Use hook
            target_file = os.path.join(temp_path, "state_test.txt")
            is_safe, reason = pre_tool_use_hook(target_file, "write")

            assert shared_state["operation_count"] == 1
            assert shared_state["last_validation"]["file_path"] == target_file
            assert shared_state["last_validation"]["is_safe"] is True

            # Step 2: Post-Tool Use hook
            evidence = self.evidence_generator.create_file_evidence([target_file])
            post_tool_use_hook(target_file, evidence)

            assert len(shared_state["evidence_log"]) > 0

            # Step 3: Communication hook
            messages = [
                {
                    "to": "validation_system",
                    "message": "State test message",
                    "priority": "normal",
                }
            ]
            communication_hook(messages)

            assert shared_state["communication_count"] == 1

            # Verify state consistency
            assert shared_state["operation_count"] == 1
            assert shared_state["communication_count"] == 1
            assert len(shared_state["evidence_log"]) > 0

    def test_performance_integration_workflow(self):
        """Test complete integration workflow with performance timing."""
        target_ms = 2000.0  # 2 second target

        with PerformanceTimer() as timer:
            with patch.object(self.hook, "_call_llm_api") as mock_llm_api:
                # Mock LLM response
                mock_response = Mock()
                mock_response.json.return_value = {
                    "is_safe": True,
                    "confidence": 0.90,
                    "cost_estimate": 0.005,
                    "reasoning": "Performance test operation",
                }
                mock_llm_api.return_value = mock_response

                with self.temp_dir as temp_path:
                    # Execute complete workflow
                    for i in range(5):  # Run 5 times to test performance
                        target_file = os.path.join(temp_path, f"perf_test_{i}.txt")

                        # Pre-Tool Use validation
                        is_safe, reason = self.hook.validate_file_operation(
                            target_file, "write"
                        )
                        assert is_safe is True

                        # File operation
                        with open(target_file, "w") as f:
                            f.write(f"Performance test {i}")

                        # Evidence collection
                        evidence = self.evidence_generator.create_file_evidence(
                            [target_file]
                        )
                        self.hook.log_evidence(
                            "file_operations", evidence[0], [target_file]
                        )

                        # LLM validation
                        operation_context = {
                            "operation": "write_file",
                            "target_path": target_file,
                            "content": f"Performance test {i}",
                            "user_intent": "Performance testing",
                        }

                        self.hook._validate_with_llm_supervisor(operation_context)

                        # Communication
                        validation_msg = {
                            "type": "performance_test",
                            "iteration": i,
                            "target_file": target_file,
                            "timestamp": time.time(),
                        }

                        self.mock_comm.send_message(
                            "performance_monitor", json.dumps(validation_msg), "normal"
                        )

                        # Task completion
                        context = {
                            "evidence_provided": True,
                            "checklist": {
                                "evidence_provided": True,
                                "tests_written": True,
                                "tests_pass": True,
                            },
                        }

                        self.hook.can_complete_task(context)

        # Should complete within 2 seconds
        assert (
            timer.elapsed_ms < target_ms
        ), f"Integration workflow took {timer.elapsed_ms}ms, target: {target_ms}ms"

    def test_hook_interaction_error_scenarios(self):
        """Test error scenarios in hook interactions."""
        # Test 1: File operation failure
        with self.temp_dir as temp_path:
            # Create read-only file
            read_only_file = os.path.join(temp_path, "read_only.txt")
            with open(read_only_file, "w") as f:
                f.write("read only content")

            # Make file read-only (simulated)
            os.chmod(read_only_file, 0o444)

            # Try to write to read-only file
            is_safe, reason = self.hook.validate_file_operation(read_only_file, "write")
            assert is_safe is False  # Should fail gracefully

        # Test 2: LLM API failure
        with patch.object(self.hook, "_call_llm_api") as mock_llm_api:
            mock_llm_api.side_effect = Exception("LLM API unavailable")

            operation_context = {
                "operation": "write_file",
                "target_path": "P:\\__csf\\test.txt",
                "content": "test content",
            }

            # Should fall back to rule-based validation
            result = self.hook._validate_with_llm_supervisor(operation_context)
            assert result is not None

        # Test 3: Communication system failure
        self.mock_comm.connected = False

        msg_sent = self.mock_comm.send_message("test", "test message", "normal")
        assert msg_sent is False

        # Test 4: Evidence collection failure
        evidence_result = self.hook.require_evidence("Test claim", None)
        assert evidence_result is False

        # Test 5: Task completion with mixed state
        context = {
            "evidence_provided": True,
            "checklist": {
                "evidence_provided": True,
                "tests_written": False,
                "tests_pass": False,
            },
        }

        can_complete, issues = self.hook.can_complete_task(context)
        assert len(issues) > 0

    def test_hook_interaction_status_reporting(self):
        """Test status reporting across all hooks."""
        # Execute various operations to populate state
        with self.temp_dir as temp_path:
            # Pre-Tool Use validation
            target_file = os.path.join(temp_path, "status_test.txt")
            self.hook.validate_file_operation(target_file, "write")

            # Evidence collection
            evidence = self.evidence_generator.create_file_evidence([target_file])
            self.hook.log_evidence("file_operations", evidence[0], [target_file])

            # Communication
            self.mock_comm.send_message("status_test", "status test message", "normal")

            # Validation failures
            self.hook.require_evidence("Test claim", [])

            # Generate comprehensive status report
            status = self.hook.get_status_report()

            # Verify status report includes information from all hooks
            assert "total_evidence_items" in status
            assert "validation_failures" in status
            assert "recent_failures" in status
            assert "evidence_summary" in status
            assert "config_loaded" in status

            # Verify specific hook information
            assert status["total_evidence_items"] > 0
            assert status["validation_failures"] > 0
            assert status["config_loaded"] is True

            # Verify communication system status
            comm_count = self.mock_comm.get_message_count()
            assert comm_count > 0


if __name__ == "__main__":
    # Run the tests
    import pytest

    pytest.main([__file__, "-v"])
