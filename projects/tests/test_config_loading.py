#!/usr/bin/env python3
"""
Configuration Loading Tests - Tier 0 Smoke Test

Test Case ID: TC-TIER0-004
Priority: Critical
Test Type: Smoke Testing

Purpose:
Verify that CSF NIP configuration loading works correctly.
These tests ensure the system can load and parse configuration files.

Preconditions:
- Basic import tests pass
- Configuration files exist
- System has read access to config files

Expected Results:
- Configuration files load successfully
- Configuration values are accessible
- Error handling works for missing/invalid configs

Test Duration: <0.2 seconds
"""

import os
import sys
from pathlib import Path


def test_main_config_accessibility():
    """
    Test main configuration file accessibility.

    Algorithm Approach: Verify that tier1_tests.yaml can be accessed and read.

    Returns:
    bool: True if config file is accessible

    Raises:
    AssertionError: If config file is not accessible
    """
    config_path = Path("__csf/config/tier1_tests.yaml")

    assert config_path.exists(), f"Main config file not found: {config_path}"
    assert config_path.is_file(), f"Config path is not a file: {config_path}"

    # Check file permissions
    try:
        with open(config_path, encoding="utf-8") as f:
            content = f.read(100)  # Read first 100 chars
            assert len(content) > 0, "Config file appears empty"
    except PermissionError:
        raise AssertionError(f"No read permission for config file: {config_path}")
    except Exception as e:
        raise AssertionError(f"Cannot read config file: {config_path}, error: {e}")

    print(f"✓ Main config file accessible: {config_path}")


def test_config_file_structure():
    """
    Test configuration file structure.

    Algorithm Approach: Verify that the config file has expected structure and content.

    Returns:
    bool: True if config structure is valid

    Raises:
    AssertionError: If config structure is invalid
    """
    config_path = Path("__csf/config/tier1_tests.yaml")

    try:
        with open(config_path, encoding="utf-8") as f:
            content = f.read()

        # Check for essential sections
        required_sections = [
            "version:",
            "tier0_smoke_tests:",
            "tier1_critical_tests:",
            "enforcement_tiers:",
        ]

        missing_sections = []
        for section in required_sections:
            if section not in content:
                missing_sections.append(section)

        assert not missing_sections, f"Missing config sections: {missing_sections}"

        # Check that file has substantial content
        lines = [
            line.strip()
            for line in content.split("\n")
            if line.strip() and not line.strip().startswith("#")
        ]
        assert (
            len(lines) > 30
        ), f"Config file appears too short: {len(lines)} non-empty lines"

        print("✓ Configuration file structure valid")

    except Exception as e:
        raise AssertionError(f"Config structure validation failed: {e}")


def test_tier0_config_content():
    """
    Test Tier 0 configuration content.

    Algorithm Approach: Verify that Tier 0 smoke test configuration is present and valid.

    Returns:
    bool: True if Tier 0 config is valid

    Raises:
    AssertionError: If Tier 0 config is invalid
    """
    config_path = Path("__csf/config/tier1_tests.yaml")

    try:
        with open(config_path, encoding="utf-8") as f:
            content = f.read()

        # Check Tier 0 section structure
        tier0_section_found = False
        in_tier0_section = False
        tier0_has_tests = False

        lines = content.split("\n")
        for line in lines:
            line = line.strip()
            if line == "tier0_smoke_tests:":
                tier0_section_found = True
                in_tier0_section = True
                continue
            elif line.endswith("_tests:") and in_tier0_section:
                # We've moved to another section
                in_tier0_section = False
            elif in_tier0_section and line and not line.startswith("#"):
                # Found content in tier0 section
                tier0_has_tests = True

        assert tier0_section_found, "tier0_smoke_tests section not found"
        assert tier0_has_tests, "tier0_smoke_tests section appears empty"

        # Look for specific tier0 test patterns
        tier0_patterns = [
            "test_basic_import.py",
            "test_core_functionality.py",
            "test_system_health.py",
            "test_config_loading.py",
        ]

        found_patterns = []
        for pattern in tier0_patterns:
            if pattern in content:
                found_patterns.append(pattern)

        assert (
            len(found_patterns) >= 2
        ), f"Too few Tier 0 test patterns found: {found_patterns}"

        print(
            f"✓ Tier 0 configuration valid ({len(found_patterns)} test patterns found)"
        )

    except Exception as e:
        raise AssertionError(f"Tier 0 config validation failed: {e}")


def test_environment_variable_defaults():
    """
    Test environment variable configuration defaults.

    Algorithm Approach: Check that environment variables have sensible defaults.

    Returns:
    bool: True if environment variable defaults are working

    Raises:
    AssertionError: If environment variable defaults are problematic
    """
    # Test that required environment variables can be read
    required_vars = ["PATH"]  # PATH should always exist

    for var in required_vars:
        value = os.environ.get(var)
        assert value is not None, f"Required environment variable {var} is missing"
        assert isinstance(value, str), f"Environment variable {var} is not a string"
        assert len(value) > 0, f"Environment variable {var} is empty"

    # Test optional CSF NIP environment variables
    csf_vars = [
        "CSF_STRICT_MODE",
        "CSF_TIER1_BLOCKING",
        "CSF_NEW_FIREWALL_RULES",
        "CSF_TDD_LEVEL",
        "CSF_TDD_EVIDENCE",
    ]

    optional_values = {}
    for var in csf_vars:
        optional_values[var] = os.environ.get(var, "NOT_SET")

    print("✓ Environment variable defaults accessible")
    for var, value in optional_values.items():
        print(f"  {var}: {value}")


def test_config_path_resolution():
    """
    Test configuration path resolution.

    Algorithm Approach: Verify that configuration paths resolve correctly.

    Returns:
    bool: True if path resolution works correctly

    Raises:
    AssertionError: If path resolution fails
    """
    project_root = Path.cwd()

    # Test that we can resolve config-related paths
    config_dir = project_root / "__csf/config"
    src_dir = project_root / "__csf/src"

    assert config_dir.exists(), f"Config directory not found: {config_dir}"
    assert src_dir.exists(), f"Src directory not found: {src_dir}"

    # Test path resolution
    resolved_config = config_dir.resolve()
    resolved_src = src_dir.resolve()

    assert (
        resolved_config.exists()
    ), f"Resolved config path not found: {resolved_config}"
    assert resolved_src.exists(), f"Resolved src path not found: {resolved_src}"

    # Test relative path calculations
    try:
        relative_path = src_dir.relative_to(project_root)
        # Handle both Unix and Windows path separators
        relative_str = str(relative_path).replace("\\", "/")
        assert (
            relative_str == "__csf/src"
        ), f"Unexpected relative path: {relative_path}"
    except ValueError as e:
        raise AssertionError(f"Cannot calculate relative path: {e}")

    print("✓ Configuration path resolution working correctly")


def test_basic_error_handling():
    """
    Test basic error handling in configuration loading.

    Algorithm Approach: Test that configuration system handles errors gracefully.

    Returns:
    bool: True if error handling works correctly

    Raises:
    AssertionError: If error handling is insufficient
    """
    # Test handling of non-existent config file
    non_existent_path = Path("__csf/config/non_existent_config.yaml")

    assert not non_existent_path.exists(), "Test file should not exist"

    try:
        with open(non_existent_path) as f:
            content = f.read()
        raise AssertionError("Should have failed to open non-existent file")
    except FileNotFoundError:
        pass  # Expected
    except Exception as e:
        raise AssertionError(f"Unexpected error type: {e}")

    # Test handling of malformed file (create a test file)
    malformed_config = Path("tests/test_outputs/malformed_config.yaml")
    try:
        # Create a malformed YAML file
        with open(malformed_config, "w") as f:
            f.write("invalid: yaml: content:\n  - missing\n    proper: structure")

        # Try to read it (we're not parsing YAML, just reading)
        with open(malformed_config) as f:
            content = f.read()
            assert len(content) > 0, "Malformed config file should be readable"

        # Cleanup
        malformed_config.unlink()

        print("✓ Basic error handling working correctly")

    except Exception as e:
        # Cleanup on error
        if malformed_config.exists():
            malformed_config.unlink()
        raise AssertionError(f"Error handling test failed: {e}")


def test_config_file_integrity():
    """
    Test configuration file integrity.

    Algorithm Approach: Verify that configuration files are not corrupted.

    Returns:
    bool: True if config files have integrity

    Raises:
    AssertionError: If config files appear corrupted
    """
    config_path = Path("__csf/config/tier1_tests.yaml")

    try:
        # Check file size
        file_size = config_path.stat().st_size
        assert file_size > 1000, f"Config file too small: {file_size} bytes"
        assert file_size < 1024 * 1024, f"Config file too large: {file_size} bytes"

        # Check for basic UTF-8 readability
        with open(config_path, encoding="utf-8") as f:
            content = f.read()

        # Check for null bytes (sign of corruption)
        assert (
            "\x00" not in content
        ), "Config file contains null bytes (possible corruption)"

        # Check for BOM (Byte Order Mark)
        if content.startswith("\ufeff"):
            print("⚠ Config file has BOM, consider removing")

        # Check for basic structural elements
        has_colons = ":" in content
        has_newlines = "\n" in content
        has_content = len(content.strip()) > 0

        assert has_colons, "Config file missing colons (YAML structure)"
        assert has_newlines, "Config file missing newlines"
        assert has_content, "Config file appears empty"

        print(f"✓ Configuration file integrity verified ({file_size} bytes)")

    except Exception as e:
        raise AssertionError(f"Config integrity check failed: {e}")


def run_all_config_loading_tests():
    """
    Run all configuration loading smoke tests.

    Algorithm Approach: Execute all config loading tests in sequence and report results.

    Returns:
    tuple: (total_tests, passed_tests, failed_tests)
    """
    test_functions = [
        test_main_config_accessibility,
        test_config_file_structure,
        test_tier0_config_content,
        test_environment_variable_defaults,
        test_config_path_resolution,
        test_basic_error_handling,
        test_config_file_integrity,
    ]

    total_tests = len(test_functions)
    passed_tests = 0
    failed_tests = []

    print("Running Configuration Loading Smoke Tests...")
    print("=" * 50)

    for test_func in test_functions:
        try:
            test_func()
            passed_tests += 1
        except Exception as e:
            failed_tests.append(f"{test_func.__name__}: {e}")
            print(f"✗ {test_func.__name__} failed: {e}")

    print("=" * 50)
    print(f"Configuration Loading Tests: {passed_tests}/{total_tests} passed")

    if failed_tests:
        print("Failed tests:")
        for failure in failed_tests:
            print(f"  - {failure}")

    return total_tests, passed_tests, failed_tests


if __name__ == "__main__":
    """
    Main execution for standalone testing.
    """
    total, passed, failed = run_all_config_loading_tests()

    if len(failed) == 0:
        print("✅ All Configuration Loading smoke tests passed!")
        sys.exit(0)
    else:
        print("❌ Some Configuration Loading smoke tests failed!")
        sys.exit(1)
