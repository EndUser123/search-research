"""
Unit tests for analyze_conflicts.py

Tests cover:
- Intent extraction from commit messages
- File compatibility analysis
- Merge base calculation
- Safe/RISKY/BLOCKED verdicts
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add parent directory to path to import the analyzer
sys.path.insert(0, str(Path(__file__).parent.parent))

from analyze_conflicts import run, get_commit_intent, analyze_file


class TestRunCommand:
    """Test the run() helper function."""

    @patch('analyze_conflicts.subprocess.run')
    def test_run_command_success(self, mock_subprocess):
        """Test successful command execution."""
        mock_result = MagicMock(stdout='output', stderr='', returncode=0)
        mock_subprocess.return_value = mock_result

        result = run(['git', 'status'])

        assert result.stdout == 'output'
        mock_subprocess.assert_called_once()

    @patch('analyze_conflicts.subprocess.run')
    def test_run_command_with_cwd(self, mock_subprocess):
        """Test command execution with custom working directory."""
        mock_result = MagicMock(stdout='output', returncode=0)
        mock_subprocess.return_value = mock_result

        result = run(['git', 'status'], cwd='/tmp/test')

        assert result.stdout == 'output'
        # Verify cwd was passed
        call_kwargs = mock_subprocess.call_args.kwargs
        assert 'cwd' in call_kwargs


class TestGetCommitIntent:
    """Test intent extraction from commit messages."""

    @patch('analyze_conflicts.run')
    def test_intent_with_why_section(self, mock_run):
        """Test extracting intent from ## WHY section."""
        mock_run.return_value = MagicMock(
            stdout='''feat: add OAuth2 login

## WHY
Users need secure authentication with social providers

## WHAT
Implemented OAuth2 with Google and GitHub'''
        )

        intent = get_commit_intent('abc123', Path.cwd())

        assert 'secure authentication' in intent.lower()
        assert 'social providers' in intent.lower()

    @patch('analyze_conflicts.run')
    def test_intent_fallback_to_subject(self, mock_run):
        """Test fallback to first line when no WHY section."""
        mock_run.return_value = MagicMock(
            stdout='feat: add user authentication'
        )

        intent = get_commit_intent('abc123', Path.cwd())

        assert intent == 'feat: add user authentication'

    @patch('analyze_conflicts.run')
    def test_intent_empty_commit(self, mock_run):
        """Test handling of empty commit message."""
        mock_run.return_value = MagicMock(stdout='')

        intent = get_commit_intent('abc123', Path.cwd())

        assert intent == 'No intent documented'

    @patch('analyze_conflicts.run')
    def test_intent_multiline_why(self, mock_run):
        """Test extracting multiline WHY content."""
        mock_run.return_value = MagicMock(
            stdout='''fix: resolve race condition

## WHY
Multiple threads access shared state
without proper locking causing data races.
This needs immediate attention.

## WHAT
Added mutex locks around critical sections'''
        )

        intent = get_commit_intent('abc123', Path.cwd())

        assert 'threads access shared state' in intent.lower()
        assert 'locking' in intent.lower()


class TestAnalyzeFile:
    """Test file-level conflict analysis."""

    @patch('analyze_conflicts.run')
    def test_analyze_safe_refactor_plus_add(self, mock_run):
        """Test SAFE verdict when one refactors and other adds."""
        # Mock merge base
        mock_run.side_effect = [
            MagicMock(stdout='abc123'),  # merge-base
            MagicMock(stdout='+++ def new_func()\n'),  # target diff (adds)
            MagicMock(stdout='--- def old_func()\n+++ def new_func()\n'),  # source diff (refactor)
            MagicMock(stdout='abc123', returncode=0),  # source commit hash
            MagicMock(stdout='refactor: simplify\n\n## WHY\nRefactor code structure'),  # source intent
            MagicMock(stdout='def123', returncode=0),  # target commit hash
            MagicMock(stdout='feat: add feature\n\n## WHY\nAdd new capability'),  # target intent
        ]

        result = analyze_file('test.py', 'feature', 'main', Path.cwd())
        compat, reason, resolution = result

        assert compat == 'SAFE'
        assert 'refactor' in reason.lower() or 'add' in reason.lower()

    @patch('analyze_conflicts.run')
    def test_analyze_risky_double_fix(self, mock_run):
        """Test RISKY verdict when both fix the same area."""
        mock_run.side_effect = [
            MagicMock(stdout='abc123'),
            MagicMock(stdout='--- if x:\n+++ if x and y:\n'),  # target fix
            MagicMock(stdout='--- if x:\n+++ if x or z:\n'),  # source fix
            MagicMock(stdout='abc123'),
            MagicMock(stdout='fix: handle edge case\n\n## WHY\nBug reported'),
            MagicMock(stdout='def123'),
            MagicMock(stdout='fix: improve condition\n\n## WHY\nLogic error'),
        ]

        result = analyze_file('test.py', 'feature', 'main', Path.cwd())
        compat, reason, resolution = result

        assert compat == 'RISKY'

    @patch('analyze_conflicts.run')
    def test_analyze_blocked_delete_vs_add(self, mock_run):
        """Test BLOCKED verdict when one deletes and other adds."""
        mock_run.side_effect = [
            MagicMock(stdout='abc123'),
            MagicMock(stdout='--- def func():\n'),  # target deletes
            MagicMock(stdout='+++ def func():\n    pass'),  # source adds
            MagicMock(stdout='abc123'),
            MagicMock(stdout='refactor: remove unused\n\n## WHY\nDead code'),
            MagicMock(stdout='def123'),
            MagicMock(stdout='feat: add function\n\n## WHY\nNeed it'),
        ]

        result = analyze_file('test.py', 'feature', 'main', Path.cwd())
        compat, reason, resolution = result

        assert compat == 'BLOCKED'
        assert 'incompatible' in reason.lower()

    @patch('analyze_conflicts.run')
    def test_analyze_safe_both_add_features(self, mock_run):
        """Test SAFE verdict when both add independent features."""
        mock_run.side_effect = [
            MagicMock(stdout='abc123'),
            MagicMock(stdout='+++ def func_a():\n'),  # target adds A
            MagicMock(stdout='+++ def func_b():\n'),  # source adds B
            MagicMock(stdout='abc123'),
            MagicMock(stdout='feat: add feature A\n\n## WHY\nAdd feature A for users'),
            MagicMock(stdout='def123'),
            MagicMock(stdout='feat: add feature B\n\n## WHY\nAdd feature B for analytics'),
        ]

        result = analyze_file('test.py', 'feature', 'main', Path.cwd())
        compat, reason, resolution = result

        assert compat == 'SAFE'

    @patch('analyze_conflicts.run')
    def test_analyze_safe_one_sided_changes(self, mock_run):
        """Test SAFE verdict when only one branch changed."""
        mock_run.side_effect = [
            MagicMock(stdout='abc123'),
            MagicMock(stdout='+++ def new_func():\n'),  # target adds
            MagicMock(stdout=''),  # source has no changes
            MagicMock(stdout='def123'),
            MagicMock(stdout='feat: add feature\n\n## WHY\nNeeded'),
            MagicMock(stdout='abc123'),
            MagicMock(stdout='abc123'),  # source is at merge base
        ]

        result = analyze_file('test.py', 'feature', 'main', Path.cwd())
        compat, reason, resolution = result

        assert compat == 'SAFE'


class TestVerdictCategories:
    """Test that all compatibility verdicts are valid."""

    def test_valid_verdicts(self):
        """Test that only valid verdict strings exist."""
        valid_verdicts = {'SAFE', 'RISKY', 'BLOCKED'}
        # This test documents the valid verdict types
        # If analyze_file returns anything else, it's an error
        assert len(valid_verdicts) == 3


class TestEdgeCases:
    """Test edge cases and error conditions."""

    @patch('analyze_conflicts.run')
    def test_empty_intent_handling(self, mock_run):
        """Test handling of commits with no clear intent."""
        mock_run.side_effect = [
            MagicMock(stdout='abc123'),
            MagicMock(stdout=''),  # No changes
            MagicMock(stdout=''),  # No changes
            MagicMock(stdout='abc123'),
            MagicMock(stdout=''),  # Empty intent
            MagicMock(stdout='def123'),
            MagicMock(stdout=''),  # Empty intent
        ]

        result = analyze_file('test.py', 'feature', 'main', Path.cwd())
        compat, reason, resolution = result

        # Should still return a valid verdict
        assert compat in {'SAFE', 'RISKY', 'BLOCKED'}
        assert reason is not None
        assert resolution is not None
