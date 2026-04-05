#!/usr/bin/env python3
"""Regression tests for Stop router reminder-only assistant messages."""

from __future__ import annotations

import json
import sys
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
HOOKS_LIB_DIR = HOOKS_DIR / "__lib"
for path in (HOOKS_DIR, HOOKS_LIB_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from Stop_router import route_stop  # noqa: E402


def test_route_stop_skips_system_reminder_only_assistant_message(tmp_path):
    transcript_path = tmp_path / "system_reminder_only.jsonl"
    with transcript_path.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps({"role": "user", "content": "Run /pre-mortem"}) + "\n")
        fh.write(json.dumps({"role": "assistant", "content": "Final report already delivered."}) + "\n")
        fh.write(
            json.dumps(
                {
                    "role": "assistant",
                    "content": "<system-reminder>Reminder after completion</system-reminder>",
                }
            )
            + "\n"
        )

    result = route_stop(
        {
            "hook_event_name": "Stop",
            "transcript_path": str(transcript_path),
            "prompt": "Run /pre-mortem",
        }
    )

    assert result == {}
