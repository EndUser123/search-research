"""Integration tests for intent_classifier + skill_enforcer interaction.

This test file verifies the end-to-end behavior:
1. intent_classifier runs first (priority 0.5)
2. skill_enforcer respects topic inquiry classification (priority 1.0)
3. Topic inquiries do NOT trigger SKILL EXECUTION LANE injection
4. Normal commands still trigger enforcement
"""

from UserPromptSubmit.intent_classifier import is_topic_inquiry
from UserPromptSubmit.skill_enforcer import is_command_directive


class TestIntentClassifierIntegration:
    """Test end-to-end integration of intent classification with skill enforcement."""

    def test_topic_inquiry_not_treated_as_command(self):
        """Verify that topic inquiries about /s are NOT treated as command directives."""
        topic_inquiries = [
            "tell me about /s",
            "what is /s",
            "find information about /s",
            "/s usage and frictions",
            "errors from today regarding /s",
        ]

        for prompt in topic_inquiries:
            # Topic inquiry should be detected
            assert is_topic_inquiry(prompt), f"Prompt '{prompt}' should be detected as topic inquiry"

            # But NOT treated as a command directive (no enforcement)
            assert not is_command_directive(prompt), f"Prompt '{prompt}' should NOT trigger command enforcement"

    def test_commands_still_enforced(self):
        """Verify that actual slash commands still trigger enforcement.

        Note: skill_enforcer only detects commands at the START of the prompt.
        "run /s" is not a command because it doesn't start with "/".
        """
        commands = [
            "/s",
            "/s args",
        ]

        for prompt in commands:
            # Should NOT be detected as topic inquiry
            assert not is_topic_inquiry(prompt), f"Prompt '{prompt}' should NOT be detected as topic inquiry"

            # But SHOULD be treated as command directive (enforcement triggered)
            assert is_command_directive(prompt), f"Prompt '{prompt}' should trigger command enforcement"

        # Edge case: "run /s" is NOT a command (doesn't start with /)
        # and is NOT a topic inquiry (no "about" keyword)
        assert not is_command_directive("run /s"), "Prompt 'run /s' should NOT trigger enforcement (doesn't start with /)"
        assert not is_topic_inquiry("run /s"), "Prompt 'run /s' should NOT be topic inquiry"

    def test_case_insensitive_integration(self):
        """Verify case-insensitive pattern matching works end-to-end."""
        variations = [
            "TELL ME ABOUT /S",
            "What Is /Ask-Cli",
            "REGARDING /s",
        ]

        for prompt in variations:
            # Should be detected as topic inquiry
            assert is_topic_inquiry(prompt), f"Prompt '{prompt}' should be detected as topic inquiry (case-insensitive)"

            # Should NOT trigger enforcement
            assert not is_command_directive(prompt), f"Prompt '{prompt}' should NOT trigger enforcement (case-insensitive)"

    def test_hook_execution_order(self):
        """Verify that intent_classifier runs before skill_enforcer."""
        from UserPromptSubmit.registry import HOOK_PRIORITY

        # Get priorities for both hooks
        intent_priority = HOOK_PRIORITY.get("intent_classifier")
        skill_priority = HOOK_PRIORITY.get("skill_enforcer")

        # Verify intent_classifier has lower priority number (runs earlier)
        assert intent_priority is not None, "intent_classifier hook should be registered"
        assert skill_priority is not None, "skill_enforcer hook should be registered"
        assert intent_priority < skill_priority, (
            f"intent_classifier priority ({intent_priority}) "
            f"should be less than skill_enforcer priority ({skill_priority})"
        )
