from __future__ import annotations
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

HOOKS = Path(__file__).resolve().parent.parent if "hooks" in str(__file__) else Path("P:/.claude/hooks")
SELF_DOC = HOOKS / "PreToolUse_task_self_doc_gate.py"
DONE_GATE = HOOKS / "PreToolUse_task_done_evidence_gate.py"
PRETOOLUSE = HOOKS / "PreToolUse.py"


def _load_tool_hooks():
    spec = importlib.util.spec_from_file_location("_pretooluse_under_test", PRETOOLUSE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.TOOL_HOOKS


def _run_hook(script, payload, env=None):
    e = dict(os.environ)
    if env:
        e.update(env)
    r = subprocess.run([sys.executable, str(script)], input=json.dumps(payload).encode(),
                       capture_output=True, timeout=20, env=e)
    return r.returncode, r.stdout.decode(errors="replace"), r.stderr.decode(errors="replace")


def test_dispatch_covers_real_tool_names():
    th = _load_tool_hooks()
    assert "TaskCreate" in th
    assert "TaskUpdate" in th
    assert "TaskList" in th
    assert "TaskGet" in th


def test_dispatch_dropped_bare_Task():
    th = _load_tool_hooks()
    assert "Task" not in th


def test_gate_registration():
    th = _load_tool_hooks()
    assert "PreToolUse_task_self_doc_gate.py" in th["TaskCreate"]
    assert "PreToolUse_task_self_doc_gate.py" in th["TaskUpdate"]
    # done_evidence gate removed from dispatch per GR-1: advisory stderr is
    # swallowed by run_hook (captures stdout only); receipt-based /task clean
    # is the actual deletion guard.
    assert "PreToolUse_task_done_evidence_gate.py" not in th["TaskUpdate"]


VALID = {"tool_name": "TaskCreate", "tool_input": {
    "subject": "Fix auth bug in the SSO login redirect flow",
    "description": ("Users hit a 500 error when logging in via SSO during the redirect step. "
                    "The crash shows a null token; it throws an AttributeError in the validator.")}}
VAGUE = {"tool_name": "TaskCreate", "tool_input": {"subject": "x", "description": "short"}}


def test_self_doc_valid_allows():
    rc, out, err = _run_hook(SELF_DOC, VALID)
    assert rc == 0
    assert out.strip() == ""


def test_self_doc_vague_blocks_with_reason():
    rc, out, err = _run_hook(SELF_DOC, VAGUE)
    assert rc == 0
    payload = json.loads(out)
    assert payload["decision"] == "block"
    assert payload.get("reason")


def test_self_doc_autocorrect_taskupdate_param():
    payload = {"tool_name": "TaskUpdate", "tool_input": {"task_id": "5", "status": "in_progress"}}
    rc, out, err = _run_hook(SELF_DOC, payload)
    assert rc == 0
    if out.strip():
        data = json.loads(out)
        assert data["decision"] in ("modify", "block")
        if data["decision"] == "modify":
            assert "taskId" in data["tool_input"]
            assert "task_id" not in data["tool_input"]


def test_self_doc_malformed_no_traceback():
    r = subprocess.run([sys.executable, str(SELF_DOC)], input=b"not valid json {{{",
                       capture_output=True, timeout=20, env=dict(os.environ))
    assert r.returncode == 0
    assert b"Traceback" not in r.stderr


def test_self_doc_non_dict_no_traceback():
    r = subprocess.run([sys.executable, str(SELF_DOC)], input=b"[1, 2, 3]",
                       capture_output=True, timeout=20, env=dict(os.environ))
    assert r.returncode == 0
    assert b"Traceback" not in r.stderr


def test_self_doc_completion_requires_description():
    payload = {"tool_name": "TaskUpdate", "tool_input": {"taskId": "7", "status": "completed", "description": "done"}}
    rc, out, err = _run_hook(SELF_DOC, payload)
    assert rc == 0
    data = json.loads(out)
    assert data["decision"] == "block"


def test_done_gate_never_blocks():
    payload = {"tool_name": "TaskUpdate", "tool_input": {"taskId": "4242", "status": "completed"}}
    rc, out, err = _run_hook(DONE_GATE, payload, env={"TASK_RECEIPT_DIR": "/nonexistent_xyz"})
    assert rc == 0


def test_done_gate_advisory_when_no_receipt():
    payload = {"tool_name": "TaskUpdate", "tool_input": {"taskId": "4242", "status": "completed"}}
    rc, out, err = _run_hook(DONE_GATE, payload, env={"TASK_RECEIPT_DIR": "/nonexistent_xyz"})
    assert rc == 0
    assert "receipt" in err.lower()


def test_done_gate_silent_when_receipt_exists(tmp_path):
    rd = tmp_path / "receipts"
    # Some pytest runners pre-create named temporary descendants when tests
    # from multiple roots share a basetemp. The test only needs the directory
    # to exist, not to prove mkdir semantics.
    rd.mkdir(parents=True, exist_ok=True)
    # Terminal-scoped path: the gate resolves terminal_id from env; use "testterm".
    term_dir = rd / "testterm"
    term_dir.mkdir()
    (term_dir / "4242.json").write_text(json.dumps({"task_id": "4242", "evidence_class": "VERIFIED"}))
    payload = {"tool_name": "TaskUpdate", "tool_input": {"taskId": "4242", "status": "completed"}}
    rc, out, err = _run_hook(DONE_GATE, payload,
                              env={"TASK_RECEIPT_DIR": str(rd), "CLAUDE_TERMINAL_ID": "testterm"})
    assert rc == 0
    assert err.strip() == ""


def test_done_gate_ignores_non_completion():
    payload = {"tool_name": "TaskUpdate", "tool_input": {"taskId": "4242", "status": "in_progress"}}
    rc, out, err = _run_hook(DONE_GATE, payload, env={"TASK_RECEIPT_DIR": "/nonexistent_xyz"})
    assert rc == 0
    assert err.strip() == ""
