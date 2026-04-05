"""Tests for think_trigger.py integration with unified detection.

Tests the updated think_trigger hook that:
1. Uses unified_detection.detect_prompt() for pattern matching
2. Emits [THINK:profile_name] tags via tag_emission module
3. Maps UnifiedDetectionResult.matched_profiles to ThinkProfile selection
4. Maintains backward compatibility with all 7 profiles

Profiles tested:
1. debug_rca
2. tradeoff_decision
3. architecture
4. pre_commit_risk
5. security_review
6. performance_analysis
7. multi_file_refactor
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add parent package to path so we can import as a package
_hooks_dir = Path(__file__).resolve().parent.parent.parent
if str(_hooks_dir) not in sys.path:
    sys.path.insert(0, str(_hooks_dir))

from UserPromptSubmit.base import HookContext
from UserPromptSubmit.think_trigger import (
    _PROFILES,
    _detect_profile,
    think_trigger,
)


class TestDetectProfileUnified:
    """Test _detect_profile() uses unified detection correctly."""

    def test_no_keywords_returns_none(self):
        """Prompts without detection patterns should return None."""
        result = _detect_profile("just fix the button color")
        assert result is None

    def test_short_prompt_rejected(self):
        """Very short prompts should be rejected."""
        result = _detect_profile("bug")
        assert result is None

    def test_debug_rca_detection(self):
        """Debug RCA profile should match debugging prompts."""
        result = _detect_profile("the test is flaky and keeps failing intermittently")
        assert result == "debug_rca"

    def test_tradeoff_decision_detection(self):
        """Tradeoff decision profile should match comparison prompts."""
        result = _detect_profile("should we use Redis vs Memcached for the cache?")
        assert result == "tradeoff_decision"

    def test_architecture_detection(self):
        """Architecture profile should match system design prompts."""
        result = _detect_profile("should we split into microservice or keep the monolith?")
        assert result == "architecture"

    def test_pre_commit_risk_detection(self):
        """Pre-commit risk profile should match deployment prompts."""
        result = _detect_profile("we are deploying the migration to production tonight")
        assert result == "pre_commit_risk"

    def test_security_review_detection(self):
        """Security review profile should match security prompts."""
        result = _detect_profile("SQL injection vulnerability detected")
        assert result == "security_review"

    def test_performance_analysis_detection(self):
        """Performance analysis profile should match performance prompts."""
        result = _detect_profile("This query is really slow and needs optimization")
        assert result == "performance_analysis"

    def test_multi_file_refactor_detection(self):
        """Multi-file refactor profile should match refactoring prompts."""
        result = _detect_profile("Refactor this across multiple files")
        assert result == "multi_file_refactor"


class TestThinkTriggerHookIntegration:
    """Test think_trigger hook integrates with unified detection and emits tags."""

    def test_non_think_prompt_returns_empty(self):
        """Prompts without patterns should return empty result."""
        ctx = HookContext(prompt="just fix the bug", data={})
        result = think_trigger(ctx)
        assert result.is_empty()

    def test_debug_rca_injects_template_with_tag(self):
        """Debug RCA should inject template with [THINK:debug_rca] tag."""
        ctx = HookContext(prompt="this keeps crashing with an error", data={})
        result = think_trigger(ctx)

        assert not result.is_empty()
        assert "5 Whys" in result.context
        assert "[THINK:debug_rca]" in result.context

    def test_tradeoff_decision_injects_template_with_tag(self):
        """Tradeoff decision should inject template with [THINK:tradeoff_decision] tag."""
        ctx = HookContext(prompt="should we use Redis or Memcached?", data={})
        result = think_trigger(ctx)

        assert not result.is_empty()
        assert "Decision frame" in result.context
        assert "[THINK:tradeoff_decision]" in result.context

    def test_architecture_injects_template_with_tag(self):
        """Architecture should inject template with [THINK:architecture] tag."""
        ctx = HookContext(prompt="should we split into microservices?", data={})
        result = think_trigger(ctx)

        assert not result.is_empty()
        assert "Cynefin" in result.context
        assert "[THINK:architecture]" in result.context

    def test_pre_commit_risk_injects_template_with_tag(self):
        """Pre-commit risk should inject template with [THINK:pre_commit_risk] tag."""
        ctx = HookContext(prompt="about to deploy to production", data={})
        result = think_trigger(ctx)

        assert not result.is_empty()
        assert "Pre-mortem" in result.context
        assert "[THINK:pre_commit_risk]" in result.context

    def test_security_review_injects_template_with_tag(self):
        """Security review should inject template with [THINK:security_review] tag."""
        ctx = HookContext(prompt="fix the SQL injection vulnerability", data={})
        result = think_trigger(ctx)

        assert not result.is_empty()
        assert "OWASP" in result.context
        assert "[THINK:security_review]" in result.context

    def test_performance_analysis_injects_template_with_tag(self):
        """Performance analysis should inject template with [THINK:performance_analysis] tag."""
        ctx = HookContext(prompt="optimize the slow query", data={})
        result = think_trigger(ctx)

        assert not result.is_empty()
        assert "Performance investigation" in result.context
        assert "[THINK:performance_analysis]" in result.context

    def test_multi_file_refactor_injects_template_with_tag(self):
        """Multi-file refactor should inject template with [THINK:multi_file_refactor] tag."""
        ctx = HookContext(prompt="restructure across the codebase", data={})
        result = think_trigger(ctx)

        assert not result.is_empty()
        assert "Refactoring strategy" in result.context
        assert "[THINK:multi_file_refactor]" in result.context

    def test_tag_format_is_correct(self):
        """Emitted tags should follow format [PREFIX:VALUE]."""
        ctx = HookContext(prompt="debug the intermittent failure", data={})
        result = think_trigger(ctx)

        assert not result.is_empty()
        # Tag format: [THINK:profile_name]
        assert "[THINK:" in result.context
        assert "]" in result.context
        # No spaces within tag brackets
        assert "[THINK: " not in result.context
        assert "[ THINK:" not in result.context


class TestAllSevenProfilesTrigger:
    """Verify all 7 profiles still trigger correctly with unified detection."""

    @pytest.mark.parametrize("prompt,expected_profile,expected_content", [
        # Debug RCA
        ("the test keeps failing intermittently", "debug_rca", "5 Whys"),

        # Tradeoff decision
        ("should we use Redis or Memcached?", "tradeoff_decision", "Decision frame"),

        # Architecture
        ("should we split into microservices?", "architecture", "Cynefin"),

        # Pre-commit risk
        ("about to deploy to production", "pre_commit_risk", "Pre-mortem"),

        # Security review
        ("SQL injection vulnerability", "security_review", "OWASP"),

        # Performance analysis
        ("optimize the slow query", "performance_analysis", "Performance investigation"),

        # Multi-file refactor
        ("restructure across the codebase", "multi_file_refactor", "Refactoring strategy"),
    ])
    def test_all_profiles_trigger(self, prompt, expected_profile, expected_content):
        """All 7 profiles should trigger and inject correct templates."""
        ctx = HookContext(prompt=prompt, data={})
        result = think_trigger(ctx)

        assert not result.is_empty(), f"Profile '{expected_profile}' should trigger for: {prompt}"
        assert expected_content in result.context, \
            f"Profile '{expected_profile}' should inject template with '{expected_content}'"
        assert f"[THINK:{expected_profile}]" in result.context, \
            f"Profile '{expected_profile}' should emit tag [THINK:{expected_profile}]"

    def test_all_profiles_exist(self):
        """All 7 profiles should have templates defined."""
        expected_profiles = [
            "debug_rca",
            "tradeoff_decision",
            "architecture",
            "pre_commit_risk",
            "security_review",
            "performance_analysis",
            "multi_file_refactor",
        ]

        for profile in expected_profiles:
            assert profile in _PROFILES, f"Profile '{profile}' should exist in _PROFILES"
            assert len(_PROFILES[profile]) > 0, f"Profile '{profile}' should have a non-empty template"


class TestTagEmissionIntegration:
    """Test tag emission module integration."""

    def test_tag_emitted_first(self):
        """[THINK:profile_name] tag should be emitted before template."""
        ctx = HookContext(prompt="debug the intermittent failure", data={})
        result = think_trigger(ctx)

        assert not result.is_empty()
        # Tag should come before template content
        tag_position = result.context.index("[THINK:")
        template_position = result.context.index("5 Whys")
        assert tag_position < template_position, "Tag should be emitted before template"

    def test_tag_and_template_separated(self):
        """Tag and template should be separated by blank lines."""
        ctx = HookContext(prompt="debug the intermittent failure", data={})
        result = think_trigger(ctx)

        assert not result.is_empty()
        # Should have tag, then \n\n, then template
        assert "[THINK:debug_rca]\n\n" in result.context


# Import pytest for parametrize
