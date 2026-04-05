#!/usr/bin/env python3
"""
Breadcrumb Initialization Hook for UserPromptSubmit
======================================================

This is a redirect to the actual implementation in the skill-guard package.

The implementation lives at:
P:/packages/skill-guard/src/skill_guard/breadcrumb/hooks/UserPromptSubmit_breadcrumb_init.py

This redirect pattern is used because Windows symlinks require admin privileges.
"""

import sys
from pathlib import Path

# Add skill-guard to path
SKILL_GUARD = Path("P:/packages/skill-guard/src")
if SKILL_GUARD.exists():
    sys.path.insert(0, str(SKILL_GUARD))

# Import and run the actual hook implementation
from skill_guard.breadcrumb.hooks.UserPromptSubmit_breadcrumb_init import (
    process_prompt_for_breadcrumbs,
)

if __name__ == "__main__":
    # Hook entry point
    import json
    input_data = json.loads(sys.stdin.read())
    result = process_prompt_for_breadcrumbs(input_data.get("prompt", ""), input_data)

    if result:
        print(json.dumps({"additionalContext": result}))
    else:
        print(json.dumps({}))
