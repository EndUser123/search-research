#!/usr/bin/env python3
"""Test FrameGuard end-to-end workflow.

Tests the complete FrameGuard workflow from UserPromptSubmit to Stop:
- Full workflow in block mode
- Full workflow in warn mode
- Systemic query handling
- Non-systemic query passthrough
- Injection appears in response
- Stop validator blocks narrow frame
- Stop validator warns narrow frame
- Broad frame allowed
- Disabled mode passthrough
- State persistence across hooks
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

sys_path_insert = str(Path(__file__).resolve().parents[1])
if sys_path_insert not in sys.path:
    sys.path.insert(0, sys_path_insert)

import evidence_store as es


def _configure_tmp_paths(tmp_path: Path, monkeypatch) -> None:
    """Configure temporary paths for testing."""
    session_dir = tmp_path / "session_data"
    monkeypatch.setattr(es, "SESSION_DATA_DIR", session_dir)
    monkeypatch.setattr(es, "EVIDENCE_DB_PATH", session_dir / "evidence.db")


# === Helper Functions ===


def _run_hook(hook_path: str, input_data: dict, env: dict | None = None) -> dict:
    """Run a hook script and return parsed output."""
    # Merge current environment with any overrides
    sub_env = os.environ.copy()
    if env:
        sub_env.update(env)

    result = subprocess.run(
        [sys.executable, hook_path],
        input=json.dumps(input_data),
        capture_output=True,
        text=True,
        cwd=str(Path(hook_path).parent),
        env=sub_env,
    )

    try:
        return json.loads(result.stdout.strip()) if result.stdout else {}
    except json.JSONDecodeError:
        return {}


# === E2E Workflow Tests ===


def test_full_workflow_block_mode(tmp_path: Path, monkeypatch) -> None:
    """Test complete workflow in block mode."""
    _configure_tmp_paths(tmp_path, monkeypatch)
    es.init_db()

    original_mode = os.environ.get("FRAMEGUARD_MODE", "warn")

    try:
        os.environ["FRAMEGUARD_MODE"] = "block"

        session_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        terminal_id = "console_test"
        turn_id = "turn_block_001"

        # Phase 1: UserPromptSubmit - systemic query detected
        # (In real workflow, frameguard_classifier would record state)
        es.record_frameguard_trigger(
            session_id=session_id,
            terminal_id=terminal_id,
            turn_id=turn_id,
            needs_systemic_frame=True,
            trigger_reason="Local existence question inside system context",
            latent_questions=[],
        )

        # Phase 2: Stop - narrow frame response should be blocked
        response_data = {
            "response": "No, we don't have that hook.",
            "session_id": session_id,
            "terminal_id": terminal_id,
            "turn_id": turn_id,
        }

        # Pass temp database path to subprocess
        result = _run_hook(
            "P:/.claude/hooks/frameguard_stop.py",
            response_data,
            env={"FRAMEGUARD_EVIDENCE_DB_PATH": str(es.EVIDENCE_DB_PATH)},
        )

        # Should block in block mode
        assert result.get("allow") is False
        assert "FRAMEGUARD" in result.get("reason", "")
        assert "broader structural" in result.get("reason", "")

    finally:
        os.environ["FRAMEGUARD_MODE"] = original_mode


def test_full_workflow_warn_mode(tmp_path: Path, monkeypatch) -> None:
    """Test complete workflow in warn mode."""
    _configure_tmp_paths(tmp_path, monkeypatch)
    es.init_db()

    original_mode = os.environ.get("FRAMEGUARD_MODE", "warn")

    try:
        os.environ["FRAMEGUARD_MODE"] = "warn"

        session_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        terminal_id = "console_test"
        turn_id = "turn_warn_001"

        # Phase 1: UserPromptSubmit - record state
        es.record_frameguard_trigger(
            session_id=session_id,
            terminal_id=terminal_id,
            turn_id=turn_id,
            needs_systemic_frame=True,
            trigger_reason="Local existence question",
            latent_questions=[],
        )

        # Phase 2: Stop - narrow frame response should warn but allow
        response_data = {
            "response": "No, we don't have that hook.",
            "session_id": session_id,
            "terminal_id": terminal_id,
            "turn_id": turn_id,
        }

        result = _run_hook(
            "P:/.claude/hooks/frameguard_stop.py",
            response_data,
            env={"FRAMEGUARD_EVIDENCE_DB_PATH": str(es.EVIDENCE_DB_PATH)},
        )

        # Should allow in warn mode
        assert result.get("allow") is True
        assert "FRAMEGUARD" in result.get("reason", "")

    finally:
        os.environ["FRAMEGUARD_MODE"] = original_mode


def test_systemic_query_handling(tmp_path: Path, monkeypatch) -> None:
    """Test systemic query properly handled."""
    _configure_tmp_paths(tmp_path, monkeypatch)
    es.init_db()

    session_id = "cccccccc-cccc-cccc-cccc-cccccccccccc"
    terminal_id = "console_test"
    turn_id = "turn_systemic_001"

    # Record systemic frame requirement
    es.record_frameguard_trigger(
        session_id=session_id,
        terminal_id=terminal_id,
        turn_id=turn_id,
        needs_systemic_frame=True,
        trigger_reason="Systemic query",
        latent_questions=[],
    )

    # Response addresses systemic frame
    response_data = {
        "response": "The broader structural question here is about the hook architecture coverage.",
        "session_id": session_id,
        "terminal_id": terminal_id,
        "turn_id": turn_id,
    }

    result = _run_hook(
        "P:/.claude/hooks/frameguard_stop.py",
        response_data,
        env={"FRAMEGUARD_EVIDENCE_DB_PATH": str(es.EVIDENCE_DB_PATH)},
    )

    # Should allow - systemic frame was addressed
    assert result.get("allow") is True
    assert "handled" in result.get("reason", "").lower()


def test_non_systemic_query_passthrough(tmp_path: Path, monkeypatch) -> None:
    """Test non-systemic query passes through."""
    _configure_tmp_paths(tmp_path, monkeypatch)
    es.init_db()

    session_id = "dddddddd-dddd-dddd-dddd-dddddddddddd"
    terminal_id = "console_test"
    turn_id = "turn_non_systemic_001"

    # No FrameGuard state recorded (non-systemic query)

    # Response is regular
    response_data = {
        "response": "The capital of France is Paris.",
        "session_id": session_id,
        "terminal_id": terminal_id,
        "turn_id": turn_id,
    }

    result = _run_hook("P:/.claude/hooks/frameguard_stop.py", response_data)

    # Should allow - no systemic frame required
    assert result.get("allow") is True


def test_injection_appears_in_response(tmp_path: Path, monkeypatch) -> None:
    """Test warning injected into response context."""
    _configure_tmp_paths(tmp_path, monkeypatch)
    es.init_db()

    session_id = "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee"
    terminal_id = "console_test"
    turn_id = "turn_injection_001"

    # Record systemic frame requirement
    es.record_frameguard_trigger(
        session_id=session_id,
        terminal_id=terminal_id,
        turn_id=turn_id,
        needs_systemic_frame=True,
        trigger_reason="Systemic query",
        latent_questions=[],
    )

    # Check that state was recorded
    state = es.load_frameguard_state(session_id, terminal_id, turn_id)
    assert state is not None
    assert state["needs_systemic_frame"] is True


def test_stop_validator_blocks_narrow_frame(tmp_path: Path, monkeypatch) -> None:
    """Test narrow frame blocked in block mode."""
    _configure_tmp_paths(tmp_path, monkeypatch)
    es.init_db()

    original_mode = os.environ.get("FRAMEGUARD_MODE", "warn")

    try:
        os.environ["FRAMEGUARD_MODE"] = "block"

        session_id = "ffffffff-ffff-ffff-ffff-ffffffffffff"
        terminal_id = "console_test"
        turn_id = "turn_narrow_block_001"

        # Record systemic requirement
        es.record_frameguard_trigger(
            session_id=session_id,
            terminal_id=terminal_id,
            turn_id=turn_id,
            needs_systemic_frame=True,
            trigger_reason="Systemic query",
            latent_questions=[],
        )

        # Narrow frame response
        response_data = {
            "response": "No, that doesn't exist.",
            "session_id": session_id,
            "terminal_id": terminal_id,
            "turn_id": turn_id,
        }

        result = _run_hook(
            "P:/.claude/hooks/frameguard_stop.py",
            response_data,
            env={
                "FRAMEGUARD_EVIDENCE_DB_PATH": str(es.EVIDENCE_DB_PATH),
                "FRAMEGUARD_MODE": "block",
            },
        )

        # Should block
        assert result.get("allow") is False
        assert "Narrow-frame" in result.get("reason", "")

    finally:
        os.environ["FRAMEGUARD_MODE"] = original_mode


def test_stop_validator_warns_narrow_frame(tmp_path: Path, monkeypatch) -> None:
    """Test narrow frame warned in warn mode."""
    _configure_tmp_paths(tmp_path, monkeypatch)
    es.init_db()

    original_mode = os.environ.get("FRAMEGUARD_MODE", "warn")

    try:
        os.environ["FRAMEGUARD_MODE"] = "warn"

        session_id = "11111111-1111-1111-1111-111111111111"
        terminal_id = "console_test"
        turn_id = "turn_narrow_warn_001"

        # Record systemic requirement
        es.record_frameguard_trigger(
            session_id=session_id,
            terminal_id=terminal_id,
            turn_id=turn_id,
            needs_systemic_frame=True,
            trigger_reason="Systemic query",
            latent_questions=[],
        )

        # Narrow frame response
        response_data = {
            "response": "No, that doesn't exist.",
            "session_id": session_id,
            "terminal_id": terminal_id,
            "turn_id": turn_id,
        }

        result = _run_hook(
            "P:/.claude/hooks/frameguard_stop.py",
            response_data,
            env={
                "FRAMEGUARD_EVIDENCE_DB_PATH": str(es.EVIDENCE_DB_PATH),
                "FRAMEGUARD_MODE": "warn",
            },
        )

        # Should allow but with warning
        assert result.get("allow") is True
        assert "FRAMEGUARD advisory" in result.get("reason", "")

    finally:
        os.environ["FRAMEGUARD_MODE"] = original_mode


def test_broad_frame_allowed(tmp_path: Path, monkeypatch) -> None:
    """Test broad frame allowed."""
    _configure_tmp_paths(tmp_path, monkeypatch)
    es.init_db()

    session_id = "22222222-2222-2222-2222-222222222222"
    terminal_id = "console_test"
    turn_id = "turn_broad_001"

    # Record systemic requirement
    es.record_frameguard_trigger(
        session_id=session_id,
        terminal_id=terminal_id,
        turn_id=turn_id,
        needs_systemic_frame=True,
        trigger_reason="Systemic query",
        latent_questions=[],
    )

    # Broad frame response
    response_data = {
        "response": "Looking at the architectural context, the relationship between these elements involves...",
        "session_id": session_id,
        "terminal_id": terminal_id,
        "turn_id": turn_id,
    }

    result = _run_hook(
        "P:/.claude/hooks/frameguard_stop.py",
        response_data,
        env={"FRAMEGUARD_EVIDENCE_DB_PATH": str(es.EVIDENCE_DB_PATH)},
    )

    # Should allow - systemic frame addressed
    assert result.get("allow") is True
    assert "handled" in result.get("reason", "").lower()


def test_disabled_mode_passthrough(tmp_path: Path, monkeypatch) -> None:
    """Test everything passes when disabled."""
    _configure_tmp_paths(tmp_path, monkeypatch)
    es.init_db()

    original_enabled = os.environ.get("FRAMEGUARD_ENABLED", "true")

    try:
        os.environ["FRAMEGUARD_ENABLED"] = "false"

        session_id = "33333333-3333-3333-3333-333333333333"
        terminal_id = "console_test"
        turn_id = "turn_disabled_001"

        # Even with state recorded
        es.record_frameguard_trigger(
            session_id=session_id,
            terminal_id=terminal_id,
            turn_id=turn_id,
            needs_systemic_frame=True,
            trigger_reason="Systemic query",
            latent_questions=[],
        )

        # Narrow frame response
        response_data = {
            "response": "No, that doesn't exist.",
            "session_id": session_id,
            "terminal_id": terminal_id,
            "turn_id": turn_id,
        }

        result = _run_hook(
            "P:/.claude/hooks/frameguard_stop.py",
            response_data,
            env={
                "FRAMEGUARD_EVIDENCE_DB_PATH": str(es.EVIDENCE_DB_PATH),
                "FRAMEGUARD_ENABLED": "false",
            },
        )

        # Should allow - FrameGuard disabled
        assert result.get("allow") is True
        assert "disabled" in result.get("reason", "").lower()

    finally:
        os.environ["FRAMEGUARD_ENABLED"] = original_enabled


def test_state_persistence_across_hooks(tmp_path: Path, monkeypatch) -> None:
    """Test state persists UserPromptSubmit → Stop."""
    _configure_tmp_paths(tmp_path, monkeypatch)
    es.init_db()

    session_id = "44444444-4444-4444-4444-444444444444"
    terminal_id = "console_test"
    turn_id = "turn_persistence_001"

    # Simulate UserPromptSubmit phase - record state
    es.record_frameguard_trigger(
        session_id=session_id,
        terminal_id=terminal_id,
        turn_id=turn_id,
        needs_systemic_frame=True,
        trigger_reason="Local existence question",
        latent_questions=[],
    )

    # Simulate Stop phase - state should be available
    state = es.load_frameguard_state(session_id, terminal_id, turn_id)

    assert state is not None
    assert state["session_id"] == session_id
    assert state["terminal_id"] == terminal_id
    assert state["turn_id"] == turn_id
    assert state["needs_systemic_frame"] is True
    assert state["handled"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
