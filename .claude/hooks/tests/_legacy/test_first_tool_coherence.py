"""
Tests for first-tool coherence check (v3.5).

Validates that skills declaring allowed_first_tools in frontmatter
get their first non-investigation tool call checked for coherence.

Run with: pytest .claude/hooks/tests/test_first_tool_coherence.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

# Add hooks directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "PreToolUse"))

from PreToolUse_skill_pattern_gate import _check_first_tool_coherence

# =============================================================================
# STATE FIXTURES
# =============================================================================


def _make_state(
    skill: str = "ask",
    allowed_first_tools: list[str] | None = None,
    first_tool_validated: bool = False,
) -> dict:
    """Build a minimal skill execution state for testing."""
    return {
        "skill": skill,
        "allowed_first_tools": allowed_first_tools or [],
        "first_tool_validated": first_tool_validated,
    }


# =============================================================================
# TESTS: COHERENCE CHECK LOGIC
# =============================================================================


class TestFirstToolCoherence:
    """Test the _check_first_tool_coherence function."""

    def test_allows_tool_in_allowed_list(self):
        """Grep is allowed as first tool for /ask."""
        state = _make_state(
            skill="ask",
            allowed_first_tools=["Grep", "Glob", "Read", "Task", "WebSearch"],
        )
        with patch("PreToolUse_skill_pattern_gate.FIRST_TOOL_COHERENCE_ENABLED", True):
            result = _check_first_tool_coherence("Grep", state)
        assert not result.get("block"), f"Should allow Grep but got: {result}"

    def test_blocks_tool_not_in_allowed_list(self):
        """Bash is NOT allowed as first tool for /ask (discovery skill)."""
        state = _make_state(
            skill="ask",
            allowed_first_tools=["Grep", "Glob", "Read", "Task", "WebSearch"],
        )
        with patch("PreToolUse_skill_pattern_gate.FIRST_TOOL_COHERENCE_ENABLED", True):
            result = _check_first_tool_coherence("Bash", state)
        assert result.get("block"), "Should block Bash for /ask"
        assert "FIRST-TOOL COHERENCE MISMATCH" in result.get("reason", "")

    def test_skips_when_no_allowed_first_tools(self):
        """Skills without allowed_first_tools are not checked."""
        state = _make_state(
            skill="standards",
            allowed_first_tools=[],
        )
        with patch("PreToolUse_skill_pattern_gate.FIRST_TOOL_COHERENCE_ENABLED", True):
            result = _check_first_tool_coherence("Bash", state)
        assert not result.get("block"), "Should allow when no allowed_first_tools declared"

    def test_skips_when_already_validated(self):
        """After first tool passes, subsequent tools are not checked."""
        state = _make_state(
            skill="ask",
            allowed_first_tools=["Grep", "Glob"],
            first_tool_validated=True,
        )
        with patch("PreToolUse_skill_pattern_gate.FIRST_TOOL_COHERENCE_ENABLED", True):
            result = _check_first_tool_coherence("Bash", state)
        assert not result.get("block"), "Should allow after first tool validated"

    def test_skips_when_disabled(self):
        """Feature flag disables coherence checking."""
        state = _make_state(
            skill="ask",
            allowed_first_tools=["Grep", "Glob"],
        )
        with patch("PreToolUse_skill_pattern_gate.FIRST_TOOL_COHERENCE_ENABLED", False):
            result = _check_first_tool_coherence("Bash", state)
        assert not result.get("block"), "Should allow when feature disabled"

    def test_task_tool_allowed_for_ask(self):
        """Task tool (subagent) is allowed as first tool for /ask."""
        state = _make_state(
            skill="ask",
            allowed_first_tools=["Grep", "Glob", "Read", "Task", "WebSearch"],
        )
        with patch("PreToolUse_skill_pattern_gate.FIRST_TOOL_COHERENCE_ENABLED", True):
            result = _check_first_tool_coherence("Task", state)
        assert not result.get("block"), "Task should be allowed for /ask"

    def test_blocks_edit_for_discover(self):
        """Edit is NOT allowed as first tool for /discover."""
        state = _make_state(
            skill="discover",
            allowed_first_tools=["Grep", "Glob", "Read", "Task"],
        )
        with patch("PreToolUse_skill_pattern_gate.FIRST_TOOL_COHERENCE_ENABLED", True):
            result = _check_first_tool_coherence("Edit", state)
        assert result.get("block"), "Should block Edit for /discover"

    def test_bash_allowed_for_test_skill(self):
        """Bash IS allowed as first tool for /test (needs to run pytest)."""
        state = _make_state(
            skill="test",
            allowed_first_tools=["Bash", "Task", "Grep", "Glob", "Read"],
        )
        with patch("PreToolUse_skill_pattern_gate.FIRST_TOOL_COHERENCE_ENABLED", True):
            result = _check_first_tool_coherence("Bash", state)
        assert not result.get("block"), "Bash should be allowed for /test"

    def test_block_message_includes_skill_name(self):
        """Block reason includes the skill name for debugging."""
        state = _make_state(
            skill="ask",
            allowed_first_tools=["Grep"],
        )
        with patch("PreToolUse_skill_pattern_gate.FIRST_TOOL_COHERENCE_ENABLED", True):
            result = _check_first_tool_coherence("Bash", state)
        assert "/ask" in result.get("reason", ""), "Block reason should mention /ask"

    def test_block_message_lists_allowed_tools(self):
        """Block reason lists the allowed tools for user guidance."""
        state = _make_state(
            skill="ask",
            allowed_first_tools=["Grep", "Glob", "Read"],
        )
        with patch("PreToolUse_skill_pattern_gate.FIRST_TOOL_COHERENCE_ENABLED", True):
            result = _check_first_tool_coherence("Bash", state)
        reason = result.get("reason", "")
        assert "Grep" in reason, "Block reason should list allowed tools"
        assert "Glob" in reason, "Block reason should list allowed tools"


# =============================================================================
# INTEGRATION: STATE MANAGEMENT
# =============================================================================


class TestStateManagement:
    """Test that skill_execution_state properly tracks first-tool fields."""

    def test_load_frontmatter_ask(self):
        """Verify /ask SKILL.md frontmatter contains allowed_first_tools."""
        from skill_guard.skill_execution_state import _load_skill_frontmatter

        result = _load_skill_frontmatter("ask")
        aft = result.get("allowed_first_tools", [])
        assert len(aft) > 0, "/ask should declare allowed_first_tools"
        assert "Grep" in aft, "/ask should allow Grep as first tool"
        assert "Bash" not in aft, "/ask should NOT allow Bash as first tool"

    def test_load_frontmatter_test(self):
        """Verify /test SKILL.md frontmatter contains allowed_first_tools."""
        from skill_guard.skill_execution_state import _load_skill_frontmatter

        result = _load_skill_frontmatter("test")
        aft = result.get("allowed_first_tools", [])
        assert len(aft) > 0, "/test should declare allowed_first_tools"
        assert "Bash" in aft, "/test should allow Bash as first tool"

    def test_load_frontmatter_nonexistent_skill(self):
        """Non-existent skill returns empty allowed_first_tools."""
        from skill_guard.skill_execution_state import _load_skill_frontmatter

        result = _load_skill_frontmatter("this-skill-does-not-exist-xyz")
        assert result.get("allowed_first_tools") == []

    def test_load_frontmatter_skill_without_field(self):
        """Skill without allowed_first_tools returns empty list."""
        from skill_guard.skill_execution_state import _load_skill_frontmatter

        # standards skill should NOT have allowed_first_tools
        result = _load_skill_frontmatter("standards")
        assert result.get("allowed_first_tools") == []
