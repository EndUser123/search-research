#!/usr/bin/env python3
"""
Test that UserPromptSubmit subprocess patching doesn't break other hooks.

This test verifies the fix for the cascading import failure bug where
UserPromptSubmit's global subprocess monkey-patching broke imports
for PostToolUse_router and StopHook_unverified_stance.

Bug: https://github.com/anthropics/claude-code/issues/XXX
"""

import subprocess
import sys
from pathlib import Path

# Add hooks directory to path
HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))


def test_user_prompt_submit_imports_cleanly():
    """UserPromptSubmit should import without side effects on subprocess."""
    # Import in a fresh subprocess to ensure clean state
    result = subprocess.run(
        [sys.executable, "-c", "import UserPromptSubmit"],
        cwd=HOOKS_DIR,
        capture_output=True,
        text=True,
        timeout=5,
        creationflags=subprocess.CREATE_NO_WINDOW
    )

    # Should import successfully with no errors
    assert result.returncode == 0, f"Import failed: {result.stderr}"

    # subprocess should NOT be globally patched after import
    # (test by importing another hook that uses asyncio)
    result2 = subprocess.run(
        [sys.executable, "-c", "import UserPromptSubmit; import PostToolUse_router"],
        cwd=HOOKS_DIR,
        capture_output=True,
        text=True,
        timeout=5,
        creationflags=subprocess.CREATE_NO_WINDOW
    )

    # Both imports should succeed (cascading bug fixed)
    assert result2.returncode == 0, f"Cascading import failed: {result2.stderr}"


def test_posttooluse_router_imports_successfully():
    """PostToolUse_router should import without errors."""
    result = subprocess.run(
        [sys.executable, "-c", "import PostToolUse_router"],
        cwd=HOOKS_DIR,
        capture_output=True,
        text=True,
        timeout=5,
        creationflags=subprocess.CREATE_NO_WINDOW
    )

    assert result.returncode == 0, f"Import failed: {result.stderr}"


def test_stop_unverified_stance_imports_successfully():
    """StopHook_unverified_stance should import without errors."""
    result = subprocess.run(
        [sys.executable, "-c", "import StopHook_unverified_stance"],
        cwd=HOOKS_DIR,
        capture_output=True,
        text=True,
        timeout=5,
        creationflags=subprocess.CREATE_NO_WINDOW
    )

    assert result.returncode == 0, f"Import failed: {result.stderr}"


def test_all_hooks_import_together():
    """All three hooks should import successfully in the same process."""
    code = """
import UserPromptSubmit
import PostToolUse_router
import StopHook_unverified_stance
print("All hooks imported successfully")
"""

    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=HOOKS_DIR,
        capture_output=True,
        text=True,
        timeout=5,
        creationflags=subprocess.CREATE_NO_WINDOW
    )

    assert result.returncode == 0, f"Combined import failed: {result.stderr}"
    assert "All hooks imported successfully" in result.stdout


if __name__ == "__main__":
    import pytest

    # Run tests
    pytest.main([__file__, "-v"])
