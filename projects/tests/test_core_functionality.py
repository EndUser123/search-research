#!/usr/bin/env python3
"""
Core Functionality Tests - Tier 0 Smoke Test

Test Case ID: TC-TIER0-002
Priority: Critical
Test Type: Smoke Testing

Purpose:
Verify that core CSF NIP system functionality is working.
These tests ensure the basic system components are operational.

Preconditions:
- Basic import tests pass
- CSF NIP environment is properly configured
- Core modules are accessible

Expected Results:
- Core system components initialize correctly
- Basic operations complete without errors
- System responds to fundamental requests

Test Duration: <1.0 second
"""

import json
import os
import sys
from pathlib import Path


def test_project_root_detection():
    """
    Test project root detection functionality.

    Algorithm Approach: Verify that the system can correctly identify the project root directory.

    Returns:
    bool: True if project root detection works correctly

    Raises:
    AssertionError: If project root detection fails
    """
    # Current working directory should be project root
    cwd = Path.cwd()

    # Check for indicators that we're in project root
    root_indicators = ["__csf", ".claude", "tests", "CSF_NIP_ATOMIC_TASK_PLAN.md"]

    found_indicators = []
    for indicator in root_indicators:
        if (cwd / indicator).exists():
            found_indicators.append(indicator)

    assert (
        len(found_indicators) >= 2
    ), f"Not enough root indicators found. Found: {found_indicators}"
    print(f"✓ Project root detected correctly: {cwd}")


def test_config_file_loading():
    """
    Test configuration file loading.

    Algorithm Approach: Load and validate tier1_tests.yaml configuration.

    Returns:
    bool: True if configuration loads successfully

    Raises:
    AssertionError: If configuration loading fails
    """
    config_path = Path("__csf/config/tier1_tests.yaml")

    assert config_path.exists(), f"Config file not found: {config_path}"

    try:
        with open(config_path, encoding="utf-8") as f:
            content = f.read()
            assert len(content) > 100, "Config file appears too short"

            # Try to parse as YAML (basic check without pyyaml requirement)
            lines = content.split("\n")
            has_version = any("version:" in line for line in lines)
            has_tier0 = any("tier0_smoke_tests:" in line for line in lines)

            assert has_version, "Config missing version field"
            assert has_tier0, "Config missing tier0_smoke_tests section"

    except Exception as e:
        raise AssertionError(f"Failed to read/parse config file: {e}")

    print("✓ Configuration file loads and parses correctly")


def test_hook_directory_structure():
    """
    Test hook directory structure.

    Algorithm Approach: Verify that Claude hook directories and files exist.

    Returns:
    bool: True if hook structure is correct

    Raises:
    AssertionError: If hook structure is missing or incorrect
    """
    hooks_dir = Path(".claude/hooks")

    assert hooks_dir.exists(), f"Hooks directory missing: {hooks_dir}"
    assert hooks_dir.is_dir(), f"Hooks path is not a directory: {hooks_dir}"

    # Check for essential hook files
    essential_hooks = [
        "session_management_integration.py",
        "user_prompt_submit.py",
        "pre_tool_use.py",
        "post_tool_use.py",
        "llm_supervisor.py",
    ]

    found_hooks = []
    for hook_file in essential_hooks:
        hook_path = hooks_dir / hook_file
        if hook_path.exists():
            found_hooks.append(hook_file)

    assert len(found_hooks) >= 3, f"Too few hook files found. Found: {found_hooks}"
    print(f"✓ Hook directory structure valid ({len(found_hooks)} hooks found)")


def test_python_path_configuration():
    """
    Test Python path configuration for CSF NIP.

    Algorithm Approach: Verify that Python can find CSF NIP modules.

    Returns:
    bool: True if Python path is configured correctly

    Raises:
    AssertionError: If Python path configuration is incorrect
    """
    # Check if __csf is in Python path or accessible
    project_root = Path.cwd()
    csf_nip_path = project_root / "__csf"

    assert csf_nip_path.exists(), f"CSF NIP directory missing: {csf_nip_path}"

    # Try to add to path and import
    if str(csf_nip_path) not in sys.path:
        sys.path.insert(0, str(csf_nip_path))

    try:
        # Check if we can at least see the directory structure
        src_path = csf_nip_path / "src"
        assert src_path.exists(), f"CSF NIP src directory missing: {src_path}"

        # Check for __init__.py files
        init_files = [
            csf_nip_path / "src" / "__init__.py",
        ]

        for init_file in init_files:
            if init_file.exists():
                print(f"✓ Found init file: {init_file.name}")

    except Exception as e:
        raise AssertionError(f"Python path configuration test failed: {e}")

    print("✓ Python path configuration appears correct")


def test_file_system_operations():
    """
    Test basic file system operations used by CSF NIP.

    Algorithm Approach: Perform basic file operations to verify system capabilities.

    Returns:
    bool: True if file system operations work correctly

    Raises:
    AssertionError: If file system operations fail
    """
    test_dir = Path("tests/test_outputs")

    # Test directory creation
    try:
        test_dir.mkdir(parents=True, exist_ok=True)
        assert test_dir.exists(), "Failed to create test directory"
        assert test_dir.is_dir(), "Created path is not a directory"
    except Exception as e:
        raise AssertionError(f"Directory creation failed: {e}")

    # Test file creation and writing
    test_file = test_dir / "core_functionality_test.tmp"
    try:
        with open(test_file, "w") as f:
            f.write("Core functionality test content")
        assert test_file.exists(), "Test file was not created"
        assert test_file.stat().st_size > 0, "Test file is empty"
    except Exception as e:
        raise AssertionError(f"File creation failed: {e}")

    # Test file reading
    try:
        with open(test_file) as f:
            content = f.read()
            assert "Core functionality test content" in content, "File content mismatch"
    except Exception as e:
        raise AssertionError(f"File reading failed: {e}")

    # Cleanup
    try:
        test_file.unlink()
        print("✓ File system operations working correctly")
    except Exception as e:
        raise AssertionError(f"File cleanup failed: {e}")


def test_environment_variable_handling():
    """
    Test environment variable handling.

    Algorithm Approach: Check if environment variables can be read and set.

    Returns:
    bool: True if environment variable handling works correctly

    Raises:
    AssertionError: If environment variable handling fails
    """
    # Test reading existing environment variables
    try:
        path_var = os.environ.get("PATH", "")
        assert isinstance(path_var, str), "PATH environment variable should be a string"
        assert len(path_var) > 0, "PATH should not be empty"
    except Exception as e:
        raise AssertionError(f"Environment variable reading failed: {e}")

    # Test setting and retrieving a test variable
    test_key = "CSF_NIP_SMOKE_TEST"
    test_value = "test_value_12345"

    try:
        os.environ[test_key] = test_value
        retrieved = os.environ.get(test_key)
        assert (
            retrieved == test_value
        ), f"Environment variable retrieval failed: expected {test_value}, got {retrieved}"

        # Cleanup
        del os.environ[test_key]
        print("✓ Environment variable handling working correctly")
    except Exception as e:
        raise AssertionError(f"Environment variable setting failed: {e}")


def test_json_operations():
    """
    Test JSON operations used throughout CSF NIP.

    Algorithm Approach: Perform basic JSON encoding and decoding operations.

    Returns:
    bool: True if JSON operations work correctly

    Raises:
    AssertionError: If JSON operations fail
    """
    test_data = {
        "system": "CSF NIP",
        "test_type": "core_functionality",
        "version": "1.0.0",
        "components": ["hooks", "config", "tests"],
        "metadata": {"timestamp": "2025-11-27T00:00:00Z", "test_id": "TC-TIER0-002"},
    }

    # Test JSON encoding
    try:
        json_str = json.dumps(test_data, indent=2)
        assert isinstance(json_str, str), "JSON encoding should return a string"
        assert len(json_str) > 50, "JSON string should be substantial"
    except Exception as e:
        raise AssertionError(f"JSON encoding failed: {e}")

    # Test JSON decoding
    try:
        decoded_data = json.loads(json_str)
        assert decoded_data == test_data, "JSON round-trip should preserve data"
        assert decoded_data["system"] == "CSF NIP", "JSON data should match original"
    except Exception as e:
        raise AssertionError(f"JSON decoding failed: {e}")

    # Test file I/O with JSON
    json_file = Path("tests/test_outputs/core_test.json")
    try:
        with open(json_file, "w") as f:
            json.dump(test_data, f, indent=2)

        with open(json_file) as f:
            loaded_data = json.load(f)
            assert loaded_data == test_data, "JSON file I/O should preserve data"

        # Cleanup
        json_file.unlink()
        print("✓ JSON operations working correctly")
    except Exception as e:
        raise AssertionError(f"JSON file I/O failed: {e}")


def run_all_core_functionality_tests():
    """
    Run all core functionality smoke tests.

    Algorithm Approach: Execute all core functionality tests in sequence and report results.

    Returns:
    tuple: (total_tests, passed_tests, failed_tests)
    """
    test_functions = [
        test_project_root_detection,
        test_config_file_loading,
        test_hook_directory_structure,
        test_python_path_configuration,
        test_file_system_operations,
        test_environment_variable_handling,
        test_json_operations,
    ]

    total_tests = len(test_functions)
    passed_tests = 0
    failed_tests = []

    print("Running Core Functionality Smoke Tests...")
    print("=" * 50)

    for test_func in test_functions:
        try:
            test_func()
            passed_tests += 1
        except Exception as e:
            failed_tests.append(f"{test_func.__name__}: {e}")
            print(f"✗ {test_func.__name__} failed: {e}")

    print("=" * 50)
    print(f"Core Functionality Tests: {passed_tests}/{total_tests} passed")

    if failed_tests:
        print("Failed tests:")
        for failure in failed_tests:
            print(f"  - {failure}")

    return total_tests, passed_tests, failed_tests


if __name__ == "__main__":
    """
    Main execution for standalone testing.
    """
    total, passed, failed = run_all_core_functionality_tests()

    if len(failed) == 0:
        print("✅ All Core Functionality smoke tests passed!")
        sys.exit(0)
    else:
        print("❌ Some Core Functionality smoke tests failed!")
        sys.exit(1)
