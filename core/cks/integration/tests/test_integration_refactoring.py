import sys
from pathlib import Path

"""Test script to verify CKS integration refactoring works correctly.

This script tests that the new centralized CKS integration system
maintains the same functionality as the scattered system.
"""


project_root = Path(__file__).resolve().parent.parent.parent.parent.parent


def test_centralized_import() -> bool | None:
    """Test that centralized imports work correctly."""
    try:
        from ...integration import (
            CKSContext,
            IntegrationResult,
            IntegrationType,
            adapter_registry,
            cks_adapter_factory,
            cks_integration_manager,
        )

        print("✅ All centralized imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False


def test_integration_types() -> bool | None:
    """Test that all integration types are available."""
    try:
        from ...integration import IntegrationType

        # Test all expected integration types
        expected_types = [
            IntegrationType.CONSTITUTIONAL_COMPLIANCE,
            IntegrationType.ORCHESTRATION,
            IntegrationType.MONITORING,
            IntegrationType.PERFORMANCE,
            IntegrationType.TASK_MANAGEMENT,
            IntegrationType.KNOWLEDGE_SYSTEM,
            IntegrationType.RESILIENCE,
            IntegrationType.UNIVERSAL_INSTRUMENTATION,
        ]

        for integration_type in expected_types:
            assert hasattr(integration_type, "value"), f"Missing value for {integration_type}"
            print(f"✅ IntegrationType.{integration_type.name} available")

        print("✅ All integration types available")
        return True
    except Exception as e:
        print(f"❌ Integration types test failed: {e}")
        return False


def test_factory_registry() -> bool | None:
    """Test factory and registry functionality."""
    try:
        from ...integration import adapter_registry, cks_adapter_factory

        # Test factory exists
        assert cks_adapter_factory is not None, "Factory not found"
        assert adapter_registry is not None, "Registry not found"

        # Test factory methods
        available_integrations = cks_adapter_factory.get_available_integrations()
        assert isinstance(available_integrations, list), "Should return list"

        print(
            f"✅ Factory and registry working. Available integrations: {len(available_integrations)}"
        )
        return True
    except Exception as e:
        print(f"❌ Factory/registry test failed: {e}")
        return False


def test_integration_manager() -> bool | None:
    """Test integration manager functionality."""
    try:
        from ...integration import IntegrationType, cks_integration_manager

        # Test manager exists
        assert cks_integration_manager is not None, "Integration manager not found"

        # Test manager methods
        available_integrations = cks_integration_manager.list_available_integrations()
        assert isinstance(available_integrations, list), "Should return list"

        # Test metrics
        metrics = cks_integration_manager.get_system_metrics()
        assert isinstance(metrics, dict), "Metrics should be dict"
        assert "operation_metrics" in metrics, "Should have operation metrics"

        # Test context creation
        context = cks_integration_manager.create_context(
            IntegrationType.MONITORING,
            "test_operation_123",
        )
        assert context is not None, "Context should be created"
        assert context.integration_type == IntegrationType.MONITORING, "Context type mismatch"

        print("✅ Integration manager working correctly")
        return True
    except Exception as e:
        print(f"❌ Integration manager test failed: {e}")
        return False


def test_context_validation() -> bool | None:
    """Test CKS context validation."""
    try:
        from ...integration import CKSContext, IntegrationType

        # Test valid context
        valid_context = CKSContext(
            integration_type=IntegrationType.KNOWLEDGE_SYSTEM,
            operation_id="test_123",
        )

        # Basic validation
        assert valid_context.integration_type == IntegrationType.KNOWLEDGE_SYSTEM
        assert valid_context.operation_id == "test_123"

        print("✅ Context validation working")
        return True
    except Exception as e:
        print(f"❌ Context validation test failed: {e}")
        return False


def test_result_structures() -> bool | None:
    """Test result structures."""
    try:
        from ...integration import IntegrationResult

        # Test IntegrationResult
        success_result = IntegrationResult(success=True, data={"test": "data"})
        assert success_result.success is True
        assert success_result.data == {"test": "data"}

        error_result = IntegrationResult(success=False, error="test error")
        assert error_result.success is False
        assert error_result.error == "test error"

        print("✅ Result structures working")
        return True
    except Exception as e:
        print(f"❌ Result structures test failed: {e}")
        return False


def test_example_usage() -> bool | None:
    """Test the example usage patterns."""
    try:
        # Test metrics without initialization
        metrics = cks_integration_manager.get_system_metrics()
        assert "operation_metrics" in metrics

        # Test available integrations
        integrations = cks_integration_manager.list_available_integrations()
        assert isinstance(integrations, list)

        print(f"✅ Example usage working. Available integrations: {len(integrations)}")
        return True
    except Exception as e:
        print(f"❌ Example usage test failed: {e}")
        return False


def run_all_tests():
    """Run all tests and return results."""
    print("🧪 Testing CKS Integration Refactoring")
    print("=" * 50)

    tests = [
        ("Centralized Imports", test_centralized_import),
        ("Integration Types", test_integration_types),
        ("Factory Registry", test_factory_registry),
        ("Integration Manager", test_integration_manager),
        ("Context Validation", test_context_validation),
        ("Result Structures", test_result_structures),
        ("Example Usage", test_example_usage),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n🔍 {test_name}:")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test crashed: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {test_name}")

    print(f"\n🎯 Overall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! CKS integration refactoring is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")

    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
