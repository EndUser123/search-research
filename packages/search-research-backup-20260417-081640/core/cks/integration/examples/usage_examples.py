from pathlib import Path

from ...integration import IntegrationType, cks_integration_manager

"""Examples of how to use the new centralized CKS integration system.

This file demonstrates the migration patterns from scattered imports
to the new centralized integration interface.
"""

# === OLD WAY (Before Refactoring) ===
# from modules.orchestration.cks_agent_coordinator import CKSAgentCoordinator
# from modules.monitoring.cks_monitoring_analytics import CKSMonitoringAnalytics
# from modules.constitutional_compliance.cks_compliance_monitor import CKSComplianceMonitor

# === NEW WAY (After Refactoring) ===

project_root = Path(__file__).resolve().parent.parent.parent.parent


def example_constitutional_compliance() -> None:
    """Example: Constitutional compliance validation."""
    # Initialize integration manager (do this once at startup)
    init_result = cks_integration_manager.initialize_all_integrations()

    if init_result.success:
        print("✅ CKS integrations initialized")
    else:
        print(f"❌ Failed to initialize: {init_result.error}")
        return

    # Process with constitutional compliance integration
    result = cks_integration_manager.process_with_integration(
        IntegrationType.CONSTITUTIONAL_COMPLIANCE,
        operation_data={
            "action": "validate_compliance",
            "target": "current_operation",
            "context": {"user": "solo_developer"},
        },
    )

    if result.success:
        print("✅ Compliance validation passed")
        print(f"Data: {result.data}")
    else:
        print(f"❌ Compliance validation failed: {result.error}")


def example_monitoring() -> None:
    """Example: System monitoring integration."""
    # Process with monitoring integration
    result = cks_integration_manager.process_with_integration(
        IntegrationType.MONITORING,
        operation_data={
            "action": "collect_metrics",
            "metrics_type": "performance",
            "time_range": "last_hour",
        },
    )

    if result.success:
        print("✅ Monitoring data collected")
        print(f"Metrics: {result.data}")
    else:
        print(f"❌ Monitoring failed: {result.error}")


def example_orchestration() -> None:
    """Example: Orchestration integration."""
    # Process with orchestration integration
    result = cks_integration_manager.process_with_integration(
        IntegrationType.ORCHESTRATION,
        operation_data={
            "action": "coordinate_agents",
            "agents": ["test_agent", "build_agent"],
            "workflow": "continuous_integration",
        },
    )

    if result.success:
        print("✅ Agent coordination successful")
        print(f"Result: {result.data}")
    else:
        print(f"❌ Orchestration failed: {result.error}")


def example_system_metrics() -> None:
    """Example: Get system-wide metrics."""
    metrics = cks_integration_manager.get_system_metrics()

    print("📊 CKS System Metrics:")
    print(f"Total Operations: {metrics['operation_metrics']['total_operations']}")
    print(f"Success Rate: {metrics['operation_metrics']['success_rate_percent']}%")
    print(f"Active Operations: {metrics['operation_metrics']['active_operations']}")
    print(f"Available Integrations: {cks_integration_manager.list_available_integrations()}")


def example_factory_usage() -> None:
    """Example: Using the factory directly."""
    from ...integration import cks_adapter_factory

    # Create a specific adapter
    result = cks_adapter_factory.create_adapter(
        IntegrationType.KNOWLEDGE_SYSTEM,
        config={"validation_level": "strict"},
    )

    if result.success:
        adapter = result.data
        print(f"✅ Created adapter: {type(adapter).__name__}")

        # Use the adapter directly
        from ...integration import CKSContext

        context = CKSContext(
            integration_type=IntegrationType.KNOWLEDGE_SYSTEM,
            operation_id="manual_operation_123",
        )

        process_result = adapter.process_context(context)
        print(f"Processing result: {process_result.success}")
    else:
        print(f"❌ Failed to create adapter: {result.error}")


# Migration template for existing code
def MIGRATION_TEMPLATE() -> None:
    """Template showing how to migrate existing code.

    Replace scattered imports like:

    OLD:
        from modules.some_module.cks_integration import SomeCKSIntegration
        integration = SomeCKSIntegration()
        result = integration.process(data)

    NEW:
        from ...integration import (
            cks_integration_manager,
            IntegrationType
        )

        # Initialize once at startup
        cks_integration_manager.initialize_all_integrations()

        # Use centralized manager
        result = cks_integration_manager.process_with_integration(
            IntegrationType.SOME_MODULE,
            operation_data=data
        )
    """


if __name__ == "__main__":
    print("🚀 CKS Integration Examples")
    print("=" * 50)

    print("\n1. Constitutional Compliance Example:")
    example_constitutional_compliance()

    print("\n2. Monitoring Example:")
    example_monitoring()

    print("\n3. Orchestration Example:")
    example_orchestration()

    print("\n4. System Metrics Example:")
    example_system_metrics()

    print("\n5. Factory Usage Example:")
    example_factory_usage()
