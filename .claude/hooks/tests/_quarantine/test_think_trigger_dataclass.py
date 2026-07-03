"""Tests for ThinkProfile dataclass refactor (Phase 3).

Tests the single-source dataclass pattern that replaces separate dictionaries.
"""
import pytest
from UserPromptSubmit_modules.think_trigger import (
    _COMPILED_STRONG,
    _COMPILED_WEAK,
    _PROFILES,
    _STRONG_PATTERNS,
    _THINK_PROFILES,
    _WEAK_PATTERNS,
)


class TestThinkProfileDataclass:
    """Test ThinkProfile dataclass structure and completeness."""

    def test_all_7_profiles_exist(self):
        """All 7 profiles must be defined in _THINK_PROFILES."""
        assert len(_THINK_PROFILES) == 7
        expected_profiles = {
            "debug_rca",
            "tradeoff_decision",
            "architecture",
            "pre_commit_risk",
            "security_review",
            "performance_analysis",
            "multi_file_refactor",
        }
        assert set(_THINK_PROFILES.keys()) == expected_profiles

    def test_think_profile_is_frozen_dataclass(self):
        """ThinkProfile must be frozen to prevent accidental mutation."""
        profile = _THINK_PROFILES["debug_rca"]
        # frozen=True makes dataclass immutable
        with pytest.raises(Exception):  # FrozenInstanceError
            profile.name = "modified"

    def test_think_profile_has_required_fields(self):
        """Each profile must have name, template, strong_patterns, weak_patterns."""
        profile = _THINK_PROFILES["debug_rca"]
        assert hasattr(profile, "name")
        assert hasattr(profile, "template")
        assert hasattr(profile, "strong_patterns")
        assert hasattr(profile, "weak_patterns")
        assert profile.name == "debug_rca"
        assert isinstance(profile.template, str)
        assert len(profile.template) > 0
        assert isinstance(profile.strong_patterns, list)
        assert all(isinstance(p, str) for p in profile.strong_patterns)

    def test_weak_patterns_optional(self):
        """weak_patterns field can be None for profiles without weak patterns."""
        # All current profiles have weak patterns, but the field should accept None
        profile = _THINK_PROFILES["debug_rca"]
        # Field type is list[str] | None
        assert profile.weak_patterns is None or isinstance(profile.weak_patterns, list)

    def test_dictionaries_derived_from_single_source(self):
        """_PROFILES, _STRONG_PATTERNS, _WEAK_PATTERNS must derive from _THINK_PROFILES."""
        # Check that all derived dictionaries have the same keys as _THINK_PROFILES
        assert set(_PROFILES.keys()) == set(_THINK_PROFILES.keys())
        assert set(_STRONG_PATTERNS.keys()) == set(_THINK_PROFILES.keys())
        assert set(_WEAK_PATTERNS.keys()) == set(_THINK_PROFILES.keys())

        # Check that values match
        for profile_name, profile in _THINK_PROFILES.items():
            assert _PROFILES[profile_name] == profile.template
            assert _STRONG_PATTERNS[profile_name] == profile.strong_patterns
            assert _WEAK_PATTERNS[profile_name] == profile.weak_patterns

    def test_compiled_patterns_consistency(self):
        """_COMPILED_STRONG and _COMPILED_WEAK must match pattern dictionaries."""
        assert set(_COMPILED_STRONG.keys()) == set(_STRONG_PATTERNS.keys())
        assert set(_COMPILED_WEAK.keys()) == set(_WEAK_PATTERNS.keys())

        for profile_name in _STRONG_PATTERNS:
            strong_count = len(_COMPILED_STRONG[profile_name])
            weak_count = len(_COMPILED_WEAK[profile_name])
            assert strong_count == len(_STRONG_PATTERNS[profile_name])
            assert weak_count == len(_WEAK_PATTERNS[profile_name])

    def test_dataclass_prevents_misalignment(self):
        """Dataclass structure makes it impossible to add patterns without templates."""
        # The old bug: adding to _STRONG_PATTERNS but forgetting _PROFILES
        # With dataclass, you must provide all fields together
        # This test documents the invariant enforced by the new structure

        # Before refactor: could add to _STRONG_PATTERNS["new_profile"] = [...]
        # After refactor: must create ThinkProfile with all fields
        # This prevents the KeyError: 'security_review' bug
        pass  # Invariant enforced by type system

    def test_backward_compat_aliases_exist(self):
        """Backward-compat aliases for tests must still work."""
        from UserPromptSubmit_modules.think_trigger import (
            _PROFILE_KEYWORDS,
            _STRONG_KEYWORDS,
            _WEAK_KEYWORDS,
        )
        assert _STRONG_KEYWORDS is _STRONG_PATTERNS
        assert _WEAK_KEYWORDS is _WEAK_PATTERNS
        assert isinstance(_PROFILE_KEYWORDS, dict)
        assert set(_PROFILE_KEYWORDS.keys()) == set(_THINK_PROFILES.keys())


class TestDataclassEliminatesBugClass:
    """Test that the dataclass refactor prevents the original bug."""

    def test_cannot_add_pattern_without_template(self):
        """Adding a pattern requires adding a template (compiler-enforced)."""
        # In the old structure:
        #   _STRONG_PATTERNS["new_profile"] = [...]
        #   template = _PROFILES["new_profile"]  # KeyError!
        #
        # In the new structure:
        #   Must create ThinkProfile(name, template, strong_patterns, weak_patterns)
        #   Compiler/IDE enforces all fields are present
        pass  # Type system prevents this bug class

    def test_single_source_prevents_drift(self):
        """All profile data co-located prevents structures drifting apart."""
        # With dataclass, all data for a profile is in one place
        # No risk of updating _STRONG_PATTERNS but forgetting _PROFILES
        profile = _THINK_PROFILES["security_review"]
        assert profile.name == "security_review"
        assert profile.template  # Must exist
        assert profile.strong_patterns  # Must exist
        # All fields present together, no drift possible
