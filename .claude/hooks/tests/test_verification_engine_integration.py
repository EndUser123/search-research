#!/usr/bin/env python3
"""Integration tests for Phase 1 verification engine.

Tests the actual verification engine flow without mocks, using real
evidence_store and verification/engine components.

Anti-mock stance: These tests use real components to verify actual
integration, not mocked behavior.
"""

import sys
from pathlib import Path

import pytest

hooks_dir = Path(__file__).resolve().parent.parent
if str(hooks_dir) not in sys.path:
    sys.path.insert(0, str(hooks_dir))

from verification import claims, engine


class TestPhase1VerificationEngineIntegration:
    """Integration tests for Phase 1 verification engine.

    These tests verify that:
    1. extract_claims() detects ABSENCE/RULE claims
    2. build_verdicts() processes claims and events
    3. The full pipeline (claims → verdicts) works
    """

    def test_extract_claims_detects_absence_claims(self):
        """Verify extract_claims() detects ABSENCE claim patterns."""
        response = "Package has no skill/ directory."

        extracted = claims.extract_claims(response_text=response)

        assert len(extracted) >= 1
        absence_claims = [c for c in extracted if "ABSENCE" in c.type.upper()]
        assert len(absence_claims) >= 1

    def test_extract_claims_returns_empty_for_benign_response(self):
        """Verify extract_claims() returns empty list for non-claims."""
        response = "Let me check the documentation for that."

        extracted = claims.extract_claims(response_text=response)

        assert len(extracted) == 0

    def test_build_verdicts_processes_synthetic_events(self):
        """Verify build_verdicts() processes synthetic event data correctly."""
        # Create synthetic tool event (simulating Read of skill/SKILL.md)
        synthetic_event = {
            "id": 1,
            "name": "Read",
            "timestamp": "2026-03-24T12:00:00",
            "command": "skill/SKILL.md",
            "cwd": "/test",
            "output": "# Skill documentation",
            "session_id": "test-session",
            "terminal_id": "test-terminal",
            "success": True,
        }

        # Create ABSENCE claim for skill/ directory
        claim = claims.Claim(
            id="test-claim-1",
            text="Package has no skill/ directory",
            targets=["skill/"],
            type="ABSENCE",
            confidence=0.9,
            risk_domain="negative_existence",
            has_hedge=False,
        )

        # Build verdicts with synthetic event
        verdicts = engine.build_verdicts([claim], [synthetic_event])

        # Verify verdict structure (integration test - verify data flows through)
        assert len(verdicts) == 1
        assert verdicts[0].claim_id == "test-claim-1"
        assert verdicts[0].confidence == 0.9

    def test_build_verdicts_silent_without_relevant_tools(self):
        """Verify build_verdicts() returns SILENT when no verification tools used."""
        # No tool events (empty list)

        # Create ABSENCE claim
        claim = claims.Claim(
            id="test-claim-2",
            text="Package has no skill/ directory",
            targets=["skill/"],
            type="ABSENCE",
            confidence=0.9,
            risk_domain="negative_existence",
            has_hedge=False,
        )

        # Build verdicts with empty events
        verdicts = engine.build_verdicts([claim], [])

        assert len(verdicts) == 1
        assert verdicts[0].status == engine.VerificationStatus.SILENT

    def test_full_pipeline_end_to_end(self):
        """Verify the full pipeline: extract → verify.

        This test simulates the actual Stop hook flow:
        1. Extract claims from response
        2. Build verdicts (without tool events - simulating ungrounded claim)
        3. Verify ungrounded claims are detected
        """
        # User makes confident absence claim without verification
        response = "Package has no skill/ directory."

        # Extract claims
        extracted = claims.extract_claims(response_text=response)

        assert len(extracted) >= 1

        # No tool events (user didn't verify)
        events = []

        # Build verdicts
        verdicts = engine.build_verdicts(extracted, events)

        # At least one claim should be SILENT (no verification tools used)
        silent_verdicts = [v for v in verdicts if v.status == engine.VerificationStatus.SILENT]
        assert len(silent_verdicts) >= 1

    def test_graceful_degradation_on_empty_input(self):
        """Verify graceful degradation when verification engine receives empty input.

        COMP-001: Engine errors should fail-closed (block with clear error).
        """
        # Test with empty string (graceful degradation)
        response = ""

        # extract_claims should handle empty string gracefully
        extracted = claims.extract_claims(response_text=response)

        # Verify that empty claims were returned (graceful degradation)
        assert len(extracted) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
