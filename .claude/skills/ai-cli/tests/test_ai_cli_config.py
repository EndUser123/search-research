"""Tests for ai-cli recipe config persistence."""

from __future__ import annotations

import json

import ai_cli
from ai_cli import _load_ai_cli_config, _save_ai_cli_config


def test_save_writes_structured_config_and_load_round_trips(tmp_path, monkeypatch):
    config_path = tmp_path / "ai-cli-recipe.json"
    monkeypatch.setattr(ai_cli, "_AI_CLI_CONFIG", config_path)

    _save_ai_cli_config(["qwen", "gemini"], ["kimi", "minimax"])

    raw = json.loads(config_path.read_text(encoding="utf-8"))
    assert raw["default"]["clis"] == [{"name": "qwen"}, {"name": "gemini"}]
    assert raw["aux"]["clis"] == [
        {"name": "opencode", "model": "chutes/moonshotai/Kimi-K2.5-TEE"},
        {"name": "opencode", "model": "chutes/MiniMaxAI/MiniMax-M2.1-TEE"},
    ]
    assert raw["opencode_models"] == [
        "chutes/moonshotai/Kimi-K2.5-TEE",
        "chutes/MiniMaxAI/MiniMax-M2.1-TEE",
    ]

    loaded = _load_ai_cli_config()
    assert loaded is not None
    assert loaded["default"]["clis"] == [{"name": "qwen"}, {"name": "gemini"}]
    assert loaded["aux"]["clis"][0]["model"] == "chutes/moonshotai/Kimi-K2.5-TEE"


def test_load_normalizes_legacy_flat_format(tmp_path, monkeypatch):
    config_path = tmp_path / "ai-cli-recipe.json"
    monkeypatch.setattr(ai_cli, "_AI_CLI_CONFIG", config_path)

    config_path.write_text(
        json.dumps({"clis": ["qwen", "opencode:ignored"], "opencode_models": ["kimi"]}),
        encoding="utf-8",
    )

    loaded = _load_ai_cli_config()
    assert loaded is not None
    assert loaded["default"]["clis"] == [{"name": "qwen"}]
    assert loaded["aux"]["clis"] == [
        {"name": "opencode", "model": "chutes/moonshotai/Kimi-K2.5-TEE"}
    ]
