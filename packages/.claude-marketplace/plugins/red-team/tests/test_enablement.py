"""Integration test: red-team is enabled in ~/.claude/settings.json.

Regression for the 5f52d82 enablement gap (marketplace registration != enablement).
Reads the real settings.json — no mocking.
"""

import json
from pathlib import Path


def test_red_team_enabled():
    settings = json.loads((Path.home() / ".claude" / "settings.json").read_text(encoding="utf-8"))
    enabled = settings.get("enabledPlugins", {})
    assert enabled.get("red-team@local") is True, (
        "red-team@local must be true in enabledPlugins — "
        "marketplace registration alone leaves the command as 'Unknown'"
    )
