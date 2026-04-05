#!/usr/bin/env python3
"""Test hook for RELAY pattern - safe, does nothing"""

# Configuration: Set to False to disable this hook without restarting CC
ENABLED = True

import json
import sys


def main():
    """Entry point with ENABLED toggle for easy iteration."""
    # Read input
    input_text = sys.stdin.read()
    if input_text.strip():
        try:
            data = json.loads(input_text)
        except json.JSONDecodeError:
            data = {"prompt": ""}
    else:
        data = {"prompt": ""}

    # Quick exit if disabled - pass through silently
    if not ENABLED:
        print(json.dumps(data))
        return

    # RELAY output when enabled
    print("RELAY_TO_USER:", flush=True)
    print("🧪 TEST: Hook relay working", flush=True)
    print("END_RELAY", flush=True)

    # Pass through unchanged
    print(json.dumps(data))

if __name__ == "__main__":
    main()
