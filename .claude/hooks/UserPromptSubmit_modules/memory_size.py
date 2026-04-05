"""MEMORY.md size enforcement hook.

Checks MEMORY.md line count on every UserPromptSubmit and prevents bloat.
Implements the auto-condense safeguard from the memory system pre-mortem.

Configuration:
- MEMORY_SIZE_ENABLED: Enable/disable hook (default: true)
- MEMORY_WARN_LINES: Warning threshold (default: 180)
- MEMORY_BLOCK_LINES: Blocking threshold (default: 195)
- MEMORY_MAX_LINES: Absolute limit (default: 200)
"""

from __future__ import annotations

import os
from pathlib import Path

from .base import HookContext, HookResult
from .registry import register_hook

# Configuration
MEMORY_MD = Path("C:/Users/brsth/.claude/projects/P--/memory/MEMORY.md")
MAX_LINES = int(os.environ.get("MEMORY_MAX_LINES", "200"))
WARN_LINES = int(os.environ.get("MEMORY_WARN_LINES", "180"))
BLOCK_LINES = int(os.environ.get("MEMORY_BLOCK_LINES", "195"))
ENABLED = os.environ.get("MEMORY_SIZE_ENABLED", "true").lower() in ("1", "true", "yes")


def check_memory_size() -> tuple[int, str | None]:
    """Check MEMORY.md line count and return status.

    Returns:
        Tuple of (line_count, warning_message or block_message)
    """
    if not ENABLED:
        return 0, None

    if not MEMORY_MD.exists():
        return 0, None

    try:
        content = MEMORY_MD.read_text(encoding="utf-8")
        line_count = len(content.splitlines())

        if line_count > BLOCK_LINES:
            message = (
                f"⚠️ **MEMORY.md SIZE LIMIT EXCEEDED**\n\n"
                f"MEMORY.md has {line_count} lines (limit: {MAX_LINES}).\n\n"
                f"Cannot proceed. Please condense MEMORY.md by moving verbose sections to topic files.\n\n"
                f"See `discovery_patterns.md`, `learning_patterns.md`, or "
                f"`workflow_clarification.md` for examples of content that should be in topic files."
            )
            return line_count, message

        if line_count > WARN_LINES:
            message = (
                f"⚠️ **MEMORY.md approaching size limit**\n\n"
                f"MEMORY.md has {line_count} lines (limit: {MAX_LINES}). "
                f"Consider condensing soon to avoid hitting the {BLOCK_LINES}-line block threshold."
            )
            return line_count, message

        return line_count, None

    except Exception:
        # Fail open - never block due to read errors
        return 0, None


@register_hook("memory_size_check", priority=2.0)
def memory_size_hook(context: HookContext) -> HookResult:
    """Check MEMORY.md size and warn/block if needed.

    Runs on every UserPromptSubmit to prevent memory system bloat.
    Priority 2.0 (early) to catch issues before context processing.
    """
    line_count, message = check_memory_size()

    if message:
        # Check if this is a block (over BLOCK_LINES)
        if line_count > BLOCK_LINES:
            # Block the prompt - user must fix MEMORY.md first
            return HookResult(
                context={
                    "additionalContext": message,
                    "replacePrompt": None,  # Don't replace, just block
                },
                tokens=len(message),
            )

        # Warning only - inject message but allow prompt
        return HookResult(context=message, tokens=len(message))

    return HookResult.empty()
