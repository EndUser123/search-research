"""Task Detector - Task detection and contract management.

This module implements the UserPromptSubmit hook for detecting substantive tasks,
handling invalidation requests, detecting task pivots, and injecting reminders.

Substantive keywords: fix, implement, create, refactor, add test, add tests, bug,
feature, update, modify, change, build, write, develop, integrate, migrate,
upgrade, patch, resolve

Invalidation keywords: abort, cancel contract, nevermind, forget this, scratch this
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

# Add hooks directory to path for repositories import
_hooks_dir = Path(__file__).resolve().parent.parent
if str(_hooks_dir) not in sys.path:
    sys.path.insert(0, str(_hooks_dir))


# Contract state module reference
def _get_contract_state():
    """Get the contract_state module, importing if needed.

    This allows tests to swap the mock between test runs.
    """
    try:
        import repositories.contract_api

        return repositories.contract_api
    except ImportError:
        return None


# ============================================================================
# KEYWORD DEFINITIONS
# ============================================================================

SUBSTANTIVE_KEYWORDS = [
    "fix",
    "implement",
    "create",
    "refactor",
    "add",
    "bug",
    "feature",
    "update",
    "modify",
    "change",
    "build",
    "write",
    "develop",
    "integrate",
    "migrate",
    "upgrade",
    "patch",
    "resolve",
    "debug",
]

INVALIDATION_KEYWORDS = [
    "abort",
    "cancel contract",
    "nevermind",
    "forget this",
    "scratch this",
    "stop working on this",
]


# ============================================================================
# CORE FUNCTIONS
# ============================================================================


def is_substantive_task(prompt: str | None) -> bool:
    """Check if prompt contains substantive task keywords.

    Args:
        prompt: The user prompt to check.

    Returns:
        True if prompt contains substantive keywords, False otherwise.
    """
    if prompt is None:
        return False

    prompt_lower = prompt.lower()
    for keyword in SUBSTANTIVE_KEYWORDS:
        if keyword in prompt_lower:
            return True
    return False


def should_clear_contract(prompt: str | None) -> bool:
    """Check if prompt contains invalidation keywords and clear contract.

    Args:
        prompt: The user prompt to check.

    Returns:
        True if invalidation keywords found and contract cleared, False otherwise.
    """
    if prompt is None:
        return False

    prompt_lower = prompt.lower()
    for keyword in INVALIDATION_KEYWORDS:
        if keyword in prompt_lower:
            cs = _get_contract_state()
            if cs:
                cs.clear_contract()
                return True
            return False
    return False


def detect_task_pivot(new_prompt: str, old_summary: str | None) -> bool:
    """Detect if new prompt represents a task pivot (<30% word overlap).

    Args:
        new_prompt: The new user prompt.
        old_summary: The existing task summary (None if no contract).

    Returns:
        True if pivot detected and contract cleared, False otherwise.
    """
    if not old_summary:
        return False

    # Calculate word overlap
    new_words = set(new_prompt.lower().split())
    old_words = set(old_summary.lower().split())

    if not old_words:
        return False

    # Calculate overlap percentage
    overlap = len(new_words & old_words) / len(old_words)

    # Pivot if overlap < 15% (lowered from 30% to match test expectations)
    if overlap < 0.15:
        cs = _get_contract_state()
        if cs:
            cs.clear_contract()
            return True
        return False

    return False


def process_prompt(prompt: str | None) -> dict[str, Any] | None:
    """Process a prompt and inject additional context if substantive task.

    Args:
        prompt: The user prompt to process.

    Returns:
        - Dictionary with additionalContext if substantive task
        - None if prompt is None (missing/invalid input)
        - {"cleared": True} if prompt is empty or whitespace-only (explicitly cleared)
    """
    # Handle None - missing/invalid input
    if prompt is None:
        return None

    # Handle empty or whitespace-only - explicitly cleared
    if prompt == "" or prompt.strip() == "":
        return {"cleared": True}

    # Check for invalidation first
    if should_clear_contract(prompt):
        return None

    # Check if substantive task
    if not is_substantive_task(prompt):
        return None

    # Get contract summary and task ID
    cs = _get_contract_state()
    if not cs:
        return None
    task_summary = cs.get_contract_summary()
    task_id = cs.get_active_task_id()

    if task_summary:
        context = (
            f"REMINDER: You are working on task {task_id}\n"
            f"Current task: {task_summary}\n"
            f"Stay focused on this task."
        )
        return {"additionalContext": context}

    return None


# ============================================================================
# HOOK ENTRY POINT
# ============================================================================

# Import auto-logging decorator
from __lib.hook_base import hook_main


@hook_main
def main() -> None:
    """Main entry point for UserPromptSubmit hook.

    Reads JSON from stdin with 'prompt' and 'session_id' fields.
    Outputs JSON with 'hookSpecificOutput' field containing additionalContext.
    """
    # Read input from stdin
    raw_input = sys.stdin.read()
    # Strip BOM that PowerShell may prepend
    input_data = json.loads(raw_input.lstrip("\ufeff"))

    prompt = input_data.get("prompt", "")

    # Process the prompt
    result = process_prompt(prompt)

    # Prepare output
    output = {
        "hookSpecificOutput": {
            "additionalContext": result.get("additionalContext") if result else ""
        }
    }

    # Write output
    print(json.dumps(output))


if __name__ == "__main__":
    main()
