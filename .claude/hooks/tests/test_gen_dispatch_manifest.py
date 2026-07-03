"""Tests for gen_dispatch_manifest.py — synthetic fixtures only."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from gen_dispatch_manifest import (
    extract_hooks_from_settings,
    extract_from_plugin_router,
    build_manifest,
    is_live,
)


class TestExtractHooksFromSettings:
    """Test extraction from a synthetic settings.json."""

    def test_basic_extraction(self, tmp_path: Path):
        settings = tmp_path / "settings.json"
        settings.write_text(json.dumps({
            "hooks": {
                "PreToolUse": [
                    {"hooks": [{"type": "command", "command": "python hook.py"}]}
                ],
                "Stop": [
                    {"hooks": [{"type": "command", "command": "python stop.py"}]}
                ],
            }
        }))
        result = extract_hooks_from_settings(settings)
        assert "PreToolUse" in result
        assert "Stop" in result
        assert result["PreToolUse"] == ["python hook.py"]
        assert result["Stop"] == ["python stop.py"]

    def test_empty_hooks(self, tmp_path: Path):
        settings = tmp_path / "settings.json"
        settings.write_text(json.dumps({"hooks": {}}))
        result = extract_hooks_from_settings(settings)
        assert result == {}

    def test_missing_file(self, tmp_path: Path):
        result = extract_hooks_from_settings(tmp_path / "nonexistent.json")
        assert result == {}

    def test_multiple_hooks_same_event(self, tmp_path: Path):
        settings = tmp_path / "settings.json"
        settings.write_text(json.dumps({
            "hooks": {
                "PreToolUse": [
                    {"hooks": [
                        {"type": "command", "command": "cmd_a"},
                        {"type": "command", "command": "cmd_b"},
                    ]}
                ]
            }
        }))
        result = extract_hooks_from_settings(settings)
        assert result["PreToolUse"] == ["cmd_a", "cmd_b"]


class TestExtractFromPluginRouter:
    """Test extraction from a synthetic router.py."""

    def test_extracts_dispatch(self, tmp_path: Path):
        router = tmp_path / "__lib" / "router.py"
        router.parent.mkdir(parents=True)
        router.write_text('''
DISPATCH = {
    "Stop": ["hook_a", "hook_b"],
    "PreToolUse": ["hook_c"],
}
''')
        dispatch, err = extract_from_plugin_router(router)
        assert err is None
        assert "Stop" in dispatch
        assert "hook_a" in dispatch["Stop"]
        assert "hook_c" in dispatch["PreToolUse"]

    def test_syntax_error_recorded(self, tmp_path: Path):
        router = tmp_path / "__lib" / "router.py"
        router.parent.mkdir(parents=True)
        router.write_text("this is not python {{{{")
        dispatch, err = extract_from_plugin_router(router)
        assert dispatch == {}
        assert err is not None
        assert "SyntaxError" in err


class TestIsLive:
    """Test liveness check against a manifest dict."""

    def test_live_match(self):
        manifest = {
            "events": {
                "Stop": [
                    {"target": "python P:/.claude/hooks/Stop.py", "scope": "project"},
                ]
            }
        }
        assert is_live(manifest, "Stop.py") is True

    def test_not_live(self):
        manifest = {
            "events": {
                "Stop": [
                    {"target": "python P:/.claude/hooks/Other.py", "scope": "project"},
                ]
            }
        }
        assert is_live(manifest, "Stop.py") is False

    def test_empty_manifest(self):
        manifest = {"events": {}}
        assert is_live(manifest, "anything.py") is False


class TestBuildManifest:
    """Test full build with synthetic settings and empty plugin dir."""

    def test_build_with_synthetic_settings(self, tmp_path: Path, monkeypatch):
        settings = tmp_path / "settings.json"
        settings.write_text(json.dumps({
            "hooks": {
                "Stop": [{"hooks": [{"type": "command", "command": "python stop.py"}]}]
            }
        }))
        import gen_dispatch_manifest as mod
        monkeypatch.setattr(mod, "PROJECT_SETTINGS", settings)
        monkeypatch.setattr(mod, "USER_SETTINGS", tmp_path / "empty.json")
        monkeypatch.setattr(mod, "PLUGINS_DIR", tmp_path / "no_plugins")
        manifest = build_manifest()
        assert "generated_at" in manifest
        assert "inputs_hash" in manifest
        assert "events" in manifest
        assert any(
            e["target"] == "python stop.py"
            for e in manifest["events"].get("Stop", [])
        )
