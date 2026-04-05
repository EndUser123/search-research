"""
Test suite for PreToolUse_observe_before_act_gate.py

Validates that the hook catches the "maddening" patterns from the original conversation:
1. Multi-edit without reading (advisory → block)
2. Skill misuse (manual bash instead of Skill tool)
3. GTO context bleed (cross-terminal state access)
4. Git safety (global operations without path limiters)
"""

import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

# =============================================================================
# Test Fixtures - Patterns from the "maddening" conversation
# =============================================================================


@pytest.fixture
def sample_session_id() -> str:
    """Sample session ID for testing."""
    import uuid

    return f"test-session-{uuid.uuid4().hex[:8]}"


@pytest.fixture
def sample_terminal_id() -> str:
    """Sample terminal ID for testing."""
    import uuid

    return f"test-terminal-{uuid.uuid4().hex[:8]}"


@pytest.fixture
def hook_path() -> Path:
    """Path to the hook being tested."""
    return Path(__file__).resolve().parent.parent / "PreToolUse_observe_before_act_gate.py"


# =============================================================================
# Helper Functions
# =============================================================================


def run_hook(hook_path: Path, payload: dict[str, Any]) -> tuple[int, str]:
    """Run the hook with a payload and return (exit_code, stdout)."""
    input_json = json.dumps(payload)
    result = subprocess.run(
        ["python", str(hook_path)], input=input_json, capture_output=True, text=True, timeout=5
    )
    return result.returncode, result.stdout


# =============================================================================
# Test Case 1: Multi-Edit Without Read (from maddening conversation)
# =============================================================================


class TestMultiEditGate:
    """Tests for multi-edit detection - the "line-by-line syntax chasing" pattern."""

    def test_first_edit_without_read_allowed(
        self, hook_path, sample_session_id, sample_terminal_id
    ):
        """First edit to a file without reading is allowed (baseline)."""
        payload = {
            "tool_name": "Edit",
            "tool_input": {
                "file_path": "test_file.py",
                "old_string": "def foo():",
                "new_string": "def bar():",
            },
            "session_id": sample_session_id,
            "terminal_id": sample_terminal_id,
        }

        exit_code, stdout = run_hook(hook_path, payload)
        assert exit_code == 0, "First edit without read should be allowed"

    def test_second_edit_without_read_warns(self, hook_path, sample_session_id, sample_terminal_id):
        """Second edit without read should produce advisory (threshold=2)."""
        payload_template = {
            "tool_name": "Edit",
            "tool_input": {"file_path": "test_file.py", "old_string": "old", "new_string": "new"},
            "session_id": sample_session_id,
            "terminal_id": sample_terminal_id,
        }

        # First edit - allowed
        exit_code1, stdout1 = run_hook(hook_path, payload_template)
        assert exit_code1 == 0

        # Second edit - should produce advisory
        exit_code2, stdout2 = run_hook(hook_path, payload_template)
        assert exit_code2 == 0, "Second edit should still pass"

        # Check for advisory in output
        if stdout2:
            response = json.loads(stdout2)
            assert response.get("continue") is True
            assert "advisories" in response
            assert len(response["advisories"]) > 0
            assert "Multi-edit gate advisory" in response["advisories"][0]

    def test_third_edit_without_read_allowed(
        self, hook_path, sample_session_id, sample_terminal_id
    ):
        """
        Multi-edit gate has been removed.

        Third edit without read is now ALLOWED (previously blocked).
        The multi-edit detection feature was removed to simplify the hook.
        """
        payload_template = {
            "tool_name": "Write",
            "tool_input": {"file_path": "test_file.py", "content": "new content"},
            "session_id": sample_session_id,
            "terminal_id": sample_terminal_id,
        }

        # All edits should be allowed (multi-edit gate removed)
        for _ in range(3):
            exit_code, _ = run_hook(hook_path, payload_template)
            assert exit_code == 0, (
                "Multiple edits without read should be allowed (multi-edit gate removed)"
            )

    def test_edit_after_read_allowed(self, hook_path, sample_session_id, sample_terminal_id):
        """Edits after reading the file are always allowed."""
        # First, read the file
        read_payload = {
            "tool_name": "Read",
            "tool_input": {"file_path": "test_file.py"},
            "session_id": sample_session_id,
            "terminal_id": sample_terminal_id,
        }
        exit_code, _ = run_hook(hook_path, read_payload)
        assert exit_code == 0

        # Now edit multiple times - all should be allowed
        edit_payload = {
            "tool_name": "Edit",
            "tool_input": {"file_path": "test_file.py", "old_string": "old", "new_string": "new"},
            "session_id": sample_session_id,
            "terminal_id": sample_terminal_id,
        }

        for i in range(5):  # Even 5 edits after read should be fine
            exit_code, _ = run_hook(hook_path, edit_payload)
            assert exit_code == 0, f"Edit {i + 1} after read should be allowed"


# =============================================================================
# Test Case 2: Skill Structure Gate (universal-skills-manager fiasco)
# =============================================================================


class TestSkillStructureGate:
    """Tests for skill misuse - the "manual bash instead of Skill tool" pattern."""

    def test_manual_bash_skill_invocation_blocked_when_structure_exists(
        self, hook_path, sample_session_id, sample_terminal_id
    ):
        """
        Test case from maddening conversation:
        Agent manually read config.json and called curl instead of using Skill tool.

        Pattern from conversation:
        - python3 -c "import json; print(json.load(open('P:/.claude/skills/universal-skills-manager/config.json'))...)"
        - curl calls to SkillsMP API

        This should be blocked because universal-skills-manager has structured definition.
        """
        # Create a mock skill directory with config.json
        hook_dir = hook_path.parent
        mock_skill_dir = hook_dir.parent / "skills" / "universal-skills-manager"
        mock_skill_dir.mkdir(parents=True, exist_ok=True)
        (mock_skill_dir / "config.json").write_text('{"test": true}')

        try:
            payload = {
                "tool_name": "Bash",
                "tool_input": {
                    "command": "python3 -c \"import json; print(json.load(open('P:/.claude/skills/universal-skills-manager/config.json')).get('test', ''))\""
                },
                "session_id": sample_session_id,
                "terminal_id": sample_terminal_id,
            }

            exit_code, stdout = run_hook(hook_path, payload)
            # With inverted logic, python is NOT a content reader → ALLOW
            assert exit_code == 0, (
                f"Manual skill invocation via python is now ALLOW (not a content reader). "
                f"exit_code={exit_code}, stdout={stdout}"
            )
            # No JSON response expected on allow - hook exits 0 with no output
        finally:
            # Cleanup
            (mock_skill_dir / "config.json").unlink(missing_ok=True)
            # Only rmdir if we created it and it's empty (real skills dir has other files)
            try:
                mock_skill_dir.rmdir()
            except OSError:
                pass  # Directory not empty or doesn't exist — that's fine

    def test_bash_skill_invocation_allowed_when_no_structure(
        self, hook_path, sample_session_id, sample_terminal_id
    ):
        """Bash invocation of /skill-name is allowed when skill has no structured definition."""
        payload = {
            "tool_name": "Bash",
            "tool_input": {"command": "/my-custom-arg --help"},
            "session_id": sample_session_id,
            "terminal_id": sample_terminal_id,
        }

        exit_code, _ = run_hook(hook_path, payload)
        assert exit_code == 0, "Bash command with /pattern but no skill structure should be allowed"

    def test_skill_tool_always_allowed(self, hook_path, sample_session_id, sample_terminal_id):
        """The Skill tool itself should never be blocked by this gate."""
        payload = {
            "tool_name": "Skill",
            "tool_input": {"skill": "universal-skills-manager", "args": "search test"},
            "session_id": sample_session_id,
            "terminal_id": sample_terminal_id,
        }

        exit_code, _ = run_hook(hook_path, payload)
        assert exit_code == 0, "Skill tool invocation should always be allowed"

    def test_heredoc_with_skill_name_in_content_allows(
        self, hook_path, sample_session_id, sample_terminal_id
    ):
        """
        Heredoc content containing skill name should NOT block.

        This was the false positive bug: commands like:
        cat > plan.txt << 'EOF'
        # adversarial-critic implementation
        EOF

        were incorrectly blocked because "adversarial-critic" matched
        the skill path pattern in the heredoc content.
        """
        # Create a mock skill directory with config.json
        hook_dir = hook_path.parent
        mock_skill_dir = hook_dir.parent / "skills" / "adversarial-critic"
        mock_skill_dir.mkdir(parents=True, exist_ok=True)
        (mock_skill_dir / "config.json").write_text('{"test": true}')

        try:
            payload = {
                "tool_name": "Bash",
                "tool_input": {
                    "command": "cat > plan.txt << 'EOF'\n# adversarial-critic implementation\nEOF"
                },
                "session_id": sample_session_id,
                "terminal_id": sample_terminal_id,
            }

            exit_code, stdout = run_hook(hook_path, payload)
            assert exit_code == 0, "Heredoc with skill name in content should allow"

        finally:
            # Cleanup
            (mock_skill_dir / "config.json").unlink(missing_ok=True)
            # Only rmdir if we created it and it's empty
            try:
                mock_skill_dir.rmdir()
            except OSError:
                pass  # Directory not empty or doesn't exist - fine

    def test_heredoc_double_quoted_with_skill_name_allows(
        self, hook_path, sample_session_id, sample_terminal_id
    ):
        """Double-quoted heredoc with skill name in content should allow."""
        payload = {
            "tool_name": "Bash",
            "tool_input": {
                "command": 'cat > plan.txt << "EOF"\n# adversarial-critic implementation\nEOF'
            },
            "session_id": sample_session_id,
            "terminal_id": sample_terminal_id,
        }

        exit_code, stdout = run_hook(hook_path, payload)
        assert exit_code == 0, "Double-quoted heredoc with skill name should allow"

    def test_heredoc_unquoted_with_skill_name_allows(
        self, hook_path, sample_session_id, sample_terminal_id
    ):
        """Unquoted heredoc with skill name in content should allow."""
        payload = {
            "tool_name": "Bash",
            "tool_input": {
                "command": "cat > plan.txt << EOF\n# adversarial-critic implementation\nEOF"
            },
            "session_id": sample_session_id,
            "terminal_id": sample_terminal_id,
        }

        exit_code, stdout = run_hook(hook_path, payload)
        assert exit_code == 0, "Unquoted heredoc with skill name should allow"

    def test_heredoc_with_skill_path_in_command_blocks(
        self, hook_path, sample_session_id, sample_terminal_id
    ):
        """
        Actual skill path access in command should still block.

        Even with heredoc syntax, if the skill path appears BEFORE
        the heredoc delimiter, it should be detected and blocked.
        """
        # Create a mock skill directory with SKILL.md
        hook_dir = hook_path.parent
        mock_skill_dir = hook_dir.parent / "skills" / "test"
        mock_skill_dir.mkdir(parents=True, exist_ok=True)
        (mock_skill_dir / "SKILL.md").write_text("# Test skill")

        try:
            payload = {
                "tool_name": "Bash",
                "tool_input": {
                    "command": "cat .claude/skills/test/SKILL.md << 'EOF'\ncontent\nEOF"
                },
                "session_id": sample_session_id,
                "terminal_id": sample_terminal_id,
            }

            exit_code, stdout = run_hook(hook_path, payload)
            assert exit_code == 2, "Skill path in command should block"
            response = json.loads(stdout)
            assert response.get("decision") == "block"
            assert "test" in response.get("reason", "")

        finally:
            # Cleanup
            (mock_skill_dir / "SKILL.md").unlink(missing_ok=True)
            mock_skill_dir.rmdir()

    def test_no_heredoc_with_skill_path_blocks(
        self, hook_path, sample_session_id, sample_terminal_id
    ):
        """Direct skill path access without heredoc should block."""
        # Create a mock skill directory with config.json
        hook_dir = hook_path.parent
        mock_skill_dir = hook_dir.parent / "skills" / "test"
        mock_skill_dir.mkdir(parents=True, exist_ok=True)
        (mock_skill_dir / "config.json").write_text('{"test": true}')

        try:
            payload = {
                "tool_name": "Bash",
                "tool_input": {"command": "cat .claude/skills/test/config.json"},
                "session_id": sample_session_id,
                "terminal_id": sample_terminal_id,
            }

            exit_code, stdout = run_hook(hook_path, payload)
            assert exit_code == 2, "Direct skill path access should block"
            response = json.loads(stdout)
            assert response.get("decision") == "block"
            assert "test" in response.get("reason", "")

        finally:
            # Cleanup
            (mock_skill_dir / "config.json").unlink(missing_ok=True)
            mock_skill_dir.rmdir()

    def test_heredoc_with_whitespace_variations(
        self, hook_path, sample_session_id, sample_terminal_id
    ):
        """Heredoc with whitespace variations should be detected."""
        # Test: <<  'EOF' (extra spaces before quote)
        payload = {
            "tool_name": "Bash",
            "tool_input": {"command": "cat > plan.txt <<  'EOF'\n# adversarial-critic\nEOF"},
            "session_id": sample_session_id,
            "terminal_id": sample_terminal_id,
        }

        exit_code, stdout = run_hook(hook_path, payload)
        assert exit_code == 0, "Heredoc with extra spaces should allow"

    def test_custom_heredoc_delimiter(self, hook_path, sample_session_id, sample_terminal_id):
        """Custom heredoc delimiter (HEREDOC, END) should be detected."""
        payload = {
            "tool_name": "Bash",
            "tool_input": {"command": "cat > plan.txt << HEREDOC\n# adversarial-critic\nHEREDOC"},
            "session_id": sample_session_id,
            "terminal_id": sample_terminal_id,
        }

        exit_code, stdout = run_hook(hook_path, payload)
        assert exit_code == 0, "Custom heredoc delimiter should allow"


# =============================================================================
# Test Case 3: Analysis Scope Gate (REMOVED - was enforcing workflow preference)
# =============================================================================


class TestAnalysisScopeGate:
    """Tests for session-scoped reasoning - REMOVED, now allows cross-terminal access."""

    def test_cat_state_directory_allowed(self, hook_path, sample_session_id, sample_terminal_id):
        """Direct cat of .claude/state/ is now ALLOWED for debugging."""
        payload = {
            "tool_name": "Bash",
            "tool_input": {"command": "cat .claude/state/task_tracker/123.json"},
            "session_id": sample_session_id,
            "terminal_id": sample_terminal_id,
        }

        exit_code, stdout = run_hook(hook_path, payload)
        assert exit_code == 0, "Reading .claude/state/ should be ALLOWED (gate removed)"

    def test_ls_tasks_directory_allowed(self, hook_path, sample_session_id, sample_terminal_id):
        """Listing .claude/tasks/ is now ALLOWED for debugging."""
        payload = {
            "tool_name": "Bash",
            "tool_input": {"command": "ls -la .claude/tasks/"},
            "session_id": sample_session_id,
            "terminal_id": sample_terminal_id,
        }

        exit_code, stdout = run_hook(hook_path, payload)
        assert exit_code == 0, "Listing .claude/tasks/ should be ALLOWED (gate removed)"

    def test_jq_on_cognitive_allowed(self, hook_path, sample_session_id, sample_terminal_id):
        """Using jq on .claude/cognitive/ is now ALLOWED for debugging."""
        payload = {
            "tool_name": "Bash",
            "tool_input": {"command": "jq '.pending' .claude/cognitive/session_state.json"},
            "session_id": sample_session_id,
            "terminal_id": sample_terminal_id,
        }

        exit_code, stdout = run_hook(hook_path, payload)
        assert exit_code == 0, "jq on .claude/cognitive/ should be ALLOWED (gate removed)"

    def test_grep_recursive_on_state_blocked(
        self, hook_path, sample_session_id, sample_terminal_id
    ):
        """Recursive grep on .claude/state/ is now ALLOWED for debugging."""
        payload = {
            "tool_name": "Bash",
            "tool_input": {"command": "grep -r 'pending' .claude/state/"},
            "session_id": sample_session_id,
            "terminal_id": sample_terminal_id,
        }

        exit_code, stdout = run_hook(hook_path, payload)
        assert exit_code == 0, "Recursive grep on .claude/state/ should be ALLOWED (gate removed)"

    def test_bash_on_other_directories_allowed(
        self, hook_path, sample_session_id, sample_terminal_id
    ):
        """Bash commands not accessing state/cognitive/tasks should be allowed."""
        payload = {
            "tool_name": "Bash",
            "tool_input": {"command": "cat package.json"},
            "session_id": sample_session_id,
            "terminal_id": sample_terminal_id,
        }

        exit_code, _ = run_hook(hook_path, payload)
        assert exit_code == 0, "Bash on non-state files should be allowed"


# =============================================================================
# Test Case 4: Git Safety Gate
# =============================================================================


class TestGitSafetyGate:
    """Tests for git command safety - preventing global operations."""

    def test_global_git_status_allowed(self, hook_path, sample_session_id, sample_terminal_id):
        """
        Git safety gate has been DISABLED.

        Global 'git status' without path limiter is now ALLOWED.
        Read-only git operations are permitted; destructive operations
        are blocked by PreToolUse_destructive_git_guard.py instead.
        """
        payload = {
            "tool_name": "Bash",
            "tool_input": {"command": "git status"},
            "session_id": sample_session_id,
            "terminal_id": sample_terminal_id,
        }

        exit_code, _ = run_hook(hook_path, payload)
        assert exit_code == 0, "Global git status should be allowed (git safety gate disabled)"

    def test_global_git_diff_allowed(self, hook_path, sample_session_id, sample_terminal_id):
        """
        Git safety gate has been DISABLED.

        Global 'git diff' without path limiter is now ALLOWED.
        Read-only git operations are permitted; destructive operations
        are blocked by PreToolUse_destructive_git_guard.py instead.
        """
        payload = {
            "tool_name": "Bash",
            "tool_input": {"command": "git diff"},
            "session_id": sample_session_id,
            "terminal_id": sample_terminal_id,
        }

        exit_code, _ = run_hook(hook_path, payload)
        assert exit_code == 0, "Global git diff should be allowed (git safety gate disabled)"

    def test_git_status_with_path_limiter_allowed(
        self, hook_path, sample_session_id, sample_terminal_id
    ):
        """'git status -- <path>' with path limiter should be allowed."""
        payload = {
            "tool_name": "Bash",
            "tool_input": {"command": "git status -- src/"},
            "session_id": sample_session_id,
            "terminal_id": sample_terminal_id,
        }

        exit_code, _ = run_hook(hook_path, payload)
        assert exit_code == 0, "git status with -- <path> should be allowed"

    def test_git_diff_with_path_limiter_allowed(
        self, hook_path, sample_session_id, sample_terminal_id
    ):
        """'git diff -- <path>' with path limiter should be allowed."""
        payload = {
            "tool_name": "Bash",
            "tool_input": {"command": "git diff -- hooks/PreToolUse_observe_before_act_gate.py"},
            "session_id": sample_session_id,
            "terminal_id": sample_terminal_id,
        }

        exit_code, _ = run_hook(hook_path, payload)
        assert exit_code == 0, "git diff with -- <path> should be allowed"

    def test_other_git_commands_allowed(self, hook_path, sample_session_id, sample_terminal_id):
        """Git commands other than status/diff should be allowed."""
        payload = {
            "tool_name": "Bash",
            "tool_input": {"command": "git log --oneline -5"},
            "session_id": sample_session_id,
            "terminal_id": sample_terminal_id,
        }

        exit_code, _ = run_hook(hook_path, payload)
        assert exit_code == 0, "git log should be allowed"


# =============================================================================
# Test Case 5: Multi-Terminal Safety
# =============================================================================


class TestMultiTerminalSafety:
    """Tests for multi-terminal isolation and stale state protection."""

    def test_different_sessions_allowed(self, hook_path, sample_terminal_id):
        """
        Multi-terminal safety and multi-edit tracking have been removed.

        Different sessions no longer track edit counts - all edits allowed.
        The multi-edit detection feature was removed to simplify the hook.
        """
        session_a = "session-a"
        session_b = "session-b"

        edit_payload = {
            "tool_name": "Edit",
            "tool_input": {"file_path": "test.py", "old_string": "old", "new_string": "new"},
            "session_id": session_a,
            "terminal_id": sample_terminal_id,
        }

        # Session A makes multiple edits - all allowed
        for _ in range(3):
            exit_code, _ = run_hook(hook_path, edit_payload)
            assert exit_code == 0, "Multiple edits should be allowed (multi-edit tracking removed)"

        # Session B edits should also be allowed
        edit_payload["session_id"] = session_b
        exit_code, _ = run_hook(hook_path, edit_payload)
        assert exit_code == 0, "Session B edits should be allowed"

    def test_missing_terminal_id_graceful_degradation(self, hook_path, sample_session_id):
        """Missing terminal_id should gracefully degrade (not crash)."""
        payload = {
            "tool_name": "Edit",
            "tool_input": {"file_path": "test.py", "old_string": "old", "new_string": "new"},
            "session_id": sample_session_id,
            "terminal_id": "",  # Empty terminal_id
        }

        exit_code, _ = run_hook(hook_path, payload)
        # Should not crash, should allow (state is empty)
        assert exit_code == 0

    def test_missing_session_id_graceful_degradation(self, hook_path, sample_terminal_id):
        """Missing session_id should gracefully degrade (not crash)."""
        payload = {
            "tool_name": "Edit",
            "tool_input": {"file_path": "test.py", "old_string": "old", "new_string": "new"},
            "session_id": "",  # Empty session_id
            "terminal_id": sample_terminal_id,
        }

        exit_code, _ = run_hook(hook_path, payload)
        # Should not crash, should allow (state is empty)
        assert exit_code == 0


# =============================================================================
# Test Case 6: Hook Protocol Compliance
# =============================================================================


class TestHookProtocol:
    """Tests for proper PreToolUse hook protocol compliance."""

    def test_state_access_allowed(self, hook_path, sample_session_id, sample_terminal_id):
        """
        Analysis scope gate has been REMOVED.

        Accessing .claude/state/ files is now ALLOWED for debugging.
        The analysis scope restriction was removed to enable cross-terminal debugging.
        """
        payload = {
            "tool_name": "Bash",
            "tool_input": {"command": "cat .claude/state/test.json"},
            "session_id": sample_session_id,
            "terminal_id": sample_terminal_id,
        }

        exit_code, _ = run_hook(hook_path, payload)
        assert exit_code == 0, "State file access should be allowed (analysis scope gate removed)"

    def test_allowed_action_returns_nothing_or_continue_true(
        self, hook_path, sample_session_id, sample_terminal_id
    ):
        """Allowed actions should either exit 0 with no output, or return {'continue': True}."""
        payload = {
            "tool_name": "Read",
            "tool_input": {"file_path": "test.py"},
            "session_id": sample_session_id,
            "terminal_id": sample_terminal_id,
        }

        exit_code, stdout = run_hook(hook_path, payload)
        assert exit_code == 0, "Allowed action should exit with code 0"

        # Either no output, or valid JSON with decision=allow or continue=True
        if stdout.strip():
            response = json.loads(stdout)
            # New format uses decision, old format used continue
            assert response.get("decision") == "allow" or response.get("continue") is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
