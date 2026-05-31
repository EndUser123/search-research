"""Tests for skill_enforcer.py module."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_hooks_dir = Path(__file__).resolve().parent.parent.parent
if str(_hooks_dir) not in sys.path:
    sys.path.insert(0, str(_hooks_dir))


def test_skill_enforcer_module_exists():
    from UserPromptSubmit import skill_enforcer

    assert skill_enforcer is not None


class TestSlashCommandDetection:
    def test_detect_command_directive_positive(self):
        from UserPromptSubmit.skill_enforcer import is_command_directive

        assert is_command_directive("/analyze") is True

    def test_extract_command_name(self):
        from UserPromptSubmit.skill_enforcer import extract_command_name

        assert extract_command_name("/analyze file.py") == "analyze"


class TestCommandBlocking:
    def test_should_block_command_allowlist_mode(self):
        from unittest.mock import patch

        from UserPromptSubmit.skill_enforcer import should_block_command

        mock_config = {
            "mode": "allowlist",
            "ignored_commands": ["help"],
            "enforced_skills": ["test"],
        }
        with patch(
            "skill_guard.skill_enforcer._load_enforcement_config", return_value=mock_config
        ):
            assert should_block_command("test") is False


class TestCommandContextBuilding:
    def test_build_command_context_injects_execution_instruction(self):
        from UserPromptSubmit.skill_enforcer import build_command_context

        result = build_command_context("search", "query", context=None)
        assert "INSTRUCTION: Execute skill" in result
        assert "Skill(" in result or 'Skill("' in result


class TestHealthReportPaths:
    def test_health_report_paths_custom_override(self):
        import os

        from UserPromptSubmit.skill_enforcer import _health_report_paths

        os.environ["HOOK_HEALTH_REPORT_PATH"] = "/custom/path.json"
        try:
            result = _health_report_paths()
            assert len(result) == 1
        finally:
            os.environ.pop("HOOK_HEALTH_REPORT_PATH", None)


class TestBuildMainHealthContext:
    def test_build_main_health_context_no_report(self):
        from unittest.mock import patch

        from UserPromptSubmit.skill_enforcer import build_main_health_context

        with patch("UserPromptSubmit.skill_enforcer._health_report_paths", return_value=[]):
            result = build_main_health_context()
            assert "No startup health report found yet" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
