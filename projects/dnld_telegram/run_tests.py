#!/usr/bin/env python3
"""
Test runner for dnld_telegram unit tests.

Run this script to execute all unit tests and ensure UI improvements
don't break existing functionality.
"""

import subprocess
import sys
from pathlib import Path


def main():
    """Run all unit tests."""
    project_root = Path(__file__).parent
    tests_dir = project_root / "tests"

    if not tests_dir.exists():
        print("❌ Tests directory not found!")
        return False

    print("🧪 Running dnld_telegram unit tests...")
    print(f"📁 Tests directory: {tests_dir}")

    # Try with pytest
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", str(tests_dir), "-v", "--tb=short"],
            cwd=project_root,
            capture_output=True,
            text=True,
        )

        print(result.stdout)
        if result.stderr:
            print("Warnings/Errors:", result.stderr)

        if result.returncode == 0:
            print("✅ All tests passed!")
            return True
        else:
            print(f"❌ Tests failed with return code {result.returncode}")
            return False

    except FileNotFoundError:
        print("⚠️  pytest not found, trying manual test discovery...")

        # Manual test execution as fallback
        test_files = list(tests_dir.glob("test_*.py"))
        if not test_files:
            print("❌ No test files found!")
            return False

        print(f"📋 Found {len(test_files)} test files:")
        for test_file in test_files:
            print(f"  - {test_file.name}")

        all_passed = True
        for test_file in test_files:
            print(f"\n🔍 Running {test_file.name}...")
            try:
                result = subprocess.run(
                    [sys.executable, str(test_file)],
                    cwd=project_root,
                    capture_output=True,
                    text=True,
                )

                if result.returncode == 0:
                    print(f"  ✅ {test_file.name} passed")
                else:
                    print(f"  ❌ {test_file.name} failed")
                    print(f"  Output: {result.stdout}")
                    print(f"  Error: {result.stderr}")
                    all_passed = False

            except Exception as e:
                print(f"  ❌ Error running {test_file.name}: {e}")
                all_passed = False

        if all_passed:
            print("\n✅ All tests passed!")
            return True
        else:
            print("\n❌ Some tests failed!")
            return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
