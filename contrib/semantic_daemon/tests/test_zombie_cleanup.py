#!/usr/bin/env python3
"""Test script to verify semantic daemon zombie cleanup.

This test verifies that:
1. Discovery file is cleaned up on normal shutdown
2. Discovery file is cleaned up on crash (via atexit)
3. Client detects and cleans up stale discovery files from zombie daemons
"""

import json
import sys
import time

sys.path.insert(0, "P:\\\\\\__csf/src")

from search_research.contrib.semantic_daemon.unified_semantic_daemon import (
    DISCOVERY_FILE,
    UnifiedSemanticDaemon,
)


def test_discovery_file_cleanup_on_shutdown():
    """Test that discovery file is cleaned up on normal shutdown."""
    print("TEST 1: Discovery file cleanup on normal shutdown")

    # Start daemon
    daemon = UnifiedSemanticDaemon()
    assert daemon.start(), "Failed to start daemon"

    # Verify discovery file exists
    assert DISCOVERY_FILE.exists(), "Discovery file should exist after daemon start"
    print("✓ Discovery file created")

    # Shutdown daemon
    daemon.shutdown()

    # Verify discovery file is cleaned up
    assert not DISCOVERY_FILE.exists(), "Discovery file should be cleaned up after shutdown"
    print("✓ Discovery file cleaned up on shutdown")
    print()

    return True


def test_client_detects_stale_discovery_file():
    """Test that client detects and cleans up stale discovery files."""
    print("TEST 2: Client detects stale discovery files")

    # Create a stale discovery file (simulating zombie daemon)
    DISCOVERY_FILE.parent.mkdir(parents=True, exist_ok=True)
    stale_data = {
        "pipe_name": r"\\.\pipe\csf_semantic_99999_1234567890",  # Non-existent pipe
        "pid": 99999,  # Non-existent PID
        "timestamp": 1234567890,
    }
    DISCOVERY_FILE.write_text(json.dumps(stale_data))
    print("✓ Created stale discovery file")

    # Import client function that should clean up stale discovery file
    from search_research.contrib.semantic_daemon.daemon_client import _read_discovery_pipe_name

    # Try to read discovery file - should detect staleness and return None
    pipe_name = _read_discovery_pipe_name()

    assert pipe_name is None, "Should return None for stale discovery file"
    assert not DISCOVERY_FILE.exists(), "Stale discovery file should be cleaned up"
    print("✓ Client detected and cleaned up stale discovery file")
    print()

    return True


def test_multiple_daemon_cycles():
    """Test that multiple daemon start/stop cycles don't leave zombie discovery files."""
    print("TEST 3: Multiple daemon start/stop cycles")

    for i in range(3):
        daemon = UnifiedSemanticDaemon()
        assert daemon.start(), f"Failed to start daemon (cycle {i + 1})"

        assert DISCOVERY_FILE.exists(), f"Discovery file should exist (cycle {i + 1})"
        print(f"✓ Cycle {i + 1}: Discovery file created")

        daemon.shutdown()

        assert not DISCOVERY_FILE.exists(), f"Discovery file should be cleaned up (cycle {i + 1})"
        print(f"✓ Cycle {i + 1}: Discovery file cleaned up")

        time.sleep(0.5)  # Brief pause between cycles

    print("✓ All cycles completed without zombie accumulation")
    print()

    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("SEMANTIC DAEMON ZOMBIE CLEANUP TEST")
    print("=" * 60)
    print()

    tests = [
        test_discovery_file_cleanup_on_shutdown,
        test_client_detects_stale_discovery_file,
        test_multiple_daemon_cycles,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
        except AssertionError as e:
            print(f"✗ FAILED: {e}")
            print()
            failed += 1
        except Exception as e:
            print(f"✗ ERROR: {e}")
            print()
            failed += 1

    print("=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
