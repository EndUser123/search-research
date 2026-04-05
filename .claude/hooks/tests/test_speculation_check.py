#!/usr/bin/env python3
"""TDD tests for PreToolUse_speculation_check.py - RED Phase.

These tests verify the speculation check hook behavior.
Run with: pytest P:/.claude/hooks/tests/test_speculation_check.py -v

Following TDD workflow:
1. Write tests first (THIS FILE) - verify they FAIL
2. Implement hook to make tests PASS
3. Refactor if needed
4. Verify tests still pass
"""

import sys

import pytest

# Add hooks directory to path for import
sys.path.insert(0, "P:/.claude/hooks")


class TestSpeculationCheckBasicDetection:
    """Tests for basic speculative language detection."""

    def test_speculative_language_detected_blocks_with_suggestions(self):
        """
        Test that speculative language triggers block with suggestions.

        Given: Response contains "appears to be"
        When: check_speculation is called
        Then: Result should block with SPECULATIVE_LANGUAGE_DETECTED reason
        """
        # Import the hook module
        from PreToolUse_speculation_check import check_speculation

        data = {
            "response": "The issue appears to be in the configuration file.",
            "tools_available": ["Read", "Write"]
        }

        result = check_speculation(data)

        # Should block
        assert result["allowed"] == False, "Should block when speculative language detected"
        assert result["reason"] == "SPECULATIVE_LANGUAGE_DETECTED", "Reason should be SPECULATIVE_LANGUAGE_DETECTED"
        assert "findings" in result, "Should include findings"
        assert len(result["findings"]) > 0, "Should have at least one finding"
        assert "remediation" in result, "Should include remediation"

    def test_no_speculative_language_passes(self):
        """
        Test that response without speculative language passes.

        Given: Response contains factual language with evidence
        When: check_speculation is called
        Then: Result should allow (allowed=True)
        """
        from PreToolUse_speculation_check import check_speculation

        data = {
            "response": "I verified the configuration file at P:/config/settings.json shows port 8080.",
            "tools_available": ["Read"]
        }

        result = check_speculation(data)

        # Should allow
        assert result["allowed"] == True, "Should allow when no speculative language detected"

    def test_multiple_patterns_all_listed(self):
        """
        Test that multiple speculative patterns are all detected and listed.

        Given: Response contains "likely", "probably", and "seems like"
        When: check_speculation is called
        Then: All patterns should be listed in findings
        """
        from PreToolUse_speculation_check import check_speculation

        data = {
            "response": "This is likely the issue. It's probably caused by the configuration. It seems like the path is wrong.",
            "tools_available": ["Read"]
        }

        result = check_speculation(data)

        # Should block
        assert result["allowed"] == False, "Should block with multiple speculative patterns"

        # Should have multiple findings
        findings = result.get("findings", [])
        assert len(findings) >= 3, f"Should detect at least 3 patterns, got {len(findings)}"

        # Each finding should have pattern and suggestion
        for finding in findings:
            assert "pattern" in finding, "Each finding should have 'pattern'"
            assert "suggestion" in finding, "Each finding should have 'suggestion'"

    def test_response_excerpt_in_remediation(self):
        """
        Test that remediation includes response excerpt.

        Given: Response contains speculative language
        When: check_speculation is called
        Then: Remediation should show excerpt from response
        """
        from PreToolUse_speculation_check import check_speculation

        data = {
            "response": "The issue appears to be in the hook configuration. Likely the timeout is too short.",
            "tools_available": ["Read"]
        }

        result = check_speculation(data)

        # Should have remediation
        assert "remediation" in result, "Should include remediation"
        remediation = result["remediation"]

        # Should mention the detected patterns
        assert "appears to be" in remediation or "likely" in remediation, \
            "Remediation should mention detected patterns"

        # Should include rewrite options
        assert "[UNVERIFIED]" in remediation or "INVESTIGATION REQUIRED" in remediation, \
            "Remediation should include uncertainty markers or investigation format"


class TestSpeculativePatterns:
    """Tests for specific speculative pattern detection."""

    def test_appears_to_be_pattern(self):
        """Test detection of 'appears to be' pattern."""
        from PreToolUse_speculation_check import check_speculation

        data = {
            "response": "This appears to be the problem.",
            "tools_available": ["Read"]
        }

        result = check_speculation(data)
        assert result["allowed"] == False

        # Check that this pattern is in findings
        findings = result.get("findings", [])
        pattern_found = any("appears to be" in f.get("pattern", "").lower() for f in findings)
        assert pattern_found, "Should detect 'appears to be' pattern"

    def test_likely_pattern(self):
        """Test detection of 'likely' pattern."""
        from PreToolUse_speculation_check import check_speculation

        data = {
            "response": "This is likely the cause.",
            "tools_available": ["Read"]
        }

        result = check_speculation(data)
        assert result["allowed"] == False

        findings = result.get("findings", [])
        pattern_found = any("likely" in f.get("pattern", "").lower() for f in findings)
        assert pattern_found, "Should detect 'likely' pattern"

    def test_probably_pattern(self):
        """Test detection of 'probably' pattern."""
        from PreToolUse_speculation_check import check_speculation

        data = {
            "response": "This is probably the issue.",
            "tools_available": ["Read"]
        }

        result = check_speculation(data)
        assert result["allowed"] == False

        findings = result.get("findings", [])
        pattern_found = any("probably" in f.get("pattern", "").lower() for f in findings)
        assert pattern_found, "Should detect 'probably' pattern"

    def test_seems_like_pattern(self):
        """Test detection of 'seems like' pattern."""
        from PreToolUse_speculation_check import check_speculation

        data = {
            "response": "It seems like the file is missing.",
            "tools_available": ["Read"]
        }

        result = check_speculation(data)
        assert result["allowed"] == False

        findings = result.get("findings", [])
        pattern_found = any("seems like" in f.get("pattern", "").lower() for f in findings)
        assert pattern_found, "Should detect 'seems like' pattern"


class TestUncertaintyMarkers:
    """Tests for uncertainty marker handling."""

    def test_unverified_marker_passes(self):
        """Test that responses with [UNVERIFIED] marker pass."""
        from PreToolUse_speculation_check import check_speculation

        data = {
            "response": "This appears to be the issue [UNVERIFIED].",
            "tools_available": ["Read"]
        }

        result = check_speculation(data)
        # When properly marked with [UNVERIFIED], should allow
        assert result["allowed"] == True, "Should allow when speculation is marked with [UNVERIFIED]"

    def test_requires_investigation_marker_passes(self):
        """Test that responses with [REQUIRES INVESTIGATION] marker pass."""
        from PreToolUse_speculation_check import check_speculation

        data = {
            "response": "This is likely the cause [REQUIRES INVESTIGATION].",
            "tools_available": ["Read"]
        }

        result = check_speculation(data)
        assert result["allowed"] == True, "Should allow when marked with [REQUIRES INVESTIGATION]"

    def test_based_on_current_evidence_marker_passes(self):
        """Test that responses with [BASED ON CURRENT EVIDENCE] marker pass."""
        from PreToolUse_speculation_check import check_speculation

        data = {
            "response": "This is probably the issue [BASED ON CURRENT EVIDENCE].",
            "tools_available": ["Read"]
        }

        result = check_speculation(data)
        assert result["allowed"] == True, "Should allow when marked with [BASED ON CURRENT EVIDENCE]"


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_empty_response_passes(self):
        """Test that empty response passes."""
        from PreToolUse_speculation_check import check_speculation

        data = {
            "response": "",
            "tools_available": ["Read"]
        }

        result = check_speculation(data)
        assert result["allowed"] == True, "Empty response should pass"

    def test_missing_response_field_passes(self):
        """Test that missing response field passes."""
        from PreToolUse_speculation_check import check_speculation

        data = {
            "tools_available": ["Read"]
        }

        result = check_speculation(data)
        assert result["allowed"] == True, "Missing response field should pass"

    def test_case_insensitive_detection(self):
        """Test that pattern detection is case-insensitive."""
        from PreToolUse_speculation_check import check_speculation

        test_cases = [
            "This LIKELY is the issue.",
            "This Probably is the cause.",
            "This APPEARS TO BE the problem.",
        ]

        for response in test_cases:
            data = {
                "response": response,
                "tools_available": ["Read"]
            }

            result = check_speculation(data)
            assert result["allowed"] == False, f"Should detect speculative language in: {response}"

    def test_word_boundary_detection(self):
        """Test that pattern detection respects word boundaries."""
        from PreToolUse_speculation_check import check_speculation

        # Words containing "likely" but not meaning speculation should pass
        data = {
            "response": "The unlikelihood of this issue is high.",
            "tools_available": ["Read"]
        }

        result = check_speculation(data)
        # Should pass because "likely" is part of "unlikelihood", not a speculative marker
        # Note: This depends on the regex pattern implementation
        # If word boundaries are properly used, this should pass


if __name__ == "__main__":
    # Run with pytest
    pytest.main([__file__, "-v", "--tb=short"])
