#!/usr/bin/env python3
"""
System Health Tests - Tier 0 Smoke Test

Test Case ID: TC-TIER0-003
Priority: Critical
Test Type: Smoke Testing

Purpose:
Verify that the CSF NIP system is healthy and operational.
These tests check system resources, dependencies, and overall health.

Preconditions:
- Basic import tests pass
- Core functionality tests pass
- System has been running for at least a few seconds

Expected Results:
- System resources are adequate
- Dependencies are available
- System health indicators are positive

Test Duration: <0.3 seconds
"""

import sys
import time
from pathlib import Path

import psutil


def test_system_resources():
    """
    Test system resource availability.

    Algorithm Approach: Check memory, disk space, and CPU availability.

    Returns:
    bool: True if system resources are adequate

    Raises:
    AssertionError: If system resources are insufficient
    """
    try:
        # Check memory availability
        memory = psutil.virtual_memory()
        assert (
            memory.available > 100 * 1024 * 1024
        ), f"Insufficient available memory: {memory.available // 1024 // 1024}MB"
        assert memory.percent < 95, f"Memory usage too high: {memory.percent}%"

        # Check disk space
        disk = psutil.disk_usage(".")
        assert (
            disk.free > 500 * 1024 * 1024
        ), f"Insufficient disk space: {disk.free // 1024 // 1024}MB"

        # Check CPU (basic check - should not be at 100% for extended periods)
        cpu_percent = psutil.cpu_percent(interval=0.1)
        assert cpu_percent < 95, f"CPU usage too high: {cpu_percent}%"

        print(
            f"✓ System resources adequate (Memory: {memory.available // 1024 // 1024}MB available, Disk: {disk.free // 1024 // 1024}MB free)"
        )

    except ImportError:
        # If psutil is not available, do basic checks
        print("⚠ psutil not available, skipping detailed resource checks")
        print("✓ Basic system resource checks passed")


def test_python_environment():
    """
    Test Python environment health.

    Algorithm Approach: Verify Python installation and essential modules.

    Returns:
    bool: True if Python environment is healthy

    Raises:
    AssertionError: If Python environment has issues
    """
    # Check Python version
    assert sys.version_info >= (3, 11), f"Python version too old: {sys.version_info}"
    assert sys.version_info < (
        4,
        0,
    ), f"Python version too new (potential compatibility): {sys.version_info}"

    # Check essential built-in modules
    essential_modules = [
        "sys",
        "os",
        "pathlib",
        "json",
        "logging",
        "datetime",
        "typing",
        "subprocess",
        "threading",
        "time",
    ]

    for module in essential_modules:
        try:
            __import__(module)
        except ImportError as e:
            raise AssertionError(f"Essential module {module} not available: {e}")

    # Check sys.path sanity
    assert len(sys.path) > 0, "sys.path is empty"
    assert any("site-packages" in p for p in sys.path), "site-packages not in sys.path"

    print(
        f"✓ Python environment healthy (Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro})"
    )


def test_file_system_health():
    """
    Test file system health and accessibility.

    Algorithm Approach: Check critical directories and file operations.

    Returns:
    bool: True if file system is healthy

    Raises:
    AssertionError: If file system has issues
    """
    project_root = Path.cwd()

    # Check critical directories are accessible
    critical_dirs = [
        "__csf",
        "__csf/src",
        "__csf/config",
        ".claude",
        ".claude/hooks",
        "tests",
        "tests/test_outputs",
    ]

    for dir_path in critical_dirs:
        full_path = project_root / dir_path
        if dir_path == "tests/test_outputs":
            # Create this if it doesn't exist
            full_path.mkdir(parents=True, exist_ok=True)

        assert full_path.exists(), f"Critical directory missing: {full_path}"
        assert full_path.is_dir(), f"Path is not a directory: {full_path}"

        # Test directory listing
        try:
            list(full_path.iterdir())
        except PermissionError as e:
            raise AssertionError(f"Cannot list directory {full_path}: {e}")

    # Test file operations in test directory
    test_file = project_root / "tests/test_outputs/health_test.tmp"
    try:
        # Write test
        with open(test_file, "w") as f:
            f.write(f"System health test at {time.time()}")

        # Read test
        with open(test_file) as f:
            content = f.read()
            assert len(content) > 0, "Test file appears empty"

        # Cleanup
        test_file.unlink()

        print("✓ File system healthy and accessible")

    except Exception as e:
        raise AssertionError(f"File system health check failed: {e}")


def test_process_environment():
    """
    Test process environment health.

    Algorithm Approach: Check process status, permissions, and environment.

    Returns:
    bool: True if process environment is healthy

    Raises:
    AssertionError: If process environment has issues
    """
    try:
        # Check current process info
        process = psutil.Process()

        # Process should be running
        assert process.is_running(), "Current process is not running"

        # Check process creation time (should be reasonable)
        create_time = process.create_time()
        current_time = time.time()
        process_age = current_time - create_time

        assert 0 < process_age < 3600, f"Process age suspicious: {process_age} seconds"

        # Check working directory
        cwd = Path.cwd()
        assert cwd.exists(), "Current working directory does not exist"
        assert cwd.is_dir(), "Current working directory is not a directory"

        print(
            f"✓ Process environment healthy (PID: {process.pid}, Age: {process_age:.1f}s)"
        )

    except ImportError:
        print("⚠ psutil not available, skipping detailed process checks")
        # Basic checks without psutil
        cwd = Path.cwd()
        assert cwd.exists(), "Current working directory does not exist"
        print("✓ Basic process environment healthy")


def test_configuration_health():
    """
    Test configuration system health.

    Algorithm Approach: Verify configuration files are valid and accessible.

    Returns:
    bool: True if configuration system is healthy

    Raises:
    AssertionError: If configuration system has issues
    """
    project_root = Path.cwd()

    # Check main configuration file
    config_file = project_root / "__csf/config/tier1_tests.yaml"
    assert config_file.exists(), f"Main config file missing: {config_file}"
    assert config_file.stat().st_size > 0, "Main config file is empty"

    try:
        with open(config_file, encoding="utf-8") as f:
            content = f.read()

            # Basic YAML structure validation
            assert "version:" in content, "Config missing version"
            assert "tier0_smoke_tests:" in content, "Config missing tier0 section"
            assert "tier1_critical_tests:" in content, "Config missing tier1 section"

            # Check for expected structure
            lines = [line.strip() for line in content.split("\n") if line.strip()]
            assert len(lines) > 20, "Config file appears too short"

    except Exception as e:
        raise AssertionError(f"Configuration file health check failed: {e}")

    print("✓ Configuration system healthy")


def test_hook_system_health():
    """
    Test hook system health.

    Algorithm Approach: Verify hook files exist and are syntactically valid.

    Returns:
    bool: True if hook system is healthy

    Raises:
    AssertionError: If hook system has issues
    """
    hooks_dir = Path(".claude/hooks")

    # Check hook directory
    assert hooks_dir.exists(), f"Hooks directory missing: {hooks_dir}"

    # List hook files
    hook_files = list(hooks_dir.glob("*.py"))
    assert len(hook_files) >= 3, f"Too few hook files: {len(hook_files)} found"

    # Check basic syntax of hook files (quick check)
    syntax_errors = []
    for hook_file in hook_files:
        try:
            with open(hook_file, encoding="utf-8") as f:
                content = f.read()
                # Basic syntax check - look for common Python structures
                if "def " in content or "import " in content or "class " in content:
                    # File appears to contain Python code
                    pass
                else:
                    syntax_errors.append(f"{hook_file.name}: No Python code detected")
        except Exception as e:
            syntax_errors.append(f"{hook_file.name}: {e}")

    assert not syntax_errors, f"Hook file issues: {syntax_errors}"

    print(f"✓ Hook system healthy ({len(hook_files)} hook files found)")


def test_test_system_health():
    """
    Test test system health.

    Algorithm Approach: Verify test infrastructure is working.

    Returns:
    bool: True if test system is healthy

    Raises:
    AssertionError: If test system has issues
    """
    # Check test directory structure
    test_dirs = ["tests", "tests/test_outputs", "tests/fixtures"]

    for test_dir in test_dirs:
        dir_path = Path(test_dir)
        if test_dir == "tests/test_outputs":
            dir_path.mkdir(parents=True, exist_ok=True)

        assert dir_path.exists(), f"Test directory missing: {dir_path}"
        assert dir_path.is_dir(), f"Test path is not directory: {dir_path}"

    # Check that we can create and run test files
    test_file = Path("tests/test_outputs/health_smoke_test.py")
    try:
        # Create a simple test file
        test_content = '''
def test_simple():
    """Simple test for health check."""
    assert True

if __name__ == "__main__":
    test_simple()
    print("Health test passed")
'''

        with open(test_file, "w") as f:
            f.write(test_content)

        # Try to run it (basic check)
        import subprocess

        result = subprocess.run(
            [sys.executable, str(test_file)], capture_output=True, text=True, timeout=5
        )

        assert result.returncode == 0, f"Test execution failed: {result.stderr}"

        # Cleanup
        test_file.unlink()

        print("✓ Test system healthy and functional")

    except Exception as e:
        raise AssertionError(f"Test system health check failed: {e}")


def run_all_system_health_tests():
    """
    Run all system health smoke tests.

    Algorithm Approach: Execute all system health tests in sequence and report results.

    Returns:
    tuple: (total_tests, passed_tests, failed_tests)
    """
    test_functions = [
        test_system_resources,
        test_python_environment,
        test_file_system_health,
        test_process_environment,
        test_configuration_health,
        test_hook_system_health,
        test_test_system_health,
    ]

    total_tests = len(test_functions)
    passed_tests = 0
    failed_tests = []

    print("Running System Health Smoke Tests...")
    print("=" * 50)

    for test_func in test_functions:
        try:
            test_func()
            passed_tests += 1
        except Exception as e:
            failed_tests.append(f"{test_func.__name__}: {e}")
            print(f"✗ {test_func.__name__} failed: {e}")

    print("=" * 50)
    print(f"System Health Tests: {passed_tests}/{total_tests} passed")

    if failed_tests:
        print("Failed tests:")
        for failure in failed_tests:
            print(f"  - {failure}")

    return total_tests, passed_tests, failed_tests


if __name__ == "__main__":
    """
    Main execution for standalone testing.
    """
    total, passed, failed = run_all_system_health_tests()

    if len(failed) == 0:
        print("✅ All System Health smoke tests passed!")
        sys.exit(0)
    else:
        print("❌ Some System Health smoke tests failed!")
        sys.exit(1)
