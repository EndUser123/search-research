"""
Monitoring and observability utilities for dnld_telegram
"""

import asyncio
import time
import uuid
from contextlib import asynccontextmanager, contextmanager
from typing import Any, Dict, Optional

from loguru import logger


class ObservabilityContext:
    """Manages observability context for tracking operations across the application."""

    def __init__(self):
        self._context_stack = []

    @asynccontextmanager
    async def async_operation_context(self, operation_name: str, **kwargs):
        """Async context manager for tracking operations with structured logging."""
        start_time = time.time()
        context_id = str(uuid.uuid4())[:8]

        # Create context data
        context_data = {
            "context_id": context_id,
            "operation": operation_name,
            "start_time": start_time,
            **kwargs,
        }

        # Add to context stack
        self._context_stack.append(context_data)

        # Add structured context for all logs within this context
        with logger.contextualize(**context_data):
            logger.info(f"START: {operation_name} (context_id: {context_id})")

            try:
                yield context_id
                elapsed = time.time() - start_time
                logger.info(
                    f"END: {operation_name} (context_id: {context_id}) - Duration: {elapsed:.2f}s"
                )
            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(
                    f"ERROR: {operation_name} (context_id: {context_id}) - Duration: {elapsed:.2f}s - Error: {str(e)}"
                )
                raise
            finally:
                # Remove from context stack
                if self._context_stack:
                    self._context_stack.pop()

    @contextmanager
    def operation_context(self, operation_name: str, **kwargs):
        """Sync context manager for tracking operations with structured logging."""
        start_time = time.time()
        context_id = str(uuid.uuid4())[:8]

        # Create context data
        context_data = {
            "context_id": context_id,
            "operation": operation_name,
            "start_time": start_time,
            **kwargs,
        }

        # Add to context stack
        self._context_stack.append(context_data)

        # Add structured context for all logs within this context
        with logger.contextualize(**context_data):
            logger.info(f"START: {operation_name} (context_id: {context_id})")

            try:
                yield context_id
                elapsed = time.time() - start_time
                logger.info(
                    f"END: {operation_name} (context_id: {context_id}) - Duration: {elapsed:.2f}s"
                )
            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(
                    f"ERROR: {operation_name} (context_id: {context_id}) - Duration: {elapsed:.2f}s - Error: {str(e)}"
                )
                raise
            finally:
                # Remove from context stack
                if self._context_stack:
                    self._context_stack.pop()

    def get_current_context(self) -> dict[str, Any] | None:
        """Get the current observability context."""
        return self._context_stack[-1] if self._context_stack else None

    def get_context_stack(self) -> list:
        """Get the full context stack."""
        return self._context_stack.copy()


# Global observability context instance
observability_context = ObservabilityContext()


def generate_correlation_id(prefix: str = "") -> str:
    """Generate a unique correlation ID for tracking requests across services."""
    timestamp = int(time.time() * 1000)  # Millisecond precision
    random_part = str(uuid.uuid4())[:8]
    return (
        f"{prefix}{timestamp}_{random_part}" if prefix else f"{timestamp}_{random_part}"
    )


async def test_concurrent_task_correlation():
    """Test that concurrent operations have unique correlation IDs."""
    correlation_ids = set()

    async def mock_operation():
        # Generate correlation ID for this operation
        correlation_id = generate_correlation_id("test_op")
        correlation_ids.add(correlation_id)
        await asyncio.sleep(0.01)
        return correlation_id

    # Run concurrent operations
    results = await asyncio.gather(*[mock_operation() for _ in range(10)])

    # All should have unique correlation IDs
    assert len(correlation_ids) == 10
    assert len(results) == 10

    return correlation_ids


# Export public API
__all__ = [
    "ObservabilityContext",
    "observability_context",
    "generate_correlation_id",
    "test_concurrent_task_correlation",
]
