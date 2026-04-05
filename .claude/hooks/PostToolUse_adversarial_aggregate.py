#!/usr/bin/env python3
"""PostToolUse hook for adversarial aggregation - delegates to subprocess."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent


def aggregate_subagent_results(tool_name: str, tool_input: dict, tool_result: dict) -> dict:
    """Delegate aggregation work to subprocess."""

    if tool_name != "Task":
        return {}

    # Run aggregator script (subprocess, no context bloat)
    script = HOOKS_DIR / "adversarial_aggregator.py"
    if not script.exists():
        return {}

    try:
        result = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True,
            text=True,
            timeout=30
        )
        # Script prints summary to stdout, pass it through
        if result.stdout:
            print(result.stdout.strip())
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        print(f"[PostToolUse] Adversarial aggregation error: {e}")

    return {}


if __name__ == "__main__":
    input_data = json.loads(sys.stdin.read())
    result = aggregate_subagent_results(
        input_data.get("tool_name", ""),
        input_data.get("tool_input", {}),
        input_data.get("tool_result", {})
    )
    print(json.dumps(result))
