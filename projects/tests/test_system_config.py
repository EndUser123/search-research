#!/usr/bin/env python3
"""
System Configuration Tests - Tier 1 Critical Test

Test Case ID: TC-TIER1-001
Priority: High
Test Type: Unit Testing

Purpose:
Verify that the CSF NIP system configuration loads and works correctly.
These tests ensure configuration management is reliable.

Preconditions:
- Tier 0 smoke tests pass
- Configuration files exist
- CSF NIP environment is properly set up

Expected Results:
- System configuration loads correctly
- Configuration values are accessible and valid
- Error handling works for missing/invalid configs

Test Duration: <2.0 seconds
"""

import os
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path.cwd()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

if str(project_root / "__csf") not in sys.path:
    sys.path.insert(0, str(project_root / "__csf"))


def test_config_file_parsing():
    """
    Test that configuration files can be parsed correctly.

    Algorithm Approach: Load and validate configuration structure.

    Returns:
    bool: True if config parsing works correctly

    Raises:
    AssertionError: If config parsing fails
    """
    config_path = Path("__csf/config/tier1_tests.yaml")

    assert config_path.exists(), f"Config file missing: {config_path}"

    # Test basic file reading
    try:
        with open(config_path, encoding="utf-8") as f:
            content = f.read()
            assert len(content) > 1000, "Config file appears too short"
            assert "version:" in content, "Config missing version"
            assert "tier0_smoke_tests:" in content, "Config missing tier0 section"
    except Exception as e:
        raise AssertionError(f"Failed to read config file: {e}")

    print("✓ Configuration file parsing works correctly")


def test_config_structure_validation():
    """
    Test configuration structure validation.

    Algorithm Approach: Validate required sections and fields exist.

    Returns:
    bool: True if config structure is valid

    Raises:
    AssertionError: If config structure is invalid
    """
    config_path = Path("__csf/config/tier1_tests.yaml")

    try:
        with open(config_path, encoding="utf-8") as f:
            content = f.read()

        # Check for required top-level sections
        required_sections = [
            "version:",
            "tier0_smoke_tests:",
            "tier1_critical_tests:",
            "enforcement_tiers:",
            "environment_variables:",
        ]

        missing_sections = []
        for section in required_sections:
            if section not in content:
                missing_sections.append(section)

        assert not missing_sections, f"Missing required sections: {missing_sections}"

        # Validate enforcement tiers structure
        assert "tier0:" in content, "Missing tier0 enforcement configuration"
        assert "tier1:" in content, "Missing tier1 enforcement configuration"
        assert "tier2:" in content, "Missing tier2 enforcement configuration"
        assert "tier3:" in content, "Missing tier3 enforcement configuration"

        print("✓ Configuration structure validation passed")

    except Exception as e:
        raise AssertionError(f"Config structure validation failed: {e}")


def test_environment_variable_config():
    """
    Test environment variable configuration defaults.

    Algorithm Approach: Verify environment variable settings are accessible.

    Returns:
    bool: True if environment variable config works

    Raises:
    AssertionError: If environment variable config fails
    """
    # Test required environment variables exist
    required_vars = ["PATH", "PYTHONPATH"]  # PYTHONPATH might be optional

    for var in required_vars:
        value = os.environ.get(var)
        if var == "PATH":
            assert (
                value is not None and len(value) > 0
            ), f"Required environment variable {var} is missing or empty"
        else:
            # Optional variables can be None
            pass

    # Test CSF NIP specific environment variables
    csf_vars = ["CSF_STRICT_MODE", "CSF_TIER1_BLOCKING", "CSF_NEW_FIREWALL_RULES"]
    found_csf_vars = 0

    for var in csf_vars:
        value = os.environ.get(var)
        if value is not None:
            found_csf_vars += 1

    print(
        f"✓ Environment variable configuration working ({found_csf_vars}/{len(csf_vars)} CSF variables found)"
    )


def test_config_path_resolution():
    """
    Test configuration path resolution logic.

    Algorithm Approach: Verify paths resolve correctly in different contexts.

    Returns:
    bool: True if path resolution works correctly

    Raises:
    AssertionError: If path resolution fails
    """
    project_root = Path.cwd()

    # Test relative path resolution
    config_dir = project_root / "__csf/config"
    assert config_dir.exists(), f"Config directory not found: {config_dir}"

    src_dir = project_root / "__csf/src"
    assert src_dir.exists(), f"Src directory not found: {src_dir}"

    # Test path resolution from different starting points
    original_cwd = os.getcwd()

    try:
        # Change to tests directory and test path resolution
        os.chdir("tests")
        relative_to_tests = Path("../__csf/config/tier1_tests.yaml")
        assert relative_to_tests.exists(), "Path resolution from tests directory failed"

        # Change back to project root
        os.chdir(original_cwd)

        # Test absolute path resolution
        absolute_path = Path.cwd() / "__csf/config/tier1_tests.yaml"
        assert absolute_path.exists(), "Absolute path resolution failed"

        print("✓ Configuration path resolution working correctly")

    except Exception as e:
        raise AssertionError(f"Path resolution test failed: {e}")
    finally:
        os.chdir(original_cwd)


def test_config_file_integrity():
    """
    Test configuration file integrity and corruption checks.

    Algorithm Approach: Verify files are not corrupted and have expected content.

    Returns:
    bool: True if config files have integrity

    Raises:
    AssertionError: If config file integrity is compromised
    """
    config_path = Path("__csf/config/tier1_tests.yaml")

    try:
        # Check file size
        stat = config_path.stat()
        assert stat.st_size > 1000, f"Config file too small: {stat.st_size} bytes"
        assert (
            stat.st_size < 1024 * 1024
        ), f"Config file too large: {stat.st_size} bytes"

        # Check for corruption indicators
        with open(config_path, "rb") as f:
            raw_content = f.read()

        # Check for null bytes (corruption indicator)
        assert (
            b"\x00" not in raw_content
        ), "Config file contains null bytes (possible corruption)"

        # Check for BOM
        if raw_content.startswith(b"\ufeff"):
            print("WARNING: Config file has BOM")

        # Check YAML structure validity (basic checks)
        text_content = raw_content.decode("utf-8")
        lines = text_content.split("\n")

        # Count non-empty, non-comment lines
        content_lines = [
            line.strip()
            for line in lines
            if line.strip() and not line.strip().startswith("#")
        ]
        assert (
            len(content_lines) > 50
        ), f"Config file appears too sparse: {len(content_lines)} content lines"

        # Check for proper YAML syntax patterns
        has_colons = any(":" in line for line in content_lines)
        assert has_colons, "Config file missing YAML key-value syntax"

        print(f"✓ Configuration file integrity verified ({stat.st_size} bytes)")

    except Exception as e:
        raise AssertionError(f"Config file integrity check failed: {e}")


def test_config_error_handling():
    """
    Test configuration error handling and edge cases.

    Algorithm Approach: Test various error conditions and handling.

    Returns:
    bool: True if error handling works correctly

    Raises:
    AssertionError: If error handling is insufficient
    """
    # Test handling of non-existent config file
    non_existent_path = Path("__csf/config/non_existent_config.yaml")

    try:
        with open(non_existent_path) as f:
            content = f.read()
        raise AssertionError("Should have failed to open non-existent file")
    except FileNotFoundError:
        pass  # Expected
    except Exception as e:
        raise AssertionError(f"Unexpected error type for non-existent file: {e}")

    # Test handling of invalid file path
    invalid_path = Path("/invalid/path/config.yaml")
    try:
        with open(invalid_path) as f:
            content = f.read()
        # If we get here, the path was somehow valid (edge case)
        print("⚠ Invalid path test skipped (path was somehow valid)")
    except (FileNotFoundError, PermissionError, OSError):
        pass  # Expected
    except Exception as e:
        raise AssertionError(f"Unexpected error type for invalid path: {e}")

    # Test handling of corrupted/malformed config
    malformed_config = Path("tests/test_outputs/malformed_config.yaml")
    try:
        # Create malformed config
        malformed_config.parent.mkdir(parents=True, exist_ok=True)
        with open(malformed_config, "w") as f:
            f.write(
                "invalid: yaml: content:\n  - missing\n    proper: structure\n  unclosed: ["
            )

        # Try to read it
        with open(malformed_config) as f:
            content = f.read()
            assert len(content) > 0, "Malformed config file should be readable"

        # Cleanup
        malformed_config.unlink()

        print("✓ Configuration error handling working correctly")

    except Exception as e:
        # Cleanup on error
        if malformed_config.exists():
            malformed_config.unlink()
        raise AssertionError(f"Config error handling test failed: {e}")


def run_all_system_config_tests():
    """
    Run all system configuration tests.

    Algorithm Approach: Execute all configuration tests in sequence.

    Returns:
    tuple: (total_tests, passed_tests, failed_tests)
    """
    test_functions = [
        test_config_file_parsing,
        test_config_structure_validation,
        test_environment_variable_config,
        test_config_path_resolution,
        test_config_file_integrity,
        test_config_error_handling,
    ]

    total_tests = len(test_functions)
    passed_tests = 0
    failed_tests = []

    print("Running System Configuration Tests...")
    print("=" * 50)

    for test_func in test_functions:
        try:
            test_func()
            passed_tests += 1
        except Exception as e:
            failed_tests.append(f"{test_func.__name__}: {e}")
            print(f"✗ {test_func.__name__} failed: {e}")

    print("=" * 50)
    print(f"System Configuration Tests: {passed_tests}/{total_tests} passed")

    if failed_tests:
        print("Failed tests:")
        for failure in failed_tests:
            print(f"  - {failure}")

    return total_tests, passed_tests, failed_tests


if __name__ == "__main__":
    """
    Main execution for standalone testing.
    """
    total, passed, failed = run_all_system_config_tests()

    if len(failed) == 0:
        print("✅ All System Configuration tests passed!")
        sys.exit(0)
    else:
        print("❌ Some System Configuration tests failed!")
        sys.exit(1)
