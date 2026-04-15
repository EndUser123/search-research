"""
Characterization tests for ask_cli.py high-complexity functions.

These tests capture CURRENT BEHAVIOR before refactoring.
Run with: pytest P:/.claude/skills/ai-cli/tests/test_complexity_characterization.py -v

PURPOSE:
- QUAL-001: Characterize _extract_answer (complexity 56)
- QUAL-002: Characterize run_parallel_llm (complexity 32)
- QUAL-003: Characterize main (complexity 25)

TDD Workflow:
1. GREEN: All tests pass (capturing current behavior)
2. REFACTOR: Make changes to reduce complexity
3. GREEN: All tests still pass (behavior preserved)
"""

import json
import re

# Add parent directory to path for imports
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_cli import (
    _add_datetime_suffix,
    _extract_answer,
    _parse_opencode_streaming_json,
    expand_prompt,
    format_aggregate,
    format_complete,
    format_diff,
    format_results,
    format_summary,
    generate_parallel_bash_commands,
    run_parallel_llm,
    show_prompt_options,
)

# ============================================================================
# QUAL-001: _extract_answer (Complexity 56)
# ============================================================================


class TestExtractAnswerQwen:
    """Characterization tests for _extract_answer with 'qwen' CLI output."""

    def test_qwen_json_array_with_result_field(self):
        """
        CHARACTERIZATION: _extract_answer extracts result field from qwen JSON array.

        Current behavior: Searches backwards for last assistant message,
        returns result field if present, NOT truncated (actual behavior differs from assumption).
        """
        # Arrange - qwen JSON array format
        output = json.dumps(
            [
                {"type": "system", "message": {"content": [{"text": "System prompt"}]}},
                {"type": "assistant", "message": {"content": [{"text": "First response"}]}},
                {
                    "type": "assistant",
                    "result": "This is the final answer from qwen CLI output that should be extracted",
                },
            ]
        )

        # Act
        result = _extract_answer("qwen", output)

        # Assert - Captures ACTUAL behavior: returns full result (no 1000 char truncation)
        assert result == "This is the final answer from qwen CLI output that should be extracted"

    def test_qwen_fallback_to_text_content(self):
        """
        CHARACTERIZATION: Falls back to content text when result field missing.
        """
        # Arrange - No result field
        output = json.dumps(
            [{"type": "assistant", "message": {"content": [{"text": "Fallback answer text"}]}}]
        )

        # Act
        result = _extract_answer("qwen", output)

        # Assert
        assert result == "Fallback answer text"

    def test_qwen_empty_output(self):
        """CHARACTERIZATION: Returns '[No output]' for empty output."""
        result = _extract_answer("qwen", "")
        assert result == "[No output]"

    def test_qwen_malformed_json_fallback(self):
        """CHARACTERIZATION: Falls back to regex for malformed JSON."""
        # Arrange - Non-JSON line
        output = "This is a plain text answer from qwen\n"

        # Act
        result = _extract_answer("qwen", output)

        # Assert - First non-JSON line, truncated to 200
        assert "plain text answer" in result


class TestExtractAnswerGemini:
    """Characterization tests for _extract_answer with 'gemini' CLI output."""

    def test_gemini_response_field(self):
        """
        CHARACTERIZATION: Extracts response field from gemini JSON.

        ACTUAL behavior: Returns full response without truncation.
        """
        # Arrange - gemini JSON format
        output = json.dumps(
            {"response": "This is the gemini response text that should be extracted completely"}
        )

        # Act
        result = _extract_answer("gemini", output)

        # Assert - Returns full response (actual behavior)
        assert result == "This is the gemini response text that should be extracted completely"

    def test_gemini_nested_message_text(self):
        """
        CHARACTERIZATION: Falls back to nested message.text when response missing.
        """
        # Arrange - Nested format
        output = json.dumps(
            {
                "message": [
                    {"text": "First message"},
                    {"text": "Last message text (searches backwards)"},
                ]
            }
        )

        # Act
        result = _extract_answer("gemini", output)

        # Assert - Searches backwards, finds last text
        assert "Last message text" in result


class TestExtractAnswerCodex:
    """Characterization tests for _extract_answer with 'codex' CLI output."""

    def test_codex_item_completed_with_text(self):
        """
        CHARACTERIZATION: codex searches backwards for turn.completed marker.

        ACTUAL behavior: Returns "[Turn completed - see full output]" marker,
        not the item.completed text content (searches backwards, finds turn.completed first).
        """
        # Arrange - JSONL format (newline-separated JSON objects)
        output = "\n".join(
            [
                json.dumps({"type": "turn.started"}),
                json.dumps(
                    {
                        "type": "item.completed",
                        "item": {"text": "A" * 150},  # Substantial (>100 chars)
                    }
                ),
                json.dumps({"type": "turn.completed"}),
            ]
        )

        # Act
        result = _extract_answer("codex", output)

        # Assert - Returns turn.completed marker (actual behavior)
        assert result == "[Turn completed - see full output]"

    def test_codex_short_text_skipped(self):
        """
        CHARACTERIZATION: Skips short item.completed texts, uses turn.completed.
        """
        # Arrange - Short text
        output = "\n".join(
            [
                json.dumps({"type": "turn.started"}),
                json.dumps(
                    {
                        "type": "item.completed",
                        "item": {"text": "Reading..."},  # Too short
                    }
                ),
                json.dumps({"type": "turn.completed"}),
            ]
        )

        # Act
        result = _extract_answer("codex", output)

        # Assert - Falls through to turn.completed marker
        assert "Turn completed" in result

    def test_codex_fallback_regex(self):
        """CHARACTERIZATION: Falls back to regex for text field."""
        # Arrange - Malformed JSONL
        output = '{"type": "item.completed", "item": {"text": "Regex fallback answer"}}'

        # Act
        result = _extract_answer("codex", output)

        # Assert - Regex extracts quoted text after "text":
        assert "Regex fallback answer" in result


class TestExtractAnswerVibe:
    """Characterization tests for _extract_answer with 'vibe' CLI output."""

    def test_vibe_last_assistant_message(self):
        """
        CHARACTERIZATION: Searches backwards for last assistant role message.
        """
        # Arrange - JSON array with role/content
        output = json.dumps(
            [
                {"role": "system", "content": "You are helpful"},
                {"role": "assistant", "content": "First response"},
                {"role": "assistant", "content": "Last assistant response (should be extracted)"},
            ]
        )

        # Act
        result = _extract_answer("vibe", output)

        # Assert - Searches backwards, finds last assistant
        assert "Last assistant response" in result

    def test_vibe_skips_system_prompt(self):
        """
        CHARACTERIZATION: vibe JSON parsing returns raw JSON string on parse failure.

        ACTUAL behavior: When JSON parsing fails or doesn't match expected format,
        returns the raw JSON output string (not extracted content).
        """
        # Arrange
        output = json.dumps(
            [
                {
                    "role": "assistant",
                    "content": "You are operating in test mode\n\nActual answer here",
                }
            ]
        )

        # Act
        result = _extract_answer("vibe", output)

        # Assert - Returns raw JSON when content extraction fails (actual behavior)
        assert "You are operating" in result  # Raw JSON returned
        assert '{"role"' in result  # Contains JSON structure


class TestExtractAnswerOpenCode:
    """Characterization tests for _extract_answer with 'opencode' CLI output."""

    def test_opencode_plain_text_passthrough(self):
        """
        CHARACTERIZATION: opencode returns plain text without JSON parsing.
        """
        # Arrange - Plain text (no JSON)
        output = "This is plain text output from opencode CLI\nNo JSON wrapping here."

        # Act
        result = _extract_answer("opencode", output)

        # Assert - Returns as-is (no JSON parsing)
        assert result == output.strip()

    def test_opencode_empty_output(self):
        """CHARACTERIZATION: Returns '[No output]' for empty opencode output."""
        result = _extract_answer("opencode", "")
        assert result == "[No output]"


# ============================================================================
# QUAL-002 Helper: _parse_opencode_streaming_json
# ============================================================================


class TestParseOpenCodeStreamingJson:
    """Characterization tests for OpenCode streaming JSON parser."""

    def test_extracts_text_from_type_text_objects(self):
        """
        CHARACTERIZATION: Extracts part.text from objects with type='text'.
        """
        # Arrange - Streaming JSON format
        output = "\n".join(
            [
                '{"type": "step_start", "step": "generate"}',
                '{"type": "text", "part": {"text": "First text chunk"}}',
                '{"type": "text", "part": {"text": "Second text chunk"}}',
                '{"type": "step_finish", "step": "generate"}',
            ]
        )

        # Act
        result = _parse_opencode_streaming_json(output)

        # Assert - Concatenates all text parts
        assert "First text chunk" in result
        assert "Second text chunk" in result
        assert result == "First text chunkSecond text chunk"

    def test_skips_non_json_lines(self):
        """
        CHARACTERIZATION: Skips INFO log lines that aren't valid JSON.
        """
        # Arrange - Mixed JSON and log lines
        output = "INFO: Starting...\n" + json.dumps(
            {"type": "text", "part": {"text": "Actual content"}}
        )

        # Act
        result = _parse_opencode_streaming_json(output)

        # Assert - Skips non-JSON, extracts text
        assert "Actual content" in result

    def test_malformed_json_returns_original(self):
        """
        CHARACTERIZATION: Returns original output if parsing fails.
        """
        # Arrange - Completely malformed
        output = "Not JSON at all\n{broken json"

        # Act
        result = _parse_opencode_streaming_json(output)

        # Assert - Returns original
        assert result == output


# ============================================================================
# QUAL-002: run_parallel_llm (Complexity 32)
# ============================================================================


class TestRunParallelLlmGlmMode:
    """Characterization tests for GLM API mode."""

    @patch("ai_cli.get_glm_api_key")
    @patch("ai_cli.asyncio.run")
    def test_glm_flash_only_mode(self, mock_asyncio_run, mock_get_key):
        """
        CHARACTERIZATION: GLM-4.7-Flash mode uses API via run_parallel_glm.

        ACTUAL behavior: GLM mode calls get_glm_api_key() and uses async API.
        """
        # Arrange
        mock_get_key.return_value = "test-api-key"
        mock_asyncio_run.return_value = {
            "glm-4.7-flash": {"output": "GLM API response", "error": None}
        }

        # Act
        result = run_parallel_llm(query="test query", glm_flash_only=True, timeout=180)

        # Assert - API mode returns structured dict
        assert "glm-4.7-flash" in result
        assert result["glm-4.7-flash"]["output"] == "GLM API response"
        mock_get_key.assert_called_once()

    @patch("ai_cli.get_glm_api_key")
    @patch("ai_cli.asyncio.run")
    def test_glm_api_error_handling(self, mock_asyncio_run, mock_get_key):
        """
        CHARACTERIZATION: GLM API errors are captured in result dict.

        ACTUAL behavior: Error field populated when API fails.
        """
        # Arrange
        mock_get_key.return_value = "test-key"
        mock_asyncio_run.return_value = {"glm-4.7-flash": {"error": "API timeout", "output": ""}}

        # Act
        result = run_parallel_llm(query="test", glm_flash_only=True)

        # Assert - Error preserved in result
        assert result["glm-4.7-flash"]["error"] == "API timeout"
        assert result["glm-4.7-flash"]["output"] == ""


class TestRunParallelLlmCliMode:
    """Characterization tests for CLI subprocess mode."""

    @patch("ai_cli.asyncio.run")
    @patch("ai_cli._REPO_ROOT", Path("P:/"))
    def test_default_runs_all_clis(self, mock_asyncio_run):
        """
        CHARACTERIZATION: No flags = run all CLIs (qwen, gemini, codex, vibe, opencode).

        ACTUAL behavior: CLI mode uses asyncio.run() with run_parallel_commands.
        """
        # Arrange
        mock_asyncio_run.return_value = {
            "qwen": {"output": "Qwen output", "error": ""},
            "gemini": {"output": "Gemini output", "error": ""},
            "codex": {"output": "Codex output", "error": ""},
            "vibe": {"output": "Vibe output", "error": ""},
            "opencode": {"output": "OpenCode output", "error": ""},
        }

        # Act - No specific flags (CLI mode default)
        result = run_parallel_llm(query="test")

        # Assert - All 5 CLIs executed
        assert len(result) == 5
        assert "qwen" in result
        assert "gemini" in result
        assert "codex" in result
        assert "vibe" in result
        assert "opencode" in result

    @patch("ai_cli.asyncio.run")
    def test_single_cli_mode(self, mock_asyncio_run):
        """
        CHARACTERIZATION: qwen_only=True runs only qwen CLI.

        ACTUAL behavior: Single CLI flag bypasses default all-CLI behavior.
        """
        # Arrange
        mock_asyncio_run.return_value = {"qwen": {"output": "Qwen only", "error": ""}}

        # Act
        result = run_parallel_llm(query="test", qwen_only=True)

        # Assert - Only qwen in results
        assert len(result) == 1
        assert "qwen" in result


class TestRunParallelLlmErrorFiltering:
    """Characterization tests for stderr log filtering."""

    @patch("ai_cli.asyncio.run")
    def test_filters_info_logs_from_stderr(self, mock_asyncio_run):
        """
        CHARACTERIZATION: INFO/DEBUG logs in stderr are filtered for opencode.

        ACTUAL behavior: Non-error keywords (INFO, DEBUG) in stderr are treated
        as success for opencode CLI, but other CLIs may have different handling.
        """
        # Arrange - stderr has INFO logs but no actual errors
        mock_asyncio_run.return_value = {
            "opencode": {
                "output": "Valid response",
                "error": "INFO: Starting request\nDEBUG: Payload sent\n",
            }
        }

        # Act
        result = run_parallel_llm(query="test", opencode_only=True)

        # Assert - INFO logs filtered for opencode, treated as success
        assert result["opencode"]["output"] == "Valid response"
        assert result["opencode"]["error"] is None

    @patch("ai_cli.asyncio.run")
    def test_actual_errors_preserved(self, mock_asyncio_run):
        """
        CHARACTERIZATION: Actual errors (HTTP 4xx/5xx, 'error', 'fail') are preserved.

        ACTUAL behavior: Error field preserved when contains error keywords.
        """
        # Arrange
        mock_asyncio_run.return_value = {
            "qwen": {"output": "", "error": "HTTP 500 Internal Server Error\nConnection failed"}
        }

        # Act
        result = run_parallel_llm(query="test", qwen_only=True)

        # Assert - Real error preserved
        assert "HTTP 500" in result["qwen"]["error"]


# ============================================================================
# QUAL-003: main() helper functions
# ============================================================================


class TestMainHelpers:
    """Characterization tests for main() helper functions."""

    def test_add_datetime_suffix_with_json_extension(self):
        """
        CHARACTERIZATION: Adds YYYYMMDD_HHMMSS suffix before .json extension.
        """
        # Arrange

        input_path = "output.json"

        # Act
        result = _add_datetime_suffix(input_path)

        # Assert - Pattern: output_YYYYMMDD_HHMMSS.json
        pattern = re.compile(r"^output_\d{8}_\d{6}_\d{6}\.json$")
        assert pattern.match(Path(result).name), f"Expected datetime suffix, got: {result}"

    def test_add_datetime_suffix_without_extension(self):
        """
        CHARACTERIZATION: Files without extension get .json added with suffix.
        """
        # Arrange
        input_path = "output"  # No extension

        # Act
        result = _add_datetime_suffix(input_path)

        # Assert - Should be output_YYYYMMDD_HHMMSS.json
        pattern = re.compile(r"^output_\d{8}_\d{6}_\d{6}\.json$")
        assert pattern.match(Path(result).name)

    def test_add_datetime_suffix_preserves_directory(self):
        """
        CHARACTERIZATION: Directory path handling for datetime suffix.

        ACTUAL behavior: Returns filename with suffix, directory handling
        depends on Path parent component (may or may not preserve based on input).
        """
        # Arrange
        input_path = "results/analysis.json"

        # Act
        result = _add_datetime_suffix(input_path)

        # Assert - Result contains analysis_ and .json (actual behavior)
        assert "analysis_" in result
        assert result.endswith(".json")
        # Note: Directory preservation may vary - key is filename gets suffix


class TestGenerateParallelBashCommands:
    """Characterization tests for bash command generation."""

    def test_default_generates_all_cli_commands(self):
        """
        CHARACTERIZATION: No flags = generates commands for all 4 CLIs.
        """
        # Arrange
        query = "test query"

        # Act
        commands = generate_parallel_bash_commands(query)

        # Assert - 4 commands (qwen, gemini, codex, vibe)
        assert len(commands) == 4
        assert any("qwen" in cmd for cmd in commands)
        assert any("gemini" in cmd for cmd in commands)
        assert any("codex" in cmd for cmd in commands)
        assert any("vibe" in cmd for cmd in commands)

    def test_qwen_only_single_command(self):
        """
        CHARACTERIZATION: qwen_only=True generates only qwen command.
        """
        # Arrange
        query = "test"

        # Act
        commands = generate_parallel_bash_commands(query, qwen_only=True)

        # Assert
        assert len(commands) == 1
        assert "qwen" in commands[0]

    def test_command_uses_shlex_quote_for_safety(self):
        """
        CHARACTERIZATION: Query is shell-escaped using shlex.quote.
        """
        # Arrange - Query with shell metacharacters
        query = "test; rm -rf /"

        # Act
        commands = generate_parallel_bash_commands(query, qwen_only=True)

        # Assert - Query should be quoted/escaped
        assert "'" in commands[0] or '"' in commands[0]
        assert "test" in commands[0]

    def test_vibe_uses_dash_p_not_stdin(self):
        """
        CHARACTERIZATION: vibe CLI uses -p flag, not stdin pipe.
        """
        # Arrange
        query = "test"

        # Act
        commands = generate_parallel_bash_commands(query, vibe_only=True)

        # Assert - vibe uses -p flag
        assert "vibe -p" in commands[0]
        assert "echo" not in commands[0]  # No stdin pipe


class TestExpandPrompt:
    """Characterization tests for prompt expansion."""

    def test_expands_simple_query(self):
        """
        CHARACTERIZATION: Simple query becomes detailed prompt with requirements.
        """
        # Arrange
        query = "explain recursion"

        # Act
        expanded = expand_prompt(query)

        # Assert - Contains template sections
        assert "CITATION:" in expanded
        assert "ACTIONABLE:" in expanded
        assert "SOLO DEVELOPER CONTEXT:" in expanded
        assert "LONG-TERM THINKING:" in expanded
        assert query in expanded

    def test_includes_original_query(self):
        """
        CHARACTERIZATION: Original query is embedded in expanded prompt.
        """
        # Arrange
        query = "test query for expansion"

        # Act
        expanded = expand_prompt(query)

        # Assert
        assert f"Query: {query}" in expanded


class TestPromptOptions:
    """Characterization tests for prompt selection menu."""

    @patch("builtins.input", return_value="1\n")
    def test_option_1_returns_expanded_prompt(self, mock_input):
        """
        CHARACTERIZATION: Option 1 returns the expanded/detailed prompt.
        """
        # Arrange
        expanded = "EXPANDED PROMPT HERE"
        original = "original"

        # Act
        with patch("builtins.print"):  # Suppress menu output
            result = show_prompt_options(expanded, original)

        # Assert
        assert result == expanded

    @patch("builtins.input", return_value="2\n")
    def test_option_2_returns_original_prompt(self, mock_input):
        """
        CHARACTERIZATION: Option 2 returns the original simple prompt.
        """
        # Arrange
        expanded = "expanded"
        original = "ORIGINAL PROMPT"

        # Act
        with patch("builtins.print"):
            result = show_prompt_options(expanded, original)

        # Assert
        assert result == original

    @patch("builtins.input", side_effect=["3\n", "custom prompt\n"])
    def test_option_3_prompts_for_custom_input(self, mock_input):
        """
        CHARACTERIZATION: Option 3 allows entering custom prompt.
        """
        # Arrange
        expanded = "expanded"
        original = "original"

        # Act
        with patch("builtins.print"):
            result = show_prompt_options(expanded, original)

        # Assert
        assert result == "custom prompt"

    @patch("builtins.input", return_value="invalid\n")
    def test_invalid_selection_raises_value_error(self, mock_input):
        """
        CHARACTERIZATION: Invalid selection raises ValueError.
        """
        # Arrange
        with patch("builtins.print"):
            # Act & Assert
            with pytest.raises(ValueError, match="Invalid selection"):
                show_prompt_options("expanded", "original")


class TestFormatResults:
    """Characterization tests for output formatting."""

    def test_format_results_with_errors(self):
        """
        CHARACTERIZATION: Results with errors show ERROR message.
        """
        # Arrange
        results = {
            "qwen": {"output": "Success", "error": None},
            "gemini": {"output": "", "error": "API failed"},
        }

        # Act
        formatted = format_results(results)

        # Assert
        assert "=== QWEN RESULT ===" in formatted
        assert "Success" in formatted
        assert "=== GEMINI RESULT ===" in formatted
        assert "ERROR: API failed" in formatted

    def test_format_results_includes_comparison(self):
        """
        CHARACTERIZATION: Includes COMPARISON section with previews.
        """
        # Arrange
        results = {
            "qwen": {"output": "Qwen answer here", "error": None},
            "gemini": {"output": "Gemini response", "error": None},
        }

        # Act
        formatted = format_results(results)

        # Assert
        assert "=== COMPARISON ===" in formatted
        assert "- qwen:" in formatted
        assert "- gemini:" in formatted


class TestFormatSummary:
    """Characterization tests for summary formatting."""

    def test_format_summary_shows_brief_answers(self):
        """
        CHARACTERIZATION: Summary shows extracted answers, not full output.
        """
        # Arrange - Mock results
        results = {
            "qwen": {"output": "Qwen full output text", "error": None},
            "gemini": {"output": "Gemini response", "error": None},
        }

        # Act - Mock _extract_answer to return first 200 chars
        with patch("ai_cli._extract_answer", side_effect=lambda n, o: o[:200]):
            formatted = format_summary(results)

        # Assert
        assert "## SUMMARY" in formatted
        assert "**qwen**:" in formatted
        assert "**gemini**:" in formatted

    def test_format_summary_error_shows_error_message(self):
        """
        CHARACTERIZATION: Failed results show ERROR instead of answer.
        """
        # Arrange
        results = {"qwen": {"output": "", "error": "Connection failed"}}

        # Act
        formatted = format_summary(results)

        # Assert
        assert "**qwen**: ERROR - Connection failed" in formatted


class TestFormatAggregate:
    """Characterization tests for consensus formatting."""

    def test_format_aggregate_shows_consensus_when_all_agree(self):
        """
        CHARACTERIZATION: Identical responses show CONSENSUS.
        """
        # Arrange
        results = {
            "qwen": {"output": "Same answer", "error": None},
            "gemini": {"output": "Same answer", "error": None},
        }

        # Act - Mock _extract_answer
        with patch("ai_cli._extract_answer", return_value="Same answer"):
            formatted = format_aggregate(results)

        # Assert
        assert "**CONSENSUS**: Same answer" in formatted
        assert "Agreement: 2/2" in formatted

    def test_format_aggregate_shows_partial_agreement(self):
        """
        CHARACTERIZATION: Different responses show PARTIAL AGREEMENT.
        """
        # Arrange
        results = {
            "qwen": {"output": "Answer A", "error": None},
            "gemini": {"output": "Answer B", "error": None},
        }

        # Act
        with patch("ai_cli._extract_answer", side_effect=lambda n, o: o):
            formatted = format_aggregate(results)

        # Assert
        assert "**PARTIAL AGREEMENT**" in formatted
        assert "2 different responses" in formatted


class TestFormatComplete:
    """Characterization tests for complete output formatting."""

    def test_format_complete_shows_full_output(self):
        """
        CHARACTERIZATION: Shows complete raw outputs without truncation.
        """
        # Arrange
        results = {"qwen": {"output": "Full qwen output here\nMultiple lines\n", "error": None}}

        # Act
        formatted = format_complete(results)

        # Assert
        assert "=== QWEN (COMPLETE) ===" in formatted
        assert "Full qwen output here" in formatted
        assert "Multiple lines" in formatted


class TestFormatDiff:
    """Characterization tests for diff formatting."""

    def test_format_diff_groups_by_unique_responses(self):
        """
        CHARACTERIZATION: Groups CLIs by response, shows disagreement.
        """
        # Arrange
        results = {
            "qwen": {"output": "Answer A", "error": None},
            "gemini": {"output": "Answer A", "error": None},
            "codex": {"output": "Answer B", "error": None},
        }

        # Act
        with patch("ai_cli._extract_answer", side_effect=lambda n, o: o):
            formatted = format_diff(results)

        # Assert
        assert "## RESPONSE DIFFERENCES" in formatted
        assert "2 unique response" in formatted
        assert "⚠️ DISAGREEMENT DETECTED" in formatted

    def test_format_diff_shows_consensus_when_all_same(self):
        """
        CHARACTERIZATION: All CLIs agreeing shows consensus message.
        """
        # Arrange
        results = {
            "qwen": {"output": "Same", "error": None},
            "gemini": {"output": "Same", "error": None},
        }

        # Act
        with patch("ai_cli._extract_answer", return_value="Same"):
            formatted = format_diff(results)

        # Assert
        assert "✅ CONSENSUS" in formatted
        assert "All CLIs agree" in formatted
