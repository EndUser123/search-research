"""Tests for the THINK trigger hook."""
from __future__ import annotations

import sys
from pathlib import Path

# Add parent package to path so we can import as a package
_hooks_dir = Path(__file__).resolve().parent.parent.parent
if str(_hooks_dir) not in sys.path:
    sys.path.insert(0, str(_hooks_dir))

from UserPromptSubmit.base import HookContext
from UserPromptSubmit.think_trigger import (
    _PROFILE_ALIASES,
    _PROFILES,
    _detect_profile,
    _parse_think,
)


def _context_text(result) -> str:
    """Return injected text across legacy/new HookResult shapes."""
    if isinstance(result.context, dict):
        return result.context.get("additionalContext", "")
    return result.context or ""

# === _parse_think tests ===

class TestParseThink:
    def test_no_think_returns_none(self):
        profile, remainder = _parse_think("just a normal prompt")
        assert profile is None
        assert remainder == "just a normal prompt"

    def test_bare_think_returns_quick(self):
        profile, remainder = _parse_think("THINK: what should I do here?")
        assert profile == "quick"
        assert remainder == "what should I do here?"

    def test_think_why_maps_to_debug_rca(self):
        profile, remainder = _parse_think("THINK WHY: why is this test flaky?")
        assert profile == "debug_rca"
        assert remainder == "why is this test flaky?"

    def test_think_debug_maps_to_debug_rca(self):
        profile, _ = _parse_think("THINK DEBUG: investigate the crash")
        assert profile == "debug_rca"

    def test_think_rca_maps_to_debug_rca(self):
        profile, _ = _parse_think("THINK RCA: find root cause")
        assert profile == "debug_rca"

    def test_think_decide_maps_to_tradeoff(self):
        profile, remainder = _parse_think("THINK DECIDE: option A vs B")
        assert profile == "tradeoff_decision"
        assert remainder == "option A vs B"

    def test_think_decision_maps_to_tradeoff(self):
        profile, _ = _parse_think("THINK DECISION: which approach?")
        assert profile == "tradeoff_decision"

    def test_think_arch_maps_to_architecture(self):
        profile, _ = _parse_think("THINK ARCH: should we split this service?")
        assert profile == "architecture"

    def test_think_architecture_maps_to_architecture(self):
        profile, _ = _parse_think("THINK ARCHITECTURE: monolith vs micro")
        assert profile == "architecture"

    def test_think_risk_maps_to_pre_commit(self):
        profile, remainder = _parse_think("THINK RISK: deploying the migration")
        assert profile == "pre_commit_risk"
        assert remainder == "deploying the migration"

    def test_think_premortem_maps_to_pre_commit(self):
        profile, _ = _parse_think("THINK PREMORTEM: what could go wrong")
        assert profile == "pre_commit_risk"

    def test_case_insensitive(self):
        profile, _ = _parse_think("think why: lowercase works")
        assert profile == "debug_rca"

    def test_mixed_case(self):
        profile, _ = _parse_think("Think Arch: mixed case")
        assert profile == "architecture"

    def test_no_colon(self):
        profile, remainder = _parse_think("THINK WHY something broke")
        assert profile == "debug_rca"
        assert remainder == "something broke"

    def test_leading_whitespace(self):
        profile, _ = _parse_think("  THINK RISK: deploy check")
        assert profile == "pre_commit_risk"

    def test_unknown_alias_defaults_to_quick(self):
        profile, _ = _parse_think("THINK BANANA: weird input")
        assert profile == "quick"

    def test_empty_string(self):
        profile, remainder = _parse_think("")
        assert profile is None
        assert remainder == ""

    def test_think_without_content(self):
        profile, remainder = _parse_think("THINK")
        assert profile == "quick"
        assert remainder == ""


# === Profile template tests ===

class TestProfiles:
    def test_all_aliases_map_to_valid_profiles(self):
        for alias, profile in _PROFILE_ALIASES.items():
            assert profile in _PROFILES, f"Alias {alias} maps to unknown profile {profile}"

    def test_quick_profile_exists(self):
        assert "quick" in _PROFILES
        assert "QUICK TRIAGE" in _PROFILES["quick"]

    def test_debug_rca_has_5_whys(self):
        assert "5 Whys" in _PROFILES["debug_rca"]
        assert "symptom -> mechanism -> upstream condition" in _PROFILES["debug_rca"]

    def test_tradeoff_has_decision_frame(self):
        assert "Compare 2 options plus the simplest fallback" in _PROFILES["tradeoff_decision"]
        assert "how to verify it" in _PROFILES["tradeoff_decision"]

    def test_architecture_has_cynefin(self):
        assert "Check the domain" in _PROFILES["architecture"]
        assert "rollback" in _PROFILES["architecture"]

    def test_pre_commit_risk_has_time_horizons(self):
        template = _PROFILES["pre_commit_risk"]
        assert "Assume this fails in 48 hours" in template
        assert "breakage" in template
        assert "reversibility" in template


# === Auto-detection tests ===

class TestDetectProfile:
    def test_no_keywords_returns_none(self):
        assert _detect_profile("just fix the button color") is None

    def test_single_keyword_not_enough(self):
        assert _detect_profile("there is an error in the output") is None

    def test_short_prompt_rejected(self):
        assert _detect_profile("bug crash") is None  # < 15 chars

    def test_meta_subject_prompt_uses_quick_not_debug(self):
        result = _detect_profile(
            "why did you use /think as the target of /think vs the topic in the chat that was actually the subject?"
        )
        assert result == "quick"

    def test_meta_subject_prompt_variants_use_quick(self):
        assert _detect_profile("what is /think doing here?") == "quick"
        assert _detect_profile("how should /think interpret the command context?") == "quick"
        assert _detect_profile("can /think distinguish the topic from the subject?") == "quick"

    def test_debug_rca_two_keywords(self):
        result = _detect_profile("the test is flaky and keeps failing intermittently")
        assert result == "debug_rca"

    def test_debug_rca_error_and_traceback(self):
        result = _detect_profile("I got an error with this traceback in production")
        assert result == "debug_rca"

    def test_debug_rca_broken_and_regression(self):
        result = _detect_profile("this is broken, looks like a regression from last week")
        assert result == "debug_rca"

    def test_tradeoff_decision_vs_keyword(self):
        result = _detect_profile("should we use Redis vs Memcached for the cache?")
        assert result == "tradeoff_decision"

    def test_tradeoff_decision_option_keywords(self):
        result = _detect_profile("compare option a and option b for the database")
        assert result == "tradeoff_decision"

    def test_tradeoff_which_is_better(self):
        result = _detect_profile("which is better: should we use SQLite or Postgres?")
        assert result == "tradeoff_decision"

    def test_architecture_keywords(self):
        result = _detect_profile("should we split into microservice or keep the monolith?")
        assert result == "architecture"

    def test_architecture_decompose(self):
        result = _detect_profile("we need to decompose this component and decouple the layers")
        assert result == "architecture"

    def test_pre_commit_risk_deploy(self):
        result = _detect_profile("we are deploying the migration to production tonight")
        assert result == "pre_commit_risk"

    def test_pre_commit_risk_release(self):
        result = _detect_profile("about to release with a breaking change in the API")
        assert result == "pre_commit_risk"

    def test_pre_commit_push_to_main(self):
        result = _detect_profile("ready to push to main, this is a risky change")
        assert result == "pre_commit_risk"

    def test_repeated_detection_works(self):
        # No cooldown — same profile should fire every time
        result1 = _detect_profile("the test is flaky and keeps failing")
        assert result1 == "debug_rca"
        result2 = _detect_profile("another error with a traceback appeared")
        assert result2 == "debug_rca"

    def test_highest_match_wins(self):
        result = _detect_profile("the service is crashing with an error and a failure in logs")
        assert result == "debug_rca"

    def test_normal_code_prompt_no_trigger(self):
        assert _detect_profile("add a new endpoint for user profiles") is None

    def test_normal_refactor_no_trigger(self):
        assert _detect_profile("rename the variable from x to user_count") is None


# === Hook function integration test ===

class TestThinkTriggerHook:
    def test_non_think_prompt_returns_empty(self):
        from UserPromptSubmit.think_trigger import think_trigger
        ctx = HookContext(prompt="just fix the bug", data={})
        result = think_trigger(ctx)
        assert result.is_empty()

    def test_think_why_injects_rca_template(self):
        from UserPromptSubmit.think_trigger import think_trigger
        ctx = HookContext(prompt="THINK WHY: test is flaky", data={})
        result = think_trigger(ctx)
        assert not result.is_empty()
        assert "5 Whys" in _context_text(result)

    def test_think_risk_injects_precommit_template(self):
        from UserPromptSubmit.think_trigger import think_trigger
        ctx = HookContext(prompt="THINK RISK: deploying migration", data={})
        result = think_trigger(ctx)
        assert not result.is_empty()
        assert "Assume this fails in 48 hours" in _context_text(result)

    def test_auto_detect_injects_template(self):
        from UserPromptSubmit.think_trigger import think_trigger
        ctx = HookContext(
            prompt="this keeps crashing with an error in the logs",
            data={},
        )
        result = think_trigger(ctx)
        assert not result.is_empty()
        assert "5 Whys" in _context_text(result)

    def test_explicit_think_still_works(self):
        from UserPromptSubmit.think_trigger import think_trigger
        ctx = HookContext(
            prompt="THINK RISK: checking before deploy",
            data={},
        )
        result = think_trigger(ctx)
        assert not result.is_empty()
        assert "Assume this fails in 48 hours" in _context_text(result)

    def test_auto_detect_tradeoff(self):
        from UserPromptSubmit.think_trigger import think_trigger
        ctx = HookContext(
            prompt="should we use Redis vs Memcached for this?",
            data={},
        )
        result = think_trigger(ctx)
        assert not result.is_empty()
        assert "Compare 2 options plus the simplest fallback" in _context_text(result)
