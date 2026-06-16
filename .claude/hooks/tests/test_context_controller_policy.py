"""Tests for context_controller.policy (deterministic classification + health).

Pure-function module: no I/O, no LLM calls. Tests verify precedence order,
boundary cases, and dataclass invariants.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Inject context_controller dir so `import policy` resolves to the
# context_controller package, not anything else.
_CONTEXT_CONTROLLER_DIR = str(Path(__file__).resolve().parent.parent / "context_controller")
if _CONTEXT_CONTROLLER_DIR not in sys.path:
    sys.path.insert(0, _CONTEXT_CONTROLLER_DIR)

import pytest

import policy as policy_mod
import state as state_mod

# Module-level imports
FRESH_PHASE_CHECKPOINT_PHASES = policy_mod.FRESH_PHASE_CHECKPOINT_PHASES
HealthAssessment = policy_mod.HealthAssessment
LARGE_OUTPUTS_COMPACT = policy_mod.LARGE_OUTPUTS_COMPACT
PHASE_TURNS_CHECKPOINT = policy_mod.PHASE_TURNS_CHECKPOINT
PhaseClassification = policy_mod.PhaseClassification
SUBAGENT_HINT_PROMPTS = policy_mod.SUBAGENT_HINT_PROMPTS
classify_phase = policy_mod.classify_phase
evaluate_health = policy_mod.evaluate_health
recommend_subagent = policy_mod.recommend_subagent
ContextHealth = state_mod.ContextHealth


# ---- Constants -------------------------------------------------------------


class TestConstants:
    def test_phase_turns_checkpoint_is_documented(self):
        # 12 is the upper bound for a focused implementation phase.
        # The plan document justifies this; tests pin the value.
        assert PHASE_TURNS_CHECKPOINT == 12

    def test_large_outputs_compact_is_low_threshold(self):
        # 2 is intentionally low; the controller is advisory-only.
        assert LARGE_OUTPUTS_COMPACT == 2

    def test_fresh_phase_checkpoint_phases(self):
        assert FRESH_PHASE_CHECKPOINT_PHASES == frozenset(
            {"research", "planning", "debugging"}
        )

    def test_subagent_hint_prompts_nonempty(self):
        # The controller must surface a recommendation for at least the
        # canonical "investigate" prompt.
        assert len(SUBAGENT_HINT_PROMPTS) >= 5
        joined = "|".join(SUBAGENT_HINT_PROMPTS)
        assert r"investigate" in joined
        assert r"trace" in joined


# ---- classify_phase -------------------------------------------------------


class TestClassifyPhasePrecedence:
    """The rule list is the contract: highest-precedence match wins."""

    def test_empty_prompt_returns_general_fallback(self):
        c = classify_phase("")
        assert c.phase == "general"
        assert c.rule_name == "fallback"
        assert c.matched_text == ""

    def test_whitespace_only_prompt_returns_general(self):
        c = classify_phase("   \t\n  ")
        assert c.phase == "general"

    def test_none_prompt_does_not_raise(self):
        # Defensive — bad caller, but must not crash the controller.
        c = classify_phase(None)  # type: ignore[arg-type]
        assert c.phase == "general"

    def test_handoff_keyword_takes_precedence_over_debug(self):
        # "debug" + "hand off" → handoff wins (higher precedence).
        c = classify_phase("debug the bug, then hand off the rest")
        assert c.phase == "handoff"

    def test_debug_verb_matches(self):
        c = classify_phase("debug the failing test")
        assert c.phase == "debugging"
        assert c.rule_name == "debug_verb"

    def test_review_verb_matches(self):
        c = classify_phase("review the implementation for bugs")
        assert c.phase == "review"
        assert c.rule_name == "review_verb"

    def test_implement_verb_matches(self):
        c = classify_phase("implement a new function for the test runner")
        assert c.phase == "implementation"
        assert c.rule_name == "implement_verb"

    def test_plan_verb_matches(self):
        c = classify_phase("plan the architecture for the new module")
        assert c.phase == "planning"
        assert c.rule_name == "plan_verb"

    def test_research_verb_matches(self):
        c = classify_phase("research how snapshot plugin works")
        assert c.phase == "research"
        assert c.rule_name == "research_verb"

    def test_curly_apostrophe_in_hand_off_still_matches(self):
        # The plan document says "verify" both straight (') and curly (')
        # apostrophes work. Regression test for that contract.
        c = classify_phase("I’ll hand off the rest to a subagent")
        assert c.phase == "handoff"

    def test_unmatched_prompt_returns_general(self):
        c = classify_phase("hello world")
        assert c.phase == "general"
        assert c.rule_name == "fallback"


class TestClassifyPhaseIsDeterministic:
    def test_same_input_same_output(self):
        a = classify_phase("implement a new test helper")
        b = classify_phase("implement a new test helper")
        assert a == b

    def test_result_is_frozen(self):
        c = classify_phase("review the plan")
        with pytest.raises(Exception):
            c.phase = "research"  # type: ignore[misc]


# ---- evaluate_health ------------------------------------------------------


class TestEvaluateHealthDataclassBranch:
    def test_zero_health_emits_no_hints(self):
        h = ContextHealth()
        a = evaluate_health(h, "general", None)
        assert a.should_compact is False
        assert a.should_start_fresh is False
        assert a.hints == ()

    def test_large_outputs_below_threshold_advises(self):
        h = ContextHealth(large_outputs=1)
        a = evaluate_health(h, "general", None)
        assert a.should_compact is False
        assert any("compact advisory" in hint for hint in a.hints)

    def test_large_outputs_at_threshold_sets_compact(self):
        h = ContextHealth(large_outputs=2)
        a = evaluate_health(h, "general", None)
        assert a.should_compact is True
        assert any(">= 2" in hint for hint in a.hints)

    def test_phase_turns_at_checkpoint_hints(self):
        h = ContextHealth(phase_turns=12)
        a = evaluate_health(h, "implementation", None)
        assert any(
            "12 turns" in hint and "consider transitioning" in hint
            for hint in a.hints
        )

    def test_phase_change_with_zero_phase_turns_sets_fresh(self):
        # phase_turns=0 right after a change = pivot mid-flight signal
        h = ContextHealth(turn_count=10, phase_turns=0)
        a = evaluate_health(h, "implementation", "research")
        assert a.should_start_fresh is True

    def test_fresh_phase_phase_turns_checkpoint_hints(self):
        # "research" is in FRESH_PHASE_CHECKPOINT_PHASES; phase_turns>0
        # but below PHASE_TURNS_CHECKPOINT → "checkpoint progress soon" hint
        h = ContextHealth(phase_turns=3)
        a = evaluate_health(h, "research", None)
        assert any("checkpoint progress" in hint for hint in a.hints)

    def test_hints_are_deduped(self):
        # If two rules produce the same hint, the list should not
        # contain duplicates (preserves the deduped invariant).
        h = ContextHealth(phase_turns=12, large_outputs=2)
        a = evaluate_health(h, "implementation", None)
        assert len(a.hints) == len(set(a.hints))


class TestEvaluateHealthDictBranch:
    """The Mapping branch is the on-disk shape of policy.json."""

    def test_dict_with_zero_values(self):
        d = {"turn_count": 0, "large_outputs": 0, "phase_turns": 0}
        a = evaluate_health(d, "general", None)
        assert a.hints == ()

    def test_dict_at_large_outputs_threshold(self):
        d = {"turn_count": 0, "large_outputs": 2, "phase_turns": 0}
        a = evaluate_health(d, "general", None)
        assert a.should_compact is True

    def test_dict_with_phase_change(self):
        d = {"turn_count": 5, "large_outputs": 0, "phase_turns": 0}
        a = evaluate_health(d, "implementation", "research")
        assert a.should_start_fresh is True

    def test_dict_with_no_previous_phase(self):
        # previous_phase=None should NOT set should_start_fresh
        d = {"turn_count": 5, "large_outputs": 0, "phase_turns": 0}
        a = evaluate_health(d, "general", None)
        assert a.should_start_fresh is False


# ---- recommend_subagent ---------------------------------------------------


class TestRecommendSubagent:
    def test_empty_returns_false(self):
        assert recommend_subagent("") is False

    def test_none_returns_false(self):
        assert recommend_subagent(None) is False  # type: ignore[arg-type]

    def test_investigate_returns_true(self):
        assert recommend_subagent("investigate the failing test") is True

    def test_trace_returns_true(self):
        assert recommend_subagent("trace the call graph") is True

    def test_find_all_references_returns_true(self):
        assert recommend_subagent("find all references to X") is True

    def test_map_call_graph_returns_true(self):
        assert recommend_subagent("map the call graph") is True

    def test_compare_across_returns_true(self):
        assert recommend_subagent("compare across all modules") is True

    def test_refactor_class_returns_true(self):
        assert recommend_subagent("refactor the class to be smaller") is True

    def test_debug_returns_true(self):
        # "debug" is in the pattern list.
        assert recommend_subagent("debug the bug") is True

    def test_implement_returns_false(self):
        # implementation is in our phase list, not the subagent hint list.
        assert recommend_subagent("implement a new helper") is False

    def test_review_returns_false(self):
        # review is not in the subagent hint list.
        assert recommend_subagent("review the code for bugs") is False


# ---- HealthAssessment dataclass -------------------------------------------


class TestHealthAssessmentDataclass:
    def test_construction(self):
        a = HealthAssessment(
            should_compact=True,
            should_start_fresh=False,
            hints=("hint 1", "hint 2"),
        )
        assert a.should_compact is True
        assert a.should_start_fresh is False
        assert a.hints == ("hint 1", "hint 2")

    def test_frozen(self):
        a = HealthAssessment(should_compact=False, should_start_fresh=False, hints=())
        with pytest.raises(Exception):
            a.should_compact = True  # type: ignore[misc]


# ---- PhaseClassification dataclass ---------------------------------------


class TestPhaseClassificationDataclass:
    def test_construction(self):
        c = PhaseClassification(
            phase="research", rule_name="research_verb", matched_text="research how"
        )
        assert c.phase == "research"
        assert c.rule_name == "research_verb"
        assert c.matched_text == "research how"

    def test_frozen(self):
        c = PhaseClassification(phase="general", rule_name="fallback", matched_text="")
        with pytest.raises(Exception):
            c.phase = "research"  # type: ignore[misc]

    def test_equality(self):
        a = PhaseClassification(phase="research", rule_name="x", matched_text="y")
        b = PhaseClassification(phase="research", rule_name="x", matched_text="y")
        assert a == b
