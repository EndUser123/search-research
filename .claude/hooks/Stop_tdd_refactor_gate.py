#!/usr/bin/env python3
"""
Stop_tdd_refactor_gate — REFACTOR phase enforcement with circuit breaker.

Prevents premature completion claims during TDD REFACTORING phase.
Blocks when:
  - TDD phase is REFACTORING
  - Response contains completion language without REFACTOR evidence
  - Tests haven't been re-run after cleanup

Circuit breaker: After MAX_CONSECUTIVE_BLOCKS, safety valve allows through.

Philosophy: Never block without a clear, actionable path forward.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

HOOKS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(HOOKS_DIR))

from tdd_core import TDDPhase, TDDState

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

MAX_CONSECUTIVE_BLOCKS = 5
STATE_DIR = HOOKS_DIR / "state" / "tdd_refactor"

# Completion language patterns that indicate premature stopping
COMPLETION_PATTERNS = [
    r"(?i)\brefactor(?:ing)?\s+(?:complete|done|finished)",
    r"(?i)\btests?\s+(?:all\s+)?pass(?:ing)?\s+(?:now|again|still)",
    r"(?i)\ball\s+done\b",
    r"(?i)\bcode\s+(?:is\s+)?clean\b",
    r"(?i)\brefactor(?:ing)?\s+(?:phase\s+)?complete",
    r"(?i)\bgreen\b.*\brefactor\b",
    r"(?i)✅.*(?:refactor|green|clean)",
]

# Evidence patterns that indicate REFACTOR is actually complete
REFACTOR_COMPLETE_PATTERNS = [
    r"(?i)pytest.*(?:pass|ok)",
    r"(?i)tests?.*(?:pass|ok|green)",
    r"(?i)run.*pytest",
    r"(?i)test.*suite",
    r"(?i)all\s+tests?\s+(?:pass|ok)",
]


def _get_session_id() -> str:
    """Extract session ID from environment or generate fallback."""
    session_obj = os.environ.get("CLAUDE_SESSION_ID", "")
    if session_obj and session_obj.strip():
        return session_obj.strip()
    return "default"


def _get_block_count_path() -> Path:
    """Get path for session-scoped block counter."""
    session_id = _get_session_id()
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    return STATE_DIR / f"block_count_{session_id}.json"


def _load_block_count() -> int:
    """Load consecutive block count for this session."""
    path = _get_block_count_path()
    if path.exists():
        try:
            data = json.loads(path.read_text())
            return data.get("count", 0)
        except (json.JSONDecodeError, OSError):
            pass
    return 0


def _save_block_count(count: int) -> None:
    """Save consecutive block count for this session."""
    path = _get_block_count_path()
    try:
        path.write_text(json.dumps({"count": count, "timestamp": time.time()}))
    except OSError:
        pass


def _check_active_refactor() -> tuple[bool, str | None]:
    """
    Check if any TDD state file indicates REFACTORING phase.

    Returns (is_refactoring, test_file_or_None)
    """
    tdd_state = TDDState()
    state_file = tdd_state.state_file

    if not state_file or not state_file.exists():
        return False, None

    try:
        data = json.loads(state_file.read_text())
        phase_str = data.get("phase", "")
        phase = TDDPhase.from_string(phase_str) if phase_str else TDDPhase.IDLE

        if phase == TDDPhase.REFACTORING:
            return True, tdd_state.test_file
    except (json.JSONDecodeError, OSError):
        pass

    return False, None


def _has_refactor_evidence(response_text: str) -> bool:
    """Check if response contains evidence that refactoring is complete."""
    for pattern in REFACTOR_COMPLETE_PATTERNS:
        if re.search(pattern, response_text):
            return True
    return False


def _has_completion_language(response_text: str) -> bool:
    """Check if response contains premature completion language."""
    for pattern in COMPLETION_PATTERNS:
        if re.search(pattern, response_text):
            return True
    return False


def check_tdd_refactor(data: dict[str, Any]) -> dict[str, Any] | None:
    """
    Main gate function.

    Returns None to allow, or dict with 'decision': 'block' and 'reason'.
    """
    # Check if TDD is in REFACTORING phase
    is_refactoring, test_file = _check_active_refactor()

    if not is_refactoring:
        return None

    # Get response text
    response_text = ""
    if isinstance(data, dict):
        response_text = data.get("response_text", "") or data.get("text", "")
        if isinstance(response_text, dict):
            response_text = response_text.get("content", "") or str(response_text)

    # If no completion language, allow through
    if not _has_completion_language(response_text):
        # Reset block count on non-blocking response
        _save_block_count(0)
        return None

    # Has completion language - check if evidence exists
    has_evidence = _has_refactor_evidence(response_text)

    if has_evidence:
        # Evidence present - allow but track
        _save_block_count(0)
        return None

    # No evidence - this is premature completion
    # Check circuit breaker
    block_count = _load_block_count()
    new_count = block_count + 1
    _save_block_count(new_count)

    if new_count >= MAX_CONSECUTIVE_BLOCKS:
        # Safety valve - allow through after MAX blocks
        _save_block_count(0)
        return None

    # Block with guidance
    test_name = Path(test_file).name if test_file else "the test"
    return {
        "decision": "block",
        "reason": (
            f"TDD REFACTORING phase active ({test_name}).\n\n"
            f"You claimed refactoring is complete but provided no test evidence.\n\n"
            f"Before declaring refactoring done:\n"
            f"1. Run pytest to verify tests still pass after cleanup\n"
            f"2. Show the test output proving green\n"
            f"3. Then claim refactoring is complete\n\n"
            f"Circuit breaker: {new_count}/{MAX_CONSECUTIVE_BLOCKS} blocks\n"
            f"(Safety valve opens after {MAX_CONSECUTIVE_BLOCKS} consecutive blocks)"
        ),
    }


def main() -> None:
    """CLI entry point for standalone testing."""
    import sys

    input_data = json.loads(sys.stdin.read())
    result = check_tdd_refactor(input_data)

    if result is None:
        print(json.dumps({"allow": True}))
    else:
        print(json.dumps({"allow": False, "reason": result.get("reason", "")}))
        sys.exit(1)


if __name__ == "__main__":
    main()
