"""
SessionStart_commitment_tracker.py - Inject uncompleted commitments on post-compaction resume.

At session start (post-compaction resume only):
1. Checks if checkpoint file exists (compaction resume detection)
2. If checkpoint exists, loads commitments via load_checkpoint()
3. Formats commitments for additionalContext injection
4. Outputs JSON with hookSpecificOutput.additionalContext

Compaction survival pattern: PreCompact saves checkpoint -> SessionStart reads it on resume.

Feature-gated by PROACTIVE_COMMITMENT_TRACKER_ENABLED.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Add __lib to path for commitment_tracker import
_HOOKS_DIR = Path(__file__).resolve().parent
_HOOKS_LIB_DIR = _HOOKS_DIR / "__lib"
if str(_HOOKS_LIB_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_LIB_DIR))

from commitment_tracker import CommitmentTracker

# Feature flag check
_ENABLED = os.environ.get("PROACTIVE_COMMITMENT_TRACKER_ENABLED", "").lower() in (
    "1",
    "true",
    "yes",
)


def main() -> None:
    """Main entry point for SessionStart router."""
    if not _ENABLED:
        sys.exit(0)

    raw_input = sys.stdin.read().strip()
    if not raw_input:
        sys.exit(0)

    try:
        raw_input = raw_input.lstrip("\ufeff")
        data = json.loads(raw_input)
    except json.JSONDecodeError:
        sys.exit(0)

    try:
        terminal_id = _extract_terminal_id(data)
        if not terminal_id:
            sys.exit(0)

        # Check if this is a compaction resume by checking for checkpoint
        tracker = CommitmentTracker()
        commitments = tracker.load_checkpoint(terminal_id)

        if not commitments:
            sys.exit(0)

        # Format commitments for additionalContext injection
        context = _format_commitments(commitments)
        output = {"hookSpecificOutput": {"additionalContext": context}}
        print(json.dumps(output))

    except Exception:
        # Fail silently - SessionStart errors should not block startup
        pass

    sys.exit(0)


def _format_commitments(commitments: list) -> str:
    """Format commitments as human-readable context string."""
    lines = ["## Uncompleted Commitments from Previous Session\n"]
    for i, c in enumerate(commitments, 1):
        lines.append(f"{i}. {c.content}")
    return "\n".join(lines)


def _extract_terminal_id(data: dict) -> str:
    """Extract terminal_id from hook data."""
    terminal = data.get("terminal_id", "")
    if terminal:
        return str(terminal)

    session = data.get("session", {})
    if isinstance(session, dict):
        terminal = session.get("terminal_id", "")
        if terminal:
            return str(terminal)

    terminal = os.environ.get("CLAUDE_TERMINAL_ID", "")
    if terminal:
        return terminal

    return ""


if __name__ == "__main__":
    main()
