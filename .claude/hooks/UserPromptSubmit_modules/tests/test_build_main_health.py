"""Test for build_main_health_context() function.

RED PHASE: This test is intentionally failing to verify TDD workflow.
"""

import sys
from pathlib import Path

_hooks_dir = Path(__file__).resolve().parent.parent.parent
if str(_hooks_dir) not in sys.path:
    sys.path.insert(0, str(_hooks_dir))

from unittest.mock import patch

import pytest


class TestCommandContextBuilding:
    """Tests for command context building."""

    def test_build_main_health_context_no_report(self):
        """Test build_main_health_context when no health report exists.

        Given: No hook health report file exists in any checked path
        When: build_main_health_context() is called
        Then: Returns message about missing report with checked paths

        This test verifies that when _health_report_paths() returns an empty
        list or none of the paths exist, the function provides helpful
        feedback about where it looked for the health report.
        """
        from UserPromptSubmit.skill_enforcer import (
            FALLBACK_HOOK_HEALTH_REPORT,
            HOOK_HEALTH_REPORT,
            build_main_health_context,
        )

        # Mock _health_report_paths to return empty list
        with patch(
            "UserPromptSubmit.skill_enforcer._health_report_paths",
            return_value=[]
        ):
            result = build_main_health_context()

            # Should mention no report found
            assert "No startup health report found yet" in result

            # Should include both checked paths
            assert str(HOOK_HEALTH_REPORT) in result
            assert str(FALLBACK_HOOK_HEALTH_REPORT) in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
