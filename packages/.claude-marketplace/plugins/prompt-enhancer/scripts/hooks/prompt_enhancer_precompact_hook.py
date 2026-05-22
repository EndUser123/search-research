#!/usr/bin/env python3
"""
PreCompact hook for prompt-enhancer context preservation.

Reads active_enhancement.json from per-terminal artifacts and reinjects
EnhancementResult fields via additionalContext so that enhancement
constraints survive context summarization.

Registered via hook_runner.py in settings.json:
  python "P:/.claude/hooks/__lib/hook_runner.py" "P:/packages/prompt-enhancer/scripts/hooks/prompt_enhancer_precompact_hook.py"
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Add package root to path so we can import schemas
_plugin_root = Path(__file__).parents[2]
sys.path.insert(0, str(_plugin_root))

TERMINAL_ID = os.environ.get("CLAUDE_TERMINAL_ID", "default")
ARTIFACT_DIR = Path.home() / ".claude" / ".artifacts" / TERMINAL_ID / "prompt-enhancer"
ACTIVE_ENHANCEMENT = ARTIFACT_DIR / "active_enhancement.json"


def main() -> None:
    if not ACTIVE_ENHANCEMENT.exists():
        # PreCompact schema — NOT hookSpecificOutput
        print(json.dumps({"decision": "approve", "reason": "No active enhancement to preserve"}))
        sys.exit(0)

    with open(ACTIVE_ENHANCEMENT, encoding="utf-8") as f:
        er = json.load(f)
    lines = ["Prompt Clarification (preserved from prior turn)"]
    if er.get("clarified_intent"):
        lines.append(f"• Intent: {er['clarified_intent']}")
    if er.get("missing_details"):
        lines.append(f"• Clarified: {', '.join(er['missing_details'])}")
    if er.get("safety_flags"):
        lines.append(f"• Flags: {', '.join(er['safety_flags'])}")
    if er.get("estimated_tokens"):
        lines.append(f"• Tokens: ~{er['estimated_tokens']}")

    # PreCompact schema — NOT hookSpecificOutput (PreCompact is not UserPromptSubmit)
    output = {
        "decision": "approve",
        "reason": "Enhancement state preserved for next session",
        "additionalContext": "\n".join(lines),
    }
    print(json.dumps(output))


if __name__ == "__main__":
    main()