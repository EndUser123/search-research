"""Regression tests for namespaced fact-guard hook entrypoints."""

from __future__ import annotations

import json
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
HOOKS_JSON = PACKAGE_ROOT / "hooks" / "hooks.json"


def test_fact_guard_hooks_use_namespaced_entrypoints() -> None:
    """Verify hooks.json commands reference namespaced entrypoints, not generic names."""
    manifest = json.loads(HOOKS_JSON.read_text(encoding="utf-8"))
    commands = [
        hook["command"]
        for entries in manifest["hooks"].values()
        for match in entries
        for hook in match["hooks"]
    ]

    assert "python \"$CLAUDE_PLUGIN_ROOT/hooks/fact-guard_PreToolUse.py\"" in commands
    assert "python \"$CLAUDE_PLUGIN_ROOT/hooks/fact-guard_PostToolUse.py\"" in commands
    # Verify no generic name references remain
    assert all("PreToolUse.py\"" not in command or "fact-guard_PreToolUse" in command for command in commands)
    assert all("PostToolUse.py\"" not in command or "fact-guard_PostToolUse" in command for command in commands)