#!/usr/bin/env python3
"""Real-subprocess smoke + unit coverage for Stop-block logging in __lib/router.py.

A mock cannot fake these: the integration tests run the actual router.py as a
subprocess and assert the on-disk diagnostic row. Per the repo anti-mock policy,
no Mock objects are used — a real gate blocks on a real secret pattern.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
ROUTER = PLUGIN_ROOT / "__lib" / "router.py"
LIB = PLUGIN_ROOT / "__lib"

# A format-prefixed secret: triggers Stop_safety_gate Tier-1 detection deterministically.
SECRET = "sk-abcdefghijklmnopqrstuvwxyz0123456789ABCD"


def _write_transcript(tdir: Path, assistant_text: str) -> Path:
    tpath = tdir / "transcript.jsonl"
    tpath.write_text(
        "\n".join(
            json.dumps(o)
            for o in [
                {"type": "user", "message": {"role": "user", "content": "hi"}},
                {
                    "type": "assistant",
                    "message": {
                        "role": "assistant",
                        "content": [{"type": "text", "text": assistant_text}],
                    },
                },
            ]
        ),
        encoding="utf-8",
    )
    return tpath


def _run_router(payload: dict, diag_dir: Path) -> subprocess.CompletedProcess:
    env = dict(os.environ, CC_DIAGNOSTICS_DIR=str(diag_dir))
    return subprocess.run(
        [sys.executable, str(ROUTER), "Stop"],
        input=json.dumps(payload).encode(),
        capture_output=True,
        env=env,
    )


def test_real_block_writes_diagnostic_row():
    with tempfile.TemporaryDirectory() as td:
        tdir = Path(td)
        tpath = _write_transcript(tdir, f"Here it is: {SECRET}")
        result = _run_router(
            {"session_id": "t1", "transcript_path": str(tpath), "last_assistant_message": f"x {SECRET}"},
            tdir,
        )
        assert result.returncode == 2, result.stderr.decode(errors="replace")

        log = tdir / "stop_blocks.jsonl"
        assert log.exists(), "block must write a stop_blocks.jsonl row"
        row = json.loads(log.read_text(encoding="utf-8").strip().splitlines()[-1])
        assert row["gate_name"] == "Stop_safety_gate.py"
        assert "SAFETY VIOLATION" in row["reason"]
        assert row["session_id"] == "t1"
        assert len(row["response_hash"]) == 16  # sha256[:16]
        assert set(row) >= {
            "timestamp", "event", "gate_name", "reason",
            "matched_span", "response_hash", "session_id", "terminal_id",
        }


def test_clean_turn_writes_no_row():
    with tempfile.TemporaryDirectory() as td:
        tdir = Path(td)
        tpath = _write_transcript(tdir, "All good, nothing sensitive here.")
        result = _run_router(
            {"session_id": "t2", "transcript_path": str(tpath), "last_assistant_message": "All good."},
            tdir,
        )
        assert result.returncode == 0
        assert json.loads(result.stdout.decode())["decision"] == "approve"
        assert not (tdir / "stop_blocks.jsonl").exists()


def test_response_hash_keyed_to_assistant_text():
    import hashlib

    if str(LIB) not in sys.path:
        sys.path.insert(0, str(LIB))
    import router as r

    with tempfile.TemporaryDirectory() as td:
        tdir = Path(td)
        text = "You're right. I'll proceed now."
        tpath = _write_transcript(tdir, text)
        ctx = r._extract_block_ctx(
            "Stop", json.dumps({"transcript_path": str(tpath)}).encode()
        )
        expect = hashlib.sha256(text.encode("utf-8", "replace")).hexdigest()[:16]
        assert ctx["response_hash"] == expect


def test_non_stop_event_is_not_logged():
    if str(LIB) not in sys.path:
        sys.path.insert(0, str(LIB))
    import router as r

    with tempfile.TemporaryDirectory() as td:
        tdir = Path(td)
        os.environ["CC_DIAGNOSTICS_DIR"] = str(tdir)
        try:
            r._log_stop_block("X", "reason", "", {"event": "PreToolUse"})
            assert not (tdir / "stop_blocks.jsonl").exists()
        finally:
            os.environ.pop("CC_DIAGNOSTICS_DIR", None)


def test_gate_blocks_on_last_assistant_message_without_response():
    """Live CC Stop payloads carry last_assistant_message, not response.
    Regression for the dead-gate bug: the gate read "" and never scanned.
    No mock — the real gate runs as a subprocess on a real secret pattern."""
    gate = PLUGIN_ROOT / "hooks" / "stop" / "Stop_safety_gate.py"
    payload = {"last_assistant_message": f"leaked here: {SECRET}"}
    r = subprocess.run(
        [sys.executable, str(gate)], input=json.dumps(payload).encode(), capture_output=True
    )
    assert r.returncode == 2, r.stderr.decode(errors="replace")
    assert "SAFETY VIOLATION" in r.stdout.decode()


def test_gate_no_longer_blocks_neutered_protocol_pattern():
    """check_protocol (DESCRIPTION_PATTERNS) was removed as an FP landmine;
    a former-trigger phrase must now pass."""
    gate = PLUGIN_ROOT / "hooks" / "stop" / "Stop_safety_gate.py"
    payload = {"last_assistant_message": "Let me explain what the /foo command does."}
    r = subprocess.run(
        [sys.executable, str(gate)], input=json.dumps(payload).encode(), capture_output=True
    )
    assert r.returncode == 0, r.stdout.decode() + r.stderr.decode(errors="replace")


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
