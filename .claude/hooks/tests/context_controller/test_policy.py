"""Tests for context_controller.policy.

Verifies the v1 deterministic contract:
- classify_phase uses the documented precedence order.
- classify_phase returns the fallback for empty / unmatched prompts.
- evaluate_health produces booleans that match the documented decision rules.
- evaluate_health accepts both ContextHealth and Mapping inputs.
- evaluate_health dedupes hints while preserving order.
- recommend_subagent matches the narrow keyword set; v1 is advisory only.

No I/O, no LLM calls. Pure functions; the only "state" is the constants
in the module under test.
"""

from __future__ import annotations

import pytest

from context_controller import policy as policy_mod
from context_controller import state as state_mod


# ---------------------------------------------------------------------------
# classify_phase — precedence and fallback
# ---------------------------------------------------------------------------


def test_classify_phase_falls_back_for_empty_prompt() -> None:
    result = policy_mod.classify_phase("")
    assert result.phase == "general"
    assert result.rule_name == "fallback"
    assert result.matched_text == ""


def test_classify_phase_falls_back_for_whitespace_only() -> None:
    result = policy_mod.classify_phase("   \n\t  ")
    assert result.phase == "general"
    assert result.rule_name == "fallback"


def test_classify_phase_falls_back_for_unmatched_prompt() -> None:
    """A prompt with no phase keywords still classifies as general."""
    result = policy_mod.classify_phase("thanks, looks good")
    assert result.phase == "general"
    assert result.rule_name == "fallback"


def test_classify_phase_handoff_wins_over_all_other_rules() -> None:
    """The handoff rule has the highest precedence — even if the prompt
    also contains implementation or research keywords, handoff wins."""
    result = policy_mod.classify_phase(
        "please hand off and continue from the last session, "
        "then implement a new function"
    )
    assert result.phase == "handoff"
    assert result.rule_name == "handoff_keyword"


def test_classify_phase_debug_wins_over_review_and_implementation() -> None:
    result = policy_mod.classify_phase(
        "please debug the function and review the test"
    )
    assert result.phase == "debugging"
    assert result.rule_name == "debug_verb"


def test_classify_phase_review_wins_over_implementation() -> None:
    result = policy_mod.classify_phase("review the implementation")
    assert result.phase == "review"


def test_classify_phase_implementation_matches_verb_object_pairs() -> None:
    result = policy_mod.classify_phase("implement a new helper function")
    assert result.phase == "implementation"


def test_classify_phase_planning_matches_plan_verb() -> None:
    result = policy_mod.classify_phase("let's plan the design")
    assert result.phase == "planning"


def test_classify_phase_research_matches_research_verb() -> None:
    result = policy_mod.classify_phase("research the existing implementation")
    assert result.phase == "research"


def test_classify_phase_is_case_insensitive() -> None:
    """Pattern flag is re.IGNORECASE; case must not change the verdict."""
    a = policy_mod.classify_phase("IMPLEMENT a new function")
    b = policy_mod.classify_phase("implement a new function")
    c = policy_mod.classify_phase("Implement A New Function")
    assert a.phase == b.phase == c.phase == "implementation"


def test_classify_phase_returns_frozen_dataclass() -> None:
    """PhaseClassification is frozen for hashability; mutation must raise."""
    result = policy_mod.classify_phase("implement a function")
    with pytest.raises((AttributeError, Exception)):
        result.phase = "review"  # type: ignore[misc]


def test_classify_phase_returns_matched_text() -> None:
    """The renderer uses ``matched_text`` to show *why* a phase was chosen."""
    result = policy_mod.classify_phase("please debug the bug")
    assert "debug" in result.matched_text.lower()


# ---------------------------------------------------------------------------
# evaluate_health — decision rules and hint ordering
# ---------------------------------------------------------------------------


def test_evaluate_health_no_flags_for_default_counters() -> None:
    health = state_mod.ContextHealth()
    a = policy_mod.evaluate_health(health, current_phase="general", previous_phase=None)
    assert a.should_compact is False
    assert a.should_start_fresh is False
    assert a.hints == ()


def test_evaluate_health_should_compact_at_threshold() -> None:
    """large_outputs >= LARGE_OUTPUTS_COMPACT trips should_compact."""
    health = state_mod.ContextHealth(large_outputs=policy_mod.LARGE_OUTPUTS_COMPACT)
    a = policy_mod.evaluate_health(health, current_phase="general", previous_phase=None)
    assert a.should_compact is True
    assert any("compact" in h.lower() for h in a.hints)


def test_evaluate_health_should_compact_above_threshold() -> None:
    health = state_mod.ContextHealth(
        large_outputs=policy_mod.LARGE_OUTPUTS_COMPACT + 5
    )
    a = policy_mod.evaluate_health(health, current_phase="general", previous_phase=None)
    assert a.should_compact is True


def test_evaluate_health_advisory_only_below_threshold() -> None:
    """1 large output: no compact, but a hint is emitted."""
    health = state_mod.ContextHealth(large_outputs=1)
    a = policy_mod.evaluate_health(health, current_phase="general", previous_phase=None)
    assert a.should_compact is False
    assert any("large output" in h.lower() for h in a.hints)


def test_evaluate_health_should_start_fresh_only_on_phase_change_with_nonzero_turns(
    tmp_path,
) -> None:
    """Phase change + phase_turns==0 + turn_count>0 = should_start_fresh.

    The phase_turns==0 means update_policy_state already reset the
    counter; the user pivoted after some work."""
    health = state_mod.ContextHealth(turn_count=5, phase_turns=0)
    a = policy_mod.evaluate_health(
        health, current_phase="research", previous_phase="implementation"
    )
    assert a.should_start_fresh is True
    assert any("phase changed" in h.lower() for h in a.hints)


def test_evaluate_health_no_fresh_on_first_turn() -> None:
    """previous_phase=None means fresh session — no should_start_fresh signal."""
    health = state_mod.ContextHealth(turn_count=0, phase_turns=0)
    a = policy_mod.evaluate_health(
        health, current_phase="research", previous_phase=None
    )
    assert a.should_start_fresh is False


def test_evaluate_health_no_fresh_when_phase_turns_not_zero(tmp_path) -> None:
    """If phase_turns is nonzero, the phase hasn't been reset — not a pivot."""
    health = state_mod.ContextHealth(turn_count=5, phase_turns=3)
    a = policy_mod.evaluate_health(
        health, current_phase="research", previous_phase="implementation"
    )
    assert a.should_start_fresh is False


def test_evaluate_health_phase_turns_checkpoint_emits_hint(tmp_path) -> None:
    health = state_mod.ContextHealth(phase_turns=policy_mod.PHASE_TURNS_CHECKPOINT)
    a = policy_mod.evaluate_health(
        health, current_phase="implementation", previous_phase=None
    )
    assert any("phase" in h.lower() and "turns" in h.lower() for h in a.hints)


def test_evaluate_health_long_running_phase_emits_hint(tmp_path) -> None:
    """Phases in FRESH_PHASE_CHECKPOINT_PHASES get a hint at any
    nonzero phase_turns count."""
    health = state_mod.ContextHealth(phase_turns=2)
    a = policy_mod.evaluate_health(
        health, current_phase="research", previous_phase=None
    )
    assert any("checkpoint" in h.lower() or "long-running" in h.lower() for h in a.hints)


def test_evaluate_health_accepts_mapping_input(tmp_path) -> None:
    """Mapping fallback for callers that already have a dict."""
    health_dict = {
        "turn_count": 0,
        "large_outputs": policy_mod.LARGE_OUTPUTS_COMPACT,
        "phase_turns": 0,
    }
    a = policy_mod.evaluate_health(
        health_dict, current_phase="general", previous_phase=None
    )
    assert a.should_compact is True


def test_evaluate_health_accepts_partial_mapping(tmp_path) -> None:
    """Missing keys default to 0; the function never raises."""
    a = policy_mod.evaluate_health(
        {"turn_count": 1}, current_phase="general", previous_phase=None
    )
    assert a.should_compact is False


def test_evaluate_health_dedupes_hints_preserving_order(tmp_path) -> None:
    """The compact-trigger and phase-changed hints must appear at most once
    each, in the order they were appended."""
    health = state_mod.ContextHealth(
        large_outputs=policy_mod.LARGE_OUTPUTS_COMPACT,
        phase_turns=0,
        turn_count=5,
    )
    a = policy_mod.evaluate_health(
        health, current_phase="research", previous_phase="implementation"
    )
    # No hint appears twice
    assert len(a.hints) == len(set(a.hints))
    # Order is stable across calls
    b = policy_mod.evaluate_health(
        health, current_phase="research", previous_phase="implementation"
    )
    assert a.hints == b.hints


# ---------------------------------------------------------------------------
# recommend_subagent — narrow keyword set, advisory only
# ---------------------------------------------------------------------------


def test_recommend_subagent_false_for_empty_prompt() -> None:
    assert policy_mod.recommend_subagent("") is False
    assert policy_mod.recommend_subagent("   ") is False


def test_recommend_subagent_true_for_investigate() -> None:
    assert policy_mod.recommend_subagent("investigate the bug") is True


def test_recommend_subagent_true_for_trace() -> None:
    assert policy_mod.recommend_subagent("trace the call through the cache") is True


def test_recommend_subagent_true_for_find_all_uses() -> None:
    assert policy_mod.recommend_subagent("find all uses of this function") is True


def test_recommend_subagent_true_for_map_call_graph() -> None:
    assert policy_mod.recommend_subagent("map the call graph") is True


def test_recommend_subagent_false_for_unrelated_prompts() -> None:
    """The intent is narrow: the controller is advisory, false negatives
    are worse than false positives, so we only match a tight set."""
    assert policy_mod.recommend_subagent("implement a function") is False
    assert policy_mod.recommend_subagent("review the code") is False
    assert policy_mod.recommend_subagent("plan the design") is False


def test_recommend_subagent_is_case_insensitive() -> None:
    a = policy_mod.recommend_subagent("INVESTIGATE the bug")
    b = policy_mod.recommend_subagent("investigate the bug")
    assert a is True
    assert b is True
