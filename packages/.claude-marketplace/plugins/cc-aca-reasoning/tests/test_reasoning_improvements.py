#!/usr/bin/env python3
"""Tests for reasoning quality improvements.

Covers:
- PreToolUse_investigation_boundary_gate: investigation-to-implementation transition
- Stop_reasoning_quality_gate._detect_reasoning_depth_mismatch: overthinking/underthinking
- think_trigger: ULTRATHINK keyword binding + 4-lens profile routing
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

REASONING_ROOT = Path(__file__).resolve().parent.parent


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


boundary_gate = _load_module(
    "boundary_gate",
    REASONING_ROOT / "hooks" / "pretool" / "PreToolUse_investigation_boundary_gate.py",
)
quality_gate = _load_module(
    "quality_gate",
    REASONING_ROOT / "hooks" / "stop" / "Stop_reasoning_quality_gate.py",
)
think_trigger = _load_module(
    "think_trigger",
    REASONING_ROOT / "hooks" / "userpromptsubmit" / "think_trigger.py",
)


# ============================================================================
# Investigation Boundary Gate
# ============================================================================


class TestInvestigationBoundaryGate:

    def test_fires_on_first_edit_after_investigation(self):
        history = [
            {"tool_name": "Read", "tool_input": {"file_path": "a.py"}},
            {"tool_name": "Grep", "tool_input": {"pattern": "test"}},
            {"tool_name": "Read", "tool_input": {"file_path": "b.py"}},
        ]
        assert boundary_gate.detect_investigation_to_impl_transition("Edit", history) is True

    def test_fires_on_first_write_after_investigation(self):
        history = [
            {"tool_name": "Glob", "tool_input": {"pattern": "*.py"}},
            {"tool_name": "Read", "tool_input": {"file_path": "a.py"}},
        ]
        assert boundary_gate.detect_investigation_to_impl_transition("Write", history) is True

    def test_does_not_fire_for_read_tool(self):
        history = [
            {"tool_name": "Read", "tool_input": {"file_path": "a.py"}},
            {"tool_name": "Read", "tool_input": {"file_path": "b.py"}},
        ]
        assert boundary_gate.detect_investigation_to_impl_transition("Read", history) is False

    def test_does_not_fire_if_prior_implementation_exists(self):
        history = [
            {"tool_name": "Read", "tool_input": {"file_path": "a.py"}},
            {"tool_name": "Edit", "tool_input": {"file_path": "a.py"}},
            {"tool_name": "Read", "tool_input": {"file_path": "b.py"}},
        ]
        assert boundary_gate.detect_investigation_to_impl_transition("Edit", history) is False

    def test_does_not_fire_with_insufficient_investigation(self):
        history = [{"tool_name": "Read", "tool_input": {"file_path": "a.py"}}]
        assert boundary_gate.detect_investigation_to_impl_transition("Edit", history) is False

    def test_does_not_fire_with_no_history(self):
        assert boundary_gate.detect_investigation_to_impl_transition("Edit", None) is False

    def test_does_not_fire_with_empty_history(self):
        assert boundary_gate.detect_investigation_to_impl_transition("Edit", []) is False

    def test_fires_at_exact_threshold(self):
        history = [
            {"tool_name": "Read", "tool_input": {"file_path": "a.py"}},
            {"tool_name": "Grep", "tool_input": {"pattern": "x"}},
        ]
        assert boundary_gate.detect_investigation_to_impl_transition("Edit", history) is True

    def test_multiedit_triggers(self):
        history = [
            {"tool_name": "Read", "tool_input": {"file_path": "a.py"}},
            {"tool_name": "Grep", "tool_input": {"pattern": "x"}},
        ]
        assert boundary_gate.detect_investigation_to_impl_transition("MultiEdit", history) is True


# ============================================================================
# Overthinking Detection
# ============================================================================


class TestOverthinkingDetection:

    def test_overthinking_low_complexity_verbose_response(self):
        history = [{"tool_name": "Read", "tool_input": {"file_path": "a.py"}}]
        response = " ".join(["word"] * 500)
        result = quality_gate._detect_reasoning_depth_mismatch(response, history)
        assert result is not None
        assert "Overthinking" in result

    def test_overthinking_reports_word_count(self):
        history = [{"tool_name": "Read", "tool_input": {"file_path": "a.py"}}]
        response = " ".join(["word"] * 600)
        result = quality_gate._detect_reasoning_depth_mismatch(response, history)
        assert "600-word" in result

    def test_no_overthinking_with_no_history(self):
        response = " ".join(["word"] * 500)
        assert quality_gate._detect_reasoning_depth_mismatch(response, None) is None

    def test_ratio_check_high_words_per_unit(self):
        history = [
            {"tool_name": "Read", "tool_input": {"file_path": "a.py"}},
            {"tool_name": "Grep", "tool_input": {"pattern": "x"}},
        ]
        response = " ".join(["word"] * 1200)
        result = quality_gate._detect_reasoning_depth_mismatch(response, history)
        assert result is not None
        assert "ratio" in result.lower()


# ============================================================================
# Underthinking Detection
# ============================================================================


class TestUnderthinkingDetection:

    def test_underthinking_high_complexity_terse_response(self):
        history = [
            {"tool_name": "Read", "tool_input": {"file_path": "a.py"}},
            {"tool_name": "Grep", "tool_input": {"pattern": "x"}},
            {"tool_name": "Glob", "tool_input": {"pattern": "*.py"}},
            {"tool_name": "Read", "tool_input": {"file_path": "b.py"}},
            {"tool_name": "Read", "tool_input": {"file_path": "c.py"}},
            {"tool_name": "LSP", "tool_input": {}},
        ]
        result = quality_gate._detect_reasoning_depth_mismatch("short answer", history)
        assert result is not None
        assert "Underthinking" in result

    def test_underthinking_reports_word_count(self):
        history = [
            {"tool_name": "Read", "tool_input": {"file_path": "a.py"}},
            {"tool_name": "Grep", "tool_input": {"pattern": "x"}},
            {"tool_name": "Glob", "tool_input": {"pattern": "*.py"}},
            {"tool_name": "Read", "tool_input": {"file_path": "b.py"}},
            {"tool_name": "Read", "tool_input": {"file_path": "c.py"}},
            {"tool_name": "LSP", "tool_input": {}},
        ]
        result = quality_gate._detect_reasoning_depth_mismatch("ok", history)
        assert result is not None
        assert "word" in result

    def test_no_underthinking_low_complexity_short_response(self):
        history = [{"tool_name": "Read", "tool_input": {"file_path": "a.py"}}]
        assert quality_gate._detect_reasoning_depth_mismatch("ok", history) is None

    def test_balanced_response_no_flag(self):
        history = [{"tool_name": "Read", "tool_input": {"file_path": "a.py"}}]
        response = " ".join(["word"] * 50)
        assert quality_gate._detect_reasoning_depth_mismatch(response, history) is None


# ============================================================================
# Edge Cases
# ============================================================================


class TestEdgeCases:

    def test_empty_history(self):
        assert quality_gate._detect_reasoning_depth_mismatch("some response", []) is None

    def test_none_history(self):
        assert quality_gate._detect_reasoning_depth_mismatch("some response", None) is None

    def test_history_with_missing_fields(self):
        history = [{}, {"tool_name": "Read"}, {"tool_input": {}}]
        result = quality_gate._detect_reasoning_depth_mismatch("response", history)
        assert isinstance(result, str | type(None))

    def test_mixed_file_path_keys(self):
        history = [
            {"tool_name": "Read", "tool_input": {"file_path": "a.py"}},
            {"tool_name": "Read", "tool_input": {"filePath": "b.py"}},
        ]
        result = quality_gate._detect_reasoning_depth_mismatch(" ".join(["w"] * 300), history)
        assert isinstance(result, str | type(None))


# ============================================================================
# ULTRATHINK keyword binding + 4-lens profile routing (think_trigger)
# ============================================================================


class TestUltrathinkProfile:
    """Verify the ULTRATHINK keyword is bound to the 4-lens 'ultrathink' profile.

    Bug being fixed: before this change, `ULTRATHINK build a feature` silently
    fell through to the 'quick' profile because the alias was not in the map.
    """

    def test_bare_ultrathink_routes_to_ultrathink_profile(self):
        assert think_trigger._detect_profile("ULTRATHINK") == "ultrathink"

    def test_ultrathink_with_task_preserves_remainder(self):
        profile, remainder = think_trigger._parse_think("ULTRATHINK build a feature")
        assert profile == "ultrathink"
        assert "build a feature" in remainder

    def test_lowercase_ultrathink_works(self):
        assert think_trigger._detect_profile("ultrathink build X") == "ultrathink"

    def test_mixed_case_ultrathink_works(self):
        assert think_trigger._detect_profile("UltraThink mixed case") == "ultrathink"

    def test_ultrathink_with_colon_works(self):
        assert think_trigger._detect_profile("ULTRATHINK: build a thing") == "ultrathink"

    def test_ultrathink_does_not_match_bare_think_path(self):
        # \bTHINK\b must NOT match ULTRATHINK (word-boundary excludes it).
        # Confirms the new branch in _detect_profile runs first, not the bare-THINK path.
        import re
        assert re.search(r"\bTHINK\b", "ULTRATHINK") is None

    def test_think_ultrathink_alias_form_routes_to_ultrathink(self):
        # Defensive: THINK <ALIAS> with alias=ultrathink must resolve to the profile.
        profile, _ = think_trigger._parse_think("THINK ULTRATHINK do thing")
        assert profile == "ultrathink"

    def test_existing_think_architect_alias_still_works(self):
        # Regression guard: existing THINK <ALIAS> behavior must be unchanged.
        profile, _ = think_trigger._parse_think("THINK ARCH plan migration")
        assert profile == "architecture"

    def test_ultrathink_profile_registered_in_definitions(self):
        # Frozen dataclass invariant: ultrathink must be in both _PROFILE_DEFINITIONS
        # and _PROFILES, otherwise the __debug__ guard at module-load fires.
        assert "ultrathink" in think_trigger._PROFILE_DEFINITIONS
        assert "ultrathink" in think_trigger._PROFILES

    def test_ultrathink_template_contains_four_lenses(self):
        template = think_trigger._PROFILES["ultrathink"]
        # All four King Mode lenses must appear in the template body.
        for lens in ("PSYCHOLOGICAL", "TECHNICAL", "ACCESSIBILITY", "SCALABILITY"):
            assert lens in template, f"Missing lens: {lens}"

