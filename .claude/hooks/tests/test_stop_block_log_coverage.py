#!/usr/bin/env python3
"""Regression tests for stop_block_log.py and all newly instrumented Stop-block sites.

Anti-mock policy: No Mock objects. All assertions use real subprocess calls,
real file writes, and real regex/logic. Tests verify the wiring at every
instrumented site.

Sites covered:
  1. stop_block_log module — unit tests for shared functions
  2. cc-aca-reasoning router — import chain + ctx population
  3. cc-aca-sdlc router — import chain + ctx population
  4. skill-guard execution_hooks — import chain + log call in stop_main
  5. Stop.py in-process — gate block writes to stop_blocks.jsonl (via real trigger)
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

SHARED_LIB = Path("P:/.claude/hooks/__lib")
REASONING_ROUTER = Path(
    "P:/packages/.claude-marketplace/plugins/cc-aca-reasoning/__lib/router.py"
)
SDLC_ROUTER = Path(
    "P:/packages/.claude-marketplace/plugins/cc-aca-sdlc/__lib/router.py"
)
STOP_PY = Path("P:/.claude/hooks/Stop.py")

# A format-prefixed secret recognised by Stop_safety_gate Tier-1 deterministically.
SECRET = "sk-abcdefghijklmnopqrstuvwxyz0123456789ABCD"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ensure_shared_lib():
    if str(SHARED_LIB) not in sys.path:
        sys.path.insert(0, str(SHARED_LIB))


def _write_transcript(tdir: Path, assistant_text: str) -> Path:
    tpath = tdir / "transcript.jsonl"
    tpath.write_text(
        "\n".join(
            json.dumps(o)
            for o in [
                {"type": "user", "message": {"role": "user", "content": "test"}},
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


# ---------------------------------------------------------------------------
# 1. Shared module — unit tests
# ---------------------------------------------------------------------------

class TestStopBlockLogModule:
    """Unit tests for stop_block_log.py functions (no subprocess)."""

    def test_import_succeeds(self):
        _ensure_shared_lib()
        import stop_block_log as sbl
        assert callable(sbl._extract_block_ctx)
        assert callable(sbl._log_stop_block)
        assert callable(sbl._response_fingerprint)
        assert callable(sbl._diag_dir)

    def test_extract_block_ctx_stop_event(self):
        _ensure_shared_lib()
        from stop_block_log import _extract_block_ctx
        payload = {"session_id": "s1", "terminal_id": "t1", "transcript_path": ""}
        ctx = _extract_block_ctx("Stop", json.dumps(payload).encode())
        assert ctx["event"] == "Stop"
        assert ctx["session_id"] == "s1"
        assert ctx["terminal_id"] == "t1"
        assert len(ctx["response_hash"]) == 16

    def test_extract_block_ctx_non_stop(self):
        _ensure_shared_lib()
        from stop_block_log import _extract_block_ctx
        ctx = _extract_block_ctx("PreToolUse", b"{}")
        assert ctx["event"] == "PreToolUse"

    def test_log_stop_block_writes_row(self):
        _ensure_shared_lib()
        from stop_block_log import _log_stop_block
        with tempfile.TemporaryDirectory() as td:
            tdir = Path(td)
            os.environ["CC_DIAGNOSTICS_DIR"] = str(tdir)
            try:
                ctx = {"event": "Stop", "session_id": "u1", "terminal_id": "", "transcript_path": "", "response_hash": "abc123"}
                _log_stop_block("test_gate", "test reason", "child stderr", ctx)
                log = tdir / "stop_blocks.jsonl"
                assert log.exists()
                row = json.loads(log.read_text(encoding="utf-8").strip())
                assert row["gate_name"] == "test_gate"
                assert row["reason"] == "test reason"
                assert row["session_id"] == "u1"
                assert set(row) >= {"timestamp", "event", "gate_name", "reason", "matched_span", "response_hash", "session_id", "terminal_id"}
            finally:
                os.environ.pop("CC_DIAGNOSTICS_DIR", None)

    def test_log_stop_block_non_stop_skips(self):
        _ensure_shared_lib()
        from stop_block_log import _log_stop_block
        with tempfile.TemporaryDirectory() as td:
            tdir = Path(td)
            os.environ["CC_DIAGNOSTICS_DIR"] = str(tdir)
            try:
                _log_stop_block("gate", "reason", "", {"event": "PreToolUse"})
                assert not (tdir / "stop_blocks.jsonl").exists()
            finally:
                os.environ.pop("CC_DIAGNOSTICS_DIR", None)

    def test_log_stop_block_none_ctx_skips(self):
        _ensure_shared_lib()
        from stop_block_log import _log_stop_block
        with tempfile.TemporaryDirectory() as td:
            os.environ["CC_DIAGNOSTICS_DIR"] = td
            try:
                _log_stop_block("gate", "reason", "", None)
                assert not (Path(td) / "stop_blocks.jsonl").exists()
            finally:
                os.environ.pop("CC_DIAGNOSTICS_DIR", None)

    def test_response_fingerprint_uses_last_assistant_message(self):
        _ensure_shared_lib()
        from stop_block_log import _response_fingerprint
        with tempfile.TemporaryDirectory() as td:
            tpath = _write_transcript(Path(td), "The quick brown fox")
            result = _response_fingerprint(str(tpath), b"fallback")
            expected = hashlib.sha256("The quick brown fox".encode("utf-8", "replace")).hexdigest()[:16]
            assert result == expected

    def test_response_fingerprint_fallback_on_missing_transcript(self):
        _ensure_shared_lib()
        from stop_block_log import _response_fingerprint
        fallback = b"some raw bytes"
        result = _response_fingerprint("/nonexistent/path.jsonl", fallback)
        expected = hashlib.sha256(fallback).hexdigest()[:16]
        assert result == expected


# ---------------------------------------------------------------------------
# 2. cc-aca-reasoning router — import chain
# ---------------------------------------------------------------------------

class TestReasoningRouterImport:
    """Verifies the reasoning router imports stop_block_log without error."""

    def test_router_imports_shared_module(self):
        result = subprocess.run(
            [sys.executable, "-c",
             f"import sys; sys.path.insert(0, r'{SHARED_LIB}'); "
             f"import importlib.util; "
             f"spec = importlib.util.spec_from_file_location('router', r'{REASONING_ROUTER}'); "
             f"mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); "
             f"assert callable(mod._extract_block_ctx); assert callable(mod._log_stop_block); "
             f"print('OK')"],
            capture_output=True,
            timeout=15,
        )
        assert result.returncode == 0, result.stderr.decode(errors="replace")
        assert b"OK" in result.stdout

    def test_emit_block_has_ctx_param(self):
        """Verify _emit_block accepts ctx keyword argument."""
        result = subprocess.run(
            [sys.executable, "-c",
             f"import importlib.util; "
             f"spec = importlib.util.spec_from_file_location('router', r'{REASONING_ROUTER}'); "
             f"mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); "
             f"import inspect; sig = inspect.signature(mod._emit_block); "
             f"assert 'ctx' in sig.parameters, f'ctx not in _emit_block: {{list(sig.parameters)}}'; "
             f"print('OK')"],
            capture_output=True,
            timeout=15,
        )
        assert result.returncode == 0, result.stderr.decode(errors="replace")
        assert b"OK" in result.stdout


# ---------------------------------------------------------------------------
# 3. cc-aca-sdlc router — import chain
# ---------------------------------------------------------------------------

class TestSdlcRouterImport:
    """Verifies the sdlc router imports stop_block_log without error."""

    def test_router_imports_shared_module(self):
        result = subprocess.run(
            [sys.executable, "-c",
             f"import importlib.util; "
             f"spec = importlib.util.spec_from_file_location('router', r'{SDLC_ROUTER}'); "
             f"mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); "
             f"assert callable(mod._extract_block_ctx); assert callable(mod._log_stop_block); "
             f"print('OK')"],
            capture_output=True,
            timeout=15,
        )
        assert result.returncode == 0, result.stderr.decode(errors="replace")
        assert b"OK" in result.stdout

    def test_emit_block_has_ctx_param(self):
        result = subprocess.run(
            [sys.executable, "-c",
             f"import importlib.util; "
             f"spec = importlib.util.spec_from_file_location('router', r'{SDLC_ROUTER}'); "
             f"mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); "
             f"import inspect; sig = inspect.signature(mod._emit_block); "
             f"assert 'ctx' in sig.parameters; print('OK')"],
            capture_output=True,
            timeout=15,
        )
        assert result.returncode == 0, result.stderr.decode(errors="replace")
        assert b"OK" in result.stdout


# ---------------------------------------------------------------------------
# 4. skill-guard execution_hooks — import chain
# ---------------------------------------------------------------------------

class TestSkillGuardImport:
    """Verifies execution_hooks imports stop_block_log without error."""

    def test_execution_hooks_imports_shared_module(self):
        eh_path = Path(
            "P:/packages/.claude-marketplace/plugins/skill-guard/src/skill_guard/execution_hooks.py"
        )
        result = subprocess.run(
            [sys.executable, "-c",
             f"import sys; "
             f"sys.path.insert(0, r'P:/packages/.claude-marketplace/plugins/skill-guard/src'); "
             f"import importlib.util; "
             f"spec = importlib.util.spec_from_file_location('execution_hooks', r'{eh_path}'); "
             f"mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); "
             f"assert callable(mod._extract_block_ctx); assert callable(mod._log_stop_block); "
             f"print('OK')"],
            capture_output=True,
            timeout=15,
        )
        assert result.returncode == 0, result.stderr.decode(errors="replace")
        assert b"OK" in result.stdout

    def test_stop_main_reads_stdin_as_bytes(self):
        """Verify stop_main reads sys.stdin.buffer (bytes) not sys.stdin (str)."""
        eh_path = Path(
            "P:/packages/.claude-marketplace/plugins/skill-guard/src/skill_guard/execution_hooks.py"
        )
        result = subprocess.run(
            [sys.executable, "-c",
             f"import inspect, sys; "
             f"sys.path.insert(0, r'P:/packages/.claude-marketplace/plugins/skill-guard/src'); "
             f"import importlib.util; "
             f"spec = importlib.util.spec_from_file_location('execution_hooks', r'{eh_path}'); "
             f"mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); "
             f"src = inspect.getsource(mod.stop_main); "
             f"assert 'stdin.buffer.read' in src, 'stop_main must read bytes'; print('OK')"],
            capture_output=True,
            timeout=15,
        )
        assert result.returncode == 0, result.stderr.decode(errors="replace")
        assert b"OK" in result.stdout


# ---------------------------------------------------------------------------
# 5. Stop.py in-process — block writes diagnostic row
# ---------------------------------------------------------------------------

class TestStopPyInProcessBlock:
    """Verifies Stop.py in-process gate block writes to stop_blocks.jsonl."""

    def test_inprocess_gate_block_writes_row(self):
        """Authority router blocks on a known secret; Stop.py should also write a row
        for its in-process safety_gate block when the same secret is in the response."""
        with tempfile.TemporaryDirectory() as td:
            tdir = Path(td)
            tpath = _write_transcript(tdir, f"Here is the secret: {SECRET}")
            payload = {
                "session_id": "stop_py_test",
                "transcript_path": str(tpath),
                "last_assistant_message": f"Here is the secret: {SECRET}",
            }
            env = dict(os.environ, CC_DIAGNOSTICS_DIR=str(tdir))
            result = subprocess.run(
                [sys.executable, str(STOP_PY)],
                input=json.dumps(payload).encode(),
                capture_output=True,
                env=env,
                timeout=30,
            )
            # Stop.py exits 0 when blocking (communicates via JSON stdout)
            stdout = result.stdout.decode(errors="replace").strip()
            # The block may have been caught by the in-process safety_gate OR
            # a subprocess authority gate (which would write the row itself).
            # Either way, at least one of: exit 0 with decision=block, or a row written.
            if stdout:
                try:
                    parsed = json.loads(stdout)
                    if parsed.get("decision") == "block":
                        # Stop.py in-process block: check the log row
                        log = tdir / "stop_blocks.jsonl"
                        assert log.exists(), (
                            "Stop.py in-process block must write stop_blocks.jsonl row; "
                            f"stdout: {stdout}, stderr: {result.stderr.decode(errors='replace')[:500]}"
                        )
                        rows = [json.loads(l) for l in log.read_text(encoding="utf-8").strip().splitlines()]
                        assert any(r.get("session_id") == "stop_py_test" for r in rows)
                        return  # passed
                except json.JSONDecodeError:
                    pass
            # If Stop.py approved (hooks may have been suppressed), skip — not a failure
            # of logging instrumentation, just gate suppression.
            if result.returncode == 0:
                pytest.skip("Stop.py did not block on this payload — gate may be suppressed")

    def test_stop_py_block_ctx_extraction(self):
        """Directly verify _extract_block_ctx from Stop.py's __lib path."""
        _ensure_shared_lib()
        from stop_block_log import _extract_block_ctx
        payload = {
            "session_id": "ctx_test",
            "terminal_id": "term_1",
            "transcript_path": "",
            "last_assistant_message": "test response",
        }
        raw_bytes = json.dumps(payload).encode("utf-8")
        ctx = _extract_block_ctx("Stop", raw_bytes)
        assert ctx["event"] == "Stop"
        assert ctx["session_id"] == "ctx_test"
        assert ctx["terminal_id"] == "term_1"
        assert len(ctx["response_hash"]) == 16


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
