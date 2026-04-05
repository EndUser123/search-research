#!/usr/bin/env python3
"""Runtime verifier for active hook command wiring.

Checks that hooks configured in P:/.claude/settings.json have non-empty commands
and that python-script targets referenced by those commands exist.
"""

from __future__ import annotations

import json
from pathlib import Path

SETTINGS_PATH = Path("P:/.claude/settings.json")
HOOK_EVENTS = ("UserPromptSubmit", "PreToolUse", "PostToolUse", "Stop", "SessionStart")


def _extract_python_target(command: str) -> Path | None:
    parts = command.strip().split()
    if not parts:
        return None
    # Expected pattern:
    # python P:/.claude/hooks/__lib/hook_runner.py P:/.claude/hooks/<Hook>.py ...
    if len(parts) >= 3 and parts[0].lower().endswith("python"):
        # If hook_runner is used, actual target is 3rd token.
        if parts[1].replace("\\", "/").endswith("/hook_runner.py"):
            return Path(parts[2])
        return Path(parts[1])
    return None


def main() -> int:
    if not SETTINGS_PATH.exists():
        print(json.dumps({"ok": False, "error": f"Missing settings file: {SETTINGS_PATH}"}))
        return 1

    data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    hooks = data.get("hooks", {})

    problems: list[dict] = []
    checked: list[dict] = []

    for event in HOOK_EVENTS:
        event_configs = hooks.get(event, [])
        if not event_configs:
            problems.append({"event": event, "issue": "missing_event"})
            continue

        for config in event_configs:
            for hook in config.get("hooks", []):
                if hook.get("type") != "command":
                    continue
                command = str(hook.get("command", "")).strip()
                if not command:
                    problems.append({"event": event, "issue": "empty_command"})
                    continue
                target = _extract_python_target(command)
                target_exists = True
                if target is not None:
                    target_exists = target.exists()
                    if not target_exists:
                        problems.append(
                            {"event": event, "issue": "missing_target", "target": str(target)}
                        )
                checked.append(
                    {"event": event, "command": command, "target": str(target) if target else None}
                )

    ok = len(problems) == 0
    print(json.dumps({"ok": ok, "checked_count": len(checked), "problems": problems}, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

