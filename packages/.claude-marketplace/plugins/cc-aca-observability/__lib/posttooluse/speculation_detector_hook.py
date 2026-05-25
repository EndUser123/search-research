#!/usr/bin/env python3
from __future__ import annotations

"""
Speculation Detector - In-process adapter.

Detects speculation patterns after tool use to inject guidance.
Absorbed from PostToolUse_speculation_detector.py.

Original matcher: ^(Read|Grep|Glob)$
"""

import sys
from pathlib import Path
from typing import Any

from posttooluse.base import PostToolUseHook

_hooks_dir = Path(__file__).resolve().parent.parent
if str(_hooks_dir) not in sys.path:
    sys.path.insert(0, str(_hooks_dir))


SPECULATION_MARKERS = (
    "maybe",
    "probably",
    "likely",
    "appears",
    "seems",
    "might",
    "could be",
)


def _flatten_text(value: Any) -> str:
    """Extract text payloads from tool responses for simple marker checks."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        parts = []
        for key in ("content", "output", "result", "stdout", "stderr", "error"):
            raw = value.get(key)
            if isinstance(raw, str) and raw.strip():
                parts.append(raw)
        if parts:
            return "\n".join(parts)
        return str(value)
    return str(value)


class SpeculationDetectorHook(PostToolUseHook):
    """Detects speculation patterns after tool use."""

    tool_matcher = {"Read", "Grep", "Glob"}

    def process(self, tool_name: str, tool_input: dict[str, Any], tool_response: dict[str, Any]) -> dict[str, Any]:
        try:
            from PostToolUse_speculation_detector import check_tool_context, format_injection

            # Build input_data in the format the detector expects
            input_data = {
                "tool_name": tool_name,
                "tool_input": tool_input,
                "tool_response": tool_response,
            }

            warning = check_tool_context(input_data)
            if warning:
                injection = format_injection(warning)
                return {"passed": True, "injection": injection}
            return {"passed": True}
        except ImportError:
            # Fallback mode: lightweight in-process detector to avoid dead hook.
            text = _flatten_text(tool_response).lower()
            if any(marker in text for marker in SPECULATION_MARKERS):
                return {
                    "passed": True,
                    "injection": (
                        "SPECULATION WARNING: Observed uncertainty markers in recent tool output. "
                        "Do not convert uncertain language into factual claims without direct verification."
                    ),
                }

            if not text.strip():
                return {
                    "passed": True,
                    "injection": (
                        "SPECULATION WARNING: Latest observation tool produced no concrete output. "
                        "Avoid definitive claims until you collect direct evidence."
                    ),
                }
            return {"passed": True}
