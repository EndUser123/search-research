import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4

from .adapter_factory import cks_adapter_factory
from .interfaces.base_adapter import CKSContext, IntegrationResult, IntegrationType

"""CKS Integration Manager

Central manager for coordinating all CKS integrations.
Provides high-level interface for system-wide CKS operations.

Constitutional Requirements:
- Solo developer optimization (simple interface)
- Evidence-based implementation (clear operations)
- Force multiplier integration (system-wide coordination)
- No enterprise bloat (direct Python usage)
"""


logger = logging.getLogger(__name__)


@dataclass
class OperationMetrics:
    """Metrics for CKS integration operations."""

    operation_id: str
    integration_type: str
    start_time: datetime
    end_time: datetime | None = None
    success: bool = False
    error: str | None = None
    processing_time_ms: float | None = None


@dataclass
class SystemMetrics:
    """System-wide CKS integration metrics."""

    total_operations: int = 0
    successful_operations: int = 0
    failed_operations: int = 0
    adapter_metrics: dict[str, Any] = field(default_factory=dict)
    operation_history: list[OperationMetrics] = field(default_factory=list)


class CKSIntegrationManager:
    """Central manager for CKS integrations.

    Coordinates all CKS integration operations, provides system-wide
    metrics, and ensures consistent behavior across integrations.
    """

    def __init__(self) -> None:
        """Initialize the integration manager."""
        self.logger = logging.getLogger(f"{__name__}.CKSIntegrationManager")
        self.metrics = SystemMetrics()
        self._active_operations: dict[str, CKSContext] = {}

    def initialize_all_integrations(
        self,
        configs: dict[IntegrationType, dict[str, Any]] | None = None,
    ) -> IntegrationResult:
        """Initialize all CKS integrations.

        Args:
            configs: Configuration for each integration type

        Returns:
            IntegrationResult indicating overall success

        """
        try:
            self.logger.info("Initializing all CKS integrations")

            results = cks_adapter_factory.initialize_all_adapters(configs)

            successful = sum(1 for r in results.values() if r.success)
            total = len(results)

            if successful == total:
                self.logger.info(f"Successfully initialized all {total} CKS integrations")
                return IntegrationResult(
                    success=True,
                    data={"initialized_count": total, "successful_count": successful},
                )
            self.logger.warning(f"Initialized {successful}/{total} CKS integrations")
            failed_integrations = [
                integration_type.value
                for integration_type, result in results.items()
                if not result.success
            ]
            return IntegrationResult(
                success=False,
                error=f"Failed to initialize integrations: {', '.join(failed_integrations)}",
                data={"initialized_count": successful, "failed_integrations": failed_integrations},
            )

        except Exception as e:
            self.logger.exception(f"Error initializing CKS integrations: {e!s}")
            return IntegrationResult(
                success=False,
                error=f"Initialization error: {e!s}",
            )

    def create_context(
        self,
        integration_type: IntegrationType,
        operation_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> CKSContext:
        """Create a CKS context for integration operations.

        Args:
            integration_type: Type of integration
            operation_id: Unique operation identifier
            metadata: Additional context metadata

        Returns:
            CKS context instance

        """
        return CKSContext(
            integration_type=integration_type,
            operation_id=operation_id,
            metadata=metadata,
        )

    def process_with_integration(
        self,
        integration_type: IntegrationType,
        operation_data: dict[str, Any],
        config: dict[str, Any] | None = None,
    ) -> IntegrationResult:
        """Process operation using specific integration.

        Args:
            integration_type: Type of integration to use
            operation_data: Data for the operation
            config: Additional configuration (optional)

        Returns:
            IntegrationResult with processed data

        """
        start_time = datetime.now()
        operation_id = str(uuid4())

        try:
            # Create context
            context = cks_adapter_factory.create_context(
                integration_type=integration_type,
                operation_id=operation_id,
                metadata={"operation_data": operation_data},
            )

            # Track active operation
            self._active_operations[operation_id] = context

            # Get adapter
            adapter = cks_adapter_factory.adapter_registry.get_adapter(integration_type)
            if not adapter:
                return IntegrationResult(
                    success=False,
                    error=f"No adapter available for {integration_type.value}",
                )

            # Validate context
            if not adapter.validate_context(context):
                return IntegrationResult(
                    success=False,
                    error="Invalid context provided",
                )

            # Process with adapter
            result = adapter.process_context(context)

            # Record metrics
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds() * 1000

            operation_metrics = OperationMetrics(
                operation_id=operation_id,
                integration_type=integration_type.value,
                start_time=start_time,
                end_time=end_time,
                success=result.success,
                error=result.error,
                processing_time_ms=processing_time,
            )

            self._record_operation_metrics(operation_metrics)

            # Log operation
            adapter.log_operation(
                operation=f"process_{integration_type.value}",
                context=context,
                result=result,
            )

            # Clean up active operation
            self._active_operations.pop(operation_id, None)

            return result

        except Exception as e:
            # Record failed operation
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds() * 1000

            operation_metrics = OperationMetrics(
                operation_id=operation_id,
                integration_type=integration_type.value,
                start_time=start_time,
                end_time=end_time,
                success=False,
                error=str(e),
                processing_time_ms=processing_time,
            )

            self._record_operation_metrics(operation_metrics)

            # Clean up active operation
            self._active_operations.pop(operation_id, None)

            self.logger.exception(f"Error processing with {integration_type.value}: {e!s}")
            return IntegrationResult(
                success=False,
                error=f"Processing error: {e!s}",
            )

    def _record_operation_metrics(self, metrics: OperationMetrics) -> None:
        """Record operation metrics.

        Args:
            metrics: Operation metrics to record

        """
        self.metrics.total_operations += 1

        if metrics.success:
            self.metrics.successful_operations += 1
        else:
            self.metrics.failed_operations += 1

        # Keep only last 100 operations in history
        self.metrics.operation_history.append(metrics)
        if len(self.metrics.operation_history) > 100:
            self.metrics.operation_history.pop(0)

    def get_system_metrics(self) -> dict[str, Any]:
        """Get system-wide metrics.

        Returns:
            Dictionary of system metrics

        """
        # Update adapter metrics
        self.metrics.adapter_metrics = cks_adapter_factory.get_adapter_metrics()

        # Calculate success rate
        success_rate = 0.0
        if self.metrics.total_operations > 0:
            success_rate = (
                self.metrics.successful_operations / self.metrics.total_operations
            ) * 100

        return {
            "operation_metrics": {
                "total_operations": self.metrics.total_operations,
                "successful_operations": self.metrics.successful_operations,
                "failed_operations": self.metrics.failed_operations,
                "success_rate_percent": round(success_rate, 2),
                "active_operations": len(self._active_operations),
            },
            "adapter_metrics": self.metrics.adapter_metrics,
            "recent_operations": [
                {
                    "operation_id": op.operation_id,
                    "integration_type": op.integration_type,
                    "success": op.success,
                    "processing_time_ms": op.processing_time_ms,
                    "timestamp": op.end_time.isoformat() if op.end_time else None,
                }
                for op in self.metrics.operation_history[-10:]  # Last 10 operations
            ],
        }

    def get_active_operations(self) -> list[dict[str, Any]]:
        """Get list of currently active operations.

        Returns:
            List of active operation details

        """
        return [
            {
                "operation_id": context.operation_id,
                "integration_type": context.integration_type.value,
                "session_id": context.session_id,
                "metadata": context.metadata,
            }
            for context in self._active_operations.values()
        ]

    def list_available_integrations(self) -> list[str]:
        """Get list of available integration types.

        Returns:
            List of available integration type names

        """
        integrations = cks_adapter_factory.get_available_integrations()
        return [integration.value for integration in integrations]

    def shutdown(self) -> None:
        """Shutdown the integration manager and clean up resources."""
        try:
            self.logger.info("Shutting down CKS Integration Manager")

            # Clear active operations
            active_count = len(self._active_operations)
            if active_count > 0:
                self.logger.warning(f"Clearing {active_count} active operations during shutdown")
                self._active_operations.clear()

            # Final metrics logging
            metrics = self.get_system_metrics()
            self.logger.info(f"Final metrics: {metrics['operation_metrics']}")

        except Exception as e:
            self.logger.exception(f"Error during shutdown: {e!s}")


# Global integration manager instance
cks_integration_manager = CKSIntegrationManager()
