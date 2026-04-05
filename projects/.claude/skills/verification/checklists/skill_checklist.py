"""
Skill-specific verification checklist.

This module provides verification checks for skill plans, ensuring
all required sections are present and complete.
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

    Checks skill plans for completeness of required sections:
    - problem_statement
    - context_analysis
    - solution_proposed
    - risks_identified
    - test_coverage_plan
    """

    #: Required sections for a complete skill plan
    REQUIRED_SECTIONS = [
        "problem_statement",
        "context_analysis",
        "solution_proposed",
        "risks_identified",
        "test_coverage_plan",
    ]

    def verify_target(self, target_type: str, target_path: str) -> ChecklistResult:
        """Verify a skill plan against the checklist.

        Args:
            target_type: Type of target being verified (should be "skill")
            target_path: Path to the skill plan file to verify

        Returns:
            ChecklistResult with verification outcomes
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
        except Exception as e:
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

        Args:
            domain: Domain to get checklist for (supports: 'skill', 'hook', 'feature')

        Returns:
            Dictionary containing the checklist for the domain

        Raises:
            ValueError: If domain is not one of the supported domains
        """
        # Validate domain
        if domain not in self.VALID_DOMAINS:
            raise ValueError(
                f"Invalid domain: {domain}. Must be one of {self.VALID_DOMAINS}"
            )

        # Return skill-specific checklist
        if domain == "skill":
            return {
                "domain": "skill",
                "items": [
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
                ],
            }

        # Return empty checklist for other domains
        return {"domain": domain, "items": []}
