#!/usr/bin/env python3
"""Test E2E Tracker integration with PostToolUse router."""

import sys
from pathlib import Path

import pytest

# Add hooks directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from posttooluse.e2e_tracker_hook import E2ETrackerHook


class TestE2ETrackerIntegration:
    """Test E2E tracker hook integration."""

    def test_hook_creation(self):
        """Test that E2E tracker hook can be instantiated."""
        hook = E2ETrackerHook()
        assert hook is not None
        assert hook.enabled is True
        assert hook.tool_matcher is None  # Tracks all tools

    def test_skill_invocation_tracking(self):
        """Test tracking skill invocations."""
        hook = E2ETrackerHook()

        result = hook.process(
            tool_name='Skill',
            tool_input={'skill': 'test-skill'},
            tool_response={'success': True, 'context': {'session_id': 'test-session'}}
        )

        assert result['passed'] is True
        assert result['tracked'] is True
        assert result['workflow_type'] == 'skill_invocation'

    def test_tool_chain_tracking(self):
        """Test tracking tool chain operations."""
        hook = E2ETrackerHook()

        # Test Read
        result = hook.process(
            tool_name='Read',
            tool_input={'file_path': 'test.py'},
            tool_response={'success': True}
        )
        assert result['workflow_type'] == 'tool_chain'

        # Test Edit
        result = hook.process(
            tool_name='Edit',
            tool_input={'file_path': 'test.py'},
            tool_response={'success': True}
        )
        assert result['workflow_type'] == 'tool_chain'

        # Test Write
        result = hook.process(
            tool_name='Write',
            tool_input={'file_path': 'test.py'},
            tool_response={'success': True}
        )
        assert result['workflow_type'] == 'tool_chain'

        # Test Bash
        result = hook.process(
            tool_name='Bash',
            tool_input={'command': 'echo test'},
            tool_response={'success': True}
        )
        assert result['workflow_type'] == 'tool_chain'

    def test_error_handling(self):
        """Test that hook handles errors gracefully."""
        hook = E2ETrackerHook()

        # Test with invalid input (should not raise)
        result = hook.process(
            tool_name='Read',
            tool_input={},  # Missing file_path
            tool_response={'success': False}
        )

        # Hook should always return success (non-blocking)
        assert result['passed'] is True

    def test_environment_variable(self):
        """Test E2E_TRACKER_ENABLED environment variable."""
        import os

        # Test disabled
        os.environ['E2E_TRACKER_ENABLED'] = 'false'
        hook = E2ETrackerHook()
        assert hook.enabled is False

        # Test enabled
        os.environ['E2E_TRACKER_ENABLED'] = 'true'
        hook = E2ETrackerHook()
        assert hook.enabled is True

        # Clean up
        del os.environ['E2E_TRACKER_ENABLED']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
