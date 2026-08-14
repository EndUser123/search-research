import re
from datetime import date

from .adapter_factory import cks_adapter_factory
from .integration_manager import OperationMetrics, cks_integration_manager

"""CKS Integration Module

Central module for all CKS integration functionality.
Provides simple interfaces for working with CKS integrations.

Usage:
    from ..integration import (
        cks_integration_manager,
        IntegrationType,
        cks_adapter_factory
    )

    # Initialize all integrations
    result = cks_integration_manager.initialize_all_integrations()

    # Process with specific integration
    result = cks_integration_manager.process_with_integration(
        IntegrationType.CONSTITUTIONAL_COMPLIANCE,
        operation_data={"action": "validate"}
    )
"""

from .interfaces.base_adapter import (
    BaseCKSAdapter,
    CKSContext,
    IntegrationResult,
    IntegrationType,
    adapter_registry,
)

# Version information
__version__ = "1.0.0"

# Export main interfaces for easy import
__all__ = [
    "BaseCKSAdapter",
    "CKSContext",
    "IntegrationResult",
    # Core classes
    "IntegrationType",
    # Registry
    "adapter_registry",
    # Factory and manager
    "cks_adapter_factory",
    "cks_integration_manager",
]
