#!/usr/bin/env python3
"""
Breadcrumb Trail Cleanup (SessionEnd Hook)
==========================================

Cleanup was previously delegated to skill_guard (a library, which is the
wrong model for a plugin). This hook is now a no-op: any breadcrumb state
cleanup is the responsibility of the owning skill's own SessionEnd/PreCompact
hooks, not cc-aca-session.
"""

import json
import sys


def run(data: dict) -> dict:
    return {"cleaned": 0, "reason": "No-op: skill_guard library usage removed"}


if __name__ == "__main__":
    input_data = json.loads(sys.stdin.read())
    result = run(input_data)
    print(json.dumps(result, indent=2))
