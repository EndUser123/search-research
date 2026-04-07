#!/usr/bin/env python3
"""Tests for Stop_proposal_decision_scanner.py."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from Stop_proposal_decision_scanner import (
    _extract_decision_claims,
    _extract_rejections,
    _normalize_option,
    _check_response_for_conflation,
)


class TestExtractDecisionClaims:
    """Tests for decision claim extraction."""

    def test_option_is_correct(self):
        result = _extract_decision_claims("Option B is correct")
        assert result == ["Option B"]

    def test_option_is_right(self):
        result = _extract_decision_claims("Option A is right")
        assert result == ["Option A"]

    def test_go_with_option(self):
        result = _extract_decision_claims("Let's go with Option C")
        assert result == ["Option C"]

    def test_option_should_be_used(self):
        result = _extract_decision_claims("Option D should be used")
        assert result == ["Option D"]

    def test_no_claim(self):
        result = _extract_decision_claims("The implementation is complete")
        assert result == []

    def test_case_insensitive(self):
        result = _extract_decision_claims("OPTION A IS CORRECT")
        assert result == ["OPTION A"]


class TestExtractRejections:
    """Tests for rejection extraction."""

    def test_option_doesnt_make_sense(self):
        result = _extract_rejections("Option B doesn't make sense")
        assert result == ["Option B"]

    def test_option_rejected(self):
        result = _extract_rejections("Option C was rejected")
        assert result == ["Option C"]

    def test_option_shouldnt_be_used(self):
        result = _extract_rejections("Option A shouldn't be used")
        assert result == ["Option A"]

    def test_dont_rebuild(self):
        result = _extract_rejections("That doesn't make sense to rebuild it then")
        assert result == []

    def test_no_rejection(self):
        result = _extract_rejections("The option seems reasonable")
        assert result == []


class TestNormalizeOption:
    """Tests for option normalization."""

    def test_lowercase(self):
        assert _normalize_option("option b") == "OPTION B"

    def test_mixed_case(self):
        assert _normalize_option("Option A") == "OPTION A"


class TestConflationDetection:
    """Tests for conflation detection (contradiction between claim and rejection)."""

    def test_contradiction_detected(self):
        """Response claims Option B is correct, but transcript shows Option B was rejected."""
        response = "Option B is correct and should be used"
        transcript = [
            {"type": "user", "message": {"content": "Option B doesn't make sense to rebuild it then"}},
        ]
        result = _check_response_for_conflation(response, transcript)
        assert result is not None
        assert result["decision"] == "warn"
        assert "Option B" in result["reason"]

    def test_no_contradiction(self):
        """Response claims Option A is correct, but Option B was rejected (no conflict)."""
        response = "Option A is correct and should be used"
        transcript = [
            {"type": "user", "message": {"content": "Option B doesn't make sense to rebuild it then"}},
        ]
        result = _check_response_for_conflation(response, transcript)
        assert result is None

    def test_no_decision_claim(self):
        """Response has no decision claim, no warning even with rejection in history."""
        response = "The implementation is complete"
        transcript = [
            {"type": "user", "message": {"content": "Option B was rejected"}},
        ]
        result = _check_response_for_conflation(response, transcript)
        assert result is None

    def test_empty_response(self):
        result = _check_response_for_conflation("", [])
        assert result is None

    def test_empty_transcript(self):
        result = _check_response_for_conflation("Option B is correct", [])
        assert result is None

    def test_multiple_claims_one_rejected(self):
        """Response claims both A and B are correct, B was rejected."""
        response = "Option A is correct and Option B is also correct"
        transcript = [
            {"type": "user", "message": {"content": "Option B doesn't make sense"}},
        ]
        result = _check_response_for_conflation(response, transcript)
        assert result is not None
        assert result["decision"] == "warn"
        assert "Option B" in result["reason"]
        assert "Option A" not in result["reason"]
