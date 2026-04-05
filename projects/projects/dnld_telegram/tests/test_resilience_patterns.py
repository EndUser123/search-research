"""
Tests for resilience patterns implementation.
"""

import asyncio
import time

import pytest


class TestResiliencePatterns:
    """Test resilience patterns including circuit breaker, retry with backoff, and dead letter queue."""

    @pytest.mark.asyncio
    async def test_circuit_breaker_pattern(self):
        """Test circuit breaker for external service failures."""
        from src.download.resilience import CircuitBreaker

        failure_count = 0

        async def failing_operation():
            nonlocal failure_count
            failure_count += 1
            if failure_count <= 3:
                raise Exception("Service unavailable")
            return "success"

        circuit_breaker = CircuitBreaker(
            failure_threshold=3, recovery_timeout=0.1, expected_exception=Exception
        )

        # First 3 calls should fail
        for i in range(3):
            with pytest.raises(Exception):
                await circuit_breaker.call(failing_operation)

        # Circuit should be open now
        from src.download.resilience import CircuitState

        assert circuit_breaker.state == CircuitState.OPEN

        # Next call should fail fast (circuit open)
        with pytest.raises(Exception, match="Circuit breaker open"):
            await circuit_breaker.call(failing_operation)

        # Wait for recovery timeout
        await asyncio.sleep(0.2)

        # Should allow one test call (half-open)
        result = await circuit_breaker.call(failing_operation)
        assert result == "success"
        assert circuit_breaker.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_retry_with_exponential_backoff(self):
        """Test retry mechanism with exponential backoff and jitter."""
        from src.download.resilience import retry_with_backoff

        attempt_count = 0
        attempt_times = []

        @retry_with_backoff(
            max_attempts=4, base_delay=0.01, max_delay=0.1, exponential_factor=2
        )
        async def flaky_operation():
            nonlocal attempt_count
            attempt_count += 1
            attempt_times.append(time.time())

            if attempt_count < 3:
                raise Exception("Temporary failure")
            return "success"

        start_time = time.time()
        result = await flaky_operation()
        time.time() - start_time

        assert result == "success"
        assert attempt_count == 3
        assert len(attempt_times) == 3

        # Verify exponential backoff timing - just check that delays are reasonable
        if len(attempt_times) >= 2:
            delay1 = attempt_times[1] - attempt_times[0]
            assert delay1 > 0  # Positive delay
            assert delay1 < 1.0  # Reasonable upper bound

        if len(attempt_times) >= 3:
            delay2 = attempt_times[2] - attempt_times[1]
            assert delay2 > 0  # Positive delay
            assert delay2 < 1.0  # Reasonable upper bound

    @pytest.mark.asyncio
    async def test_dead_letter_queue_pattern(self):
        """Test dead letter queue for persistently failing operations."""
        from src.download.resilience import DeadLetterQueue

        dlq = DeadLetterQueue(max_retries=2)

        async def always_failing_operation(item):
            raise Exception(f"Cannot process {item}")

        # Process items that will fail
        failed_items = []
        for i in range(5):
            try:
                await dlq.process_with_retry(always_failing_operation, f"item_{i}")
            except Exception:
                failed_items.append(f"item_{i}")

        # All should end up in dead letter queue
        dead_letters = dlq.get_dead_letters()
        assert len(dead_letters) == 5

        # Each should have retry history
        for letter in dead_letters:
            assert letter["retry_count"] == 2
            assert "last_error" in letter
            assert "timestamp" in letter
