#!/usr/bin/env python3
"""
Multi-Terminal Hook Verification Test

Tests that UserPromptSubmit hook loads correctly across multiple terminals
using subprocess isolation. This prevents issues where hooks work in one
terminal but fail in another due to stale state or caching.

Problem: Previous UserPromptSubmit import failures were terminal-specific
due to bytecode cache corruption. This test catches such issues early.

Integration:
    Run as part of pytest test suite
    Also runnable standalone: python test_multi_terminal_hooks.py

Usage:
    pytest tests/test_multi_terminal_hooks.py -v
    python tests/test_multi_terminal_hooks.py
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def get_hooks_dir() -> Path:
    """Get hooks directory path."""
    return Path(__file__).resolve().parent.parent


def create_test_input(prompt: str = "test prompt") -> dict:
    """Create test input for UserPromptSubmit hook."""
    return {
        "prompt": prompt,
        "message": prompt,
        "session_id": "test_session",
        "terminal_id": "test_terminal",
    }


def run_hook_in_subprocess(hook_path: Path, input_data: dict) -> dict:
    """Run hook in isolated subprocess.

    Simulates separate terminal execution without sharing interpreter state.
    This catches issues with:
    - Stale module imports
    - Bytecode cache corruption
    - Terminal-specific state contamination
    """
    input_json = json.dumps(input_data)

    try:
        result = subprocess.run(
            [sys.executable, str(hook_path)],
            input=input_json,
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(hook_path.parent),
        )

        output = result.stdout.strip()
        if output:
            try:
                parsed = json.loads(output)
                # Add exit code for verification
                parsed["exit_code"] = result.returncode
                return parsed
            except json.JSONDecodeError:
                return {"raw_output": output, "exit_code": result.returncode}

        # Empty output means success (no injections needed)
        return {"exit_code": result.returncode, "output": "empty"}

    except subprocess.TimeoutExpired:
        return {"error": "Hook execution timeout", "exit_code": -1}
    except Exception as e:
        return {"error": str(e), "exit_code": -1}


def test_userpromptsubmit_imports() -> None:
    """Test that UserPromptSubmit hook imports successfully in isolation."""
    hooks_dir = get_hooks_dir()
    hook_path = hooks_dir / "UserPromptSubmit.py"

    if not hook_path.exists():
        # Skip if hook doesn't exist yet
        return

    # Run in subprocess (isolated environment)
    result = run_hook_in_subprocess(hook_path, create_test_input())

    # Check for import errors
    assert "error" not in result, f"Import error in isolated subprocess: {result['error']}"
    assert result.get("exit_code") == 0, f"Hook failed with exit code {result.get('exit_code')}"


def test_userpromptsubmit_registry_import() -> None:
    """Test that registry module imports correctly."""
    hooks_dir = get_hooks_dir()
    registry_path = hooks_dir / "UserPromptSubmit_modules" / "registry.py"

    if not registry_path.exists():
        return

    # Test registry module in isolation
    result = subprocess.run(
        [sys.executable, "-c", "import sys; sys.path.insert(0, '.'); from UserPromptSubmit_modules import registry; print('OK')"],
        capture_output=True,
        text=True,
        timeout=5,
        cwd=str(hooks_dir),
    )

    assert result.returncode == 0, f"Registry import failed: {result.stderr}"
    assert "OK" in result.stdout, "Registry import didn't complete"


def test_userpromptsubmit_relative_imports() -> None:
    """Test that relative imports in package work correctly."""
    hooks_dir = get_hooks_dir()
    test_code = """
import sys
sys.path.insert(0, '.')

# Test importing through the package
from UserPromptSubmit_modules import registry

# Test that registry can access its dependencies
assert hasattr(registry, 'run_hooks'), "registry.run_hooks not found"

print('Relative imports OK')
"""

    result = subprocess.run(
        [sys.executable, "-c", test_code],
        capture_output=True,
        text=True,
        timeout=5,
        cwd=str(hooks_dir),
    )

    assert result.returncode == 0, f"Relative imports failed: {result.stderr}"
    assert "Relative imports OK" in result.stdout


def test_backward_compatibility_alias() -> None:
    """Test that backward compatibility alias works."""
    hooks_dir = get_hooks_dir()
    test_code = """
import sys
sys.path.insert(0, '.')

# Old import style should still work via alias
import UserPromptSubmit_modules

# Verify alias exists in sys.modules
assert 'UserPromptSubmit' in sys.modules, 'Backward compatibility alias not created'
assert sys.modules['UserPromptSubmit'] is sys.modules['UserPromptSubmit_modules'], 'Alias points to wrong module'

print('Backward compatibility OK')
"""

    result = subprocess.run(
        [sys.executable, "-c", test_code],
        capture_output=True,
        text=True,
        timeout=5,
        cwd=str(hooks_dir),
    )

    assert result.returncode == 0, f"Backward compatibility failed: {result.stderr}"
    assert "Backward compatibility OK" in result.stdout


def run_all_tests() -> int:
    """Run all tests when script is executed directly."""
    print("Running multi-terminal hook verification tests...\n")

    tests = [
        ("UserPromptSubmit imports", test_userpromptsubmit_imports),
        ("Registry imports", test_userpromptsubmit_registry_import),
        ("Relative imports", test_userpromptsubmit_relative_imports),
        ("Backward compatibility", test_backward_compatibility_alias),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            print(f"Testing: {name}...", end=" ")
            test_func()
            print("✓ PASS")
            passed += 1
        except AssertionError as e:
            print("✗ FAIL")
            print(f"  Error: {e}")
            failed += 1
        except Exception as e:
            print("✗ ERROR")
            print(f"  Unexpected error: {e}")
            failed += 1

    print(f"\n{'='*60}")
    print(f"Results: {passed} passed, {failed} failed")
    print(f"{'='*60}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
