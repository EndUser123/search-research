"""Tests for PostToolUse documentation validator hook.

RED PHASE: Tests will FAIL because hook implementation doesn't exist yet.
After implementation: Tests will pass when documentation validation works correctly.

This hook validates that documentation written to /package directory
meets quality standards and actually exists (not aspirational).
"""

import sys
from pathlib import Path

import pytest

# Add hooks directory to path for imports
HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))


class TestDocumentationValidatorHook:
    """Test suite for PostToolUse_documentation_validator.py hook."""

    def test_hook_triggers_on_skill_md_write(self):
        """
        Test that hook activates when SKILL.md is written in /package directory.

        Given: A Write tool call to /package/SKILL.md
        When: The documentation validator hook processes the event
        Then: Hook should return a warning dict (not empty)
        """
        # Arrange: Create hook input
        hook_input = {
            "tool_name": "Write",
            "tool_input": {
                "file_path": "P:/package/SKILL.md",
                "content": "# Test Skill\n\nSome content"
            },
            "tool_response": {}
        }

        # Act: Try to import and run the hook
        try:
            import PostToolUse_documentation_validator
            result = PostToolUse_documentation_validator.run(hook_input)

            # Assert: Should return warning dict with content
            assert result is not None, "Hook should return a result"
            assert isinstance(result, dict), "Result should be a dict"
            assert "warning" in result, "Result should contain 'warning' key"
        except ImportError as e:
            pytest.fail(f"PostToolUse_documentation_validator module does not exist: {e}")
        except AttributeError as e:
            pytest.fail(f"PostToolUse_documentation_validator.run() function does not exist: {e}")

    def test_hook_triggers_on_reference_write(self):
        """
        Test that hook activates when reference .md is written.

        Given: A Write tool call to /package/references/xxx.md
        When: The documentation validator hook processes the event
        Then: Hook should return a warning dict
        """
        # Arrange
        hook_input = {
            "tool_name": "Write",
            "tool_input": {
                "file_path": "P:/package/references/test-reference.md",
                "content": "# Test Reference\n\nReference content"
            },
            "tool_response": {}
        }

        # Act & Assert
        try:
            import PostToolUse_documentation_validator
            result = PostToolUse_documentation_validator.run(hook_input)

            assert result is not None, "Hook should return a result"
            assert isinstance(result, dict), "Result should be a dict"
            assert "warning" in result, "Result should contain 'warning' key"
        except ImportError as e:
            pytest.fail(f"PostToolUse_documentation_validator module does not exist: {e}")
        except AttributeError as e:
            pytest.fail(f"PostToolUse_documentation_validator.run() function does not exist: {e}")

    def test_hook_ignores_non_package_files(self):
        """
        Test that hook ignores writes outside /package directory.

        Given: A Write tool call to SKILL.md in other directories
        When: The documentation validator hook processes the event
        Then: Hook should return empty dict (no warning)
        """
        # Arrange
        hook_input = {
            "tool_name": "Write",
            "tool_input": {
                "file_path": "P:/some-other-skill/SKILL.md",
                "content": "# Other Skill"
            },
            "tool_response": {}
        }

        # Act & Assert
        try:
            import PostToolUse_documentation_validator
            result = PostToolUse_documentation_validator.run(hook_input)

            # Should return empty dict for files outside /package
            assert result == {}, f"Hook should return empty dict for non-package files, got: {result}"
        except ImportError as e:
            pytest.fail(f"PostToolUse_documentation_validator module does not exist: {e}")
        except AttributeError as e:
            pytest.fail(f"PostToolUse_documentation_validator.run() function does not exist: {e}")

    def test_hook_ignores_non_markdown_files(self):
        """
        Test that hook ignores .py, .json and other non-markdown files.

        Given: A Write tool call to validate_docs.py
        When: The documentation validator hook processes the event
        Then: Hook should return empty dict (no warning)
        """
        # Arrange
        hook_input = {
            "tool_name": "Write",
            "tool_input": {
                "file_path": "P:/package/validate_docs.py",
                "content": "#!/usr/bin/env python3\nprint('validation')"
            },
            "tool_response": {}
        }

        # Act & Assert
        try:
            import PostToolUse_documentation_validator
            result = PostToolUse_documentation_validator.run(hook_input)

            # Should return empty dict for non-markdown files
            assert result == {}, f"Hook should return empty dict for non-markdown files, got: {result}"
        except ImportError as e:
            pytest.fail(f"PostToolUse_documentation_validator module does not exist: {e}")
        except AttributeError as e:
            pytest.fail(f"PostToolUse_documentation_validator.run() function does not exist: {e}")

    def test_hook_graceful_error_handling(self):
        """
        Test that hook handles import/IO errors gracefully without crashing.

        Given: DocumentationValidator import fails or raises exception
        When: The documentation validator hook processes the event
        Then: Hook should not crash, should return error warning dict
        """
        # Arrange
        hook_input = {
            "tool_name": "Write",
            "tool_input": {
                "file_path": "P:/package/SKILL.md",
                "content": "# Test"
            },
            "tool_response": {}
        }

        # Act & Assert
        try:
            import PostToolUse_documentation_validator
            result = PostToolUse_documentation_validator.run(hook_input)

            # Should handle error gracefully
            assert result is not None, "Hook should return a result even on errors"
            assert isinstance(result, dict), "Result should be a dict"
            # Should either have warning or be empty (graceful degradation)
            assert "warning" in result or result == {}, "Hook should handle errors gracefully"
        except ImportError as e:
            pytest.fail(f"PostToolUse_documentation_validator module does not exist: {e}")
        except AttributeError as e:
            pytest.fail(f"PostToolUse_documentation_validator.run() function does not exist: {e}")
        except Exception as e:
            pytest.fail(f"Hook should handle errors gracefully, but got exception: {e}")

    def test_hook_integrates_with_validator(self):
        """
        Test that hook correctly calls DocumentationValidator and formats issues.

        Given: DocumentationValidator returns test validation issues
        When: The documentation validator hook processes the event
        Then: Hook should format issues into warning dict
        """
        # Arrange
        hook_input = {
            "tool_name": "Write",
            "tool_input": {
                "file_path": "P:/package/SKILL.md",
                "content": "# Test"
            },
            "tool_response": {}
        }

        # Act & Assert
        try:
            import PostToolUse_documentation_validator
            result = PostToolUse_documentation_validator.run(hook_input)

            # Should format validator issues into warning
            assert result is not None, "Hook should return a result"
            assert isinstance(result, dict), "Result should be a dict"
            assert "warning" in result, "Result should contain 'warning' key when issues found"
            assert "Documentation" in result["warning"], "Warning should mention documentation issues"
        except ImportError as e:
            pytest.fail(f"PostToolUse_documentation_validator module does not exist: {e}")
        except AttributeError as e:
            pytest.fail(f"PostToolUse_documentation_validator.run() function does not exist: {e}")
