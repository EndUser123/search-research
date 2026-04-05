"""Tests for skill_autonomy_registry.py.

From ADR-20260329-llm-consultation-pattern-fix.md — CHANGE-004
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add skills/__lib to path for registry import
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "skills" / "__lib__"))

from skill_autonomy_registry import (
    SkillTier,
    classify_skill_invocation,
    _has_adr_path,
    _has_file_path,
    _is_destructive_operation,
)


class TestHasAdrPath:
    """Tests for _has_adr_path helper."""

    def test_adr_pattern_detected(self):
        assert _has_adr_path("ADR-20260329-llm-consultation-pattern-fix.md") is True

    def test_arch_decisions_directory_detected(self):
        assert _has_adr_path("__csf/arch_decisions/ADR-20260329-test.md") is True

    def test_windows_arch_decisions_directory_detected(self):
        assert _has_adr_path("__csf\\arch_decisions\\ADR-20260329-test.md") is True

    def test_empty_string_returns_false(self):
        assert _has_adr_path("") is False

    def test_none_returns_false(self):
        assert _has_adr_path(None) is False

    def test_no_adr_pattern_returns_false(self):
        assert _has_adr_path("some random text without adr") is False

    def test_case_insensitive(self):
        assert _has_adr_path("adr-20260329-test.md") is True
        assert _has_adr_path("ARCH_DECISIONS/file.md") is True


class TestHasFilePath:
    """Tests for _has_file_path helper."""

    def test_windows_path_detected(self):
        assert _has_file_path("P:\\projects\\test.py") is True

    def test_unix_path_detected(self):
        assert _has_file_path("/home/user/file.py") is True

    def test_file_extension_detected(self):
        assert _has_file_path("read file.py first") is True

    def test_no_path_returns_false(self):
        assert _has_file_path("some text without paths") is False

    def test_empty_string_returns_false(self):
        assert _has_file_path("") is False

    def test_none_returns_false(self):
        assert _has_file_path(None) is False


class TestIsDestructiveOperation:
    """Tests for _is_destructive_operation helper."""

    def test_delete_skill_blocking(self):
        assert _is_destructive_operation("/delete", {}) is True

    def test_destroy_skill_blocking(self):
        assert _is_destructive_operation("/destroy", {}) is True

    def test_purge_skill_blocking(self):
        assert _is_destructive_operation("/purge", {}) is True

    def test_wipe_skill_blocking(self):
        assert _is_destructive_operation("/wipe", {}) is True

    def test_drop_skill_blocking(self):
        assert _is_destructive_operation("/drop", {}) is True

    def test_non_destructive_skill_returns_false(self):
        assert _is_destructive_operation("/planning", {}) is False

    def test_force_flag_in_args_blocking(self):
        assert _is_destructive_operation("/refactor", {"skill_args": "use --force"}) is True

    def test_delete_flag_in_args_blocking(self):
        assert _is_destructive_operation("/code", {"skill_args": "file.py --delete"}) is True


class TestClassifySkillInvocation:
    """Tests for classify_skill_invocation main function."""

    def test_planning_with_adr_path_is_pre_authorized(self):
        result = classify_skill_invocation(
            "/planning",
            {"skill_args": "P:\\__csf\\arch_decisions\\ADR-20260329-test.md"},
        )
        assert result == SkillTier.PRE_AUTHORIZED

    def test_planning_without_adr_is_ambiguous(self):
        result = classify_skill_invocation("/planning", {"skill_args": ""})
        assert result == SkillTier.AMBIGUOUS

    def test_verify_with_file_path_is_pre_authorized(self):
        result = classify_skill_invocation(
            "/verify",
            {"skill_args": "P:\\projects\\test.py"},
        )
        assert result == SkillTier.PRE_AUTHORIZED

    def test_verify_without_file_path_is_ambiguous(self):
        result = classify_skill_invocation("/verify", {"skill_args": ""})
        assert result == SkillTier.AMBIGUOUS

    def test_delete_skill_is_blocking(self):
        result = classify_skill_invocation("/delete", {"skill_args": "some file"})
        assert result == SkillTier.BLOCKING

    def test_unknown_skill_defaults_to_ambiguous(self):
        result = classify_skill_invocation("/unknown-skill", {})
        assert result == SkillTier.AMBIGUOUS

    def test_registry_skills_are_ambiguous_by_default(self):
        for skill in ["/refactor", "/code", "/search", "/research"]:
            result = classify_skill_invocation(skill, {"skill_args": ""})
            assert result == SkillTier.AMBIGUOUS, f"{skill} should be AMBIGUOUS"

    def test_destructive_args_override_ambiguous_registry(self):
        # /refactor is normally AMBIGUOUS, but with --delete flag it becomes BLOCKING
        result = classify_skill_invocation(
            "/refactor",
            {"skill_args": "old_file.py --delete"},
        )
        assert result == SkillTier.BLOCKING
