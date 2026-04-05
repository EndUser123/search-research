#!/usr/bin/env python3
"""
Unit tests for constitutional_compliance_integration module.

Tests for constitutional compliance integration functionality.
"""


from prompting_framework.constitutional_compliance_integration import (
    ComplianceCheck,
    ComplianceConfig,
    CompliancePrinciple,
    ComplianceResult,
)


class TestCompliancePrinciple:
    """Test CompliancePrinciple enum."""

    def test_all_principles_defined(self):
        """Verify all expected principles are defined."""
        expected_principles = [
            "anti_deception",
            "evidence_based",
            "transparency",
            "accountability",
            "fairness",
            "safety",
        ]
        actual_values = [p.value for p in CompliancePrinciple]
        for expected in expected_principles:
            assert expected in actual_values


class TestComplianceCheck:
    """Test ComplianceCheck dataclass."""

    def test_create_check(self):
        """Create a compliance check."""
        check = ComplianceCheck(
            check_id="check_1",
            principle=CompliancePrinciple.ANTI_DECEPTION,
            description="Verify response is not deceptive",
            required=True,
            severity="high",
        )
        assert check.principle == CompliancePrinciple.ANTI_DECEPTION
        assert check.required is True

    def test_optional_check(self):
        """Create optional compliance check."""
        check = ComplianceCheck(
            check_id="optional",
            principle=CompliancePrinciple.TRANSPARENCY,
            description="Check for transparency",
            required=False,
            severity="low",
        )
        assert check.required is False


class TestComplianceResult:
    """Test ComplianceResult dataclass."""

    def test_create_result_passing(self):
        """Create passing compliance result."""
        result = ComplianceResult(
            principle=CompliancePrinciple.EVIDENCE_BASED,
            passed=True,
            confidence=0.95,
            details="Response includes supporting evidence",
            issues=[],
        )
        assert result.passed is True
        assert result.confidence == 0.95
        assert len(result.issues) == 0

    def test_create_result_failing(self):
        """Create failing compliance result."""
        result = ComplianceResult(
            principle=CompliancePrinciple.ANTI_DECEPTION,
            passed=False,
            confidence=0.7,
            details="Response may contain misleading claims",
            issues=[
                "Unsubstantiated claim detected",
                "Missing source for statistic",
            ],
        )
        assert result.passed is False
        assert len(result.issues) == 2


class TestComplianceConfig:
    """Test ComplianceConfig dataclass."""

    def test_create_config(self):
        """Create compliance configuration."""
        checks = [
            ComplianceCheck(
                check_id="c1",
                principle=CompliancePrinciple.ANTI_DECEPTION,
                description="Check for deception",
                required=True,
                severity="high",
            ),
            ComplianceCheck(
                check_id="c2",
                principle=CompliancePrinciple.EVIDENCE_BASED,
                description="Check for evidence",
                required=True,
                severity="medium",
            ),
        ]

        config = ComplianceConfig(
            config_id="config_1",
            checks=checks,
            enforce_all_required=True,
            allow_partial_compliance=False,
        )
        assert len(config.checks) == 2
        assert config.enforce_all_required is True

    def test_config_optional_only(self):
        """Config with only optional checks."""
        config = ComplianceConfig(
            config_id="optional_only",
            checks=[
                ComplianceCheck(
                    check_id="opt",
                    principle=CompliancePrinciple.TRANSPARENCY,
                    description="Optional transparency check",
                    required=False,
                    severity="low",
                )
            ],
            enforce_all_required=False,
            allow_partial_compliance=True,
        )
        assert config.allow_partial_compliance is True


class TestCompliancePrinciples:
    """Test different compliance principles."""

    def test_anti_deception_principle(self):
        """Anti-deception compliance principle."""
        assert CompliancePrinciple.ANTI_DECEPTION.value == "anti_deception"

    def test_evidence_based_principle(self):
        """Evidence-based compliance principle."""
        assert CompliancePrinciple.EVIDENCE_BASED.value == "evidence_based"

    def test_transparency_principle(self):
        """Transparency compliance principle."""
        assert CompliancePrinciple.TRANSPARENCY.value == "transparency"

    def test_accountability_principle(self):
        """Accountability compliance principle."""
        assert CompliancePrinciple.ACCOUNTABILITY.value == "accountability"

    def test_fairness_principle(self):
        """Fairness compliance principle."""
        assert CompliancePrinciple.FAIRNESS.value == "fairness"

    def test_safety_principle(self):
        """Safety compliance principle."""
        assert CompliancePrinciple.SAFETY.value == "safety"


class TestEdgeCases:
    """Test edge cases for compliance."""

    def test_perfect_compliance(self):
        """Perfect compliance score."""
        result = ComplianceResult(
            principle=CompliancePrinciple.SAFETY,
            passed=True,
            confidence=1.0,
            details="Fully compliant",
            issues=[],
        )
        assert result.passed is True
        assert result.confidence == 1.0

    def test_borderline_compliance(self):
        """Borderline compliance."""
        result = ComplianceResult(
            principle=CompliancePrinciple.FAIRNESS,
            passed=True,
            confidence=0.51,
            details="Barely compliant",
            issues=["Minor bias detected"],
        )
        assert result.passed is True
        assert 0.5 < result.confidence < 0.6

    def test_empty_checks_config(self):
        """Config with no compliance checks."""
        config = ComplianceConfig(
            config_id="empty",
            checks=[],
        )
        assert len(config.checks) == 0


class TestComplianceScenarios:
    """Test various compliance scenarios."""

    def test_multi_principle_compliance(self):
        """Compliance across multiple principles."""
        results = [
            ComplianceResult(
                principle=CompliancePrinciple.ANTI_DECEPTION,
                passed=True,
                confidence=0.9,
                details="",
                issues=[],
            ),
            ComplianceResult(
                principle=CompliancePrinciple.EVIDENCE_BASED,
                passed=True,
                confidence=0.85,
                details="",
                issues=[],
            ),
            ComplianceResult(
                principle=CompliancePrinciple.TRANSPARENCY,
                passed=False,
                confidence=0.7,
                details="",
                issues=["Unclear sourcing"],
            ),
        ]
        passed = [r for r in results if r.passed]
        assert len(passed) == 2

    def test_high_severity_failure(self):
        """High severity compliance failure."""
        result = ComplianceResult(
            principle=CompliancePrinciple.SAFETY,
            passed=False,
            confidence=0.9,
            details="Safety violation detected",
            issues=["Harmful content", "Unsafe recommendation"],
        )
        assert result.passed is False
        assert len(result.issues) == 2
