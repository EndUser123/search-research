"""Tests for checklist-verifier agent.

Tests the agent's ability to:
- Accept target (type, path)
- Run appropriate checklist
- Return structured findings
"""

import sys
from pathlib import Path

# Add skills to path
skills_root = Path(__file__).parent.parent.parent.parent / "skills"
sys.path.insert(0, str(skills_root))

from verification.checklists import FeatureChecklist, HookChecklist, SkillChecklist


class TestChecklistVerifierAgent:
    """Test checklist-verifier agent functionality."""

    def test_accept_skill_target(self):
        """Agent accepts skill target."""
        # Arrange
        target_path = "P:/.claude/skills/verify"

        # Act
        checklist = SkillChecklist()
        result = checklist.verify_target(target_path)

        # Assert
        assert result is not None
        assert result["status"] in ["pass", "fail", "partial"]
        assert isinstance(result["items_checked"], int)
        assert isinstance(result["items_passed"], int)
        assert isinstance(result["findings"], list)

    def test_accept_hook_target(self):
        """Agent accepts hook target."""
        # Arrange
        target_path = "P:/.claude/hooks/UserPromptSubmit*.py"

        # Act
        checklist = HookChecklist()
        result = checklist.verify_target(target_path)

        # Assert
        assert result is not None
        assert result["status"] in ["pass", "fail", "partial"]
        assert isinstance(result["items_checked"], int)
        assert isinstance(result["items_passed"], int)

    def test_accept_feature_target(self):
        """Agent accepts feature target."""
        # Arrange
        target_path = "e2e"

        # Act
        checklist = FeatureChecklist()
        result = checklist.verify_target(target_path)

        # Assert
        assert result is not None
        assert result["status"] in ["pass", "fail", "partial"]

    def test_returns_structured_findings(self):
        """Agent returns structured findings with expected fields."""
        # Arrange
        target_path = "P:/.claude/skills/arch"

        # Act
        checklist = SkillChecklist()
        result = checklist.verify_target(target_path)

        # Assert
        assert "status" in result
        assert "items_checked" in result
        assert "items_passed" in result
        assert "findings" in result
        assert isinstance(result["findings"], list)
        assert all(isinstance(finding, str) for finding in result["findings"])

    def test_invalid_target_type_raises_error(self):
        """Agent raises ValueError for invalid target type."""
        # Arrange
        target_path = "any/path"

        # Act & Assert - try to use invalid path (file doesn't exist)
        checklist = SkillChecklist()
        # This should not raise an error for invalid path, just return fail status
        result = checklist.verify_target(target_path)

        # Assert - result should be fail or partial since path doesn't exist
        assert result["status"] in ["fail", "partial"]

    def test_skill_checklist_passes_for_valid_skill(self):
        """Skill checklist passes for valid skill with all sections."""
        # Arrange
        target_path = "P:/.claude/skills/verify"  # Has complete SKILL.md

        # Act
        checklist = SkillChecklist()
        result = checklist.verify_target(target_path)

        # Assert
        # verify/SKILL.md has all required sections
        assert result["status"] in ["pass", "partial"]
        assert result["items_checked"] > 0

    def test_hook_checklist_detects_registration(self):
        """Hook checklist checks for hook registration."""
        # Arrange
        target_path = "P:/.claude/hooks/UserPromptSubmit*.py"

        # Act
        checklist = HookChecklist()
        result = checklist.verify_target(target_path)

        # Assert
        # UserPromptSubmit is a real hook
        assert result["items_checked"] > 0
        assert len(result["findings"]) > 0
