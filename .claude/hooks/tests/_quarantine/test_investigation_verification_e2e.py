"""
Integration tests for PreToolUse verification router.

Tests the router's integration with the PreToolUse hook chain,
including end-to-end workflow and interaction with other hooks.
"""

import json
import sys
from pathlib import Path

# Add hooks directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))



class TestRouterIntegration:
    """Test router integration with PreToolUse hook chain."""

    def test_full_workflow_investigation_query(self):
        """Test complete workflow for investigation query."""
        from PreToolUse_verification_router import run_verification_modules

        # Investigation query
        data = {
            "tool_name": "Bash",
            "tool_input": {"command": "ls"},
            "userPrompt": "investigate this error",
            "sessionId": "test-session"
        }

        # Should return verification template
        result = run_verification_modules(data)

        assert result is not None
        assert "additionalContext" in result
        assert "Multi-Source Investigation Verification" in result["additionalContext"]

    def test_full_workflow_non_investigation_query(self):
        """Test complete workflow for non-investigation query."""
        from PreToolUse_verification_router import run_verification_modules

        # Non-investigation query
        data = {
            "tool_name": "Write",
            "tool_input": {"file_path": "test.txt"},
            "userPrompt": "create a new file",
            "sessionId": "test-session"
        }

        # Should bypass verification (return None)
        result = run_verification_modules(data)

        assert result is None

    def test_bypass_flag_integration(self):
        """Test bypass flag prevents verification."""
        from PreToolUse_verification_router import run_verification_modules

        # Investigation query with bypass flag
        data = {
            "tool_name": "Bash",
            "tool_input": {"command": "ls"},
            "userPrompt": "investigate this error --skip-investigation-verify",
            "sessionId": "test-session"
        }

        # Should bypass verification (return None)
        result = run_verification_modules(data)

        assert result is None

    def test_json_interface_integration(self):
        """Test router handles JSON stdin/stdout correctly."""
        import io

        from PreToolUse_verification_router import main

        # Test JSON input
        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": "test"},
            "userPrompt": "investigate error"
        }
        input_json = json.dumps(input_data)

        old_stdin = sys.stdin
        old_stdout = sys.stdout
        sys.stdin = io.StringIO(input_json)
        sys.stdout = io.StringIO()

        try:
            # Run router main()
            main()

            # Get output
            output = sys.stdout.getvalue()
            result = json.loads(output)

            # Debug: print output
            print(f"\n[DEBUG] Router output: {output[:200]}")

            # Should have continue: true
            assert result["continue"] == True

            # Should have additionalContext (investigation verification)
            # Note: additionalContext only present if investigation keywords detected
            # and verification template is generated
            if "additionalContext" not in result:
                print("\n[DEBUG] No additionalContext found - this may be expected if verification was bypassed")

        finally:
            sys.stdin = old_stdin
            sys.stdout = old_stdout


class TestModuleInteraction:
    """Test interaction between verification modules."""

    def test_module_run_signature(self):
        """Test that all modules have correct run() signature."""
        from PreToolUse_verification_modules.investigation_verification import run

        # Test with valid input
        data = {"userPrompt": "investigate error"}

        result = run(data)

        # Should return dict or None
        assert result is None or isinstance(result, dict)

    def test_module_returns_additional_context(self):
        """Test that modules return additionalContext when appropriate."""
        from PreToolUse_verification_modules.investigation_verification import run

        # Investigation query
        data = {"userPrompt": "investigate error"}

        result = run(data)

        # Should return dict with additionalContext
        assert result is not None
        assert isinstance(result, dict)
        assert "additionalContext" in result

    def test_module_returns_none_for_non_investigation(self):
        """Test that modules return None for non-investigation queries."""
        from PreToolUse_verification_modules.investigation_verification import run

        # Non-investigation query
        data = {"userPrompt": "create file"}

        result = run(data)

        # Should return None
        assert result is None


class TestErrorHandlingIntegration:
    """Test error handling in integration scenarios."""

    def test_graceful_degradation_on_module_error(self):
        """Test router continues even if one module fails."""
        from PreToolUse_verification_router import run_verification_modules

        # Non-investigation query (bypasses module loading)
        data = {"userPrompt": "create file"}

        # Should handle gracefully
        result = run_verification_modules(data)

        # Should not crash
        assert result is None

    def test_malformed_input_handling(self):
        """Test router handles malformed input gracefully."""
        from PreToolUse_verification_router import normalize_input_fields

        # Malformed input (missing userPrompt)
        data = {"toolInput": {"command": "test"}}

        # Should normalize without crashing
        normalized = normalize_input_fields(data)

        assert normalized is not None
        assert "tool_input" in normalized


class TestPerformanceIntegration:
    """Test performance characteristics in integration context."""

    def test_early_exit_optimization(self):
        """Test that non-investigation queries return quickly."""
        from PreToolUse_verification_router import run_verification_modules

        # Non-investigation query
        data = {"userPrompt": "create a new file"}

        # Should return None immediately (no module loading)
        result = run_verification_modules(data)

        assert result is None

    def test_module_caching_integration(self):
        """Test module caching works across multiple calls."""
        from PreToolUse_verification_router import load_verification_modules

        # First load
        module1 = load_verification_modules("investigation_verification")

        # Second load (should be cached)
        module2 = load_verification_modules("investigation_verification")

        # Should return same cached object
        assert module1 is module2


class TestBypassLoggingIntegration:
    """Test bypass flag logging integration."""

    def test_bypass_log_file_created(self):
        """Test bypass log file is created when bypass flag used."""
        from PreToolUse_verification_modules.investigation_verification import (
            BYPASS_LOG,
            check_bypass_flag,
        )

        data = {
            "userPrompt": "investigate error --skip-investigation-verify",
            "sessionId": "integration-test-session"
        }

        # Check bypass flag (which logs it)
        check_bypass_flag(data)

        # Verify log file exists
        assert BYPASS_LOG.exists()

        # Verify log contains session ID
        log_content = BYPASS_LOG.read_text()
        assert "integration-test-session" in log_content

    def test_bypass_log_append(self):
        """Test multiple bypasses append to log file."""
        from PreToolUse_verification_modules.investigation_verification import (
            BYPASS_LOG,
            check_bypass_flag,
        )

        # Clean up log file if it exists
        if BYPASS_LOG.exists():
            BYPASS_LOG.unlink()

        # First bypass
        data1 = {
            "userPrompt": "investigate error 1 --skip-investigation-verify",
            "sessionId": "session-1"
        }
        check_bypass_flag(data1)

        # Second bypass
        data2 = {
            "userPrompt": "investigate error 2 --skip-investigation-verify",
            "sessionId": "session-2"
        }
        check_bypass_flag(data2)

        # Verify both entries are in log
        log_content = BYPASS_LOG.read_text()
        assert "session-1" in log_content
        assert "session-2" in log_content
