"""
Regression tests for the tool-evidence gate in Stop_deletion_verification_guard.

Root-cause FP fix (2026-06-18): the guard previously pattern-matched deletion
words in *prose* (reviews, recaps, recommendations, code-edit notes) and
hard-blocked the Stop even though no deletion ever ran — 757 firings in the
block log, blocking legitimate analytical turns. The fix gates the guard on real
per-turn tool evidence: it only engages when this turn actually executed a
filesystem-deletion command.

These tests load the real module (no mocks, per the project anti-mock stance)
and exercise check() end-to-end.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

_GUARD = (
    Path(__file__).resolve().parent.parent
    / "hooks" / "stop" / "Stop_deletion_verification_guard.py"
)
_LIB = Path(__file__).resolve().parent.parent / "__lib"


def _load():
    import sys
    for p in (str(_GUARD.parent), str(_LIB)):
        if p not in sys.path:
            sys.path.insert(0, p)
    spec = importlib.util.spec_from_file_location("dg_toolgate", _GUARD)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


dg = _load()

# A path guaranteed to exist on disk (this guard file itself).
EXISTING = str(_GUARD)


# ── _turn_performed_deletion ─────────────────────────────────────────────────

@pytest.mark.parametrize("cmd", [
    "rm -v /tmp/foo.py",
    "rm -rf build/",
    "rm ./scratch.txt",
    "git rm somemodule",
    "Remove-Item .\\stale.log",
    "del /q C:\\temp\\x.tmp",
    "python -c 'import os; os.remove(\"x\")'",
    "shutil.rmtree(target)",
    "Path('a.py').unlink()",
])
def test_detects_real_deletion_commands(cmd):
    data = {"response": "done", "tool_events": [{"name": "Bash", "input": {"command": cmd}}]}
    assert dg._turn_performed_deletion(data) is True


@pytest.mark.parametrize("events", [
    [],
    [{"name": "Read", "input": {"file_path": "x.py"}}],
    [{"name": "Grep", "input": {"pattern": "rm"}}],
    [{"name": "Bash", "input": {"command": "git restore x.py"}}],
    [{"name": "Bash", "input": {"command": "ls -la && grep removed log"}}],
])
def test_ignores_non_deletion_turns(events):
    data = {"response": "I removed the duplicate entry from the config", "tool_events": events}
    assert dg._turn_performed_deletion(data) is False


def test_tool_calls_string_fallback():
    assert dg._turn_performed_deletion({"tool_calls": "Bash(rm -rf dist)"}) is True
    assert dg._turn_performed_deletion({"tool_calls": "Read(x) Grep(y)"}) is False


# ── check() end-to-end ───────────────────────────────────────────────────────

def test_prose_review_with_existing_paths_allowed():
    """The exact FP class: review prose mentioning deletion + real paths, no rm."""
    data = {
        "response": f"The recommendation would have deleted live capability. See {EXISTING}.",
        "tool_events": [{"name": "Read", "input": {"file_path": EXISTING}}],
    }
    assert dg.check(data) is None


def test_bare_deletion_prose_allowed():
    data = {"response": "I did not delete anything; 'deleted files' was a quote.",
            "tool_events": []}
    assert dg.check(data) is None


def test_real_deletion_still_existing_blocks():
    """True positive preserved: ran rm, file still on disk -> block."""
    data = {
        "response": f"Deleted {EXISTING} successfully.",
        "tool_events": [{"name": "Bash", "input": {"command": f"rm -v {EXISTING}"}}],
    }
    result = dg.check(data)
    assert result is not None and result.get("decision") == "block"


def test_real_deletion_truly_gone_allowed():
    gone = str(_GUARD.parent / "zzz_definitely_not_here_12345.py")
    data = {
        "response": f"Deleted {gone}.",
        "tool_events": [{"name": "Bash", "input": {"command": f"rm {gone}"}}],
    }
    assert dg.check(data) is None


# ── transcript_path path (the REAL Stop payload has no tool_events) ───────────

import json as _json
import os as _os
import tempfile as _tempfile


def _write_transcript(entries):
    fd, path = _tempfile.mkstemp(suffix=".jsonl")
    _os.close(fd)
    with open(path, "w", encoding="utf-8") as f:
        for e in entries:
            f.write(_json.dumps(e) + "\n")
    return path


def test_transcript_detects_deletion_in_current_turn():
    path = _write_transcript([
        {"type": "user", "message": {"content": "clean up"}},
        {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "Bash", "input": {"command": "rm -rf build/"}}]}},
    ])
    try:
        assert dg._transcript_turn_has_deletion(path) is True
    finally:
        _os.unlink(path)


def test_transcript_no_deletion_review_turn():
    path = _write_transcript([
        {"type": "user", "message": {"content": "review the recommendation"}},
        {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "Read", "input": {"file_path": "x.py"}}]}},
        {"type": "assistant", "message": {"content": [
            {"type": "text", "text": "would have deleted live capability"}]}},
    ])
    try:
        assert dg._transcript_turn_has_deletion(path) is False
    finally:
        _os.unlink(path)


def test_transcript_stops_at_turn_boundary():
    """A deletion in a PRIOR turn (before the last real user prompt) is ignored."""
    path = _write_transcript([
        {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "Bash", "input": {"command": "rm old.py"}}]}},
        {"type": "user", "message": {"content": "now just review, don't delete"}},
        {"type": "assistant", "message": {"content": [
            {"type": "text", "text": "removed the duplicate entry from config"}]}},
    ])
    try:
        assert dg._transcript_turn_has_deletion(path) is False
    finally:
        _os.unlink(path)


def test_check_real_payload_shape_blocks_on_real_deletion():
    """No tool_events (real Stop shape); deletion proven via transcript; file exists."""
    path = _write_transcript([
        {"type": "user", "message": {"content": "delete the guard"}},
        {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "Bash", "input": {"command": f"rm {EXISTING}"}}]}},
    ])
    try:
        result = dg.check({"response": f"Deleted {EXISTING}.", "transcript_path": path})
        assert result is not None and result.get("decision") == "block"
    finally:
        _os.unlink(path)


def test_check_real_payload_shape_allows_review_prose():
    """No tool_events, no deletion in transcript -> review prose is allowed."""
    path = _write_transcript([
        {"type": "user", "message": {"content": "review"}},
        {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "Read", "input": {"file_path": EXISTING}}]}},
    ])
    try:
        assert dg.check({"response": f"would have deleted live capability; see {EXISTING}",
                         "transcript_path": path}) is None
    finally:
        _os.unlink(path)


def test_missing_transcript_path_fails_open():
    assert dg._turn_performed_deletion({"transcript_path": "P:/nonexistent/zzz.jsonl"}) is False
    assert dg._turn_performed_deletion({}) is False
