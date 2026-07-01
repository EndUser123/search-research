"""Tests for the model-router prompt classification hook."""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys

import pytest

HOOK_PATH = pathlib.Path(
    "P:/packages/.claude-marketplace/plugins/cc-model-router"
    "/hooks/userpromptsubmit/model_router_classify.py"
)


@pytest.fixture
def tmp_state_dir(tmp_path, monkeypatch):
    """Point CWD at tmp_path so the hook's get_state_path() resolves there."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".claude" / "state" / "model-router" / "term1" / "sess1").mkdir(
        parents=True
    )
    return tmp_path


@pytest.fixture
def fake_home(tmp_path, monkeypatch):
    """Point Path.home()/USERPROFILE at tmp_path so hook-local logging stays isolated."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    return tmp_path


def _run_hook(stdin_json: dict) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(HOOK_PATH)],
        input=json.dumps(stdin_json),
        capture_output=True,
        text=True,
        timeout=10,
    )


def test_classify_autoswitch_uses_versioned_haiku_alias(tmp_state_dir, fake_home):
    """Haiku autoswitch should preserve the dated model string Claude Code emits."""
    state_dir = (
        tmp_state_dir / ".claude" / "state" / "model-router" / "term1" / "sess1"
    )
    state_dir.joinpath("config.json").write_text(
        json.dumps(
            {
                "config": {
                    "action": "autoswitch",
                },
                "current_model": "claude-sonnet-4-6",
                "current_tier": "sonnet",
            }
        ),
        encoding="utf-8",
    )

    result = _run_hook(
        {
            "prompt": "rename foo to bar",
            "terminal_id": "term1",
            "session_id": "sess1",
        }
    )

    assert result.returncode == 0

    rec_path = state_dir / "recommendation.json"
    assert rec_path.exists(), "classification should write a recommendation"
    rec = json.loads(rec_path.read_text(encoding="utf-8"))
    assert rec["recommended_tier"] == "haiku"
    assert rec["recommended_model"] == "claude-haiku-4-5-20251001"
