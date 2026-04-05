#!/usr/bin/env python3
"""Test for skill template substitution - multiple {{USER_PROMPT}} occurrences.

This test verifies that when a skill file contains multiple {{USER_PROMPT}}
placeholders, ALL occurrences are replaced with the actual user prompt.

Current behavior: No substitution happens, all occurrences remain as literal {{USER_PROMPT}}
Expected behavior: All occurrences should be replaced with the actual prompt

Run with: pytest tests/test_skill_template_substitution.py -v
"""

import sys
from pathlib import Path

# Add hooks directory to path
HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))


def test_multiple_user_prompt_occurrences_replaced():
    """
    Test that multiple {{USER_PROMPT}} occurrences are all replaced.

    Given: A skill file with {{USER_PROMPT}} appearing 3 times
    When: run_skill_enforcement() is called with a test prompt
    Then: All 3 occurrences should be replaced with the actual prompt

    Current Behavior: No substitution happens, so all occurrences remain as literal {{USER_PROMPT}}
    Expected Behavior: All occurrences of {{USER_PROMPT}} should be replaced
    """
    # Arrange
    test_prompt = "Write a failing test for multiple placeholder replacement"
    skill_name = "test_skill_multiple"

    # Create a mock skill file with {{USER_PROMPT}} appearing 3 times
    skill_content = """# Test Skill

## Instructions
You are a helpful assistant. The user requested: {{USER_PROMPT}}

## Analysis
Please analyze the following request: {{USER_PROMPT}}

## Summary
Based on the request "{{USER_PROMPT}}", provide a comprehensive response.
"""

    # Create the skill in the actual skills directory
    skills_dir = Path("P:/.claude/skills")
    test_skill_dir = skills_dir / skill_name
    test_skill_dir.mkdir(parents=True, exist_ok=True)
    skill_file = test_skill_dir / "SKILL.md"
    skill_file.write_text(skill_content, encoding="utf-8")

    try:
        # Import router
        import UserPromptSubmit_router as router

        # Create test data
        user_input = f"/{skill_name} {test_prompt}"
        data = {
            "prompt": user_input,
            "message": user_input
        }

        # Act - Call run_skill_enforcement
        result = router.run_skill_enforcement(data, user_input)

        # Assert
        assert result is not None, "run_skill_enforcement should return a result"
        assert "context" in result, "Result should contain context key"

        injected_context = result["context"]

        # Verify all {{USER_PROMPT}} occurrences were replaced
        placeholder_count = injected_context.count("{{USER_PROMPT}}")

        # This assertion will FAIL because current behavior does not replace placeholders
        assert placeholder_count == 0, (
            f"Expected 0 occurrences of {{USER_PROMPT}} after substitution, "
            f"but found {placeholder_count}. "
            f"All placeholders should be replaced with the actual prompt: '{test_prompt}'"
        )

        # Verify the actual prompt appears in the injected content
        # It should appear 3 times (once for each placeholder)
        prompt_count = injected_context.count(test_prompt)
        assert prompt_count == 3, (
            f"Expected the test prompt to appear 3 times in the injected content, "
            f"but found {prompt_count} occurrences. "
            f"Prompt: '{test_prompt}'"
        )

    finally:
        # Cleanup: Remove the test skill file
        if skill_file.exists():
            skill_file.unlink()
        if test_skill_dir.exists():
            test_skill_dir.rmdir()


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
