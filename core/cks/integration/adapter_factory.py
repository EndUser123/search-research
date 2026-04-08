import logging
from typing import Any

#!/usr/bin/env python3
"""CKS Integration Factory

Factory pattern for creating and managing CKS integration adapters.
Provides centralized creation and configuration of all CKS integrations.

Constitutional Requirements:
- Solo developer optimization (simple factory pattern)
- Evidence-based implementation (clear factory methods)
- Force multiplier integration (extensible factory)
- No enterprise bloat (direct Python usage)
"""

# Import base adapter components
from .interfaces.base_adapter import (
    BaseCKSAdapter,
    CKSContext,
    IntegrationResult,
    IntegrationType,
    adapter_registry,
)

logger = logging.getLogger(__name__)


class CKSAdapterFactory:
    """Factory for creating CKS integration adapters.

    Provides centralized creation and configuration of CKS integration
    adapters with consistent patterns and error handling.
    """

    def __init__(self) -> None:
        """Initialize the adapter factory."""
        self.logger = logging.getLogger(f"{__name__}.CKSAdapterFactory")
        self._adapter_classes: dict[IntegrationType, type[BaseCKSAdapter]] = {}
        self._default_configs: dict[IntegrationType, dict[str, Any]] = {}

        # Register default adapter classes (will be populated as we move them)
        self._register_default_adapters()

    def _register_default_adapters(self) -> None:
        """Register default adapter implementations."""
        # This will be populated as we refactor each integration
        # For now, set up the structure for future adapter registration

    def register_adapter_class(
        self, integration_type: IntegrationType, adapter_class: type[BaseCKSAdapter]
    ) -> None:
        """Register an adapter class for an integration type.

        Args:
            integration_type: Type of integration
            adapter_class: Adapter class to register

        """
        self._adapter_classes[integration_type] = adapter_class
        self.logger.info(f"Registered adapter class for {integration_type.value}")

    def set_default_config(self, integration_type: IntegrationType, config: dict[str, Any]) -> None:
        """Set default configuration for an integration type.

        Args:
            integration_type: Type of integration
            config: Default configuration

        """
        self._default_configs[integration_type] = config
        self.logger.info(f"Set default config for {integration_type.value}")

    def create_adapter(
        self, integration_type: IntegrationType, config: dict[str, Any] | None = None
    ) -> IntegrationResult:
        """Create an adapter instance.

        Args:
            integration_type: Type of integration to create
            config: Configuration for the adapter (optional)

        Returns:
            IntegrationResult with adapter instance or error

        """
        try:
            # Get default config and merge with provided config
            default_config = self._default_configs.get(integration_type, {})
            final_config = {**default_config, **(config or {})}

            # Check if adapter class is registered
            if integration_type not in self._adapter_classes:
                return IntegrationResult(
                    success=False,
                    error=f"No adapter class registered for {integration_type.value}",
                )

            # Create adapter instance
            adapter_class = self._adapter_classes[integration_type]
            adapter = adapter_class(integration_type)

            # Initialize adapter
            init_result = adapter.initialize(final_config)
            if not init_result.success:
                return IntegrationResult(
                    success=False,
                    error=f"Failed to initialize adapter: {init_result.error}",
                )

            # Register with global registry
            adapter_registry.register_adapter(adapter)

            self.logger.info(f"Created adapter for {integration_type.value}")
            return IntegrationResult(
                success=True,
                data=adapter,
                metadata={"integration_type": integration_type.value},
            )

        except Exception as e:
            self.logger.exception(f"Error creating adapter for {integration_type.value}: {e!s}")
            return IntegrationResult(
                success=False,
                error=f"Failed to create adapter: {e!s}",
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

    def get_available_integrations(self) -> list[IntegrationType]:
        """Get list of available integration types.

        Returns:
            List of available integration types

        """
        return list(self._adapter_classes.keys())

    def initialize_all_adapters(
        self,
        configs: dict[IntegrationType, dict[str, Any]] | None = None,
    ) -> dict[IntegrationType, IntegrationResult]:
        """Initialize all registered adapters.

        Args:
            configs: Configuration for each adapter type (optional)

        Returns:
            Dictionary of initialization results by integration type

        """
        results = {}
        configs = configs or {}

        for integration_type in self._adapter_classes:
            config = configs.get(integration_type, {})
            result = self.create_adapter(integration_type, config)
            results[integration_type] = result

        return results

    def get_adapter_metrics(self) -> dict[str, Any]:
        """Get metrics for all registered adapters.

        Returns:
            Dictionary of adapter metrics

        """
        metrics = {
            "factory_metrics": {
                "registered_adapters": len(self._adapter_classes),
                "available_integrations": [t.value for t in self.get_available_integrations()],
            },
            "adapter_metrics": {},
        }

        # Get metrics from each adapter in the global registry
        for integration_type in adapter_registry.list_adapters():
            adapter = adapter_registry.get_adapter(integration_type)
            if adapter:
                try:
                    adapter_metrics = adapter.get_metrics()
                    metrics["adapter_metrics"][integration_type.value] = adapter_metrics
                except Exception as e:
                    self.logger.warning(f"Failed to get metrics for {integration_type.value}: {e}")

        return metrics


# Global factory instance
cks_adapter_factory = CKSAdapterFactory()
