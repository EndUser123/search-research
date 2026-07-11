"""
Repository structure contract tests.

Validates that the plugin layout conforms to the expected conventions:
- Hook scripts are in hooks/ using plugin naming convention
- schemas.py and config/ exist at the expected locations
- hooks.json is valid and populated
- plugin.json is valid and populated
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


PLUGIN_ROOT = Path(__file__).parent.parent


class TestRepoStructure:
    def test_userpromprsubmit_hook_exists(self):
        assert (PLUGIN_ROOT / "hooks" / "prompt-enhancer_UserPromptSubmit.py").is_file()


    def test_hooks_json_empty_per_router_invariant(self):
        """Dispatch is via __lib/router.py registered in settings.json.

        Router-XOR-hooks.json invariant (packages/CLAUDE.md): a plugin with a
        router MUST keep hooks.json as {"hooks": {}} — populating both
        double-fires every hook. The old assertion here encoded the pre-router
        dispatch model and was permanently red.
        """
        hooks_json = PLUGIN_ROOT / "hooks" / "hooks.json"
        assert hooks_json.is_file()
        data = json.loads(hooks_json.read_text(encoding="utf-8"))
        assert data == {"hooks": {}}, (
            f"hooks.json must stay empty (router dispatch), got: {data}"
        )
        assert (PLUGIN_ROOT / "__lib" / "router.py").is_file()

    def test_schemas_exists(self):
        assert (PLUGIN_ROOT / "schemas.py").is_file()

    def test_bypass_prefixes_config_valid_json(self):
        config_path = PLUGIN_ROOT / "config" / "bypass_prefixes.json"
        assert config_path.is_file()
        data = json.loads(config_path.read_text(encoding="utf-8"))
        assert isinstance(data, list), "bypass_prefixes.json should be a list"
        assert len(data) > 0, "bypass_prefixes.json should not be empty"

    def test_plugin_json_valid(self):
        plugin_json = PLUGIN_ROOT / ".claude-plugin" / "plugin.json"
        assert plugin_json.is_file()
        data = json.loads(plugin_json.read_text(encoding="utf-8"))
        assert "name" in data, "plugin.json must have a 'name' field"
        assert "description" in data, "plugin.json must have a 'description' field"
        assert data["name"] == "prompt-enhancer"