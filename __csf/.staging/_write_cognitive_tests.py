#!/usr/bin/env python3
"""Write test_cognitive_enhancers.py to the hooks/tests directory."""

from pathlib import Path

TEST_FILE = Path("P:/.claude/hooks/tests/test_cognitive_enhancers.py")

CONTENT = r'''#!/usr/bin/env python3
"""
Tests for Cognitive Enhancers - UserPromptSubmit Hooks
======================================================

Tests all 6 cognitive enhancers:
1. assumption_surfacing  - Surface unstated assumptions
2. outcome_anchoring     - Define "done" before starting
3. inversion_prompting   - "What would make this fail?"
4. chestertons_fence     - Understand existing code before changing
5. calibrated_confidence - Force confidence labeling on claims
6. socratic_decomposition- Break vague mega-prompts into sub-questions
"""

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add hooks directories to path
HOOKS_DIR = Path(__file__).resolve().parent.parent
USERPROMPT_DIR = HOOKS_DIR / "UserPromptSubmit"
sys.path.insert(0, str(HOOKS_DIR))
sys.path.insert(0, str(USERPROMPT_DIR))

from UserPromptSubmit.base import HookContext, HookResult
from UserPromptSubmit.cognitive_enhancers import (
    assumption_surfacing,
    outcome_anchoring,
    inversion_prompting,
    chestertons_fence,
    calibrated_confidence,
    socratic_decomposition,
    _is_actionable_prompt,
    _has_impl_intent,
    _has_modify_intent,
    _has_plan_or_impl_intent,
    _has_diagnostic_or_impl_intent,
    _is_vague_long_prompt,
    _extract_skill_name,
    _load_config,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _ctx(prompt: str) -> HookContext:
    """Create a HookContext with the given prompt."""
    return HookContext(prompt=prompt, data={})


def _enabled_config(**overrides):
    """Return a fully-enabled config with optional overrides."""
    cfg = {
        "enabled": True,
        "assumption_surfacing": True,
        "outcome_anchoring": True,
        "inversion_prompting": True,
        "chestertons_fence": True,
        "calibrated_confidence": True,
        "socratic_decomposition": True,
        "socratic_min_length": 200,
        "min_prompt_length": 30,
        "enhance_skills": True,
        "skip_skills": ["commit", "push", "search", "help"],
    }
    cfg.update(overrides)
    return cfg


# ---------------------------------------------------------------------------
# Helper function tests
# ---------------------------------------------------------------------------

class TestExtractSkillName:
    """Tests for _extract_skill_name."""

    def test_slash_command(self):
        assert _extract_skill_name("/commit fix things") == "commit"

    def test_slash_command_no_args(self):
        assert _extract_skill_name("/help") == "help"

    def test_not_slash_command(self):
        assert _extract_skill_name("build a new feature") is None

    def test_empty_string(self):
        assert _extract_skill_name("") is None

    def test_slash_with_leading_space(self):
        assert _extract_skill_name("  /test run all") == "test"


class TestIsActionablePrompt:
    """Tests for _is_actionable_prompt."""

    def test_too_short(self):
        cfg = _enabled_config()
        assert _is_actionable_prompt("hi", cfg) is False

    def test_question_only_no_impl(self):
        cfg = _enabled_config()
        assert _is_actionable_prompt("What is Python?", cfg) is False

    def test_question_with_impl(self):
        cfg = _enabled_config()
        assert _is_actionable_prompt("How do I build a REST API?", cfg) is True

    def test_impl_statement(self):
        cfg = _enabled_config()
        assert _is_actionable_prompt("Build a new authentication module for the app", cfg) is True

    def test_blacklisted_skill(self):
        cfg = _enabled_config()
        assert _is_actionable_prompt("/commit fix the bug", cfg) is False

    def test_non_blacklisted_skill(self):
        cfg = _enabled_config()
        assert _is_actionable_prompt("/refactor extract the auth module", cfg) is True

    def test_skills_disabled(self):
        cfg = _enabled_config(enhance_skills=False)
        assert _is_actionable_prompt("/refactor extract the auth module", cfg) is False


class TestIntentDetection:
    """Tests for intent detection helpers."""

    def test_impl_intent_build(self):
        assert _has_impl_intent("build a new feature") is True

    def test_impl_intent_create(self):
        assert _has_impl_intent("create the authentication module") is True

    def test_impl_intent_negative(self):
        assert _has_impl_intent("what is a database?") is False

    def test_modify_intent_refactor(self):
        assert _has_modify_intent("refactor the login flow") is True

    def test_modify_intent_update(self):
        assert _has_modify_intent("update the config handler") is True

    def test_modify_intent_negative(self):
        assert _has_modify_intent("build a new feature") is False

    def test_plan_or_impl_plan(self):
        assert _has_plan_or_impl_intent("plan the architecture for the API") is True

    def test_plan_or_impl_build(self):
        assert _has_plan_or_impl_intent("build the authentication system") is True

    def test_plan_or_impl_negative(self):
        assert _has_plan_or_impl_intent("what is a database?") is False

    def test_diagnostic_debug(self):
        assert _has_diagnostic_or_impl_intent("debug the auth failure") is True

    def test_diagnostic_investigate(self):
        assert _has_diagnostic_or_impl_intent("investigate why tests fail") is True

    def test_diagnostic_why(self):
        assert _has_diagnostic_or_impl_intent("why does the server crash?") is True

    def test_diagnostic_plan(self):
        assert _has_diagnostic_or_impl_intent("plan the migration strategy") is True

    def test_diagnostic_negative(self):
        assert _has_diagnostic_or_impl_intent("what is Python?") is False


class TestIsVagueLongPrompt:
    """Tests for _is_vague_long_prompt (Socratic trigger)."""

    def test_short_prompt(self):
        cfg = _enabled_config()
        assert _is_vague_long_prompt("build a feature", cfg) is False

    def test_long_vague_prompt(self):
        cfg = _enabled_config()
        prompt = "I want to completely overhaul the way our application handles user sessions and authentication tokens across all microservices, making sure everything is backward compatible and properly tested with good error handling " * 2
        assert _is_vague_long_prompt(prompt, cfg) is True

    def test_long_specific_prompt(self):
        cfg = _enabled_config()
        prompt = "Refactor auth_handler.py to use JWT tokens instead of session cookies, update the middleware in middleware.py and ensure all tests in test_auth.py still pass " * 2
        # Contains file.ext references -> specific, not vague
        assert _is_vague_long_prompt(prompt, cfg) is False

    def test_long_with_line_ref(self):
        cfg = _enabled_config()
        prompt = "There's a bug around line 42 in the authentication module that causes the entire session management system to fail when tokens expire during concurrent requests " * 2
        assert _is_vague_long_prompt(prompt, cfg) is False

    def test_long_with_class_ref(self):
        cfg = _enabled_config()
        prompt = "The class AuthHandler needs to be completely redesigned to support multiple authentication providers while maintaining backward compatibility with existing session management " * 2
        assert _is_vague_long_prompt(prompt, cfg) is False


# ---------------------------------------------------------------------------
# Enhancer 1: Assumption Surfacing
# ---------------------------------------------------------------------------

class TestAssumptionSurfacing:
    """Tests for the assumption_surfacing hook."""

    def test_fires_on_impl_prompt(self):
        result = assumption_surfacing(_ctx("Build a new REST API endpoint for user management"))
        assert not result.is_empty()
        assert "Assumption Check" in result.context

    def test_skips_non_impl_prompt(self):
        result = assumption_surfacing(_ctx("What is a database index?"))
        assert result.is_empty()

    def test_skips_short_prompt(self):
        result = assumption_surfacing(_ctx("build"))
        assert result.is_empty()

    def test_skips_when_disabled(self):
        with patch("UserPromptSubmit.cognitive_enhancers._load_config",
                   return_value=_enabled_config(assumption_surfacing=False)):
            result = assumption_surfacing(_ctx("Build a new REST API endpoint for user management"))
            assert result.is_empty()

    def test_skips_when_globally_disabled(self):
        with patch("UserPromptSubmit.cognitive_enhancers._load_config",
                   return_value=_enabled_config(enabled=False)):
            result = assumption_surfacing(_ctx("Build a new REST API endpoint for user management"))
            assert result.is_empty()

    def test_priority(self):
        result = assumption_surfacing(_ctx("Build a new REST API endpoint for user management"))
        assert result.priority == 11.5


# ---------------------------------------------------------------------------
# Enhancer 2: Outcome Anchoring
# ---------------------------------------------------------------------------

class TestOutcomeAnchoring:
    """Tests for the outcome_anchoring hook."""

    def test_fires_on_impl_prompt(self):
        result = outcome_anchoring(_ctx("Build the authentication system for the new app"))
        assert not result.is_empty()
        assert "Outcome Anchor" in result.context

    def test_fires_on_plan_prompt(self):
        result = outcome_anchoring(_ctx("Plan the architecture for the microservices migration"))
        assert not result.is_empty()

    def test_skips_non_plan_non_impl(self):
        result = outcome_anchoring(_ctx("What is a database index?"))
        assert result.is_empty()

    def test_skips_short_prompt(self):
        result = outcome_anchoring(_ctx("plan"))
        assert result.is_empty()

    def test_skips_when_disabled(self):
        with patch("UserPromptSubmit.cognitive_enhancers._load_config",
                   return_value=_enabled_config(outcome_anchoring=False)):
            result = outcome_anchoring(_ctx("Plan the new architecture for the app"))
            assert result.is_empty()

    def test_priority(self):
        result = outcome_anchoring(_ctx("Build a new REST API endpoint for user management"))
        assert result.priority == 11.4


# ---------------------------------------------------------------------------
# Enhancer 3: Inversion Prompting
# ---------------------------------------------------------------------------

class TestInversionPrompting:
    """Tests for the inversion_prompting hook."""

    def test_fires_on_impl_prompt(self):
        result = inversion_prompting(_ctx("Implement the payment processing module for the store"))
        assert not result.is_empty()
        assert "Inversion Check" in result.context

    def test_skips_non_impl_prompt(self):
        result = inversion_prompting(_ctx("Explain how databases work for beginners"))
        assert result.is_empty()

    def test_skips_when_disabled(self):
        with patch("UserPromptSubmit.cognitive_enhancers._load_config",
                   return_value=_enabled_config(inversion_prompting=False)):
            result = inversion_prompting(_ctx("Implement the payment processing module"))
            assert result.is_empty()

    def test_priority(self):
        result = inversion_prompting(_ctx("Build a new REST API endpoint for user management"))
        assert result.priority == 11.6


# ---------------------------------------------------------------------------
# Enhancer 4: Chesterton's Fence
# ---------------------------------------------------------------------------

class TestChestertonsFence:
    """Tests for the chestertons_fence hook."""

    def test_fires_on_modify_prompt(self):
        result = chestertons_fence(_ctx("Refactor the authentication handler to use JWT tokens"))
        assert not result.is_empty()
        assert "Chesterton" in result.context

    def test_fires_on_update(self):
        result = chestertons_fence(_ctx("Update the config parser to support YAML format"))
        assert not result.is_empty()

    def test_fires_on_fix(self):
        result = chestertons_fence(_ctx("Fix the broken session handling in the middleware"))
        assert not result.is_empty()

    def test_skips_new_build(self):
        result = chestertons_fence(_ctx("Build a brand new logging module from scratch"))
        assert result.is_empty()

    def test_skips_non_modify(self):
        result = chestertons_fence(_ctx("What is a REST API design pattern?"))
        assert result.is_empty()

    def test_skips_when_disabled(self):
        with patch("UserPromptSubmit.cognitive_enhancers._load_config",
                   return_value=_enabled_config(chestertons_fence=False)):
            result = chestertons_fence(_ctx("Refactor the auth handler"))
            assert result.is_empty()

    def test_priority(self):
        result = chestertons_fence(_ctx("Refactor the authentication handler to use JWT tokens"))
        assert result.priority == 11.7


# ---------------------------------------------------------------------------
# Enhancer 5: Calibrated Confidence
# ---------------------------------------------------------------------------

class TestCalibratedConfidence:
    """Tests for the calibrated_confidence hook."""

    def test_fires_on_diagnostic_prompt(self):
        result = calibrated_confidence(_ctx("Debug why the authentication is failing intermittently"))
        assert not result.is_empty()
        assert "Calibrated Confidence" in result.context

    def test_fires_on_impl_prompt(self):
        result = calibrated_confidence(_ctx("Build the new caching layer for the API endpoints"))
        assert not result.is_empty()

    def test_fires_on_plan_prompt(self):
        result = calibrated_confidence(_ctx("Plan the architecture for the new microservice"))
        assert not result.is_empty()

    def test_fires_on_investigate(self):
        result = calibrated_confidence(_ctx("Investigate the root cause of the memory leak issue"))
        assert not result.is_empty()

    def test_skips_simple_question(self):
        result = calibrated_confidence(_ctx("What is a database index used for?"))
        assert result.is_empty()

    def test_skips_when_disabled(self):
        with patch("UserPromptSubmit.cognitive_enhancers._load_config",
                   return_value=_enabled_config(calibrated_confidence=False)):
            result = calibrated_confidence(_ctx("Debug the auth failure"))
            assert result.is_empty()

    def test_priority(self):
        result = calibrated_confidence(_ctx("Debug why the authentication is failing intermittently"))
        assert result.priority == 11.8


# ---------------------------------------------------------------------------
# Enhancer 6: Socratic Decomposition
# ---------------------------------------------------------------------------

class TestSocraticDecomposition:
    """Tests for the socratic_decomposition hook."""

    def test_fires_on_vague_long_prompt(self):
        prompt = ("I want to completely overhaul the way our application handles "
                  "user sessions and authentication tokens across all microservices, "
                  "making sure everything is backward compatible and properly tested "
                  "with good error handling and logging throughout the entire stack")
        result = socratic_decomposition(_ctx(prompt))
        assert not result.is_empty()
        assert "Decompose First" in result.context

    def test_skips_short_prompt(self):
        result = socratic_decomposition(_ctx("Build a login page for the app"))
        assert result.is_empty()

    def test_skips_specific_long_prompt(self):
        prompt = ("Refactor auth_handler.py to use JWT tokens instead of session cookies, "
                  "update the middleware in middleware.py and ensure all tests in "
                  "test_auth.py still pass with the new token-based approach and "
                  "proper error handling for expired tokens in the validation layer")
        result = socratic_decomposition(_ctx(prompt))
        assert result.is_empty()

    def test_skips_when_disabled(self):
        long_vague = "I want to " + "completely redesign the system " * 20
        with patch("UserPromptSubmit.cognitive_enhancers._load_config",
                   return_value=_enabled_config(socratic_decomposition=False)):
            result = socratic_decomposition(_ctx(long_vague))
            assert result.is_empty()

    def test_custom_min_length(self):
        prompt = "Build a new feature with good tests"  # 36 chars, over 30 min_prompt
        with patch("UserPromptSubmit.cognitive_enhancers._load_config",
                   return_value=_enabled_config(socratic_min_length=30)):
            result = socratic_decomposition(_ctx(prompt))
            # Still needs to be long AND vague — 36 chars is under default 200
            # With min_length=30, this IS long enough, but lacks vagueness check
            # Actually: it IS vague (no specific file refs) so it fires
            assert not result.is_empty()

    def test_priority(self):
        prompt = ("I want to completely overhaul the way our application handles "
                  "user sessions and authentication tokens across all microservices, "
                  "making sure everything is backward compatible and properly tested "
                  "with good error handling and logging throughout the entire stack")
        result = socratic_decomposition(_ctx(prompt))
        assert result.priority == 11.3


# ---------------------------------------------------------------------------
# Integration: Multiple enhancers on same prompt
# ---------------------------------------------------------------------------

class TestMultipleEnhancers:
    """Test that multiple enhancers fire correctly on overlapping prompts."""

    def test_impl_triggers_assumption_outcome_inversion_confidence(self):
        prompt = "Build a new caching layer for the authentication API service"
        results = {
            "assumption": assumption_surfacing(_ctx(prompt)),
            "outcome": outcome_anchoring(_ctx(prompt)),
            "inversion": inversion_prompting(_ctx(prompt)),
            "confidence": calibrated_confidence(_ctx(prompt)),
        }
        for name, result in results.items():
            assert not result.is_empty(), f"{name} should fire on impl prompt"

    def test_modify_triggers_fence_and_confidence(self):
        prompt = "Refactor the session handler to support distributed caching"
        fence = chestertons_fence(_ctx(prompt))
        confidence = calibrated_confidence(_ctx(prompt))
        assert not fence.is_empty()
        assert not confidence.is_empty()

    def test_modify_does_not_trigger_fence_on_pure_build(self):
        prompt = "Create a brand new metrics dashboard from scratch please"
        fence = chestertons_fence(_ctx(prompt))
        assert fence.is_empty()

    def test_priority_ordering(self):
        """Verify priority order: socratic < outcome < assumption < inversion < fence < confidence."""
        prompt = ("Refactor the entire authentication and session management system "
                  "across all services to use JWT with proper error handling and tests "
                  "and make sure backward compatibility is maintained throughout") * 2
        results = [
            socratic_decomposition(_ctx(prompt)),
            outcome_anchoring(_ctx(prompt)),
            assumption_surfacing(_ctx(prompt)),
            inversion_prompting(_ctx(prompt)),
            chestertons_fence(_ctx(prompt)),
            calibrated_confidence(_ctx(prompt)),
        ]
        priorities = [r.priority for r in results if not r.is_empty()]
        assert priorities == sorted(priorities), f"Priorities not in order: {priorities}"


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------

class TestConfigLoading:
    """Tests for configuration loading."""

    def test_default_config_all_enabled(self):
        cfg = _enabled_config()
        assert cfg["enabled"] is True
        assert cfg["assumption_surfacing"] is True
        assert cfg["calibrated_confidence"] is True
        assert cfg["socratic_decomposition"] is True

    def test_global_disable(self):
        """When enabled=False, all enhancers should be silent."""
        with patch("UserPromptSubmit.cognitive_enhancers._load_config",
                   return_value=_enabled_config(enabled=False)):
            prompt = "Build a new REST API and refactor the auth module"
            assert assumption_surfacing(_ctx(prompt)).is_empty()
            assert outcome_anchoring(_ctx(prompt)).is_empty()
            assert inversion_prompting(_ctx(prompt)).is_empty()
            assert chestertons_fence(_ctx(prompt)).is_empty()
            assert calibrated_confidence(_ctx(prompt)).is_empty()
            assert socratic_decomposition(_ctx(prompt + " " * 200)).is_empty()


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    """Edge case tests."""

    def test_empty_prompt(self):
        assert assumption_surfacing(_ctx("")).is_empty()
        assert outcome_anchoring(_ctx("")).is_empty()
        assert inversion_prompting(_ctx("")).is_empty()
        assert chestertons_fence(_ctx("")).is_empty()
        assert calibrated_confidence(_ctx("")).is_empty()
        assert socratic_decomposition(_ctx("")).is_empty()

    def test_none_prompt(self):
        ctx = HookContext(prompt=None, data={})
        assert assumption_surfacing(ctx).is_empty()
        assert outcome_anchoring(ctx).is_empty()

    def test_whitespace_only(self):
        assert assumption_surfacing(_ctx("   ")).is_empty()

    def test_hookresult_empty(self):
        r = HookResult.empty()
        assert r.is_empty()
        assert r.context is None
        assert r.tokens == 0

    def test_hookresult_with_context(self):
        r = HookResult(context="test", tokens=1)
        assert not r.is_empty()
        assert r.context == "test"
'''

TEST_FILE.parent.mkdir(parents=True, exist_ok=True)
TEST_FILE.write_text(CONTENT.lstrip(), encoding="utf-8")
print(f"Written: {TEST_FILE} ({TEST_FILE.stat().st_size} bytes)")
