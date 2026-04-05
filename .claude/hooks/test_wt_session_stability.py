#!/usr/bin/env python3
"""
Test WT_SESSION stability across multiple invocations.

This script tests:
1. WT_SESSION is available in hook subprocess context
2. WT_SESSION remains stable across multiple invocations
3. Different terminal windows have different WT_SESSION values
"""

import json
import os
from pathlib import Path

STATE_FILE = Path(__file__).resolve().parent / "state" / "wt_session_test.json"

def test_wt_session_availability():
    """Test if WT_SESSION is available."""
    wt_session = os.environ.get("WT_SESSION")
    print(f"WT_SESSION available: {wt_session is not None}")
    if wt_session:
        print(f"WT_SESSION value: {wt_session}")
        print(f"WT_SESSION length: {len(wt_session)}")
        print(f"WT_SESSION format: UUID-like {wt_session.count('-') == 4}")
    return wt_session

def test_wt_session_stability():
    """Test if WT_SESSION remains stable across invocations."""
    wt_session = os.environ.get("WT_SESSION")
    if not wt_session:
        print("No WT_SESSION available - cannot test stability")
        return None

    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Read previous value if exists
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            data = json.load(f)
        previous_session = data.get("wt_session")
        invocation_count = data.get("invocation_count", 0) + 1

        if previous_session == wt_session:
            print(f"✓ WT_SESSION stable (invocation #{invocation_count})")
            print(f"  Previous: {previous_session}")
            print(f"  Current:  {wt_session}")
        else:
            print(f"✗ WT_SESSION CHANGED (invocation #{invocation_count})")
            print(f"  Previous: {previous_session}")
            print(f"  Current:  {wt_session}")
            print("  WARNING: Terminal ID instability detected!")
    else:
        invocation_count = 1
        print("First invocation - storing WT_SESSION for stability check")
        print(f"WT_SESSION: {wt_session}")

    # Store current value
    with open(STATE_FILE, 'w') as f:
        json.dump({
            "wt_session": wt_session,
            "invocation_count": invocation_count
        }, f)

    return wt_session

def main():
    print("=== WT_SESSION Stability Test ===")
    print(f"Python PID: {os.getpid()}")
    print()

    print("Test 1: WT_SESSION Availability")
    print("-" * 40)
    wt_session = test_wt_session_availability()
    print()

    print("Test 2: WT_SESSION Stability")
    print("-" * 40)
    test_wt_session_stability()
    print()

    print("Test 3: Environment Context")
    print("-" * 40)
    print(f"PROJECT_ROOT: {os.environ.get('PROJECT_ROOT', 'NOT SET')}")
    print(f"CLAUDE_TERMINAL_ID: {os.environ.get('CLAUDE_TERMINAL_ID', 'NOT SET')}")
    print(f"CLAUDE_SESSION_ID: {os.environ.get('CLAUDE_SESSION_ID', 'NOT SET')}")

if __name__ == "__main__":
    main()
