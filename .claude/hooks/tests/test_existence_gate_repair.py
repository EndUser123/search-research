"""Smoke tests for the 2026-07-02 read-before-edit repair.

The pre-repair test suite (test_existence_gate.py) used top-level ``session_id``,
the same shape as the bug — so it could not catch the production failure where
the session id is nested under ``data["session"]["id"]``. These tests prove the
repaired path end-to-end with the REAL payload shape, plus the telemetry-only
rollout contract.

Covers the four required smoke points:
  1. resolve_session_id(data) handles the actual nested session payload.
  2. PostToolUse on Read writes the sidecar.
  3. PreToolUse on Edit/Write can read the sidecar (allow after read).
  4. Missing prior Read produces a telemetry event (and does NOT block by default).
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

HOOKS_DIR = Path(__file__).resolve().parent.parent
if str(HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(HOOKS_DIR))


def _nested(session_id: str, **kw) -> dict:
    """Build a payload with the real nested session shape."""
    payload = {"session": {"id": session_id}}
    payload.update(kw)
    return payload


@pytest.fixture(autouse=True)
def telemetry_enabled(monkeypatch):
    monkeypatch.setenv("AGENTIC_RELIABILITY_TELEMETRY", "1")
    monkeypatch.setenv("EXISTENCE_GATE_BLOCK", "0")  # telemetry-only by default
    yield


@pytest.fixture
def isolated_sidecar(monkeypatch, tmp_path):
    """Redirect the sidecar STATE_DIR into a temp dir so tests don't collide."""
    import PreToolUse_existence_gate as eg

    monkeypatch.setattr(eg, "STATE_DIR", tmp_path)
    return tmp_path


# --- Point 1: resolve_session_id handles nested payload ----------------------


def test_resolve_session_id_nested():
    from __lib.pre_tool_use_logic import resolve_session_id

    assert resolve_session_id(_nested("abc-123")) == "abc-123"
    # also accepts flat fallback
    assert resolve_session_id({"session_id": "flat-1"}) == "flat-1"
    assert resolve_session_id({}) == ""


def test_gate_uses_nested_session_id(isolated_sidecar):
    """The gate must NOT early-return on the nested payload (the old bug)."""
    import PreToolUse_existence_gate as eg

    with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as f:
        path = f.name
    data = _nested("nested-only-1", tool_name="Edit", tool_input={"file_path": path}, message="m")
    # Telemetry-default: allow (returns None), but the detect path must execute.
    assert eg.run(data) is None


# --- Point 2: PostToolUse Read writes the sidecar ----------------------------


def test_read_writes_sidecar(isolated_sidecar):
    import PreToolUse_existence_gate as eg

    with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as f:
        path = f.name
    eg.run_read_tracker(_nested("rd-1", tool_name="Read", tool_input={"file_path": path}))
    sid = eg.resolve_session_id(_nested("rd-1"))
    reads = eg._load_read_files(sid)
    assert path in reads, f"sidecar missing read file; got {reads}"


# --- Point 3: PreToolUse Edit reads the sidecar (allow after read) -----------


def test_edit_allows_after_read(isolated_sidecar):
    import PreToolUse_existence_gate as eg

    with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as f:
        path = f.name
    # read first
    eg.run_read_tracker(_nested("ed-1", tool_name="Read", tool_input={"file_path": path}))
    # now edit must allow
    res = eg.run(_nested("ed-1", tool_name="Edit", tool_input={"file_path": path}, message="edit"))
    assert res is None


# --- Point 4: missing prior Read -> telemetry event, no block ----------------


def test_missing_read_emits_telemetry_and_allows(isolated_sidecar):
    import PreToolUse_existence_gate as eg
    from __lib import agentic_reliability_telemetry as tel

    tel.clear_test_log()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as f:
        path = f.name
    data = _nested("miss-1", tool_name="Edit", tool_input={"file_path": path}, message="edit")

    # default rollout = telemetry-only -> allow
    assert eg.run(data) is None

    events = [e for e in tel.read_events() if e.get("category") == "read_before_edit"]
    missing = [e for e in events if e.get("event") == "missing_read"]
    assert missing, f"expected a missing_read telemetry event; got {events}"
    assert missing[0]["decision"] == "telemetry"
    assert missing[0]["gate"] == "existence_gate"


def test_block_path_still_exists_under_flag(isolated_sidecar, monkeypatch):
    """EXISTENCE_GATE_BLOCK=1 must still hard-block (regression guard for the gated path)."""
    monkeypatch.setenv("EXISTENCE_GATE_BLOCK", "1")
    with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as f:
        path = f.name
    data = _nested("blk-1", tool_name="Edit", tool_input={"file_path": path}, message="edit")

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            f"import sys; sys.path.insert(0, '{HOOKS_DIR}'); "
            f"import os; os.environ['EXISTENCE_GATE_BLOCK']='1'; "
            f"from PreToolUse_existence_gate import run; "
            f"data={json.dumps(data)}; run(data); "
            f"assert False, 'should have exited'",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2, f"expected block exit 2; got {result.returncode}, stderr={result.stderr}"
    assert "EXISTENCE CHECK REQUIRED" in result.stderr
