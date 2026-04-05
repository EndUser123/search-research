"""Characterization test for HIGH-001: run_parallel_llm complexity reduction.

This test captures the current behavior of run_parallel_llm before refactoring.
Run with: pytest P:/.claude/skills/ai-cli/tests/test_high_001_run_parallel_llm_characterization.py -v

RED PHASE: This test documents current behavior before refactoring.
GREEN PHASE: After refactoring, this test should still pass.
"""

import os

# Add parent directory to path for imports
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_cli import run_parallel_llm


class TestHigh001RunParallelLlmCharacterization:
    """Characterization tests for run_parallel_llm function (complexity 37)."""

    @pytest.fixture
    def mock_parallel_commands(self):
        """Mock run_parallel_commands from parallel_llm module."""
        with patch("ai_cli.run_parallel_commands", new_callable=AsyncMock) as mock:
            yield mock

    @pytest.fixture
    def mock_parallel_glm(self):
        """Mock run_parallel_glm from parallel_llm module."""
        with patch("ai_cli.run_parallel_glm", new_callable=AsyncMock) as mock:
            yield mock

    def test_glm_flash_only_mode_returns_glm_results(self, mock_parallel_glm):
        """
        Test that --glm-flash-only flag runs only GLM API.

        Given: glm_flash_only=True, other flags=False
        When: run_parallel_llm is called
        Then: Should call run_parallel_glm with GLM query
              And: Should return formatted results
        """
        # Arrange
        query = "test query"
        mock_parallel_glm.return_value = {
            "glm-4.7-flash": {"output": "GLM response"}  # No error field = success
        }

        # Act
        with patch("ai_cli.get_glm_api_key", return_value="test-key"):
            results = run_parallel_llm(query, glm_flash_only=True)

        # Assert - Characterize current behavior
        assert "glm-4.7-flash" in results
        assert results["glm-4.7-flash"]["output"] == "GLM response"
        assert results["glm-4.7-flash"].get("error") is None

    def test_default_mode_runs_all_clis(self, mock_parallel_commands):
        """
        Test that default mode (no flags) runs all CLI tools.

        Given: No specific CLI flags set
        When: run_parallel_llm is called
        Then: Should queue all 5 CLI commands (qwen, gemini, codex, vibe, opencode)
        """
        # Arrange
        query = "test query"
        mock_parallel_commands.return_value = {
            "qwen": {"output": "Qwen response", "error": None},
            "gemini": {"output": "Gemini response", "error": None},
            "codex": {"output": "Codex response", "error": None},
            "vibe": {"output": "Vibe response", "error": None},
            "opencode": {"output": "OpenCode response", "error": None},
        }

        # Act
        results = run_parallel_llm(query)

        # Assert - Characterize current behavior
        mock_parallel_commands.assert_called_once()
        assert len(results) == 5  # All 5 CLIs
        assert "qwen" in results
        assert "gemini" in results
        assert "codex" in results
        assert "vibe" in results
        assert "opencode" in results

    def test_qwen_only_flag_runs_single_cli(self, mock_parallel_commands):
        """
        Test that --qwen-only flag runs only qwen CLI.

        Given: qwen_only=True, other flags=False
        When: run_parallel_llm is called
        Then: Should queue only qwen command
        """
        # Arrange
        query = "test query"
        mock_parallel_commands.return_value = {
            "qwen": {"output": "Qwen response", "error": None},
        }

        # Act
        results = run_parallel_llm(query, qwen_only=True)

        # Assert
        assert len(results) == 1
        assert "qwen" in results
        assert results["qwen"]["output"] == "Qwen response"

    def test_error_handling_preserves_error_output(self, mock_parallel_commands):
        """
        Test that CLI errors are preserved in results.

        Given: CLI returns error in stderr
        When: run_parallel_llm is called
        Then: Results should contain error field
        """
        # Arrange
        query = "test query"
        mock_parallel_commands.return_value = {
            "qwen": {"output": "", "error": "Command failed: exit code 1"},
        }

        # Act
        results = run_parallel_llm(query, qwen_only=True)

        # Assert
        assert "qwen" in results
        assert results["qwen"]["error"] == "Command failed: exit code 1"
        assert results["qwen"]["output"] == ""

    def test_empty_response_flagged_as_error(self, mock_parallel_commands):
        """
        Test that empty CLI responses are flagged as errors.

        Given: CLI returns empty output with no error
        When: run_parallel_llm is called
        Then: Should add error message about silent failure
        """
        # Arrange
        query = "test query"
        mock_parallel_commands.return_value = {
            "qwen": {"output": "", "error": ""},  # Empty both
        }

        # Act
        results = run_parallel_llm(query, qwen_only=True)

        # Assert
        assert "qwen" in results
        assert "Empty response" in results["qwen"]["error"]

    def test_info_logs_filtered_from_errors(self, mock_parallel_commands):
        """
        Test that INFO/DEBUG logs are not treated as errors.

        Given: CLI stderr contains only INFO logs (no error keywords)
        When: run_parallel_llm is called
        Then: Should treat as success (error=None)
        """
        # Arrange
        query = "test query"
        mock_parallel_commands.return_value = {
            "qwen": {
                "output": "Response text",
                "error": "INFO: Starting process\nDEBUG: Loading model",
            },
        }

        # Act
        results = run_parallel_llm(query, qwen_only=True)

        # Assert - INFO logs filtered, treated as success
        assert "qwen" in results
        assert results["qwen"]["error"] is None
        assert results["qwen"]["output"] == "Response text"

    def test_windows_platform_uses_node_invocation(self, mock_parallel_commands):
        """
        Test that Windows platform uses direct node invocation.

        Given: Platform is win32
        When: Commands are built
        Then: Should use 'node ...' instead of CLI names
        """
        # Arrange
        query = "test query"
        mock_parallel_commands.return_value = {
            "qwen": {"output": "Response", "error": None},
        }

        # Act
        with patch("ai_cli.sys.platform", "win32"):
            results = run_parallel_llm(query, qwen_only=True)

        # Assert - Verify command includes 'node' for Windows
        called_args = mock_parallel_commands.call_args
        commands = called_args[0][0]  # First positional arg is commands list
        qwen_cmd = commands[0][1]  # Tuple is (name, command)

        assert "node" in qwen_cmd
        assert "qwen-code" in qwen_cmd

    def test_glm_api_key_absent_skips_glm(self, mock_parallel_commands):
        """
        Test that missing ZAI_API_KEY skips GLM in default mode.

        Given: No ZAI_API_KEY environment variable
        When: run_parallel_llm is called with no flags
        Then: Should NOT include GLM in results
        """
        # Arrange
        query = "test query"
        mock_parallel_commands.return_value = {
            "qwen": {"output": "Response", "error": None},
            "gemini": {"output": "Response", "error": None},
            "codex": {"output": "Response", "error": None},
            "vibe": {"output": "Response", "error": None},
            "opencode": {"output": "Response", "error": None},
        }

        # Act - Remove ZAI_API_KEY from environment
        original_env = os.environ.get("ZAI_API_KEY")
        if "ZAI_API_KEY" in os.environ:
            del os.environ["ZAI_API_KEY"]

        try:
            results = run_parallel_llm(query)
        finally:
            # Restore environment
            if original_env is not None:
                os.environ["ZAI_API_KEY"] = original_env

        # Assert - GLM should not be in results
        assert "glm-4.7-flash" not in results
        assert len(results) == 5  # Only CLI tools

    def test_timeout_parameter_passed_to_execution(self, mock_parallel_commands):
        """
        Test that timeout parameter is passed through.

        Given: timeout=300 specified
        When: run_parallel_llm is called
        Then: Should pass timeout to run_parallel_commands
        """
        # Arrange
        query = "test query"
        mock_parallel_commands.return_value = {"qwen": {"output": "Response", "error": None}}

        # Act
        results = run_parallel_llm(query, qwen_only=True, timeout=300)

        # Assert
        called_args = mock_parallel_commands.call_args
        timeout_arg = called_args[1].get("timeout")  # Keyword argument
        assert timeout_arg == 300
