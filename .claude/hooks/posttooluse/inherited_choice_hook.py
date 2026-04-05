#!/usr/bin/env python3
from __future__ import annotations

"""
Inherited Choice Validator - In-process adapter.

Prevents copying versioned patterns from existing code without validation.
PostToolUse side: detects patterns in Read/Grep/Glob output, stores in state.
Absorbed from inherited_choice_validator.py.

Original matcher: ^(Read|Grep|Glob)$
"""

import json
import re
import sys
from pathlib import Path
from typing import Any

from posttooluse.base import PostToolUseHook

_hooks_dir = Path(__file__).resolve().parent.parent
if str(_hooks_dir) not in sys.path:
    sys.path.insert(0, str(_hooks_dir))

STATE_DIR = Path(__file__).resolve().parent.parent / ".state"
STATE_FILE = STATE_DIR / "inherited_choice_patterns.json"
VERSION_RE = re.compile(r"\b(v?\d+\.\d+(?:\.\d+)?)\b|\b(python\s*\d(?:\.\d+)?)\b", re.IGNORECASE)


def _extract_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for key in ("content", "output", "result", "stdout"):
            raw = value.get(key)
            if isinstance(raw, str) and raw.strip():
                return raw
        return str(value)
    return str(value)


class InheritedChoiceHook(PostToolUseHook):
    """Detects versioned patterns in Read/Grep/Glob output for later validation."""

    env_var = "INHERITED_CHOICE_VALIDATOR_ENABLED"
    tool_matcher = {"Read", "Grep", "Glob"}

    def process(self, tool_name: str, tool_input: dict[str, Any], tool_response: dict[str, Any]) -> dict[str, Any]:
        try:
            from inherited_choice_validator import handle_post_tool_use

            event = {
                "tool_name": tool_name,
                "tool_input": tool_input,
                "tool_result": tool_response,
            }
            handle_post_tool_use(event)
            return {"passed": True}
        except ImportError:
            # Fallback mode: detect version-like patterns and persist for next turn.
            text = _extract_text(tool_response)
            matches = [m.group(0) for m in VERSION_RE.finditer(text)]
            if not matches:
                return {"passed": True}

            try:
                STATE_DIR.mkdir(parents=True, exist_ok=True)
                snapshot = {
                    "tool_name": tool_name,
                    "file": tool_input.get("file_path") or tool_input.get("path") or "",
                    "patterns": sorted(set(matches))[:20],
                }
                STATE_FILE.write_text(json.dumps(snapshot), encoding="utf-8")
            except OSError:
                # State persistence is best-effort.
                pass
            return {
                "passed": True,
                "injection": (
                    "INHERITED CHOICE WARNING: Versioned patterns were observed in referenced material. "
                    "Validate compatibility before copying the pattern."
                ),
            }
