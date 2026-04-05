"""
Tests for shared checklist library structure.

These tests verify the VerificationChecklist base class and related components
provide the required interface for domain-specific verification checklists.

Run with: pytest .claude/skills/verification/tests/test_checklists.py -v
"""

import pytest
from dataclasses import dataclass
from typing import Dict, Any, List
from abc import ABC, abstractmethod
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))


class TestVerificationChecklistBaseClass:
    """Tests for VerificationChecklist base class structure."""

    def test_verification_checklist_class_exists(self):
        """
        Test that VerificationChecklist base class exists.

        Given: The checklist library module
        When: Importing VerificationChecklist
        Then: The class should be importable
        """
        from claude.skills.verification.checklists import VerificationChecklist

        assert VerificationChecklist is not None
        assert isinstance(VerificationChecklist, type)

    def test_verify_target_is_abstract_method(self):
        """
        Test that verify_target() is an abstract method that must be overridden.

        Given: A VerificationChecklist base class
        When: Trying to instantiate it directly
        Then: Should raise TypeError due to abstract method
        """
        from claude.skills.verification.checklists import VerificationChecklist

        # Attempting to instantiate abstract base class should fail
        with pytest.raises(TypeError):
            VerificationChecklist()

    def test_verify_target_signature(self):
        """
        Test that verify_target() has the correct signature.

        Given: A concrete VerificationChecklist subclass
        When: Implementing verify_target method
        Then: Should accept type and path parameters
        """
        from claude.skills.verification.checklists import (
            VerificationChecklist,
            ChecklistResult,
        )

        class ConcreteChecklist(VerificationChecklist):
            def verify_target(self, target_type: str, target_path: str) -> ChecklistResult:
                return ChecklistResult(
                    status="pass",
                    items_checked=0,
                    items_passed=0,
                    findings=[],
                )

            def get_checklist(self, domain: str) -> Dict[str, Any]:
                return {}

        # Should be able to instantiate concrete class
        checklist = ConcreteChecklist()
        assert callable(checklist.verify_target)

        # Method should accept type and path parameters
        import inspect

        sig = inspect.signature(checklist.verify_target)
        params = list(sig.parameters.keys())
        assert "target_type" in params
        assert "target_path" in params

    def test_get_checklist_method_exists(self):
        """
        Test that get_checklist() method exists and returns a dictionary.

        Given: A VerificationChecklist instance
        When: Calling get_checklist() with a domain
        Then: Should return a checklist dictionary
        """
        from claude.skills.verification.checklists import (
            VerificationChecklist,
            ChecklistResult,
        )

        class ConcreteChecklist(VerificationChecklist):
            def verify_target(self, target_type: str, target_path: str) -> ChecklistResult:
                return ChecklistResult(
                    status="pass",
                    items_checked=0,
                    items_passed=0,
                    findings=[],
                )

            def get_checklist(self, domain: str) -> Dict[str, Any]:
                return {"domain": domain, "items": []}

        checklist = ConcreteChecklist()
        result = checklist.get_checklist("skill")

        assert isinstance(result, dict)
        assert "domain" in result

    def test_invalid_domain_raises_value_error(self):
        """
        Test that invalid domain raises ValueError.

        Given: A VerificationChecklist instance
        When: Calling get_checklist() with an invalid domain
        Then: Should raise ValueError
        """
        from claude.skills.verification.checklists import (
            VerificationChecklist,
            ChecklistResult,
        )

        class ConcreteChecklist(VerificationChecklist):
            VALID_DOMAINS = ["skill", "hook", "feature"]

            def verify_target(self, target_type: str, target_path: str) -> ChecklistResult:
                return ChecklistResult(
                    status="pass",
                    items_checked=0,
                    items_passed=0,
                    findings=[],
                )

            def get_checklist(self, domain: str) -> Dict[str, Any]:
                if domain not in self.VALID_DOMAINS:
                    raise ValueError(f"Invalid domain: {domain}. Must be one of {self.VALID_DOMAINS}")
                return {"domain": domain, "items": []}

        checklist = ConcreteChecklist()

        with pytest.raises(ValueError, match="Invalid domain"):
            checklist.get_checklist("invalid_domain")


class TestChecklistResultDataclass:
    """Tests for ChecklistResult dataclass structure."""

    def test_checklist_result_exists(self):
        """
        Test that ChecklistResult dataclass exists.

        Given: The checklist library module
        When: Importing ChecklistResult
        Then: The dataclass should be importable
        """
        from claude.skills.verification.checklists import ChecklistResult

        assert ChecklistResult is not None
        assert isinstance(ChecklistResult, type)

    def test_checklist_result_has_status_field(self):
        """
        Test that ChecklistResult has status field.

        Given: A ChecklistResult dataclass
        When: Creating an instance
        Then: Should have a status field
        """
        from claude.skills.verification.checklists import ChecklistResult

        result = ChecklistResult(
            status="pass",
            items_checked=5,
            items_passed=5,
            findings=[],
        )

        assert hasattr(result, "status")
        assert result.status == "pass"

    def test_checklist_result_has_items_checked_field(self):
        """
        Test that ChecklistResult has items_checked field.

        Given: A ChecklistResult dataclass
        When: Creating an instance
        Then: Should have an items_checked field
        """
        from claude.skills.verification.checklists import ChecklistResult

        result = ChecklistResult(
            status="pass",
            items_checked=10,
            items_passed=8,
            findings=[],
        )

        assert hasattr(result, "items_checked")
        assert result.items_checked == 10

    def test_checklist_result_has_items_passed_field(self):
        """
        Test that ChecklistResult has items_passed field.

        Given: A ChecklistResult dataclass
        When: Creating an instance
        Then: Should have an items_passed field
        """
        from claude.skills.verification.checklists import ChecklistResult

        result = ChecklistResult(
            status="pass",
            items_checked=10,
            items_passed=8,
            findings=[],
        )

        assert hasattr(result, "items_passed")
        assert result.items_passed == 8

    def test_checklist_result_has_findings_field(self):
        """
        Test that ChecklistResult has findings field.

        Given: A ChecklistResult dataclass
        When: Creating an instance
        Then: Should have a findings field (list of issues/discoveries)
        """
        from claude.skills.verification.checklists import ChecklistResult

        result = ChecklistResult(
            status="fail",
            items_checked=5,
            items_passed=3,
            findings=["Missing documentation", "Invalid type hint"],
        )

        assert hasattr(result, "findings")
        assert isinstance(result.findings, list)
        assert len(result.findings) == 2

    def test_checklist_result_all_required_fields(self):
        """
        Test that ChecklistResult has all required fields.

        Given: A ChecklistResult dataclass
        When: Creating an instance with all fields
        Then: All fields should be accessible
        """
        from claude.skills.verification.checklists import ChecklistResult

        result = ChecklistResult(
            status="partial",
            items_checked=15,
            items_passed=12,
            findings=["Warning: Incomplete coverage"],
        )

        assert result.status == "partial"
        assert result.items_checked == 15
        assert result.items_passed == 12
        assert isinstance(result.findings, list)
        assert len(result.findings) == 1
