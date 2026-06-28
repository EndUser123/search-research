"""Regression tests for Stop_diagnostic_analysis_quality_gate.run() decision logic.

Pins the 2026-06-27 Class A fix (cc-aca-epistemic 0.2.61):
  - In block mode, run() blocks ONLY on a missing discriminating_test / falsifier.
  - competing_hypotheses / baseline / mechanism stay advisory (warn), never block.
  - shallow_compliance always blocks regardless of mode.

These are mutation-killer tests: each case targets one branch of run(), so
flipping the surgical `f.check == "discriminating_test"` guard, removing the
`mode == "block"` gate, or widening the block to all warn findings will fail a
named test below. See test_docstring on each for the mutation it kills.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
# Mirror test_quote_exemption_gates.py: add plugin __lib + hooks/stop, NOT the
# plugin root (would shadow the global hooks __lib per conftest.py).
sys.path.insert(0, str(_ROOT / "__lib"))
sys.path.insert(0, str(_ROOT / "hooks" / "stop"))

import Stop_diagnostic_analysis_quality_gate as g  # noqa: E402


# ── Fixtures: RCA texts chosen to isolate exactly one check ──────────────────

# Diagnostic, causal, but NO falsifier AND no competing hypotheses.
# Triggers: competing_hypotheses (warn) + discriminating_test (warn) + mechanism (warn).
BAD_RCA_NO_FALSIFIER = (
    "The root cause is the empty environment variable. This is why the provider "
    "returns 401 on every request, because the token never reaches the outbound "
    "call. The regression occurred when the migration dropped the export statement, "
    "so Bifrost reads nothing and the upstream rejects the call. Diagnosing further, "
    "the causal chain is that the missing export leaves the header empty, which "
    "results in authentication failure across all routes."
)

# Diagnostic, causal, WITH falsifier AND competing hypotheses AND a file trace.
# Every check satisfied -> no findings -> run() returns None (true pass).
GOOD_COMPLETE_RCA = (
    "The root cause is the empty environment variable, but there are two plausible "
    "explanations. Hypothesis A: the migration dropped the export. Hypothesis B: the "
    "loader overwrites it. To distinguish them, run in a clean shell; this would be "
    "wrong if the var were present and the call still failed. See loader.py:42."
)

# Diagnostic, causal, WITH a falsifier but NO competing hypotheses.
# competing_hypotheses fires (warn); discriminating_test passes. Must NOT block.
FOCUSED_RCA_WITH_FALSIFIER = (
    "The root cause is the empty environment variable; this is why the provider "
    "returns 401 on every request. To distinguish this from a network fault, note "
    "the failure is deterministic and reproduces only when the var is unset; this "
    "would be wrong if the var were present and the call still failed. See auth.py:10."
)

# 'Possible causes:' header with <2 substantive bullets -> shallow compliance.
SHALLOW_COMPLIANCE = (
    "The root cause requires investigation. Possible causes:\n"
    "- the config file\n"
    "- the network layer\n"
    "- a timing issue somewhere in the pipeline that I have not yet traced "
    "through carefully enough to be certain about the exact defect involved."
)

# Implementation report -> not a diagnostic turn -> no findings.
NOT_DIAGNOSTIC = "Fixed. All tests pass and the file was updated."


# ── Block mode (the shipped config) ───────────────────────────────────────────

def test_block_mode_bad_rca_without_falsifier_blocks(monkeypatch):
    """Kills mutation: removing the `discriminating_test` block branch would
    let a premature 'Root Cause:' claim with no falsifier ship."""
    monkeypatch.setenv("DIAGNOSTIC_ANALYSIS_QUALITY_GATE_ENABLED", "true")
    monkeypatch.setenv("DIAGNOSTIC_ANALYSIS_QUALITY_GATE_MODE", "block")
    out = g.run({"response": BAD_RCA_NO_FALSIFIER})
    assert out is not None
    assert out["decision"] == "block"
    assert "falsification" in out["reason"].lower() or "falsif" in out["reason"].lower()


def test_block_mode_complete_rca_passes(monkeypatch):
    """A diagnostic RCA with a falsifier, alternatives, and a source trace must
    produce no finding and return None."""
    monkeypatch.setenv("DIAGNOSTIC_ANALYSIS_QUALITY_GATE_ENABLED", "true")
    monkeypatch.setenv("DIAGNOSTIC_ANALYSIS_QUALITY_GATE_MODE", "block")
    assert g.run({"response": GOOD_COMPLETE_RCA}) is None


def test_block_mode_focused_rca_with_falsifier_does_not_block(monkeypatch):
    """Kills mutation: widening the block to ALL warn findings (the overfire
    path we rejected) would block a legitimate focused RCA that HAS a falsifier
    but lists no competing hypotheses. Must warn, not block."""
    monkeypatch.setenv("DIAGNOSTIC_ANALYSIS_QUALITY_GATE_ENABLED", "true")
    monkeypatch.setenv("DIAGNOSTIC_ANALYSIS_QUALITY_GATE_MODE", "block")
    out = g.run({"response": FOCUSED_RCA_WITH_FALSIFIER})
    assert out is None or out["decision"] != "block", (
        f"focused RCA with falsifier must not block, got: {out}"
    )


def test_shallow_compliance_blocks_regardless_of_mode(monkeypatch):
    """Kills mutation: gating shallow_compliance on `mode == block` would let
    an empty 'Possible causes:' list ship in warn mode."""
    monkeypatch.setenv("DIAGNOSTIC_ANALYSIS_QUALITY_GATE_ENABLED", "true")
    monkeypatch.setenv("DIAGNOSTIC_ANALYSIS_QUALITY_GATE_MODE", "warn")
    out = g.run({"response": SHALLOW_COMPLIANCE})
    assert out is not None and out["decision"] == "block"


# ── Warn mode ─────────────────────────────────────────────────────────────────

def test_warn_mode_bad_rca_returns_warn_not_block(monkeypatch):
    """Kills mutation: warn mode must never emit decision:block on the soft
    findings (only shallow_compliance escalates)."""
    monkeypatch.setenv("DIAGNOSTIC_ANALYSIS_QUALITY_GATE_ENABLED", "true")
    monkeypatch.setenv("DIAGNOSTIC_ANALYSIS_QUALITY_GATE_MODE", "warn")
    out = g.run({"response": BAD_RCA_NO_FALSIFIER})
    assert out is not None
    assert out["decision"] == "warn"


# ── Disabled / non-diagnostic ─────────────────────────────────────────────────

def test_disabled_returns_none(monkeypatch):
    """Kills mutation: a missing/early-return bypass when disabled."""
    monkeypatch.setenv("DIAGNOSTIC_ANALYSIS_QUALITY_GATE_ENABLED", "false")
    monkeypatch.setenv("DIAGNOSTIC_ANALYSIS_QUALITY_GATE_MODE", "block")
    assert g.run({"response": BAD_RCA_NO_FALSIFIER}) is None


def test_non_diagnostic_turn_returns_none(monkeypatch):
    """Implementation reports / status summaries must not trip the gate."""
    monkeypatch.setenv("DIAGNOSTIC_ANALYSIS_QUALITY_GATE_ENABLED", "true")
    monkeypatch.setenv("DIAGNOSTIC_ANALYSIS_QUALITY_GATE_MODE", "block")
    assert g.run({"response": NOT_DIAGNOSTIC}) is None
