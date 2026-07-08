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
    """Point the hook's get_state_path() at tmp_path, not the real state dir.

    get_state_path() reads CSF_STATE_DIR first and falls back to a hardcoded
    P:/.claude/state — chdir alone does NOT redirect it. Without this setenv,
    a globally-set CSF_STATE_DIR leaks through and the subprocess reads/
    writes the real state dir instead of this fixture's tmp_path.
    """
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("CSF_STATE_DIR", str(tmp_path / ".claude" / "state"))
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


def test_classify_autoswitch_preserves_tier_labeling(tmp_state_dir, fake_home):
    """Classify a short code-flavored prompt and assert the recommendation
    uses the dated model string (Phase 1: code → local-coding → ornith)."""
    state_dir = (
        tmp_state_dir / ".claude" / "state" / "model-router" / "term1" / "sess1"
    )
    state_dir.joinpath("config.json").write_text(
        json.dumps(
            {
                "config": {
                    "action": "autoswitch",
                },
                "current_model": "claude-opus-4-8",
                "current_tier": "opus",
            }
        ),
        encoding="utf-8",
    )

    result = _run_hook(
        {
            "prompt": "rename the function foo to bar",
            "terminal_id": "term1",
            "session_id": "sess1",
        }
    )

    assert result.returncode == 0

    rec_path = state_dir / "recommendation.json"
    assert rec_path.exists(), "classification should write a recommendation"
    rec = json.loads(rec_path.read_text(encoding="utf-8"))
    # Phase 1: "rename the function foo to bar" has code-marker ("function") →
    # code + under 64k tokens → local-coding → ornith
    assert rec["recommended_tier"] == "local"
    assert rec["recommended_model"] == "claude-local-ornith"
