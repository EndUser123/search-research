#!/usr/bin/env python3
"""
SessionStart Hook - Contract System Health Check (event-first model)

Lightweight anomaly detector for session-start health surfacing.
Reads recent events from JSONL telemetry and returns compact alerts.

No external dependencies. Fails open on any error.
Healthy = silent. Unhealthy = compact alert block.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent


def main() -> int:
    try:
        sys.path.insert(0, str(HOOKS_DIR / "__lib"))
        from contract_health import get_health_summary

        summary = get_health_summary()
        silent = summary.format_silent()

        if silent is None:
            # Healthy: silent — no output
            return 0

        # Unhealthy: print compact alert block via SessionStart protocol
        print(
            json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "SessionStart",
                        "additionalContext": silent,
                    }
                }
            )
        )
        return 0

    except Exception:
        # Fail open — any error means we don't know, so silent
        return 0


if __name__ == "__main__":
    sys.exit(main())