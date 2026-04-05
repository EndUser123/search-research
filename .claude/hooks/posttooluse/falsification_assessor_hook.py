#!/usr/bin/env python3
from __future__ import annotations

"""
Falsification Assessor - In-process adapter.

Assesses execution results against expectations to detect mismatches.
Also provides post-action verification reminders.
Absorbed from PostToolUse_falsification_assessor.py.

Original matcher: ^(Edit|Write|Bash|Read|Grep)$
"""

import sys
from pathlib import Path
from typing import Any

from posttooluse.base import PostToolUseHook

_hooks_dir = Path(__file__).resolve().parent.parent
if str(_hooks_dir) not in sys.path:
    sys.path.insert(0, str(_hooks_dir))


class FalsificationAssessorHook(PostToolUseHook):
    """Assesses execution results against expectations."""

    env_var = "FALSIFICATION_ASSESSOR_ENABLED"
    tool_matcher = {"Edit", "Write", "Bash", "Read", "Grep"}

    def process(self, tool_name: str, tool_input: dict[str, Any], tool_response: dict[str, Any]) -> dict[str, Any]:
        # Delegate to the existing post_tool_use function
        from PostToolUse_falsification_assessor import post_tool_use

        result = post_tool_use(tool_name, tool_input, tool_response)

        if result and result.get("user_message"):
            return {"passed": True, "injection": result["user_message"]}

        return {"passed": True}
