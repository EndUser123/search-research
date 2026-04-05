#!/usr/bin/env python3
"""
PreCompact - Lean Router v2.0
=============================

Replaces monolithic PreCompact_handoff_router.py.
Ensures session continuity by capturing handoff and checkpoint state before compaction.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent

# sequence (Priority-ordered)
SEQUENCE = [
    "PreCompact_handoff_capture.py",
    "precompact_imports_patch.py",
    "PreCompact_commitment_tracker.py",
]


def run_task(hook_name: str, input_data: str):
    try:
        hook_path = HOOKS_DIR / hook_name
        if not hook_path.exists():
            return f"{hook_name}: missing file"

        creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        result = subprocess.run(
            [sys.executable, hook_path.as_posix()],
            input=input_data.encode(),
            capture_output=True,
            timeout=10.0,
            creationflags=creation_flags,
        )

        # Capture stdout (hook output JSON) and stderr (logger messages)
        stdout_text = result.stdout.decode(errors="replace").strip()
        stderr_text = result.stderr.decode(errors="replace").strip()

        # Extract message from child hook JSON output
        if stdout_text:
            try:
                # Parse child hook JSON to extract additionalContext
                hook_output = json.loads(stdout_text)
                if isinstance(hook_output, dict) and "additionalContext" in hook_output:
                    # Return plain text message, not embedded JSON
                    return hook_output["additionalContext"]
                else:
                    # Fallback: child hook returned non-dict output or no additionalContext
                    return f"{hook_name}: {stdout_text}"
            except json.JSONDecodeError:
                # Child hook returned non-JSON output (rare fallback)
                return f"{hook_name}: {stdout_text}"

        # On error, include stderr
        if result.returncode != 0:
            return f"{hook_name}: exit={result.returncode} {stderr_text}".strip()

        # No output and success = silent success
        return None
    except Exception as e:
        return f"{hook_name}: exception={type(e).__name__}: {e}"


def main():
    raw_input = sys.stdin.read().strip()
    if not raw_input:
        sys.exit(0)

    try:
        raw_input = raw_input.lstrip("\ufeff")
        data = json.loads(raw_input)
    except json.JSONDecodeError:
        sys.exit(0)

    warnings: list[str] = []
    for task in SEQUENCE:
        warning = run_task(task, json.dumps(data))
        if warning:
            warnings.append(warning)

    # PreCompact has no hookSpecificOutput schema defined
    # Warnings are logged but not output (would fail validation)
    # Child hooks handle their own output/logging

    sys.exit(0)


if __name__ == "__main__":
    main()
