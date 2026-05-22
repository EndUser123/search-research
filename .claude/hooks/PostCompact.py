#!/usr/bin/env python3
"""PostCompact hook — DEPRECATED stub.

All compaction state recovery is now handled by the snapshot plugin's
SessionStart_snapshot_restore.py, which provides:
- Checksum-validated handoff envelopes
- MEMORY.md corrections at session start
- transcript_chain tracking across sessions

This local hook is kept as a stub so settings.json registration remains valid
during the transition period.
"""

from __future__ import annotations

import json
import sys


def main() -> None:
    data = json.load(sys.stdin)
    terminal_id = data.get("terminal_id", "unknown")
    session_id = data.get("session_id", "unknown")
    print(
        json.dumps(
            {
                "status": "success",
                "additional_context": (
                    "⚠️ DEPRECATED: Local PostCompact.py is retired.\n"
                    "Snapshot plugin handles all compaction recovery.\n"
                    f"Terminal: {terminal_id}\n"
                    f"Session: {session_id}"
                ),
            }
        ),
        file=sys.stdout,
    )


if __name__ == "__main__":
    main()