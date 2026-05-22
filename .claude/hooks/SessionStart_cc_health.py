#!/usr/bin/env python3
"""
SessionStart Hook - Epistemic Gate Health Surfacing

Wires cc_health.py helpers into the session startup surface.
Uses STOP_SESSION_MODE / STOP_TELEMETRY env vars.

Silent when NORMAL with no actionable issues.
Surfaces mode line for AUDIT/DEBUG_GATES.
Surfaces attention lines when something is wrong.

Follows SessionStart protocol: print JSON to stdout when there's content.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_HOOKS_DIR = Path(__file__).resolve().parent


def _telemetry_enabled() -> bool:
    """Read STOP_TELEMETRY env var at runtime (not import-time)."""
    return os.environ.get("STOP_TELEMETRY", "0") not in {"0", "false", "no", "off"}


def _get_session_mode() -> str:
    """Resolve session mode from env."""
    explicit = os.environ.get("STOP_SESSION_MODE", "").strip().lower()
    if explicit in ("audit", "debug_gates", "normal"):
        return explicit
    return "normal"


def main() -> int:
    try:
        sys.path.insert(0, str(_HOOKS_DIR / "__lib"))
        from stop_gate_telemetry import (
            get_recent_gate_summary,
            get_runtime_claim_summary,
            get_rollout_summary,
            render_attention_lines,
        )

        session_mode = _get_session_mode()

        # Always surface mode for AUDIT and DEBUG_GATES
        if session_mode == "audit":
            mode_line = "Session Mode: AUDIT  (format-only friction softened on audit-report turns)"
        elif session_mode == "debug_gates":
            mode_line = "Session Mode: DEBUG_GATES  (quality gates suppressed)"
        else:
            mode_line = None  # NORMAL mode — only surface if actionable

        # Gather telemetry summaries when enabled
        gate_summary: dict[str, int] = {}
        claim_summary: dict[str, int] = {"matched": 0, "artifact_missing": 0, "no_match": 0, "other": 0}
        rollout_summary: dict[str, int] = {}

        if _telemetry_enabled():
            gate_summary = get_recent_gate_summary(hours=24, top_n=5)
            claim_summary = get_runtime_claim_summary(hours=24)
            rollout_summary = get_rollout_summary(hours=24)

        attention = render_attention_lines(gate_summary, claim_summary, rollout_summary, session_mode)

        # Build output: mode line + attention lines
        output_lines: list[str] = []
        if mode_line:
            output_lines.append(mode_line)
        output_lines.extend(attention)

        if not output_lines:
            # NORMAL with nothing actionable — silent
            return 0

        print(
            json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "SessionStart",
                        "additionalContext": "\n".join(output_lines),
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