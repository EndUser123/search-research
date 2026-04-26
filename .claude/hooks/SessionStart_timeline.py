#!/usr/bin/env python3
"""
SessionStart Timeline Hook
==========================

Shows last checkpoint reference on session start.

Timeline summary disabled — CheckpointTimeline module doesn't exist.
Last checkpoint lookup retained (reads from ~/.claude/checkpoints/).
"""
from __future__ import annotations

# Import auto-logging decorator
from __lib.hook_base import hook_main

import json
import sys
from pathlib import Path


def get_last_checkpoint() -> str | None:
    """Get last checkpoint reference."""
    try:
        checkpoint_dir = Path.home() / ".claude" / "checkpoints"
        if not checkpoint_dir.exists():
            return None

        checkpoints = sorted(checkpoint_dir.glob("ckpt_*.json"), reverse=True)
        if not checkpoints:
            return None

        latest = checkpoints[0]
        with open(latest) as f:
            data = json.load(f)

        checkpoint_id = data.get("checkpoint_id", latest.stem)
        created_at = data.get("created_at", "")[:16]
        citation_id = data.get("citation_id", "")

        lines = [f"Last checkpoint: {checkpoint_id}"]
        lines.append(f"   Created: {created_at}")
        if citation_id:
            lines.append(f"   Citation: {citation_id}")

        return "\n".join(lines)

    except Exception:
        return None


@hook_main
def main():
    """Hook entry point."""
    result = {
        "hookSpecificOutput": "",
        "additionalContext": "",
    }

    # Get last checkpoint
    checkpoint_info = get_last_checkpoint()

    if checkpoint_info:
        result["additionalContext"] = checkpoint_info
        result["hookSpecificOutput"] = checkpoint_info.split("\n")[0]

    # Return JSON
    import json
    print(json.dumps(result))


if __name__ == "__main__":
    main()
