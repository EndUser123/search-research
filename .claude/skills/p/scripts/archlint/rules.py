# SPDX-License-Identifier: MIT
"""SOLID principles validation rules.

This module provides validation logic for SOLID principles in software architecture:
- Single Responsibility Principle (SRP)
- Open/Closed Principle (OCP)
- Liskov Substitution Principle (LSP)
- Interface Segregation Principle (ISP)
- Dependency Inversion Principle (DIP)

The SOLIDValidator class evaluates an ArchitectureContext against these principles
and returns detailed violation information when issues are detected.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from archlint.core import ArchitectureContext

__all__ = [
    "ClassLike",
    "ValidationResult",
    "SOLIDValidator",
]


class ClassLike(Protocol):
    """Protocol for objects that can be validated as classes.

    This protocol defines the expected interface for validation targets
    passed to SOLID validation methods. Using a Protocol allows mypy to
    type-check code that uses dynamic object attributes without requiring
    a common base class.
    """

    name: str
    responsibilities: list[str] | None
    methods: list[str] | None
    concerns: list[str] | None


@dataclass(slots=True)
class ValidationResult:
    """Result of architectural validation.

    Attributes:
        score: Compliance score from 0.0 to 1.0
        violations: List of violation dictionaries
        is_compliant: Whether validation passed
    """

    score: float
    violations: list[dict[str, object]]
    is_compliant: bool


class SOLIDValidator:
    """Validator for SOLID principles in software architecture.

    This validator evaluates software architectures against the five SOLID principles
    to identify potential design violations and provide actionable recommendations.

    Each validation method examines a specific principle and returns a list of
    violations found. An empty list indicates compliance with that principle.

    PERF-001 Fix: Violations are capped at MAX_VIOLATIONS to prevent unbounded
    memory growth on large architectures.

    Attributes:
        MAX_VIOLATIONS: Maximum number of violations to track (prevents OOM)
        MAX_INTERFACE_METHODS: Maximum methods before ISP violation
        MAX_RESPONSIBILITIES: Maximum responsibilities before SRP violation

    Example:
        >>> validator = SOLIDValidator()
        >>> violations = validator.validate_single_responsibility(context)
        >>> if violations:
        ...     for v in violations:
        ...         print(f"{v['rule_id']}: {v['description']}")
    """

    # Maximum number of violations to track (prevents OOM on large architectures)
    MAX_VIOLATIONS = 1000

    # Maximum number of methods allowed in an interface before triggering ISP violation
    MAX_INTERFACE_METHODS = 3

    # Maximum number of responsibilities allowed in a class before triggering SRP violation
    MAX_RESPONSIBILITIES = 1

    # Score calculation constants
    VIOLATION_PENALTY = 0.1  # Penalty per violation
    MAX_PENALTY_VIOLATIONS = 10  # Cap penalties at this many violations

    def validate_single_responsibility(
        self, context: ArchitectureContext
    ) -> list[dict[str, object]]:
        """Validate Single Responsibility Principle (SRP).

        SRP states that a class should have one reason to change, meaning it should
        have only one responsibility. Classes with multiple responsibilities are
        harder to maintain, test, and understand.

        Args:
            context: ArchitectureContext containing architecture information including
                    classes with their responsibilities

        Returns:
            List of violation dicts with keys:
                - class_name: Name of the violating class
                - rule_id: 'SRP-001'
                - severity: 'high'
                - description: Human-readable violation description
                - location: Class name
                - recommendation: Suggested fix

            Empty list if architecture complies with SRP.
        """
        violations: list[dict[str, object]] = []

        if not hasattr(context, "classes"):
            return violations

        for cls in context.classes:
            if self._has_multiple_responsibilities(cls):
                violations.append(self._create_srp_violation(cls))

        return violations

    def validate_open_closed(
        self, context: ArchitectureContext
    ) -> list[dict[str, object]]:
        """Validate Open/Closed Principle (OCP).

        OCP states that software entities should be open for extension but closed
        for modification. This principle is violated when code uses conditional
        logic instead of polymorphism and extensions.

        Args:
            context: ArchitectureContext containing architecture information including
                    classes and extension mechanisms

        Returns:
            List of violation dicts with keys:
                - name: Name of the violating class
                - rule_id: 'OCP-001'
                - severity: 'medium'
                - description: Human-readable violation description
                - location: Class name
                - recommendation: Suggested fix

            Empty list if architecture complies with OCP.
        """
        violations: list[dict[str, object]] = []

        if not self._lacks_extensions(context):
            return violations

        if not hasattr(context, "classes"):
            return violations

        for cls in context.classes:
            if self._has_conditional_logic(cls):
                violations.append(self._create_ocp_violation(cls))

        return violations

    def validate_liskov_substitution(
        self, context: ArchitectureContext
    ) -> list[dict[str, object]]:
        """Validate Liskov Substitution Principle (LSP).

        LSP states that objects of a superclass should be replaceable with objects
        of a subclass without breaking the application. This requires that
        subclasses maintain the contract defined by their base classes.

        Args:
            context: ArchitectureContext containing architecture information including
                    inheritance hierarchies and compatibility information

        Returns:
            List of violation dicts with keys:
                - name: Base class name
                - rule_id: 'LSP-001'
                - severity: 'high'
                - description: Human-readable violation description
                - location: Base class name
                - recommendation: Suggested fix

            Empty list if architecture complies with LSP.
        """
        violations: list[dict[str, object]] = []

        if not hasattr(context, "inheritance_hierarchy"):
            return violations

        for hierarchy in context.inheritance_hierarchy:
            if not hierarchy.get("compatible", True):
                violations.append(self._create_lsp_violation(hierarchy))

        return violations

    def validate_interface_segregation(
        self, context: ArchitectureContext
    ) -> list[dict[str, object]]:
        """Validate Interface Segregation Principle (ISP).

        ISP states that clients should not be forced to depend on interfaces they
        don't use. Large, "fat" interfaces should be split into smaller, more
        focused interfaces.

        Args:
            context: ArchitectureContext containing architecture information including
                    interfaces with their methods

        Returns:
            List of violation dicts with keys:
                - name: Interface name
                - rule_id: 'ISP-001'
                - severity: 'medium'
                - description: Human-readable violation description
                - location: Interface name
                - recommendation: Suggested fix

            Empty list if architecture complies with ISP.
        """
        violations: list[dict[str, object]] = []

        if not hasattr(context, "interfaces"):
            return violations

        for interface in context.interfaces:
            if self._is_interface_too_large(interface):
                violations.append(self._create_isp_violation(interface))

        return violations

    def validate_dependency_inversion(
        self, context: ArchitectureContext
    ) -> list[dict[str, object]]:
        """Validate Dependency Inversion Principle (DIP).

        DIP states that high-level modules should not depend on low-level modules;
        both should depend on abstractions. Abstractions should not depend on details;
        details should depend on abstractions.

        Args:
            context: ArchitectureContext containing architecture information including
                    high-level modules and their dependencies

        Returns:
            List of violation dicts with keys:
                - name: Module name
                - rule_id: 'DIP-001'
                - severity: 'high'
                - description: Human-readable violation description
                - location: Module name
                - recommendation: Suggested fix

            Empty list if architecture complies with DIP.
        """
        violations: list[dict[str, object]] = []

        if not hasattr(context, "high_level_modules"):
            return violations

        for module in context.high_level_modules:
            if self._depends_on_concretions(module):
                violations.append(self._create_dip_violation(module))

        return violations

    def validate_separation_of_concerns(
        self, context: ArchitectureContext
    ) -> list[dict[str, object]]:
        """Validate separation of concerns in the architecture.

        Separation of concerns is a fundamental design principle stating that a
        software system must be decomposed into features (concerns) that overlap
        in functionality as little as possible. Modules should have clear,
        single-purpose boundaries.

        Args:
            context: ArchitectureContext containing architecture information including
                    modules and their concerns

        Returns:
            List of violation dicts with keys:
                - name: Module name
                - rule_id: 'SOC-001'
                - severity: 'high'
                - description: Human-readable violation description
                - location: Module name
                - recommendation: Suggested fix

            Empty list if architecture has proper separation of concerns.
        """
        violations: list[dict[str, object]] = []

        if not hasattr(context, "modules"):
            return violations

        for module in context.modules:
            if self._has_mixed_concerns(module):
                violations.append(self._create_soc_violation(module))

        return violations

    # Helper methods to reduce code duplication

    def _has_list_attribute_exceeding(
        self, obj: Any, attr_name: str, threshold: int
    ) -> bool:
        """Check if an object has a list attribute that exceeds a threshold.

        Common pattern for checking responsibilities, concerns, and methods.

        Args:
            obj: Object to check
            attr_name: Name of the list attribute to check
            threshold: Maximum allowed length before returning True

        Returns:
            True if attribute exists, is not None, and length > threshold
        """
        attr_value = getattr(obj, attr_name, None)
        return attr_value is not None and len(attr_value) > threshold

    def _has_multiple_responsibilities(self, cls: ClassLike) -> bool:
        """Check if a class has multiple responsibilities.

        Args:
            cls: Class object to check

        Returns:
            True if class has more than one responsibility, False otherwise
        """
        return self._has_list_attribute_exceeding(
            cls, "responsibilities", self.MAX_RESPONSIBILITIES
        )

    def _has_conditional_logic(self, cls: ClassLike) -> bool:
        """Check if a class uses conditional logic instead of extensions.

        Args:
            cls: Class object to check

        Returns:
            True if class has conditional logic flag set, False otherwise
        """
        return (
            hasattr(cls, "has_conditional_logic") and cls.has_conditional_logic is True
        )

    def _lacks_extensions(self, context: ArchitectureContext) -> bool:
        """Check if context lacks extension mechanisms.

        Args:
            context: ArchitectureContext to check

        Returns:
            True if has_extensions is False, False otherwise
        """
        return hasattr(context, "has_extensions") and context.has_extensions is False

    def _depends_on_concretions(self, module: ClassLike) -> bool:
        """Check if a module depends on concrete implementations.

        Args:
            module: Module object to check

        Returns:
            True if module depends on concretions, False otherwise
        """
        return (
            hasattr(module, "depends_on_concretions")
            and module.depends_on_concretions is True
        )

    def _has_mixed_concerns(self, module: ClassLike) -> bool:
        """Check if a module has mixed concerns.

        Args:
            module: Module object to check

        Returns:
            True if module has more than one concern, False otherwise
        """
        return self._has_list_attribute_exceeding(module, "concerns", 1)

    def _is_interface_too_large(self, interface: ClassLike) -> bool:
        """Check if an interface has too many methods.

        Args:
            interface: Interface object to check

        Returns:
            True if interface has more than MAX_INTERFACE_METHODS, False otherwise
        """
        return self._has_list_attribute_exceeding(
            interface, "methods", self.MAX_INTERFACE_METHODS
        )

    def _create_srp_violation(self, cls: ClassLike) -> dict[str, object]:
        """Create a violation dict for SRP violation.

        Args:
            cls: Class that violates SRP

        Returns:
            Violation dictionary
        """
        return {
            "class_name": cls.name,
            "rule_id": "SRP-001",
            "severity": "high",
            "description": f"Class {cls.name} has multiple responsibilities: {cls.responsibilities}",
            "location": f"{cls.name}",
            "recommendation": "Split the class into separate classes, each with a single responsibility",
        }

    def _create_ocp_violation(self, cls: ClassLike) -> dict[str, object]:
        """Create a violation dict for OCP violation.

        Args:
            cls: Class that violates OCP

        Returns:
            Violation dictionary
        """
        return {
            "name": cls.name,
            "rule_id": "OCP-001",
            "severity": "medium",
            "description": f"Class {cls.name} uses conditional logic instead of extensions",
            "location": f"{cls.name}",
            "recommendation": "Use inheritance or composition to extend functionality without modifying the class",
        }

    def _create_lsp_violation(self, hierarchy: dict[str, object]) -> dict[str, object]:
        """Create a violation dict for LSP violation.

        Args:
            hierarchy: Inheritance hierarchy dict with violation info

        Returns:
            Violation dictionary
        """
        return {
            "name": hierarchy["base_class"],
            "rule_id": "LSP-001",
            "severity": "high",
            "description": f"Liskov substitution violation in {hierarchy['base_class']}: {hierarchy.get('reason', 'Derived class cannot be substituted')}",
            "location": f"{hierarchy['base_class']}",
            "recommendation": "Ensure derived classes can be substituted for their base classes without changing behavior",
        }

    def _create_isp_violation(self, interface: ClassLike) -> dict[str, object]:
        """Create a violation dict for ISP violation.

        Args:
            interface: Interface that violates ISP

        Returns:
            Violation dictionary
        """
        method_count = len(interface.methods) if interface.methods else 0
        return {
            "name": interface.name,
            "rule_id": "ISP-001",
            "severity": "medium",
            "description": f"Interface {interface.name} is too large with {method_count} methods",
            "location": f"{interface.name}",
            "recommendation": "Split the interface into smaller, more focused interfaces",
        }

    def _create_dip_violation(self, module: ClassLike) -> dict[str, object]:
        """Create a violation dict for DIP violation.

        Args:
            module: Module that violates DIP

        Returns:
            Violation dictionary
        """
        return {
            "name": module.name,
            "rule_id": "DIP-001",
            "severity": "high",
            "description": f"Module {module.name} depends on concrete implementations instead of abstractions",
            "location": f"{module.name}",
            "recommendation": "Depend on abstractions (interfaces) rather than concrete implementations",
        }

    def _create_soc_violation(self, module: ClassLike) -> dict[str, object]:
        """Create a violation dict for separation of concerns violation.

        Args:
            module: Module that violates separation of concerns

        Returns:
            Violation dictionary
        """
        return {
            "name": module.name,
            "rule_id": "SOC-001",
            "severity": "high",
            "description": f"Module {module.name} has mixed concerns: {module.concerns}",
            "location": f"{module.name}",
            "recommendation": "Separate concerns into distinct modules with clear boundaries",
        }

    def validate(self, context: ArchitectureContext) -> ValidationResult:
        """
        Run all SOLID validations and return aggregated result.

        PERF-001 Fix: Violations are capped at MAX_VIOLATIONS to prevent OOM.
        EMPTY-001 Fix: Empty projects return score 0.0 with critical violation.
        """
        # Check for empty project
        is_empty = (
            context.metadata.get("is_empty", False)
            if hasattr(context, "metadata")
            else False
        )

        if is_empty:
            return ValidationResult(
                score=0.0,
                violations=[
                    {
                        "rule_id": "EMPTY-001",
                        "severity": "critical",
                        "description": "Empty project detected: No Python files found to validate",
                        "location": "Project root",
                        "recommendation": "Add Python source files to the project before validation",
                    }
                ],
                is_compliant=False,
            )

        # Run all SOLID validations
        all_violations: list[dict[str, object]] = []
        all_violations.extend(self.validate_single_responsibility(context))
        all_violations.extend(self.validate_open_closed(context))
        all_violations.extend(self.validate_liskov_substitution(context))
        all_violations.extend(self.validate_interface_segregation(context))
        all_violations.extend(self.validate_dependency_inversion(context))
        all_violations.extend(self.validate_separation_of_concerns(context))

        # PERF-001 FIX: Cap violations at maximum to prevent OOM
        original_count = len(all_violations)
        if len(all_violations) >= self.MAX_VIOLATIONS:
            # Leave room for summary violation
            truncated_count = original_count - (self.MAX_VIOLATIONS - 1)
            all_violations = all_violations[: self.MAX_VIOLATIONS - 1]
            all_violations.append(
                {
                    "rule_id": "PERF-001",
                    "severity": "critical",
                    "description": f"Violation list truncated: {truncated_count} additional violations omitted",
                    "location": "SOLIDValidator.validate",
                    "recommendation": "Fix critical issues first.",
                    "class_name": "System",
                }
            )

        # Calculate score with cap
        score = max(
            0.0,
            1.0
            - (
                min(len(all_violations), self.MAX_PENALTY_VIOLATIONS)
                * self.VIOLATION_PENALTY
            ),
        )

        return ValidationResult(score, all_violations, is_compliant=(score >= 0.7))
