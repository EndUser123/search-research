"""Subagent-delegation fallback + coherent fast-path budget for the semantic critic.

When BOTH external review backends (z.ai GLM, Mistral) are unavailable, the
critic must NOT fail open. Instead call_semantic_critic_via_bifrost returns the
BACKENDS_UNAVAILABLE sentinel and run() emits a delegation directive telling the
main agent to spawn a review subagent in the (untimed) continuation turn.

Backends are stubbed with plain functions (no Mock objects, per repo policy) so
the path is exercised deterministically without network calls.
"""
from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest

STOP_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(STOP_DIR))

import Stop_semantic_critic as sc  # noqa: E402


@pytest.fixture(autouse=True)
def _isolate(monkeypatch):
    # Hermetic: no stop_hook_active short-circuit, fresh per-session cap.
    monkeypatch.setattr(sc, "_stop_hook_active", False, raising=False)
    sc._INVOCATION_COUNTS.clear()
    # Neutralize the veridical gate (it runs before the critic and calls Mistral).
    stub = types.ModuleType("anti_sycophancy.veridical_gate")
    stub.check_veridical_integrity = lambda **kw: None
    monkeypatch.setitem(sys.modules, "anti_sycophancy.veridical_gate", stub)


def _evaluative_data():
    # >50 words + evaluative keywords (recommend/best/compare/option) so the
    # profile resolves to evaluative_recommendation, AND a diagnostic-scope
    # keyword ("trade-off", "reason") so _is_diagnostic_scope admits it — the
    # scope gate runs before the backend call and needs both conditions.
    answer = (
        "I recommend Postgres as the best default here. Compared to the "
        "alternatives, the trade-offs favor it for transactional integrity and "
        "a mature ecosystem, though DynamoDB would be a better choice if write "
        "scale dominates. The reason is your access patterns: which option you "
        "should use depends on them and your operational constraints, so weigh "
        "those criteria before committing to a final decision on the database."
    )
    return {
        "transcript": [
            {"role": "user", "content": "Which database should we use and why?"},
            {"role": "assistant", "content": answer},
        ]
    }


def _budget_under_env(env_overrides: dict) -> dict:
    """Compute the budget constants in a FRESH interpreter under given env, so
    module-level constants are recomputed without reload-polluting this process."""
    import json
    import os
    import subprocess

    code = (
        "import sys; sys.path.insert(0, r'%s');"
        "import Stop_semantic_critic as sc;"
        "import json;"
        "co = max(sc.MISTRAL_TIMEOUT_SEC, sc.SEMANTIC_CRITIC_TIMEOUT_SEC) + sc._CRITIC_JOIN_OVERHEAD_SEC;"
        "print(json.dumps({"
        "'outer': sc.STOP_HOOK_TIMEOUT_SEC,"
        "'veridical': sc.VERIDICAL_BUDGET_SEC,"
        "'critic_backend': sc.SEMANTIC_CRITIC_TIMEOUT_SEC,"
        "'critic_overall': co,"
        "'margin': sc._LOCAL_GATE_MARGIN_SEC,"
        "'viable': sc.LLM_FASTPATH_VIABLE}))"
    ) % str(STOP_DIR)
    env = {**os.environ, **{k: str(v) for k, v in env_overrides.items()}}
    out = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, env=env, timeout=30
    )
    return json.loads(out.stdout.strip().splitlines()[-1])


class TestBudgetCoherence:
    def test_two_parallel_gates_fit_outer_at_default(self):
        # The REAL invariant: max(veridical, critic_overall) + local margin must
        # fit under the outer hook timeout — the gates run in PARALLEL, so the
        # hook's wall time is the slower of the two, not their sum.
        b = _budget_under_env({"STOP_HOOK_TIMEOUT_SEC": "10"})
        assert b["viable"] is True
        assert max(b["veridical"], b["critic_overall"]) + b["margin"] <= b["outer"], b

    def test_parallel_budgets_wider_than_serial_split(self):
        # The point of parallelizing: at outer=10 the critic backend slice must
        # fit glm-5.2's measured ~5s latency (the serial split's 4s did not).
        b = _budget_under_env({"STOP_HOOK_TIMEOUT_SEC": "10"})
        assert b["critic_backend"] >= 6, b
        assert b["veridical"] >= 6, b

    def test_stale_large_env_cannot_break_invariant(self):
        # Stale 30s values must not reintroduce the incoherence; the max still fits.
        b = _budget_under_env({
            "STOP_HOOK_TIMEOUT_SEC": "10",
            "MISTRAL_TIMEOUT_SEC": "30",
            "SEMANTIC_CRITIC_TIMEOUT_SEC": "30",
            "VERIDICAL_TIMEOUT_SEC": "30",
        })
        assert max(b["veridical"], b["critic_overall"]) + b["margin"] <= b["outer"], b

    def test_degenerate_small_outer_fails_safe_to_delegation(self):
        # Too-small outer → not viable → skip LLMs entirely (delegate), never an
        # incoherent budget that gets killed mid-call.
        b = _budget_under_env({"STOP_HOOK_TIMEOUT_SEC": "3"})
        assert b["viable"] is False, b

    def test_raising_outer_widens_fastpath(self):
        # The documented performance lever: a larger outer auto-scales budgets up.
        small = _budget_under_env({"STOP_HOOK_TIMEOUT_SEC": "10"})
        large = _budget_under_env({"STOP_HOOK_TIMEOUT_SEC": "20"})
        assert large["critic_backend"] > small["critic_backend"], (small, large)
        assert (
            max(large["veridical"], large["critic_overall"]) + large["margin"]
            <= large["outer"]
        )


class TestViabilityShortCircuit:
    def test_not_viable_returns_sentinel_without_calling_backends(self, monkeypatch):
        # When not viable, the backends must NOT be invoked at all.
        called = {"minimax": False, "mistral": False}

        def _mm(*a, **k):
            called["minimax"] = True
            return None

        def _mi(*a, **k):
            called["mistral"] = True
            return None

        monkeypatch.setattr(sc, "_call_minimax_critic", _mm)
        monkeypatch.setattr(sc, "_call_mistral_critic", _mi)
        monkeypatch.setattr(sc, "LLM_FASTPATH_VIABLE", False)
        out = sc.call_semantic_critic_via_bifrost("q", "a " * 60, "sess")
        assert out is sc.BACKENDS_UNAVAILABLE
        assert called == {"minimax": False, "mistral": False}


class TestVeridicalBudgetPassthrough:
    def test_run_passes_clamped_timeout_to_veridical(self, monkeypatch):
        # The veridical gate must receive the hook-coherent budget, not its 15s
        # default — otherwise it can hard-kill the hook before the critic runs.
        seen = {}

        def _capture(**kwargs):
            seen.update(kwargs)
            return None  # allow → fall through to the critic path

        stub = types.ModuleType("anti_sycophancy.veridical_gate")
        stub.check_veridical_integrity = _capture
        monkeypatch.setitem(sys.modules, "anti_sycophancy.veridical_gate", stub)
        monkeypatch.setattr(sc, "LLM_FASTPATH_VIABLE", True)
        monkeypatch.setattr(sc, "_call_minimax_critic", lambda *a, **k: None)
        monkeypatch.setattr(sc, "_call_mistral_critic", lambda *a, **k: None)

        sc.run(_evaluative_data())
        assert seen.get("timeout_sec") == sc.VERIDICAL_BUDGET_SEC, seen
        assert sc.VERIDICAL_BUDGET_SEC < sc.STOP_HOOK_TIMEOUT_SEC


class TestParallelArbitration:
    def test_veridical_violation_wins_over_concurrent_critic_ok(self, monkeypatch):
        # Gates now run in parallel; a veridical violation must still win the
        # arbitration even when the critic returns ok on the same turn.
        violation = {"decision": "block", "reason": "veridical violation"}
        stub = types.ModuleType("anti_sycophancy.veridical_gate")
        stub.check_veridical_integrity = lambda **kw: violation
        monkeypatch.setitem(sys.modules, "anti_sycophancy.veridical_gate", stub)
        monkeypatch.setattr(sc, "LLM_FASTPATH_VIABLE", True)
        ok = sc.SemanticCriticResult(ok=True, reason="Adequate.")
        monkeypatch.setattr(sc, "_call_minimax_critic", lambda *a, **k: ok)
        monkeypatch.setattr(sc, "_call_mistral_critic", lambda *a, **k: ok)

        res = sc.run(_evaluative_data())
        assert res is violation

    def test_out_of_scope_turn_still_runs_veridical(self, monkeypatch):
        # Scope-gating the critic must not silence the veridical gate.
        violation = {"decision": "block", "reason": "veridical violation"}
        stub = types.ModuleType("anti_sycophancy.veridical_gate")
        stub.check_veridical_integrity = lambda **kw: violation
        monkeypatch.setitem(sys.modules, "anti_sycophancy.veridical_gate", stub)
        monkeypatch.setattr(sc, "LLM_FASTPATH_VIABLE", True)
        monkeypatch.setattr(sc, "_is_diagnostic_scope", lambda *a, **k: False)
        critic_called = {"n": 0}

        def _critic(*a, **k):
            critic_called["n"] += 1
            return None

        monkeypatch.setattr(sc, "_call_minimax_critic", _critic)
        monkeypatch.setattr(sc, "_call_mistral_critic", _critic)

        res = sc.run(_evaluative_data())
        assert res is violation
        assert critic_called["n"] == 0, "critic must not be spent on out-of-scope turns"


class TestBifrostSentinel:
    def test_both_backends_none_returns_sentinel(self, monkeypatch):
        monkeypatch.setattr(sc, "_call_minimax_critic", lambda *a, **k: None)
        monkeypatch.setattr(sc, "_call_mistral_critic", lambda *a, **k: None)
        out = sc.call_semantic_critic_via_bifrost("q", "a " * 60, "sess")
        assert out is sc.BACKENDS_UNAVAILABLE

    def test_one_backend_ok_does_not_signal_unavailable(self, monkeypatch):
        ok = sc.SemanticCriticResult(ok=True, reason="Adequate.")
        monkeypatch.setattr(sc, "_call_minimax_critic", lambda *a, **k: None)
        monkeypatch.setattr(sc, "_call_mistral_critic", lambda *a, **k: ok)
        out = sc.call_semantic_critic_via_bifrost("q", "a " * 60, "sess")
        assert out is not sc.BACKENDS_UNAVAILABLE
        assert out.ok is True


class TestDelegationDirective:
    def test_both_down_emits_subagent_delegation(self, monkeypatch):
        monkeypatch.setattr(sc, "_call_minimax_critic", lambda *a, **k: None)
        monkeypatch.setattr(sc, "_call_mistral_critic", lambda *a, **k: None)
        res = sc.run(_evaluative_data())
        assert res is not None, "must not fail open when both backends are down"
        assert res.get("_backends_unavailable") is True
        msg = res.get("systemMessage", "")
        assert "subagent" in msg.lower()
        assert res.get("_critic_profile") == "evaluative_recommendation"

    def test_wrapper_escalates_delegation_to_block_for_high_signal(self, monkeypatch):
        """End-to-end: Stop.py's _run_semantic_critic must convert the delegation
        directive into a one-shot block for the high-signal evaluative profile."""
        monkeypatch.setattr(sc, "_call_minimax_critic", lambda *a, **k: None)
        monkeypatch.setattr(sc, "_call_mistral_critic", lambda *a, **k: None)
        monkeypatch.delenv("STOP_GATE_ROLLOUT_SEMANTIC_CRITIC", raising=False)

        hooks_dir = Path("P:/.claude/hooks")
        sys.path.insert(0, str(hooks_dir))
        import Stop  # noqa: E402

        res = Stop._run_semantic_critic(_evaluative_data())
        assert res is not None
        assert res.get("decision") == "block", res
        assert "subagent" in res.get("reason", "").lower()
