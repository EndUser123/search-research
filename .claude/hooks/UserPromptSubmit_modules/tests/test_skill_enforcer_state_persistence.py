
"""Tests for skill_enforcer.py state persistence failure handling.

GREEN PHASE: Test PASSES - verifies graceful degradation when state persistence fails.

This test demonstrates that state persistence failures are handled gracefully:
- No exception is raised
- HookResult is returned
- Warning is logged to stdout
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add hooks directory to path for imports
_hooks_dir = Path(__file__).resolve().parent.parent.parent
if str(_hooks_dir) not in sys.path:
    sys.path.insert(0, str(_hooks_dir))


class TestSkillEnforcerStatePersistence:
    """Tests for state persistence failure handling in run_skill_enforcer."""

    def test_state_persistence_failure_raises_exception(self, capsys):
        """GREEN PHASE: Test PASSES - verifies graceful degradation.

        Given: A HookContext with a slash command prompt
        When: _store_command_intent() fails with OSError (permission denied)
        Then: skill_enforcement_hook() handles error gracefully and returns HookResult

        The implementation handles state persistence failures gracefully:
        - No exception is raised
        - HookResult is returned
        - Warning is logged to stdout
        """
        from unittest.mock import patch

        import UserPromptSubmit.skill_enforcer as se_module
        from UserPromptSubmit.base import HookContext, HookResult
        from UserPromptSubmit.skill_enforcer import skill_enforcement_hook

        # Create test context with slash command
        context = HookContext(
            prompt="/test command",
            data={},
            session_id="test-session",
            terminal_id="test-terminal"
        )

        # Mock module-level functions
        with patch.object(
            se_module, '_store_command_intent',
            side_effect=OSError("Permission denied")
        ), patch.object(
            se_module, '_store_active_command',
            return_value=None  # succeeds
        ):
            # GREEN PHASE: Verify graceful degradation
            # The implementation handles state persistence failures gracefully
            # and continues to return HookResult
            import warnings
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                result = skill_enforcement_hook(context)

                # Verify result is returned (no exception raised)
                assert result is not None
                assert isinstance(result, HookResult)

                # Verify warning was logged
                assert len(w) >= 1
                assert any("Failed to persist command intent" in str(warning.message) for warning in w)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
