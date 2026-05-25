"""Tests for unified_injector.py module.

Tests verify:
1. Module can be imported
2. Core functions exist: detect_command(), build_command_injection(), extract_goal(), build_goal_injection()
3. run_unified_injector() function exists and returns HookResult
4. SOLO_DEV_CONTEXT constant is defined
5. Falsification detection is implemented
"""

import sys
from pathlib import Path

import pytest

_hooks_dir = Path(__file__).resolve().parent.parent.parent
if str(_hooks_dir) not in sys.path:
    sys.path.insert(0, str(_hooks_dir))


class TestSoloDevContext:
    """Test solo dev context constant."""

    def test_solo_dev_context_exists(self):
        """Test that SOLO_DEV_CONTEXT constant is defined."""
        from UserPromptSubmit.unified_injector import SOLO_DEV_CONTEXT
        assert SOLO_DEV_CONTEXT
        assert "Solo" in SOLO_DEV_CONTEXT
        assert len(SOLO_DEV_CONTEXT) > 50


class TestUnifiedInjectorModuleExists:
    """Test module can be imported."""

    def test_module_can_be_imported(self):
        """Test that unified_injector module can be imported."""
        from UserPromptSubmit import unified_injector
        assert unified_injector is not None

    def test_detect_command_function_exists(self):
        """Test that detect_command() function exists."""
        from UserPromptSubmit import unified_injector
        assert hasattr(unified_injector, "detect_command")
        assert callable(unified_injector.detect_command)

    def test_build_command_injection_function_exists(self):
        """Test that build_command_injection() function exists."""
        from UserPromptSubmit import unified_injector
        assert hasattr(unified_injector, "build_command_injection")
        assert callable(unified_injector.build_command_injection)

    def test_extract_goal_function_exists(self):
        """Test that extract_goal() function exists."""
        from UserPromptSubmit import unified_injector
        assert hasattr(unified_injector, "extract_goal")
        assert callable(unified_injector.extract_goal)

    def test_build_goal_injection_function_exists(self):
        """Test that build_goal_injection() function exists."""
        from UserPromptSubmit import unified_injector
        assert hasattr(unified_injector, "build_goal_injection")
        assert callable(unified_injector.build_goal_injection)

    def test_detect_falsification_risk_function_exists(self):
        """Test that detect_falsification_risk() function exists."""
        from UserPromptSubmit import unified_injector
        assert hasattr(unified_injector, "detect_falsification_risk")
        assert callable(unified_injector.detect_falsification_risk)


class TestUnifiedInjectorGoalFunctions:
    """Tests for goal extraction functions."""

    def test_extract_goal_returns_string_or_none(self):
        """Test that extract_goal() returns string or None.

        Given: A prompt text with goal pattern
        When: extract_goal() is called
        Then: It should return the goal text string or None
        """
        from UserPromptSubmit.unified_injector import extract_goal
        result = extract_goal("my goal is to fix authentication")
        assert isinstance(result, (str, type(None)))
        assert result == "fix authentication" or result is None

    def test_extract_goal_no_goal_returns_none(self):
        """Test that extract_goal() returns None when no goal pattern."""
        from UserPromptSubmit.unified_injector import extract_goal
        result = extract_goal("just implement this feature")
        assert result is None


class TestUnifiedInjectorFalsificationDetection:
    """Tests for falsification detection functions."""

    def test_detect_falsification_risk_with_test_keyword(self):
        """Test that 'just test this' pattern triggers falsification detection."""
        from UserPromptSubmit.unified_injector import detect_falsification_risk
        assert detect_falsification_risk("Just test this to verify it works") is True

    def test_detect_falsification_risk_with_implementation(self):
        """Test that implementation language triggers falsification detection."""
        from UserPromptSubmit.unified_injector import detect_falsification_risk
        assert detect_falsification_risk("add minimal example code") is True

    def test_no_falsification_risk_for_normal_request(self):
        """Test that normal requests don't trigger falsification detection."""
        from UserPromptSubmit.unified_injector import detect_falsification_risk
        assert not detect_falsification_risk("implement user authentication system")


class TestUnifiedInjectorMainEntry:
    """Tests for main run_unified_injector() function."""

    def test_run_unified_injector_function_exists(self):
        """Test that run_unified_injector() function exists."""
        from UserPromptSubmit import unified_injector
        assert hasattr(unified_injector, "run_unified_injector")
        assert callable(unified_injector.run_unified_injector)

    def test_run_unified_injector_returns_hook_result(self, mock_context):
        """Test that run_unified_injector() returns HookResult."""
        from UserPromptSubmit.base import HookResult
        from UserPromptSubmit.unified_injector import run_unified_injector

        result = run_unified_injector(mock_context)
        assert isinstance(result, HookResult)
        assert hasattr(result, "context")
        assert hasattr(result, "tokens")

    def test_run_unified_injector_includes_solo_context(self, mock_context):
        """Result should always include solo dev context."""
        from UserPromptSubmit.unified_injector import run_unified_injector
        result = run_unified_injector(mock_context)
        assert "Solo" in result.context

    def test_run_unified_injector_with_command(self, mock_context):
        """Result should include command context when detected."""
        from UserPromptSubmit.unified_injector import run_unified_injector

        mock_context.prompt = 'build feature X'
        result = run_unified_injector(mock_context)
        assert '/build' in result.context

    def test_run_unified_injector_skips_slash_command_injection(self, mock_context):
        """Slash command context should come from skill_enforcer, not unified injector."""
        from UserPromptSubmit.unified_injector import run_unified_injector

        mock_context.prompt = '/build feature X'
        result = run_unified_injector(mock_context)
        assert '**Command**' not in result.context

    def test_run_unified_injector_with_falsification_note(self, mock_context):
        """Result should include falsification note when detected."""
        from UserPromptSubmit.unified_injector import run_unified_injector

        mock_context.prompt = 'Just test this to verify it works'
        result = run_unified_injector(mock_context)
        assert 'test' in result.context.lower()
        assert 'TDD' in result.context


@pytest.fixture
def mock_context():
    """Provide mock HookContext for testing."""
    from UserPromptSubmit.base import HookContext
    return HookContext(
        prompt='test prompt',
        data={},
        session_id='test-session',
        terminal_id='test-terminal'
    )


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
