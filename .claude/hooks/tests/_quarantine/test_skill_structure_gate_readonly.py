"""
Test for Pattern 2: Content-reader gate for skill file access.

Verifies the inverted-logic gate that blocks direct content-reading commands
cat, grep, head, tail, etc.) from accessing skill files via Bash, while
allowing programmatic access (python, node, wc, stat, etc.).

Content readers should be BLOCKED (use Read/Grep tools instead).
Programmatic/metadata commands should be ALLOWED.

Uses forward-slash paths to command strings to match bash usage on Windows.
"""

import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

# =============================================================================
# Test Fixtures
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


@pytest.fixture
def mock_skill_with_structure(hook_path: Path):
    """
    Create a mock skill directory with SKILL.md for testing.
    This simulates a real skill that exists in the codebase.
    """
    hook_dir = hook_path.parent
    mock_skill_dir = hook_dir.parent / "skills" / "test-refactor-skill"
    mock_skill_dir.mkdir(parents=True, exist_ok=True)

    skill_md_content = """# Test Refactor Skill

## Purpose
Test skill for verifying content-reader gate behavior.

## Usage
This is a test skill.
"""
    (mock_skill_dir / "SKILL.md").write_text(skill_md_content)

    yield mock_skill_dir

    # Cleanup
    (mock_skill_dir / "SKILL.md").unlink(missing_ok=True)
    try:
        mock_skill_dir.rmdir()
    except OSError:
        pass  # Directory not empty or doesn't exist -- that's fine


# Forward-slash relative path used in bash commands (matching the hook's regex).
SKILL_FWD_PATH = ".claude/skills/test-refactor-skill/SKILL.md"


# =============================================================================
# Test Cases: Content Reader Gate
# =============================================================================


class TestSkillStructureGateContentReaders:
    """
    Content-reading commands are BLOCKED — they output file content to the terminal.
    The hook redirects to Read/Grep tools instead.
    """

    def test_head_command_blocked(
        self, hook_path, mock_skill_with_structure, sample_session_id, sample_terminal_id
    ):
        """head is a content reader — BLOCKED, use Read tool instead."""
        payload = {
            "tool_name": "Bash",
            "tool_input": {"command": f"head -150 {SKILL_FWD_PATH}"},
            "session_id": sample_session_id,
            "terminal_id": sample_terminal_id,
        }

        exit_code, stdout = run_hook(hook_path, payload)
        assert exit_code == 2, (
            f"head command should be BLOCKED (content reader). "
            f"exit_code={exit_code}, stdout={stdout}"
        )
        response = json.loads(stdout)
        assert response.get("decision") == "block"
        assert "Skill structure gate" in response.get("reason", "")

    def test_cat_command_blocked(
        self, hook_path, mock_skill_with_structure, sample_session_id, sample_terminal_id
    ):
        """cat is a content reader — BLOCKED, use Read tool instead."""
        payload = {
            "tool_name": "Bash",
            "tool_input": {"command": f"cat {SKILL_FWD_PATH}"},
            "session_id": sample_session_id,
            "terminal_id": sample_terminal_id,
        }

        exit_code, stdout = run_hook(hook_path, payload)
        assert exit_code == 2, (
            f"cat command should be BLOCKED (content reader). "
            f"exit_code={exit_code}, stdout={stdout}"
        )
        response = json.loads(stdout)
        assert response.get("decision") == "block"
        assert "Skill structure gate" in response.get("reason", "")

    def test_grep_command_blocked(
        self, hook_path, mock_skill_with_structure, sample_session_id, sample_terminal_id
    ):
        """grep is a content searcher — BLOCKED, use Grep tool instead."""
        payload = {
            "tool_name": "Bash",
            "tool_input": {"command": f"grep 'Purpose' {SKILL_FWD_PATH}"},
            "session_id": sample_session_id,
            "terminal_id": sample_terminal_id,
        }

        exit_code, stdout = run_hook(hook_path, payload)
        assert exit_code == 2, (
            f"grep command should be BLOCKED (content reader). "
            f"exit_code={exit_code}, stdout={stdout}"
        )
        response = json.loads(stdout)
        assert response["decision"] == "block"

    def test_tail_command_blocked(
        self, hook_path, mock_skill_with_structure, sample_session_id, sample_terminal_id
    ):
        """tail is a content reader — BLOCKED."""
        payload = {
            "tool_name": "Bash",
            "tool_input": {"command": f"tail -20 {SKILL_FWD_PATH}"},
            "session_id": sample_session_id,
            "terminal_id": sample_terminal_id,
        }

        exit_code, stdout = run_hook(hook_path, payload)
        assert exit_code == 2, (
            f"tail command should be BLOCKED (content reader). "
            f"exit_code={exit_code}, stdout={stdout}"
        )

    def test_less_command_blocked(
        self, hook_path, mock_skill_with_structure, sample_session_id, sample_terminal_id
    ):
        """less is a content reader — BLOCKED."""
        payload = {
            "tool_name": "Bash",
            "tool_input": {"command": f"less {SKILL_FWD_PATH}"},
            "session_id": sample_session_id,
            "terminal_id": sample_terminal_id,
        }

        exit_code, stdout = run_hook(hook_path, payload)
        assert exit_code == 2, (
            f"less command should be BLOCKED (content reader). "
            f"exit_code={exit_code}, stdout={stdout}"
        )

    def test_rg_command_blocked(
        self, hook_path, mock_skill_with_structure, sample_session_id, sample_terminal_id
    ):
        """rg (ripgrep) is a content searcher — BLOCKED."""
        payload = {
            "tool_name": "Bash",
            "tool_input": {"command": f"rg 'Purpose' {SKILL_FWD_PATH}"},
            "session_id": sample_session_id,
            "terminal_id": sample_terminal_id,
        }

        exit_code, stdout = run_hook(hook_path, payload)
        assert exit_code == 2, (
            f"rg command should be BLOCKED (content reader). exit_code={exit_code}, stdout={stdout}"
        )


class TestSkillStructureGateProgrammaticAccess:
    """
    Programmatic/metadata commands are ALLOWED — they don't output file content directly.
    """

    def test_wc_command_allowed(
        self, hook_path, mock_skill_with_structure, sample_session_id, sample_terminal_id
    ):
        """wc is metadata-only (line count) — ALLOWED."""
        payload = {
            "tool_name": "Bash",
            "tool_input": {"command": f"wc -l {SKILL_FWD_PATH}"},
            "session_id": sample_session_id,
            "terminal_id": sample_terminal_id,
        }

        exit_code, _ = run_hook(hook_path, payload)
        assert exit_code == 0, (
            f"wc command should be ALLOWED (metadata only). exit_code={exit_code}"
        )

    def test_stat_command_allowed(
        self, hook_path, mock_skill_with_structure, sample_session_id, sample_terminal_id
    ):
        """stat is metadata-only (file info) — ALLOWED."""
        payload = {
            "tool_name": "Bash",
            "tool_input": {"command": f"stat {SKILL_FWD_PATH}"},
            "session_id": sample_session_id,
            "terminal_id": sample_terminal_id,
        }

        exit_code, _ = run_hook(hook_path, payload)
        assert exit_code == 0, (
            f"stat command should be ALLOWED (metadata only). exit_code={exit_code}"
        )

    def test_python_command_allowed(
        self, hook_path, mock_skill_with_structure, sample_session_id, sample_terminal_id
    ):
        """python is programmatic access — ALLOWED (not a content reader)."""
        payload = {
            "tool_name": "Bash",
            "tool_input": {"command": f"python {SKILL_FWD_PATH}"},
            "session_id": sample_session_id,
            "terminal_id": sample_terminal_id,
        }

        exit_code, _ = run_hook(hook_path, payload)
        assert exit_code == 0, (
            f"python command should be ALLOWED (not a content reader). exit_code={exit_code}"
        )

    def test_diff_command_allowed(
        self, hook_path, mock_skill_with_structure, sample_session_id, sample_terminal_id
    ):
        """diff is file comparison, not direct content reading — ALLOWED."""
        payload = {
            "tool_name": "Bash",
            "tool_input": {"command": f"diff {SKILL_FWD_PATH} /dev/null"},
            "session_id": sample_session_id,
            "terminal_id": sample_terminal_id,
        }

        exit_code, _ = run_hook(hook_path, payload)
        assert exit_code == 0, (
            f"diff command should be ALLOWED (not a content reader). exit_code={exit_code}"
        )

    def test_file_command_allowed(
        self, hook_path, mock_skill_with_structure, sample_session_id, sample_terminal_id
    ):
        """file is metadata-only (file type detection) — ALLOWED."""
        payload = {
            "tool_name": "Bash",
            "tool_input": {"command": f"file {SKILL_FWD_PATH}"},
            "session_id": sample_session_id,
            "terminal_id": sample_terminal_id,
        }

        exit_code, _ = run_hook(hook_path, payload)
        assert exit_code == 0, (
            f"file command should be ALLOWED (metadata only). exit_code={exit_code}"
        )


class TestSkillStructureGateUrlExemption:
    """
    URL context exemption: curl/wget fetching SKILL.md from a remote URL
    must NOT be blocked — the skill name appears in the URL, not as local invocation.
    """

    def test_curl_remote_skill_url_allowed(self, hook_path, sample_session_id, sample_terminal_id):
        """
        curl fetching .claude/skills/*/SKILL.md from GitHub must not be blocked.
        Reproduces the exact failure from the universal-skills-manager workflow.
        """
        payload = {
            "tool_name": "Bash",
            "tool_input": {
                "command": (
                    'curl -s "https://raw.githubusercontent.com/mindfold-ai/Trellis/main'
                    '/.claude/skills/trellis-meta/SKILL.md" '
                    '-H "User-Agent: Universal-Skills-Manager" -o /tmp/skill.md'
                )
            },
            "session_id": sample_session_id,
            "terminal_id": sample_terminal_id,
        }

        exit_code, _ = run_hook(hook_path, payload)
        assert exit_code == 0, (
            f"curl of remote skill URL should NOT be blocked. exit_code={exit_code}"
        )

    def test_wget_remote_skill_url_allowed(self, hook_path, sample_session_id, sample_terminal_id):
        """wget variant of the same pattern must also pass."""
        payload = {
            "tool_name": "Bash",
            "tool_input": {
                "command": (
                    "wget -q https://raw.githubusercontent.com/org/repo/main"
                    "/.claude/skills/some-skill/SKILL.md -O /tmp/skill.md"
                )
            },
            "session_id": sample_session_id,
            "terminal_id": sample_terminal_id,
        }

        exit_code, _ = run_hook(hook_path, payload)
        assert exit_code == 0, (
            f"wget of remote skill URL should NOT be blocked. exit_code={exit_code}"
        )


class TestSkillStructureGateSlashCommand:
    """
    Slash command pattern: /skill-name should be blocked when skill has structure.
    """

    def test_slash_command_still_blocked(
        self, hook_path, mock_skill_with_structure, sample_session_id, sample_terminal_id
    ):
        """Pattern 1 (/skill-name) is separate from Pattern 2 (content reader gate)."""
        payload = {
            "tool_name": "Bash",
            "tool_input": {"command": "/test-refactor-skill"},
            "session_id": sample_session_id,
            "terminal_id": sample_terminal_id,
        }

        exit_code, stdout = run_hook(hook_path, payload)
        assert exit_code == 2, f"Slash command should be blocked. Got exit code {exit_code}"
        response = json.loads(stdout)
        assert response.get("decision") == "block"
        assert "Skill structure gate" in response.get("reason", "")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
