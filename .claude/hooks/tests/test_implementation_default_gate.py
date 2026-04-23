#!/usr/bin/env python3
"""Tests for PreToolUse_implementation_default_gate."""

import json
import pytest
import subprocess
import sys
from pathlib import Path

HOOK = Path(__file__).parent.parent / "PreToolUse_implementation_default_gate.py"


def run_gate(prompt: str, tool_name: str = "Edit") -> tuple[int, str, str]:
    """Run gate with prompt, return (exit_code, stdout, stderr)."""
    input_data = {
        "tool_name": tool_name,
        "terminal_id": "test_terminal",
        "session_id": "test_session",
        "messages": [{"role": "user", "content": prompt}],
        "last_prompt": prompt,
    }
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(input_data),
        capture_output=True,
        text=True,
    )
    return proc.returncode, proc.stdout, proc.stderr


class TestImplementationTriggerDetection:
    """Test trigger word detection."""

    TRIGGERS = [
        ("implement the fix", True),
        ("build the script", True),
        ("create a handler", True),
        ("add the feature", True),
        ("develop a solution", True),
        ("fix the bug", True),
        ("refactor the code", True),
        ("update the config", True),
        ("modify the layout", True),
        ("write a test", True),
        ("make a change", True),
        ("generate a report", True),
        ("setup the environment", True),
        ("configure the server", True),
        ("install the package", True),
        ("deploy to prod", True),
    ]

    NON_TRIGGERS = [
        ("can you document the approach?", False),
        ("what is this file doing?", False),
        ("investigate the issue", False),
        ("Explain the architecture", False),
        ("how does this work?", False),
        ("why is it failing?", False),
    ]

    @pytest.mark.parametrize("prompt,expected", TRIGGERS)
    def test_triggers_allow(self, prompt, expected):
        code, stdout, stderr = run_gate(prompt)
        assert code == 0, f"Trigger '{prompt}' should allow, got stderr: {stderr}"

    @pytest.mark.parametrize("prompt,expected", NON_TRIGGERS)
    def test_non_triggers_block(self, prompt, expected):
        code, stdout, stderr = run_gate(prompt)
        assert code == 2, f"Non-trigger '{prompt}' should block, got exit: {code}"
        assert "IMPLEMENTATION BLOCKED" in stderr


class TestToolFiltering:
    def test_bash_passes_through(self):
        """Bash tool should not be checked by this gate."""
        code, _, _ = run_gate("implement the fix", tool_name="Bash")
        assert code == 0

    def test_read_passes_through(self):
        """Read tool should not be checked."""
        code, _, _ = run_gate("implement the fix", tool_name="Read")
        assert code == 0


class TestBlockMessage:
    def test_block_message_contains_triggers(self):
        """Block message should list allowed triggers."""
        _, _, stderr = run_gate("can you document the approach?")
        assert "implement" in stderr.lower()
        assert "build" in stderr.lower()
        assert "create" in stderr.lower()
