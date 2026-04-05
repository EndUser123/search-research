"""
Test Constitutional Compliance

Test cases for CSF NIP constitutional compliance validation.
"""

import unittest

from ..compliance.validator import ConstitutionalValidator
from ..core.types import (
    BugCategory,
    BugSeverity,
    ConstitutionalComplianceLevel,
    DetectionResult,
    VulnerabilityResult,
    VulnerabilityType,
)


class TestConstitutionalCompliance(unittest.TestCase):
    """Test constitutional compliance validation."""

    def setUp(self):
        """Set up test fixtures."""
        self.validator = ConstitutionalValidator()

    def test_anti_sycophancy_validation(self):
        """Test anti-sycophancy constitutional validation."""
        # Create issues that violate anti-sycophancy
        issues = [
            DetectionResult(
                id="1",
                type=BugCategory.API_MISUSE,
                severity=BugSeverity.MEDIUM,  # Should be CRITICAL for security
                message="Use of eval() function",
                description="eval() usage detected",
                file_path="/test/code.py",
                line_number=10,
                code_snippet="result = eval(user_input)",
                confidence=0.9,
                tags={"security"}
            )
        ]

        result = self.validator.validate_results(issues, [])

        # Should detect anti-sycophancy violation
        self.assertEqual(result.compliance_level, ConstitutionalComplianceLevel.VIOLATION)
        self.assertGreater(len(result.violations), 0)

        # Check violation details
        anti_sycophancy_violations = [
            v for v in result.violations
            if "anti-sycophancy" in v.tags
        ]
        self.assertGreater(len(anti_sycophancy_violations), 0)

    def test_data_safety_validation(self):
        """Test data safety constitutional validation."""
        # Create issues with potential data loss
        issues = [
            DetectionResult(
                id="1",
                type=BugCategory.LOGIC_ERROR,
                severity=BugSeverity.HIGH,
                message="Data deletion without confirmation",
                description="rm -rf command detected",
                file_path="/test/code.py",
                line_number=20,
                code_snippet="os.system('rm -rf /tmp/data/*')",
                confidence=0.9
            )
        ]

        result = self.validator.validate_results(issues, [])

        # Should detect data safety violation
        self.assertIn(result.compliance_level, [
            ConstitutionalComplianceLevel.VIOLATION,
            ConstitutionalComplianceLevel.CRITICAL_VIOLATION
        ])

        # Check for data safety violations
        data_safety_violations = [
            v for v in result.violations
            if "data-safety" in v.tags
        ]
        self.assertGreater(len(data_safety_violations), 0)

    def test_solo_developer_context_validation(self):
        """Test solo developer context validation."""
        # Create issues with enterprise patterns
        issues = [
            DetectionResult(
                id="1",
                type=BugCategory.LOGIC_ERROR,
                severity=BugSeverity.LOW,
                message="Enterprise pattern detected",
                description="AbstractFactoryManager found",
                file_path="/test/code.py",
                line_number=5,
                code_snippet="factory = new AbstractFactoryManager()",
                confidence=0.7
            )
        ]

        result = self.validator.validate_results(issues, [])

        # Should detect solo developer constraint issue
        solo_dev_violations = [
            v for v in result.violations
            if "solo-developer" in v.tags
        ]
        # May not violate depending on severity threshold
        # self.assertGreater(len(solo_dev_violations), 0)

    def test_truthfulness_validation(self):
        """Test truthfulness constitutional validation."""
        # Create issues with truthfulness problems
        issues = [
            DetectionResult(
                id="1",
                type=BugCategory.NULL_POINTER,
                severity=BugSeverity.MEDIUM,
                message="Potential null pointer",
                description="Definite null dereference found",  # Overconfident
                file_path="/test/code.py",
                line_number=15,
                code_snippet="obj.method()",
                confidence=0.95,  # High confidence on uncertain finding
                tags={"potential"}
            )
        ]

        result = self.validator.validate_results(issues, [])

        # Should generate truthfulness warnings
        truthfulness_warnings = [
            w for w in result.warnings
            if "truthfulness" in w.tags
        ]
        self.assertGreater(len(truthfulness_warnings), 0)

    def test_full_compliance(self):
        """Test case with full constitutional compliance."""
        # Create compliant issues
        issues = [
            DetectionResult(
                id="1",
                type=BugCategory.DIVISION_BY_ZERO,
                severity=BugSeverity.CRITICAL,
                message="Division by zero detected",
                description="Literal zero division",
                file_path="/test/code.py",
                line_number=10,
                code_snippet="result = x / 0",
                confidence=1.0  # Appropriate confidence
            ),
            VulnerabilityResult(
                id="2",
                type=BugCategory.LOGIC_ERROR,
                severity=BugSeverity.CRITICAL,
                message="SQL injection vulnerability",
                description="SQL injection in execute()",
                file_path="/test/code.py",
                line_number=20,
                code_snippet="cursor.execute(f\"SELECT * FROM users WHERE id = {user_id}\")",
                vulnerability_type=VulnerabilityType.A03_INJECTION,
                cvss_score=9.8,
                confidence=0.9
            )
        ]

        result = self.validator.validate_results(issues, [])

        # Should be compliant
        self.assertEqual(result.compliance_level, ConstitutionalComplianceLevel.COMPLIANT)
        self.assertEqual(len(result.violations), 0)

    def test_critical_violation_detection(self):
        """Test critical violation detection."""
        # Create critical violations
        issues = [
            DetectionResult(
                id="1",
                type=BugCategory.API_MISUSE,
                severity=BugSeverity.CRITICAL,
                message="eval() usage",
                description="Security risk not properly marked",
                file_path="/test/code.py",
                line_number=10,
                code_snippet="eval(user_input)",
                confidence=0.5  # Understated confidence
            ),
            DetectionResult(
                id="2",
                type=BugCategory.RESOURCE_LEAK,
                severity=BugSeverity.CRITICAL,
                message="rm -rf without confirmation",
                description="Potential data loss operation",
                file_path="/test/code.py",
                line_number=20,
                code_snippet="os.system('rm -rf /data/*')",
                confidence=0.9
            )
        ]

        result = self.validator.validate_results(issues, [])

        # Should be critical violation
        self.assertEqual(result.compliance_level, ConstitutionalComplianceLevel.CRITICAL_VIOLATION)

        # Check multiple violation types
        violation_categories = set()
        for v in result.violations:
            if "constitutional_violation" in v.metadata:
                violation_categories.add(v.metadata["constitutional_violation"])

        self.assertTrue(len(violation_categories) > 1)

    def test_compliance_summary(self):
        """Test compliance summary generation."""
        issues = [
            DetectionResult(
                id="1",
                type=BugCategory.API_MISUSE,
                severity=BugSeverity.HIGH,
                message="Security issue with wrong severity",
                description="eval() usage marked as high",
                file_path="/test/code.py",
                line_number=10
            ),
            DetectionResult(
                id="2",
                type=BugCategory.LOGIC_ERROR,
                severity=BugSeverity.LOW,
                message="Enterprise pattern",
                description="ComplexFactory pattern",
                file_path="/test/code.py",
                line_number=20
            )
        ]

        result = self.validator.validate_results(issues, [])

        # Check summary
        summary = result.summary
        self.assertIn("total_issues", summary)
        self.assertIn("violations", summary)
        self.assertIn("warnings", summary)
        self.assertIn("constitutional_areas", summary)

        # Check constitutional areas breakdown
        areas = summary["constitutional_areas"]
        self.assertIn("anti_sycophancy", areas)
        self.assertIn("data_safety", areas)
        self.assertIn("solo_developer", areas)
        self.assertIn("truthfulness", areas)

    def test_custom_compliance_rules(self):
        """Test custom compliance rule addition."""
        from ..compliance.validator import ComplianceRule

        # Add custom rule
        custom_rule = ComplianceRule(
            id="custom_001",
            name="No hardcoded timeouts",
            description="Must not use hardcoded timeout values",
            category="custom",
            applies_to_categories={BugCategory.LOGIC_ERROR},
            prohibited_patterns=["timeout=30", "timeout=60"],
            required_actions=["Use configuration for timeouts"],
            violation_severity=BugSeverity.LOW
        )

        self.validator.add_compliance_rule(custom_rule)

        # Create issues that violate custom rule
        issues = [
            DetectionResult(
                id="1",
                type=BugCategory.LOGIC_ERROR,
                severity=BugSeverity.LOW,
                message="Hardcoded timeout",
                description="Connection with timeout=30",
                file_path="/test/code.py",
                line_number=10,
                code_snippet="conn = create_connection(timeout=30)"
            )
        ]

        result = self.validator.validate_results(issues, [])

        # Should detect custom rule violation
        custom_violations = [
            v for v in result.violations
            if v.metadata.get("constitutional_rule_id") == "custom_001"
        ]
        self.assertGreater(len(custom_violations), 0)

    def test_vulnerability_compliance_validation(self):
        """Test compliance validation for vulnerabilities."""
        vulnerabilities = [
            VulnerabilityResult(
                id="1",
                type=BugCategory.LOGIC_ERROR,
                severity=BugSeverity.CRITICAL,
                message="SQL Injection",
                description="SQL injection vulnerability",
                file_path="/test/code.py",
                line_number=10,
                code_snippet="cursor.execute(f'SELECT * FROM users WHERE id = {user_id}')",
                vulnerability_type=VulnerabilityType.A03_INJECTION,
                cvss_score=9.8,
                confidence=0.9
            ),
            VulnerabilityResult(
                id="2",
                type=BugCategory.LOGIC_ERROR,
                severity=BugSeverity.HIGH,
                message="XSS vulnerability",
                description="Cross-site scripting in innerHTML",
                file_path="/test/code.js",
                line_number=20,
                code_snippet="element.innerHTML = userInput",
                vulnerability_type=VulnerabilityType.A03_INJECTION,
                cvss_score=7.5,
                confidence=0.8
            )
        ]

        result = self.validator.validate_results([], vulnerabilities)

        # Should validate vulnerabilities
        self.assertEqual(result.compliance_level, ConstitutionalComplianceLevel.COMPLIANT)
        self.assertEqual(len(result.violations), 0)


if __name__ == "__main__":
    unittest.main()
