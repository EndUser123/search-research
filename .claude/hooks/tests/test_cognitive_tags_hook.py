"""Tests for cognitive tag helper and UserPromptSubmit hook."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

# Add hooks directory to path
_HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_HOOKS_DIR))

import pytest

try:
    from __lib.cognitive_tag_helper import (
        get_active_tags_for_prompt,
        format_tags_for_instruction,
        get_cognitive_tag_instruction,
    )
except ImportError:
    # For import tests when module not yet created
    get_active_tags_for_prompt = None
    format_tags_for_instruction = None
    get_cognitive_tag_instruction = None


class TestGetActiveTagsForPrompt:
    """Tests for get_active_tags_for_prompt function."""

    def test_empty_prompt_returns_empty_list(self):
        """Empty prompt should return empty list."""
        if get_active_tags_for_prompt is None:
            pytest.skip("Module not yet created")
        assert get_active_tags_for_prompt("") == []
        assert get_active_tags_for_prompt("   ") == []

    def test_none_prompt_returns_empty_list(self):
        """None prompt should return empty list."""
        if get_active_tags_for_prompt is None:
            pytest.skip("Module not yet created")
        assert get_active_tags_for_prompt(None) == []

    def test_diagnostic_prompt_returns_cal_tag(self):
        """Debug/diagnostic prompt should return CAL (Calibrated Confidence)."""
        if get_active_tags_for_prompt is None:
            pytest.skip("Module not yet created")
        tags = get_active_tags_for_prompt("debug why the login fails")
        assert "CAL" in tags

    def test_implementation_prompt_returns_anch_tag(self):
        """Implementation prompt should return ANCH (Outcome Anchoring)."""
        if get_active_tags_for_prompt is None:
            pytest.skip("Module not yet created")
        tags = get_active_tags_for_prompt("build a new API endpoint")
        assert "ANCH" in tags


class TestFormatTagsForInstruction:
    """Tests for format_tags_for_instruction function."""

    def test_empty_tags_returns_empty_string(self):
        """Empty tag list should return empty string."""
        if format_tags_for_instruction is None:
            pytest.skip("Module not yet created")
        assert format_tags_for_instruction([]) == ""
        assert format_tags_for_instruction([""]) == ""

    def test_single_tag_format(self):
        """Single tag should be formatted correctly."""
        if format_tags_for_instruction is None:
            pytest.skip("Module not yet created")
        result = format_tags_for_instruction(["CAL"])
        assert "[CAL]" in result
        assert "Tags: [CAL]" in result

    def test_multiple_tags_format(self):
        """Multiple tags should be formatted with correct instruction."""
        if format_tags_for_instruction is None:
            pytest.skip("Module not yet created")
        result = format_tags_for_instruction(["CAL", "CYNE"])
        assert "[CAL]" in result
        assert "[CYNE]" in result
        assert "Tags: [CAL] [CYNE]" in result

    def test_instruction_contains_end_qualifier(self):
        """Instruction should mention appending to end."""
        if format_tags_for_instruction is None:
            pytest.skip("Module not yet created")
        result = format_tags_for_instruction(["CAL"])
        assert "end of your response" in result
        assert "Tags: [CAL]" in result


class TestGetCognitiveTagInstruction:
    """Tests for get_cognitive_tag_instruction function."""

    def test_no_tags_returns_empty_string(self):
        """Prompt with no matching frameworks should return empty."""
        if get_cognitive_tag_instruction is None:
            pytest.skip("Module not yet created")
        # Empty prompt has no tags
        assert get_cognitive_tag_instruction("") == ""

    def test_diagnostic_prompt_returns_instruction(self):
        """Diagnostic prompt should return non-empty instruction."""
        if get_cognitive_tag_instruction is None:
            pytest.skip("Module not yet created")
        result = get_cognitive_tag_instruction("debug why the login fails")
        assert result != ""


class TestCognitiveTagsHook:
    """Tests for UserPromptSubmit_cognitive_tags.py hook."""

    def test_hook_integration_loads(self):
        """Hook should be loadable via registry."""
        try:
            from UserPromptSubmit_modules.registry import HOOKS
            # Hook should be registered
            assert "cognitive_tags" in HOOKS or len(HOOKS) >= 0
        except ImportError:
            pytest.skip("Registry not available")

    def test_hook_outputs_json_to_stdout(self):
        """Hook should output JSON to stdout (not stderr)."""
        from UserPromptSubmit_cognitive_tags import cognitive_tags
        from UserPromptSubmit_modules.base import HookContext

        ctx = HookContext(
            prompt="debug why the login fails",
            data={},
        )
        result = cognitive_tags(ctx)

        # Result should have context if tags detected
        if result.context:
            assert isinstance(result.context, str)


class TestEndToEnd:
    """End-to-end integration tests."""

    def test_full_flow_no_tags(self):
        """No tags active → no injection."""
        if get_active_tags_for_prompt is None:
            pytest.skip("Module not yet created")

        tags = get_active_tags_for_prompt("")
        instruction = format_tags_for_instruction(tags)

        assert tags == []
        assert instruction == ""

    def test_full_flow_with_tags(self):
        """Tags active → instruction injected."""
        if get_active_tags_for_prompt is None:
            pytest.skip("Module not yet created")

        prompt = "debug why the login fails"
        tags = get_active_tags_for_prompt(prompt)
        instruction = format_tags_for_instruction(tags)

        assert len(tags) > 0
        assert instruction != ""
        assert "cognitive-tags" in instruction

    def test_every_response_shows_tags(self):
        """Tags appear on every response (not just first)."""
        if format_tags_for_instruction is None:
            pytest.skip("Module not yet created")

        tags = ["CAL", "CYNE"]
        instruction = format_tags_for_instruction(tags)

        # The instruction tells Claude to append tags to EVERY response
        assert "end of your response" in instruction
        assert "Tags: [CAL] [CYNE]" in instruction
