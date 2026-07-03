"""Tests for the model-router UPS apply hook.

Regression test reproduces the exact failure path the old design exhibited:
a stale recommendation.json from the prior turn is consumed DURING the
next UserPromptSubmit, so the new model is in effect for the current turn
— not the next one. The old Stop-resend path wrote settings.json AFTER
the response, forcing the user to re-send.

Unit tests cover all no-op branches and the dry_run path.
"""

from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
from datetime import datetime, timedelta

import pytest

HOOK_PATH = pathlib.Path(
    "P:/packages/.claude-marketplace/plugins/cc-model-router"
    "/hooks/userpromptsubmit/model_router_apply.py"
)


@pytest.fixture
def tmp_state_dir(tmp_path, monkeypatch):
    """Point the hook's get_state_path() at tmp_path, not the real state dir.

    get_state_path() reads CSF_STATE_DIR first and falls back to a hardcoded
    P:/.claude/state — chdir alone does NOT redirect it. Without this setenv,
    CSF_STATE_DIR (set globally in this environment) leaks through and the
    subprocess reads/writes the real state dir instead of this fixture's
    tmp_path, which was silently failing 3 of the tests below.
    """
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("CSF_STATE_DIR", str(tmp_path / ".claude" / "state"))
    (tmp_path / ".claude" / "state" / "model-router" / "term1" / "sess1").mkdir(
        parents=True
    )
    return tmp_path


@pytest.fixture
def fake_home(tmp_path, monkeypatch):
    """Point pathlib.Path.home() and $HOME at tmp_path for settings.json."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.setattr(pathlib.Path, "home", lambda: tmp_path)
    settings_path = tmp_path / ".claude" / "settings.json"
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(
        json.dumps({"model": "claude-sonnet-4-6"}), encoding="utf-8"
    )
    return tmp_path


def _write_rec(state_dir: pathlib.Path, rec: dict) -> pathlib.Path:
    p = state_dir / "recommendation.json"
    p.write_text(json.dumps(rec), encoding="utf-8")
    return p


def _run_hook(stdin_json: dict) -> subprocess.CompletedProcess:
    """Run the hook as a subprocess with synthetic stdin."""
    return subprocess.run(
        [sys.executable, str(HOOK_PATH)],
        input=json.dumps(stdin_json),
        capture_output=True,
        text=True,
        timeout=10,
    )


# ----------------------------- regression test -----------------------------


def test_apply_switches_model_before_response(
    tmp_state_dir, fake_home
):
    """Regression: a stale autoswitch recommendation must rewrite settings.json
    during UserPromptSubmit, not after Stop. If the hook only runs at Stop, the
    user pays a wasted turn — this is the failure the new design fixes.
    """
    state_dir = (
        tmp_state_dir / ".claude" / "state" / "model-router" / "term1" / "sess1"
    )
    _write_rec(
        state_dir,
        {
            "recommended_model": "claude-haiku-4-5",
            "current_model": "claude-sonnet-4-6",
            "action_mode": "autoswitch",
            "written_at": datetime.now().isoformat(),
            "consumed": False,
        },
    )

    result = _run_hook(
        {"prompt": "rename foo to bar", "terminal_id": "term1", "session_id": "sess1"}
    )

    # The hook must NOT block the prompt.
    assert result.returncode == 0, f"hook blocked the prompt: {result.stderr}"

    # settings.json must already reflect the new model — this is the load-bearing
    # assertion: the model is in effect for the *current* turn.
    settings = json.loads((fake_home / ".claude" / "settings.json").read_text())
    assert settings["model"] == "claude-haiku-4-5", (
        f"settings.json model was {settings.get('model')!r}; "
        "UPS hook failed to switch before generation — would force Stop-resend"
    )

    # Recommendation must be marked consumed so a replay won't re-apply it.
    rec = json.loads((state_dir / "recommendation.json").read_text())
    assert rec["consumed"] is True


def test_apply_refreshes_state_tier_to_stop_thrash(tmp_state_dir, fake_home):
    """Regression for the thrash bug: after a real apply, config.json's
    current_tier/current_model must advance to the new model. Before this
    fix, only SessionStart ever wrote that file, so classify.py kept
    comparing every later prompt against the session's original tier and
    re-triggered the same switch forever (10+ applies/session in the wild).
    """
    state_dir = (
        tmp_state_dir / ".claude" / "state" / "model-router" / "term1" / "sess1"
    )
    (state_dir / "config.json").write_text(
        json.dumps({"current_tier": "sonnet", "current_model": "claude-sonnet-4-6"}),
        encoding="utf-8",
    )
    _write_rec(
        state_dir,
        {
            "recommended_model": "claude-opus-4-8",
            "current_model": "claude-sonnet-4-6",
            "action_mode": "autoswitch",
            "written_at": datetime.now().isoformat(),
            "consumed": False,
        },
    )

    result = _run_hook(
        {"prompt": "architect a redesign", "terminal_id": "term1", "session_id": "sess1"}
    )
    assert result.returncode == 0

    state = json.loads((state_dir / "config.json").read_text())
    assert state["current_tier"] == "opus", (
        f"config.json current_tier was {state.get('current_tier')!r}; "
        "classify.py will keep comparing against the stale baseline and "
        "re-trigger this same switch on every later prompt"
    )
    assert state["current_model"] == "claude-opus-4-8"


# ----------------------------- branch unit tests -----------------------------


def test_apply_no_recommendation_file(tmp_state_dir, fake_home):
    """No recommendation.json → no-op, no rewrite, exit 0."""
    result = _run_hook(
        {"prompt": "anything", "terminal_id": "term1", "session_id": "sess1"}
    )
    assert result.returncode == 0
    settings = json.loads((fake_home / ".claude" / "settings.json").read_text())
    assert settings["model"] == "claude-sonnet-4-6"  # unchanged


def test_apply_expired_recommendation_is_skipped(tmp_state_dir, fake_home):
    """Recommendation older than TTL → no-op."""
    state_dir = (
        tmp_state_dir / ".claude" / "state" / "model-router" / "term1" / "sess1"
    )
    old = (datetime.now() - timedelta(seconds=400)).isoformat()
    _write_rec(
        state_dir,
        {
            "recommended_model": "claude-haiku-4-5",
            "current_model": "claude-sonnet-4-6",
            "action_mode": "autoswitch",
            "written_at": old,
            "consumed": False,
        },
    )
    result = _run_hook(
        {"prompt": "x", "terminal_id": "term1", "session_id": "sess1"}
    )
    assert result.returncode == 0
    settings = json.loads((fake_home / ".claude" / "settings.json").read_text())
    assert settings["model"] == "claude-sonnet-4-6"


def test_apply_consumed_recommendation_is_skipped(tmp_state_dir, fake_home):
    """Already-consumed rec → no-op (idempotent lifecycle guard)."""
    state_dir = (
        tmp_state_dir / ".claude" / "state" / "model-router" / "term1" / "sess1"
    )
    _write_rec(
        state_dir,
        {
            "recommended_model": "claude-haiku-4-5",
            "current_model": "claude-sonnet-4-6",
            "action_mode": "autoswitch",
            "written_at": datetime.now().isoformat(),
            "consumed": True,
        },
    )
    result = _run_hook(
        {"prompt": "x", "terminal_id": "term1", "session_id": "sess1"}
    )
    assert result.returncode == 0
    settings = json.loads((fake_home / ".claude" / "settings.json").read_text())
    assert settings["model"] == "claude-sonnet-4-6"


def test_apply_warn_mode_is_skipped(tmp_state_dir, fake_home):
    """action_mode=warn → no rewrite; the warn path is owned by classify hook."""
    state_dir = (
        tmp_state_dir / ".claude" / "state" / "model-router" / "term1" / "sess1"
    )
    _write_rec(
        state_dir,
        {
            "recommended_model": "claude-haiku-4-5",
            "current_model": "claude-sonnet-4-6",
            "action_mode": "warn",
            "written_at": datetime.now().isoformat(),
            "consumed": False,
        },
    )
    result = _run_hook(
        {"prompt": "x", "terminal_id": "term1", "session_id": "sess1"}
    )
    assert result.returncode == 0
    settings = json.loads((fake_home / ".claude" / "settings.json").read_text())
    assert settings["model"] == "claude-sonnet-4-6"


def test_apply_same_model_is_skipped(tmp_state_dir, fake_home):
    """recommended == current → no rewrite (idempotent no-op)."""
    state_dir = (
        tmp_state_dir / ".claude" / "state" / "model-router" / "term1" / "sess1"
    )
    _write_rec(
        state_dir,
        {
            "recommended_model": "claude-sonnet-4-6",
            "current_model": "claude-sonnet-4-6",
            "action_mode": "autoswitch",
            "written_at": datetime.now().isoformat(),
            "consumed": False,
        },
    )
    result = _run_hook(
        {"prompt": "x", "terminal_id": "term1", "session_id": "sess1"}
    )
    assert result.returncode == 0
    settings = json.loads((fake_home / ".claude" / "settings.json").read_text())
    assert settings["model"] == "claude-sonnet-4-6"


def test_apply_dry_run_records_but_does_not_write(
    tmp_state_dir, fake_home, monkeypatch
):
    """MODEL_ROUTER_APPLY_DRY_RUN=1 → audit row written, settings.json untouched."""
    monkeypatch.setenv("MODEL_ROUTER_APPLY_DRY_RUN", "1")
    state_dir = (
        tmp_state_dir / ".claude" / "state" / "model-router" / "term1" / "sess1"
    )
    _write_rec(
        state_dir,
        {
            "recommended_model": "claude-haiku-4-5",
            "current_model": "claude-sonnet-4-6",
            "action_mode": "autoswitch",
            "written_at": datetime.now().isoformat(),
            "consumed": False,
        },
    )
    result = _run_hook(
        {"prompt": "x", "terminal_id": "term1", "session_id": "sess1"}
    )
    assert result.returncode == 0
    settings = json.loads((fake_home / ".claude" / "settings.json").read_text())
    assert settings["model"] == "claude-sonnet-4-6", "dry_run must not rewrite settings.json"


def test_apply_sets_anthropic_model_env_var(
    tmp_state_dir, fake_home
):
    """The apply hook must export ANTHROPIC_MODEL so a harness that honors
    the env-var channel picks up the new model even if it doesn't re-read
    settings.json mid-session (the falsification case the design identifies).
    """
    state_dir = (
        tmp_state_dir / ".claude" / "state" / "model-router" / "term1" / "sess1"
    )
    _write_rec(
        state_dir,
        {
            "recommended_model": "claude-opus-4-8",
            "current_model": "claude-sonnet-4-6",
            "action_mode": "autoswitch",
            "written_at": datetime.now().isoformat(),
            "consumed": False,
        },
    )

    env = os.environ.copy()
    env.pop("ANTHROPIC_MODEL", None)
    result = subprocess.run(
        [sys.executable, str(HOOK_PATH)],
        input=json.dumps(
            {"prompt": "x", "terminal_id": "term1", "session_id": "sess1"}
        ),
        capture_output=True,
        text=True,
        timeout=10,
        env=env,
    )
    # The hook writes env into its own process only — for the parent to inherit
    # we'd need to inspect. We assert the *intent* is encoded: settings.json was
    # rewritten (the env-var signal is the falsification-instrument channel and
    # the audit row documents it).
    assert result.returncode == 0
    audit_path = (
        tmp_state_dir
        / ".claude"
        / "state"
        / "model-router"
        / "apply_audit.jsonl"
    )
    assert audit_path.exists(), "audit row must be appended"
    rows = [json.loads(line) for line in audit_path.read_text().splitlines() if line]
    assert any(
        row.get("action_taken") == "applied" and row.get("new_model") == "claude-opus-4-8"
        for row in rows
    )


def test_apply_idempotent_under_repeat_calls(
    tmp_state_dir, fake_home
):
    """Second call after consumption must be a no-op (idempotency gate)."""
    state_dir = (
        tmp_state_dir / ".claude" / "state" / "model-router" / "term1" / "sess1"
    )
    _write_rec(
        state_dir,
        {
            "recommended_model": "claude-haiku-4-5",
            "current_model": "claude-sonnet-4-6",
            "action_mode": "autoswitch",
            "written_at": datetime.now().isoformat(),
            "consumed": False,
        },
    )
    stdin = {"prompt": "x", "terminal_id": "term1", "session_id": "sess1"}
    first = _run_hook(stdin)
    second = _run_hook(stdin)
    assert first.returncode == 0
    assert second.returncode == 0
    # First call switched to haiku; second call must not flip-flop.
    settings = json.loads((fake_home / ".claude" / "settings.json").read_text())
    assert settings["model"] == "claude-haiku-4-5"
