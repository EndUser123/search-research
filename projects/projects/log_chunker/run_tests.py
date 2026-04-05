#!/usr/bin/env python3
"""Simple test runner that writes results to a file."""

import subprocess
import sys
import time
from pathlib import Path


def run_tests():
    """Run pytest and write results to file."""
    try:
        # Run pytest with verbose output
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/unit/", "-v", "--tb=short"],
            capture_output=True,
            text=True,
            cwd=Path.cwd(),
        )

        # Write results to file
        with open("test_results.txt", "w", encoding="utf-8") as f:
            f.write("=== PYTEST EXECUTION RESULTS ===\n")
            f.write(f"Return code: {result.returncode}\n")
            f.write(f"Command: {' '.join(result.args)}\n\n")

            f.write("=== STDOUT ===\n")
            f.write(result.stdout)
            f.write("\n\n=== STDERR ===\n")
            f.write(result.stderr)

            if result.returncode == 0:
                f.write("\n\n✅ ALL TESTS PASSED!")
            else:
                f.write(f"\n\n❌ TESTS FAILED (exit code: {result.returncode})")

        # Create completion marker
        try:
            with open("test_completed.marker", "w") as marker:
                marker.write(f"COMPLETED at {time.time()}\n")
                marker.write(f"Exit code: {result.returncode}\n")
            print("Marker file created successfully")
        except Exception as e:
            print(f"ERROR creating marker file: {e}")
            # Create it anyway with basic content
            try:
                with open("test_completed.marker", "w") as marker:
                    marker.write("COMPLETED\n")
            except:
                pass

        print("Test results written to test_results.txt")
        print(f"Exit code: {result.returncode}")

        return result.returncode

    except Exception as e:
        with open("test_results.txt", "w", encoding="utf-8") as f:
            f.write(f"ERROR running tests: {e}")

        # Create marker even on error
        try:
            with open("test_completed.marker", "w") as marker:
                marker.write(f"ERROR at {time.time()}\n")
                marker.write(f"Exception: {e}\n")
        except:
            pass

        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(run_tests())
