#!/usr/bin/env python3
"""
SessionStart hook for /tdd skill - breadcrumb init was previously delegated
to skill_guard (a library, which is the wrong model for a plugin).
This hook is now a no-op: breadcrumb initialization is the responsibility of
the invoking skill's own PreToolUse/UserPromptSubmit hooks, not cc-aca-session.
"""

import json
import sys


def main():
    print(json.dumps({"decision": "approve"}))
    sys.exit(0)


if __name__ == "__main__":
    main()
