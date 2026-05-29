#!/usr/bin/env python3
"""
Anti-Sycophancy Toggle Utility

Usage (from Claude Code or command line):
    python P:/.claude/hooks/anti_sycophancy/toggle.py status   # Check current state
    python P:/.claude/hooks/anti_sycophancy/toggle.py on       # Enable
    python P:/.claude/hooks/anti_sycophancy/toggle.py off      # Disable

Or use environment variable directly:
    export ANTI_SYCOPHANCY_ENABLED=false
    export ANTI_SYCOPHANCY_ENABLED=true
"""

import os
import sys


def get_status():
    return os.environ.get("ANTI_SYCOPHANCY_ENABLED", "true").lower() == "true"

def main():
    if len(sys.argv) < 2:
        print("Usage: toggle.py [status|on|off]")
        sys.exit(1)

    action = sys.argv[1].lower()

    if action == "status":
        enabled = get_status()
        print(f"Anti-Sycophancy: {'ENABLED' if enabled else 'DISABLED'}")
        print(f"  ANTI_SYCOPHANCY_ENABLED={os.environ.get('ANTI_SYCOPHANCY_ENABLED', 'true (default)')}")

    elif action == "on":
        # Can't actually set env var persistently from Python for parent shell
        # But we can instruct the user
        print("To enable anti-sycophancy, run:")
        print("  export ANTI_SYCOPHANCY_ENABLED=true")
        print("")
        print("Or in Claude Code, just say:")
        print('  "Run: export ANTI_SYCOPHANCY_ENABLED=true"')

    elif action == "off":
        print("To disable anti-sycophancy, run:")
        print("  export ANTI_SYCOPHANCY_ENABLED=false")
        print("")
        print("Or in Claude Code, just say:")
        print('  "Run: export ANTI_SYCOPHANCY_ENABLED=false"')

    else:
        print(f"Unknown action: {action}")
        print("Usage: toggle.py [status|on|off]")
        sys.exit(1)

if __name__ == "__main__":
    main()
