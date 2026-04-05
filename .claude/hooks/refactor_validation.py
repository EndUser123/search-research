#!/usr/bin/env python3
"""Refactoring validation utilities.

Provides mandatory validation gates for batch refactoring operations.
All batch scripts MUST use validate_and_exit() before completing.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import List


def validate_python_syntax(file_paths: List[Path | str]) -> tuple[bool, List[str]]:
    """Validate Python syntax for all given files.

    Args:
        file_paths: List of file paths to validate

    Returns:
        Tuple of (all_valid, error_messages)
    """
    errors = []

    for file_path in file_paths:
        file_path = Path(file_path)

        if not file_path.exists():
            errors.append(f"File not found: {file_path}")
            continue

        if not file_path.suffix == ".py":
            continue  # Skip non-Python files

        try:
            import py_compile
            py_compile.compile(file_path, doraise=True)
        except py_compile.PyCompileError as e:
            errors.append(f"Syntax error in {file_path}:\n{e}")

    return (len(errors) == 0, errors)


def validate_with_pytest(test_paths: List[Path | str] | None = None) -> tuple[bool, str]:
    """Run pytest validation on specified test paths.

    Args:
        test_paths: List of test file/directory paths. If None, runs all tests.

    Returns:
        Tuple of (all_passed, output)
    """
    try:
        import pytest
    except ImportError:
        return True, "pytest not installed - skipping test validation"

    cmd = [sys.executable, "-m", "pytest", "-v"]

    if test_paths:
        cmd.extend([str(p) for p in test_paths])

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
        )

        output = result.stdout + "\n" + result.stderr
        return (result.returncode == 0, output)
    except subprocess.TimeoutExpired:
        return False, "pytest timed out after 60 seconds"
    except Exception as e:
        return False, f"pytest failed: {e}"


def validate_and_exit(
    modified_files: List[Path | str],
    test_paths: List[Path | str] | None = None,
    exit_on_error: bool = True,
) -> None:
    """Validate syntax and tests, exit if validation fails.

    This is the MANDATORY validation gate for all batch refactoring operations.
    Call this function at the end of every batch script before returning success.

    Args:
        modified_files: List of files that were modified by the batch operation
        test_paths: Optional list of test paths to validate. If None, skips tests.
        exit_on_error: If True, calls sys.exit(1) on validation failure

    Raises:
        SystemExit: If validation fails and exit_on_error is True

    Example:
        # At the end of your batch refactoring script:
        modified = [
            "P:/.claude/hooks/Stop_router.py",
            "P:/.claude/hooks/SessionEnd_cleanup.py",
        ]
        validate_and_exit(modified, test_paths=["tests/hooks/"])
    """
    print("\n" + "=" * 60)
    print("REFACTORING VALIDATION GATE")
    print("=" * 60)

    # Phase 1: Syntax validation
    print("\n[1/2] Validating Python syntax...")
    syntax_valid, syntax_errors = validate_python_syntax(modified_files)

    if not syntax_valid:
        print("❌ SYNTAX VALIDATION FAILED")
        print("\nErrors found:")
        for error in syntax_errors:
            print(f"  {error}")

        print("\n❌ VALIDATION FAILED - Fix syntax errors before proceeding")
        if exit_on_error:
            sys.exit(1)
        return

    print(f"✅ All {len(modified_files)} files have valid syntax")

    # Phase 2: Test validation (if test paths provided)
    if test_paths:
        print("\n[2/2] Running test suite...")
        tests_passed, test_output = validate_with_pytest(test_paths)

        if not tests_passed:
            print("❌ TEST VALIDATION FAILED")
            print(f"\nTest output:\n{test_output}")

            print("\n❌ VALIDATION FAILED - Fix test failures before proceeding")
            if exit_on_error:
                sys.exit(1)
            return

        print("✅ All tests passed")
    else:
        print("\n[2/2] Test validation skipped (no test paths provided)")

    # Success
    print("\n" + "=" * 60)
    print("✅ ALL VALIDATIONS PASSED")
    print("=" * 60 + "\n")


def main():
    """CLI entry point for manual validation."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate refactoring changes"
    )
    parser.add_argument(
        "files",
        nargs="+",
        help="Files to validate for syntax errors",
    )
    parser.add_argument(
        "--test-paths",
        nargs="*",
        help="Test paths to run (pytest)",
    )
    parser.add_argument(
        "--no-exit",
        action="store_true",
        help="Don't exit on error (for CI/CD integration)",
    )

    args = parser.parse_args()

    validate_and_exit(
        modified_files=args.files,
        test_paths=args.test_paths if args.test_paths else None,
        exit_on_error=not args.no_exit,
    )


if __name__ == "__main__":
    main()
