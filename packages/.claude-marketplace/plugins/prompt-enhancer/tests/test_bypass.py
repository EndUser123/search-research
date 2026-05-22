"""
Test bypass prefix detection in detect.py.

These tests verify the bypass prefix configuration is loaded and applied correctly.
"""

import pytest
from detect import load_bypass_prefixes, triage


class TestBypassPrefixes:
    def test_bypass_prefixes_loaded_from_config(self):
        prefixes = load_bypass_prefixes()
        assert isinstance(prefixes, list)
        assert len(prefixes) > 0
        # Verify expected prefixes are present
        assert "!raw" in prefixes
        assert "*nope" in prefixes
        assert "nope:" in prefixes
        assert "prompt-enhancer: off" in prefixes

    def test_triage_returns_bypass_for_prefixed_prompts(self):
        test_cases = [
            "!raw some command",
            "*nope add a feature",
            "nope: delete the database",
            "prompt-enhancer: off delete everything",
        ]
        for prompt in test_cases:
            result = triage(prompt)
            assert result["classification"] == "bypass", f"Expected bypass for: {prompt}"

    def test_bypass_prefix_case_sensitive(self):
        """Bypass prefixes are checked as-is (case-sensitive match on prompt.startswith)."""
        # "!RAW" should NOT trigger bypass (case sensitive)
        result = triage("!RAW some command")
        assert result["classification"] != "bypass"

    def test_bypass_without_space(self):
        """Bypass should trigger even without space after prefix."""
        result = triage("*nopeadd a feature")
        assert result["classification"] == "bypass"

    def test_non_bypass_prompt_not_affected(self):
        """Non-bypass prompts return their normal classification."""
        result = triage("delete the database")
        assert result["classification"] == "confirm"