#!/usr/bin/env python3
# Test for skill template substitution behavior
import sys
from pathlib import Path

sys.path.insert(0, str(Path("P:/.claude/hooks")))

def test_skills_without_user_prompt_unchanged():
    """
    Test that skills WITHOUT {{USER_PROMPT}} template remain unchanged.
    
    Given: A skill file WITHOUT the {{USER_PROMPT}} template variable
    When: run_skill_enforcement() is called with any prompt
    Then: Skill content is injected unchanged (no modification)
    
    Current Behavior: All skills are injected as-is (desired behavior)
    """
    print("Test: Skills without USER_PROMPT remain unchanged")

    # Use a simple skill content without {{USER_PROMPT}} template
    skill_content = "# Test Skill\nThis is a test skill.\nNo template here."

    # Create a mock skill in the real skills directory
    # Note: skill name must match regex r'^/(\w+)' - only word characters allowed
    skills_dir = Path("P:/.claude/skills")
    test_skill_name = "testnotemplate"  # No hyphens, only word chars
    test_skill_dir = skills_dir / test_skill_name
    test_skill_dir.mkdir(exist_ok=True)
    skill_file = test_skill_dir / "SKILL.md"

    # Write our test skill
    skill_file.write_text(skill_content, encoding="utf-8")

    try:
        # Import and call run_skill_enforcement
        import UserPromptSubmit_router as router_module

        test_prompt = "/" + test_skill_name + " some arguments"
        test_data = {"prompt": test_prompt}

        result = router_module.run_skill_enforcement(test_data, test_prompt)

        if result is None:
            print("  FAIL: result is None")
            return False

        injected_context = result.get("context", "")

        # Verify the skill content is in the injection
        if skill_content not in injected_context:
            print("  FAIL: skill content not found in injection")
            print(f"  Looking for: {repr(skill_content)}")
            print(f"  Injection preview: {injected_context[:200]}")
            return False

        # Verify content is unchanged (no template substitution occurred)
        if skill_content in injected_context:
            print("  PASS: skill without USER_PROMPT injected unchanged")
            return True
        else:
            print("  FAIL: Skill content was modified")
            return False
    finally:
        # Cleanup: remove the test skill
        if skill_file.exists():
            skill_file.unlink()
        if test_skill_dir.exists():
            test_skill_dir.rmdir()

if __name__ == "__main__":
    success = test_skills_without_user_prompt_unchanged()
    sys.exit(0 if success else 1)
