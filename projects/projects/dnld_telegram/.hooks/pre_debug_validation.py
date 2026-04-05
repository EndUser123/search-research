#!/usr/bin/env python3
"""
Pre-debugging validation hook
Run this before any debugging session to validate environment
Created as a lesson from the dnld_telegram debugging experience
"""

import subprocess
import sys
from pathlib import Path


def validate_environment():
    """Validate development environment before debugging"""
    print("🔍 PRE-DEBUG ENVIRONMENT VALIDATION")
    print("=" * 50)

    # Check we're in project root
    if not Path("pyproject.toml").exists():
        print("❌ Not in project root - cd to project directory")
        return False
    print("✅ In project root directory")

    # Check virtual environment exists
    if not Path(".venv").exists():
        print("❌ Virtual environment not found - run 'uv sync'")
        return False
    print("✅ Virtual environment exists")

    # Check virtual environment is being used
    result = subprocess.run(
        ["uv", "run", "which", "python"], capture_output=True, text=True
    )
    if result.returncode != 0 or ".venv" not in result.stdout:
        print("❌ Virtual environment not active")
        print("Fix: Use 'uv run python' instead of 'python'")
        return False
    print(f"✅ Using venv Python: {result.stdout.strip()}")

    # Check Python version
    result = subprocess.run(
        ["uv", "run", "python", "--version"], capture_output=True, text=True
    )
    if result.returncode != 0:
        print("❌ Cannot get Python version")
        return False

    version = result.stdout.strip()
    print(f"✅ Python version: {version}")

    # Warn about Python 3.13+ compatibility issues
    if "3.13" in version or "3.14" in version:
        print(
            "⚠️  WARNING: Python 3.13+ may have compatibility issues with some packages"
        )
        print("   Consider using Python 3.11 or 3.12 if you encounter import errors")

    # Test critical imports
    test_imports = [
        ("telethon", "Telegram API library"),
        ("aiosqlite", "Async SQLite library"),
        ("loguru", "Logging library"),
    ]

    for module, description in test_imports:
        result = subprocess.run(
            ["uv", "run", "python", "-c", f"import {module}; print('OK')"],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            print(f"❌ Import failed: {module} ({description})")
            print(f"   Error: {result.stderr.strip()}")

            # Specific guidance for common import failures
            if "circular import" in result.stderr.lower():
                print("   This is likely a Python version compatibility issue")
                print("   Try using Python 3.11 or 3.12 instead")
            elif "no module named" in result.stderr.lower():
                print("   Run: uv add {module}")

            return False
        else:
            print(f"✅ {module}: OK")

    # Test project-specific imports
    project_imports = [
        "dnld_telegram.download.client",
        "dnld_telegram.download.plugins.enumeration",
        "dnld_telegram.download.database.schema",
    ]

    for module in project_imports:
        result = subprocess.run(
            ["uv", "run", "python", "-c", f"import {module}; print('OK')"],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            print(f"❌ Project import failed: {module}")
            print(f"   Error: {result.stderr.strip()}")
            return False
        else:
            print(f"✅ {module}: OK")

    print("\n✅ ENVIRONMENT VALIDATION PASSED")
    print("You can proceed with debugging confidence!")
    return True


def show_debugging_tips():
    """Show tips for effective debugging"""
    print("\n💡 DEBUGGING TIPS")
    print("=" * 20)
    print("1. Always test the actual user workflow first")
    print("2. Use 'uv run python' not 'python' for all testing")
    print("3. Question error messages - they might be symptoms, not causes")
    print("4. Start with simple tests and escalate complexity")
    print("5. When in doubt, validate your testing environment")


def main():
    """Main validation function"""
    if validate_environment():
        show_debugging_tips()
        return 0
    else:
        print("\n❌ ENVIRONMENT VALIDATION FAILED")
        print("Fix the issues above before debugging")
        return 1


if __name__ == "__main__":
    sys.exit(main())
