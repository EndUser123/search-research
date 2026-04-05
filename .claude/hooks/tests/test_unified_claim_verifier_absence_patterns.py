#!/usr/bin/env python3
"""Test unified_claim_verifier catches generic absence/non-existence patterns.

Patch 2: Adds generic absence patterns to CLAIM_PATTERNS:
- "does not exist"
- "doesn't exist"
- "not found"
- "missing"
- "absent"

Test cases:
1. Test detect_claims() catches "doesn't exist" patterns
2. Test detect_claims() catches "not found" patterns
3. Test detect_claims() catches "missing"/"absent" patterns
4. Test existing file/module patterns still work
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from unified_claim_verifier import CLAIM_PATTERNS, CLAIM_RE, detect_claims


class TestUnifiedClaimVerifierAbsencePatterns:
    """Test that unified_claim_verifier.py detects generic absence patterns."""

    def test_detects_does_not_exist(self):
        """Given: Response text contains 'does not exist'
        When: detect_claims() is called
        Then: Return list containing the claim
        """
        # Arrange
        response = "Python 3.14 does not exist in this environment"

        # Act
        claims = detect_claims(response)

        # Assert
        assert len(claims) > 0
        assert any("does not exist" in claim.lower() for claim in claims)

    def test_detects_doesnt_exist(self):
        """Given: Response text contains "doesn't exist"
        When: detect_claims() is called
        Then: Return list containing the claim
        """
        # Arrange
        response = "The module doesn't exist in the codebase"

        # Act
        claims = detect_claims(response)

        # Assert
        assert len(claims) > 0
        assert any("doesn't exist" in claim.lower() for claim in claims)

    def test_detects_not_found(self):
        """Given: Response text contains 'not found'
        When: detect_claims() is called
        Then: Return list containing the claim
        """
        # Arrange
        response = "The configuration file was not found"

        # Act
        claims = detect_claims(response)

        # Assert
        assert len(claims) > 0
        assert any("not found" in claim.lower() for claim in claims)

    def test_detects_missing(self):
        """Given: Response text contains 'missing'
        When: detect_claims() is called
        Then: Return list containing the claim
        """
        # Arrange
        response = "The required dependency is missing"

        # Act
        claims = detect_claims(response)

        # Assert
        assert len(claims) > 0
        assert any("missing" in claim.lower() for claim in claims)

    def test_detects_absent(self):
        """Given: Response text contains 'absent'
        When: detect_claims() is called
        Then: Return list containing the claim
        """
        # Arrange
        response = "The required package is absent from the system"

        # Act
        claims = detect_claims(response)

        # Assert
        assert len(claims) > 0
        assert any("absent" in claim.lower() for claim in claims)

    def test_existing_file_patterns_still_work(self):
        """Given: Response text contains existing file existence patterns
        When: detect_claims() is called
        Then: Return list containing the claim (regression check)
        """
        # Arrange
        response = "The file src/config.py exists and contains the settings"

        # Act
        claims = detect_claims(response)

        # Assert
        assert len(claims) > 0
        assert any("exists" in claim.lower() for claim in claims)

    def test_claims_pattern_compilation(self):
        """Given: CLAIM_PATTERNS contains new absence patterns
        When: CLAIM_RE is compiled
        Then: Regex compiles without error and matches absence patterns
        """
        # Assert - Check patterns compile
        assert CLAIM_RE is not None

        # Check absence patterns are in CLAIM_PATTERNS
        absence_patterns = [
            r"\b(?:does|do)\s+not\s+exist\b",
            r"\b(?:doesn't|don't)\s+exist\b",
            r"\b(?:not found|missing|absent)\b",
        ]

        for pattern in absence_patterns:
            assert any(pattern in cp or cp in pattern for cp in CLAIM_PATTERNS), \
                f"Pattern '{pattern}' not found in CLAIM_PATTERNS"

    def test_multiple_absence_claims_detected(self):
        """Given: Response text contains multiple different absence claims
        When: detect_claims() is called
        Then: Return list with multiple claims
        """
        # Arrange
        response = """
        The module doesn't exist in the codebase.
        Additionally, the config file was not found.
        The required package is missing.
        """

        # Act
        claims = detect_claims(response)

        # Assert
        assert len(claims) >= 3
