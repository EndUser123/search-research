"""Tests for the THINK trigger hook — auto-detection only."""
from __future__ import annotations

import sys
from pathlib import Path

# Add parent package to path so we can import as a package
_hooks_dir = Path(__file__).parent.parent.parent
if str(_hooks_dir) not in sys.path:
    sys.path.insert(0, str(_hooks_dir))

from UserPromptSubmit.base import HookContext
from UserPromptSubmit.think_trigger import (
    _PROFILES,
    _detect_profile,
)

# === Profile template tests ===

class TestProfiles:
    def test_debug_rca_has_5_whys(self):
        assert "5 Whys" in _PROFILES["debug_rca"]
        assert "Why #1" in _PROFILES["debug_rca"]

    def test_tradeoff_has_decision_frame(self):
        assert "Decision frame" in _PROFILES["tradeoff_decision"]
        assert "Inversion" in _PROFILES["tradeoff_decision"]

    def test_architecture_has_cynefin(self):
        assert "Cynefin" in _PROFILES["architecture"]
        assert "Chesterton" in _PROFILES["architecture"]

    def test_pre_commit_risk_has_time_horizons(self):
        template = _PROFILES["pre_commit_risk"]
        assert "Immediate" in template
        assert "Short-term" in template
        assert "Medium-term" in template
        assert "Reversibility" in template

    def test_all_four_profiles_exist(self):
        expected = {"debug_rca", "tradeoff_decision", "architecture", "pre_commit_risk"}
        assert set(_PROFILES.keys()) == expected


# === Auto-detection tests ===

class TestDetectProfile:
    def test_no_keywords_returns_none(self):
        assert _detect_profile("just fix the button color") is None

    def test_single_weak_keyword_not_enough(self):
        # "error" is weak — needs 2+ weak keywords to trigger
        assert _detect_profile("there is an error in the output") is None

    def test_short_prompt_rejected(self):
        assert _detect_profile("bug crash") is None  # < 10 chars

    # --- Strong keyword triggers (1 match enough) ---

    def test_strong_flaky_triggers_alone(self):
        assert _detect_profile("the test is flaky sometimes") == "debug_rca"

    def test_strong_regression_triggers_alone(self):
        assert _detect_profile("this looks like a regression from last week") == "debug_rca"

    def test_strong_not_working_triggers_alone(self):
        assert _detect_profile("the login page is not working anymore") == "debug_rca"

    def test_strong_traceback_triggers_alone(self):
        assert _detect_profile("I got a traceback when running the script") == "debug_rca"

    def test_strong_vs_triggers_tradeoff(self):
        assert _detect_profile("Redis vs Memcached for the cache layer") == "tradeoff_decision"

    def test_strong_should_we_use_triggers_tradeoff(self):
        assert _detect_profile("should we use SQLite or Postgres here?") == "tradeoff_decision"

    def test_strong_monolith_triggers_architecture(self):
        assert _detect_profile("should we keep the monolith or split up?") == "architecture"

    def test_strong_microservice_triggers_architecture(self):
        assert _detect_profile("thinking about converting to a microservice") == "architecture"

    def test_strong_decompose_triggers_architecture(self):
        assert _detect_profile("we need to decompose this into smaller parts") == "architecture"

    def test_strong_push_to_main_triggers_risk(self):
        assert _detect_profile("ready to push to main with these changes") == "pre_commit_risk"

    def test_strong_breaking_change_triggers_risk(self):
        assert _detect_profile("this is a breaking change in the API") == "pre_commit_risk"

    def test_strong_rollback_triggers_risk(self):
        assert _detect_profile("we might need to rollback if this fails") == "pre_commit_risk"

    # --- Weak keyword pairs (2+ needed) ---

    def test_two_weak_error_and_crash(self):
        assert _detect_profile("there was an error and then it crashed") == "debug_rca"

    def test_two_weak_broken_and_failing(self):
        assert _detect_profile("this is broken and the tests are failing") == "debug_rca"

    def test_two_weak_deploy_and_production(self):
        assert _detect_profile("we need to deploy this to production soon") == "pre_commit_risk"

    def test_two_weak_release_and_risky(self):
        assert _detect_profile("this release looks risky to me") == "pre_commit_risk"

    # --- Multi-keyword (strong + weak combos) ---

    def test_debug_rca_strong_plus_weak(self):
        assert _detect_profile("the test is flaky and keeps failing intermittently") == "debug_rca"

    def test_debug_rca_error_and_traceback(self):
        assert _detect_profile("I got an error with this traceback in production") == "debug_rca"

    def test_debug_rca_broken_and_regression(self):
        assert _detect_profile("this is broken, looks like a regression from last week") == "debug_rca"

    def test_tradeoff_decision_option_keywords(self):
        assert _detect_profile("compare option a and option b for the database") == "tradeoff_decision"

    def test_tradeoff_which_is_better(self):
        assert _detect_profile("which is better: should we use SQLite or Postgres?") == "tradeoff_decision"

    def test_architecture_keywords(self):
        assert _detect_profile("should we split into microservice or keep the monolith?") == "architecture"

    def test_pre_commit_risk_deploy(self):
        assert _detect_profile("we are deploying the migration to production tonight") == "pre_commit_risk"

    def test_pre_commit_risk_release(self):
        assert _detect_profile("about to release with a breaking change in the API") == "pre_commit_risk"

    def test_pre_commit_push_to_main(self):
        assert _detect_profile("ready to push to main, this is a risky change") == "pre_commit_risk"

    def test_repeated_detection_works(self):
        result1 = _detect_profile("the test is flaky and keeps failing")
        assert result1 == "debug_rca"
        result2 = _detect_profile("another error with a traceback appeared")
        assert result2 == "debug_rca"

    def test_highest_score_wins(self):
        assert _detect_profile("the service is crashing with an error and a failure in logs") == "debug_rca"

    # --- False positive guards ---

    def test_normal_code_prompt_no_trigger(self):
        assert _detect_profile("add a new endpoint for user profiles") is None

    def test_normal_refactor_no_trigger(self):
        assert _detect_profile("rename the variable from x to user_count") is None

    def test_add_error_handling_no_trigger(self):
        assert _detect_profile("add error handling to this function") is None

    def test_deploy_script_no_trigger(self):
        assert _detect_profile("write a deploy script for the service") is None

    def test_production_config_no_trigger(self):
        assert _detect_profile("update the production config file") is None

    # --- Strong/weak keyword list integrity ---

    def test_strong_and_weak_dont_overlap(self):
        from UserPromptSubmit.think_trigger import _STRONG_KEYWORDS, _WEAK_KEYWORDS
        for profile in _STRONG_KEYWORDS:
            strong_set = set(_STRONG_KEYWORDS[profile])
            weak_set = set(_WEAK_KEYWORDS.get(profile, []))
            overlap = strong_set & weak_set
            assert not overlap, f"Profile {profile} has overlap: {overlap}"


# === Hook function integration tests ===

class TestThinkTriggerHook:
    def test_no_match_returns_empty(self):
        from UserPromptSubmit.think_trigger import think_trigger
        ctx = HookContext(prompt="just fix the bug", data={})
        result = think_trigger(ctx)
        assert result.is_empty()

    def test_auto_detect_debug_rca(self):
        from UserPromptSubmit.think_trigger import think_trigger
        ctx = HookContext(
            prompt="this keeps crashing with an error in the logs",
            data={},
        )
        result = think_trigger(ctx)
        assert not result.is_empty()
        assert "5 Whys" in result.context

    def test_auto_detect_tradeoff(self):
        from UserPromptSubmit.think_trigger import think_trigger
        ctx = HookContext(
            prompt="should we use Redis vs Memcached for this?",
            data={},
        )
        result = think_trigger(ctx)
        assert not result.is_empty()
        assert "Decision frame" in result.context

    def test_auto_detect_architecture(self):
        from UserPromptSubmit.think_trigger import think_trigger
        ctx = HookContext(
            prompt="should we decompose this monolith into services?",
            data={},
        )
        result = think_trigger(ctx)
        assert not result.is_empty()
        assert "Cynefin" in result.context

    def test_auto_detect_pre_commit_risk(self):
        from UserPromptSubmit.think_trigger import think_trigger
        ctx = HookContext(
            prompt="about to deploy this breaking change to production",
            data={},
        )
        result = think_trigger(ctx)
        assert not result.is_empty()
        assert "Pre-mortem" in result.context


# === Stemming tests — word form variants should match ===

class TestStemming:
    """Verify stemming patterns catch all word forms."""

    # debug_rca stemming
    def test_regression_singular(self):
        assert _detect_profile("there's a regression in the login flow") == "debug_rca"

    def test_regressions_plural(self):
        assert _detect_profile("we found multiple regressions after the update") == "debug_rca"

    def test_regressed(self):
        assert _detect_profile("the performance regressed significantly") == "debug_rca"

    def test_intermittently(self):
        assert _detect_profile("it intermittently fails during peak hours") == "debug_rca"

    # weak debug_rca stemming (need 2+)
    def test_weak_failures_and_errors(self):
        assert _detect_profile("seeing failures and errors in the pipeline") == "debug_rca"

    def test_weak_exceptions_and_bugs(self):
        assert _detect_profile("there are exceptions and bugs piling up") == "debug_rca"

    def test_weak_crashed_and_broke(self):
        assert _detect_profile("the server crashed and something broke") == "debug_rca"

    # architecture stemming
    def test_monolithic(self):
        assert _detect_profile("our monolithic app is getting too big") == "architecture"

    def test_microservices_plural(self):
        assert _detect_profile("should we migrate to microservices?") == "architecture"

    def test_decomposition(self):
        assert _detect_profile("let's discuss the decomposition of this module") == "architecture"

    def test_decoupling(self):
        assert _detect_profile("decoupling the frontend from the backend is critical") == "architecture"

    def test_service_boundaries(self):
        assert _detect_profile("we need to define service boundaries here") == "architecture"

    # pre_commit_risk stemming
    def test_deployed(self):
        assert _detect_profile("we deployed to production and it's broken") == "pre_commit_risk"

    def test_rollbacks(self):
        assert _detect_profile("how do we handle rollbacks for this?") == "pre_commit_risk"

    def test_migration_and_release(self):
        assert _detect_profile("the migration is part of the next release") == "pre_commit_risk"

    def test_shipping_and_risky(self):
        assert _detect_profile("shipping this feels risky, should we wait?") == "pre_commit_risk"

    # tradeoff_decision stemming
    def test_comparison(self):
        assert _detect_profile("let's do a comparison of the two approaches, which one is better?") == "tradeoff_decision"

    def test_evaluation(self):
        assert _detect_profile("we need an evaluation of the alternatives") == "tradeoff_decision"

    def test_choosing(self):
        assert _detect_profile("choosing between these options is hard, what approach works?") == "tradeoff_decision"

    # broader strong patterns
    def test_keeps_failing(self):
        assert _detect_profile("this keeps failing in CI every other run") == "debug_rca"

    def test_keeps_breaking(self):
        assert _detect_profile("the build keeps breaking after merges") == "debug_rca"

    def test_why_doesnt(self):
        assert _detect_profile("why doesn't this test pass anymore?") == "debug_rca"

    def test_why_wont(self):
        assert _detect_profile("why won't the server start in development?") == "debug_rca"

    def test_going_live(self):
        assert _detect_profile("we're going live with this tomorrow evening") == "pre_commit_risk"

    def test_before_shipping(self):
        assert _detect_profile("what should we check before shipping this?") == "pre_commit_risk"

    def test_pushing_to_master(self):
        assert _detect_profile("I'm about to start pushing to master now") == "pre_commit_risk"

    def test_extracting_a_service(self):
        assert _detect_profile("we're extracting a service from the monolith") == "architecture"


# === Code-span stripping tests ===

class TestCodeSpanStripping:
    """Verify backtick code spans are stripped before keyword matching."""

    def test_error_in_code_span_ignored(self):
        assert _detect_profile("fix the `handle_error()` function to return early") is None

    def test_exception_in_code_span_ignored(self):
        assert _detect_profile("refactor the `raise_exception()` helper method") is None

    def test_crash_in_code_span_ignored(self):
        assert _detect_profile("rename the `crash_reporter` module to diagnostics") is None

    def test_deploy_in_code_span_ignored(self):
        assert _detect_profile("update the `deploy_config` variable in settings") is None

    def test_real_keyword_outside_span_still_triggers(self):
        assert _detect_profile("the `test_helper()` test is flaky") == "debug_rca"

    def test_mixed_code_and_real_keywords(self):
        assert _detect_profile("the `error_handler` saw a crash and failure") == "debug_rca"

    def test_multiple_code_spans_stripped(self):
        assert _detect_profile("update `deploy_script` and `release_manager` modules") is None

    def test_code_span_with_strong_keyword_outside(self):
        assert _detect_profile("fix `utils.py` — there's a traceback in the logs") == "debug_rca"
