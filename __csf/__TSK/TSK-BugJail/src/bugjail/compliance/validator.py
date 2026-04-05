"""
BugJail Constitutional Compliance Validator

Validates detected issues against CSF NIP constitutional requirements
and security policies.
"""

import uuid
from dataclasses import dataclass
from typing import Any

from ..core.types import (
    BugCategory,
    BugSeverity,
    ConstitutionalComplianceLevel,
    DetectionResult,
    VulnerabilityResult,
    VulnerabilityType,
)


@dataclass
class ComplianceRule:
    """Rule for constitutional compliance validation."""

    id: str
    name: str
    description: str
    category: str  # e.g., "anti-sycophancy", "data-safety", "exploration-before-planning"

    # Rule conditions
    applies_to_categories: set[BugCategory]
    applies_to_vulnerabilities: set[VulnerabilityType]
    min_severity: BugSeverity = BugSeverity.LOW

    # Compliance requirements
    required_actions: list[str]
    prohibited_patterns: list[str]
    required_documentation: list[str]

    # Violation levels
    violation_severity: BugSeverity = BugSeverity.MEDIUM
    auto_violation: bool = False


@dataclass
class ComplianceResult:
    """Result of compliance validation."""

    compliance_level: ConstitutionalComplianceLevel
    violations: list[DetectionResult]
    warnings: list[DetectionResult]
    summary: dict[str, Any]


class ConstitutionalValidator:
    """
    Validates bug detection results against constitutional requirements.

    Enforces CSF NIP constitutional constraints including:
    - Anti-sycophancy requirements
    - Data safety protocols
    - Exploration-before-planning mandate
    - Truthfulness and verification
    - Atomic separation of concerns
    - Solo developer context constraints
    """

    def __init__(self):
        """Initialize constitutional validator."""
        self.compliance_rules = self._initialize_compliance_rules()

    def validate_results(
        self,
        bugs: list[DetectionResult],
        vulnerabilities: list[VulnerabilityResult]
    ) -> ComplianceResult:
        """
        Validate detection results against constitutional requirements.

        Args:
            bugs: List of detected bugs
            vulnerabilities: List of detected vulnerabilities

        Returns:
            Compliance validation result
        """
        violations = []
        warnings = []

        all_issues = bugs + vulnerabilities

        # Check each rule
        for rule in self.compliance_rules:
            rule_violations = self._check_rule(rule, all_issues)
            violations.extend(rule_violations)

        # Apply constitutional constraints

        # 1. Anti-sycophancy validation
        anti_sycophancy_violations = self._validate_anti_sycophancy(all_issues)
        violations.extend(anti_sycophancy_violations)

        # 2. Data safety validation
        data_safety_violations = self._validate_data_safety(all_issues)
        violations.extend(data_safety_violations)

        # 3. Solo developer context validation
        solo_dev_violations = self._validate_solo_developer_context(all_issues)
        violations.extend(solo_dev_violations)

        # 4. Truthfulness validation
        truthfulness_warnings = self._validate_truthfulness(all_issues)
        warnings.extend(truthfulness_warnings)

        # Determine overall compliance level
        if any(v.severity == BugSeverity.CRITICAL for v in violations):
            compliance_level = ConstitutionalComplianceLevel.CRITICAL_VIOLATION
        elif violations:
            compliance_level = ConstitutionalComplianceLevel.VIOLATION
        elif warnings:
            compliance_level = ConstitutionalComplianceLevel.WARNING
        else:
            compliance_level = ConstitutionalComplianceLevel.COMPLIANT

        # Create summary
        summary = {
            "total_issues": len(all_issues),
            "violations": len(violations),
            "warnings": len(warnings),
            "compliance_level": compliance_level.value,
            "rules_checked": len(self.compliance_rules),
            "constitutional_areas": {
                "anti_sycophancy": len(anti_sycophancy_violations),
                "data_safety": len(data_safety_violations),
                "solo_developer": len(solo_dev_violations),
                "truthfulness": len(truthfulness_warnings)
            }
        }

        return ComplianceResult(
            compliance_level=compliance_level,
            violations=violations,
            warnings=warnings,
            summary=summary
        )

    def _initialize_compliance_rules(self) -> list[ComplianceRule]:
        """Initialize constitutional compliance rules."""
        return [
            # Anti-sycophancy rules
            ComplianceRule(
                id="anti_sycophancy_001",
                name="No Agreement with False Premises",
                description="Must not agree with or validate incorrect code patterns",
                category="anti-sycophancy",
                applies_to_categories={BugCategory.LOGIC_ERROR, BugCategory.API_MISUSE},
                prohibited_patterns=["eval()", "exec()", "shell=True"],
                required_actions=["Identify pattern as incorrect", "Provide safe alternative"],
                violation_severity=BugSeverity.HIGH
            ),

            # Data safety rules
            ComplianceRule(
                id="data_safety_001",
                name="Prevent Catastrophic Data Loss",
                description="Must prevent operations that could cause data loss",
                category="data_safety",
                applies_to_categories={BugCategory.RESOURCE_LEAK, BugCategory.ARRAY_BOUNDS},
                min_severity=BugSeverity.HIGH,
                required_actions=["Flag for user confirmation", "Suggest backup"],
                violation_severity=BugSeverity.CRITICAL,
                auto_violation=True
            ),

            # Exploration-before-planning rules
            ComplianceRule(
                id="exploration_001",
                name="Must Explore Before Planning",
                description="Solutions must be based on existing code analysis",
                category="exploration-before-planning",
                applies_to_categories=set(),
                required_actions=["Provide exploration evidence", "Reference existing code"],
                violation_severity=BugSeverity.MEDIUM
            ),

            # Truthfulness rules
            ComplianceRule(
                id="truthfulness_001",
                name="Honest Confidence Scoring",
                description="Confidence scores must reflect actual certainty",
                category="truthfulness",
                applies_to_categories=set(),
                required_actions=["Justify confidence levels", "Document uncertainty"],
                violation_severity=BugSeverity.MEDIUM
            ),

            # Solo developer context rules
            ComplianceRule(
                id="solo_dev_001",
                name="No Enterprise Over-Engineering",
                description="Avoid patterns too complex for solo development",
                category="solo-developer",
                applies_to_categories={BugCategory.LOGIC_ERROR},
                prohibited_patterns=["AbstractFactory", "ObserverPatternManager", "DependencyInjectionContainer"],
                violation_severity=BugSeverity.LOW
            )
        ]

    def _check_rule(self, rule: ComplianceRule, issues: list[DetectionResult]) -> list[DetectionResult]:
        """Check a specific compliance rule against issues."""
        violations = []

        for issue in issues:
            # Check if rule applies to this issue
            if not self._rule_applies(rule, issue):
                continue

            # Check for prohibited patterns
            for pattern in rule.prohibited_patterns:
                if pattern.lower() in issue.description.lower() or \
                   pattern.lower() in issue.code_snippet.lower():
                    violation = self._create_violation(rule, issue, f"Contains prohibited pattern: {pattern}")
                    violations.append(violation)

            # Check if required actions are documented
            if rule.required_actions and not issue.metadata.get("required_actions"):
                violation = self._create_violation(rule, issue, "Missing required action documentation")
                violations.append(violation)

            # Auto-violation if configured
            if rule.auto_violation and issue.severity.value >= rule.min_severity.value:
                violation = self._create_violation(rule, issue, "Automatic constitutional violation")
                violations.append(violation)

        return violations

    def _validate_anti_sycophancy(self, issues: list[DetectionResult]) -> list[DetectionResult]:
        """Validate anti-sycophancy constitutional requirements."""
        violations = []

        # Check for issues that might enable incorrect behavior
        dangerous_patterns = ["eval(", "exec(", "subprocess.call", "os.system", "shell=True"]

        for issue in issues:
            if any(pattern in issue.code_snippet for pattern in dangerous_patterns):
                if issue.severity != BugSeverity.CRITICAL:
                    # Should be marked as critical for security issues
                    violation = DetectionResult(
                        id=str(uuid.uuid4()),
                        type=BugCategory.LOGIC_ERROR,
                        severity=BugSeverity.HIGH,
                        message="Anti-sycophancy violation: Security issue not marked as critical",
                        description="Security vulnerabilities must be marked with appropriate severity",
                        file_path=issue.file_path,
                        line_number=issue.line_number,
                        code_snippet=issue.code_snippet,
                        confidence=0.9,
                        tags={"constitutional", "anti-sycophancy"},
                        metadata={
                            "constitutional_violation": "anti_sycophancy",
                            "original_issue_id": issue.id
                        }
                    )
                    violations.append(violation)

        return violations

    def _validate_data_safety(self, issues: list[DetectionResult]) -> list[DetectionResult]:
        """Validate data safety constitutional requirements."""
        violations = []

        # Look for potential data loss patterns
        data_loss_patterns = ["rm -rf", "delete(", "DROP TABLE", "TRUNCATE"]

        for issue in issues:
            for pattern in data_loss_patterns:
                if pattern in issue.code_snippet.lower():
                    violation = DetectionResult(
                        id=str(uuid.uuid4()),
                        type=BugCategory.LOGIC_ERROR,
                        severity=BugSeverity.CRITICAL,
                        message="Data safety violation: Potential data loss operation detected",
                        description="Operations that could cause data loss must require explicit user confirmation",
                        file_path=issue.file_path,
                        line_number=issue.line_number,
                        code_snippet=issue.code_snippet,
                        confidence=0.8,
                        tags={"constitutional", "data-safety"},
                        metadata={
                            "constitutional_violation": "data_safety",
                            "dangerous_pattern": pattern
                        }
                    )
                    violations.append(violation)

        return violations

    def _validate_solo_developer_context(self, issues: list[DetectionResult]) -> list[DetectionResult]:
        """Validate solo developer context constraints."""
        violations = []

        # Look for enterprise patterns
        enterprise_patterns = [
            "AbstractFactory", "FactoryManager", "ServiceLocator",
            "AspectManager", "TransactionManager", "CacheManager"
        ]

        for issue in issues:
            for pattern in enterprise_patterns:
                if pattern in issue.code_snippet:
                    violation = DetectionResult(
                        id=str(uuid.uuid4()),
                        type=BugCategory.LOGIC_ERROR,
                        severity=BugSeverity.LOW,
                        message="Solo developer constraint: Enterprise pattern detected",
                        description="Avoid enterprise patterns that add unnecessary complexity",
                        file_path=issue.file_path,
                        line_number=issue.line_number,
                        code_snippet=issue.code_snippet,
                        confidence=0.7,
                        tags={"constitutional", "solo-developer"},
                        metadata={
                            "constitutional_violation": "solo_developer",
                            "enterprise_pattern": pattern
                        }
                    )
                    violations.append(violation)

        return violations

    def _validate_truthfulness(self, issues: list[DetectionResult]) -> list[DetectionResult]:
        """Validate truthfulness constitutional requirements."""
        warnings = []

        for issue in issues:
            # Check confidence scores
            if issue.confidence > 0.9 and "potential" in issue.description.lower():
                warning = DetectionResult(
                    id=str(uuid.uuid4()),
                    type=BugCategory.LOGIC_ERROR,
                    severity=BugSeverity.LOW,
                    message="Truthfulness warning: High confidence on uncertain finding",
                    description="Confidence score may not reflect uncertainty in detection",
                    file_path=issue.file_path,
                    line_number=issue.line_number,
                    code_snippet=issue.code_snippet,
                    confidence=0.6,
                    tags={"constitutional", "truthfulness"},
                    metadata={
                        "constitutional_warning": "truthfulness",
                        "original_confidence": issue.confidence
                    }
                )
                warnings.append(warning)

            # Check for unsubstantiated claims
            if issue.confidence < 0.5 and not issue.description.startswith("Potential"):
                warning = DetectionResult(
                    id=str(uuid.uuid4()),
                    type=BugCategory.LOGIC_ERROR,
                    severity=BugSeverity.LOW,
                    message="Truthfulness warning: Unsubstantiated claim",
                    description="Low confidence findings should be explicitly marked as potential",
                    file_path=issue.file_path,
                    line_number=issue.line_number,
                    code_snippet=issue.code_snippet,
                    confidence=0.6,
                    tags={"constitutional", "truthfulness"},
                    metadata={
                        "constitutional_warning": "truthfulness",
                        "original_confidence": issue.confidence
                    }
                )
                warnings.append(warning)

        return warnings

    def _rule_applies(self, rule: ComplianceRule, issue: DetectionResult) -> bool:
        """Check if a compliance rule applies to an issue."""
        # Check category
        if rule.applies_to_categories and issue.type not in rule.applies_to_categories:
            return False

        # Check vulnerability type
        if hasattr(issue, 'vulnerability_type'):
            if rule.applies_to_vulnerabilities and issue.vulnerability_type not in rule.applies_to_vulnerabilities:
                return False

        # Check minimum severity
        severity_order = {
            BugSeverity.INFO: 0,
            BugSeverity.LOW: 1,
            BugSeverity.MEDIUM: 2,
            BugSeverity.HIGH: 3,
            BugSeverity.CRITICAL: 4
        }

        if severity_order.get(issue.severity, 0) < severity_order.get(rule.min_severity, 0):
            return False

        return True

    def _create_violation(
        self,
        rule: ComplianceRule,
        original_issue: DetectionResult,
        reason: str
    ) -> DetectionResult:
        """Create a constitutional violation result."""
        return DetectionResult(
            id=str(uuid.uuid4()),
            type=BugCategory.LOGIC_ERROR,
            severity=rule.violation_severity,
            message=f"Constitutional violation: {rule.name}",
            description=f"{rule.description}. {reason}",
            file_path=original_issue.file_path,
            line_number=original_issue.line_number,
            code_snippet=original_issue.code_snippet,
            function_name=original_issue.function_name,
            confidence=0.9,
            tags={"constitutional", "violation", rule.category},
            metadata={
                "constitutional_rule_id": rule.id,
                "constitutional_rule": rule.name,
                "constitutional_category": rule.category,
                "original_issue_id": original_issue.id,
                "violation_reason": reason
            }
        )

    def get_compliance_rules(self) -> list[ComplianceRule]:
        """Get all compliance rules."""
        return self.compliance_rules.copy()

    def add_compliance_rule(self, rule: ComplianceRule):
        """Add a new compliance rule."""
        self.compliance_rules.append(rule)
