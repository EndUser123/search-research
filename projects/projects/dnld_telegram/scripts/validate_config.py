#!/usr/bin/env python3
"""
Configuration validation script for dnld_telegram.
This script validates the project's configuration files.
"""

import subprocess  # config-validator: allow subprocess
import sys

import toml


def validate_config():
    """Validate the main configuration file."""
    try:
        # Load the main config file
        with open("config.toml") as f:
            config = toml.load(f)

        # Check required sections
        if "telegram" not in config:
            print("ERROR: Missing 'telegram' section in config")
            return False

        if "channels" not in config:
            print("ERROR: Missing 'channels' section in config")
            return False

        # Check required telegram fields
        telegram = config["telegram"]
        if "api_id" not in telegram:
            print("ERROR: Missing 'api_id' in telegram section")
            return False

        if "api_hash" not in telegram:
            print("ERROR: Missing 'api_hash' in telegram section")
            return False

        # Validate api_id is an integer
        if not isinstance(telegram["api_id"], int):
            print("ERROR: telegram.api_id must be an integer")
            return False

        # Example of a legitimate subprocess call that should be allowed
        # due to the allow-list comment above
        try:
            result = subprocess.run(
                ["python", "--version"], capture_output=True, text=True, timeout=5
            )
            print(f"Python version check: {result.stdout.strip()}")
        except Exception as e:
            print(f"Warning: Could not check Python version: {e}")

        print("✅ Configuration validation passed")
        return True

    except Exception as e:
        print(f"ERROR: Configuration validation failed: {e}")
        return False


if __name__ == "__main__":
    if not validate_config():
        sys.exit(1)
