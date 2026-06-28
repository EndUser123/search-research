#!/usr/bin/env python3
"""CHANGE-003 (OQ-1: block-first, narrow trigger) — TDD for the done-gate.

Contract (director decision 2026-06-27):
  A. BLOCK on the first fabricated evidence-existence claim (claimed edit/verification
     that did not happen) — replaces advisory-first/block-on-repeat.
  B. WARN on ungrounded superlatives WITH satisfied file grounding.
  C. PASS on satisfied grounding (no superlative issue).
Plus the preserved existing contract: done-claim + real file -> pass (self-test Test 1).

Run: python -m pytest P:/.claude/hooks/test_fake_done_block_first.py -q
"""
from __future__ import annotations

import sys
from pathlib import Path

_PLUGIN_STOP = Path(r"P:/packages/.claude-marketplace/plugins/cc-aca-epistemic/hooks/stop")
_GLOBAL_HOOKS = Path(r"P:/.claude/hooks")
for _p in (str(_PLUGIN_STOP), str(_GLOBAL_HOOKS)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from Stop_fake_done_detector import run_fake_done_detector  # noqa: E402
from hook_state_manager import clear_state  # noqa: E402


def _fresh(tid: str) -> None:
    """Reset violation state so each test sees a first occurrence (block-first scope)."""
    clear_state(tid, "fake_done_count.json")
    clear_state(tid, "last_violations.json")


def _data(tid: str, sid: str, text: str, cwd: str) -> dict:
    return {
        "terminal_id": tid,
        "session_id": sid,
        "cwd": cwd,
        "output_text": text,
        "all_violations": [],
    }


# --- Test C: satisfied grounding -> PASS (preserves existing self-test Test 1) ---
def test_pass_on_grounded_evidence(tmp_path):
    tid, sid = "tbd_c", "sbd_c"
    _fresh(tid)
    (tmp_path / "engine.py").write_text("x=1\n", encoding="utf-8")
    result = run_fake_done_detector(_data(tid, sid, "Implementation complete. Wrote engine.py", str(tmp_path)))
    assert result is None, f"grounded evidence must pass, got {result}"


# --- Test A: fabricated evidence-existence -> BLOCK on FIRST occurrence ---
def test_block_on_fabricated_evidence_first_occurrence(tmp_path):
    tid, sid = "tbd_a", "sbd_a"
    _fresh(tid)
    # References a file that does NOT exist -> fabricated evidence-existence.
    result = run_fake_done_detector(
        _data(tid, sid, "Implementation complete. Wrote council_core/engine/council.py", str(tmp_path))
    )
    assert result is not None, "fabricated evidence must trigger the gate"
    assert result["severity"] == "block", (
        f"OQ-1 block-first: fabricated evidence-existence must BLOCK on first occurrence, got {result.get('severity')}"
    )


# --- Test 2 -> block-first: done-claim with NO evidence -> BLOCK on first occurrence ---
def test_block_on_no_evidence_first_occurrence(tmp_path):
    tid, sid = "tbd_2", "sbd_2"
    _fresh(tid)
    result = run_fake_done_detector(_data(tid, sid, "Implementation complete.", str(tmp_path)))
    assert result is not None
    assert result["severity"] == "block", (
        f"block-first: completion claim with no evidence must BLOCK on first occurrence, got {result.get('severity')}"
    )


# --- Test B: ungrounded superlative WITH satisfied grounding -> WARN ---
def test_warn_on_ungrounded_superlative_with_grounding(tmp_path):
    tid, sid = "tbd_b", "sbd_b"
    _fresh(tid)
    (tmp_path / "engine.py").write_text("x=1\n", encoding="utf-8")
    # Grounding satisfied (engine.py exists) but the claim is an ungrounded superlative.
    text = "Implementation complete. The fix is flawlessly robust and perfectly bulletproof. Wrote engine.py"
    result = run_fake_done_detector(_data(tid, sid, text, str(tmp_path)))
    assert result is not None, "ungrounded superlative with satisfied grounding must WARN (not pass silently)"
    assert result["severity"] == "warning", (
        f"OQ-1: ungrounded superlative + satisfied grounding -> WARN, got {result.get('severity')}"
    )


# --- Regression: no done-claim -> PASS (gate does not fire) ---
def test_no_done_claim_no_gate(tmp_path):
    tid, sid = "tbd_n", "sbd_n"
    _fresh(tid)
    result = run_fake_done_detector(_data(tid, sid, "I'll look at engine.py next.", str(tmp_path)))
    assert result is None


# --- Regression: fabricated evidence still blocks even when repeated (block stays block) ---
def test_block_persists_on_repeat(tmp_path):
    tid, sid = "tbd_r", "sbd_r"
    _fresh(tid)
    first = run_fake_done_detector(
        _data(tid, sid, "Implementation complete. Wrote missing.py", str(tmp_path))
    )
    assert first is not None and first["severity"] == "block"
    second = run_fake_done_detector(
        _data(tid, sid, "Implementation complete. Wrote still_missing.py", str(tmp_path))
    )
    assert second is not None and second["severity"] == "block"
