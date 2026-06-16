"""Regression test: regeneration cap wired into Stop.py gate dispatch.

Roots: the original 7m35s incident was an unbounded Stop block -> regenerate loop.
The NBM-3 circuit breaker (__lib/circuit_breaker.py) existed and was tested but was
never wired into Stop._process_gate_result. These tests prove the wiring:

  - QUALITY gate blocks are bounded: after DEFAULT_THRESHOLD repair iterations the
    breaker trips and the verdict is surfaced as an advisory instead of blocking
    (allow + surface), turning an infinite loop into a bounded one.
  - POLICY gates (safety/secret/fabrication) are exempt: they always block and the
    breaker counter is never incremented for them.
  - A fresh stop (stop_hook_active=False) is the natural reset point.

No mocks (project anti-mock policy): exercises the real circuit_breaker + the real
Stop._process_gate_result via a temp iteration file.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

HOOKS_DIR = Path(__file__).resolve().parent.parent
if str(HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(HOOKS_DIR))

import Stop  # noqa: E402
from __lib.circuit_breaker import (  # noqa: E402
    DEFAULT_THRESHOLD,
    get_iteration_count,
    reset_iteration,
)

KEY = "test-regen-cap"


@pytest.fixture(autouse=True)
def _temp_counter(tmp_path, monkeypatch):
    monkeypatch.setenv("CIRCUIT_BREAKER_ITERATION_FILE", str(tmp_path / "cb" / "it.tmp"))
    reset_iteration(KEY)
    Stop._policy_block_this_turn = None  # main() resets this per turn
    yield
    reset_iteration(KEY)


def _block(gate_name: str):
    """Drive one quality/policy block decision through the real dispatch."""
    Stop._policy_block_this_turn = None  # mimic per-turn reset for policy arbitration
    qm: list[str] = []
    blocked = Stop._process_gate_result(
        {"decision": "block", "reason": "synthetic violation"},
        gate_name, [], qm, {"terminal_id": KEY, "response": "x", "stop_hook_active": True},
        "analysis", "normal",
    )
    return blocked, qm


def test_quality_gate_blocks_then_trips_to_allow_and_surface():
    # First DEFAULT_THRESHOLD calls block (and increment the counter).
    for i in range(DEFAULT_THRESHOLD):
        blocked, qm = _block("epistemic_contract")
        assert blocked is True, f"call {i + 1} should still block (below threshold)"
        assert qm == [], "no advisory surfaced while still blocking"
        assert get_iteration_count(KEY) == i + 1

    # Threshold reached: breaker trips -> allow + surface the unresolved verdict.
    blocked, qm = _block("epistemic_contract")
    assert blocked is False, "breaker must allow continuation once threshold is reached"
    assert qm and "unresolved" in qm[0].lower(), "verdict must be surfaced, not dropped"


def test_policy_gate_is_never_capped_and_never_counted():
    for _ in range(DEFAULT_THRESHOLD + 3):
        blocked, _qm = _block("safety_gate")
        assert blocked is True, "policy gate must block every time (no cap)"
    assert get_iteration_count(KEY) == 0, "policy gate must not touch the regen counter"


def test_inactive_stop_does_not_count():
    """When stop_hook_active is False, a quality block does not increment the counter."""
    Stop._policy_block_this_turn = None
    blocked = Stop._process_gate_result(
        {"decision": "block", "reason": "v"},
        "epistemic_contract", [], [], {"terminal_id": KEY, "response": "x", "stop_hook_active": False},
        "analysis", "normal",
    )
    assert blocked is True
    assert get_iteration_count(KEY) == 0
