#\!/usr/bin/env python3
"""Tests for artifact validation hooks (DISCOVER and VERIFY phases)."""

import importlib.util
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def load_hook_module(module_name, file_path):
    """Load a Python module from a file path (handles hyphens in names)."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class TestDiscoverEvidenceHook:
    """Test suite for PostToolUse_discover_evidence.py hook."""

    @property
    def discover_module(self):
        """Lazily load the discover evidence module."""
        hooks_dir = Path(__file__).resolve().parent.parent
        return load_hook_module(
            "PostToolUse_discover_evidence",
            hooks_dir / "PostToolUse_discover_evidence.py"
        )

    def test_discover_complete_with_all_evidence(self, tmp_path):
        """DISCOVER phase passes when all evidence files exist."""
        discover_dir = tmp_path / ".tdd_discovery"
        discover_dir.mkdir()

        (discover_dir / "grep_tests.txt").write_text("test found")
        (discover_dir / "imports_list.json").write_text('[]')
        (discover_dir / "coverage_baseline.json").write_text('{}')

        module = self.discover_module
        original_dir = module.DISCOVERY_DIR
        module.DISCOVERY_DIR = discover_dir

        try:
            is_complete, reason = module.validate_discovery_evidence()
            assert is_complete, f"Expected complete but got: {reason}"
        finally:
            module.DISCOVERY_DIR = original_dir

    def test_discover_fails_without_grep_tests(self, tmp_path):
        """DISCOVER phase blocks when grep_tests.txt is missing."""
        discover_dir = tmp_path / ".tdd_discovery"
        discover_dir.mkdir()

        (discover_dir / "imports_list.json").write_text('[]')
        (discover_dir / "coverage_baseline.json").write_text('{}')

        module = self.discover_module
        original_dir = module.DISCOVERY_DIR
        module.DISCOVERY_DIR = discover_dir

        try:
            is_complete, reason = module.validate_discovery_evidence()
            assert not is_complete
            assert "grep_tests.txt" in reason or "missing" in reason.lower()
        finally:
            module.DISCOVERY_DIR = original_dir

    def test_discover_fails_with_no_evidence(self, tmp_path):
        """DISCOVER phase blocks when no evidence directory exists."""
        discover_dir = tmp_path / ".tdd_discovery"
        # Do not create directory

        module = self.discover_module
        original_dir = module.DISCOVERY_DIR
        module.DISCOVERY_DIR = discover_dir

        try:
            is_complete, reason = module.validate_discovery_evidence()
            assert not is_complete
        finally:
            module.DISCOVERY_DIR = original_dir


class TestVerifyExecutionHook:
    """Test suite for StopHook_verify_execution.py hook."""

    @property
    def verify_module(self):
        """Lazily load the verify execution module."""
        hooks_dir = Path(__file__).resolve().parent.parent
        return load_hook_module(
            "StopHook_verify_execution",
            hooks_dir / "StopHook_verify_execution.py"
        )

    def test_verify_passes_with_two_tool_outputs(self, tmp_path):
        """VERIFY phase passes with 2+ valid JSON tool outputs."""
        verify_dir = tmp_path / ".tdd_verify"
        verify_dir.mkdir()

        (verify_dir / "ruff_output.json").write_text('{"results": []}')
        (verify_dir / "mypy_output.json").write_text('{"errors": []}')

        module = self.verify_module
        original_dir = module.VERIFY_DIR
        module.VERIFY_DIR = verify_dir

        try:
            is_valid, reason = module.validate_verify_execution()
            assert is_valid, f"Expected valid but got: {reason}"
        finally:
            module.VERIFY_DIR = original_dir

    def test_verify_fails_with_no_tool_outputs(self, tmp_path):
        """VERIFY phase blocks when no tool output files exist."""
        verify_dir = tmp_path / ".tdd_verify"
        verify_dir.mkdir()

        module = self.verify_module
        original_dir = module.VERIFY_DIR
        module.VERIFY_DIR = verify_dir

        try:
            is_valid, reason = module.validate_verify_execution()
            assert not is_valid
            assert "insufficient" in reason.lower() or "tool" in reason.lower()
        finally:
            module.VERIFY_DIR = original_dir

    def test_verify_rejects_invalid_json(self, tmp_path):
        """VERIFY phase rejects non-JSON files (not real tool output)."""
        verify_dir = tmp_path / ".tdd_verify"
        verify_dir.mkdir()

        (verify_dir / "ruff_output.json").write_text("not valid json {")

        module = self.verify_module
        original_dir = module.VERIFY_DIR
        module.VERIFY_DIR = verify_dir

        try:
            is_valid, reason = module.validate_verify_execution()
            assert not is_valid
            assert "0/" in reason
        finally:
            module.VERIFY_DIR = original_dir

    def test_verify_counts_only_valid_json(self, tmp_path):
        """VERIFY phase only counts properly formatted JSON files."""
        verify_dir = tmp_path / ".tdd_verify"
        verify_dir.mkdir()

        # 1 valid JSON, 1 invalid = should fail (need at least 2)
        (verify_dir / "ruff_output.json").write_text('{"results": []}')
        (verify_dir / "mypy_output.json").write_text("invalid json")

        module = self.verify_module
        original_dir = module.VERIFY_DIR
        module.VERIFY_DIR = verify_dir

        try:
            is_valid, reason = module.validate_verify_execution()
            assert not is_valid, "Should fail with only 1 valid JSON file (need at least 2)"
            assert "1/" in reason
        finally:
            module.VERIFY_DIR = original_dir


class TestArtifactGrounder:
    """Test suite for __lib/artifact_grounder.py - artifact grounding functions."""

    @property
    def grouper_module(self):
        """Lazily load the artifact grouper module."""
        hooks_dir = Path(__file__).resolve().parent.parent
        lib_path = hooks_dir / "__lib" / "artifact_grounder.py"

        if not lib_path.exists():
            return None

        return load_hook_module(
            "artifact_grounder",
            lib_path
        )

    @property
    def validator_module(self):
        """Lazily load the artifact validator module."""
        hooks_dir = Path(__file__).resolve().parent.parent
        validator_path = hooks_dir / "PostToolUse_artifact_validator.py"

        if not validator_path.exists():
            return None

        return load_hook_module(
            "PostToolUse_artifact_validator",
            validator_path
        )

    def test_ground_blocked_command_basic(self):
        """
        Test that ground_blocked_command creates proper artifact structure.

        Given: Mock hook data with blocked Bash command
        When: Call ground_blocked_command()
        Then: Returns proper blocked_command artifact schema
        """
        module = self.grouper_module
        if module is None:
            raise AttributeError("artifact_grounder module not found - function not implemented")

        # Arrange
        data = {
            "tool_name": "Bash",
            "tool_input": {
                "command": 'python -c "import sys"'
            }
        }
        blocking_hook = "PreToolUse_auth.py"
        reason = "Requires auth"

        # Act
        result = module.ground_blocked_command(data, blocking_hook, reason)

        # Assert
        assert result["schema"] == "blocked_command"
        assert result["tool_name"] == "Bash"
        assert "python" in result["tool_input"]["command"]

    def test_ground_blocked_command_preserves_exact_command(self):
        """
        Test that ground_blocked_command preserves command character-for-character.

        Given: Complex command with escaped characters and quotes
        When: Call ground_blocked_command()
        Then: Command is preserved exactly (character-for-character match)
        """
        module = self.grouper_module
        if module is None:
            raise AttributeError("artifact_grounder module not found - function not implemented")

        # Arrange
        cmd = 'cd "P:\\\\.claude\\\\hooks" && python -c "import sys; print(42)"'
        data = {
            "tool_name": "Bash",
            "tool_input": {
                "command": cmd
            }
        }

        # Act
        result = module.ground_blocked_command(data, "git_safety.py", "Blocked")

        # Assert
        assert result["tool_input"]["command"] == cmd

    def test_extract_command_tokens(self):
        """
        Test that extract_command_tokens tokenizes commands properly.

        Given: A python command with imports and function calls
        When: Call extract_command_tokens()
        Then: Returns meaningful tokens, filters stopwords
        """
        module = self.grouper_module
        if module is None:
            pytest.skip("artifact_grounder.py not implemented yet")

        # Arrange
        cmd = 'python -c "import sys; print(sys.version)"'

        # Act
        tokens = module.extract_command_tokens(cmd)

        # Assert
        assert "python" in tokens
        assert "import" in tokens or "sys" in tokens
        assert "cd" not in tokens  # Should filter stopwords

    def test_ground_git_safety_block(self):
        """
        Test that ground_git_safety_block creates proper git_safety_block artifact.

        Given: Mock data for blocked git status command
        When: Call ground_git_safety_block()
        Then: Returns proper git_safety_block artifact with subcommand
        """
        module = self.grouper_module
        if module is None:
            pytest.skip("artifact_grounder.py not implemented yet")

        # Arrange
        data = {
            "tool_name": "Bash",
            "tool_input": {
                "command": "git status --porcelain"
            }
        }
        blocking_hook = "PreToolUse_git_safety.py"
        reason = "Git safety check: no operations during merge conflict"

        # Act
        result = module.ground_git_safety_block(data, blocking_hook, reason)

        # Assert
        assert result["schema"] == "git_safety_block"
        assert result["git_subcommand"] == "status"


class TestDriftDetection:
    """Test suite for drift detection in PostToolUse_artifact_validator.py."""

    @property
    def validator_module(self):
        """Lazily load the artifact validator module."""
        hooks_dir = Path(__file__).resolve().parent.parent
        validator_path = hooks_dir / "PostToolUse_artifact_validator.py"

        if not validator_path.exists():
            return None

        return load_hook_module(
            "PostToolUse_artifact_validator",
            validator_path
        )

    def test_no_drift_when_command_mentioned(self, tmp_path):
        """
        Test that no warning is issued when RCA mentions the actual command.

        Given: Artifact with python command, RCA that quotes the command
        When: validate_rca_against_artifact() is called
        Then: Returns None (no warning)
        """
        module = self.validator_module
        if module is None or not hasattr(module, 'validate_rca_against_artifact'):
            pytest.skip("validate_rca_against_artifact not implemented yet")

        # Arrange - create artifact file in hooks state directory
        hooks_dir = Path(__file__).resolve().parent.parent
        state_dir = hooks_dir / "state"
        state_dir.mkdir(exist_ok=True)

        artifact = {
            "schema": "blocked_command",
            "tool_name": "Bash",
            "tool_input": {"command": "python -c \"import sys\""},
            "command_tokens": ["python", "import", "sys"],
            "blocking_hook": "PreToolUse_auth.py",
            "raw_reason": "Requires auth"
        }

        session_id = "test-session-no-drift"
        safe_session = re.sub(r"[^a-zA-Z0-9_.-]+", "_", session_id)
        artifact_path = state_dir / f"grounded_artifact_{safe_session}.json"

        # Cleanup any existing artifact from previous test run
        artifact_path.unlink(missing_ok=True)

        try:
            artifact_path.write_text(json.dumps(artifact))

            # Simulate hook input
            data = {
                "session": {"id": session_id},
                "tool_result": "The command `python -c \"import sys\"` was blocked because it requires auth. Root cause: missing credentials."
            }

            # Act
            result = module.validate_rca_against_artifact(data)

            # Assert - no warning when command is mentioned
            assert result is None, f"Expected None when command is mentioned, got: {result}"
        finally:
            # Cleanup artifact file
            artifact_path.unlink(missing_ok=True)

    def test_drift_when_wrong_command(self, tmp_path):
        """
        Test that warning is issued when RCA talks about different command.

        Given: Artifact with python command, RCA talks about git safety
        When: validate_rca_against_artifact() is called
        Then: Returns warning injection
        """
        module = self.validator_module
        if module is None or not hasattr(module, 'validate_rca_against_artifact'):
            pytest.skip("validate_rca_against_artifact not implemented yet")

        # Arrange - create artifact file in hooks state directory
        hooks_dir = Path(__file__).resolve().parent.parent
        state_dir = hooks_dir / "state"
        state_dir.mkdir(exist_ok=True)

        artifact = {
            "schema": "blocked_command",
            "tool_name": "Bash",
            "tool_input": {"command": "python -c \"import sys\""},
            "command_tokens": ["python", "import", "sys"],
            "blocking_hook": "PreToolUse_auth.py",
            "raw_reason": "Requires auth"
        }

        session_id = "test-session-drift"
        safe_session = re.sub(r"[^a-zA-Z0-9_.-]+", "_", session_id)
        artifact_path = state_dir / f"grounded_artifact_{safe_session}.json"
        artifact_path.unlink(missing_ok=True)

        try:
            artifact_path.write_text(json.dumps(artifact))

            # Simulate hook input - RCA talks about git safety, not python
            data = {
                "session": {"id": session_id},
                "tool_result": "The global git status command was blocked by the git safety gate. Root cause: running git without path limiter is dangerous during merge conflicts."
            }

            # Act
            result = module.validate_rca_against_artifact(data)

            # Assert - warning should be injected
            assert result is not None, "Expected warning injection for drift"
            assert "hookSpecificOutput" in result
            assert "additionalContext" in result["hookSpecificOutput"]
            context = result["hookSpecificOutput"]["additionalContext"]
            assert "WARNING" in context or "wrong artifact" in context.lower()
        finally:
            artifact_path.unlink(missing_ok=True)

    def test_low_token_overlap_triggers_warning(self, tmp_path):
        """
        Test that low token overlap ratio triggers drift warning.

        Given: Artifact with specific tokens, RCA with unrelated content
        When: validate_rca_against_artifact() is called
        Then: Returns warning injection
        """
        module = self.validator_module
        if module is None or not hasattr(module, 'validate_rca_against_artifact'):
            pytest.skip("validate_rca_against_artifact not implemented yet")

        # Arrange - create artifact file in hooks state directory
        hooks_dir = Path(__file__).resolve().parent.parent
        state_dir = hooks_dir / "state"
        state_dir.mkdir(exist_ok=True)

        artifact = {
            "schema": "blocked_command",
            "tool_name": "Bash",
            "tool_input": {"command": "python -c \"import sys\""},
            "command_tokens": ["python", "import", "sys"],
            "blocking_hook": "PreToolUse_auth.py",
            "raw_reason": "Requires auth"
        }

        session_id = "test-session-low-overlap"
        safe_session = re.sub(r"[^a-zA-Z0-9_.-]+", "_", session_id)
        artifact_path = state_dir / f"grounded_artifact_{safe_session}.json"
        artifact_path.unlink(missing_ok=True)

        try:
            artifact_path.write_text(json.dumps(artifact))

            # RCA with completely unrelated content (low token overlap)
            data = {
                "session": {"id": session_id},
                "tool_result": "The docker container failed to start because the network configuration was invalid. Root cause: missing bridge network definition in docker-compose.yml."
            }

            # Act
            result = module.validate_rca_against_artifact(data)

            # Assert - warning for low overlap
            assert result is not None, "Expected warning for low token overlap"
            assert "hookSpecificOutput" in result
            assert "additionalContext" in result["hookSpecificOutput"]
            context = result["hookSpecificOutput"]["additionalContext"]
            assert "WARNING" in context or "wrong artifact" in context.lower()
        finally:
            artifact_path.unlink(missing_ok=True)

    def test_terminal_scoped_artifact_is_preferred(self, tmp_path):
        """
        Test that terminal-scoped artifact files are preferred over legacy session files.

        Given: Both terminal+session and session-only artifacts exist
        When: validate_rca_against_artifact() is called
        Then: The terminal-scoped artifact is used first
        """
        module = self.validator_module
        if module is None or not hasattr(module, 'validate_rca_against_artifact'):
            pytest.skip("validate_rca_against_artifact not implemented yet")

        hooks_dir = Path(__file__).resolve().parent.parent
        state_dir = hooks_dir / "state"
        state_dir.mkdir(exist_ok=True)

        session_id = "test-session-terminal-priority"
        terminal_id = "console_terminal_priority"
        safe_session = re.sub(r"[^a-zA-Z0-9_.-]+", "_", session_id)
        safe_terminal = re.sub(r"[^a-zA-Z0-9_.-]+", "_", terminal_id)

        terminal_artifact_path = state_dir / f"grounded_artifact_{safe_terminal}_{safe_session}.json"
        legacy_artifact_path = state_dir / f"grounded_artifact_{safe_session}.json"
        terminal_artifact_path.unlink(missing_ok=True)
        legacy_artifact_path.unlink(missing_ok=True)

        terminal_artifact = {
            "schema": "blocked_command",
            "tool_name": "Bash",
            "tool_input": {"command": "python -c \"import terminal_scope\""},
            "command_tokens": ["python", "import", "terminal_scope"],
            "blocking_hook": "PreToolUse_auth.py",
            "raw_reason": "Requires auth"
        }
        legacy_artifact = {
            "schema": "blocked_command",
            "tool_name": "Bash",
            "tool_input": {"command": "git status"},
            "command_tokens": ["git", "status"],
            "blocking_hook": "PreToolUse_git.py",
            "raw_reason": "Requires limiter"
        }

        try:
            terminal_artifact_path.write_text(json.dumps(terminal_artifact), encoding="utf-8")
            legacy_artifact_path.write_text(json.dumps(legacy_artifact), encoding="utf-8")

            data = {
                "session": {"id": session_id, "terminal_id": terminal_id},
                "tool_result": (
                    "The command `python -c \"import terminal_scope\"` was blocked because "
                    "it requires auth. Root cause: missing credentials."
                )
            }

            result = module.validate_rca_against_artifact(data)
            assert result is None, f"Expected terminal-scoped artifact to validate cleanly, got: {result}"
        finally:
            terminal_artifact_path.unlink(missing_ok=True)
            legacy_artifact_path.unlink(missing_ok=True)

    def test_short_output_skips_validation(self, tmp_path):
        """
        Test that short outputs skip validation (< 50 chars).

        Given: Artifact exists, but tool output is only 30 characters
        When: validate_rca_against_artifact() is called
        Then: Returns None (skip validation)
        """
        module = self.validator_module
        if module is None or not hasattr(module, 'validate_rca_against_artifact'):
            pytest.skip("validate_rca_against_artifact not implemented yet")

        # Arrange
        state_dir = tmp_path / "state"
        state_dir.mkdir()

        artifact = {
            "schema": "blocked_command",
            "tool_input": {"command": "test command"},
            "command_tokens": ["test"],
            "blocking_hook": "test.py"
        }

        session_id = "test-session-short"
        safe_session = re.sub(r"[^a-zA-Z0-9_.-]+", "_", session_id)
        artifact_path = state_dir / f"grounded_artifact_{safe_session}.json"
        artifact_path.write_text(json.dumps(artifact))

        # Short output (< 50 chars)
        data = {
            "session": {"id": session_id},
            "tool_result": "This is short."  # 17 chars
        }

        # Act
        result = module.validate_rca_against_artifact(data)

        # Assert - should skip validation
        assert result is None, "Expected None for short output"

    def test_no_rca_markers_skips_validation(self, tmp_path):
        """
        Test that outputs without RCA markers skip validation.

        Given: Artifact exists, output has no RCA marker words
        When: validate_rca_against_artifact() is called
        Then: Returns None (skip validation)
        """
        module = self.validator_module
        if module is None or not hasattr(module, 'validate_rca_against_artifact'):
            pytest.skip("validate_rca_against_artifact not implemented yet")

        # Arrange
        state_dir = tmp_path / "state"
        state_dir.mkdir()

        artifact = {
            "schema": "blocked_command",
            "tool_input": {"command": "test command here"},
            "command_tokens": ["test", "command"],
            "blocking_hook": "test.py"
        }

        session_id = "test-session-no-markers"
        safe_session = re.sub(r"[^a-zA-Z0-9_.-]+", "_", session_id)
        artifact_path = state_dir / f"grounded_artifact_{safe_session}.json"
        artifact_path.write_text(json.dumps(artifact))

        # Output without RCA markers (just normal text)
        data = {
            "session": {"id": session_id},
            "tool_result": "The operation completed successfully and returned the expected results. All tests passed."
        }

        # Act
        result = module.validate_rca_against_artifact(data)

        # Assert - should skip validation
        assert result is None, "Expected None when no RCA markers"

    def test_tool_type_drift_heuristic(self, tmp_path):
        """
        Test tool-type drift: git safety phrases vs python command.

        Given: Artifact with python command, RCA has git-safety-specific phrases
        When: validate_rca_against_artifact() is called
        Then: Returns warning injection
        """
        module = self.validator_module
        if module is None or not hasattr(module, 'validate_rca_against_artifact'):
            pytest.skip("validate_rca_against_artifact not implemented yet")

        # Arrange - python command, not git - use hooks state directory
        hooks_dir = Path(__file__).resolve().parent.parent
        state_dir = hooks_dir / "state"
        state_dir.mkdir(exist_ok=True)

        artifact = {
            "schema": "blocked_command",
            "tool_name": "Bash",
            "tool_input": {"command": "python -c \"print('test')\""},
            "command_tokens": ["python", "print", "test"],
            "blocking_hook": "PreToolUse_auth.py",
            "raw_reason": "Requires auth"
        }

        session_id = "test-session-tool-drift"
        safe_session = re.sub(r"[^a-zA-Z0-9_.-]+", "_", session_id)
        artifact_path = state_dir / f"grounded_artifact_{safe_session}.json"
        artifact_path.unlink(missing_ok=True)

        try:
            artifact_path.write_text(json.dumps(artifact))

            # RCA with git safety phrases but actual command is python
            data = {
                "session": {"id": session_id},
                "tool_result": "Global git status without path limiter was blocked by the git safety gate. Root cause: this operation is not allowed during merge conflicts."
            }

            # Act
            result = module.validate_rca_against_artifact(data)

            # Assert - tool-type drift should trigger warning
            assert result is not None, "Expected warning for tool-type drift (git phrases vs python command)"
            assert "hookSpecificOutput" in result
            context = result["hookSpecificOutput"]["additionalContext"]
            # Should mention the actual python command
            assert "python" in context.lower()
        finally:
            artifact_path.unlink(missing_ok=True)

    def test_no_artifact_skips_validation(self, tmp_path):
        """
        Test that validation is skipped when no artifact exists.

        Given: No artifact file exists
        When: validate_rca_against_artifact() is called
        Then: Returns None (skip gracefully)
        """
        module = self.validator_module
        if module is None or not hasattr(module, 'validate_rca_against_artifact'):
            pytest.skip("validate_rca_against_artifact not implemented yet")

        # Arrange - create state dir but no artifact
        state_dir = tmp_path / "state"
        state_dir.mkdir()

        data = {
            "session": {"id": "test-session-no-artifact"},
            "tool_result": "Root cause analysis: This is a long enough output with RCA markers."
        }

        # Act
        result = module.validate_rca_against_artifact(data)

        # Assert - should handle missing artifact gracefully
        assert result is None, "Expected None when no artifact exists"

    def test_best_effort_error_handling(self, tmp_path):
        """
        Test that malformed artifact JSON is handled gracefully.

        Given: Artifact file exists but contains invalid JSON
        When: validate_rca_against_artifact() is called
        Then: Returns None (best-effort, no crash)
        """
        module = self.validator_module
        if module is None or not hasattr(module, 'validate_rca_against_artifact'):
            pytest.skip("validate_rca_against_artifact not implemented yet")

        # Arrange - create malformed artifact file
        state_dir = tmp_path / "state"
        state_dir.mkdir()

        session_id = "test-session-malformed"
        safe_session = re.sub(r"[^a-zA-Z0-9_.-]+", "_", session_id)
        artifact_path = state_dir / f"grounded_artifact_{safe_session}.json"
        artifact_path.write_text("invalid json {")

        data = {
            "session": {"id": session_id},
            "tool_result": "Root cause: This should not crash the validator."
        }

        # Act - should not raise exception
        try:
            result = module.validate_rca_against_artifact(data)
            # Assert - should handle gracefully
            assert result is None, "Expected None for malformed artifact"
        except Exception as e:
            pytest.fail(f"validate_rca_against_artifact raised exception: {e}")


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
