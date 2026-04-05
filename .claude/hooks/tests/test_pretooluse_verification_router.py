"""
Tests for PreToolUse verification router.

Tests the router's module loading, priority-based execution,
bypass flag handling, and error handling.
"""

import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Add hooks directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class TestRouterModuleLoading:
    """Test router module loading and caching."""

    def test_router_module_exists(self):
        """Test that router module can be imported."""
        # This will fail until we create the router module
        from PreToolUse_verification_router import (
            HOOK_PRIORITY,
            load_verification_modules,
            run_verification_modules,
        )

        assert HOOK_PRIORITY is not None
        assert callable(load_verification_modules)
        assert callable(run_verification_modules)

    def test_module_caching(self):
        """Test that modules are cached after first load."""
        from PreToolUse_verification_router import load_verification_modules

        # First load should cache the module
        module1 = load_verification_modules("investigation_verification")
        assert module1 is not None

        # Second load should return cached module
        module2 = load_verification_modules("investigation_verification")
        assert module1 is module2  # Same object


class TestPriorityExecution:
    """Test priority-based execution order."""

    def test_priority_dict_exists(self):
        """Test that HOOK_PRIORITY dict is defined."""
        from PreToolUse_verification_router import HOOK_PRIORITY

        assert isinstance(HOOK_PRIORITY, dict)
        # investigation_verification should have priority 4.5
        assert "investigation_verification" in HOOK_PRIORITY
        assert HOOK_PRIORITY["investigation_verification"] == 4.5

    @pytest.mark.skip(reason="Requires mock modules")
    def test_execution_order(self):
        """Test that modules execute in priority order."""
        from PreToolUse_verification_router import run_verification_modules

        # Create mock modules that record execution order
        execution_order = []

        def mock_module_a(data):
            execution_order.append("module_a")
            return None

        def mock_module_b(data):
            execution_order.append("module_b")
            return None

        # Mock module loading
        with patch('PreToolUse_verification_router.load_verification_module') as mock_load:
            # Set up priority: module_b (3.0) < module_a (5.0)
            mock_load.side_effect = lambda name: Mock(
                return_value=lambda data: (
                    execution_order.append("module_b") if name == "module_b" else None
                ) if name == "module_b" else (
                    execution_order.append("module_a") if name == "module_a" else None
                )
            )

            data = {}
            run_verification_modules(data)

            # module_b (priority 3.0) should execute before module_a (priority 5.0)
            assert execution_order == ["module_b", "module_a"]


class TestBypassFlag:
    """Test bypass flag functionality."""

    def test_bypass_flag_detected(self):
        """Test that bypass flag is detected in user prompt."""
        from PreToolUse_verification_modules.investigation_verification import check_bypass_flag

        # Bypass flag present
        data_with_bypass = {
            "userPrompt": "investigate error --skip-investigation-verify"
        }
        assert check_bypass_flag(data_with_bypass) == True

        # No bypass flag
        data_without_bypass = {
            "userPrompt": "investigate error"
        }
        assert check_bypass_flag(data_without_bypass) == False

    def test_bypass_flag_audit_logging(self):
        """Test that bypass usage is logged."""
        from PreToolUse_verification_modules.investigation_verification import (
            BYPASS_LOG,
            check_bypass_flag,
        )

        data_with_bypass = {
            "userPrompt": "investigate error --skip-investigation-verify",
            "sessionId": "test-session-123"
        }

        # Check that bypass is logged
        check_bypass_flag(data_with_bypass)

        # Verify log file was created and contains entry
        assert BYPASS_LOG.exists()
        log_content = BYPASS_LOG.read_text()
        assert "test-session-123" in log_content
        assert "--skip-investigation-verify" in log_content


class TestInvestigationKeywordDetection:
    """Test keyword detection for error investigations."""

    def test_has_investigation_keywords_direct(self):
        """Test detection of direct investigation keywords."""
        from PreToolUse_verification_modules.investigation_verification import (
            has_investigation_keywords,
        )

        # Direct keywords
        data = {"userPrompt": "investigate this error"}
        assert has_investigation_keywords(data) == True

        # Non-investigation
        data = {"userPrompt": "create a new file"}
        assert has_investigation_keywords(data) == False

    def test_synonym_detection(self):
        """Test that synonym keywords are detected."""
        from PreToolUse_verification_modules.investigation_verification import (
            has_investigation_keywords,
        )

        # Synonyms
        data = {"userPrompt": "I'm having trouble with this code"}
        assert has_investigation_keywords(data) == True

        data = {"userPrompt": "diagnose the issue"}
        assert has_investigation_keywords(data) == True

    def test_obfuscation_normalization(self):
        """Test that obfuscated keywords are detected."""
        from PreToolUse_verification_modules.investigation_verification import (
            has_investigation_keywords,
        )

        # Obfuscated with spaces
        data = {"userPrompt": "There's an e r r o r in the system"}
        assert has_investigation_keywords(data) == True

    def test_empty_input_handling(self):
        """Test handling of empty and non-string input."""
        from PreToolUse_verification_modules.investigation_verification import (
            has_investigation_keywords,
        )

        # Empty string
        data = {"userPrompt": ""}
        assert has_investigation_keywords(data) == False

        # Non-string input (dict)
        data = {"userPrompt": {"key": "value"}}
        # Should sanitize to string and check
        assert has_investigation_keywords(data) == False


class TestEarlyExitOptimization:
    """Test early-exit optimization for non-investigation queries."""

    def test_non_investigation_query_bypasses_verification(self):
        """Test that non-investigation queries bypass verification."""
        from PreToolUse_verification_router import run_verification_modules

        # Non-investigation query
        data = {"userPrompt": "create a new file"}

        # Should return None (no verification)
        result = run_verification_modules(data)
        assert result is None or result.get("additionalContext") is None


class TestInputSanitization:
    """Test input sanitization."""

    def test_non_string_input_sanitized(self):
        """Test that non-string userPrompt is converted to string."""
        from PreToolUse_verification_router import sanitize_input

        # Dict input
        data = {"userPrompt": {"key": "value"}}
        sanitized = sanitize_input(data)

        assert isinstance(sanitized["userPrompt"], str)
        assert sanitized["userPrompt"] == "{'key': 'value'}"


class TestRateLimiting:
    """Test rate limiting on verification template injection."""

    def test_rate_limit_state_file_created(self):
        """Test that rate limit state file is created."""
        from PreToolUse_verification_router import RATE_LIMIT_STATE

        assert RATE_LIMIT_STATE is not None
        assert isinstance(RATE_LIMIT_STATE, str)


class TestErrorHandling:
    """Test error handling and graceful degradation."""

    def test_module_failure_doesnt_crash_router(self):
        """Test that module failures are logged but don't crash router."""
        from PreToolUse_verification_router import run_verification_modules

        # Create mock module that raises exception
        def failing_module(data):
            raise ValueError("Module failed")

        # Mock module loader to return failing module
        with patch('PreToolUse_verification_router.load_verification_modules') as mock_load:
            mock_load.return_value = failing_module

            data = {}
            # Should handle exception gracefully
            result = run_verification_modules(data)
            # Should return None or partial result, not crash
            assert result is None or isinstance(result, dict)


class TestJSONInterface:
    """Test JSON stdin/stdout interface."""

    def test_json_input_parsing(self):
        """Test that JSON input is parsed correctly."""
        import io

        # Test valid JSON input
        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": "test"},
            "userPrompt": "investigate error"
        }
        input_json = json.dumps(input_data)

        old_stdin = sys.stdin
        sys.stdin = io.StringIO(input_json)

        try:
            # This should not raise
            # (We'll test the actual parsing in GREEN phase)
            assert True
        finally:
            sys.stdin = old_stdin

    def test_field_name_normalization(self):
        """Test camelCase to snake_case field normalization."""
        from PreToolUse_verification_router import normalize_input_fields

        # Input with camelCase
        data = {
            "toolInput": {"command": "test"},
            "userPrompt": "investigate error"
        }

        normalized = normalize_input_fields(data)

        assert "tool_input" in normalized
        assert normalized["tool_input"] == data["toolInput"]


class TestModuleInterface:
    """Test VerificationModule protocol compliance."""

    def test_module_has_run_function(self):
        """Test that verification modules have run() function."""
        from PreToolUse_verification_modules.investigation_verification import run

        assert callable(run)

    def test_run_returns_dict_or_none(self):
        """Test that run() returns dict or None."""
        from PreToolUse_verification_modules.investigation_verification import run

        # Investigation query - should return dict
        data = {"userPrompt": "investigate error"}
        result = run(data)

        assert result is None or isinstance(result, dict)

        # Non-investigation query - should return None
        data = {"userPrompt": "create file"}
        result = run(data)

        assert result is None


class TestBypassFlagEdgeCases:
    """Test bypass flag edge cases."""

    def test_bypass_flag_at_start(self):
        """Test bypass flag at start of prompt."""
        from PreToolUse_verification_modules.investigation_verification import check_bypass_flag

        data = {"userPrompt": "--skip-investigation-verify investigate error"}
        assert check_bypass_flag(data) == True

    def test_bypass_flag_at_middle(self):
        """Test bypass flag in middle of prompt."""
        from PreToolUse_verification_modules.investigation_verification import check_bypass_flag

        data = {"userPrompt": "investigate --skip-investigation-verify error"}
        assert check_bypass_flag(data) == True

    def test_bypass_flag_at_end(self):
        """Test bypass flag at end of prompt."""
        from PreToolUse_verification_modules.investigation_verification import check_bypass_flag

        data = {"userPrompt": "investigate error --skip-investigation-verify"}
        assert check_bypass_flag(data) == True

    def test_bypass_flag_typo_not_detected(self):
        """Test that typos in bypass flag are not detected."""
        from PreToolUse_verification_modules.investigation_verification import check_bypass_flag

        data = {"userPrompt": "investigate error --skip-investigation-verfiy"}
        assert check_bypass_flag(data) == False


class TestAdversarialInputs:
    """Test router behavior with adversarial inputs."""

    def test_malformed_json_input(self):
        """Test router handles malformed JSON gracefully."""
        import io

        # Malformed JSON
        input_json = "{invalid json"

        old_stdin = sys.stdin
        sys.stdin = io.StringIO(input_json)

        try:
            # Should handle gracefully and exit with ok:true
            assert True  # We'll verify in GREEN phase
        finally:
            sys.stdin = old_stdin

    def test_extremely_long_prompt(self):
        """Test router handles very long prompts (10MB+)."""
        from PreToolUse_verification_router import run_verification_modules

        # Generate long prompt (simulated with shorter string for test)
        long_prompt = "error " * 10000
        data = {"userPrompt": long_prompt}

        # Should not crash or hang
        result = run_verification_modules(data)
        assert result is not None  # Should process normally

    def test_special_characters(self):
        """Test router handles special characters."""
        from PreToolUse_verification_router import run_verification_modules

        # Null bytes and control characters
        data = {"userPrompt": "Error\x00Null\x1BCtrl"}
        result = run_verification_modules(data)

        # Should sanitize and continue
        assert result is not None


class TestModuleIsolation:
    """Test that verification modules are properly isolated."""

    @pytest.mark.skip(reason="Requires mock modules")
    def test_module_state_isolation(self):
        """Test that modules can't affect each other's state."""
        # This test verifies that module A setting a global variable
        # doesn't affect module B

        # Will implement in GREEN phase with actual modules
        assert True

    @pytest.mark.skip(reason="Requires mock modules")
    def test_module_exception_isolation(self):
        """Test that module exceptions don't crash router."""
        # This test verifies that module A raising exception
        # doesn't prevent module B from running

        # Will implement in GREEN phase with actual modules
        assert True


class TestRouterExecutionEndToEnd:
    """Test end-to-end execution of the router's main() function."""

    def test_investigation_query_runs_verification(self):
        """Test that investigation queries trigger verification modules."""
        import io

        from PreToolUse_verification_router import main

        # Investigation query input
        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": "ls"},
            "userPrompt": "investigate this error"
        }
        input_json = json.dumps(input_data)

        old_stdin = sys.stdin
        old_stdout = sys.stdout
        sys.stdin = io.StringIO(input_json)
        sys.stdout = io.StringIO()

        try:
            # Run main() - should execute verification
            main()
            output = sys.stdout.getvalue()

            # Should return JSON output
            result = json.loads(output)
            assert "continue" in result
            assert result["continue"] is True

        finally:
            sys.stdin = old_stdin
            sys.stdout = old_stdout

    def test_non_investigation_query_bypasses(self):
        """Test that non-investigation queries bypass verification."""
        import io

        from PreToolUse_verification_router import main

        # Non-investigation query
        input_data = {
            "tool_name": "Write",
            "tool_input": {"file_path": "test.txt"},
            "userPrompt": "create a new file"
        }
        input_json = json.dumps(input_data)

        old_stdin = sys.stdin = io.StringIO(input_json)
        old_stdout = sys.stdout = io.StringIO()

        try:
            # Run main() - should bypass verification
            main()
            output = sys.stdout.getvalue()

            # Should return JSON output without verification context
            result = json.loads(output)
            assert "continue" in result
            assert result["continue"] is True
            # Should not have additionalContext from verification
            assert "additionalContext" not in result or result.get("additionalContext") == ""

        finally:
            sys.stdin = old_stdin
            sys.stdout = old_stdout

    def test_bypass_flag_skips_verification(self):
        """Test that bypass flag prevents verification."""
        import io

        from PreToolUse_verification_router import main

        # Investigation query with bypass flag
        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": "ls"},
            "userPrompt": "investigate this error --skip-investigation-verify"
        }
        input_json = json.dumps(input_data)

        old_stdin = sys.stdin = io.StringIO(input_json)
        old_stdout = sys.stdout = io.StringIO()

        try:
            # Run main() - should skip verification due to bypass flag
            main()
            output = sys.stdout.getvalue()

            # Should return JSON output allowing continuation
            result = json.loads(output)
            assert "continue" in result
            assert result["continue"] is True

        finally:
            sys.stdin = old_stdin
            sys.stdout = old_stdout

    def test_malformed_json_returns_continue(self):
        """Test that malformed JSON returns continue=true (fail open)."""
        import io

        from PreToolUse_verification_router import main

        # Malformed JSON
        input_json = "{invalid json"

        old_stdin = sys.stdin = io.StringIO(input_json)
        old_stdout = sys.stdout = io.StringIO()

        try:
            # Run main() - should handle gracefully
            main()
            output = sys.stdout.getvalue()

            # Should return JSON allowing continuation (fail open)
            result = json.loads(output)
            assert "continue" in result
            assert result["continue"] is True
            assert "Invalid JSON" in result["reason"]

        finally:
            sys.stdin = old_stdin
            sys.stdout = old_stdout

    def test_camelcase_fields_normalized(self):
        """Test that camelCase input fields are normalized to snake_case."""
        import io

        from PreToolUse_verification_router import main

        # Input with camelCase fields
        input_data = {
            "toolName": "Bash",
            "toolInput": {"command": "ls"},
            "userPrompt": "investigate error"
        }
        input_json = json.dumps(input_data)

        old_stdin = sys.stdin = io.StringIO(input_json)
        old_stdout = sys.stdout = io.StringIO()

        try:
            # Run main() - should normalize fields
            main()
            output = sys.stdout.getvalue()

            # Should return JSON allowing continuation
            result = json.loads(output)
            assert "continue" in result
            assert result["continue"] is True

        finally:
            sys.stdin = old_stdin
            sys.stdout = old_stdout

    def test_verification_context_included_in_output(self):
        """Test that verification context is included in output."""
        import io
        from unittest.mock import patch

        from PreToolUse_verification_router import main

        # Mock the investigation_verification module to return context
        mock_verification_result = {
            "additionalContext": "Please investigate the root cause before making changes."
        }

        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": "ls"},
            "userPrompt": "investigate this error"
        }
        input_json = json.dumps(input_data)

        old_stdin = sys.stdin = io.StringIO(input_json)
        old_stdout = sys.stdout = io.StringIO()

        # Mock run_verification_modules to return context
        with patch('PreToolUse_verification_router.run_verification_modules', return_value=mock_verification_result):
            try:
                main()
                output = sys.stdout.getvalue()

                # Should include verification context in output
                result = json.loads(output)
                assert "continue" in result
                assert "additionalContext" in result
                assert "investigate" in result["additionalContext"].lower()

            finally:
                sys.stdin = old_stdin
                sys.stdout = old_stdout

    def test_empty_input_returns_continue(self):
        """Test that empty input returns continue=true (fail open)."""
        import io

        from PreToolUse_verification_router import main

        # Empty input (invalid JSON)
        input_json = ""

        old_stdin = sys.stdin = io.StringIO(input_json)
        old_stdout = sys.stdout = io.StringIO()

        try:
            # Run main() - should handle gracefully
            main()
            output = sys.stdout.getvalue()

            # Should return continue=true for empty input (fail open)
            result = json.loads(output)
            assert "continue" in result
            assert result["continue"] is True
            assert "Invalid JSON" in result["reason"]

        finally:
            sys.stdin = old_stdin
            sys.stdout = old_stdout

    def test_exception_in_main_returns_continue(self):
        """Test that exceptions in main() return continue=true (fail open)."""
        import io
        from unittest.mock import patch

        from PreToolUse_verification_router import main

        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": "ls"},
            "userPrompt": "investigate error"
        }
        input_json = json.dumps(input_data)

        old_stdin = sys.stdin = io.StringIO(input_json)
        old_stdout = sys.stdout = io.StringIO()

        # Mock run_verification_modules to raise exception
        with patch('PreToolUse_verification_router.run_verification_modules', side_effect=Exception("Router error")):
            try:
                main()
                output = sys.stdout.getvalue()

                # Should handle exception and return continue=true (fail open)
                result = json.loads(output)
                assert "continue" in result
                assert result["continue"] is True
                assert "Router error" in result["reason"]

            finally:
                sys.stdin = old_stdin
                sys.stdout = old_stdout
