"""Tests for domain_detector module."""

from __future__ import annotations

import pytest

from core.domain_detector import (
    DOMAIN_KEYWORDS,
    MAX_DOMAINS_PER_QUERY,
    MIN_KEYWORD_MATCHES,
    DomainClassification,
    detect_domain,
)


class TestDetectDomain:
    """Tests for detect_domain() function."""

    def test_empty_query_returns_empty_classification(self):
        """Empty or whitespace query returns empty domains."""
        result = detect_domain("")
        assert result.domains == []
        assert result.confidence == 0.0

        result = detect_domain("   ")
        assert result.domains == []
        assert result.confidence == 0.0

    def test_hook_domain_detection(self):
        """Query about hooks.json triggers hook domain."""
        result = detect_domain("hooks.json bug plugin registration")
        assert "hook" in result.domains

    def test_plugin_domain_detection(self):
        """Query about marketplace triggers plugin domain."""
        result = detect_domain("cc-model-router plugin not firing")
        assert "plugin" in result.domains

    def test_constraint_domain_detection(self):
        """Query with constraint language triggers constraint domain."""
        result = detect_domain("must use settings.json for hook registration")
        assert "constraint" in result.domains

    def test_multiple_domains_detected(self):
        """Query matching multiple domain keywords returns all."""
        result = detect_domain("hooks.json bug must use settings.json")
        assert "hook" in result.domains
        assert "constraint" in result.domains

    def test_confidence_based_on_domain_count(self):
        """Confidence increases with number of matched domains."""
        single = detect_domain("hooks.json")
        multi = detect_domain("hooks.json pretooluse posttooluse plugin .claude-plugin")

        # More domains = higher confidence
        assert multi.confidence > single.confidence

    def test_confidence_max_capped_at_095(self):
        """Confidence is capped at 0.95."""
        long_query = "hooks pretooluse posttooluse " * 10 + ".claude-plugin plugin.json marketplace " * 10
        result = detect_domain(long_query)
        assert result.confidence <= 0.95

    def test_constraint_domain_boosts_confidence(self):
        """Constraint domain match adds bonus to confidence."""
        without_constraint = detect_domain("hooks.json plugin")
        with_constraint = detect_domain("hooks.json plugin settings.json router.py")

        assert with_constraint.confidence > without_constraint.confidence
        assert "constraint" in with_constraint.domains

    def test_domain_cap_enforced(self):
        """No more than MAX_DOMAINS_PER_QUERY domains returned."""
        query = "hooks.json pretooluse posttooluse .claude-plugin plugin.json cks decision entry architecture design adr sdlc tdd /find backend refactor technical debt verify validate audit"
        result = detect_domain(query)
        assert len(result.domains) <= MAX_DOMAINS_PER_QUERY

    def test_matched_keywords_recorded(self):
        """Matched keywords are tracked in matched_keywords."""
        result = detect_domain("hooks.json pretooluse posttooluse")
        assert len(result.matched_keywords) >= 3

    def test_architecture_domain(self):
        """ADR keywords trigger architecture domain."""
        result = detect_domain("design decision architecture ADR")
        assert "architecture" in result.domains

    def test_cks_domain(self):
        """CKS keywords trigger cks domain."""
        result = detect_domain("CKS decision entry pattern")
        assert "cks" in result.domains

    def test_search_domain(self):
        """Slash-search keyword triggers search domain."""
        result = detect_domain("/find backend FTS5 query")
        assert "search" in result.domains

    def test_sdlc_domain(self):
        """SDLC keywords trigger sdcc domain."""
        result = detect_domain("tdd test-driven development CI/CD")
        assert "sdcc" in result.domains

    def test_verification_domain(self):
        """Verification keywords trigger verification domain."""
        result = detect_domain("verify validate audit assertion")
        assert "verification" in result.domains

    def test_refactor_domain(self):
        """Refactor keywords trigger refactor domain."""
        result = detect_domain("refactor technical debt redesign")
        assert "refactor" in result.domains


class TestDomainClassification:
    """Tests for DomainClassification dataclass."""

    def test_has_constraints_true_when_domains_present(self):
        """has_constraints is True when domains list is non-empty."""
        dc = DomainClassification(domains=["hook", "plugin"], confidence=0.7)
        assert dc.has_constraints is True

    def test_has_constraints_false_when_domains_empty(self):
        """has_constraints is False when domains list is empty."""
        dc = DomainClassification(domains=[], confidence=0.0)
        assert dc.has_constraints is False

    def test_default_values(self):
        """Default values are sensible empty values."""
        dc = DomainClassification()
        assert dc.domains == []
        assert dc.confidence == 0.0
        assert dc.matched_keywords == []
        assert dc.has_constraints is False

    def test_matched_keywords_type(self):
        """matched_keywords is list of (domain, keyword) tuples."""
        dc = DomainClassification(
            domains=["hook"],
            matched_keywords=[("hook", "hooks.json"), ("hook", "pretooluse")],
        )
        assert len(dc.matched_keywords) == 2
        assert dc.matched_keywords[0] == ("hook", "hooks.json")
