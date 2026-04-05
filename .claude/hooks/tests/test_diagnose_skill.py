#!/usr/bin/env python3
"""Integration tests for /diagnose skill."""

import json
import subprocess
from pathlib import Path

import pytest


def invoke_diagnose(prompt: str) -> dict:
    """Helper to invoke /diagnose skill."""
    skill_path = Path("P:/.claude/skills/diagnose/SKILL.md")

    # In a real test, we'd use the Skill tool, but for integration testing
    # we'll simulate by reading the skill and checking its structure
    result = subprocess.run(
        ["python", "-c", f"""
import sys
sys.path.insert(0, 'P:/.claude/skills/diagnose')

# Simulate skill invocation by reading SKILL.md
with open('{skill_path}') as f:
    skill_content = f.read()

# Check skill has required sections
required_sections = [
    'Purpose',
    'Template Structure',
    'Protocol Checklist',
    'Prohibited Behaviors'
]

missing = []
for section in required_sections:
    if section not in skill_content:
        missing.append(section)

print(json.dumps({{
    'has_required_sections': len(missing) == 0,
    'missing_sections': missing,
    'skill_content_length': len(skill_content)
}}))
        """],
        capture_output=True,
        text=True,
        cwd="P:/"
    )

    try:
        return json.loads(result["stdout"].strip())
    except json.JSONDecodeError:
        return {
            "error": "Failed to parse skill output",
            "stdout": result["stdout"],
            "stderr": result["stderr"]
        }


class TestDiagnoseSkillStructure:
    """Test /diagnose skill has correct structure."""

    def test_skill_exists(self):
        """Skill file should exist."""
        skill_path = Path("P:/.claude/skills/diagnose/SKILL.md")
        assert skill_path.exists()

    def test_skill_manifest_exists(self):
        """Skill manifest should exist."""
        manifest_path = Path("P:/.claude/skills/diagnose/skill.json")
        assert manifest_path.exists()

    def test_skill_has_required_sections(self):
        """Skill should have all required sections."""
        result = invoke_diagnose("test")
        assert result["has_required_sections"], \
            f"Missing sections: {result.get('missing_sections', [])}"

    def test_skill_content_substantial(self):
        """Skill should have substantial content."""
        result = invoke_diagnose("test")
        assert result["skill_content_length"] > 1000, \
            "Skill content too short, needs more detail"


class TestDiagnoseSkillTemplate:
    """Test diagnostic template structure."""

    def test_template_has_hypotheses_section(self):
        """Template should require hypotheses section."""
        skill_path = Path("P:/.claude/skills/diagnose/SKILL.md")
        content = skill_path.read_text()

        assert "**Hypotheses**:" in content
        assert "H1:" in content
        assert "H2:" in content
        assert "H3:" in content

    def test_template_has_test_results_section(self):
        """Template should require test results section."""
        skill_path = Path("P:/.claude/skills/diagnose/SKILL.md")
        content = skill_path.read_text()

        assert "**Test Results**:" in content
        assert "RULED OUT" in content
        assert "CONFIRMED" in content

    def test_template_has_conclusion_section(self):
        """Template should require conclusion section."""
        skill_path = Path("P:/.claude/skills/diagnose/SKILL.md")
        content = skill_path.read_text()

        assert "**Conclusion**:" in content
        assert "H[confirmed]" in content

    def test_template_has_next_step_section(self):
        """Template should require next step section."""
        skill_path = Path("P:/.claude/skills/diagnose/SKILL.md")
        content = skill_path.read_text()

        assert "**Next Step**:" in content


class TestDiagnoseSkillRequirements:
    """Test skill requirements enforcement."""

    def test_requires_3_hypotheses(self):
        """Skill should require minimum 3 hypotheses."""
        skill_path = Path("P:/.claude/skills/diagnose/SKILL.md")
        content = skill_path.read_text()

        assert "minimum 3" in content.lower()
        assert "3+ hypotheses" in content

    def test_requires_systematic_testing(self):
        """Skill should require systematic testing."""
        skill_path = Path("P:/.claude/skills/diagnose/SKILL.md")
        content = skill_path.read_text()

        assert "systematic" in content.lower()
        assert "FOR EACH hypothesis" in content

    def test_requires_documentation(self):
        """Skill should require diagnostic path documentation."""
        skill_path = Path("P:/.claude/skills/diagnose/SKILL.md")
        content = skill_path.read_text()

        assert "Document the diagnostic path" in content

    def test_requires_conclusion_before_next_step(self):
        """Skill should require conclusion before next step."""
        skill_path = Path("P:/.claude/skills/diagnose/SKILL.md")
        content = skill_path.read_text()

        # Should emphasize concluding before proceeding
        assert "only proceed" in content.lower()
        assert "all but one ruled out" in content.lower()


class TestDiagnoseSkillIntegration:
    """Test /diagnose skill integration with enforcement system."""

    def test_diagnose_enforces_verification_first(self):
        """Skill should enforce Verification First protocol."""
        skill_path = Path("P:/.claude/skills/diagnose/SKILL.md")
        content = skill_path.read_text()

        assert "Verification First Protocol" in content
        assert "Claim → Test → Document" in content

    def test_diagnose_enforces_solution_proposal_gate(self):
        """Skill should enforce Solution Proposal Gate."""
        skill_path = Path("P:/.claude/skills/diagnose/SKILL.md")
        content = skill_path.read_text()

        assert "Solution Proposal Gate" in content

    def test_diagnose_references_memory_protocols(self):
        """Skill should reference MEMORY.md protocols."""
        skill_path = Path("P:/.claude/skills/diagnose/SKILL.md")
        content = skill_path.read_text()

        assert "MEMORY.md" in content


class TestDiagnoseSkillExamples:
    """Test diagnostic examples in skill."""

    def test_pytest_hanging_example(self):
        """Skill should include pytest hanging example."""
        skill_path = Path("P:/.claude/skills/diagnose/SKILL.md")
        content = skill_path.read_text()

        assert "pytest" in content.lower()
        assert "testmon" in content.lower()

    def test_has_multiple_examples(self):
        """Skill should have multiple examples."""
        skill_path = Path("P:/.claude/skills/diagnose/SKILL.md")
        content = skill_path.read_text()

        # Count example sections
        example_count = content.count("### Example")
        assert example_count >= 2, "Should have at least 2 examples"

    def test_examples_follow_template(self):
        """Examples should follow the required template."""
        skill_path = Path("P:/.claude/skills/diagnose/SKILL.md")
        content = skill_path.read_text()

        # Check that examples have required sections
        assert "**Issue**:" in content
        assert "**Hypotheses**:" in content
        assert "**Test Results**:" in content
        assert "**Conclusion**:" in content


@pytest.mark.parametrize("section,required_content", [
    ("Purpose", "investigation"),
    ("Template", "hypotheses"),
    ("Protocol", "3"),
    ("Prohibited", "jump to solution"),
])
def test_diagnose_skill_section_requirements(section, required_content):
    """Parametrized test for skill section requirements."""
    skill_path = Path("P:/.claude/skills/diagnose/SKILL.md")
    content = skill_path.read_text()

    # Find the section
    section_start = content.find(f"## {section}")
    assert section_start != -1, f"Section '{section}' not found"

    # Check section has required content
    section_content = content[section_start:section_start+2000]  # Next 2000 chars
    assert required_content.lower() in section_content.lower(), \
        f"Section '{section}' missing required content: {required_content}"
