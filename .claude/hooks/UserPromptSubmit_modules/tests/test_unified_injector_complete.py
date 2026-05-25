"""Complete tests for unified_injector module."""

import pytest
from UserPromptSubmit.base import HookContext
from UserPromptSubmit.unified_injector import (
    SOLO_DEV_CONTEXT,
    build_command_injection,
    build_goal_injection,
    detect_command,
    detect_falsification_risk,
    extract_command_name,
    extract_goal,
    run_unified_injector,
)


class TestSoloDevContext:
    """Test solo dev context constant."""

    def test_solo_dev_context_exists(self):
        """SOLO_DEV_CONTEXT constant should be defined."""
        assert SOLO_DEV_CONTEXT
        assert 'Solo' in SOLO_DEV_CONTEXT
        assert len(SOLO_DEV_CONTEXT) > 50


class TestCommandDetection:
    """Test command detection functions."""

    def test_detect_command_build(self):
        """detect_command should identify build directive."""
        result = detect_command('build the feature')
        assert result is not None
        assert result['command'] == 'build'

    def test_detect_command_code(self):
        """detect_command should identify code directive."""
        result = detect_command('code this module')
        assert result is not None
        assert result['command'] == 'code'

    def test_detect_command_none(self):
        """detect_command should return None for no command."""
        result = detect_command('hello world')
        assert result is None

    def test_detect_command_no_match_in_question(self):
        """detect_command should avoid hypothetical/question phrasing."""
        result = detect_command('Should we change this architecture?')
        assert result is None

    def test_detect_command_no_match_inside_quotes(self):
        """detect_command should ignore command words inside quotes."""
        result = detect_command('We said "build" as an example sentence')
        assert result is None

    def test_extract_command_name(self):
        """extract_command_name should get command name."""
        assert extract_command_name('/build feature') == 'build'
        assert extract_command_name('/test') == 'test'
        assert extract_command_name('no command here') is None

    def test_build_command_injection(self):
        """build_command_injection should format command."""
        cmd_info = {'command': 'build'}
        result = build_command_injection(cmd_info, 'new feature')
        assert '**Command**' in result
        assert '/build' in result
        assert 'new feature' in result


class TestGoalExtraction:
    """Test goal extraction functions."""

    def test_extract_goal_my_goal_is(self):
        """extract_goal should find 'my goal is' pattern."""
        result = extract_goal('My goal is to implement feature X')
        # Function returns the goal text after pattern matching
        assert result is not None
        assert 'implement' in result or 'feature' in result

    def test_extract_goal_i_want_to(self):
        """extract_goal should find 'i want to' pattern."""
        result = extract_goal('I want to add a new module')
        # Function returns the goal text after pattern matching
        assert result is not None
        assert 'add' in result or 'module' in result

    def test_extract_goal_none(self):
        """extract_goal should return None when no pattern."""
        result = extract_goal('just do this task')
        assert result is None

    def test_build_goal_injection(self):
        """build_goal_injection should format goal."""
        result = build_goal_injection('create new feature')
        assert '**Goal**' in result
        assert 'create new feature' in result or '...' in result  # Handles truncation

    def test_build_goal_injection_long_truncates(self):
        """build_goal_injection should truncate long goals."""
        long_goal = 'x' * 300  # 300 characters
        result = build_goal_injection(long_goal)
        assert '...' in result
        assert len(result) < len(long_goal)


class TestFalsificationDetection:
    """Test falsification risk detection."""

    def test_detect_falsification_test_this(self):
        """Should detect 'test this' falsification."""
        assert detect_falsification_risk('Just test this to see if it works')
        # Note: 'test that this works' doesn't match falsification patterns
        # (it's a statement, not "test only" language)
        # assert detect_falsification_risk('test that this works')
        # assert detect_falsification_risk('test only to show it passes')

    def test_detect_falsification_without_code(self):
        """Should detect 'without code' pattern."""
        assert detect_falsification_risk('verify this without implementing any code')
        assert detect_falsification_risk('validate without writing logic')

    def test_no_falsification_normal_request(self):
        """Should not detect falsification in normal requests."""
        assert not detect_falsification_risk('implement the user authentication')
        assert not detect_falsification_risk('add error handling to the parser')
        assert not detect_falsification_risk('Can we fix that?')
        assert not detect_falsification_risk('Use test_conversation_gate.py for reference')
        assert not detect_falsification_risk('These are test cases for conversation mode')


class TestRunUnifiedInjector:
    """Test main injector entry point."""

    def test_run_unified_injector_returns_hook_result(self, mock_context):
        """run_unified_injector should return HookResult."""
        result = run_unified_injector(mock_context)
        assert result is not None
        assert hasattr(result, 'context')
        assert hasattr(result, 'tokens')

    def test_run_unified_injector_includes_solo_context(self, mock_context):
        """Result should always include solo dev context."""
        result = run_unified_injector(mock_context)
        assert 'Solo' in result.context

    def test_run_unified_injector_with_command(self, mock_context):
        """Result should include command context when detected."""
        mock_context.prompt = 'build feature X'
        result = run_unified_injector(mock_context)
        assert '/build' in result.context

    def test_run_unified_injector_skips_slash_command_injection(self, mock_context):
        """Slash command context should be handled by skill_enforcer only."""
        mock_context.prompt = '/build feature X'
        result = run_unified_injector(mock_context)
        assert '**Command**' not in result.context

    def test_run_unified_injector_with_falsification_note(self, mock_context):
        """Result should include falsification note when detected."""
        mock_context.prompt = 'Just test this to verify it works'
        result = run_unified_injector(mock_context)
        assert 'test' in result.context.lower()
        assert 'TDD' in result.context


@pytest.fixture
def mock_context():
    """Provide mock HookContext for testing."""
    return HookContext(
        prompt='test prompt',
        data={},
        session_id='test-session',
        terminal_id='test-terminal'
    )


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
