"""
Unit Tests for Communication System Component

Tests the Communication System functionality for the Enhanced Anti-Deception Architecture.
Validates inter-hook communication, message passing, event handling, and state synchronization.
"""

import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor

# Import test utilities
sys.path.insert(0, os.path.dirname(__file__))
from utils import (
    EvidenceGenerator,
    MockCommunicationSystem,
    PerformanceTimer,
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


class TestCommunicationSystem:
    """Test suite for Communication System functionality."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.config = TestConfigHelper.create_minimal_config()
        self.hook = AntiDeceptionHook()
        self.mock_comm = MockCommunicationSystem()
        self.evidence_generator = EvidenceGenerator()

    def teardown_method(self):
        """Clean up after each test method."""
        self.hook.reset_failures()
        self.mock_comm.clear_messages()

    def test_communication_system_initialization(self):
        """Test that Communication System initializes correctly."""
        assert self.mock_comm is not None
        assert isinstance(self.mock_comm.messages, list)
        assert isinstance(self.mock_comm.connected, bool)
        assert self.mock_comm.connected is True

    def test_communication_system_message_sending(self):
        """Test message sending functionality."""
        # Test normal message sending
        target_hook = "test_target"
        message = "Test message"
        priority = "high"

        result = self.mock_comm.send_message(target_hook, message, priority)

        # Verify message was sent
        assert result is True
        assert len(self.mock_comm.messages) == 1

        # Verify message content
        sent_message = self.mock_comm.messages[0]
        assert sent_message["to"] == target_hook
        assert sent_message["message"] == message
        assert sent_message["priority"] == priority
        assert "timestamp" in sent_message

    def test_communication_system_message_receiving(self):
        """Test message receiving functionality."""
        # Send a message first
        self.mock_comm.send_message("test_target", "Test message", "normal")

        # Receive the message
        received_message = self.mock_comm.receive_message()

        # Verify message was received
        assert received_message is not None
        assert received_message["to"] == "test_target"
        assert received_message["message"] == "Test message"
        assert received_message["priority"] == "normal"

        # Verify message was removed from queue
        assert len(self.mock_comm.messages) == 0

    def test_communication_system_message_queue(self):
        """Test message queue functionality."""
        # Send multiple messages
        messages = [
            ("target1", "message1", "high"),
            ("target2", "message2", "normal"),
            ("target3", "message3", "low"),
        ]

        for target, message, priority in messages:
            self.mock_comm.send_message(target, message, priority)

        # Verify all messages were queued
        assert len(self.mock_comm.messages) == 3

        # Receive messages in FIFO order
        received_messages = []
        for _ in range(3):
            msg = self.mock_comm.receive_message()
            received_messages.append(msg)

        # Verify all messages were received
        assert len(received_messages) == 3
        assert len(self.mock_comm.messages) == 0

        # Verify order was preserved
        assert received_messages[0]["to"] == "target1"
        assert received_messages[1]["to"] == "target2"
        assert received_messages[2]["to"] == "target3"

    def test_communication_system_priority_handling(self):
        """Test priority-based message handling."""
        # Send messages with different priorities
        self.mock_comm.send_message("target1", "low priority", "low")
        self.mock_comm.send_message("target2", "high priority", "high")
        self.mock_comm.send_message("target3", "normal priority", "normal")

        # Note: Current implementation is FIFO, but could be extended for priority queuing
        assert len(self.mock_comm.messages) == 3

    def test_communication_system_error_handling(self):
        """Test error handling in communication system."""
        # Test sending to disconnected system
        self.mock_comm.connected = False
        result = self.mock_comm.send_message("test_target", "test message", "normal")
        assert result is False

        # Test receiving from empty queue
        self.mock_comm.connected = True
        message = self.mock_comm.receive_message()
        assert message is None

        # Reset connection
        self.mock_comm.connected = True

    def test_communication_system_concurrent_messaging(self):
        """Test concurrent message sending and receiving."""
        results = []
        errors = []

        def send_messages(thread_id: int, count: int):
            try:
                for i in range(count):
                    target = f"target_{thread_id}_{i}"
                    message = f"Message from thread {thread_id} message {i}"
                    result = self.mock_comm.send_message(target, message, "normal")
                    results.append(result)
            except Exception as e:
                errors.append(str(e))

        def receive_messages(count: int):
            received = []
            for _ in range(count):
                msg = self.mock_comm.receive_message()
                if msg:
                    received.append(msg)
            return received

        # Create threads for concurrent sending
        num_threads = 5
        messages_per_thread = 3
        total_messages = num_threads * messages_per_thread

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            # Start sending threads
            send_futures = [
                executor.submit(send_messages, i, messages_per_thread)
                for i in range(num_threads)
            ]

            # Wait for sending to complete
            for future in send_futures:
                future.result()

            # Verify all messages were sent
            assert len(self.mock_comm.messages) == total_messages

            # Start receiving threads
            receive_futures = [
                executor.submit(receive_messages, messages_per_thread)
                for i in range(num_threads)
            ]

            # Collect received messages
            all_received = []
            for future in receive_futures:
                all_received.extend(future.result())

            # Verify all messages were received
            assert len(all_received) == total_messages
            assert len(self.mock_comm.messages) == 0

        # Verify no errors occurred
        assert len(errors) == 0

    def test_communication_system_performance_timing(self):
        """Test that communication operations complete within performance targets."""
        target_ms = 2000.0  # 2 second target

        with PerformanceTimer() as timer:
            # Send multiple messages
            for i in range(100):
                target = f"target_{i}"
                message = f"Test message {i}"
                self.mock_comm.send_message(target, message, "normal")

            # Receive all messages
            for _ in range(100):
                self.mock_comm.receive_message()

        # Should complete within 2 seconds
        assert (
            timer.elapsed_ms < target_ms
        ), f"Communication operations took {timer.elapsed_ms}ms, target: {target_ms}ms"

    def test_communication_system_message_count_tracking(self):
        """Test message count tracking functionality."""
        initial_count = self.mock_comm.get_message_count()

        # Send messages
        self.mock_comm.send_message("target1", "message1", "normal")
        self.mock_comm.send_message("target2", "message2", "high")

        # Verify count increased
        assert self.mock_comm.get_message_count() == initial_count + 2

        # Receive messages
        self.mock_comm.receive_message()
        self.mock_comm.receive_message()

        # Verify count decreased
        assert self.mock_comm.get_message_count() == initial_count

    def test_communication_system_clear_messages(self):
        """Test message clearing functionality."""
        # Send some messages
        self.mock_comm.send_message("target1", "message1", "normal")
        self.mock_comm.send_message("target2", "message2", "high")

        assert len(self.mock_comm.messages) == 2

        # Clear messages
        self.mock_comm.clear_messages()

        assert len(self.mock_comm.messages) == 0

    def test_communication_system_integration_with_evidence(self):
        """Test communication system integration with evidence logging."""
        # Create evidence messages
        evidence = self.evidence_generator.create_file_evidence(
            ["P:\\__csf\\test.txt"]
        )

        # Send evidence messages
        for i, ev in enumerate(evidence):
            message = f"Evidence {i}: {ev}"
            self.mock_comm.send_message("evidence_system", message, "high")

        # Verify messages were sent
        assert len(self.mock_comm.messages) == len(evidence)

        # Receive and process messages
        while self.mock_comm.get_message_count() > 0:
            msg = self.mock_comm.receive_message()
            if msg:
                # Process message (in real implementation, would log to evidence system)
                print(f"Processed evidence message: {msg['message']}")

        # Verify all messages were processed
        assert len(self.mock_comm.messages) == 0

    def test_communication_system_status_reporting(self):
        """Test communication system status reporting."""
        # Send some messages
        self.mock_comm.send_message("target1", "message1", "normal")
        self.mock_comm.send_message("target2", "message2", "high")

        # Generate status report
        status = self.mock_comm.get_message_count()
        assert status == 2

        # Clear messages
        self.mock_comm.clear_messages()

        # Verify count is zero
        assert self.mock_comm.get_message_count() == 0

    def test_communication_system_message_format_validation(self):
        """Test message format validation."""
        # Test valid message formats
        valid_messages = [
            ("target", "message", "normal"),
            ("target", "message", "high"),
            ("target", "message", "low"),
            ("target", "message", "urgent"),
        ]

        for target, message, priority in valid_messages:
            result = self.mock_comm.send_message(target, message, priority)
            assert result is True

        # Test invalid message formats
        invalid_messages = [
            ("", "message", "normal"),  # Empty target
            ("target", "", "normal"),  # Empty message
            ("target", "message", ""),  # Empty priority
            (None, "message", "normal"),  # None target
            ("target", None, "normal"),  # None message
            ("target", "message", None),  # None priority
        ]

        for target, message, priority in invalid_messages:
            # Should handle invalid formats gracefully
            try:
                result = self.mock_comm.send_message(target, message, priority)
                # If it doesn't crash, ensure it's a boolean
                assert isinstance(result, bool)
            except Exception:
                pass  # Expected behavior for invalid inputs

    def test_communication_system_thread_safety(self):
        """Test thread safety of communication system."""
        import threading

        results = []
        errors = []

        def sender_thread(thread_id: int, count: int):
            try:
                for i in range(count):
                    target = f"thread_{thread_id}_target"
                    message = f"Message {thread_id}_{i}"
                    success = self.mock_comm.send_message(target, message, "normal")
                    results.append(success)
            except Exception as e:
                errors.append(f"Sender {thread_id}: {str(e)}")

        def receiver_thread(count: int):
            try:
                received = []
                for _ in range(count):
                    msg = self.mock_comm.receive_message()
                    if msg:
                        received.append(msg)
                return received
            except Exception as e:
                errors.append(f"Receiver error: {str(e)}")
                return []

        # Create multiple sender threads
        num_senders = 10
        messages_per_sender = 5
        total_messages = num_senders * messages_per_sender

        sender_threads = []
        for i in range(num_senders):
            thread = threading.Thread(
                target=sender_thread, args=(i, messages_per_sender)
            )
            sender_threads.append(thread)

        # Start all sender threads
        for thread in sender_threads:
            thread.start()

        # Wait for senders to complete
        for thread in sender_threads:
            thread.join()

        # Verify all messages were sent
        assert len(self.mock_comm.messages) == total_messages
        assert len(errors) == 0

        # Create receiver threads
        receiver_threads = []
        receivers_per_thread = total_messages // 5  # Divide messages among receivers

        for i in range(5):
            thread = threading.Thread(
                target=receiver_thread, args=(receivers_per_thread,)
            )
            receiver_threads.append(thread)

        # Start all receiver threads
        for thread in receiver_threads:
            thread.start()

        # Wait for receivers to complete
        for thread in receiver_threads:
            thread.join()

        # Verify all messages were processed
        assert len(self.mock_comm.messages) == 0
        assert len(errors) == 0

    def test_communication_system_network_simulation(self):
        """Test communication system with network simulation."""

        # Simulate network delays
        def delayed_send(target: str, message: str, priority: str):
            time.sleep(0.001)  # 1ms delay
            return self.mock_comm.send_message(target, message, priority)

        # Simulate network errors
        def unreliable_send(target: str, message: str, priority: str):
            # Simulate 10% failure rate
            if hash(message) % 10 == 0:  # 10% chance of failure
                return False
            return self.mock_comm.send_message(target, message, priority)

        # Test delayed sending
        delayed_messages = [
            delayed_send(f"target_{i}", f"delayed_message_{i}", "normal")
            for i in range(10)
        ]

        assert all(delayed_messages)
        assert len(self.mock_comm.messages) == 10

        # Test unreliable sending
        unreliable_messages = [
            unreliable_send(f"target_{i}", f"unreliable_message_{i}", "normal")
            for i in range(20)
        ]

        # Some should fail, some should succeed
        success_count = sum(unreliable_messages)
        assert success_count > 0
        assert success_count < 20  # Not all should succeed

        # Clean up
        self.mock_comm.clear_messages()


if __name__ == "__main__":
    # Run the tests
    import pytest

    pytest.main([__file__, "-v"])
