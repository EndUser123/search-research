"""Tests for proposal_critique_gate — block proposals presented with no self-critique.

The gate is a deterministic PRESENCE check: a proposal/recommendation turn must
contain at least one failure-mode/falsification marker, or it is blocked. It does
NOT judge critique quality (a shallow-but-present critique passes — out of scope).

Also verifies the gate is wired into Stop.py's three registration structures and
that the GATE_CLASSES/GATE_METADATA sync invariant still holds.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))

import proposal_critique_gate as g  # noqa: E402

_LONG = "We wire the continuation-token allowlist into the gate and ship it. " * 8


def _proposal_no_critique() -> str:
    return "I recommend Option B here. " + _LONG


def _proposal_with_critique() -> str:
    return _proposal_no_critique() + (
        " This would be wrong if the contract lacks self-review content; "
        "the main risk is that it is gameable."
    )


class TestDetect:
    def test_proposal_without_critique_blocks(self):
        r = g.detect(_proposal_no_critique())
        assert r is not None and r["decision"] == "block"
        assert "self-critique" in r["reason"].lower()

    def test_proposal_with_failure_mode_passes(self):
        assert g.detect(_proposal_with_critique()) is None

    @pytest.mark.parametrize("marker", [
        "This would be wrong if X.",
        "The main risk is Y.",
        "It is gameable.",
        "This could fail when input is empty.",
        "The downside: it nags on trivial turns.",
        "False positive rate is the cost.",
    ])
    def test_each_critique_marker_satisfies(self, marker):
        # A recognized critique marker on a proposal turn → pass (no block).
        assert g.detect("I recommend Option B. " + _LONG + " " + marker) is None

    def test_non_proposal_passes(self):
        assert g.detect("Here is how the code works. " * 12) is None

    def test_short_response_passes(self):
        # Below the trivial threshold — never a substantive proposal.
        assert g.detect("I recommend Option B.") is None

    def test_bypass_token_in_prompt_passes(self):
        assert g.detect(_proposal_no_critique(), "--skip-critique-gate") is None

    def test_bypass_token_in_response_does_NOT_bypass(self):
        # External-review fix (2026-06-21): a bypass token in the assistant's own
        # response must NOT self-unblock — only the user prompt can bypass.
        r = g.detect(_proposal_no_critique() + " --skip-critique-gate")
        assert r is not None and r["decision"] == "block"

    @pytest.mark.parametrize("vacuous", [
        "Risk: none.",
        "risk: low.",
        "No caveats.",
        "There are no real downsides.",
        "Caveat: none known.",
        "Trade-offs: n/a.",
    ])
    def test_vacuous_critique_still_blocks(self, vacuous):
        # A proposal whose only "critique" is hollow filler must still block.
        assert g.detect("I recommend Option B. " + _LONG + " " + vacuous)["decision"] == "block"

    def test_genuine_soft_critique_survives_vacuous_strip(self):
        # A real soft critique is not falsely stripped even if a vacuous phrase
        # appears elsewhere in the same response.
        txt = ("I recommend Option B. " + _LONG +
               " The main risk is that it is gameable under load. Caveat: none about naming.")
        assert g.detect(txt) is None

    def test_disabled_returns_none(self, monkeypatch):
        monkeypatch.setattr(g, "ENABLED", False)
        assert g.detect(_proposal_no_critique()) is None

    @pytest.mark.parametrize("lead", [
        "I recommend", "My recommendation is", "I propose", "the fix is",
        "the solution is", "Option A", "the best approach is",
    ])
    def test_proposal_markers_recall(self, lead):
        # Each recognized proposal lead, with no critique, must block.
        txt = f"{lead} to do the thing. " + _LONG
        assert g.detect(txt) is not None


class TestRunExtraction:
    def test_run_reads_transcript(self):
        data = {"transcript": [
            {"role": "user", "content": "what should we do?"},
            {"role": "assistant", "content": _proposal_no_critique()},
        ]}
        r = g.run(data)
        assert r is not None and r["decision"] == "block"

    def test_run_reads_flat_response_field(self):
        assert g.run({"response": _proposal_no_critique()})["decision"] == "block"

    def test_run_passes_with_critique(self):
        assert g.run({"response": _proposal_with_critique()}) is None


class TestStopWiring:
    def test_registered_in_all_three_structures(self):
        import Stop
        assert "proposal_critique_gate" in Stop.GATE_CLASSES
        assert "proposal_critique_gate" in Stop.GATE_METADATA
        assert any(n == "proposal_critique_gate" for n, _ in Stop.IN_PROCESS_GATES)

    def test_metadata_is_blocking_quality(self):
        import Stop
        meta = Stop.GATE_METADATA["proposal_critique_gate"]
        assert Stop.GATE_CLASSES["proposal_critique_gate"] == "quality"
        assert meta["class"] == "quality"
        assert meta["rollout_mode"] == Stop.RolloutMode.BLOCK

    def test_metadata_covers_analysis_unknown_and_plan(self):
        # PLAN included (2026-06-21): "what should we do?" → proposal classifies as
        # a plan turn; the analysis/unknown-only set silently skipped it.
        import Stop
        tks = Stop.GATE_METADATA["proposal_critique_gate"]["relevant_turn_kinds"]
        assert Stop.TurnKind.PLAN in tks
        assert Stop.TurnKind.ANALYSIS in tks
        assert Stop.TurnKind.UNKNOWN in tks

    def test_runner_blocks_on_plan_turn(self):
        # Regression for the coverage hole: a plan-turn proposal w/o critique blocks.
        import Stop
        long_no_crit = ("I recommend Option B as the best approach. "
                        + "We wire the allowlist into the gate and ship it now. " * 5)
        data = {"response": long_no_crit, "last_assistant_message": long_no_crit,
                "prompt": "what should we do?"}
        r = Stop._run_proposal_critique_gate(data)
        assert r is not None and r["decision"] == "block"

    def test_runner_blocks_end_to_end(self):
        import Stop
        data = {"transcript": [
            {"role": "user", "content": "what should we do?"},
            {"role": "assistant", "content": _proposal_no_critique()},
        ]}
        r = Stop._run_proposal_critique_gate(data)
        assert r is not None and r["decision"] == "block"
