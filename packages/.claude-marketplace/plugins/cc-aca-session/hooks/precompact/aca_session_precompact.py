#!/usr/bin/env python3
"""PreCompact hook — DEPRECATED stub.

All compaction capture is now handled by the snapshot plugin's PreCompact hook.
The snapshot plugin provides:
- Rich V2 handoff envelope with checksums
- Evidence indexing and chain tracking
- MEMORY.md corrections ranked by relevance
- transcript_chain pre-computation

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
                "decision": "approve",
                "additional_context": (
                    "⚠️ DEPRECATED: Local PreCompact.py is retired.\n"
                    "Snapshot plugin handles all compaction capture.\n"
                    f"Terminal: {terminal_id}\n"
                    f"Session: {session_id}"
                ),
            }
        ),
        file=sys.stdout,
    )


if __name__ == "__main__":
    main()