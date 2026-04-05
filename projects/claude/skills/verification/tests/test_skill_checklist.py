"""
Tests for SkillChecklist verification.

These tests verify skill-specific checklist behavior including plan completeness checks.
Run with: pytest .claude/skills/verification/tests/test_skill_checklist.py -v
"""

import sys
from pathlib import Path
from typing import Any

import pytest

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))


class TestSkillChecklistClassExists:
    """Tests for SkillChecklist class existence and structure."""

    def test_skill_checklist_class_exists(self):
        """
        Test that SkillChecklist class exists and can be imported.

        Given: The skill checklist module
        When: Importing SkillChecklist
        Then: The class should be importable
        """
        from claude.skills.verification.checklists.skill_checklist import SkillChecklist

        assert SkillChecklist is not None
        assert isinstance(SkillChecklist, type)

    def test_skill_checklist_extends_base(self):
        """
        Test that SkillChecklist extends VerificationChecklist.

        Given: SkillChecklist class
        When: Checking class hierarchy
        Then: Should be a subclass of VerificationChecklist
        """
        from claude.skills.verification.checklists.skill_checklist import SkillChecklist

        from claude.skills.verification.checklists import VerificationChecklist

        assert issubclass(SkillChecklist, VerificationChecklist)

    def test_skill_checklist_has_verify_target_method(self):
        """
        Test that SkillChecklist implements verify_target() method.

        Given: A SkillChecklist instance
        When: Checking available methods
        Then: Should have verify_target method
        """
        from claude.skills.verification.checklists.skill_checklist import SkillChecklist

        checklist = SkillChecklist()
        assert hasattr(checklist, "verify_target")
        assert callable(checklist.verify_target)


class TestSkillChecklistPlanCompleteness:
    """Tests for skill plan completeness verification."""

    @pytest.fixture
    def complete_plan(self) -> dict[str, Any]:
        """Fixture providing a complete skill plan."""
        return {
            "problem_statement": "Test problem statement",
            "context_analysis": "Test context analysis",
            "solution_proposed": "Test solution",
            "risks_identified": ["Risk 1", "Risk 2"],
            "test_coverage_plan": "Test coverage plan",
        }

    @pytest.fixture
    def incomplete_plan(self) -> dict[str, Any]:
        """Fixture providing an incomplete skill plan."""
        return {
            "problem_statement": "Test problem statement",
            # Missing: context_analysis
            # Missing: solution_proposed
            # Missing: risks_identified
            # Missing: test_coverage_plan
        }

    def test_verify_complete_plan_passes(self, complete_plan):
        """
        Test that a complete plan passes verification.

        Given: A complete skill plan with all required sections
        When: Verifying the plan
        Then: Should return pass status with all items checked
        """
        import json
        import tempfile

        from claude.skills.verification.checklists.skill_checklist import SkillChecklist

        from claude.skills.verification.checklists import ChecklistResult

        # Create a temporary file with the complete plan
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(complete_plan, f)
            plan_path = f.name

        try:
            checklist = SkillChecklist()
            result = checklist.verify_target("skill", plan_path)

            assert isinstance(result, ChecklistResult)
            assert result.status == "pass"
            assert result.items_checked == 5
            assert result.items_passed == 5
            assert len(result.findings) == 0
        finally:
            Path(plan_path).unlink()

    def test_verify_incomplete_plan_fails(self, incomplete_plan):
        """
        Test that an incomplete plan fails verification.

        Given: An incomplete skill plan missing required sections
        When: Verifying the plan
        Then: Should return fail status with findings about missing sections
        """
        import json
        import tempfile

        from claude.skills.verification.checklists.skill_checklist import SkillChecklist

        from claude.skills.verification.checklists import ChecklistResult

        # Create a temporary file with the incomplete plan
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(incomplete_plan, f)
            plan_path = f.name

        try:
            checklist = SkillChecklist()
            result = checklist.verify_target("skill", plan_path)

            assert isinstance(result, ChecklistResult)
            assert result.status == "fail"
            assert result.items_checked == 5
            assert result.items_passed < 5
            assert len(result.findings) > 0
            # Check that missing sections are reported
            findings_text = " ".join(result.findings)
            assert "context_analysis" in findings_text or "context analysis" in findings_text.lower()
        finally:
            Path(plan_path).unlink()

    def test_verify_checks_problem_statement(self, complete_plan):
        """
        Test that verify_target checks for problem_statement.

        Given: A skill plan
        When: The plan is missing problem_statement
        Then: Should be reported in findings
        """
        import json
        import tempfile

        from claude.skills.verification.checklists.skill_checklist import SkillChecklist

        incomplete = complete_plan.copy()
        del incomplete["problem_statement"]

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(incomplete, f)
            plan_path = f.name

        try:
            checklist = SkillChecklist()
            result = checklist.verify_target("skill", plan_path)

            assert result.items_passed < result.items_checked
            findings_text = " ".join(result.findings).lower()
            assert any(
                term in findings_text
                for term in ["problem", "statement", "problem_statement"]
            )
        finally:
            Path(plan_path).unlink()

    def test_verify_checks_context_analysis(self, complete_plan):
        """
        Test that verify_target checks for context_analysis.

        Given: A skill plan
        When: The plan is missing context_analysis
        Then: Should be reported in findings
        """
        import json
        import tempfile

        from claude.skills.verification.checklists.skill_checklist import SkillChecklist

        incomplete = complete_plan.copy()
        del incomplete["context_analysis"]

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(incomplete, f)
            plan_path = f.name

        try:
            checklist = SkillChecklist()
            result = checklist.verify_target("skill", plan_path)

            assert result.items_passed < result.items_checked
            findings_text = " ".join(result.findings).lower()
            assert any(
                term in findings_text
                for term in ["context", "analysis", "context_analysis"]
            )
        finally:
            Path(plan_path).unlink()

    def test_verify_checks_solution_proposed(self, complete_plan):
        """
        Test that verify_target checks for solution_proposed.

        Given: A skill plan
        When: The plan is missing solution_proposed
        Then: Should be reported in findings
        """
        import json
        import tempfile

        from claude.skills.verification.checklists.skill_checklist import SkillChecklist

        incomplete = complete_plan.copy()
        del incomplete["solution_proposed"]

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(incomplete, f)
            plan_path = f.name

        try:
            checklist = SkillChecklist()
            result = checklist.verify_target("skill", plan_path)

            assert result.items_passed < result.items_checked
            findings_text = " ".join(result.findings).lower()
            assert any(
                term in findings_text
                for term in ["solution", "proposed", "solution_proposed"]
            )
        finally:
            Path(plan_path).unlink()

    def test_verify_checks_risks_identified(self, complete_plan):
        """
        Test that verify_target checks for risks_identified.

        Given: A skill plan
        When: The plan is missing risks_identified
        Then: Should be reported in findings
        """
        import json
        import tempfile

        from claude.skills.verification.checklists.skill_checklist import SkillChecklist

        incomplete = complete_plan.copy()
        del incomplete["risks_identified"]

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(incomplete, f)
            plan_path = f.name

        try:
            checklist = SkillChecklist()
            result = checklist.verify_target("skill", plan_path)

            assert result.items_passed < result.items_checked
            findings_text = " ".join(result.findings).lower()
            assert any(
                term in findings_text
                for term in ["risks", "identified", "risks_identified"]
            )
        finally:
            Path(plan_path).unlink()

    def test_verify_checks_test_coverage_plan(self, complete_plan):
        """
        Test that verify_target checks for test_coverage_plan.

        Given: A skill plan
        When: The plan is missing test_coverage_plan
        Then: Should be reported in findings
        """
        import json
        import tempfile

        from claude.skills.verification.checklists.skill_checklist import SkillChecklist

        incomplete = complete_plan.copy()
        del incomplete["test_coverage_plan"]

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(incomplete, f)
            plan_path = f.name

        try:
            checklist = SkillChecklist()
            result = checklist.verify_target("skill", plan_path)

            assert result.items_passed < result.items_checked
            findings_text = " ".join(result.findings).lower()
            assert any(
                term in findings_text
                for term in ["test", "coverage", "plan", "test_coverage_plan"]
            )
        finally:
            Path(plan_path).unlink()

    def test_verify_handles_invalid_json(self):
        """
        Test that verify_target handles invalid JSON gracefully.

        Given: A file path pointing to invalid JSON
        When: Verifying the file
        Then: Should return fail status with error findings
        """
        import tempfile

        from claude.skills.verification.checklists.skill_checklist import SkillChecklist

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            f.write("{ invalid json }")
            plan_path = f.name

        try:
            checklist = SkillChecklist()
            result = checklist.verify_target("skill", plan_path)

            assert result.status == "fail"
            assert len(result.findings) > 0
        finally:
            Path(plan_path).unlink()

    def test_verify_handles_missing_file(self):
        """
        Test that verify_target handles missing files gracefully.

        Given: A file path that doesn't exist
        When: Verifying the file
        Then: Should return fail status with error findings
        """
        from claude.skills.verification.checklists.skill_checklist import SkillChecklist

        checklist = SkillChecklist()
        result = checklist.verify_target("skill", "/nonexistent/path/to/plan.json")

        assert result.status == "fail"
        assert len(result.findings) > 0


class TestSkillChecklistGetChecklist:
    """Tests for get_checklist method."""

    def test_get_checklist_for_skill_domain(self):
        """
        Test that get_checklist returns skill-specific checklist.

        Given: A SkillChecklist instance
        When: Calling get_checklist with "skill" domain
        Then: Should return skill checklist items
        """
        from claude.skills.verification.checklists.skill_checklist import SkillChecklist

        checklist = SkillChecklist()
        result = checklist.get_checklist("skill")

        assert isinstance(result, dict)
        assert "domain" in result
        assert result["domain"] == "skill"
        assert "items" in result
