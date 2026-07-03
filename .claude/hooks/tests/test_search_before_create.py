#!/usr/bin/env python3
"""Tests for PreToolUse_search_before_create.py (Phase 2 promotion).

Promoted 2026-07-02 from telemetry-only to active protection:
- High-risk extension points (PreToolUse_*, PostToolUse_*, Stop_*, etc.):
  soft-block with explicit bypass.
- Normal helper/utility paths: warn with the existing message.
- Bypass: --allow-no-search in the user message.
"""

import importlib
import importlib.util
import os
import sys
import tempfile
from pathlib import Path

import pytest

HOOKS_DIR = Path("P:/.claude/hooks")
if str(HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(HOOKS_DIR))


def _load_module():
    spec = importlib.util.spec_from_file_location(
        "PreToolUse_search_before_create",
        HOOKS_DIR / "PreToolUse_search_before_create.py",
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["PreToolUse_search_before_create"] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def probe():
    return _load_module()


@pytest.fixture
def fresh_sessions(probe, monkeypatch, tmp_path):
    """Point STATE_DIR at a per-test temp dir; clean sidecar before each test."""
    monkeypatch.setattr(probe, "STATE_DIR", tmp_path)
    return tmp_path


def _new_helper(path: Path, name: str = "my_util.py") -> Path:
    p = path / name
    p.touch()
    return p


def test_trivial_path_returns_none(probe, fresh_sessions):
    """A non-helper file path is below the heuristic's noise floor and returns None."""
    p = fresh_sessions / "notes.md"
    p.touch()
    data = {
        "tool_name": "Write",
        "session": {"id": "t1"},
        "tool_input": {"file_path": str(p)},
        "message": "",
    }
    assert probe.run(data) is None


def test_existing_file_returns_none(probe, fresh_sessions):
    """Editing an existing file is existence_gate's job; this probe only sees Creates."""
    p = fresh_sessions / "my_util.py"
    p.touch()  # already exists
    data = {
        "tool_name": "Write",
        "session": {"id": "t2"},
        "tool_input": {"file_path": str(p)},
        "message": "",
    }
    assert probe.run(data) is None


def test_helper_path_with_prior_search_returns_none(probe, fresh_sessions):
    """A new helper file with a prior Grep/Glob search in the sidecar passes."""
    p = fresh_sessions / "my_util.py"
    p.touch()
    # Pre-record a search in the sidecar.
    sid = "t3"
    sidecar = fresh_sessions / f"searches_{sid}.json"
    import json as _j
    sidecar.write_text(_j.dumps({"searches": ["Grep:my_util"]}))
    data = {
        "tool_name": "Write",
        "session": {"id": sid},
        "tool_input": {"file_path": str(p)},
        "message": "",
    }
    assert probe.run(data) is None


def test_high_risk_extension_without_search_soft_blocks(probe, fresh_sessions):
    """A new PreToolUse_*.py without prior Grep/Glob returns a block decision payload."""
    p = fresh_sessions / "PreToolUse_my_new_check.py"
    # DO NOT touch the file: the gate only fires on Creates (non-existent files).
    assert not p.exists()
    data = {
        "tool_name": "Write",
        "session": {"id": "t4"},
        "tool_input": {"file_path": str(p)},
        "message": "",
    }
    result = probe.run(data)
    assert result is not None
    assert result["decision"] == "block"
    assert "high-risk extension point" in result["reason"]
    assert result["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_high_risk_extension_with_allow_bypass_passes(probe, fresh_sessions):
    """--allow-no-search in the user message bypasses the soft-block (audit-logged)."""
    p = fresh_sessions / "PostToolUse_my_new_check.py"
    # DO NOT touch the file: gate only fires on Creates.
    assert not p.exists()
    data = {
        "tool_name": "Write",
        "session": {"id": "t5"},
        "tool_input": {"file_path": str(p)},
        "message": "I checked for conflicts already --allow-no-search",
    }
    result = probe.run(data)
    assert result is None  # bypassed


def test_normal_helper_path_warns(probe, fresh_sessions):
    """A new helper/utility file not in a high-risk path returns a warn payload."""
    p = fresh_sessions / "my_helper.py"
    assert not p.exists()
    data = {
        "tool_name": "Write",
        "session": {"id": "t6"},
        "tool_input": {"file_path": str(p)},
        "message": "",
    }
    result = probe.run(data)
    assert result is not None
    assert result["decision"] == "warn"
    assert "search-before-create" in result["systemMessage"].lower()


def test_high_risk_with_allow_bypass_emits_telemetry(probe, fresh_sessions, monkeypatch):
    """--allow-no-search emits a separate telemetry event with high_risk=True."""
    # Enable telemetry.
    monkeypatch.setenv("AGENTIC_RELIABILITY_TELEMETRY", "1")
    from __lib import agentic_reliability_telemetry as tel
    monkeypatch.setattr(tel, "_ENABLED", True)
    tel.clear_test_log()

    p = fresh_sessions / "Stop_my_check.py"
    # Do NOT touch — hook only fires on Creates.
    data = {
        "tool_name": "Write",
        "session": {"id": "t7"},
        "tool_input": {"file_path": str(p)},
        "message": "--allow-no-search",
    }
    probe.run(data)

    events = [
        e for e in tel.read_events()
        if e.get("category") == "search_before_create"
    ]
    assert any(e.get("event") == "create_without_search_bypass" for e in events), events
    bypass = [e for e in events if e.get("event") == "create_without_search_bypass"][0]
    assert bypass["extra"]["high_risk"] is True
    assert bypass["extra"]["file"].endswith("Stop_my_check.py")
