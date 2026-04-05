#!/usr/bin/env python3
"""
One-time cleanup script for corrupted dependency verification state files.

This script removes invalid package names from existing state files that were
corrupted by the overly permissive regex pattern (\\S+) in earlier versions.

Run this once to clean up existing corrupted state files. After cleanup,
the enhanced validation in PreToolUse_dependency_verification_gate.py will
prevent future corruption.

Usage:
    python clean_dependency_verification_state.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path


def main() -> None:
    """Clean corrupted entries from dependency verification state files."""
    # State directory
    hooks_dir = Path(__file__).resolve().parent
    state_dir = hooks_dir / "state"

    if not state_dir.exists():
        print(f"State directory not found: {state_dir}")
        return

    # Manager-specific validation patterns (same as Fix 3)
    valid_patterns = {
        "npm": re.compile(r"^@[\w.-]+/[\w.-]+$|^[\w.-]+$"),
        "pip": re.compile(r"^[a-zA-Z0-9](?:[a-zA-Z0-9._-]*[a-zA-Z0-9])?$"),
        "cargo": re.compile(r"^[a-z][a-z0-9_-]*$"),
    }

    # Find all dependency verification state files
    state_files = list(state_dir.glob("dependency_verification_*.json"))

    if not state_files:
        print("No dependency verification state files found.")
        return

    print(f"Found {len(state_files)} state file(s) to clean.\n")

    total_removed = 0

    for state_file in state_files:
        print(f"Processing: {state_file.name}")

        try:
            # Read state file
            data = json.loads(state_file.read_text())

            if "verified_packages" not in data:
                print("  No verified_packages section. Skipping.\n")
                continue

            verified = data["verified_packages"]
            original_count = len(verified)

            # Filter out invalid packages
            clean = {}
            removed = []

            for pkg, ts in verified.items():
                # Check against all manager patterns
                is_valid = any(pattern.match(pkg) for pattern in valid_patterns.values())

                if is_valid:
                    clean[pkg] = ts
                else:
                    removed.append(pkg)
                    total_removed += 1

            # Update state if any packages were removed
            if removed:
                data["verified_packages"] = clean

                # Write back to file
                with state_file.open("w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)

                print(f"  Removed {len(removed)} invalid package(s):")
                for pkg in removed:
                    print(f"    - {pkg}")
                print(f"  Kept {len(clean)} valid package(s) (was {original_count})\n")
            else:
                print(f"  All {original_count} package(s) valid. No changes needed.\n")

        except (json.JSONDecodeError, OSError) as e:
            print(f"  Error processing file: {e}\n")

    print(f"Cleanup complete. Removed {total_removed} invalid package(s) total.")


if __name__ == "__main__":
    main()
