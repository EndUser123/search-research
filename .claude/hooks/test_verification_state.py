#!/usr/bin/env python3
import json
import time
from pathlib import Path

STATE_DIR = Path("state")
VERIFICATION_TTL = 5 * 60  # 5 minutes

# Check most recent state file
state_files = sorted(STATE_DIR.glob("dependency_verification_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
print(f"Found {len(state_files)} state file(s)")

for state_file in state_files[:3]:
    print(f"\n--- {state_file.name} ---")
    print(f"Modified: {time.ctime(state_file.stat().st_mtime)}")

    with open(state_file) as f:
        state = json.load(f)

    verified = state.get("verified_packages", {})
    print(f"Verified packages: {list(verified.keys())}")

    # Check if serde is verified
    if "serde" in verified:
        timestamp = verified["serde"]
        age = time.time() - timestamp
        is_valid = age < VERIFICATION_TTL
        print("\nserde:")
        print(f"  Timestamp: {timestamp}")
        print(f"  Age: {age:.1f} seconds ({age/60:.1f} minutes)")
        print(f"  Valid (TTL={VERIFICATION_TTL}s): {is_valid}")
