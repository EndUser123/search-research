"""
Tests for enhanced commit message body generation.

These tests verify the generate_commit_body function which creates
structured commit message bodies with WHY, WHAT, and VERIFICATION sections.

RED Phase: Tests are written to FAIL initially, then implementation will follow.
"""

import sys
from pathlib import Path

import pytest

# Add hooks directory to path for imports
HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))


class TestCommitBodyGeneration:
    """Test commit message body generation with structured sections."""

    def test_generate_commit_body_returns_string(self):
        """
        Test that generate_commit_body returns a string.

        Given: Valid files_data with file changes
        When: generate_commit_body is called
        Then: Should return a string
        """
        from commit_message_parser import generate_commit_body

        files_data = {
            "files": [
                {"path": "src/feature.py", "additions": 10, "deletions": 2, "new": False}
            ],
            "type": "feat"
        }

        result = generate_commit_body(files_data)

        assert isinstance(result, str)
        assert len(result) > 0

    def test_commit_body_has_why_section(self):
        """
        Test that commit body includes WHY section with markdown header.

        Given: Files data indicating a fix commit
        When: generate_commit_body is called
        Then: Body should contain '## WHY' section explaining the problem
        """
        from commit_message_parser import generate_commit_body

        files_data = {
            "files": [
                {"path": "src/bug_fix.py", "additions": 5, "deletions": 3, "new": False}
            ],
            "type": "fix"
        }

        result = generate_commit_body(files_data)

        assert "## WHY" in result
        # Should contain problem-related content for fix commits
        assert len(result) > 20

    def test_commit_body_has_what_section(self):
        """
        Test that commit body includes WHAT section with bullet items.

        Given: Files data with multiple file changes
        When: generate_commit_body is called
        Then: Body should contain '## WHAT' section with bullet points
        """
        from commit_message_parser import generate_commit_body

        files_data = {
            "files": [
                {"path": "src/feature.py", "additions": 10, "deletions": 2, "new": True},
                {"path": "tests/test_feature.py", "additions": 15, "deletions": 0, "new": True},
                {"path": "docs/api.md", "additions": 5, "deletions": 1, "new": False},
            ],
            "type": "feat"
        }

        result = generate_commit_body(files_data)

        assert "## WHAT" in result
        # Should have bullet points (markdown format)
        assert "-" in result or "*" in result

    def test_commit_body_limits_to_3_bullets(self):
        """
        Test that WHAT section limits to maximum 3 bullet items.

        Given: Files data with more than 3 files changed
        When: generate_commit_body is called
        Then: WHAT section should have at most 3 bullet points
        """
        from commit_message_parser import generate_commit_body

        files_data = {
            "files": [
                {"path": f"src/file_{i}.py", "additions": 5, "deletions": 0, "new": False}
                for i in range(5)
            ],
            "type": "feat"
        }

        result = generate_commit_body(files_data)

        # Count bullet lines in WHAT section
        what_section = result.split("## WHAT")[1].split("##")[0] if "## WHAT" in result else ""
        bullet_count = what_section.count("-") + what_section.count("*")

        assert bullet_count <= 3

    def test_commit_body_has_verification_section(self):
        """
        Test that commit body includes VERIFICATION section with pytest command.

        Given: Files data including test file changes
        When: generate_commit_body is called
        Then: Body should contain '## VERIFICATION' section suggesting pytest
        """
        from commit_message_parser import generate_commit_body

        files_data = {
            "files": [
                {"path": "tests/test_feature.py", "additions": 20, "deletions": 0, "new": True}
            ],
            "type": "test"
        }

        result = generate_commit_body(files_data)

        assert "## VERIFICATION" in result
        # Should suggest pytest command
        assert "pytest" in result.lower()

    def test_commit_body_detects_fix_vs_feat(self):
        """
        Test that WHY section differentiates fix from feat commits.

        Given: Files data with type 'fix' vs 'feat'
        When: generate_commit_body is called for each
        Then: WHY content should reflect problem fix vs new feature
        """
        from commit_message_parser import generate_commit_body

        fix_data = {
            "files": [
                {"path": "src/bug.py", "additions": 3, "deletions": 5, "new": False}
            ],
            "type": "fix"
        }

        feat_data = {
            "files": [
                {"path": "src/new.py", "additions": 20, "deletions": 0, "new": True}
            ],
            "type": "feat"
        }

        fix_result = generate_commit_body(fix_data)
        feat_result = generate_commit_body(feat_data)

        # Both should have WHY section
        assert "## WHY" in fix_result
        assert "## WHY" in feat_result

        # Results should differ based on type
        assert fix_result != feat_result

    def test_commit_body_all_sections_present(self):
        """
        Test that all three sections (WHY, WHAT, VERIFICATION) are present.

        Given: Complete files_data with type and scopes
        When: generate_commit_body is called
        Then: All three markdown sections should be present in order
        """
        from commit_message_parser import generate_commit_body

        files_data = {
            "files": [
                {"path": "src/module.py", "additions": 15, "deletions": 3, "new": True}
            ],
            "scopes": ["core"],
            "type": "feat"
        }

        result = generate_commit_body(files_data)

        # Check all sections are present
        assert "## WHY" in result
        assert "## WHAT" in result
        assert "## VERIFICATION" in result

        # Check sections appear in order
        why_pos = result.find("## WHY")
        what_pos = result.find("## WHAT")
        verify_pos = result.find("## VERIFICATION")

        assert why_pos < what_pos < verify_pos

    def test_commit_body_empty_files(self):
        """
        Test generate_commit_body with empty files list.

        Given: Empty files_data
        When: generate_commit_body is called
        Then: Should still return valid body with sections
        """
        from commit_message_parser import generate_commit_body

        files_data = {
            "files": [],
            "type": "chore"
        }

        result = generate_commit_body(files_data)

        assert isinstance(result, str)
        # Should still have structure even with minimal content
        assert "## WHY" in result or "## WHAT" in result or "## VERIFICATION" in result


class TestCommitBodyEdgeCases:
    """Test edge cases for commit body generation."""

    def test_body_with_deleted_files(self):
        """
        Test commit body when files are deleted.

        Given: Files data with deleted=True
        When: generate_commit_body is called
        Then: Should handle deletion in WHAT section appropriately
        """
        from commit_message_parser import generate_commit_body

        files_data = {
            "files": [
                {"path": "src/legacy.py", "additions": 0, "deletions": 50, "deleted": True}
            ],
            "type": "fix"
        }

        result = generate_commit_body(files_data)

        assert "## WHAT" in result
        # Should reference the deleted file
        assert "legacy" in result.lower() or "delete" in result.lower() or "remove" in result.lower()

    def test_body_with_binary_files(self):
        """
        Test commit body with binary file changes.

        Given: Files data including binary files
        When: generate_commit_body is called
        Then: Should handle binary files without errors
        """
        from commit_message_parser import generate_commit_body

        files_data = {
            "files": [
                {"path": "assets/image.png", "binary": True}
            ],
            "type": "chore"
        }

        result = generate_commit_body(files_data)

        assert isinstance(result, str)
        assert len(result) > 0

    def test_body_no_type_provided(self):
        """
        Test commit body when commit type is not explicitly provided.

        Given: Files data without 'type' key
        When: generate_commit_body is called
        Then: Should infer type or default gracefully
        """
        from commit_message_parser import generate_commit_body

        files_data = {
            "files": [
                {"path": "config.yaml", "additions": 2, "deletions": 1, "new": False}
            ]
        }

        result = generate_commit_body(files_data)

        # Should not crash and should return structured body
        assert isinstance(result, str)
        assert "##" in result  # At least one markdown header


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
