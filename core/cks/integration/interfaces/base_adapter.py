import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any

"""Base interface for CKS integration adapters.

Provides common patterns and interfaces for all CKS integration adapters
to ensure consistency and maintainability across the system.

Constitutional Requirements:
- Solo developer optimization (simple interfaces)
- Evidence-based implementation (clear patterns)
- Force multiplier integration (extensible architecture)
- No enterprise bloat (direct Python usage)
"""


logger = logging.getLogger(__name__)


class IntegrationType(Enum):
    """Types of CKS integrations."""

    # Original integration types
    CONSTITUTIONAL_COMPLIANCE = "constitutional_compliance"
    ORCHESTRATION = "orchestration"
    MONITORING = "monitoring"
    PERFORMANCE = "performance"
    TASK_MANAGEMENT = "task_management"
    KNOWLEDGE_SYSTEM = "knowledge_system"
    RESILIENCE = "resilience"
    UNIVERSAL_INSTRUMENTATION = "universal_instrumentation"

    # Extended integration types for additional adapters
    AGENT_COORDINATION = "agent_coordination"
    ERROR_RECOVERY = "error_recovery"
    KNOWLEDGE_VALIDATION = "knowledge_validation"
    AUTOMATED_FIXES = "automated_fixes"
    EVIDENCE_INTEGRATION = "evidence_integration"
    RAG_COORDINATION = "rag_coordination"
    SESSION_INTEGRATION = "session_integration"


@dataclass
class IntegrationResult:
    """Standard result structure for CKS integration operations."""

    success: bool
    data: Any | None = None
    error: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass
class CKSContext:
    """Context object for CKS operations."""

    integration_type: IntegrationType
    operation_id: str
    session_id: str | None = None
    metadata: dict[str, Any] | None = None


class BaseCKSAdapter(ABC):
    """Abstract base class for all CKS integration adapters.

    Provides common patterns and ensures consistent behavior across
    all CKS integration implementations.
    """

    def __init__(self, integration_type: IntegrationType) -> None:
        """Initialize adapter with integration type."""
        self.integration_type = integration_type
        self.logger = logging.getLogger(f"{__name__}.{integration_type.value}")

    @abstractmethod
    def initialize(self, config: dict[str, Any]) -> IntegrationResult:
        """Initialize the adapter with configuration.

        Args:
            config: Configuration dictionary for the adapter

        Returns:
            IntegrationResult indicating success/failure

        """

    @abstractmethod
    def process_context(self, context: CKSContext) -> IntegrationResult:
        """Process CKS context and return integration-specific results.

        Args:
            context: CKS context containing operation details

        Returns:
            IntegrationResult with processed data

        """

    def validate_context(self, context: CKSContext) -> bool:
        """Validate CKS context before processing.

        Args:
            context: CKS context to validate

        Returns:
            True if context is valid, False otherwise

        """
        if not context:
            return False

        if not isinstance(context, CKSContext):
            return False

        return context.operation_id

    def log_operation(self, operation: str, context: CKSContext, result: IntegrationResult) -> None:
        """Log operation with consistent formatting.

        Args:
            operation: Description of operation
            context: CKS context used
            result: Result of operation

        """
        log_data = {
            "operation": operation,
            "integration_type": self.integration_type.value,
            "operation_id": context.operation_id,
            "session_id": context.session_id,
            "success": result.success,
            "error": result.error,
        }

        if result.success:
            self.logger.info(f"CKS Integration Success: {operation}", extra=log_data)
        else:
            self.logger.error(f"CKS Integration Error: {operation}", extra=log_data)

    def get_metrics(self) -> dict[str, Any]:
        """Get adapter-specific metrics.

        Returns:
            Dictionary of adapter metrics

        """
        return {
            "integration_type": self.integration_type.value,
            "adapter_class": self.__class__.__name__,
            "initialized": getattr(self, "_initialized", False),
        }


class AdapterRegistry:
    """Registry for managing CKS integration adapters."""

    def __init__(self) -> None:
        self._adapters: dict[IntegrationType, BaseCKSAdapter] = {}
        self.logger = logging.getLogger(__name__)

    def register_adapter(self, adapter: BaseCKSAdapter) -> None:
        """Register an adapter with the registry.

        Args:
            adapter: Adapter instance to register

        """
        self._adapters[adapter.integration_type] = adapter
        self.logger.info(f"Registered CKS adapter: {adapter.integration_type.value}")

    def get_adapter(self, integration_type: IntegrationType) -> BaseCKSAdapter | None:
        """Get adapter by integration type.

        Args:
            integration_type: Type of integration needed

        Returns:
            Adapter instance if found, None otherwise

        """
        return self._adapters.get(integration_type)

    def list_adapters(self) -> list[IntegrationType]:
        """List all registered adapter types.

        Returns:
            List of registered integration types

        """
        return list(self._adapters.keys())

    def initialize_all(
        self, configs: dict[IntegrationType, dict[str, Any]]
    ) -> dict[IntegrationType, IntegrationResult]:
        """Initialize all registered adapters.

        Args:
            configs: Configuration for each adapter type

        Returns:
            Dictionary of initialization results by adapter type

        """
        results = {}

        for integration_type, adapter in self._adapters.items():
            config = configs.get(integration_type, {})
            result = adapter.initialize(config)
            results[integration_type] = result

            if result.success:
                self.logger.info(f"Initialized adapter: {integration_type.value}")
            else:
                self.logger.error(f"Failed to initialize adapter: {integration_type.value}")

        return results


# Global adapter registry instance
adapter_registry = AdapterRegistry()
