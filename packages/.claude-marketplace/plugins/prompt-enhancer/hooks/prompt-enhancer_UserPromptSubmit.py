#!/usr/bin/env python3
"""prompt-enhancer hook module for UserPromptSubmit event.

Reads JSON payload from stdin: {"prompt": "...", "terminalId": "..."}
Runs triage(), dispatches to enhance() if ambiguous/confirm, returns hook response JSON to stdout.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_plugin_root = Path(os.environ.get("CLAUDE_PLUGIN_ROOT", Path(__file__).parent.parent))
sys.path.insert(0, str(_plugin_root))

from detect import triage
from prompt_enhancer import enhance, build_additional_context, DEFAULT_INJECT_THRESHOLD
from context import (
    read_session_context,
    write_session_context,
    extract_subject,
)

TERMINAL_ID = os.environ.get("CLAUDE_TERMINAL_ID", "default")
ARTIFACT_DIR = Path.home() / ".claude" / ".artifacts" / TERMINAL_ID / "prompt-enhancer"
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
ACTIVE_ENHANCEMENT = ARTIFACT_DIR / "active_enhancement.json"


def main() -> None:
    payload = json.load(sys.stdin)
    prompt = payload.get("prompt", "")
    result = triage(prompt)

    if result["classification"] in ("bypass", "clear", "ambiguous"):
        session_ctx = read_session_context()
        subject_hint = extract_subject(prompt)
        write_session_context(prompt, subject_hint)
    else:
        session_ctx = None
        subject_hint = None

    if result["classification"] in ("bypass", "clear"):
        _clear_active_enhancement()
        output = {}

    elif result["classification"] == "ambiguous":
        er = enhance(prompt, os.getcwd(), ctx=session_ctx)
        _save_active_enhancement(er, payload)
        if er.confidence >= DEFAULT_INJECT_THRESHOLD:
            ctx = build_additional_context(er)
            output = {
                "hookSpecificOutput": {
                    "hookEventName": "UserPromptSubmit",
                    "additionalContext": ctx,
                }
            }
        else:
            output = {}

    elif result["classification"] == "confirm":
        er = enhance(prompt, os.getcwd())
        _save_active_enhancement(er, payload)
        ctx = build_additional_context(er)
        detail = er.missing_details[0] if er.missing_details else "the target"
        if detail.startswith("confirm "):
            confirm_part = detail[7:].lstrip()
            question = f"This action appears destructive or high-impact. Please confirm {confirm_part}."
        else:
            question = f"This action appears destructive or high-impact. Please confirm {detail}."
        output = {
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": ctx,
                "AskUserQuestion": {
                    "question": question,
                    "options": [
                        {"label": "Specify target", "description": "Provide a specific target path or scope"},
                        {"label": "Cancel", "description": "Cancel this action"},
                    ],
                },
            }
        }

    elif result["classification"] == "prohibited":
        _clear_active_enhancement()
        output = {
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "block": True,
                "stopReason": f"prohibited prompt: {result['reason']}",
            }
        }

    else:
        _clear_active_enhancement()
        output = {}

    print(json.dumps(output))


def _save_active_enhancement(er, payload: dict) -> None:
    data = er.model_dump()
    data["session_id"] = payload.get("sessionId", "")
    with open(ACTIVE_ENHANCEMENT, "w", encoding="utf-8") as f:
        json.dump(data, f)


def _clear_active_enhancement() -> None:
    if ACTIVE_ENHANCEMENT.exists():
        ACTIVE_ENHANCEMENT.unlink()


if __name__ == "__main__":
    main()
