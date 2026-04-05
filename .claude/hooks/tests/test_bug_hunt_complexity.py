#!/usr/bin/env python3
"""
Tests for BUG-HUNT Command Complexity Integration.

TDD RED phase: These tests FAIL initially, then drive implementation.

This module tests the --focus complexity flag integration in the /bug-hunt command.
"""

from pathlib import Path

import pytest


# Helper to get bug-hunt SKILL.md path
def get_bug_hunt_md():
    # From .claude/hooks/tests/, go up 3 levels to .claude/, then into skills/
    base_dir = Path(__file__).resolve().parent.parent.parent
    candidates = [
        base_dir / "skills" / "bug-hunt" / "SKILL.md",
        Path("P:/.claude/skills/bug-hunt/SKILL.md"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]  # Fallback


def test_bug_hunt_complexity_in_focus_categories():
    """
    Test that --focus complexity is in the Focus Categories table.

    Given: The bug-hunt command documentation
    When: Checking for complexity focus category
    Then: Should be listed with tools and example bugs

    This enables users to focus bug-hunt on complexity issues.
    """
    bug_hunt_md = get_bug_hunt_md()
    content = bug_hunt_md.read_text()

    assert "--focus complexity" in content or "`--focus complexity`" in content, \
        "bug-hunt.md should include --focus complexity in Focus Categories"


def test_bug_hunt_complexity_in_handles():
    """
    Test that complexity-related terms are in handles.

    Given: The bug-hunt command frontmatter
    When: Checking handles for complexity terms
    Then: Should include cyclomatic complexity, code complexity

    This makes the command discoverable for complexity-related queries.
    """
    bug_hunt_md = get_bug_hunt_md()
    content = bug_hunt_md.read_text()

    # Check for complexity-related handles
    has_complexity_handle = (
        "cyclomatic complexity" in content.lower() or
        "code complexity" in content.lower() or
        "complex" in content.lower() and "complexity" in content.lower()
    )

    assert has_complexity_handle, \
        "bug-hunt.md handles should include complexity-related terms"


def test_bug_hunt_complexity_in_tool_table():
    """
    Test that complexity is in the Tool Integration table.

    Given: The bug-hunt command documentation
    When: Checking the Tool Integration table
    Then: Should include complexity/radon/lizard

    This shows complexity as a first-class tool in bug-hunt.
    """
    bug_hunt_md = get_bug_hunt_md()
    content = bug_hunt_md.read_text()

    # Check for complexity tools in the tool table
    has_complexity_tool = (
        "complexity" in content.lower() and (
            "radon" in content.lower() or
            "lizard" in content.lower()
        )
    )

    assert has_complexity_tool, \
        "bug-hunt.md Tool Integration table should include complexity/radon/lizard"


def test_bug_hunt_complexity_example():
    """
    Test that there's a complexity focus example.

    Given: The bug-hunt command documentation
    When: Looking at Examples section
    Then: Should have example for --focus complexity

    This shows users how to use complexity focus.
    """
    bug_hunt_md = Path(__file__).resolve().parent.parent / "commands" / "bug-hunt.md"

    # Try relative path from tests
    bug_hunt_md = get_bug_hunt_md()
    content = bug_hunt_md.read_text()

    # Check for complexity example in Examples section
    has_example = (
        "## Examples" in content and
        ("complexity" in content.lower() and "bug-hunt" in content.lower())
    )

    assert has_example, \
        "bug-hunt.md Examples section should show complexity usage"


def test_bug_hunt_complexity_refers_to_complexity_command():
    """
    Test that bug-hunt references /complexity command.

    Given: The bug-hunt command documentation
    When: Checking See Also section
    Then: Should reference /complexity command

    This provides cross-referencing between commands.
    """
    bug_hunt_md = get_bug_hunt_md()
    content = bug_hunt_md.read_text()

    # Check for /complexity reference in See Also
    see_also_section = content.split("## See Also")[-1] if "## See Also" in content else ""
    has_complexity_ref = "/complexity" in see_also_section

    assert has_complexity_ref, \
        "bug-hunt.md See Also section should reference /complexity command"


def test_bug_hunt_complexity_tools_flag():
    """
    Test that --tools complexity is supported.

    Given: The bug-hunt command documentation
    When: Checking Tool-Specific Flags table
    Then: Should support --tools complexity

    This allows selective complexity analysis.
    """
    bug_hunt_md = get_bug_hunt_md()
    content = bug_hunt_md.read_text()

    # Check for complexity in tools flag options
    tools_section = content.split("### Tool-Specific Flags")[1].split("##")[0] if "### Tool-Specific Flags" in content else ""
    has_complexity_tools = (
        "complexity" in tools_section.lower() or
        "radon" in tools_section.lower() or
        "lizard" in tools_section.lower()
    )

    assert has_complexity_tools, \
        "bug-hunt.md Tool-Specific Flags should include complexity/radon/lizard"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
