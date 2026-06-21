"""Scoped self-critique enforcement for the semantic critic (Stop.py).

Covers the two changes that un-mute the critic so it actually forces a revision
on a flawed proposal instead of only logging an advisory note:

  Change A: semantic_critic is applicable on TurnKind.UNKNOWN (turn_mode
            meta/query/unknown collapse to UNKNOWN and were silently excluded).
  Change B: _run_semantic_critic escalates a HIGH-SIGNAL veto
            (evaluative_recommendation / software_rca) to a one-shot block when
            rollout is BLOCK; general_diagnostic stays advisory; the env
            override STOP_GATE_ROLLOUT_SEMANTIC_CRITIC=advisory reverts to
            pure advisory with no code change.

The external dual-LLM critic is replaced with a plain stub module (a real
function, not a Mock — per the repo anti-mock policy) so the wrapper's decision
logic is exercised deterministically without network calls.
"""
from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest

HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))

import Stop  # noqa: E402


# --- Change A: turn-kind eligibility -----------------------------------------

class TestTurnKindHole:
    def test_unknown_turn_now_applicable(self):
        ok, reason = Stop.is_gate_applicable(
            "semantic_critic", Stop.TurnKind.UNKNOWN, Stop.ClaimKind.FACTUAL, set()
        )
        assert ok is True, f"UNKNOWN should be eligible now, got skip reason {reason!r}"

    def test_analysis_turn_still_applicable(self):
        ok, _ = Stop.is_gate_applicable(
            "semantic_critic", Stop.TurnKind.ANALYSIS, Stop.ClaimKind.FACTUAL, set()
        )
        assert ok is True

    def test_control_turn_still_excluded(self):
        ok, reason = Stop.is_gate_applicable(
            "semantic_critic", Stop.TurnKind.CONTROL, Stop.ClaimKind.FACTUAL, set()
        )
        assert ok is False
        assert "turn_kind_excluded" in reason


# --- Change B: scoped escalation ---------------------------------------------

def _install_stub_critic(monkeypatch, *, veto: bool, profile: str):
    """Inject a stub Stop_semantic_critic module with deterministic behavior."""
    mod = types.ModuleType("Stop_semantic_critic")

    def run(data: dict):
        if not veto:
            return None
        return {"allow": True, "systemMessage": "Semantic critic: missing tradeoffs."}

    def _detect_critic_profile(user_prompt: str, response_text: str) -> str:
        return profile

    mod.run = run
    mod._detect_critic_profile = _detect_critic_profile
    monkeypatch.setitem(sys.modules, "Stop_semantic_critic", mod)


def _data():
    return {
        "transcript": [
            {"role": "user", "content": "Which database should we use?"},
            {"role": "assistant", "content": "Postgres. " * 30},
        ]
    }


class TestScopedEnforcement:
    def test_high_signal_veto_blocks_when_rollout_block(self, monkeypatch):
        monkeypatch.delenv("STOP_GATE_ROLLOUT_SEMANTIC_CRITIC", raising=False)
        _install_stub_critic(monkeypatch, veto=True, profile="evaluative_recommendation")
        res = Stop._run_semantic_critic(_data())
        assert res is not None
        assert res.get("decision") == "block", res
        assert "tradeoffs" in res.get("reason", "")

    def test_software_rca_veto_also_blocks(self, monkeypatch):
        monkeypatch.delenv("STOP_GATE_ROLLOUT_SEMANTIC_CRITIC", raising=False)
        _install_stub_critic(monkeypatch, veto=True, profile="software_rca")
        res = Stop._run_semantic_critic(_data())
        assert res.get("decision") == "block", res

    def test_general_diagnostic_veto_stays_advisory(self, monkeypatch):
        monkeypatch.delenv("STOP_GATE_ROLLOUT_SEMANTIC_CRITIC", raising=False)
        _install_stub_critic(monkeypatch, veto=True, profile="general_diagnostic")
        res = Stop._run_semantic_critic(_data())
        assert res.get("decision") != "block", res
        assert res.get("allow") is True
        assert "systemMessage" in res

    def test_env_override_advisory_disables_block(self, monkeypatch):
        monkeypatch.setenv("STOP_GATE_ROLLOUT_SEMANTIC_CRITIC", "advisory")
        _install_stub_critic(monkeypatch, veto=True, profile="evaluative_recommendation")
        res = Stop._run_semantic_critic(_data())
        assert res.get("decision") != "block", res
        assert res.get("allow") is True

    def test_no_veto_returns_none(self, monkeypatch):
        monkeypatch.delenv("STOP_GATE_ROLLOUT_SEMANTIC_CRITIC", raising=False)
        _install_stub_critic(monkeypatch, veto=False, profile="evaluative_recommendation")
        res = Stop._run_semantic_critic(_data())
        assert res is None

    def test_profile_surfaced_for_telemetry(self, monkeypatch):
        monkeypatch.setenv("STOP_GATE_ROLLOUT_SEMANTIC_CRITIC", "advisory")
        _install_stub_critic(monkeypatch, veto=True, profile="general_diagnostic")
        res = Stop._run_semantic_critic(_data())
        assert res.get("_critic_profile") == "general_diagnostic"
