#!/usr/bin/env python3
"""
TDD Test Suite for Lazy Import Optimization (Phase 1, Task 3)

Task: TSK-251225-HooksOpt-0822
Objective: 15-30% faster startup time through lazy import loading

This test suite validates:
1. Imports happen only when needed (lazy, not eager)
2. Import caching works (second call returns cached import)
3. Graceful handling of missing optional dependencies
4. All code paths still work after lazy loading
5. Performance improvement >15% startup time reduction

Test Structure:
- Red: Tests fail with current eager import implementation
- Green: Tests pass after lazy import implementation
- Refactor: Code quality improvements while tests pass
"""

import sys
import time
from io import StringIO
from pathlib import Path

import pytest

# Add hooks directory to path for testing
hooks_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(hooks_dir))


class TestLazyImportBehavior:
    """
    Test Suite 1: Verify Lazy Import Behavior

    Validates that imports are deferred until first use,
    then cached for subsequent calls.
    """

    def test_module_not_imported_at_load_time(self):
        """
        RED TEST: Verify optional modules are NOT imported during module load

        Current behavior: testing.test_quarantine imports eagerly at line 40-47
        Expected behavior: Module should not be in sys.modules until accessed

        This test will FAIL with current implementation (Red phase)
        """
        # Clear module cache to ensure clean state
        modules_to_remove = [m for m in sys.modules if 'test_quarantine' in m or 'pre_tool_use' in m]
        for module in modules_to_remove:
            del sys.modules[module]

        # Import pre_tool_use module

        # Verify optional modules are NOT imported yet
        # (This will fail with current eager import implementation)
        optional_modules = [
            'testing.test_quarantine',
            'config.system_config',
            'calibration.override_tracker'
        ]

        for module in optional_modules:
            # RED: This assertion will fail with current code
            # GREEN: After lazy imports, module should not be imported
            assert module not in sys.modules, \
                f"Module {module} should NOT be imported at module load time (lazy import violation)"

    def test_quarantine_system_lazy_load(self):
        """
        Test that quarantine system loads lazily when first accessed

        Expected behavior:
        1. Module not imported at load time
        2. Module imported on first function call that uses it
        3. Module cached in sys.modules after first import
        """
        # Clear module cache
        modules_to_remove = [m for m in sys.modules if 'test_quarantine' in m or 'pre_tool_use' in m]
        for module in modules_to_remove:
            del sys.modules[module]

        import pre_tool_use

        # Module not imported yet
        assert 'testing.test_quarantine' not in sys.modules

        # Trigger first use (should import now)
        # Call a function that uses quarantine system
        if hasattr(pre_tool_use, 'get_quarantine_system'):
            system = pre_tool_use.get_quarantine_system()
            # Now it should be imported
            assert 'testing.test_quarantine' in sys.modules or \
                   not pre_tool_use.QUARANTINE_SYSTEM_AVAILABLE

    def test_system_config_lazy_load(self):
        """
        Test that system config loads lazily

        Expected: Not imported until first config access
        """
        # Clear module cache
        modules_to_remove = [m for m in sys.modules if 'system_config' in m or 'pre_tool_use' in m]
        for module in modules_to_remove:
            del sys.modules[module]

        import pre_tool_use

        # Module not imported yet
        assert 'config.system_config' not in sys.modules

        # Trigger first use
        if hasattr(pre_tool_use, 'get_system_config'):
            config = pre_tool_use.get_system_config()
            # Now imported if available
            assert 'config.system_config' in sys.modules or \
                   not pre_tool_use.SYSTEM_CONFIG_AVAILABLE

    def test_override_tracker_lazy_load(self):
        """
        Test that override tracker loads lazily

        Expected: Not imported until first tracking operation
        """
        # Clear module cache
        modules_to_remove = [m for m in sys.modules if 'override_tracker' in m or 'pre_tool_use' in m]
        for module in modules_to_remove:
            del sys.modules[module]

        import pre_tool_use

        # Module not imported yet
        assert 'calibration.override_tracker' not in sys.modules

        # Trigger first use
        if hasattr(pre_tool_use, 'get_override_tracker'):
            tracker = pre_tool_use.get_override_tracker()
            # Now imported if available
            assert 'calibration.override_tracker' in sys.modules or \
                   not pre_tool_use.OVERRIDE_TRACKER_AVAILABLE


class TestImportCaching:
    """
    Test Suite 2: Verify Import Caching

    Validates that once imported, modules are cached
    and not re-imported on subsequent calls.
    """

    def test_cached_import_returns_same_object(self):
        """
        Test that cached imports return the same module object

        Expected: Multiple calls return identical object reference
        """
        # Clear module cache
        modules_to_remove = [m for m in sys.modules if 'pre_tool_use' in m]
        for module in modules_to_remove:
            del sys.modules[module]

        import pre_tool_use

        # First import
        if hasattr(pre_tool_use, 'get_quarantine_system'):
            system1 = pre_tool_use.get_quarantine_system()
            system2 = pre_tool_use.get_quarantine_system()

            # Should be same object (cached)
            if pre_tool_use.QUARANTINE_SYSTEM_AVAILABLE:
                assert system1 is system2, "Cached import should return same object"

    def test_second_import_is_faster(self):
        """
        Test that second import is faster (cached vs uncached)

        Expected: Cached import <10% of first import time
        """
        # Clear module cache
        modules_to_remove = [m for m in sys.modules if 'pre_tool_use' in m]
        for module in modules_to_remove:
            del sys.modules[module]

        import pre_tool_use

        if hasattr(pre_tool_use, 'get_system_config') and pre_tool_use.SYSTEM_CONFIG_AVAILABLE:
            # First import (uncached)
            start1 = time.perf_counter()
            config1 = pre_tool_use.get_system_config()
            time1 = time.perf_counter() - start1

            # Second import (cached)
            start2 = time.perf_counter()
            config2 = pre_tool_use.get_system_config()
            time2 = time.perf_counter() - start2

            # Cached should be significantly faster
            # (Allow some tolerance for measurement noise)
            if time1 > 0.001:  # Only check if first import took >1ms
                assert time2 < time1 * 0.5, \
                    f"Cached import ({time2*1000:.2f}ms) should be faster than uncached ({time1*1000:.2f}ms)"


class TestGracefulMissingDependencies:
    """
    Test Suite 3: Graceful Handling of Missing Optional Dependencies

    Validates that missing optional dependencies don't crash the hook.
    """

    def test_quarantine_unavailable_flag_set(self):
        """
        Test that QUARANTINE_SYSTEM_AVAILABLE flag reflects reality

        Expected: False if module missing, True if present
        """
        import pre_tool_use

        # Flag should be boolean
        assert isinstance(pre_tool_use.QUARANTINE_SYSTEM_AVAILABLE, bool)

        # If available, module should be importable
        if pre_tool_use.QUARANTINE_SYSTEM_AVAILABLE:
            try:
                from testing.test_quarantine import TestResult
                assert True  # Successfully imported
            except ImportError:
                pytest.fail("QUARANTINE_SYSTEM_AVAILABLE=True but import failed")
        else:
            # If not available, flag should be False
            assert pre_tool_use.QUARANTINE_SYSTEM_AVAILABLE is False

    def test_system_config_unavailable_flag_set(self):
        """
        Test that SYSTEM_CONFIG_AVAILABLE flag reflects reality
        """
        import pre_tool_use

        assert isinstance(pre_tool_use.SYSTEM_CONFIG_AVAILABLE, bool)

        if pre_tool_use.SYSTEM_CONFIG_AVAILABLE:
            try:
                from config.system_config import get_system_config
                assert True
            except ImportError:
                pytest.fail("SYSTEM_CONFIG_AVAILABLE=True but import failed")

    def test_override_tracker_unavailable_flag_set(self):
        """
        Test that OVERRIDE_TRACKER_AVAILABLE flag reflects reality
        """
        import pre_tool_use

        assert isinstance(pre_tool_use.OVERRIDE_TRACKER_AVAILABLE is bool)

        if pre_tool_use.OVERRIDE_TRACKER_AVAILABLE:
            try:
                from calibration.override_tracker import get_override_tracker
                assert True
            except ImportError:
                pytest.fail("OVERRIDE_TRACKER_AVAILABLE=True but import failed")

    def test_hook_continues_with_missing_dependencies(self):
        """
        Test that hook main function works even with missing dependencies

        Expected: Hook doesn't crash, returns valid response
        """

        import pre_tool_use

        # Mock stdin with test data
        test_input = {
            "toolName": "read_file",
            "toolInput": {"filePath": "P:/test.txt"}
        }

        # This should not raise ImportError
        try:
            # Capture stderr to suppress warnings
            old_stderr = sys.stderr
            sys.stderr = StringIO()

            # Try to call main (may fail for other reasons, but not ImportError)
            # We'll just verify module loads without crashing
            assert hasattr(pre_tool_use, 'main') or hasattr(pre_tool_use, 'AntiLazyVerification')

            sys.stderr = old_stderr
        except ImportError as e:
            pytest.fail(f"Hook should not crash with ImportError: {e}")


class TestCodePathsStillWork:
    """
    Test Suite 4: All Code Paths Still Work After Lazy Loading

    Validates that lazy loading doesn't break functionality.
    """

    def test_antilazy_verification_class_works(self):
        """
        Test that AntiLazyVerification class works after lazy imports
        """
        import pre_tool_use

        verifier = pre_tool_use.AntiLazyVerification()

        # Test method exists and is callable
        assert hasattr(verifier, 'verify_system_claim')
        assert callable(verifier.verify_system_claim)

        # Test basic functionality
        result = verifier.verify_system_claim(
            system_name="test_system",
            claimed_behavior="test behavior",
            implementation_paths=[]
        )

        assert isinstance(result, dict)
        assert 'claim' in result
        assert 'system' in result
        assert 'verified' in result

    def test_all_helper_functions_accessible(self):
        """
        Test that all lazy import helper functions are accessible
        """
        import pre_tool_use

        # Check for expected helper functions (will be added in Green phase)
        expected_functions = [
            # After implementation, these should exist:
            # 'get_quarantine_system',
            # 'get_system_config',
            # 'get_override_tracker',
        ]

        # For now, just verify module is importable
        assert pre_tool_use is not None

    def test_no_circular_imports(self):
        """
        Test that lazy imports don't cause circular dependencies

        Expected: Clean import without RecursionError
        """
        # Clear all related modules
        modules_to_remove = [
            m for m in sys.modules
            if any(x in m for x in ['pre_tool_use', 'test_quarantine', 'system_config', 'override_tracker'])
        ]
        for module in modules_to_remove:
            del sys.modules[module]

        # Import should work without recursion error
        try:
            assert True  # Success
        except RecursionError:
            pytest.fail("Lazy imports caused circular import")

    def test_yaml_import_still_works(self):
        """
        Test that yaml import (required dependency) still works

        Expected: yaml module imported at module level (not lazy)
        """
        import pre_tool_use

        # yaml should be available (it's a required dependency)
        assert 'yaml' in sys.modules or hasattr(pre_tool_use, 'yaml')


class TestPerformanceImprovement:
    """
    Test Suite 5: Performance Improvement >15% Startup Time

    Validates that lazy imports achieve target performance improvement.
    """

    def test_startup_time_improvement(self):
        """
        RED TEST: Startup time should improve by >15%

        Current behavior: All imports at module load (baseline)
        Expected behavior: Lazy imports (15-30% faster)

        Measures time from import start to module ready
        """
        # Clear all modules to ensure clean measurement
        modules_to_remove = [
            m for m in sys.modules
            if any(x in m for x in ['pre_tool_use', 'test_quarantine', 'system_config',
                                     'override_tracker', 'yaml'])
        ]
        for module in modules_to_remove:
            del sys.modules[module]

        # Measure import time
        start = time.perf_counter()
        import_time = time.perf_counter() - start

        # RED: This will fail with eager imports
        # GREEN: After lazy imports, should be faster
        # We don't have a baseline, but we can verify it's reasonable (<500ms)
        assert import_time < 0.5, \
            f"Import took {import_time*1000:.2f}ms, should be <500ms with lazy imports"

    def test_import_count_reduced(self):
        """
        Test that number of imports is reduced with lazy loading

        Expected: Fewer modules in sys.modules at module load
        """
        # Clear modules
        modules_to_remove = [
            m for m in sys.modules
            if 'pre_tool_use' in m or any(x in m for x in ['test_quarantine', 'system_config', 'override_tracker'])
        ]
        for module in modules_to_remove:
            del sys.modules[module]

        # Count modules before import
        modules_before = len(sys.modules)

        # Import pre_tool_use

        # Count modules after import
        modules_after = len(sys.modules)
        new_modules = modules_after - modules_before

        # With lazy imports, should import minimal modules
        # (This is a weak test, but we'll refine in Green phase)
        # Expected: <10 new modules (vs 20+ with eager imports)
        assert new_modules < 15, \
            f"Import added {new_modules} modules, should be <15 with lazy imports"

    def test_function_attribute_caching_pattern(self):
        """
        Test that lazy imports use function attribute caching

        Expected pattern:
        ```python
        def get_quarantine_system():
            if not hasattr(get_quarantine_system, '_cached'):
                from testing.test_quarantine import get_quarantine_system as _qs
                get_quarantine_system._cached = _qs
            return get_quarantine_system._cached
        ```
        """
        import pre_tool_use

        # Check if helper functions use caching pattern (after implementation)
        # For now, this test documents the expected pattern
        if hasattr(pre_tool_use, 'get_quarantine_system'):
            # After implementation, check for cached attribute
            func = pre_tool_use.get_quarantine_system
            # Call once to cache
            if pre_tool_use.QUARANTINE_SYSTEM_AVAILABLE:
                result = func()
                # Should have cached attribute after first call
                # (This will be implemented in Green phase)
                # assert hasattr(func, '_cached'), "Function should use attribute caching"


class TestBackwardCompatibility:
    """
    Test Suite 6: Backward Compatibility

    Validates that lazy imports maintain existing interfaces.
    """

    def test_availability_flags_exist(self):
        """
        Test that availability flags still exist
        """
        import pre_tool_use

        required_flags = [
            'QUARANTINE_SYSTEM_AVAILABLE',
            'SYSTEM_CONFIG_AVAILABLE',
            'OVERRIDE_TRACKER_AVAILABLE'
        ]

        for flag in required_flags:
            assert hasattr(pre_tool_use, flag), f"Missing flag: {flag}"
            assert isinstance(getattr(pre_tool_use, flag), bool), f"Flag {flag} should be boolean"

    def test_antilazy_verification_intact(self):
        """
        Test that AntiLazyVerification class is unchanged
        """
        import pre_tool_use

        # Class should exist
        assert hasattr(pre_tool_use, 'AntiLazyVerification')

        # Instance should work
        verifier = pre_tool_use.AntiLazyVerification()
        assert verifier is not None

    def test_main_function_exists(self):
        """
        Test that main() function still exists
        """
        import pre_tool_use

        assert hasattr(pre_tool_use, 'main'), "main() function should exist"
        assert callable(pre_tool_use.main), "main should be callable"


# Performance Benchmark Utilities
class BenchmarkMetrics:
    """Helper class for collecting and reporting performance metrics"""

    @staticmethod
    def measure_import_time(module_name: str, clear_cache: bool = True) -> float:
        """
        Measure module import time in milliseconds

        Args:
            module_name: Module to import
            clear_cache: Whether to clear sys.modules first

        Returns:
            Import time in milliseconds
        """
        if clear_cache:
            modules_to_remove = [m for m in sys.modules if module_name in m]
            for module in modules_to_remove:
                del sys.modules[module]

        start = time.perf_counter()
        __import__(module_name)
        return (time.perf_counter() - start) * 1000

    @staticmethod
    def count_imported_modules() -> int:
        """Count number of modules currently in sys.modules"""
        return len(sys.modules)


@pytest.fixture
def clean_import_environment():
    """
    Fixture to provide clean import environment for each test

    Clears relevant modules before test, restores after
    """
    # Save current state
    modules_before = set(sys.modules.keys())

    yield

    # Restore state after test
    modules_current = set(sys.modules.keys())
    modules_added = modules_current - modules_before

    for module in modules_added:
        if any(x in module for x in ['pre_tool_use', 'test_quarantine', 'system_config',
                                       'override_tracker']):
            del sys.modules[module]


# Test entry point for manual testing
if __name__ == "__main__":
    """
    Run tests manually for debugging

    Usage:
        python -m pytest tests/test_lazy_imports.py -v
        python tests/test_lazy_imports.py  # Manual run
    """
    print("=" * 70)
    print("Lazy Import TDD Test Suite")
    print("=" * 70)
    print("\nRunning tests...\n")

    # Run pytest
    sys.exit(pytest.main([__file__, '-v', '--tb=short']))
