#!/usr/bin/env python3
"""SessionStart_reminder_recovery — DEPRECATED stub.

MEMORY.md corrections are now captured at compaction time by the snapshot plugin
(PreCompact_snapshot_capture.py) and stored in the handoff envelope as
`recent_corrections`. The corrections are available in the handoff for display
but are not currently re-injected into the restore message (this is a future
enhancement opportunity).

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
                    "⚠️ DEPRECATED: SessionStart_reminder_recovery.py is retired.\n"
                    "MEMORY.md corrections are captured by the snapshot plugin\n"
                    "at compaction time and stored in the handoff envelope.\n"
                    f"Terminal: {terminal_id}\n"
                    f"Session: {session_id}"
                ),
            }
        ),
        file=sys.stdout,
    )


if __name__ == "__main__":
    main()