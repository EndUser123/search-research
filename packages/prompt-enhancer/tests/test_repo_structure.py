"""
Repository structure contract tests.

Validates that the plugin layout conforms to the expected conventions:
- Hook scripts are in scripts/hooks/
- schemas.py and config/ exist at the expected locations
- No stale hooks/ directory exists at the plugin root
- plugin.json is valid and populated
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


PLUGIN_ROOT = Path(__file__).parent.parent


class TestRepoStructure:
    def test_hook_script_exists(self):
        assert (PLUGIN_ROOT / "scripts" / "hooks" / "prompt_enhancer_hook.py").is_file()

    def test_precompact_hook_script_exists(self):
        assert (PLUGIN_ROOT / "scripts" / "hooks" / "prompt_enhancer_precompact_hook.py").is_file()

    def test_schemas_exists(self):
        assert (PLUGIN_ROOT / "schemas.py").is_file()

    def test_bypass_prefixes_config_valid_json(self):
        config_path = PLUGIN_ROOT / "config" / "bypass_prefixes.json"
        assert config_path.is_file()
        data = json.loads(config_path.read_text(encoding="utf-8"))
        assert isinstance(data, list), "bypass_prefixes.json should be a list"
        assert len(data) > 0, "bypass_prefixes.json should not be empty"

    def test_no_stale_hooks_directory(self):
        """No hooks/ directory should exist at the plugin root (stale convention)."""
        stale = PLUGIN_ROOT / "hooks"
        assert not stale.exists(), (
            f"Stale hooks/ directory found at {stale}. "
            "Hook scripts should live in scripts/hooks/."
        )

    def test_plugin_json_valid(self):
        plugin_json = PLUGIN_ROOT / ".claude-plugin" / "plugin.json"
        assert plugin_json.is_file()
        data = json.loads(plugin_json.read_text(encoding="utf-8"))
        assert "name" in data, "plugin.json must have a 'name' field"
        assert "description" in data, "plugin.json must have a 'description' field"
        assert data["name"] == "prompt-enhancer"