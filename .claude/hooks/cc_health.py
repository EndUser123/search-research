#!/usr/bin/env python3
"""
cc_health — compact epistemic gate health snapshot.

Usage:
    python cc_health.py                 # default 24h window
    python cc_health.py --hours 1        # last hour
    python cc_health.py --session-mode   # show session mode only (no telemetry)
    python cc_health.py --mode-only      # alias for --session-mode

Environment:
    STOP_SESSION_MODE  — controls session mode (normal|audit|debug_gates)
    STOP_TELEMETRY    — must be "1" for telemetry reads (default: off)

Exit codes:
    0 — success (always; no actionable output is not an error)
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_HOOKS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_HOOKS_DIR))

from __lib.stop_gate_telemetry import (
    get_recent_gate_summary,
    get_runtime_claim_summary,
    get_rollout_summary,
    render_compact_health,
    render_mode_status,
)
from __lib.turn_mode import get_session_mode


def _get_session_mode() -> str:
    """Resolve session mode from env + defaults."""
    explicit = os.environ.get("STOP_SESSION_MODE", "").strip().lower()
    if explicit in ("audit", "debug_gates"):
        return explicit
    if explicit == "normal":
        return "normal"
    # --audit-mode / --debug-gates flags are per-prompt, not env-level
    # For startup snapshot, we only check the persistent env
    return "normal"


def main() -> None:
    parser = argparse.ArgumentParser(description="Compact epistemic gate health snapshot")
    parser.add_argument(
        "--hours", type=int, default=24,
        help="Telemetry window in hours (default: 24)"
    )
    parser.add_argument(
        "--mode-only", "-m", action="store_true",
        help="Show session mode only, skip telemetry summary"
    )
    args = parser.parse_args()

    session_mode = _get_session_mode()
    print(render_mode_status(session_mode))

    if args.mode_only:
        return

    telemetry_enabled = os.environ.get("STOP_TELEMETRY", "0") not in {"0", "false", "no", "off"}

    if not telemetry_enabled:
        print("  (telemetry off — enable with STOP_TELEMETRY=1 to see gate summary)")
        return

    gate_summary = get_recent_gate_summary(hours=args.hours)
    claim_summary = get_runtime_claim_summary(hours=args.hours)
    rollout_summary = get_rollout_summary(hours=args.hours)

    health = render_compact_health(
        session_mode=session_mode,
        gate_summary=gate_summary,
        claim_summary=claim_summary,
        rollout_summary=rollout_summary,
        hours=args.hours,
    )
    # Skip the first line (mode) since we already printed it
    lines = health.splitlines()
    for line in lines[1:]:
        print(line)


if __name__ == "__main__":
    main()
