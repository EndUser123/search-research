"""
Tests for hypothesis_as_fact_detector module.

Tests cover:
- Entity absence detection
- Entity presence detection
- Rule claim detection
- Epistemic hedge detection
- Confidence scoring
- Risk domain classification
"""


from ..hypothesis_as_fact_detector import (
    ClaimType,
    HypothesisAsFactDetector,
    RawClaim,
    RiskDomain,
)


class TestRawClaim:
    """Test RawClaim dataclass."""

    def test_raw_claim_creation(self):
        """Test creating a RawClaim with all fields."""
        claim = RawClaim(
            text="Package has no skill/ directory",
            subject_entity="packages/handoff",
            claim_type=ClaimType.ENTITY_ABSENCE.value,
            confidence=0.8,
            has_hedge=False,
            risk_domain=RiskDomain.FS_CRITICAL.value,
        )

        assert claim.text == "Package has no skill/ directory"
        assert claim.subject_entity == "packages/handoff"
        assert claim.claim_type == "entity_absence"
        assert claim.confidence == 0.8
        assert claim.has_hedge is False
        assert claim.risk_domain == "FS_CRITICAL"


class TestEntityAbsenceDetection:
    """Test entity absence claim detection."""

    def test_detect_skill_directory_absence(self):
        """Test detecting claims about missing skill/ directories."""
        detector = HypothesisAsFactDetector()
        response = "The package has no skill/ directory, which means it's not a valid plugin."

        claims = detector.detect_claims(response)

        assert len(claims) == 1
        claim = claims[0]
        assert claim.claim_type == ClaimType.ENTITY_ABSENCE.value
        assert "skill/" in claim.text.lower()
        assert claim.risk_domain == RiskDomain.FS_CRITICAL.value

    def test_detect_file_not_exist_claims(self):
        """Test detecting claims that files don't exist."""
        detector = HypothesisAsFactDetector()
        response = "The file packages/handoff/README.md does not exist."

        claims = detector.detect_claims(response)

        assert len(claims) >= 1
        claim = claims[0]
        assert claim.claim_type == ClaimType.ENTITY_ABSENCE.value
        assert "packages/handoff/README.md" in claim.subject_entity
        assert claim.risk_domain == RiskDomain.FS_CRITICAL.value

    def test_detect_lacks_claims(self):
        """Test detecting 'lacks' pattern claims."""
        detector = HypothesisAsFactDetector()
        response = "This package lacks the hooks/ directory needed for automation."

        claims = detector.detect_claims(response)

        assert len(claims) >= 1
        claim = claims[0]
        assert claim.claim_type == ClaimType.ENTITY_ABSENCE.value
        assert "hooks/" in claim.text.lower()

    def test_no_false_positives(self):
        """Test that absence claims aren't falsely detected in presence claims."""
        detector = HypothesisAsFactDetector()
        response = "The package has a skill/ directory and it works great."

        claims = detector.detect_claims(response)

        # Should not detect absence claim
        absence_claims = [c for c in claims if c.claim_type == ClaimType.ENTITY_ABSENCE.value]
        assert len(absence_claims) == 0


class TestEntityPresenceDetection:
    """Test entity presence claim detection."""

    def test_detect_skill_directory_presence(self):
        """Test detecting claims about existing skill/ directories."""
        detector = HypothesisAsFactDetector()
        response = "The package has a skill/ directory that implements core functionality."

        claims = detector.detect_claims(response)

        assert len(claims) >= 1
        claim = claims[0]
        assert claim.claim_type == ClaimType.ENTITY_PRESENCE.value
        assert "skill/" in claim.text.lower()

    def test_detect_documentation_claims(self):
        """Test detecting claims based on documentation."""
        detector = HypothesisAsFactDetector()
        response = "Per the documentation in packages/handoff/README.md, this module supports async operations."

        claims = detector.detect_claims(response)

        assert len(claims) >= 1
        claim = claims[0]
        assert claim.claim_type == ClaimType.ENTITY_PRESENCE.value
        assert claim.subject_entity

    def test_detect_package_exists_claims(self):
        """Test detecting claims that packages exist."""
        detector = HypothesisAsFactDetector()
        response = "The package search-research exists and provides search functionality."

        claims = detector.detect_claims(response)

        assert len(claims) >= 1
        claim = claims[0]
        assert claim.claim_type == ClaimType.ENTITY_PRESENCE.value


class TestRuleClaimDetection:
    """Test rule and system claim detection."""

    def test_detect_documentation_rules(self):
        """Test detecting claims about documentation rules."""
        detector = HypothesisAsFactDetector()
        response = "According to the SKILL.md documentation, all skills must register themselves."

        claims = detector.detect_claims(response)

        assert len(claims) >= 1
        claim = claims[0]
        assert claim.claim_type == ClaimType.RULE.value
        assert claim.risk_domain == RiskDomain.SYSTEM.value

    def test_detect_system_requirements(self):
        """Test detecting claims about system requirements."""
        detector = HypothesisAsFactDetector()
        response = "The system requires all hooks to be idempotent and stateless."

        claims = detector.detect_claims(response)

        assert len(claims) >= 1
        claim = claims[0]
        assert claim.claim_type == ClaimType.RULE.value
        assert claim.risk_domain == RiskDomain.SYSTEM.value

    def test_detect_module_behavior_claims(self):
        """Test detecting claims about module behavior."""
        detector = HypothesisAsFactDetector()
        response = "The SessionStart hook always initializes the daemon manager before execution."

        claims = detector.detect_claims(response)

        assert len(claims) >= 1
        claim = claims[0]
        assert claim.claim_type == ClaimType.RULE.value
        assert "SessionStart" in claim.subject_entity.lower() or claim.subject_entity == "system"

    def test_detect_design_claims(self):
        """Test detecting claims about design decisions."""
        detector = HypothesisAsFactDetector()
        response = "By design, the verification gate always runs before any tool execution."

        claims = detector.detect_claims(response)

        assert len(claims) >= 1
        claim = claims[0]
        assert claim.claim_type == ClaimType.RULE.value


class TestEpistemicHedgeDetection:
    """Test epistemic hedge detection."""

    def test_detect_hedged_claims(self):
        """Test that hedged claims are correctly identified."""
        detector = HypothesisAsFactDetector()
        response = "The package might not have a skill/ directory, but we should check."

        claims = detector.detect_claims(response)

        assert len(claims) >= 1
        claim = claims[0]
        assert claim.has_hedge is True

    def test_detect_multiple_hedge_words(self):
        """Test detection of various hedge words."""
        detector = HypothesisAsFactDetector()

        test_cases = [
            ("The package could be missing the skill/ directory.", True),
            ("It possibly lacks the required hooks/", True),
            ("The file appears to not exist", True),
            ("This seems like a configuration issue", True),
            ("The module probably doesn't exist", True),
            ("The system typically requires this", True),
        ]

        for text, expected_hedge in test_cases:
            claims = detector.detect_claims(text)
            if claims:
                assert claims[0].has_hedge == expected_hedge, f"Failed for: {text}"

    def test_detect_unhedged_strong_assertions(self):
        """Test that strong assertions are marked as unhedged."""
        detector = HypothesisAsFactDetector()
        response = "The package has no skill/ directory and is invalid."

        claims = detector.detect_claims(response)

        assert len(claims) >= 1
        claim = claims[0]
        assert claim.has_hedge is False

    def test_detect_unhedged_variants(self):
        """Test detection of unhedged strong assertions."""
        detector = HypothesisAsFactDetector()

        test_cases = [
            ("The package has no skill/ directory", False),
            ("The file certainly does not exist", False),
            ("This is definitely a bug", False),
            ("The system always validates", False),
        ]

        for text, expected_hedge in test_cases:
            claims = detector.detect_claims(text)
            if claims:
                assert claims[0].has_hedge == expected_hedge, f"Failed for: {text}"


class TestConfidenceScoring:
    """Test confidence score calculation."""

    def test_confidence_range(self):
        """Test that confidence scores are always between 0.0 and 1.0."""
        detector = HypothesisAsFactDetector()
        response = "The package has no skill/ directory."

        claims = detector.detect_claims(response)

        assert all(0.0 <= claim.confidence <= 1.0 for claim in claims)

    def test_hedge_reduces_confidence(self):
        """Test that hedged claims have lower confidence."""
        detector = HypothesisAsFactDetector()

        unhedged = "The package has no skill/ directory."
        hedged = "The package might not have a skill/ directory."

        unhedged_claims = detector.detect_claims(unhedged)
        hedged_claims = detector.detect_claims(hedged)

        if unhedged_claims and hedged_claims:
            assert hedged_claims[0].confidence < unhedged_claims[0].confidence

    def test_specificity_increases_confidence(self):
        """Test that more specific claims have higher confidence."""
        detector = HypothesisAsFactDetector()

        vague = "No directory exists."
        specific = "The package packages/handoff has no skill/ directory according to the filesystem check."

        vague_claims = detector.detect_claims(vague)
        specific_claims = detector.detect_claims(specific)

        if vague_claims and specific_claims:
            # Specific claims should have equal or higher confidence
            assert specific_claims[0].confidence >= vague_claims[0].confidence


class TestRiskDomainClassification:
    """Test risk domain classification."""

    def test_filesystem_claims_critical(self):
        """Test that filesystem claims are classified as FS_CRITICAL."""
        detector = HypothesisAsFactDetector()
        response = "The package has no skill/ directory."

        claims = detector.detect_claims(response)

        assert len(claims) >= 1
        assert claims[0].risk_domain == RiskDomain.FS_CRITICAL.value

    def test_system_claims_system_domain(self):
        """Test that system claims are classified as SYSTEM."""
        detector = HypothesisAsFactDetector()
        response = "The system requires all hooks to be idempotent."

        claims = detector.detect_claims(response)

        assert len(claims) >= 1
        assert claims[0].risk_domain == RiskDomain.SYSTEM.value


class TestSentenceSplitting:
    """Test sentence splitting functionality."""

    def test_multiple_sentences(self):
        """Test detection across multiple sentences."""
        detector = HypothesisAsFactDetector()
        response = "The package has no skill/ directory. Additionally, the system requires all packages to have this directory."

        claims = detector.detect_claims(response)

        # Should detect claims from both sentences
        assert len(claims) >= 2

    def test_ignores_short_sentences(self):
        """Test that very short sentences are ignored."""
        detector = HypothesisAsFactDetector()
        response = "Yes. No. Maybe. The package has no skill/ directory."

        claims = detector.detect_claims(response)

        # Should only detect the actual claim
        assert len(claims) >= 1
        assert all(len(claim.text) > 10 for claim in claims)


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_response(self):
        """Test handling of empty response."""
        detector = HypothesisAsFactDetector()
        response = ""

        claims = detector.detect_claims(response)

        assert len(claims) == 0

    def test_no_claims_response(self):
        """Test response with no detectable claims."""
        detector = HypothesisAsFactDetector()
        response = "I'll help you with that task. Let me start by reading the files."

        claims = detector.detect_claims(response)

        assert len(claims) == 0

    def test_complex_response(self):
        """Test handling of complex multi-claim response."""
        detector = HypothesisAsFactDetector()
        response = """
        The package has no skill/ directory. According to the documentation,
        all plugins must have this directory. The system requires it for
        registration. However, this might be a library package rather than
        a workflow package, which could explain the absence.
        """

        claims = detector.detect_claims(response)

        # Should detect multiple claims
        assert len(claims) >= 3

        # Check that we have different claim types
        claim_types = {claim.claim_type for claim in claims}
        assert ClaimType.ENTITY_ABSENCE.value in claim_types
        assert ClaimType.RULE.value in claim_types

    def test_overlapping_patterns(self):
        """Test handling of overlapping patterns."""
        detector = HypothesisAsFactDetector()
        response = "The package has no skill/ directory and the system requires this directory."

        claims = detector.detect_claims(response)

        # Should detect both claims, not merge them
        assert len(claims) >= 2


class TestFieldAlignment:
    """Test that RawClaim fields align with TASK-007 requirements."""

    def test_field_names_match_spec(self):
        """Test that RawClaim has all required fields with correct names."""
        detector = HypothesisAsFactDetector()
        response = "The package has no skill/ directory."

        claims = detector.detect_claims(response)
        claim = claims[0]

        # Verify all required fields exist
        assert hasattr(claim, "text")
        assert hasattr(claim, "subject_entity")
        assert hasattr(claim, "claim_type")
        assert hasattr(claim, "confidence")
        assert hasattr(claim, "has_hedge")
        assert hasattr(claim, "risk_domain")

        # Verify field types
        assert isinstance(claim.text, str)
        assert isinstance(claim.subject_entity, str)
        assert isinstance(claim.claim_type, str)
        assert isinstance(claim.confidence, float)
        assert isinstance(claim.has_hedge, bool)
        assert isinstance(claim.risk_domain, str)

    def test_field_alignment_future_claim(self):
        """
        Test field alignment for future TASK-007 Claim dataclass.

        This verifies the 1:1 mapping:
        - text → text (same)
        - subject_entity → targets[0] (rename+move)
        - claim_type → type (rename)
        - confidence → confidence (same)
        - has_hedge → has_hedge (same)
        - risk_domain → risk_domain (same)
        """
        detector = HypothesisAsFactDetector()
        response = "The package might not have a skill/ directory."

        claims = detector.detect_claims(response)
        claim = claims[0]

        # Verify field values will map correctly in Phase 2
        assert isinstance(claim.text, str)  # → text (same)
        assert isinstance(claim.subject_entity, str)  # → targets[0] (single item list)
        assert isinstance(claim.claim_type, str)  # → type (rename)
        assert 0.0 <= claim.confidence <= 1.0  # → confidence (same)
        assert isinstance(claim.has_hedge, bool)  # → has_hedge (same)
        assert claim.risk_domain in [
            "FS_CRITICAL",
            "EXTERNAL",
            "SYSTEM",
            "OTHER",
        ]  # → risk_domain (same)
