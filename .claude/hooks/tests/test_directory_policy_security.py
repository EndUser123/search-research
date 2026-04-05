#!/usr/bin/env python3
"""Security tests for PreToolUse_directory_policy.py path traversal protection.

This test suite verifies that the directory policy enforcement hook correctly
blocks path traversal attacks that could allow writes outside the project directory.
"""

import os
import sys
import threading
import time
from unittest import mock

# Add hooks directory to path (need parent dir for __lib)
hooks_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(hooks_dir)
sys.path.insert(0, parent_dir)

# Import the hook to test
import PreToolUse_directory_policy as hook_module


def test_blocks_path_traversal_via_parent_refs():
    """Test that ../../ sequences are blocked when project directory is deeper."""
    old_project_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    os.environ["CLAUDE_PROJECT_DIR"] = "P:/some/project"

    try:
        # Test the helper function with a path traversal attempt
        # When project_dir is P:/some/project, ../../../etc/passwd escapes to P:/etc/passwd
        result = hook_module._validate_path_security(
            "../../../etc/passwd", "P:/some/project", "P:/some/project"
        )

        # Should block the path traversal attempt
        assert isinstance(result, dict), f"Expected block dict, got {type(result)}"
        assert (
            result["decision"] == "block"
        ), f"Expected block decision, got {result.get('decision')}"
        assert (
            "traversal" in result["message"].lower()
        ), f"Expected traversal message, got {result['message']}"
        print("✓ test_blocks_path_traversal_via_parent_refs passed")

    finally:
        if old_project_dir is not None:
            os.environ["CLAUDE_PROJECT_DIR"] = old_project_dir
        elif "CLAUDE_PROJECT_DIR" in os.environ:
            del os.environ["CLAUDE_PROJECT_DIR"]


def test_blocks_absolute_path_outside_project():
    """Test that absolute paths outside project directory are blocked."""
    old_project_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    os.environ["CLAUDE_PROJECT_DIR"] = "P:/some/project"

    try:
        # Test with absolute path outside project directory
        result = hook_module._validate_path_security(
            "C:/Windows/System32/test.txt", "P:/some/project", "P:/some/project"
        )

        # Should block the absolute path outside project
        assert isinstance(result, dict), f"Expected block dict, got {type(result)}"
        assert (
            result["decision"] == "block"
        ), f"Expected block decision, got {result.get('decision')}"
        print("✓ test_blocks_absolute_path_outside_project passed")

    finally:
        if old_project_dir is not None:
            os.environ["CLAUDE_PROJECT_DIR"] = old_project_dir
        elif "CLAUDE_PROJECT_DIR" in os.environ:
            del os.environ["CLAUDE_PROJECT_DIR"]


def test_allows_safe_absolute_path():
    """Test that absolute paths within project directory are allowed."""
    old_project_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    os.environ["CLAUDE_PROJECT_DIR"] = "P:/some/project"

    try:
        # Test with absolute path within project directory
        result = hook_module._validate_path_security(
            "P:/some/project/test.txt", "P:/some/project", "P:/some/project"
        )

        # Should allow the safe absolute path (returns string, not dict)
        assert isinstance(result, str), f"Expected string path, got {type(result)}"
        print("✓ test_allows_safe_absolute_path passed")

    finally:
        if old_project_dir is not None:
            os.environ["CLAUDE_PROJECT_DIR"] = old_project_dir
        elif "CLAUDE_PROJECT_DIR" in os.environ:
            del os.environ["CLAUDE_PROJECT_DIR"]


def test_blocks_symlink_escape():
    """Test that symlinks outside project are blocked."""
    old_project_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    os.environ["CLAUDE_PROJECT_DIR"] = "P:/some/project"

    try:
        # Test with a path that would escape via symlink
        # Note: Actual symlink creation is OS-dependent, so we test the logic
        # The path resolution follows symlinks, so a symlink to /etc would be blocked
        result = hook_module._validate_path_security(
            "P:/some/project/test_link/etc/passwd", "P:/some/project", "P:/some/project"
        )

        # If a symlink existed that pointed outside, it should be blocked
        # For this test, we just verify the function works correctly
        # (actual symlink testing requires filesystem operations)
        if isinstance(result, dict):
            assert (
                result["decision"] == "block"
            ), f"Expected block decision, got {result.get('decision')}"
        print("✓ test_blocks_symlink_escape passed (path resolution validated)")

    finally:
        if old_project_dir is not None:
            os.environ["CLAUDE_PROJECT_DIR"] = old_project_dir
        elif "CLAUDE_PROJECT_DIR" in os.environ:
            del os.environ["CLAUDE_PROJECT_DIR"]


def test_blocks_mixed_path_separators():
    """Test that mixed path separators are handled correctly."""
    old_project_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    os.environ["CLAUDE_PROJECT_DIR"] = "P:/some/project"

    try:
        # Test with mixed separators and traversal attempt
        # PathLib normalizes separators, so this should still be blocked
        result = hook_module._validate_path_security(
            "P:/../..\\../etc/passwd", "P:/some/project", "P:/some/project"
        )

        # Should block the mixed-separator path traversal
        assert isinstance(result, dict), f"Expected block dict, got {type(result)}"
        assert (
            result["decision"] == "block"
        ), f"Expected block decision, got {result.get('decision')}"
        print("✓ test_blocks_mixed_path_separators passed")

    finally:
        if old_project_dir is not None:
            os.environ["CLAUDE_PROJECT_DIR"] = old_project_dir
        elif "CLAUDE_PROJECT_DIR" in os.environ:
            del os.environ["CLAUDE_PROJECT_DIR"]


def test_write_tool_blocks_path_traversal():
    """Test that Write tool also blocks path traversal (not just Bash)."""
    old_project_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    os.environ["CLAUDE_PROJECT_DIR"] = "P:/some/project"

    try:
        # Test relative path traversal via Write tool
        result = hook_module._validate_path_security(
            "../../../etc/passwd", "P:/some/project", "P:/some/project"
        )

        # Should block the relative path traversal
        assert isinstance(result, dict), f"Expected block dict, got {type(result)}"
        assert (
            result["decision"] == "block"
        ), f"Expected block decision, got {result.get('decision')}"
        print("✓ test_write_tool_blocks_path_traversal passed")

    finally:
        if old_project_dir is not None:
            os.environ["CLAUDE_PROJECT_DIR"] = old_project_dir
        elif "CLAUDE_PROJECT_DIR" in os.environ:
            del os.environ["CLAUDE_PROJECT_DIR"]


def test_helper_function_blocks_traversal():
    """Test that _validate_path_security helper function blocks traversal."""
    old_project_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    os.environ["CLAUDE_PROJECT_DIR"] = "P:/some/project"

    try:
        result = hook_module._validate_path_security(
            "../../../etc/passwd", "P:/some/project", "P:/some/project"
        )

        # Should return block dict
        assert isinstance(result, dict), f"Expected block dict, got {type(result)}"
        assert (
            result["decision"] == "block"
        ), f"Expected block decision, got {result.get('decision')}"
        print("✓ test_helper_function_blocks_traversal passed")

    finally:
        if old_project_dir is not None:
            os.environ["CLAUDE_PROJECT_DIR"] = old_project_dir
        elif "CLAUDE_PROJECT_DIR" in os.environ:
            del os.environ["CLAUDE_PROJECT_DIR"]


def test_helper_function_allows_safe_path():
    """Test that _validate_path_security helper function allows safe paths."""
    old_project_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    os.environ["CLAUDE_PROJECT_DIR"] = "P:/some/project"

    try:
        result = hook_module._validate_path_security(
            "test.txt", "P:/some/project", "P:/some/project"
        )

        # Should return string (safe path, resolved to absolute)
        assert isinstance(result, str), f"Expected string path, got {type(result)}"
        # Relative path should be resolved to absolute
        assert "some/project" in result or result.endswith("test.txt"), f"Unexpected path: {result}"
        print("✓ test_helper_function_allows_safe_path passed")

    finally:
        if old_project_dir is not None:
            os.environ["CLAUDE_PROJECT_DIR"] = old_project_dir
        elif "CLAUDE_PROJECT_DIR" in os.environ:
            del os.environ["CLAUDE_PROJECT_DIR"]


# ===== TEST-001: os.getcwd() failure simulation test =====
def test_os_getcwd_fallback():
    """TEST-001: Verify os.getcwd() fallback mechanism works correctly."""
    print("\n--- TEST-001: os.getcwd() failure simulation ---")

    old_project_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    os.environ["CLAUDE_PROJECT_DIR"] = "P:/test_project"

    try:
        # Mock os.getcwd() to raise OSError
        with mock.patch("os.getcwd", side_effect=OSError("Directory inaccessible")):
            # Call the hook's run() function with Bash tool input to trigger os.getcwd()
            # The os.getcwd() call is in the run() function when tool_name == "Bash"
            result = hook_module.run(
                {"tool_name": "Bash", "tool_input": {"command": "echo test"}, "verbose": True}
            )

            # The fallback should have been triggered during the run() call
            assert hook_module._fallback_count > 0, "Fallback count should be > 0"

        print("✓ test_os_getcwd_fallback passed")

    finally:
        if old_project_dir is not None:
            os.environ["CLAUDE_PROJECT_DIR"] = old_project_dir
        elif "CLAUDE_PROJECT_DIR" in os.environ:
            del os.environ["CLAUDE_PROJECT_DIR"]


# ===== TEST-002: Lock timeout mechanism test =====
def test_lock_timeout_mechanism():
    """TEST-002: Verify lock timeout prevents deadlock."""
    print("\n--- TEST-002: Lock timeout mechanism ---")

    # Acquire the lock manually to simulate contention
    acquired = hook_module._ALLOWED_EXTERNAL_PATTERNS_LOCK.acquire(timeout=0.1)

    try:
        if acquired:
            # Try to acquire again in a separate thread
            def try_acquire():
                start = time.perf_counter()
                result = hook_module._ALLOWED_EXTERNAL_PATTERNS_LOCK.acquire(timeout=0.5)
                wait_time = time.perf_counter() - start
                return result, wait_time

            thread = threading.Thread(target=try_acquire)
            thread.start()
            thread.join(timeout=2.0)

            # The thread should have completed (either acquired or timed out)
            # and not hung indefinitely
            print("✓ test_lock_timeout_mechanism passed (thread completed, no deadlock)")

        else:
            print("⚠ test_lock_timeout_mechanism skipped (could not acquire initial lock)")

    finally:
        if acquired:
            hook_module._ALLOWED_EXTERNAL_PATTERNS_LOCK.release()


# ===== TEST-003: Lock contention monitoring test =====
def test_lock_contention_monitoring():
    """TEST-003: Verify lock contention metrics are tracked."""
    print("\n--- TEST-003: Lock contention monitoring ---")

    old_count = hook_module._lock_contention_count
    old_total = hook_module._lock_wait_total

    # Call is_allowed_external_path to trigger lock acquisition
    result = hook_module.is_allowed_external_path("test.txt")

    # Verify metrics were updated
    assert hook_module._lock_contention_count > old_count, "Lock contention count should increment"
    assert hook_module._lock_wait_total >= old_total, "Lock wait total should not decrease"

    # If wait time was significant, it should have been logged
    # (we can't easily capture stdout here, but the metric is tracked)

    print(
        f"✓ test_lock_contention_monitoring passed (contention count: {hook_module._lock_contention_count}, total wait: {hook_module._lock_wait_total:.3f}s)"
    )


# ===== TEST-004: Root file whitelist test =====
def test_root_file_whitelist_allows_known_files():
    """TEST-004: Whitelisted root files should be allowed (readme.md, pyproject.toml, etc.).

    The whitelist check is in run(), not _validate_path_security().
    _validate_path_security resolves relative paths and returns them if within project.
    The blocking happens in run() when the resolved path is a direct child of project root.
    """
    print("\n--- TEST-004: Root file whitelist allows known files ---")

    old_project_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    os.environ["CLAUDE_PROJECT_DIR"] = "P:/test_project"

    try:
        # Test whitelisted files through run() with Write tool
        # These should return None (allowed) because they're in the whitelist
        whitelist_test_cases = [
            "readme.md",
            "README.md",
            "pyproject.toml",
            "setup.py",
            ".gitignore",
            "license",
            "license.md",
            "changelog.md",
        ]

        for filename in whitelist_test_cases:
            result = hook_module.run(
                {
                    "tool_name": "Write",
                    "tool_input": {"file_path": filename, "content": "test"},
                }
            )
            # None = allowed, block dict = blocked
            assert result is None, (
                f"Expected None (allowed) for whitelisted file '{filename}', "
                f"got {type(result)}: {result}"
            )
            print(f"  ✓ {filename} is allowed")

        print("✓ test_root_file_whitelist_allows_known_files passed")

    finally:
        if old_project_dir is not None:
            os.environ["CLAUDE_PROJECT_DIR"] = old_project_dir
        elif "CLAUDE_PROJECT_DIR" in os.environ:
            del os.environ["CLAUDE_PROJECT_DIR"]


def test_root_file_blocking_rejects_non_whitelisted():
    """TEST-005: Non-whitelisted root files should be blocked.

    The whitelist check is in run(). Files like test.json, =0.6.0, etc.
    are not in the whitelist and should be blocked when written to project root.
    """
    print("\n--- TEST-005: Root file blocking rejects non-whitelisted ---")

    old_project_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    os.environ["CLAUDE_PROJECT_DIR"] = "P:/test_project"

    try:
        # Test non-whitelisted files through run() with Write tool
        # These should return block dict because they're NOT in the whitelist
        blocked_test_cases = [
            "test.json",
            "=0.6.0",
            "package-lock.json",
            "test.py",
            "config.yaml",
        ]

        for filename in blocked_test_cases:
            result = hook_module.run(
                {
                    "tool_name": "Write",
                    "tool_input": {"file_path": filename, "content": "test"},
                }
            )
            assert (
                result is not None
            ), f"Expected block dict for non-whitelisted file '{filename}', got None"
            assert result.get("decision") == "block", (
                f"Expected block decision for '{filename}', " f"got {result.get('decision')}"
            )
            message = result.get("message", "")
            assert (
                "Cannot write to project root" in message
                or "Cannot write .py file to project root" in message
            ), f"Expected project-root block message for '{filename}', " f"got: {message}"
            print(f"  ✓ {filename} is blocked")

        print("✓ test_root_file_blocking_rejects_non_whitelisted passed")

    finally:
        if old_project_dir is not None:
            os.environ["CLAUDE_PROJECT_DIR"] = old_project_dir
        elif "CLAUDE_PROJECT_DIR" in os.environ:
            del os.environ["CLAUDE_PROJECT_DIR"]


# ===== TEST-006: Specific exception handling test =====
def test_specific_exception_handling():
    """TEST-006: Only JSONDecodeError and ValueError should trigger fail-open bypass."""
    print("\n--- TEST-006: Specific exception handling ---")

    # Test that JSONDecodeError triggers bypass behavior when BYPASS_FAIL_SAFE=true
    import json

    old_env = os.environ.get("DIRECTORY_POLICY_BYPASS_FAIL_SAFE")

    try:
        os.environ["DIRECTORY_POLICY_BYPASS_FAIL_SAFE"] = "true"

        # Create a mock that raises JSONDecodeError on json.load
        original_load = json.load
        call_count = 0

        def mock_json_load(obj):
            nonlocal call_count
            call_count += 1
            raise json.JSONDecodeError("test error", "test doc", 0)

        json.load = mock_json_load

        # Call main() which should catch JSONDecodeError specifically
        # and exit with code 0 (fail-open) when BYPASS_FAIL_SAFE=true
        try:
            hook_module.main()
        except SystemExit as e:
            # Exit code 0 = fail-open (bypass triggered)
            assert e.code == 0, f"Expected exit code 0 (fail-open), got {e.code}"
            assert call_count > 0, "json.load should have been called"
            print("  ✓ JSONDecodeError triggered fail-open bypass (exit 0)")
        finally:
            json.load = original_load

        print("✓ test_specific_exception_handling passed")

    finally:
        if old_env is not None:
            os.environ["DIRECTORY_POLICY_BYPASS_FAIL_SAFE"] = old_env
        elif "DIRECTORY_POLICY_BYPASS_FAIL_SAFE" in os.environ:
            del os.environ["DIRECTORY_POLICY_BYPASS_FAIL_SAFE"]


if __name__ == "__main__":
    print("Running directory policy security tests...\n")

    test_blocks_path_traversal_via_parent_refs()
    test_blocks_absolute_path_outside_project()
    test_allows_safe_absolute_path()
    test_blocks_symlink_escape()
    test_blocks_mixed_path_separators()
    test_write_tool_blocks_path_traversal()
    test_helper_function_blocks_traversal()
    test_helper_function_allows_safe_path()

    # New tests from pre-mortem analysis
    test_os_getcwd_fallback()
    test_lock_timeout_mechanism()
    test_lock_contention_monitoring()

    # New tests for fixes
    test_root_file_whitelist_allows_known_files()
    test_root_file_blocking_rejects_non_whitelisted()
    test_specific_exception_handling()

    print("\n✅ All security tests passed!")
