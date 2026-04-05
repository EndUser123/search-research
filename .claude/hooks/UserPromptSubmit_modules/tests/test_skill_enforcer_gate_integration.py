"""Test skill_enforcer SKILL-FIRST GATE integration.

Tests that build_command_context() properly marks skills as loaded
when context is injected via UserPromptSubmit, preventing SKILL-FIRST GATE
from blocking slash commands.

This fix resolves the issue where users typing slash commands like `/plan-workflow`
would get blocked by the SKILL-FIRST GATE even though UserPromptSubmit had already
injected the skill context.
"""

import inspect
import sys

sys.path.insert(0, 'P:/.claude/hooks')

from UserPromptSubmit.skill_enforcer import (
    build_command_context,
    should_block_command,
)


class TestBuildContextSignature:
    """Test that build_command_context has the correct signature for SKILL-FIRST GATE integration."""

    def test_has_context_parameter(self):
        """Verify build_command_context accepts context parameter.

        The 'context' parameter is critical for the SKILL-FIRST GATE integration.
        When UserPromptSubmit injects skill context, it passes the HookContext,
        which build_command_context() uses to call set_skill_loaded() to mark
        the skill as loaded, preventing the SKILL-FIRST GATE from blocking.
        """
        sig = inspect.signature(build_command_context)
        params = list(sig.parameters.keys())

        assert "command" in params, "Missing 'command' parameter"
        assert "args" in params, "Missing 'args' parameter"
        assert "context" in params, "Missing 'context' parameter - SKILL-FIRST GATE integration requires this"

        # Context should be optional for backward compatibility
        assert sig.parameters["context"].default is None, "Context parameter should default to None"


class TestSkillLoadedMarking:
    """Test that build_command_context marks skills as loaded when context is provided."""

    def test_integration_code_exists_in_source(self):
        """Verify the SKILL-FIRST GATE integration code exists in the source.

        Checks that:
        1. set_skill_loaded() is imported
        2. set_skill_loaded() is called when context is provided
        3. The call is guarded by 'if context:'
        """
        import UserPromptSubmit.skill_enforcer as se_module
        source_file = inspect.getsourcefile(se_module)

        with open(source_file) as f:
            source = f.read()

        # Check for the import
        assert "from skill_guard.skill_execution_state import set_skill_loaded" in source, \
            "Missing import for set_skill_loaded - required for SKILL-FIRST GATE integration"

        # Check for the call
        assert "set_skill_loaded(command)" in source, \
            "Missing call to set_skill_loaded() - the core of the SKILL-FIRST GATE fix"

        # Check for the context guard
        assert "if context:" in source, \
            "Missing context guard - set_skill_loaded should only be called when context is provided"


class TestBackwardCompatibility:
    """Test that the fix maintains backward compatibility."""

    def test_works_without_context(self):
        """Test that build_command_context works without context (backward compatibility).

        Before the SKILL-FIRST GATE integration, build_command_context() was called
        without a context parameter. The fix should maintain this compatibility.
        """
        # Should not raise an exception
        result = build_command_context("test-skill", "some args", context=None)

        assert isinstance(result, str), "Should return a string"
        assert len(result) > 0, "Should not return empty string"
        assert "SKILL ACTIVATION REQUIRED" in result, "Should contain activation directive"

    def test_works_for_various_commands(self):
        """Test that the function works for various command types."""
        test_cases = [
            ("search", "query"),
            ("plan-workflow", "build feature"),
            ("test-command", ""),
            ("help", ""),  # Blocklisted command
        ]

        for cmd, args in test_cases:
            result = build_command_context(cmd, args, context=None)
            assert result is not None, f"Command '{cmd}' should not return None"
            assert isinstance(result, str), f"Command '{cmd}' should return string"
            assert len(result) > 0, f"Command '{cmd}' should not return empty string"


class TestGeneratedContext:
    """Test the generated context content."""

    def test_contains_activation_directive(self):
        """Test that generated context includes SKILL ACTIVATION REQUIRED directive."""
        result = build_command_context("test-skill", "some args", context=None)

        assert "SKILL ACTIVATION REQUIRED" in result, \
            "Should contain SKILL ACTIVATION REQUIRED directive"
        assert 'Skill("test-skill")' in result, \
            "Should instruct to call Skill() with the command name"

    def test_contains_command_information(self):
        """Test that generated context includes command and args."""
        result = build_command_context("test-skill", "some args here", context=None)

        assert "/test-skill" in result, "Should contain command name with slash"
        assert "some args here" in result, "Should contain command arguments"


class TestShouldBlockCommand:
    """Test should_block_command logic."""

    def test_allowed_commands_not_blocked(self):
        """Test that non-blocklisted commands are not blocked by default."""
        assert not should_block_command("search")
        assert not should_block_command("plan-workflow")
        assert not should_block_command("test-command")

    def test_blocklisted_commands_blocked(self):
        """Test that blocklisted commands return True."""
        assert should_block_command("help")
        assert should_block_command("clear")
        assert should_block_command("exit")


class TestSKILLFIRSTGateIntegration:
    """Integration tests for the complete SKILL-FIRST GATE fix."""

    def test_fix_resolves_user_issue(self):
        """
        Test that the fix resolves the original user issue.

        ORIGINAL ISSUE:
        User types: "/plan-workflow build fix contract system to support skills properly"
        Expected: Skill context is injected, SKILL-FIRST GATE recognizes skill is loaded
        Actual (before fix): SKILL-FIRST GATE blocks because it only recognizes Skill() tool calls

        FIX:
        1. UserPromptSubmit calls build_command_context() WITH context parameter
        2. build_command_context() calls set_skill_loaded() to mark skill as loaded
        3. SKILL-FIRST GATE checks state file and sees skill is already loaded
        4. SKILL-FIRST GATE allows tools to proceed

        This test verifies the integration code is in place.
        """
        import UserPromptSubmit.skill_enforcer as se_module
        source_file = inspect.getsourcefile(se_module)

        with open(source_file) as f:
            source = f.read()

        # Verify the complete integration chain exists in source
        integration_points = [
            "from skill_guard.skill_execution_state import set_skill_loaded",
            "if context:",
            "set_skill_loaded(command)",
        ]

        for point in integration_points:
            assert point in source, f"Missing integration point: {point}"

    def test_function_always_returns(self):
        """
        Test that function always returns a value (never None).

        BUG FIX: Previously, the function had a missing return statement
        when report_path was found, causing it to return None.
        """
        # Test with various commands to ensure all paths return
        test_commands = [
            ("search", "query text"),
            ("plan-workflow", "build feature"),
            ("test", ""),
        ]

        for cmd, args in test_commands:
            result = build_command_context(cmd, args, context=None)
            assert result is not None, f"Command '{cmd}' returned None (missing return statement)"
            assert isinstance(result, str), f"Command '{cmd}' returned non-string type"
            assert len(result) > 0, f"Command '{cmd}' returned empty string"
