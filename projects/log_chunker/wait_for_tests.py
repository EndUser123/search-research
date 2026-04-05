#!/usr/bin/env python3
"""Wait for test completion and return results."""

import sys
import time
from pathlib import Path


def wait_for_completion(timeout_seconds=300):
    """Wait for test completion marker, with timeout."""
    marker_file = Path("test_completed.marker")
    results_file = Path("test_results.txt")

    start_time = time.time()

    while time.time() - start_time < timeout_seconds:
        if marker_file.exists() and results_file.exists():
            # Both files exist, tests are complete
            return True
        time.sleep(2)  # Check every 2 seconds

    return False  # Timeout


if __name__ == "__main__":
    print("Waiting for test completion...")

    if wait_for_completion():
        print("Tests completed! Results available.")
        sys.exit(0)
    else:
        print("Timeout waiting for test completion.")
        sys.exit(1)
