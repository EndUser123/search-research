#!/usr/bin/env python3
"""
Basic Import Tests - Tier 0 Smoke Test

Test Case ID: TC-TIER0-001
Priority: Critical
Test Type: Smoke Testing

Purpose:
Verify that core CSF NIP modules can be imported without errors.
These are the most fundamental smoke tests that must pass for the system to function.

Preconditions:
- CSF NIP Python environment is set up
- Core modules are present in expected locations
- No external dependencies should be required for basic imports

Expected Results:
- All core system modules import successfully
- No ImportError or ModuleNotFoundError exceptions
- Basic module attributes are accessible

Test Duration: <0.5 seconds
"""

import sys
from pathlib import Path


def test_python_version():
    """
    Test Python version compatibility.

    Algorithm Approach: Check if Python version meets minimum requirements.

    Returns:
    bool: True if Python version is compatible

    Raises:
    AssertionError: If Python version is incompatible
    """
    assert sys.version_info >= (3, 11), f"Python 3.11+ required, got {sys.version_info}"
    print(
        f"✓ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} compatible"
    )


def test_core_path_access():
    """
    Test access to core CSF NIP paths.

    Algorithm Approach: Verify that essential directories exist and are accessible.

    Returns:
    bool: True if all core paths are accessible

    Raises:
    AssertionError: If any core path is missing or inaccessible
    """
    project_root = Path.cwd()

    # Check essential directories
    essential_dirs = [
        "__csf",
        "__csf/src",
        "__csf/config",
        ".claude",
        ".claude/hooks",
    ]

    for dir_path in essential_dirs:
        full_path = project_root / dir_path
        assert full_path.exists(), f"Essential directory missing: {full_path}"
        assert full_path.is_dir(), f"Path is not a directory: {full_path}"

    print(f"✓ All essential directories accessible in {project_root}")


def test_basic_config_file_access():
    """
    Test access to basic configuration files.

    Algorithm Approach: Verify that essential configuration files exist and are readable.

    Returns:
    bool: True if all config files are accessible

    Raises:
    AssertionError: If any config file is missing or unreadable
    """
    project_root = Path.cwd()

    # Check essential configuration files
    essential_files = ["__csf/config/tier1_tests.yaml", "__csf/src/__init__.py"]

    for file_path in essential_files:
        full_path = project_root / file_path
        assert full_path.exists(), f"Essential file missing: {full_path}"
        assert full_path.is_file(), f"Path is not a file: {full_path}"

        # Test file readability
        try:
            with open(full_path, encoding="utf-8") as f:
                content = f.read(10)  # Read first 10 chars
                assert len(content) > 0, f"File appears empty: {full_path}"
        except Exception as e:
            raise AssertionError(f"Cannot read file {full_path}: {e}")

    print("✓ All essential configuration files accessible")


def test_standard_library_imports():
    """
    Test standard library imports used throughout CSF NIP.

    Algorithm Approach: Import essential standard library modules to verify Python installation.

    Returns:
    bool: True if all standard library modules import successfully

    Raises:
    ImportError: If any standard library module fails to import
    """
    essential_stdlib_modules = [
        "os",
        "sys",
        "pathlib",
        "json",
        "yaml",
        "logging",
        "datetime",
        "typing",
        "subprocess",
        "threading",
    ]

    failed_imports = []

    for module_name in essential_stdlib_modules:
        try:
            if module_name == "yaml":
                # PyYAML might not be available in minimal environments
                try:
                    import yaml  # type: ignore
                except ImportError:
                    print("⚠ Warning: PyYAML not available, but non-critical")
                    continue
            else:
                __import__(module_name)
        except ImportError as e:
            failed_imports.append(f"{module_name}: {e}")

    assert not failed_imports, f"Standard library import failures: {failed_imports}"
    print("✓ All essential standard library modules importable")


def test_path_operations():
    """
    Test basic path operations that CSF NIP relies on.

    Algorithm Approach: Verify that fundamental path operations work correctly.

    Returns:
    bool: True if all path operations work as expected

    Raises:
    AssertionError: If any path operation fails
    """
    project_root = Path.cwd()

    # Test Path operations
    test_path = project_root / "__csf" / "src"
    assert test_path.exists(), "Test path should exist"
    assert test_path.is_dir(), "Test path should be a directory"

    # Test path resolution
    resolved = test_path.resolve()
    assert resolved.exists(), "Resolved path should exist"

    # Test parent operations
    parent = test_path.parent
    assert parent.name == "__csf", "Parent directory name should match"

    print("✓ Basic path operations working correctly")


def test_json_yaml_capabilities():
    """
    Test JSON and YAML parsing capabilities.

    Algorithm Approach: Create and parse simple JSON/YAML structures to verify functionality.

    Returns:
    bool: True if JSON/YAML parsing works correctly

    Raises:
    AssertionError: If JSON/YAML parsing fails
    """
    import json

    # Test JSON capabilities
    test_data = {"test": "value", "number": 42, "list": [1, 2, 3]}
    json_str = json.dumps(test_data)
    parsed_data = json.loads(json_str)
    assert parsed_data == test_data, "JSON round-trip should preserve data"

    # Test YAML capabilities if available
    try:
        import yaml  # type: ignore

        yaml_str = yaml.dump(test_data)
        parsed_yaml = yaml.safe_load(yaml_str)
        assert parsed_yaml == test_data, "YAML round-trip should preserve data"
        print("✓ JSON and YAML parsing capabilities working")
    except ImportError:
        print("✓ JSON parsing working (YAML not available)")


def test_file_system_permissions():
    """
    Test basic file system permissions.

    Algorithm Approach: Verify that we can read, write, and list files in appropriate locations.

    Returns:
    bool: True if file system permissions are adequate

    Raises:
    AssertionError: If file system permissions are insufficient
    """
    project_root = Path.cwd()

    # Test read permission on project root
    assert project_root.exists(), "Project root should exist"
    assert project_root.is_dir(), "Project root should be a directory"

    # Try to list contents
    try:
        list(project_root.iterdir())
    except PermissionError as e:
        raise AssertionError(f"Cannot list project root directory: {e}")

    # Test write permission in temp area (if it exists)
    temp_test_file = project_root / "tests" / "test_outputs" / "permission_test.tmp"
    try:
        temp_test_file.parent.mkdir(parents=True, exist_ok=True)
        with open(temp_test_file, "w") as f:
            f.write("test")
        temp_test_file.unlink()  # Clean up
        print("✓ File system permissions adequate")
    except Exception as e:
        raise AssertionError(f"File system permission test failed: {e}")


def run_all_basic_import_tests():
    """
    Run all basic import smoke tests.

    Algorithm Approach: Execute all import-related tests in sequence and report results.

    Returns:
    tuple: (total_tests, passed_tests, failed_tests)
    """
    test_functions = [
        test_python_version,
        test_core_path_access,
        test_basic_config_file_access,
        test_standard_library_imports,
        test_path_operations,
        test_json_yaml_capabilities,
        test_file_system_permissions,
    ]

    total_tests = len(test_functions)
    passed_tests = 0
    failed_tests = []

    print("Running Basic Import Smoke Tests...")
    print("=" * 50)

    for test_func in test_functions:
        try:
            test_func()
            passed_tests += 1
        except Exception as e:
            failed_tests.append(f"{test_func.__name__}: {e}")
            print(f"✗ {test_func.__name__} failed: {e}")

    print("=" * 50)
    print(f"Basic Import Tests: {passed_tests}/{total_tests} passed")

    if failed_tests:
        print("Failed tests:")
        for failure in failed_tests:
            print(f"  - {failure}")

    return total_tests, passed_tests, failed_tests


if __name__ == "__main__":
    """
    Main execution for standalone testing.
    """
    total, passed, failed = run_all_basic_import_tests()

    if len(failed) == 0:
        print("✅ All Basic Import smoke tests passed!")
        sys.exit(0)
    else:
        print("❌ Some Basic Import smoke tests failed!")
        sys.exit(1)
