"""Tests for __lib/turn_tool_events.build_turn_tool_events (no mocks).

Real Stop payloads carry no tool_events; this builder derives the current turn's
tool calls from transcript_path in the FLAT schema both consumers
(intent_artifact_alignment, overconfidence_detector) expect.
"""
from __future__ import annotations

import importlib.util
import json
import os
import tempfile
from pathlib import Path

_MOD = Path(__file__).resolve().parent.parent / "__lib" / "turn_tool_events.py"
_spec = importlib.util.spec_from_file_location("turn_tool_events", _MOD)
tte = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tte)
build = tte.build_turn_tool_events


def _tx(entries):
    fd, path = tempfile.mkstemp(suffix=".jsonl")
    os.close(fd)
    with open(path, "w", encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")
    return path


def test_flat_schema_and_pairing():
    path = _tx([
        {"type": "user", "message": {"content": "do the work"}},
        {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "id": "t1", "name": "Edit",
             "input": {"file_path": "P:/x/Stop.py"}},
            {"type": "tool_use", "id": "t2", "name": "Bash",
             "input": {"command": "ls skills/"}},
        ]}},
        {"type": "user", "message": {"content": [
            {"type": "tool_result", "tool_use_id": "t2", "content": "code\ndocs\n"}]}},
        {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "id": "t3", "name": "Skill", "input": {"skill": "gto"}}]}},
    ])
    try:
        evs = build(path)
    finally:
        os.unlink(path)

    assert len(evs) == 3
    # All flat keys present on every event.
    for e in evs:
        assert set(e) == {"name", "command", "file_path", "skill", "output_excerpt"}
    edit, bash, skill = evs
    assert edit["name"] == "Edit" and edit["file_path"] == "P:/x/Stop.py"
    assert bash["name"] == "Bash" and bash["command"] == "ls skills/"
    assert bash["output_excerpt"] == "code\ndocs\n"        # paired by tool_use_id
    assert skill["name"] == "Skill" and skill["skill"] == "gto"


def test_turn_boundary_excludes_prior_turn():
    path = _tx([
        {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "id": "old", "name": "Bash",
             "input": {"command": "rm old.py"}}]}},
        {"type": "user", "message": {"content": "now just review"}},
        {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "id": "new", "name": "Read",
             "input": {"file_path": "a.py"}}]}},
    ])
    try:
        evs = build(path)
    finally:
        os.unlink(path)
    assert [e["name"] for e in evs] == ["Read"]          # prior-turn Bash excluded
    assert all("rm old.py" != e["command"] for e in evs)


def test_fail_open():
    assert build("") == []
    assert build("P:/definitely/not/here_zzz.jsonl") == []
