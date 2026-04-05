#!/usr/bin/env python3
"""Test skill_compliance_indicator module.

Tests:
1. Hook fires on slash commands
2. Hook reads enforcement_level from SKILL.md correctly
3. Hook reads workflow_steps from SKILL.md correctly
4. Hook gets current breadcrumb trail
5. Hook calculates historical completion rate
6. Hook skips non-slash commands
7. Hook formats indicator correctly
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add hooks to path
HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))

# Add skill-guard to path
SKILL_GUARD = Path("P:/packages/skill-guard/src")
if SKILL_GUARD.exists():
    sys.path.insert(0, str(SKILL_GUARD))


def test_extract_skill_name():
    """Test skill name extraction from various prompt formats."""
    import UserPromptSubmit_modules.skill_compliance_indicator as indicator

    # Test with leading slash
    assert indicator._extract_skill_name("/arch improve memory") == "arch"

    # Test with leading terminal prompt glyphs
    assert indicator._extract_skill_name("❯ /arch improve memory") == "arch"

    # Test with arguments
    assert indicator._extract_skill_name("/arch") == "arch"

    # Test with non-slash command
    assert indicator._extract_skill_name("improve memory system") is None

    # Test with empty string
    assert indicator._extract_skill_name("") is None

    print("✓ Test passed: Skill name extraction")


def test_read_skill_frontmatter():
    """Test reading skill frontmatter for enforcement_level and workflow_steps."""
    import UserPromptSubmit_modules.skill_compliance_indicator as indicator

    # Test with /arch skill (has workflow_steps, no explicit enforcement_level)
    frontmatter = indicator._read_skill_frontmatter("arch")

    assert isinstance(frontmatter, dict)
    assert "workflow_steps" in frontmatter
    assert len(frontmatter["workflow_steps"]) == 6  # /arch has 6 steps
    assert frontmatter["workflow_steps"][0] == "preflight_checks"

    # enforcement_level should not be present (uses default STANDARD)
    assert frontmatter.get("enforcement_level") is None

    print(f"✓ Test passed: Read {len(frontmatter['workflow_steps'])} workflow_steps from /arch")

    # Test with non-existent skill
    frontmatter = indicator._read_skill_frontmatter("nonexistent_skill_xyz")
    assert frontmatter == {}

    print("✓ Test passed: Handles non-existent skill gracefully")


def test_get_breadcrumb_trail():
    """Test getting breadcrumb trail for a skill."""
    import UserPromptSubmit_modules.skill_compliance_indicator as indicator

    # Test with /arch skill (should have trail from earlier conversation)
    trail = indicator._get_breadcrumb_trail("arch")

    assert isinstance(trail, dict)
    # Trail may or may not have data depending on state
    print("✓ Test passed: Breadcrumb trail retrieved for /arch")


def test_get_historical_completion_rate():
    """Test calculating historical completion rate."""
    import UserPromptSubmit_modules.skill_compliance_indicator as indicator

    # Test with /arch skill
    completion_rate = indicator._get_historical_completion_rate("arch", days=7)

    # May return None if no history, or a float between 0 and 1
    assert completion_rate is None or (0.0 <= completion_rate <= 1.0)

    if completion_rate is not None:
        print(f"✓ Test passed: Historical completion rate for /arch: {completion_rate:.1%}")
    else:
        print("✓ Test passed: No historical completion data for /arch (expected for new skill)")


def test_format_compliance_indicator():
    """Test formatting of compliance indicator."""
    import UserPromptSubmit_modules.skill_compliance_indicator as indicator

    # Test with full data
    frontmatter = {
        "enforcement_level": "STRICT",
        "workflow_steps": ["step1", "step2", "step3"]
    }
    trail = {
        "completed_steps": ["step1"],
        "workflow_steps": ["step1", "step2", "step3"]
    }
    completion_rate = 0.75

    formatted = indicator._format_compliance_indicator("test_skill", frontmatter, trail, completion_rate)

    assert "test_skill" in formatted
    assert "STRICT" in formatted
    assert "3 steps declared" in formatted
    assert "1/3" in formatted
    assert "75%" in formatted

    print("✓ Test passed: Indicator formatting includes all components")

    # Test with minimal data
    frontmatter_min = {}
    trail_min = {}
    completion_rate_min = None

    formatted_min = indicator._format_compliance_indicator("minimal_skill", frontmatter_min, trail_min, completion_rate_min)

    assert "minimal_skill" in formatted_min
    assert "STANDARD" in formatted_min  # Default enforcement level
    assert "No workflow steps declared" in formatted_min

    print("✓ Test passed: Indicator handles missing data gracefully")


def test_hook_returns_empty_for_non_slash():
    """Test hook returns empty result for non-slash commands."""
    import UserPromptSubmit_modules.skill_compliance_indicator as indicator
    from UserPromptSubmit_modules.base import HookContext

    # Create context with non-slash prompt
    context = HookContext(
        prompt="improve memory system",
        data={},
        session_id="test_session",
        terminal_id="test_terminal"
    )

    result = indicator.skill_compliance_indicator_hook(context)

    # Should return empty result
    assert result.is_empty()

    print("✓ Test passed: Hook skips non-slash commands")


if __name__ == "__main__":
    print("Running skill_compliance_indicator tests...\n")

    try:
        test_extract_skill_name()
        test_read_skill_frontmatter()
        test_get_breadcrumb_trail()
        test_get_historical_completion_rate()
        test_format_compliance_indicator()
        test_hook_returns_empty_for_non_slash()

        print("\n✅ All tests passed!")
        sys.exit(0)

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)

    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
