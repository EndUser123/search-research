#!/usr/bin/env python3
"""
Wrap all hooks in settings.json with hook_runner.py.

This ensures all hook errors are captured in cc_errors.jsonl
instead of showing generic "hook error" messages in Claude Code.
"""

import json
import re
import shutil
from datetime import datetime
from pathlib import Path

SETTINGS_PATH = Path("P:/.claude/settings.json")
HOOK_RUNNER = "python P:/.claude/hooks/__lib/hook_runner.py"

# Pattern to detect already-wrapped hooks
RUNNER_PATTERN = re.compile(r"hook_runner\.py")

# Pattern to extract hook script path from unwrapped command
# Matches: python [path/to/script.py] or python P:/[path/to/script.py]
PYTHON_SCRIPT_PATTERN = re.compile(r"^python\s+(?:P:/)?(.+\.py)$")


def wrap_command(cmd: str, timeout: int) -> str:
    """Wrap a python command with hook_runner.py."""
    # Skip if already wrapped
    if RUNNER_PATTERN.search(cmd):
        return cmd

    # Skip non-python commands (powershell, etc.)
    if not cmd.startswith("python "):
        return cmd

    # Extract the script path
    match = PYTHON_SCRIPT_PATTERN.match(cmd)
    if not match:
        return cmd

    script_path = match.group(1)

    # Normalize path - ensure it's absolute
    if script_path.startswith(".claude/"):
        script_path = f"P:/{script_path}"
    elif script_path.startswith("P:/"):
        pass  # Already absolute
    elif not script_path.startswith("P:"):
        script_path = f"P:/.claude/hooks/{script_path}"

    # Build wrapped command with timeout
    return f"{HOOK_RUNNER} {script_path} --timeout {timeout}.0"


def main():
    # Backup settings
    backup_path = SETTINGS_PATH.with_suffix(
        f".json.backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    )
    shutil.copy(SETTINGS_PATH, backup_path)
    print(f"Backed up to: {backup_path}")

    # Load settings
    with open(SETTINGS_PATH, encoding="utf-8") as f:
        settings = json.load(f)

    hooks = settings.get("hooks", {})
    wrapped_count = 0
    skipped_count = 0

    # Process all hook types
    for event_type, matchers in hooks.items():
        if not isinstance(matchers, list):
            continue

        for matcher_group in matchers:
            hook_list = matcher_group.get("hooks", [])

            for hook in hook_list:
                if hook.get("type") != "command":
                    continue

                cmd = hook.get("command", "")
                timeout = hook.get("timeout", 5)

                # Skip non-python commands
                if not cmd.startswith("python "):
                    skipped_count += 1
                    continue

                # Skip already wrapped
                if RUNNER_PATTERN.search(cmd):
                    continue

                # Wrap the command
                new_cmd = wrap_command(cmd, timeout)
                if new_cmd != cmd:
                    print(f"Wrapping: {cmd[:60]}...")
                    hook["command"] = new_cmd
                    wrapped_count += 1

    # Save updated settings
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)

    print(
        f"\nDone! Wrapped {wrapped_count} hooks, skipped {skipped_count} non-python commands."
    )
    print(f"Settings saved to: {SETTINGS_PATH}")


if __name__ == "__main__":
    main()
