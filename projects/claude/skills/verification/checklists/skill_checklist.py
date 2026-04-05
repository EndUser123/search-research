"""
Skill-specific verification checklist.

This module provides verification checks for skill plans, ensuring
all required sections are present and complete.

Example:
    >>> checklist = SkillChecklist()
    >>> result = checklist.verify_target("skill", "path/to/plan.json")
    >>> if result.status == "pass":
    ...     print("Plan is complete!")
"""

import json
from pathlib import Path
from typing import Any

from claude.skills.verification.checklists import (
    ChecklistResult,
    VerificationChecklist,
)


class SkillChecklist(VerificationChecklist):
    """Verification checklist for skill plans.

    This class verifies that skill plans contain all required sections
    and provides detailed feedback about any missing or empty sections.

    Required sections:
        - problem_statement: Clear statement of the problem to solve
        - context_analysis: Analysis of the context and constraints
        - solution_proposed: Proposed solution approach
        - risks_identified: List of identified risks
        - test_coverage_plan: Plan for test coverage

    Example:
        >>> checklist = SkillChecklist()
        >>> result = checklist.verify_target("skill", "plan.json")
        >>> print(f"Checked {result.items_checked} items, {result.items_passed} passed")
    """

    #: Required sections for a complete skill plan
    REQUIRED_SECTIONS: list[str] = [
        "problem_statement",
        "context_analysis",
        "solution_proposed",
        "risks_identified",
        "test_coverage_plan",
    ]

    #: Checklist item definitions for documentation
    CHECKLIST_ITEMS: list[dict[str, Any]] = [
        {
            "name": "problem_statement",
            "description": "Clear statement of the problem to solve",
            "required": True,
        },
        {
            "name": "context_analysis",
            "description": "Analysis of the context and constraints",
            "required": True,
        },
        {
            "name": "solution_proposed",
            "description": "Proposed solution approach",
            "required": True,
        },
        {
            "name": "risks_identified",
            "description": "List of identified risks",
            "required": True,
        },
        {
            "name": "test_coverage_plan",
            "description": "Plan for test coverage",
            "required": True,
        },
    ]

    def verify_target(self, target_type: str, target_path: str) -> ChecklistResult:
        """Verify a skill plan against the checklist.

        This method loads a skill plan from the given path and verifies that
        all required sections are present and non-empty.

        Args:
            target_type: Type of target being verified (should be "skill")
            target_path: Path to the skill plan file to verify

        Returns:
            ChecklistResult with verification outcomes including:
                - status: "pass" if all sections present, "fail" otherwise
                - items_checked: Total number of required sections (5)
                - items_passed: Number of sections that are present and non-empty
                - findings: List of missing or empty section names

        Raises:
            No exceptions raised - all errors returned in ChecklistResult
        """
        findings: list[str] = []
        items_passed = 0
        items_checked = len(self.REQUIRED_SECTIONS)

        # Check if file exists
        plan_file = Path(target_path)
        if not plan_file.exists():
            return ChecklistResult(
                status="fail",
                items_checked=items_checked,
                items_passed=0,
                findings=[f"File not found: {target_path}"],
            )

        # Try to load and parse the plan file
        try:
            plan_content = json.loads(plan_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            return ChecklistResult(
                status="fail",
                items_checked=items_checked,
                items_passed=0,
                findings=[f"Invalid JSON in file: {e}"],
            )
        except OSError as e:
            return ChecklistResult(
                status="fail",
                items_checked=items_checked,
                items_passed=0,
                findings=[f"Error reading file: {e}"],
            )

        # Check each required section
        for section in self.REQUIRED_SECTIONS:
            if section in plan_content and plan_content[section]:
                items_passed += 1
            else:
                findings.append(f"Missing or empty required section: {section}")

        # Determine overall status
        status = "pass" if items_passed == items_checked else "fail"

        return ChecklistResult(
            status=status,
            items_checked=items_checked,
            items_passed=items_passed,
            findings=findings,
        )

    def get_checklist(self, domain: str) -> dict[str, Any]:
        """Get the checklist for a specific domain.

        This method returns a structured checklist definition for the requested
        domain. For the "skill" domain, this includes all required sections with
        their descriptions and requirements.

        Args:
            domain: Domain to get checklist for (supports: 'skill', 'hook', 'feature')

        Returns:
            Dictionary containing:
                - domain: The domain name
                - items: List of checklist items with name, description, and required flag

        Raises:
            ValueError: If domain is not one of the supported domains

        Example:
            >>> checklist = SkillChecklist()
            >>> skill_checklist = checklist.get_checklist("skill")
            >>> for item in skill_checklist["items"]:
            ...     print(f"{item['name']}: {item['description']}")
        """
        # Validate domain
        valid_domains = ["skill", "hook", "feature"]
        if domain not in valid_domains:
            raise ValueError(
                f"Invalid domain: {domain}. Must be one of {valid_domains}"
            )

        # Return skill-specific checklist
        if domain == "skill":
            return {
                "domain": "skill",
                "items": self.CHECKLIST_ITEMS,
            }

        # Return empty checklist for other domains
        return {"domain": domain, "items": []}
